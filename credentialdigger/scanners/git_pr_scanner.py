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

    def scan(self, repo_url, user_name, repo_name, pr_number,
             git_token=None, api_endpoint='https://api.github.com',
             debug=False):
        """ TODO

        Local repos are not supported because pull requests can't be treated
        locally. They need a remote ()

        """
        if debug:
            logger.setLevel(level=logging.DEBUG)

        # Get commits part of this PR
        commits = self.get_commits_from_pr(user_name, repo_name, pr_number,
                                           git_token, api_endpoint)
        logger.debug(f'Found {commits.totalCount} commits in this PR')

        detections = []
        for commit in commits:
            logger.debug(f'scan commit {commit}')
            # Use `raw_data` because it only consumes 1 api call
            files = commit.raw_data['files']
            print(f'There are {len(files)} files in this commit')
            for committed_file in files:
                if 'patch' not in committed_file:
                    # Empty file
                    continue
                patch = committed_file['patch']
                # for line in patch.split('\n'):
                #     if line[0] == '+':
                #         # If the line starts with a '+' then this line is new
                #         if category := _scan(line[1:].strip()):
                #             results.append(
                #                 {
                #                     'snippet': line[1:].strip(),
                #                     'file_name': committed_file['filename'],
                #                     'link': committed_file['raw_url'],
                #                     'category': category
                #                 }
                #             )
                detections = detections + self._regex_check(
                    patch, committed_file['filename'], commit.sha)

        logger.info(f'Found {len(detections)} candidate results')
        return detections
