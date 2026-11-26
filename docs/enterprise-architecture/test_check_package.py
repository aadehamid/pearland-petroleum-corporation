"""Counterfactual checks for the documented architecture package fixtures."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import check_package as package


class PackageCheckTests(unittest.TestCase):
    def test_publication_fixture_rejects_unavailable_correction(self):
        source = package.INFO.read_text()
        package.temporal_fixture(source)
        with self.assertRaises(AssertionError):
            package.temporal_fixture(source.replace(
                '| R2 | P2 | planner / workspace | 13:00 |',
                '| R2 | P2 | planner / workspace | 12:30 |'))

    def test_retraction_fixture_requires_late_receipt(self):
        source = package.DATA.read_text()
        package.retraction_fixture(source)
        with self.assertRaises(AssertionError):
            package.retraction_fixture(source.replace(
                '| X1 / RETRACTED | L1 | 11:00 | 11:00 | 11:10 | 11:15 | OPERATIONS |',
                '| X1 / RETRACTED | L1 | 11:00 | 11:00 | 11:10 | 11:14 | OPERATIONS |'))

    def test_register_gap_and_duplicate_are_reported(self):
        source = package.REGISTER.read_text()
        row = next(line for line in source.splitlines() if line.startswith('| T93 ·'))
        with tempfile.TemporaryDirectory() as folder:
            register = Path(folder) / 'register.md'
            register.write_text(source.replace(row, ''))
            with patch.object(package, 'REGISTER', register):
                errors = []
                package.routes(errors)
            self.assertIn('missing register exchange T93', errors)
            register.write_text(source.replace(row, row + '\n' + row))
            with patch.object(package, 'REGISTER', register):
                errors = []
                package.routes(errors)
            self.assertIn('duplicate register exchange T93', errors)

    def test_heading_anchor_check(self):
        self.assertIn('3-worked-reconstruction', package.anchors(package.INFO.read_text()))
        self.assertNotIn('missing-heading', package.anchors(package.INFO.read_text()))


if __name__ == '__main__':
    unittest.main()
