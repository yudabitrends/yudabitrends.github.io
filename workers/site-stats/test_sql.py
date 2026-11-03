'''Verify the exact Worker SQL using SQLite transactions and concurrent writers.'''
import concurrent.futures
import json
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent
SCHEMA = (ROOT / 'schema.sql').read_text(encoding='utf-8')
IMPORT = 'import { SQL } from ' + json.dumps((ROOT / 'worker.mjs').as_uri()) + '; process.stdout.write(JSON.stringify(SQL));'
SQL = json.loads(subprocess.check_output(['node', '--input-type=module', '-e', IMPORT], text=True, encoding='utf-8'))

class StatsSQLTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = str(Path(self.directory.name) / 'stats.sqlite')
        self.db = sqlite3.connect(self.path)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.executescript(SCHEMA)

    def tearDown(self):
        self.db.close()
        self.directory.cleanup()

    @staticmethod
    def increment(db, country, region, instant):
        with db:
            db.execute(SQL['touch'], (instant, instant))
            db.execute(SQL['increment'], (country, region))
            total = db.execute(SQL['totals']).fetchone()[2]
            regions = db.execute(SQL['regions']).fetchall()
        return total, regions

    def test_initial_zero_and_rerun_preserves_data(self):
        initial = self.db.execute(SQL['totals']).fetchone()
        self.assertEqual(initial[2], 0)
        self.assertRegex(initial[0], r'^\d{4}-\d{2}-\d{2}T.*Z$')
        self.increment(self.db, 'CN', 'Beijing', '2026-11-03T06:00:00.000Z')
        self.db.executescript(SCHEMA)
        current = self.db.execute(SQL['totals']).fetchone()
        self.assertEqual(current[0], initial[0])
        self.assertEqual(current[2], 1)

    def test_rollback_does_not_partially_increment(self):
        self.increment(self.db, 'CN', 'Beijing', '2026-11-03T06:00:00.000Z')
        before = self.db.execute(SQL['totals']).fetchone()
        with self.assertRaises(sqlite3.IntegrityError):
            with self.db:
                self.db.execute(SQL['touch'], ('2030-01-01T00:00:00.000Z',) * 2)
                self.db.execute(SQL['increment'], ('CN', 'Beijing'))
                self.db.execute(SQL['increment'], ('INVALID', 'Failure'))
        self.assertEqual(self.db.execute(SQL['totals']).fetchone(), before)
        self.assertEqual(self.db.execute(SQL['regions']).fetchall(), [('CN', 'Beijing', 1)])

    def test_concurrent_updates_tie_out_and_parameterization(self):
        def run(worker_id):
            db = sqlite3.connect(self.path, timeout=30)
            try:
                for i in range(75):
                    region = f'Province {worker_id % 3}'
                    self.increment(db, 'CN', region, f'2030-01-01T00:{worker_id:02}:{i % 60:02}.000Z')
            finally:
                db.close()
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(run, range(8)))
        total = self.db.execute(SQL['totals']).fetchone()[2]
        regions = self.db.execute(SQL['regions']).fetchall()
        self.assertEqual(total, 600)
        self.assertEqual(sum(row[2] for row in regions), total)
        strange_region = 'X' + chr(39) + '); DROP TABLE site_stats_regions; --'
        self.increment(self.db, 'US', strange_region, '2031-01-01T00:00:00.000Z')
        self.assertEqual(self.db.execute(SQL['totals']).fetchone()[2], 601)
        self.assertIn(('US', strange_region, 1), self.db.execute(SQL['regions']).fetchall())
        self.increment(self.db, 'ZZ', '', '2020-01-01T00:00:00.000Z')
        self.assertEqual(self.db.execute(SQL['totals']).fetchone()[1], '2031-01-01T00:00:00.000Z')

if __name__ == '__main__':
    unittest.main(verbosity=2)
