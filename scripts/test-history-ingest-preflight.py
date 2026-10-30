"""Behavior checks for conservative authoring reports and resumable mechanical stages."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('history_ingest_preflight', Path(__file__).with_name('history_ingest_preflight.py'))
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)
PERIODS = [dict(label='西周后期', from_year=-841, to_year=-770),
           dict(label='春秋', from_year=-770, to_year=-475),
           dict(label='秦汉', from_year=-221, to_year=220)]


def draft(year=-100, dynasty='西汉', description='汉廷任命使者。'):
    event = dict(group='events', row=dict(key='event_a', title='任命使者', description=description,
                 dynasty=dynasty, start_year=year, end_year=year),
                 evidence=[dict(paragraph_id='p1', quote='任命使者。')])
    curation = dict(items=[event], reused_keys=[], editorial_checklist=dict(events={
        'event_a': dict(participation=dict(status='complete', required_person_keys=[], reason='本条未具名，不补人物。'))}))
    return curation, dict(paragraphs=[dict(id='p1', text='任命使者。')])


class AuthoringTest(unittest.TestCase):
    def analyze(self, curation, packet):
        return preflight.analyze_curation(curation, packet, PERIODS)

    def test_conservative_periods_unknown_and_reused(self):
        for year, dynasty in [(None, '春秋'), (-841, '战国末至秦末'), (-500, '秦'), (220, '汉'), (975, '五代十国')]:
            c, p = draft(year, dynasty)
            self.assertEqual(self.analyze(c, p)['issues'], [])
            self.assertEqual(c['items'][0]['row']['start_year'], year)
        c, p = draft(900)
        self.assertEqual(self.analyze(c, p)['issues'][0]['code'], 'event_period_mismatch')
        c['reused_keys'] = ['event_a']
        self.assertEqual(self.analyze(c, p)['issues'], [])

    def test_overlap_is_not_a_definite_period_contradiction(self):
        c, p = draft(-300)
        c['items'][0]['row']['end_year'] = -100
        self.assertEqual(self.analyze(c, p)['issues'], [])
        c['items'][0]['row']['end_year'] = -250
        self.assertEqual(self.analyze(c, p)['issues'][0]['code'], 'event_period_mismatch')

    def test_explicit_exception_is_bound_to_observed_data_and_source(self):
        c, p = draft(900)
        original = copy.deepcopy((c, p))
        report = self.analyze(c, p)
        self.assertEqual((c, p), original)
        issue = report['issues'][0]
        c['editorial_checklist']['exceptions'] = [dict(issue_id=issue['issue_id'], reason='该条追述早事，标签为后世篇章语境，已核原文。')]
        self.assertTrue(self.analyze(c, p)['ready_to_freeze'])
        p['paragraphs'][0]['text'] += '来源发生修改。'
        changed = self.analyze(c, p)
        self.assertFalse(changed['ready_to_freeze'])
        self.assertIn(issue['issue_id'], changed['unused_exception_ids'])

    def test_internal_template_is_a_question_not_a_text_rewriter(self):
        c, p = draft(description='本条保存原记载，不由王位承继推定亲属。')
        original = copy.deepcopy(c)
        report = self.analyze(c, p)
        self.assertEqual(report['issues'][0]['code'], 'internal_description_template')
        self.assertEqual(c, original)
        c['editorial_checklist']['exceptions'] = [dict(issue_id=report['issues'][0]['issue_id'], reason='此处是在说明待考亲属，作者确认保留。')]
        self.assertTrue(self.analyze(c, p)['ready_to_freeze'])
        c, p = draft(description='《史记》本表记载汉廷任命使者。')
        p['paragraphs'][0]['text'] = '本条保存这句话只是原始引文。'
        self.assertEqual(self.analyze(c, p)['issues'], [])

    def test_actor_requirements_need_actual_edges_and_cannot_be_waived(self):
        c, p = draft()
        c['items'][0]['required_actor_keys'] = ['person_a']
        first = self.analyze(c, p)
        missing = next(x for x in first['issues'] if x['code'] == 'required_actor_missing_person_event')
        c['editorial_checklist']['exceptions'] = [dict(issue_id=missing['issue_id'], reason='试图跳过必需人物边。')]
        self.assertFalse(self.analyze(c, p)['ready_to_freeze'])
        c['items'].append(dict(group='person_events', row=dict(key='pe_a', person_key='person_a', event_key='event_a', role='使者')))
        self.assertTrue(self.analyze(c, p)['ready_to_freeze'])

    def test_checklist_is_required_and_pending_does_not_become_complete(self):
        c, p = draft()
        del c['editorial_checklist']['events']['event_a']
        self.assertEqual(self.analyze(c, p)['issues'][0]['code'], 'participation_review_missing')
        c, p = draft()
        c['editorial_checklist']['events']['event_a']['participation']['status'] = 'pending'
        self.assertEqual(self.analyze(c, p)['issues'][0]['code'], 'participation_review_pending')

    def test_only_structured_actors_are_used_never_prose_name_guessing(self):
        c, p = draft(description='刘邦派张良出使。')
        self.assertTrue(self.analyze(c, p)['ready_to_freeze'])
        c['items'][0]['actors'] = [dict(person_key='person_b', required=True)]
        missing = self.analyze(c, p)['issues']
        self.assertEqual(missing[0]['observed'], 'person_b')
        c['items'][0]['actors'] = [dict(person_key='person_b', required='false')]
        self.assertEqual(self.analyze(c, p)['issues'][0]['code'], 'invalid_actor_requirement')
        c['items'][0]['actors'] = ['张良']
        self.assertEqual(self.analyze(c, p)['issues'][0]['code'], 'invalid_actor_requirement')

    def test_person_period_check_uses_only_authored_activity_years(self):
        c, p = draft()
        person = dict(group='people', row=dict(key='person_yan', name='燕惠侯', era='春秋',
                        birth_year=None, death_year=None, description='燕国君主。'),
                      evidence=[dict(paragraph_id='p1', quote='任命使者。')])
        c['items'].append(person)
        self.assertTrue(self.analyze(c, p)['ready_to_freeze'])
        c['editorial_checklist']['period_checks'] = [dict(subject_key='person_yan', source_active_years=[-841], reason='已核此格为前841年的在位君主。')]
        report = self.analyze(c, p)
        self.assertEqual(report['issues'][0]['code'], 'person_period_mismatch')
        self.assertIsNone(person['row']['birth_year'])
        self.assertIsNone(person['row']['death_year'])
        c['editorial_checklist']['period_checks'][0]['source_active_years'] = []
        self.assertTrue(self.analyze(c, p)['ready_to_freeze'])

    def test_invalid_activity_check_shape_is_not_silently_ignored(self):
        c, p = draft()
        c['editorial_checklist']['period_checks'] = {'source_active_years': [-841]}
        self.assertFalse(self.analyze(c, p)['ready_to_freeze'])

    def test_person_exception_and_no_fuzzy_date_parsing(self):
        c, p = draft()
        c['items'].append(dict(group='people', row=dict(key='person_x', era='春秋'), evidence=[]))
        c['editorial_checklist']['period_checks'] = [dict(subject_key='person_x', source_active_years=['前841年'], reason='尚未规范年份。')]
        self.assertEqual(self.analyze(c, p)['issues'][0]['code'], 'invalid_authored_period_check')
        c['editorial_checklist']['period_checks'][0]['source_active_years'] = [-841]
        issue = self.analyze(c, p)['issues'][0]
        c['editorial_checklist']['exceptions'] = [dict(issue_id=issue['issue_id'], reason='人物标签语境已由作者单独复核。')]
        self.assertTrue(self.analyze(c, p)['ready_to_freeze'])


ENGINE = '''from pathlib import Path
import sys
source, output, counter = map(Path, sys.argv[1:4])
n = int(counter.read_text()) + 1 if counter.exists() else 1
counter.write_text(str(n))
output.write_text(source.read_text())
print('attempt', n)
print('diagnostic', file=sys.stderr)
'''


class StageRunnerTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / 'input.txt'
        self.source.write_text('first')
        self.output = self.root / 'output.txt'
        self.counter = self.root / 'counter.txt'
        self.engine = self.root / 'engine.py'
        self.engine.write_text(ENGINE)
        self.runner = preflight.StageRunner(self.root / 'receipts')
        self.command = [sys.executable, str(self.engine), str(self.source), str(self.output), str(self.counter)]

    def tearDown(self):
        self.temp.cleanup()

    def run_stage(self, **kwargs):
        return self.runner.run('mechanical validation', self.command, inputs=[self.source], outputs=[self.output], **kwargs)

    def test_unchanged_pass_skips_but_input_output_and_script_changes_rerun(self):
        first = self.run_stage()
        self.assertEqual(first['status'], 'passed')
        self.assertEqual(self.run_stage()['status'], 'skipped')
        self.source.write_text('second')
        self.assertEqual(self.run_stage()['status'], 'passed')
        self.output.write_text('tampered')
        self.assertEqual(self.run_stage()['status'], 'passed')
        self.assertEqual(self.output.read_text(), 'second')
        self.engine.write_text(ENGINE + '\n# changed engine\n')
        self.assertEqual(self.run_stage()['status'], 'passed')
        self.assertEqual(self.counter.read_text(), '4')
        self.assertIn('attempt 1', Path(first['stdout_log']).read_text())
        self.assertIn('diagnostic', Path(first['stderr_log']).read_text())

    def test_declared_shared_engine_and_logs_are_hashed(self):
        helper = self.root / 'helper.py'
        helper.write_text('VERSION = 1')
        first = self.run_stage(engines=[helper])
        self.assertEqual(self.run_stage(engines=[helper])['status'], 'skipped')
        helper.write_text('VERSION = 2')
        self.assertEqual(self.run_stage(engines=[helper])['status'], 'passed')
        last = self.run_stage(engines=[helper])
        Path(last['stdout_log']).write_text('tampered log')
        self.assertEqual(self.run_stage(engines=[helper])['status'], 'passed')
        self.assertEqual(self.counter.read_text(), '3')
        self.assertEqual(first['category'], 'engineering')

    def test_failure_never_becomes_a_cache_hit_and_same_input_can_recover(self):
        marker = self.root / 'failed-once'
        self.engine.write_text('''from pathlib import Path
import sys
source, output, marker = map(Path, sys.argv[1:4])
print('attempting')
if not marker.exists():
    marker.write_text('failure observed')
    output.write_text('stale failed product')
    print('first failure', file=sys.stderr)
    raise SystemExit(7)
output.write_text(source.read_text())
''')
        command = self.command[:4] + [str(marker)]
        failed = self.runner.run('retry', command, inputs=[self.source], outputs=[self.output], check=False)
        self.assertEqual(failed['status'], 'failed')
        self.assertEqual(failed['returncode'], 7)
        self.assertIn('first failure', Path(failed['stderr_log']).read_text())
        recovered = self.runner.run('retry', command, inputs=[self.source], outputs=[self.output])
        self.assertEqual(recovered['status'], 'passed')
        self.assertEqual(recovered['attempt'], 2)
        self.assertEqual(recovered['fingerprint'], failed['fingerprint'])
        self.assertEqual(self.output.read_text(), 'first')

    def test_missing_input_is_recorded_and_cannot_reuse_an_older_pass(self):
        self.run_stage()
        self.source.unlink()
        failed = self.run_stage(check=False)
        self.assertEqual(failed['status'], 'failed')
        self.assertIn('missing', Path(failed['stderr_log']).read_text())
        self.source.write_text('first')
        self.assertEqual(self.run_stage()['status'], 'passed')
        self.assertEqual(self.counter.read_text(), '2')

    def test_missing_output_is_failure_even_on_zero_exit(self):
        self.engine.write_text("print('no artifact')\n")
        with self.assertRaises(preflight.StageExecutionError) as error:
            self.run_stage()
        self.assertEqual(error.exception.result['returncode'], 0)
        self.assertEqual(error.exception.result['status'], 'failed')
        self.engine.write_text(ENGINE)
        self.assertEqual(self.run_stage()['status'], 'passed')

    def test_started_attempt_is_retriable_and_interrupt_is_logged(self):
        first = self.run_stage()
        state = Path(first['stdout_log']).parent / 'state.json'
        receipt = json.loads(state.read_text())
        receipt['status'] = 'started'
        state.write_text(json.dumps(receipt))
        self.assertEqual(self.run_stage()['status'], 'passed')
        with patch.object(preflight.subprocess, 'run', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):self.run_stage(cacheable=False)
        self.assertEqual(json.loads(state.read_text())['status'], 'interrupted')
        self.assertEqual(self.run_stage()['status'], 'passed')

    def test_apply_is_opt_in_and_apply_and_fresh_acceptance_always_execute(self):
        with self.assertRaises(PermissionError):self.run_stage(kind='apply')
        with self.assertRaises(PermissionError):
            self.runner.run('apply flag', self.command + ['--apply'], inputs=[self.source], outputs=[self.output])
        for kind in ['apply', 'fresh_acceptance']:
            for _ in range(2):
                result = self.run_stage(kind=kind, allow_apply=kind == 'apply')
                self.assertEqual(result['status'], 'passed')
                self.assertFalse(result['cached'])
                self.assertFalse(preflight.cache_matches(result, result['fingerprint'], result['outputs'], result['logs']))
        self.assertEqual(self.counter.read_text(), '4')

    def test_started_records_survive_retries_without_double_counting_time(self):
        result = self.run_stage()
        history = Path(result['stdout_log']).parent / 'history.jsonl'
        records = [json.loads(line) for line in history.read_text().splitlines()]
        self.assertEqual([x['status'] for x in records], ['started', 'passed'])
        summary = preflight.timing_summary(records)['engineering']
        self.assertEqual(summary['attempts'], 1)
        self.assertEqual(summary['elapsed_seconds'], result['elapsed_seconds'])

    def test_environment_changes_invalidate_without_serializing_values(self):
        first = self.run_stage(env={'HISTREE_STAGE_TEST': 'first-private-value'})
        self.assertEqual(self.run_stage(env={'HISTREE_STAGE_TEST': 'first-private-value'})['status'], 'skipped')
        changed = self.run_stage(env={'HISTREE_STAGE_TEST': 'changed-private-value'})
        self.assertEqual(changed['status'], 'passed')
        state = Path(changed['stdout_log']).parent / 'state.json'
        self.assertNotIn('private-value', state.read_text())
        self.assertNotEqual(first['fingerprint'], changed['fingerprint'])

    def test_inputs_changed_during_command_are_not_passed(self):
        self.engine.write_text(ENGINE + "source.write_text('changed during stage')\n")
        failed = self.run_stage(check=False)
        self.assertEqual(failed['status'], 'failed')
        self.assertIn('changed during', failed['failure_reason'])

    def test_directory_artifacts_and_time_categories(self):
        directory = self.root / 'artifacts'
        directory.mkdir()
        self.command[3] = str(directory / 'result.txt')
        records = []
        for category in preflight.CATEGORIES:
            records.append(self.runner.run(category, self.command, inputs=[self.source], outputs=[directory], category=category))
        (directory / 'result.txt').write_text('corrupted')
        self.assertEqual(self.runner.run('engineering', self.command, inputs=[self.source], outputs=[directory])['status'], 'passed')
        summary = preflight.timing_summary(records)
        for category in preflight.CATEGORIES:
            self.assertEqual(summary[category]['attempts'], 1)
            self.assertGreaterEqual(summary[category]['elapsed_seconds'], 0)
        with self.assertRaises(ValueError):self.run_stage(category='uncategorized')


if __name__ == '__main__':
    unittest.main()
