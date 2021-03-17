import os
import shutil
import unittest

from credentialdigger.scanners.git_scanner import GitScanner
from git import GitCommandError, InvalidGitRepositoryError
from parameterized import param, parameterized


class TestGitScanner(unittest.TestCase):
    repo_path = 'https://github.com/fabiosangregorio/credential-digger-tests'

    @classmethod
    def setUpClass(cls):
        """ Instantiate the scanner with only the password-related rules """
        rules = [{'id': 9, 'regex': 'sshpass|password|pwd|passwd|pass',
                  'category': 'password', 'description': 'password keywords'}]
        cls.git_scanner = GitScanner(rules)

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
