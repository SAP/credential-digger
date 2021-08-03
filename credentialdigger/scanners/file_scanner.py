import logging
import os
import shutil
import sys
import tempfile
from fnmatch import fnmatch

import hyperscan

from .base_scanner import BaseScanner, ResultHandler

logger = logging.getLogger(__name__)


class FileScanner(BaseScanner):
    def __init__(self, rules):
        """ Create the scanner for a local directory or file.

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

    def scan(self, scan_path, max_depth=-1, ignore_list=[], debug=False,
             **kwargs):
        """ Scan a directory.

        Parameters
        ----------
        scan_path: str
            The path (either absolute or relative) of a file or directory to
            scan
        max_depth: int, optional
            The maximum depth to which traverse the subdirectories tree.
            A negative value will not affect the scan.
        ignore_list: list, optional
            A list of paths to ignore during the scan. This can include file
            names, directory names, or whole paths. Wildcards are supported as
            per the fnmatch package.
        debug: bool, optional
            If True, visualize debug information during the scan
        kwargs: kwargs
            Keyword arguments to be passed to the scanner

        Returns
        -------
        list
            A list of discoveries (dictionaries). If there are no discoveries
            return an empty list

        Raises
        ------
        FileNotFoundError
            If the given path is not an existing directory
        """
        if debug:
            logger.setLevel(level=logging.DEBUG)
        # Ensure that `dir_path` is treated as an absolute path
        scan_path = os.path.abspath(scan_path)
        if not os.path.exists(scan_path):
            raise FileNotFoundError(
                f'{scan_path} is not an existing directory.')

        # Copy directory/file to temp folder
        project_root = tempfile.mkdtemp().rstrip(os.path.sep)
        if os.path.isdir(scan_path):
            project_root = os.path.join(project_root, 'repo')
            shutil.copytree(scan_path, project_root)
        else:
            shutil.copy(scan_path, project_root)

        all_discoveries = []

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
                logger.debug(f'Scan file {rel_file_path}')
                file_discoveries = self.scan_file(
                    project_root=project_root, relative_path=rel_file_path)
                all_discoveries.extend(file_discoveries)

        # Delete temp folder
        shutil.rmtree(project_root)

        # Generate a list of discoveries and return it.
        # NOTE: this may become inefficient when the discoveries are many.
        return all_discoveries

    def scan_file(self, project_root, relative_path, **kwargs):
        """ Scan a single file for discoveries.

        Parameters
        ----------
        project_root: str
            Root path of the scanned project
        relative_path: str
            Path of the file, relative to `project_root`
        kwargs: kwargs
            Keyword arguments to be passed to the scanner

        Returns
        -------
        list
            A list of discoveries (dictionaries). If there are no discoveries
            return an empty list
        """
        discoveries = []
        line_number = 1

        # If branch_or_commit is passed, then it's a scan_snapshot
        # The branch_or_commit is the same for every file to be scanned
        commit_id = ''
        if kwargs:
            commit_id = kwargs.get('branch_or_commit', '')

        full_path = os.path.join(project_root, relative_path)
        try:
            with open(full_path, 'r', encoding='utf-8') as file_to_scan:
                for row in file_to_scan:
                    rh = ResultHandler()
                    self.stream.scan(
                        row if sys.version_info < (3, 9) else row.encode(
                            'utf-8'),
                        match_event_handler=rh.handle_results,
                        context=[row.strip(), relative_path, commit_id,
                                 line_number]
                    )
                    if rh.result:
                        discoveries.append(rh.result)
                    line_number += 1
        except UnicodeDecodeError:
            # Don't scan binary files
            pass
        return discoveries

    def _prune(self, rel_dir_root, dirs, files, max_depth=-1, ignore_list=[]):
        """ Prune files and directories lists based on different parameters.

        NOTE: files and directories removal is done in-place in the `dirs` and
        `files` lists, as this is needed by `os.walk()`.

        Parameters
        ----------
        rel_dir_root: str
            Path of the root of subdirectories contained in `dirs`, relative to
            the project root path
        dirs: list
            List of subdirectories in the current directory
        files: list
            List of files in the current directory
        max_depth: int, optional
            The maximum depth to which traverse the subdirectories tree.
            A negative value will not affect the scan.
        ignore_list: list, optional
            A list of paths to ignore during the scan. This can include file
            names, directory names, or whole paths. Wildcards are supported as
            per the fnmatch package.
        """
        # Prune directories with regard to `max_depth` parameter
        if max_depth > -1:
            curr_depth = rel_dir_root.lstrip(os.path.sep).count(os.path.sep)
            if curr_depth >= max_depth:
                del dirs[:]

        updated_dirs = [d for d in dirs]
        updated_files = [f for f in files]

        # Prune directories in `ignore_list`
        for dir_name in dirs:
            dir_path = os.path.join(rel_dir_root, dir_name)
            if any([fnmatch(dir_path, pattern) for pattern in ignore_list]):
                updated_dirs.remove(dir_name)

        # Prune files in `ignore_list`
        for file_name in files:
            file_path = os.path.join(rel_dir_root, file_name)
            if any([fnmatch(file_path, pattern) for pattern in ignore_list]):
                updated_files.remove(file_name)

        # Removing the items is done in-place as this is needed by os.walk()
        files[:] = updated_files[:]
        dirs[:] = updated_dirs[:]
