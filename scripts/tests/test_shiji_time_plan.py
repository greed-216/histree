import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]


class ShijiTimePlanTest(unittest.TestCase):
    def test_reviewed_sources_conform_to_actual_mysql_check(self):
        plan = json.loads((ROOT / 'content/revisions/2026-10-29-shiji-vol001-010-time/plan.json').read_text())
        schema = (ROOT / 'database/mysql/001-content.sql').read_text()
        check = re.search(r'CHECK \(source_type IN \(([^)]+)\)\)', schema).group(1)
        allowed = set(re.findall(r"'([^']+)'", check))
        self.assertTrue(plan['sources'])
        for source in plan['sources']:
            self.assertIn(source['source_type'], allowed, source['id'])
