import os
import tempfile
import unittest

from credentialdigger.cli import cli
from credentialdigger.client_sqlite import SqliteClient
from git import Repo as GitRepo


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
        self.assertEqual(cm.exception.code, 9)

    def test_scan_local(self):
        repo_path = os.path.join(self.tmp_path, "tmp_repo")
        GitRepo.clone_from(self.repo_url, repo_path)

        with self.assertRaises(SystemExit) as cm:
            cli.main(["", "scan", "--sqlite", self.db_path,
                      "--models", "PathModel", "SnippetModel",
                      "--category", "password",
                      "--force", "--local", repo_path])
        self.assertEqual(cm.exception.code, 2)

    def test_scan_wiki(self):
        with self.assertRaises(SystemExit) as cm:
            cli.main(["", "scan_wiki", "--sqlite", self.db_path,
                      "--category", "password", self.repo_url])
        self.assertEqual(cm.exception.code, 5)
