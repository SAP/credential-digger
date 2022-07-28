import logging
from github import Github

from .git_scanner import GitScanner

logger = logging.getLogger(__name__)


class GitPRScanner(GitScanner):
    def __init__(self, rules):
        """ Create the scanner for a git repository.

        The scanner compiles a list of rules, and uses hyperscan for regular
        expression matching.

        Parameters
        ----------
        rules: list
            A list of rules
        """
        super().__init__(rules)
        self.stream = rules

    def get_commits_from_pr(self, user_name, repo_name, pr_number, token=None,
                            api_endpoint='https://api.github.com'):
        """ TODO """
        g = Github(login_or_token=token, base_url=api_endpoint)
        logger.debug(f'Get commits of PR {pr_number} from '
                     f'{user_name}/{repo_name}')
        commits = g.get_user(user_name).get_repo(repo_name).get_pull(
            int(pr_number))
        return commits.get_commits()

    def scan(self, repo_url, pr_number, api_endpoint='https://api.github.com',
             git_token=None, debug=False, **kwargs):
        """ Scan a pull request.

        Differently from other scanners, here local repos are not supported
        because pull requests need a remote (indeed, locally, only merge is
        allowed).

        TODO
        """
        if debug:
            logger.setLevel(level=logging.DEBUG)

        # Retrieve user_name and repo_name from repository url
        user_name, repo_name = repo_url.split('/')[-2:]
        logger.debug(f'Repo {user_name}/{repo_name}')

        # Get commits part of this PR
        commits = self.get_commits_from_pr(user_name, repo_name, pr_number,
                                           git_token, api_endpoint)
        logger.debug(f'Found {commits.totalCount} commits in this PR')

        detections = []
        for commit in commits:
            logger.debug(f'scan commit {commit}')
            # Use `raw_data` because it only consumes 1 api call
            files = commit.raw_data['files']
            logger.debug(f'There are {len(files)} files in this commit')
            for committed_file in files:
                if 'patch' not in committed_file:
                    # Empty file
                    continue
                patch = committed_file['patch']
                detections = detections + self._regex_check(
                    patch, committed_file['filename'], commit.sha)

        logger.info(f'Found {len(detections)} candidate results')
        return detections
