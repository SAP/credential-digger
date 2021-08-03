import logging
import os
import shutil

import hyperscan

from .file_scanner import FileScanner
from .git_scanner import GitScanner

logger = logging.getLogger(__name__)


class GitFileScanner(GitScanner, FileScanner):
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

    @property
    def stream(self):
        return self._stream

    @stream.setter
    def stream(self, rules):
        """ Load the hyperscan database. """
        self._stream = hyperscan.Database(mode=hyperscan.HS_MODE_BLOCK)
        patterns = []
        for r in rules:
            rule_id, rule, _, _ = r.values()
            patterns.append((rule.encode('utf-8'),
                             rule_id,
                             hyperscan.HS_FLAG_CASELESS |
                             hyperscan.HS_FLAG_UTF8 |
                             hyperscan.HS_FLAG_UCP))

        expressions, ids, flags = zip(*patterns)
        self._stream.compile(expressions=expressions,
                             ids=ids,
                             elements=len(patterns),
                             flags=flags)

    def scan(self, repo_url, branch_or_commit, max_depth=-1, ignore_list=[],
             git_token=None, debug=False, **kwargs):
        """ Scan a repository.

        Parameters
        ----------
        repo_url: str
            The location of a git repository (an url if local_repo is False, a
            local path otherwise)
        branch_or_commit: str
            Specific commit (or last commit of a specific branch name) where
            the whole repository will be scanned
        max_depth: int, optional
            The maximum depth to which traverse the subdirectories tree.
            A negative value will not affect the scan.
        ignore_list: list, optional
            A list of paths to ignore during the scan. This can include file
            names, directory names, or whole paths. Wildcards are supported as
            per the fnmatch package.
        git_token: str, optional
            Git personal access token to authenticate to the git server
        debug: bool, optional
            If True, visualize debug information during the scan
        kwargs: kwargs
            Keyword arguments to be passed to the scanner

        Returns
        -------
        list
            A list of discoveries (dictionaries). If there are no discoveries
            return an empty list
        """
        if debug:
            logger.setLevel(level=logging.DEBUG)
        if git_token:
            logger.debug('Authenticate user with token')
            repo_url = repo_url.replace('https://',
                                        f'https://oauth2:{git_token}@')

        # Clone the repository locally
        # TODO: add support for local repositories
        #       As long as that feature is not integrated yet, local_repo must
        #       be set to False
        project_path, repo = self.get_git_repo(repo_url, local_repo=False)

        # Scan the snapshot of the repository either at the last commit of
        # a branch or at a specific commit
        discoveries = self._scan(
            repo, branch_or_commit, max_depth, ignore_list)

        # Delete repo folder
        shutil.rmtree(project_path)

        # Generate a list of discoveries and return it.
        # N.B.: This may become inefficient when the discoveries are many.
        return discoveries

    def _scan(self, repo, branch_or_commit, max_depth=-1, ignore_list=[]):
        """ Perform the actual scan of the snapshot of the repository.

        Parameters
        ----------
        repo: `git.GitRepo`
            The repository object
        branch_or_commit: str
            Specific commit (or last commit of a specific branch name) where
            the whole repository will be scanned
        max_depth: int, optional
            The maximum depth to which traverse the subdirectories tree.
            A negative value will not affect the scan.
        ignore_list: list, optional
            A list of paths to ignore during the scan. This can include file
            names, directory names, or whole paths. Wildcards are supported as
            per the fnmatch package.

        Returns
        -------
        list
            A list of discoveries (dictionaries). If there are no discoveries
            return an empty list
        """
        # Move to branch/commit
        logger.debug(f'Checkout {branch_or_commit}')
        repo.git.checkout(branch_or_commit)

        scan_kwargs = {'branch_or_commit': branch_or_commit}
        all_discoveries = []

        project_root = repo.working_tree_dir
        # Walk the directory tree and scan files
        for abs_dir_root, dirs, files in os.walk(project_root):
            rel_dir_root = abs_dir_root[len(project_root):].lstrip(os.path.sep)

            # Prune unwanted files and subdirectories
            self._prune(rel_dir_root, dirs, files,
                        max_depth=max_depth,
                        ignore_list=ignore_list)

            # Scan remaining files
            for file_name in files:
                rel_file_path = os.path.join(rel_dir_root, file_name)
                file_discoveries = self.scan_file(
                    project_root=project_root, relative_path=rel_file_path,
                    **scan_kwargs)
                all_discoveries.extend(file_discoveries)

        return all_discoveries
