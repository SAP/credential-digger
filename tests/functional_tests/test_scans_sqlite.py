import os
import tempfile
import unittest

from credentialdigger.cli import cli
from credentialdigger.client_sqlite import SqliteClient
from git import Repo as GitRepo


class TestScansSqlite(unittest.TestCase):

    def setUp(self):
        self.tmp_path = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp_path, "test_db.sqlite")
        SqliteClient(self.db_path)
        cli.main(["", "add_rules", "tests/functional_tests/test_rules.yml",
                  "--sqlite", self.db_path])

    def tearDown(self):
        os.remove(self.db_path)

    def test_scan_github(self):
        repo_url = 'https://github.com/fabiosangregorio/credential-digger-tests'
        with self.assertRaises(SystemExit) as cm:
            cli.main(["", "scan", "--sqlite", self.db_path,
                      "--category", "password",
                      "--force", repo_url])
        self.assertEqual(cm.exception.code, 9)

    def test_scan_local(self):
        repo_url = 'https://github.com/fabiosangregorio/credential-digger-tests'
        repo_path = os.path.join(self.tmp_path, "tmp_repo")
        GitRepo.clone_from(repo_url, repo_path)

        with self.assertRaises(SystemExit) as cm:
            cli.main(["", "scan", "--sqlite", self.db_path,
                      "--models", "PathModel", "SnippetModel",
                      "--category", "password",
                      "--force", "--local", repo_path])
        self.assertEqual(cm.exception.code, 4)
