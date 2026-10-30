"""Read-only authoring checks and hash-bound timing for mechanical ingestion stages.

Pure API: analyze_curation(curation, packet, periods, period_aliases=None).
It reports questions, never edits facts, dates, people or edges. Participation is
explicit, e.g. editorial_checklist.events[event_key].participation = {
  "status": "complete", "required_person_keys": ["person_x"], "reason": "..."}.
An event item may also declare required_actor_keys or actors=[{"person_key": ...}].
Exceptions use editorial_checklist.exceptions=[{"issue_id": ..., "reason": ...}].
They are tied to the observed row/evidence/source text and cannot waive missing
required participation or replace an unfinished editorial review.

StageRunner contains no database client. Only kind="mechanical" is cacheable.
Apply requires allow_apply=True, and apply/fresh_acceptance always execute.
Callers must label network acceptance fresh_acceptance, declare engine/helper
files and all relevant inputs/outputs. A cached command is not historical review
or fresh public acceptance. Category labels distinguish time spent, not approval.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
import uuid

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCROLL = ROOT / 'apps/web/src/data/history-scroll.json'
RULE_VERSION = 1
CATEGORIES = ('editorial', 'publication', 'engineering')
KINDS = ('mechanical', 'apply', 'fresh_acceptance')
# Deliberately not fuzzy: 秦 may name the pre-imperial state; 北宋 and 西夏 do
# not both map to a navigation band merely because they coexisted with 宋.
PERIOD_ALIASES = {
    '秦朝': '秦汉', '漢': '秦汉', '汉': '秦汉', '西汉': '秦汉', '西漢': '秦汉',
    '东汉': '秦汉', '東漢': '秦汉', '西汉初年': '秦汉', '秦末汉初': '秦汉',
    '秦末漢初': '秦汉', '秦漢': '秦汉', '三國': '三国',
    '唐': '隋唐', '唐代': '隋唐', '晚唐': '隋唐', '隋': '隋唐',
}
TEMPLATE_PATTERNS = (
    r'本条(?:保存|仅用于)', r'本批(?:次)?(?:整理|复用|校核|新增)',
    r'不(?:由|凭|据)(?:王位|侯位)(?:承继|承袭|继承)?(?:推定|推断|推算|补)',
    r'不(?:由|凭|据)(?:世次|承袭次序|承继次序|继承次序)(?:推定|推断|推算|补)',
    r'稳定\s*key', r'temporal_review', r'curation\.json', r'person_events',
)


def json_sha256(value):
    """Pure, deterministic fingerprint of JSON data; never writes the data."""
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def _year(value):
    return isinstance(value, int) and not isinstance(value, bool) and value != 0


def _context(item, paragraphs):
    ids = sorted({e.get('paragraph_id') for e in item.get('evidence', [])
                  if isinstance(e, dict) and isinstance(e.get('paragraph_id'), str)})
    return json_sha256({'row': item.get('row'), 'evidence': item.get('evidence', []),
                        'sources': {pid: paragraphs.get(pid, {}).get('text') for pid in ids}})


def _issue(code, key, field, observed, expected, message, context='', waivable=False):
    binding = dict(version=RULE_VERSION, code=code, subject_key=key, field=field,
                   observed=observed, expected=expected, context_sha256=context)
    return dict(binding, issue_id=code + ':' + json_sha256(binding), message=message,
                waivable=waivable, status='open')


def period_issues(item, periods, context='', period_aliases=None):
    """Only wholly disjoint, explicitly mapped new event intervals are questions.

    Navigation boundaries are inclusive for this conservative check. Overlap,
    unknown dates and ambiguous/unmapped labels are not interpreted as errors.
    The caller excludes reused events; this function itself is pure.
    """
    row = item.get('row', {})
    label = row.get('dynasty') or row.get('era')
    if not isinstance(label, str):
        return []
    aliases = dict(PERIOD_ALIASES)
    if period_aliases:
        aliases.update(period_aliases)
    labels = {p['label']: p for p in periods}
    mapped = label if label in labels else aliases.get(label)
    period = labels.get(mapped)
    if not period:
        return []
    dates = [row.get(k) for k in ('start_year', 'end_year') if _year(row.get(k))]
    if not dates:
        return []
    start, end = min(dates), max(dates)
    lower, upper = period['from_year'], period['to_year']
    if end < lower or start > upper:
        return [_issue('event_period_mismatch', row.get('key'), 'dynasty',
                       dict(label=label, start_year=row.get('start_year'), end_year=row.get('end_year')),
                       dict(label=mapped, from_year=lower, to_year=upper),
                       '明确日期与站内导航分期没有交集；请核对标签或原纪年，例外须给出人工理由。',
                       context, waivable=True)]
    return []


def authored_period_issues(check, item, periods, context='', period_aliases=None):
    """Person period questions use authored activity years, never inferred lifetimes."""
    years = check.get('source_active_years')
    if years is None or years == []:
        return []
    row = item.get('row', {})
    if not isinstance(years, list) or not all(_year(y) for y in years) or not isinstance(check.get('reason'), str) or not check['reason'].strip():
        return [_issue('invalid_authored_period_check', row.get('key'), 'source_active_years', check,
                       'explicit integer activity years and an authored source reason',
                       '活动年检查需要人工已核年份与理由；工具不会解析原文数字或推生卒。', context)]
    aliases = dict(PERIOD_ALIASES)
    if period_aliases:
        aliases.update(period_aliases)
    labels = {p['label']: p for p in periods}
    label = row.get('era')
    mapped = label if label in labels else aliases.get(label)
    period = labels.get(mapped)
    if period and not any(period['from_year'] <= y <= period['to_year'] for y in years):
        return [_issue('person_period_mismatch', row.get('key'), 'era',
                       dict(label=label, source_active_years=years, source_reason=check['reason']),
                       period, '人物时代标签与人工已核活动年均不相交；请复核标签或身份，不据此推生卒。',
                       context, waivable=True)]
    return []


def description_issues(item, context=''):
    """Flag narrow internal-work phrases, not historical quotations or all 本表."""
    row = item.get('row', {})
    fields = [('description', row.get('description'))]
    for index, phase in enumerate(row.get('phases') or []):
        if isinstance(phase, dict):
            fields.append(('phases[%d].description' % index, phase.get('description')))
    found = []
    for field, value in fields:
        if not isinstance(value, str):
            continue
        matches = sorted({m.group(0) for pattern in TEMPLATE_PATTERNS
                          for m in re.finditer(pattern, value, re.IGNORECASE)})
        if matches:
            found.append(_issue('internal_description_template', row.get('key'), field,
                                dict(matches=matches, text=value), 'independently readable prose',
                                '展示说明含明确的内部工作模板句；仅报告疑点，作者可修改或写明保留理由。',
                                context, waivable=True))
    return found


def _keys(value):
    return isinstance(value, list) and all(isinstance(k, str) and k.strip() for k in value)


def participation_issues(item, person_events, checklist, context=''):
    """No name recognition: requirements come only from structured author data."""
    row = item.get('row', {})
    key = row.get('key')
    issues, required = [], set()
    explicit = item.get('required_actor_keys', [])
    if not _keys(explicit):
        issues.append(_issue('invalid_actor_requirement', key, 'required_actor_keys', explicit,
                             'list of stable person keys', '参与要求必须显式给出人物key，不能用正文姓名自动猜配。', context))
    else:
        required.update(explicit)
    actors = item.get('actors', [])
    if not isinstance(actors, list):
        actors = [actors]
    for actor in actors:
        if (not isinstance(actor, dict) or not isinstance(actor.get('person_key'), str)
                or not actor['person_key'].strip() or not isinstance(actor.get('required', True), bool)):
            issues.append(_issue('invalid_actor_requirement', key, 'actors', actor,
                                 '{person_key, required?}', 'actor必须明确指向人物key；工具不会解析姓名补边。', context))
        elif actor.get('required', True):
            required.add(actor['person_key'])
    event_reviews = checklist.get('events', {}) if isinstance(checklist, dict) else {}
    event_review = event_reviews.get(key, {}) if isinstance(event_reviews, dict) else {}
    review = event_review.get('participation') if isinstance(event_review, dict) else None
    if not isinstance(review, dict):
        issues.append(_issue('participation_review_missing', key, 'editorial_checklist.events', None,
                             'participation {status, required_person_keys, reason}',
                             '本事件尚无结构化参与审阅；不能用边数或正文自动代替作者确认。', context))
    else:
        declared = review.get('required_person_keys')
        if not _keys(declared):
            issues.append(_issue('invalid_participation_review', key, 'required_person_keys', declared,
                                 'explicit key list, possibly empty', '参与审阅需要显式人物key列表；无具名参与者可填写空列表并说明。', context))
        else:
            required.update(declared)
        if review.get('status') != 'complete' or not isinstance(review.get('reason'), str) or not review['reason'].strip():
            issues.append(_issue('participation_review_pending', key, 'editorial_checklist.events', review,
                                 'complete with a nonempty authored reason', '参与审阅仍待考或缺少人工核对理由。', context))
    present = {p.get('person_key') for p in person_events if p.get('event_key') == key}
    for person_key in sorted(required - present):
        issues.append(_issue('required_actor_missing_person_event', key, 'person_events', person_key,
                             dict(person_key=person_key, event_key=key),
                             '作者显式要求的参与人物缺少person_event；工具只报告，不自动加边。', context))
    return issues


def analyze_curation(curation, packet, periods, period_aliases=None):
    """Pure report. Neither data nor editorial exceptions are mutated."""
    if isinstance(periods, dict):
        periods = periods['periods']
    if any(not isinstance(p.get('label'), str) or not _year(p.get('from_year'))
           or not _year(p.get('to_year')) or p['from_year'] > p['to_year'] for p in periods):
        raise ValueError('Periods need explicit labels and ordered nonzero integer bounds')
    if len({p['label'] for p in periods}) != len(periods):
        raise ValueError('Duplicate navigation-period labels are ambiguous')
    paragraphs = {p['id']: p for p in packet.get('paragraphs', []) + packet.get('supplementary_paragraphs', [])}
    items = curation.get('items', [])
    reused = set(curation.get('reused_keys', []))
    checklist = curation.get('editorial_checklist', {})
    person_events = [i['row'] for i in items if i.get('group') == 'person_events']
    issues = []
    for item in items:
        context = _context(item, paragraphs)
        issues.extend(description_issues(item, context))
        if item.get('group') == 'events':
            if item.get('row', {}).get('key') not in reused:
                issues.extend(period_issues(item, periods, context, period_aliases))
            issues.extend(participation_issues(item, person_events, checklist, context))
    # Optional checks are supplied by the author; the packet is never mined for dates.
    period_checks = checklist.get('period_checks', []) if isinstance(checklist, dict) else []
    by_key = {i.get('row', {}).get('key'): i for i in items if i.get('group') == 'people'}
    events_by_key = {i.get('row', {}).get('key'): i for i in items if i.get('group') == 'events'}
    # An explicit participation plus an authored event year is an activity check.
    # This also checks reused people; names or raw text never supply dates here.
    for edge in person_events:
        person=by_key.get(edge.get('person_key'));event=events_by_key.get(edge.get('event_key'))
        if not person or not event:
            continue
        years=[event['row'].get(k) for k in ('start_year','end_year') if _year(event['row'].get(k))]
        if not years:
            continue
        context=json_sha256(dict(person=_context(person,paragraphs),event=_context(event,paragraphs),edge=edge))
        for issue in authored_period_issues(dict(source_active_years=years,reason='显式事件参与：'+edge.get('event_key','')),person,periods,context,period_aliases):
            issue['message']='参与人物的时代与该事件已核年份不相交；检查跨时代同名误复用，或记录来源差异的具体理由。'
            issues.append(issue)
    if not isinstance(period_checks, list):
        issues.append(_issue('invalid_authored_period_check', None, 'period_checks', period_checks,
                             'list of authored person checks', 'period_checks需要显式审阅条目列表，不能静默忽略。'))
    for authored in period_checks if isinstance(period_checks, list) else []:
        if not isinstance(authored, dict) or authored.get('subject_key') not in by_key:
            issues.append(_issue('invalid_authored_period_check', None, 'period_checks', authored,
                                 'an existing person subject_key', '活动年检查必须明确指向当前草稿人物。'))
            continue
        item = by_key[authored['subject_key']]
        issues.extend(authored_period_issues(authored, item, periods, _context(item, paragraphs), period_aliases))
    exceptions = checklist.get('exceptions', []) if isinstance(checklist, dict) else []
    accepted = {}
    for review in exceptions if isinstance(exceptions, list) else []:
        if isinstance(review, dict) and isinstance(review.get('issue_id'), str) and isinstance(review.get('reason'), str) and review['reason'].strip():
            accepted[review['issue_id']] = review
    used = set()
    for issue in issues:
        review = accepted.get(issue['issue_id'])
        if review and issue['waivable']:
            issue['status'] = 'accepted_exception'
            issue['exception_review'] = copy.deepcopy(review)
            used.add(issue['issue_id'])
    open_count = sum(i['status'] == 'open' for i in issues)
    return dict(format_version=1, rule_version=RULE_VERSION, ready_to_freeze=open_count == 0,
                summary=dict(issues=len(issues), open=open_count, accepted_exceptions=len(used)),
                issues=issues, unused_exception_ids=sorted(set(accepted) - used),
                note='机械疑点报告；不证明史实正确、关系完整或已经发布。')


def hash_path(path, _seen=frozenset()):
    """Hash file bytes or a deterministic directory tree, including symlink targets."""
    path = Path(path)
    if path.is_symlink():
        target = path.resolve()
        if target in _seen:
            raise ValueError('Symlink cycle: %s' % path)
        return dict(kind='symlink', target=os.readlink(path), sha256=json_sha256(hash_path(target, _seen)))
    if not path.exists():
        return dict(kind='missing')
    if path.is_file():
        h = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                h.update(block)
        return dict(kind='file', sha256=h.hexdigest(), executable=bool(path.stat().st_mode & 0o111))
    if path.is_dir():
        resolved = path.resolve()
        if resolved in _seen:
            raise ValueError('Directory cycle: %s' % path)
        entries = [(p.name, hash_path(p, _seen | {resolved})) for p in sorted(path.iterdir(), key=lambda p: p.name)]
        return dict(kind='directory', sha256=json_sha256(entries))
    raise ValueError('Unsupported artifact type: %s' % path)


def snapshot_paths(paths, cwd=None):
    base = Path(cwd or Path.cwd())
    resolved = sorted({str((base / Path(p)).resolve()) for p in paths})
    return {p: hash_path(p) for p in resolved}


def stage_fingerprint(spec, input_hashes, engine_hashes):
    """Pure cache key; engine versions and all declared input bytes participate."""
    return json_sha256(dict(version=1, spec=spec, inputs=input_hashes, engines=engine_hashes))


def cache_matches(receipt, fingerprint, output_hashes, log_hashes, cacheable=True):
    """Pure eligibility check; failures, started attempts and absent outputs never pass."""
    return bool(cacheable and receipt and len(log_hashes) == 2 and receipt.get('kind') == 'mechanical'
                and receipt.get('status') == 'passed'
                and receipt.get('fingerprint') == fingerprint
                and receipt.get('outputs') == output_hashes and receipt.get('logs') == log_hashes
                and all(x.get('kind') != 'missing' for x in list(output_hashes.values()) + list(log_hashes.values())))


def timing_summary(records):
    """Pure aggregation; engineering work is never silently counted as editorial."""
    result = {category: dict(attempts=0, cache_hits=0, failures=0, elapsed_seconds=0.0) for category in CATEGORIES}
    for record in records:
        if record.get('status') == 'started':
            continue
        bucket = result[record['category']]
        bucket['cache_hits' if record.get('cached') else 'attempts'] += 1
        bucket['failures'] += record.get('status') in ('failed', 'interrupted')
        bucket['elapsed_seconds'] += record.get('elapsed_seconds', 0.0)
    return result


def _now():
    return datetime.now(timezone.utc).isoformat()


def _write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    os.replace(temp, path)


class StageExecutionError(RuntimeError):
    def __init__(self, result):
        self.result = result
        super().__init__('%s: %s' % (result['name'], result.get('failure_reason', 'command failed')))


class StageRunner:
    def __init__(self, state_directory):
        self.state_directory = Path(state_directory).resolve()

    def run(self, name, command, inputs=(), outputs=(), engines=(), category='engineering',
            kind='mechanical', cacheable=True, allow_apply=False, cwd=None, env=None,
            timeout=None, check=True):
        requested = time.perf_counter()
        started_at = _now()
        if category not in CATEGORIES or kind not in KINDS:
            raise ValueError('Unknown stage category or execution kind')
        if not isinstance(command, (list, tuple)) or not command or not all(isinstance(x, str) for x in command):
            raise ValueError('Use an explicit argv list; shell command strings are not accepted')
        applies = kind == 'apply' or any(x == '--apply' or x.startswith('--apply=') for x in command)
        if applies and not allow_apply:
            raise PermissionError('Apply stages require explicit allow_apply=True')
        effective_kind = 'apply' if applies else kind
        can_cache = bool(cacheable and effective_kind == 'mechanical')
        cwd = Path(cwd or Path.cwd()).resolve()
        effective_env = dict(os.environ)
        if env:
            effective_env.update(env)
        # Environment values are hashed, not serialized into receipts.
        engine_paths = list(engines) + [Path(__file__).resolve()]
        executable = shutil.which(command[0], path=effective_env.get('PATH'))
        if executable and Path(executable).is_file():
            engine_paths.append(executable)
        # Capture the main interpreted script even when the caller omits engines.
        for argument in command[1:]:
            if argument in ('-c', '-m', '-e', '--eval'):
                break
            if argument.startswith('-'):
                continue
            candidate = cwd / argument
            if candidate.suffix in ('.py', '.mjs', '.cjs', '.js', '.sh') and candidate.is_file():
                engine_paths.append(candidate)
            break
        input_hashes = snapshot_paths(inputs, cwd)
        engine_hashes = snapshot_paths(engine_paths, cwd)
        missing = [p for p, value in {**input_hashes, **engine_hashes}.items() if value['kind'] == 'missing']
        output_paths = sorted(snapshot_paths(outputs, cwd))
        spec = dict(command=list(command), cwd=str(cwd), category=category, kind=effective_kind,
                    output_paths=output_paths, environment_sha256=json_sha256(effective_env))
        fingerprint = stage_fingerprint(spec, input_hashes, engine_hashes)
        token = re.sub(r'[^A-Za-z0-9_.-]', '-', str(name))[:48] + '-' + json_sha256(str(name))[:12]
        directory = self.state_directory / token
        state_path = directory / 'state.json'
        directory.mkdir(parents=True, exist_ok=True)
        try:
            previous = json.loads(state_path.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            previous = None
        current_outputs = snapshot_paths(output_paths)
        previous_logs = snapshot_paths(list((previous or {}).get('logs', {})))
        if cache_matches(previous, fingerprint, current_outputs, previous_logs, can_cache):
            result = dict(previous, status='skipped', cached=True, started_at=started_at,
                          finished_at=_now(), elapsed_seconds=time.perf_counter() - requested,
                          command_elapsed_seconds=0.0)
            self._record(directory, result)
            return result
        attempt = (previous or {}).get('attempt', 0) + 1
        attempt_id = '%04d-%s' % (attempt, uuid.uuid4().hex[:12])
        stdout_path = directory / (attempt_id + '.stdout.log')
        stderr_path = directory / (attempt_id + '.stderr.log')
        receipt = dict(format_version=1, name=str(name), category=category, kind=effective_kind,
                       attempt=attempt, attempt_id=attempt_id, status='started', cached=False,
                       fingerprint=fingerprint, inputs=input_hashes, engines=engine_hashes,
                       spec=spec, started_at=started_at, stdout_log=str(stdout_path), stderr_log=str(stderr_path))
        _write_json(state_path, receipt)
        self._record(directory, receipt)
        interrupted = None
        command_started = time.perf_counter()
        with stdout_path.open('wb') as stdout, stderr_path.open('wb') as stderr:
            try:
                if missing:
                    raise FileNotFoundError('Declared input or engine is missing: ' + ', '.join(missing))
                completed = subprocess.run(command, cwd=str(cwd), env=effective_env,
                                           stdout=stdout, stderr=stderr, timeout=timeout, check=False)
                receipt['returncode'] = completed.returncode
                if completed.returncode:
                    receipt['failure_reason'] = 'command exited %s' % completed.returncode
            except BaseException as error:
                interrupted = error if isinstance(error, (KeyboardInterrupt, SystemExit)) else None
                receipt['returncode'] = None
                receipt['failure_reason'] = type(error).__name__ + ': ' + str(error)
                stderr.write((receipt['failure_reason'] + '\n').encode('utf-8', errors='replace'))
        receipt['command_elapsed_seconds'] = time.perf_counter() - command_started
        receipt['outputs'] = snapshot_paths(output_paths)
        receipt['logs'] = snapshot_paths([stdout_path, stderr_path])
        if not receipt.get('failure_reason'):
            missing_outputs = [p for p, value in receipt['outputs'].items() if value['kind'] == 'missing']
            if missing_outputs:
                receipt['failure_reason'] = 'declared outputs missing: ' + ', '.join(missing_outputs)
            elif effective_kind == 'mechanical' and (snapshot_paths(inputs, cwd) != input_hashes
                    or snapshot_paths(engine_paths, cwd) != engine_hashes):
                receipt['failure_reason'] = 'inputs or engines changed during the command'
        receipt.update(status='interrupted' if interrupted else 'failed' if receipt.get('failure_reason') else 'passed',
                       finished_at=_now(), elapsed_seconds=time.perf_counter() - requested)
        _write_json(state_path, receipt)
        self._record(directory, receipt)
        if interrupted:
            raise interrupted
        if check and receipt['status'] != 'passed':
            raise StageExecutionError(receipt)
        return receipt

    @staticmethod
    def _record(directory, result):
        with (directory / 'history.jsonl').open('a') as stream:
            stream.write(json.dumps(result, ensure_ascii=False) + '\n')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--scroll', type=Path, default=DEFAULT_SCROLL)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--fail-on-open', action='store_true')
    args = parser.parse_args(argv)
    paths = dict(curation=args.directory / 'curation.json', packet=args.directory / 'packet.json', scroll=args.scroll)
    raw = {key: path.read_bytes() for key, path in paths.items()}
    data = {key: json.loads(value) for key, value in raw.items()}
    report = analyze_curation(data['curation'], data['packet'], data['scroll'])
    report['inputs'] = {key: dict(path=str(path.resolve()), kind='file', sha256=hashlib.sha256(raw[key]).hexdigest()) for key, path in paths.items()}
    if args.output:
        _write_json(args.output, report)
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if args.fail_on_open and not report['ready_to_freeze'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
