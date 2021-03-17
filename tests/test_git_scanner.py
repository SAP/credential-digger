import shutil
import tempfile
import unittest
from datetime import datetime, timezone

from credentialdigger.scanners.git_scanner import GitScanner
from git import GitCommandError, InvalidGitRepositoryError
from git import Repo as GitRepo
from parameterized import param, parameterized


class TestGitScanner(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Instantiate the scanner with only the password-related rules
        rules = [{'id': 9, 'regex': 'sshpass|password|pwd|passwd|pass',
                  'category': 'password', 'description': 'password keywords'}]
        cls.git_scanner = GitScanner(rules)

        # Clone the test repository from Github
        repo_url = 'https://github.com/fabiosangregorio/credential-digger-tests'
        cls.tmp_path = tempfile.mkdtemp()
        GitRepo.clone_from(repo_url, cls.tmp_path)
        cls.repo = GitRepo(cls.tmp_path)

    @classmethod
    def tearDownClass(cls):
        # Delete repo folder
        shutil.rmtree(cls.tmp_path)

    @parameterized.expand([
        "https://:@github.com/SAP/inexistent-repo",
        "not_a_url",
        "https://nonexistent.url"])
    def test_get_git_repo_invalid_url(self, url):
        """ Test raised exception on repo clone with invalid urls

        Any Github urls must be prefixed with `:@` (empty username and password)
        in order to prevent GitPython from asking credentials in an interactive
        shell when running the test
        """
        with self.assertRaises(GitCommandError):
            self.git_scanner.get_git_repo(url, local_repo=False)

    def test_get_git_repo_local_invalid(self):
        """ Test repo copy with invalid paths """
        # Inexistent path
        with self.assertRaises(FileNotFoundError):
            self.git_scanner.get_git_repo('./inexistent_path', local_repo=True)
        # Non-repo path
        with self.assertRaises(InvalidGitRepositoryError):
            self.git_scanner.get_git_repo(
                './credentialdigger', local_repo=True)

    def test_scan_since_timestamp_now(self):
        """ Test that there are no new discoveries if scanning from now """
        timestamp = int(datetime.now(timezone.utc).timestamp())
        discoveries = self.git_scanner._scan(
            self.repo, max_depth=1000000, since_timestamp=timestamp)
        self.assertEqual(len(discoveries), 0)

    def test_scan_since_timestamp_zero(self):
        """ Test discoveries count since beginning """
        discoveries = self.git_scanner._scan(
            self.repo, max_depth=1000000, since_timestamp=0)
        self.assertGreaterEqual(len(discoveries), 8)

    def test_scan_since_after_first_commit(self):
        """ Test only discoveries inserted after first commit """
        first_commit_hexsha = "ee06dc139ab360080734b3ee595e6f2627094968"
        first_commit_timestamp = 1615976544
        discoveries = self.git_scanner._scan(
            self.repo,
            max_depth=1000000,
            since_timestamp=first_commit_timestamp + 1)

        # We know that at least one discovery was inserted after first commit
        self.assertGreaterEqual(len(discoveries), 1)

        for d in discoveries:
            self.assertNotEqual(d['commit_id'], first_commit_hexsha)

    def test_regex_check_line_number(self):
        """ Test the line number of a discovery """
        diff = """@@ -120,1 +109,2 @@
                  - some_removed_text
                  + some_added_text
                  + password"""
        discovery = self.git_scanner._regex_check(diff, "", "")[0]
        self.assertEqual(discovery['line_number'], 111)
