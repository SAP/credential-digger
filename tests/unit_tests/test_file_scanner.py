import unittest

from credentialdigger.scanners.file_scanner import FileScanner
from parameterized import param, parameterized


class TestFileScanner(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """ Instantiate the scanner with only the password-related rules """
        rules = [{'id': 9, 'regex': 'sshpass|password|pwd|passwd|pass',
                  'category': 'password', 'description': 'password keywords'}]
        cls.file_scanner = FileScanner(rules)

    def setUp(self):
        self.paths = [
            {
                "root": "",
                "dirs": ["subdir_A"],
                "files": ["file_a.py", "file_b.txt", "file_c.png"]
            }, {
                "root": "subdir_A/",
                "dirs": ["subdir_AB"],
                "files": ["file_Aa.yml"]
            }, {
                "root": "subdir_A/subdir_AB/",
                "dirs": [],
                "files": ["file_ABa.txt"]
            }
        ]

    @parameterized.expand(
        ["/nonexistentdirectory/", "https://url", "not?a,path"])
    def test_scan_dir_not_found(self, dir_path):
        """ Test scan failure with nonexistent directory paths """
        with self.assertRaises(FileNotFoundError):
            self.file_scanner.scan(dir_path)

    @parameterized.expand([
        # Test root-only max depth
        param(max_depth=0,
              expected_dirs=[],
              expected_files=["file_a.py", "file_b.txt", "file_c.png"]),
        # Test max depth = 1 (one subdirectory)
        param(max_depth=1,
              expected_dirs=["subdir_A"],
              expected_files=["file_a.py", "file_b.txt", "file_c.png", "file_Aa.yml"]),
        # Test max depth = 2 (two subdirectories)
        param(max_depth=2,
              expected_dirs=["subdir_A", "subdir_AB"],
              expected_files=["file_a.py", "file_b.txt", "file_c.png",
                              "file_Aa.yml", "file_ABa.txt"]),
        # Test negative values (should not influence depth)
        param(max_depth=-1,
              expected_dirs=["subdir_A", "subdir_AB"],
              expected_files=["file_a.py", "file_b.txt", "file_c.png",
                              "file_Aa.yml", "file_ABa.txt"])
    ])
    def test_prune_depth(self, max_depth, expected_dirs, expected_files):
        """ Test prune with respect to the `max_depth` parameter """
        all_dirs = []
        all_files = []

        for path in self.paths:
            rel_dir_root = path["root"]
            dirs = path["dirs"]
            files = path["files"]
            self.file_scanner._prune(
                rel_dir_root, dirs, files, max_depth=max_depth)
            all_dirs.extend(dirs)
            all_files.extend(files)

        self.assertListEqual(all_dirs, expected_dirs)
        # self.assertListEqual(all_files, expected_files)

    @parameterized.expand([
        # Test empty ignore_list
        param(
            ignore_list=[],
            expected_ignored_dirs=[],
            expected_ignored_files=[]),
        # Test full directory and file names
        param(
            ignore_list=["subdir_A", "file_b.txt"],
            expected_ignored_dirs=["subdir_A"],
            expected_ignored_files=["file_b.txt"]),
        # Test names with wildcards
        param(
            ignore_list=["*_a*"],
            expected_ignored_dirs=[],
            expected_ignored_files=["file_a.txt", "scan_a.py"]),
        # Test nonexistent files and wildcards
        param(
            ignore_list=["nonexistent_file.txt", "*z*"],
            expected_ignored_dirs=[],
            expected_ignored_files=[]),
    ])
    def test_prune_ignore_list(self, ignore_list, expected_ignored_dirs,
                               expected_ignored_files):
        """ Test prune with respect to the `ignore_list` parameter """
        all_dirs = []
        all_files = []

        for path in self.paths:
            rel_dir_root = path["root"]
            dirs = path["dirs"]
            files = path["files"]
            self.file_scanner._prune(
                rel_dir_root, dirs, files, ignore_list=ignore_list)
            all_dirs.extend(dirs)
            all_files.extend(files)

        [self.assertNotIn(d, all_dirs) for d in expected_ignored_dirs]
        [self.assertNotIn(f, all_files) for f in expected_ignored_files]
