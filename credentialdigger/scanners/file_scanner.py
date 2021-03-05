import logging
import os
import shutil
import tempfile

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

    def scan(self, dir_path, max_depth=-1, ignore_list=[]):
        """ Scan a directory.

        TODO: docs
        """
        dir_path = os.path.abspath(dir_path)
        if not os.path.exists(dir_path):
            raise FileNotFoundError(
                f"{dir_path} is not an existing directory.")

        # Copy directory/file to temp folder
        project_path = tempfile.mkdtemp().rstrip(os.path.sep)
        shutil.copytree(dir_path, project_path, dirs_exist_ok=True)

        all_discoveries = []
        initial_depth = project_path.count(os.path.sep)

        for root, dirs, files in os.walk(project_path):
            # Prune unwanted files and subdirectories
            self._prune(root, dirs, files, initial_depth,
                        max_depth=max_depth,
                        ignore_list=ignore_list)

            for file_name in files:
                file_path = os.path.join(root, file_name)
                file_discoveries = self.scan_file(file_path, project_path)
                all_discoveries.extend(file_discoveries)

        # Delete temp folder
        shutil.rmtree(project_path)

        # Generate a list of discoveries and return it.
        # NOTE: this may become inefficient when the discoveries are many.
        return all_discoveries

    def scan_file(self, file_path, project_root):
        discoveries = []
        line_number = 1
        relative_path = file_path.lstrip(project_root)

        try:
            with open(file_path, "r", encoding='utf-8') as file_to_scan:
                for row in file_to_scan:
                    rh = ResultHandler()
                    self.stream.scan(
                        row,
                        match_event_handler=rh.handle_results,
                        context=[row, relative_path, "", line_number])
                    if rh.result:
                        discoveries.append(rh.result)
                    line_number += 1
        except UnicodeDecodeError:
            # Don't scan binary files
            pass
        return discoveries

    def _prune(self, root, dirs, files, initial_depth, max_depth=-1,
               ignore_list=[]):
        """
        TODO: docs
        """
        updated_dirs = [d for d in dirs]
        updated_files = [f for f in files]

        # Prune directories
        if max_depth > -1:
            curr_depth = root.count(os.path.sep)
            if curr_depth >= initial_depth + max_depth:
                del updated_dirs[:]

        # # Prune files
        # for file_name in files:
        #     file_path = os.path.join(root, file_name)

        #     # TODO: prune files and subdirectories in `ignore_list`

        # Removing the items is done in-place as this is needed by os.walk()
        files[:] = updated_files[:]
        dirs[:] = updated_dirs[:]
