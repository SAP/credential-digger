import os
import shutil
import tempfile
import unittest

from credentialdigger.cli import cli
from git import Repo as GitRepo
from parameterized import param, parameterized
from psycopg2 import connect

TOTAL_PW_DISCOVERIES = 11


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
        self.assertEqual(cm.exception.code, TOTAL_PW_DISCOVERIES)

    def test_scan_local(self):
        repo_path = tempfile.mkdtemp()
        GitRepo.clone_from(self.repo_url, repo_path)

        with self.assertRaises(SystemExit) as cm:
            cli.main(["", "scan", "--dotenv", self.dotenv,
                      "--models", "PathModel", "PasswordModel",
                      "--category", "password",
                      "--force", repo_path])
        # When using the models, we expect to be left with less than
        # TOTAL_PW_DISCOVERIES discoveries to manually review
        self.assertTrue(cm.exception.code < TOTAL_PW_DISCOVERIES)

        shutil.rmtree(repo_path)

    def test_scan_wiki(self):
        with self.assertRaises(SystemExit) as cm:
            cli.main(["", "scan_wiki", "--dotenv", self.dotenv,
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
            cli.main(["", "scan_pr", "--dotenv", self.dotenv,
                      "--category", "password",
                      "--pr", str(pr_num),
                      self.repo_url])
            # pr_num needed to be cast to str not to raise TypeError here, but
            # its type will later be managed by the scanner
        self.assertEqual(cm.exception.code, leaks)
