import os
import unittest
from datetime import datetime, timezone

from credentialdigger.scanners.file_scanner import FileScanner
from parameterized import param, parameterized


class TestFileScanner(unittest.TestCase):
    root_test_path = './credentialdigger/tests/file_scanner_test_folder'

    @classmethod
    def setUpClass(cls):
        rules = [{'id': 9, 'regex': 'sshpass|password|pwd|passwd|pass',
                  'category': 'password', 'description': 'password keywords'}]
        cls.file_scanner = FileScanner(rules)

    @parameterized.expand(
        ["", "/nonexistentdirectory/", "https://url", "not_a_path"])
    def test_scan_dir_not_found(self, dir_path):
        """ Test scan failure with nonexistent directory paths """
        with self.assertRaises(FileNotFoundError):
            self.file_scanner.scan(dir_path)

    @parameterized.expand([
        param(file_path='file_a.py', expected_discoveries_count=1),
        param(file_path='file_c.png', expected_discoveries_count=0)
    ])
    def test_scan_file(self, file_path, expected_discoveries_count):
        """ Test scan_file with valid and invalid files """
        discoveries = self.file_scanner.scan_file(
            os.path.join(self.root_test_path, file_path))
        self.assertEqual(len(discoveries), expected_discoveries_count)

    @parameterized.expand([
        # Since timestamp is 0, no file should be pruned
        param(timestamp=0,
              expected_dirs=["subdir_A", "subdir_AB"],
              expected_files=["file_a.py", "file_b.txt",
                              "file_Aa.yml", "file_ABa.txt"]),
        # Since timestamp is now, all files should be pruned.
        # NOTE: the mtime of a directory does not change if the content of
        # a file inside of it changes. Therefore no folders should be pruned.
        param(timestamp=int(datetime.now(timezone.utc).timestamp()),
              expected_dirs=["subdir_A", "subdir_AB"],
              expected_files=[]),
    ])
    def test_prune_timestamp(self, timestamp, expected_dirs, expected_files):
        """ Test prune with respect to the `since_timestamp` argument """
        initial_depth = self.root_test_path.count(os.path.sep)
        all_dirs = []
        all_files = []

        for root, dirs, files in os.walk(self.root_test_path):
            self.file_scanner._prune(root, dirs, files, initial_depth,
                                     since_timestamp=timestamp)
            all_dirs.extend(dirs)
            all_files.extend(files)

        set(expected_dirs).issubset(set(all_dirs))
        set(expected_files).issubset(set(all_files))

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
