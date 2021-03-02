import os
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
            expected_dirs=["subdir_A", "subdir_AB"],
            expected_files=["file_a.py", "file_b.txt",
                            "file_Aa.yml", "file_ABa.txt"]
        ),
        param(
            # Since timestamp is now, all files should be pruned.
            # NOTE: the mtime of a directory does not change if the content of
            # a file inside of it changes. Therefore no folders should be pruned.
            timestamp=int(datetime.now(timezone.utc).timestamp()),
            expected_dirs=["subdir_A", "subdir_AB"],
            expected_files=[]
        ),
    ])
    def test_prune_timestamp(self, timestamp, expected_dirs, expected_files):
        """ Test prune with respect to the `since_timestamp` argument """
        test_path = './credentialdigger/tests/file_scanner_test_folder'
        initial_depth = test_path.count(os.path.sep)
        all_dirs = []
        all_files = []

        for root, dirs, files in os.walk(test_path):
            self.file_scanner._prune(root, dirs, files, initial_depth,
                                     since_timestamp=timestamp)
            all_dirs.extend(dirs)
            all_files.extend(files)

        # Despite its name, `assertCountEqual` tests that both lists have the
        # same items (not just the same count)
        self.assertCountEqual(all_dirs, expected_dirs)
        self.assertCountEqual(all_files, expected_files)

    @parameterized.expand([
        param(
            max_depth=0,
            expected_dirs=[],
            expected_files=["file_a.py", "file_b.txt"]
        ),
        param(
            max_depth=1,
            expected_dirs=["subdir_A"],
            expected_files=["file_a.py", "file_b.txt", "file_Aa.yml"]
        ),
        param(
            max_depth=2,
            expected_dirs=["subdir_A", "subdir_AB"],
            expected_files=["file_a.py", "file_b.txt",
                            "file_Aa.yml", "file_ABa.txt"]
        ),
        param(
            max_depth=-1,
            expected_dirs=["subdir_A", "subdir_AB"],
            expected_files=["file_a.py", "file_b.txt",
                            "file_Aa.yml", "file_ABa.txt"]
        )
    ])
    def test_prune_depth(self, max_depth, expected_dirs, expected_files):
        """ Test prune with respect to the `max_depth` argument """
        test_path = './credentialdigger/tests/file_scanner_test_folder'
        initial_depth = test_path.count(os.path.sep)
        all_dirs = []
        all_files = []

        for root, dirs, files in os.walk(test_path):
            self.file_scanner._prune(root, dirs, files, initial_depth,
                                     max_depth=max_depth)
            all_dirs.extend(dirs)
            all_files.extend(files)

        # Despite its name, `assertCountEqual` tests that both lists have the
        # same items (not just the same count)
        self.assertCountEqual(all_dirs, expected_dirs)
        self.assertCountEqual(all_files, expected_files)
