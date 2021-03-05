import os
import unittest

from credentialdigger.scanners.file_scanner import FileScanner
from parameterized import param, parameterized


class TestFileScanner(unittest.TestCase):
    root_test_path = './credentialdigger/tests/file_scanner_tests'

    @classmethod
    def setUpClass(cls):
        """ Add only the password-related rules to the database """
        rules = [{'id': 9, 'regex': 'sshpass|password|pwd|passwd|pass',
                  'category': 'password', 'description': 'password keywords'}]
        cls.file_scanner = FileScanner(rules)

    def test_scan_dir(self):
        """ Test scan success on the 'scan_tests' folder """
        test_path = os.path.join(self.root_test_path, 'scan_tests')
        discoveries = self.file_scanner.scan(test_path)
        self.assertEqual(len(discoveries), 3)

    @parameterized.expand(
        ["/nonexistentdirectory/", "https://url", "not_a_path"])
    def test_scan_dir_not_found(self, dir_path):
        """ Test scan failure with nonexistent directory paths """
        with self.assertRaises(FileNotFoundError):
            self.file_scanner.scan(dir_path)

    @parameterized.expand([
        param(file_path='file_a.py', expected_discoveries=[2, 4, 5]),
        param(file_path='file_c.png', expected_discoveries=[])
    ])
    def test_scan_file(self, file_path, expected_discoveries):
        """ Test scan_file with valid and invalid files

        The `expected_discoveries` parameter is an array containing the line
        number of the discoveries in the file.
        """
        discoveries = self.file_scanner.scan_file(
            os.path.join(self.root_test_path, file_path), self.root_test_path)
        d_lines = [d["line_number"] for d in discoveries]
        self.assertCountEqual(d_lines, expected_discoveries)

    @parameterized.expand([
        param(max_depth=0,
              expected_dirs=[],
              expected_files=["file_a.py", "file_b.txt"]),
        param(max_depth=1,
              expected_dirs=["subdir_A"],
              expected_files=["file_a.py", "file_b.txt", "file_Aa.yml"]),
        param(max_depth=2,
              expected_dirs=["subdir_A", "subdir_AB"],
              expected_files=["file_a.py", "file_b.txt",
                              "file_Aa.yml", "file_ABa.txt"]),
        param(max_depth=-1,
              expected_dirs=["subdir_A", "subdir_AB"],
              expected_files=["file_a.py", "file_b.txt",
                              "file_Aa.yml", "file_ABa.txt"])
    ])
    def test_prune_depth(self, max_depth, expected_dirs, expected_files):
        """ Test prune with respect to the `max_depth` argument """
        initial_depth = self.root_test_path.count(os.path.sep)
        all_dirs = []
        all_files = []

        for root, dirs, files in os.walk(self.root_test_path):
            self.file_scanner._prune(root, dirs, files, initial_depth,
                                     max_depth=max_depth)
            all_dirs.extend(dirs)
            all_files.extend(files)

        set(expected_dirs).issubset(set(all_dirs))
        set(expected_files).issubset(set(all_files))
