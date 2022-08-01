import os
import tempfile
import unittest

from credentialdigger.cli import cli
from credentialdigger.client_sqlite import SqliteClient
from git import Repo as GitRepo
from parameterized import param, parameterized

TOTAL_PW_DISCOVERIES = 11


class TestScansSqlite(unittest.TestCase):
    repo_url = 'https://github.com/SAP/credential-digger-tests'

    @classmethod
    def setUpClass(cls):
        cls.tmp_path = tempfile.mkdtemp()
        cls.db_path = os.path.join(cls.tmp_path, "test_db.sqlite")
        SqliteClient(cls.db_path)
        cli.main(["", "add_rules", "tests/functional_tests/test_rules.yml",
                  "--sqlite", cls.db_path])

    @classmethod
    def tearDownClass(cls):
        os.remove(cls.db_path)

    def test_scan_github(self):
        with self.assertRaises(SystemExit) as cm:
            cli.main(["", "scan", "--sqlite", self.db_path,
                      "--category", "password",
                      "--force", self.repo_url])
        self.assertEqual(cm.exception.code, TOTAL_PW_DISCOVERIES)

    def test_scan_local(self):
        repo_path = os.path.join(self.tmp_path, "tmp_repo")
        GitRepo.clone_from(self.repo_url, repo_path)

        with self.assertRaises(SystemExit) as cm:
            cli.main(["", "scan", "--sqlite", self.db_path,
                      "--models", "PathModel", "PasswordModel",
                      "--category", "password",
                      "--force", repo_path])
        # When using the models, we expect to be left with less than
        # TOTAL_PW_DISCOVERIES discoveries to manually review
        self.assertTrue(cm.exception.code < TOTAL_PW_DISCOVERIES)

    def test_scan_wiki(self):
        with self.assertRaises(SystemExit) as cm:
            cli.main(["", "scan_wiki", "--sqlite", self.db_path,
                      "--category", "password", self.repo_url])
        self.assertEqual(cm.exception.code, 5)

    @parameterized.expand([
        param(pr_num=1, leaks=5),
        param(pr_num=2, leaks=0)
    ])
    def test_scan_pr(self, pr_num, leaks):
        """ Test scan_pull_request method on vulnerable and clean pull
        requests  """
        with self.assertRaises(SystemExit) as cm:
            cli.main(["", "scan_pr", "--sqlite", self.db_path,
                      "--category", "password",
                      "--pr", str(pr_num),
                      self.repo_url])
            # pr_num needed to be cast to str not to raise TypeError here, but
            # its type will later be managed by the scanner
        self.assertEqual(cm.exception.code, leaks)

    def test_scan_snapshot(self): ...
