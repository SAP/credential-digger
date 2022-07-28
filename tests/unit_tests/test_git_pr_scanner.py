import unittest

from credentialdigger.scanners.git_pr_scanner import GitPRScanner
from github import UnknownObjectException
from parameterized import param, parameterized


class TestGitPRScanner(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """ Instantiate the scanner with only the password-related rules """
        # Instantiate the scanner with only the password-related rules
        rules = [{'id': 9, 'regex': 'sshpass|password|pwd|passwd|pass',
                  'category': 'password', 'description': 'password keywords'}]
        cls.pr_scanner = GitPRScanner(rules)

    @parameterized.expand([
        param(user_name='SAP-error',
              repo_name='credential-digger-tests',
              pr_number=1),
        param(user_name='SAP',
              repo_name='credential-digger-tests-error',
              pr_number=1),
        param(user_name='SAP',
              repo_name='credential-digger-tests',
              pr_number=-1)
    ])
    def test_get_commits_from_pr_error(self, user_name, repo_name, pr_number):
        """ Test get_commit_from_pr failure with nonexistent repository or
        pull request numer """
        with self.assertRaises(UnknownObjectException):
            # self.pr_scanner.scan(user_name, repo_name, pr_number)
            self.pr_scanner.get_commits_from_pr(
                user_name, repo_name, pr_number)

    @parameterized.expand([
        param(user_name='SAP',
              repo_name='credential-digger-tests',
              pr_number=1,
              commits_nr=4),
        param(user_name='SAP',
              repo_name='credential-digger-tests',
              pr_number=2,
              commits_nr=1)
    ])
    def test_get_commits_from_pr(self, user_name, repo_name, pr_number,
                                 commits_nr):
        """ Test get_commit_from_pr execution with open pr on our test
        repository """
        self.assertEqual(
            self.pr_scanner.get_commits_from_pr(
                user_name, repo_name, pr_number).totalCount,
            commits_nr
        )
