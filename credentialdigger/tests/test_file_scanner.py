import os
import sys
import unittest
from datetime import datetime, timezone

from credentialdigger.scanners.file_scanner import FileScanner
from parameterized import param, parameterized


class TestFileScanner(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rules = [{'id': 9, 'regex': 'sshpass|password|pwd|passwd|pass',
                  'category': 'password', 'description': 'password keywords'}]
        cls.file_scanner = FileScanner(rules)

    # def test_scan_file_not_found(self, ""):

    @parameterized.expand([
        param(
            # Since timestamp is 0, no file should be pruned
            timestamp=0,
            expected_dirs=["subdir_A"],
            expected_files=["file_a.py", "file_b.txt", "file_A_a.yml"]
        ),
        param(
            # Since timestamp is now, all files should be pruned.
            # NOTE: the mtime of a directory does not change if the content of
            # a file inside of it changes. Therefore no folders should be pruned.
            timestamp=int(datetime.now(timezone.utc).timestamp()),
            expected_dirs=["subdir_A"],
            expected_files=[]
        ),
    ])
    def test_prune_timestamp(self, timestamp, expected_dirs, expected_files):
        all_dirs = []
        all_files = []

        for root, dirs, files in os.walk('./credentialdigger/tests/file_scanner_test_folder'):
            self.file_scanner._prune(root, dirs, files, since_timestamp=timestamp,
                                     ignore_list=[])
            all_dirs.extend(dirs)
            all_files.extend(files)

        self.assertCountEqual(all_dirs, expected_dirs)
        self.assertCountEqual(all_files, expected_files)
