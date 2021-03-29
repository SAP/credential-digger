import os
import tempfile
import unittest

from credentialdigger.cli import cli
from credentialdigger.client_postgres import PgClient
from git import Repo as GitRepo
from psycopg2 import connect


class TestScansPostgres(unittest.TestCase):
    dotenv = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

    @classmethod
    def setUpClass(cls):
        # Add rules
        cli.main(["", "add_rules", "--dotenv", cls.dotenv,
                  "tests/functional_tests/test_rules.yml"])

    @classmethod
    def tearDownClass(cls):
        conn = connect(dbname=os.getenv('POSTGRES_DB'),
                       user=os.getenv('POSTGRES_USER'),
                       password=os.getenv('POSTGRES_PASSWORD'),
                       host=os.getenv('DBHOST'),
                       port=os.getenv('DBPORT'))
        cur = conn.cursor()
        cur.execute("DELETE FROM discoveries;")
        cur.execute("DELETE FROM repos;")

    def test_scan_github(self):
        repo_url = 'https://github.com/fabiosangregorio/credential-digger-tests'
        with self.assertRaises(SystemExit) as cm:
            cli.main(["", "scan", "--category", "password",
                      "--dotenv", self.dotenv,
                      "--force", repo_url])
        self.assertEqual(cm.exception.code, 9)

    def test_scan_local(self):
        tmp_path = tempfile.mkdtemp()
        repo_url = 'https://github.com/fabiosangregorio/credential-digger-tests'
        repo_path = os.path.join(tmp_path, "tmp_repo")
        GitRepo.clone_from(repo_url, repo_path)

        with self.assertRaises(SystemExit) as cm:
            cli.main(["", "scan", "--dotenv", self.dotenv,
                      "--models", "PathModel", "SnippetModel",
                      "--category", "password",
                      "--force", "--local", repo_path])
        self.assertEqual(cm.exception.code, 4)

    def test_scan_wiki(self):
        repo_url = 'https://github.com/fabiosangregorio/credential-digger-tests'

        with self.assertRaises(SystemExit) as cm:
            cli.main(["", "scan_wiki", "--dotenv", self.dotenv,
                      "--category", "password", repo_url])
        self.assertEqual(cm.exception.code, 5)
