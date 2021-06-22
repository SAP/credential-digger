import os
import unittest

from credentialdigger.scanners.file_scanner import FileScanner
from parameterized import param, parameterized


class TestFileScanner(unittest.TestCase):
    root_test_path = './tests/file_scanner_tests_folder'

    @classmethod
    def setUpClass(cls):
        """ Instantiate the scanner with only the password-related rules. """
        rules = [{'id': 9, 'regex': 'sshpass|password|pwd|passwd|pass[\W_]',
                  'category': 'password', 'description': 'password keywords'}]
        cls.file_scanner = FileScanner(rules)

    @parameterized.expand([
        param(path='scan_tests', expected_discoveries=3),
        param(path='scan_tests/scan_a.py', expected_discoveries=2),
        param(path='./scan_tests/scan_a.py', expected_discoveries=2)
    ])
    def test_scan_dir(self, path, expected_discoveries):
        """ Test the overall scan success on the 'scan_tests' folder. """
        test_path = os.path.join(self.root_test_path, path)
        discoveries = self.file_scanner.scan(test_path)
        self.assertEqual(len(discoveries), expected_discoveries)

    @parameterized.expand([
        # Test file with no discoveries
        param(file_path='subdir_A/subdir_AB/file_ABa.txt',
              expected_discoveries=[]),
        # Test file with three discoveries
        param(file_path='file_a.py', expected_discoveries=[2, 4, 5]),
        # Test binary file
        param(file_path='file_c.png', expected_discoveries=[])
    ])
    def test_scan_file(self, file_path, expected_discoveries):
        """ Test scan_file with valid and invalid files.

        The `expected_discoveries` parameter is an array containing the line
        number of the discoveries in the file.
        """
        discoveries = self.file_scanner.scan_file(
            self.root_test_path, file_path)
        d_lines = [d['line_number'] for d in discoveries]
        self.assertCountEqual(d_lines, expected_discoveries)
