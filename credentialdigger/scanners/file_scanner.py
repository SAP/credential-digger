import logging
import os
import shutil
import tempfile
from datetime import datetime, timezone

import hyperscan

from base_scanner import BaseScanner, ResultHandler

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

    def scan(self, dir_path, since_timestamp=0, max_depth=20, ignore_list=[]):
        """ Scan a directory.

        TODO: docs
        """
        if not os.path.exists(dir_path):
            raise FileNotFoundError(
                f"{dir_path} is not an existing directory.")

        # Copy directory/file to temp folder
        project_path = tempfile.mkdtemp()
        shutil.copytree(dir_path, project_path, dirs_exist_ok=True)

        # IMPROVE: this may become inefficient when the discoveries are many.
        # Use generators or iter()
        all_discoveries = []

        # TODO: add `max_depth` handling
        for root, dirs, files in os.walk(project_path):
            # Prune unwanted files and subdirectories
            self._prune(root, dirs, files, ignore_list, since_timestamp)

            for file_name in files:
                file_path = root + file_name

                # IMPROVE: get hash of file and scan it only if it not in
                # `already_scanned`
                # IMPROVE: add per-file multiprocessing
                file_discoveries = self.scan_file(file_path)

                all_discoveries.append(file_discoveries)

        # Delete temp folder
        shutil.rmtree(project_path)

        # Generate a list of discoveries and return it.
        now_timestamp = int(datetime.now(timezone.utc).timestamp())
        return now_timestamp, all_discoveries

    def scan_file(self, file_path):
        discoveries = []
        line_number = 1

        with open(file_path, "r") as file_to_scan:
            for row in file_to_scan:
                rh = ResultHandler()
                self.stream.scan(row,
                                 match_event_handler=rh.handle_results,
                                 context=[row, file_path, None, line_number])
                if rh.result:
                    discoveries.append(rh.result)
                line_number += 1
        return discoveries

    def _prune(self, root, dirs, files, ignore_list, since_timestamp):
        """
        TODO: docs
        NOTE: removing the items is done in-place as it is needed by os.walk()
        """
        for file_name in files:
            file_path = root + file_name
            print(file_path)

            # TODO: prune files and subdirectories in `ignore_list`
            # TODO: prune binary/non-text files

            # Remove the file if it has not been modified since given timestamp
            last_edited_time = os.path.getmtime(file_path)
            if last_edited_time < since_timestamp:
                files.remove(file_name)
