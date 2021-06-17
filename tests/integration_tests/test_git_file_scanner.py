import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from credentialdigger.scanners.git_file_scanner import GitFileScanner
from git import GitCommandError, InvalidGitRepositoryError
from git import Repo as GitRepo
from parameterized import parameterized

import pytest

class TestGitFileScanner(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Instantiate the scanner with only the password-related rules
        rules = [{'id': 9, 'regex': 'sshpass|password|pwd|passwd|pass',
                  'category': 'password', 'description': 'password keywords'}]
        cls.git_file_scanner = GitFileScanner(rules)

        # Clone the test repository from Github
        repo_url = 'https://github.com/SAP/credential-digger-tests'
        cls.tmp_path = tempfile.mkdtemp()
        GitRepo.clone_from(repo_url, cls.tmp_path)
        cls.repo = GitRepo(cls.tmp_path)

    @classmethod
    def tearDownClass(cls):
        # Delete repo folder
        shutil.rmtree(cls.tmp_path)

    @parameterized.expand([
        'https://:@github.com/SAP/inexistent-repo',
        'not_a_url',
        'https://nonexistent.url'])
    @patch('credentialdigger.scanners.git_file_scanner.GitRepo.clone_from')
    def test_get_git_repo_invalid_url(self, url, mock_clone_from):
        """ Test raised exception on repo clone with invalid urls.

        Any Github urls must be prefixed with `:@` (empty username and password)
        in order to prevent GitPython from asking credentials in an interactive
        shell when running the test.
        """
        mock_clone_from.side_effect = GitCommandError([''], '')
        with self.assertRaises(GitCommandError):
            self.git_file_scanner.get_git_repo(url, local_repo=False)

# TODO: re-enable this method in case we'll support the scan of snapshots of
# local repositories
#
#     def test_get_git_repo_local_invalid(self):
#         """ Test repo copy with invalid paths """
#         # Inexistent path
#         with self.assertRaises(FileNotFoundError):
#             self.git_file_scanner.get_git_repo('./inexistent_path', local_repo=True)
#         # Non-repo path
#         with self.assertRaises(InvalidGitRepositoryError):
#             self.git_file_scanner.get_git_repo(
#                 './credentialdigger', local_repo=True)

    @parameterized.expand([
        'tests',                                      # Branch tests
        '09c75495f6a8ca7c3438dca034b46472c0901dc6',   # Commit in branch main
        'e6b8d00e28b8b4e27ae9fc17067247ba08fe0be6'])  # Commit in branch tests
    def test_scan_snapshot(self, mock_branch_or_commit):
        """ Test discoveries count of branch `tests`.

        We know that they are at least 9.
        """
        discoveries = self.git_file_scanner._scan(
            self.repo,
            branch_or_commit=mock_branch_or_commit,
            max_depth=1000000)
        self.assertGreaterEqual(len(discoveries), 9)

    def test_scan_snapshot_initial_commit(self):
        """ Test discoveries count of the initial commit.

        We know that they are 0, since there was only the LICENSE file.
        """
        commit_id = '91c0008384b0313e75be76ee30a9ae0e0b11e31a'
        discoveries = self.git_file_scanner._scan(
            self.repo, branch_or_commit=commit_id, max_depth=1000000)
        self.assertEqual(len(discoveries), 0)

    # TODO: test_scan_invalid_snapshot (with wrong branch name and commit id)
