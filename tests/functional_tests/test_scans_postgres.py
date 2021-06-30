import os
import shutil
import tempfile
import unittest

from credentialdigger.cli import cli
from git import Repo as GitRepo
from psycopg2 import connect


class TestScansPostgres(unittest.TestCase):
    dotenv = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    repo_url = 'https://github.com/SAP/credential-digger-tests'

    @classmethod
    def setUpClass(cls):
        # Add rules
        cli.main(["", "add_rules", "--dotenv", cls.dotenv,
                  "tests/functional_tests/test_rules.yml"])

    @classmethod
    def tearDownClass(cls):
        # Remove all discoveries and repositories
        conn = connect(dbname=os.getenv('POSTGRES_DB'),
                       user=os.getenv('POSTGRES_USER'),
                       password=os.getenv('POSTGRES_PASSWORD'),
                       host=os.getenv('DBHOST'),
                       port=os.getenv('DBPORT'))
        cur = conn.cursor()
        cur.execute("DELETE FROM discoveries;")
        cur.execute("DELETE FROM repos;")

    def test_scan_github(self):
        with self.assertRaises(SystemExit) as cm:
            cli.main(["", "scan", "--category", "password",
                      "--dotenv", self.dotenv,
                      "--force", self.repo_url])
        self.assertEqual(cm.exception.code, 9)

    def test_scan_local(self):
        repo_path = tempfile.mkdtemp()
        GitRepo.clone_from(self.repo_url, repo_path)

        with self.assertRaises(SystemExit) as cm:
            cli.main(["", "scan", "--dotenv", self.dotenv,
                      "--models", "PathModel", "SnippetModel",
                      "--category", "password",
                      "--force", "--local", repo_path])
        self.assertEqual(cm.exception.code, 2)

        shutil.rmtree(repo_path)

    def test_scan_wiki(self):
        with self.assertRaises(SystemExit) as cm:
            cli.main(["", "scan_wiki", "--dotenv", self.dotenv,
                      "--category", "password", self.repo_url])
        self.assertEqual(cm.exception.code, 5)
