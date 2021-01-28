import hashlib
import re
import shutil
from datetime import datetime, timezone

import hyperscan
from git import NULL_TREE
from git import Repo as GitRepo

from .base_scanner import BaseScanner


class GitScanner(BaseScanner):

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

    def scan(self, git_url, since_timestamp=0, max_depth=1000000):
        """ Scan a repository.

        Parameters
        ----------
        git_url: string
            The url of a git repository
        since_timestamp: int, optional
            The oldest timestamp to scan
        max_depth: int, optional
            The maximum number of commits to scan

        Returns
        -------
        int
            The latest scan timestamp (now) (`None` if the repository is empty)
        list
            A list of discoveries (dictionaries). If there are no discoveries
            return an empty list
        """
        project_path = self.clone_git_repo(git_url)
        repo = GitRepo(project_path)

        already_searched = set()
        discoveries = []

        branches = repo.remotes.origin.fetch()

        for remote_branch in branches:
            branch_name = remote_branch.name
            prev_commit = None
            # Note that the iteration of the commits is backwards, so the
            # prev_commit is newer than curr_commit
            for curr_commit in repo.iter_commits(branch_name,
                                                 max_count=max_depth):
                if curr_commit.committed_date <= since_timestamp:
                    # We have reached the (chosen) oldest timestamp, so
                    # continue with another branch
                    break

                # if not prev_commit, then curr_commit is the newest commit
                # (and we have nothing to diff with).
                # But we will diff the first commit with NULL_TREE here to
                # check the oldest code. In this way, no commit will be missed.
                # This is useful for git merge: in case of a merge, we have the
                # same commits (prev and current) in two different branches.
                # This trick avoids scanning twice the same commits
                diff_hash = hashlib.md5((str(prev_commit) + str(curr_commit))
                                        .encode('utf-8')).digest()
                if not prev_commit:
                    # The current commit is the latest one
                    prev_commit = curr_commit
                    continue
                elif diff_hash in already_searched:
                    prev_commit = curr_commit
                    continue
                else:
                    # Get the diff between two commits
                    # Ignore possible submodules (they are independent from
                    # this repo)
                    diff = curr_commit.diff(prev_commit,
                                            create_patch=True,
                                            ignore_submodules='all',
                                            ignore_all_space=True,
                                            unified=0,
                                            diff_filter='AM')
                # Avoid searching the same diffs
                already_searched.add(diff_hash)
                # Diff between the current commit and the previous one
                discoveries = discoveries + self._diff_worker(diff,
                                                              prev_commit)
                prev_commit = curr_commit

            # Handling the first commit (either from since_timestamp or the
            # oldest).
            # If `since_timestamp` is set, then there is no need to scan it
            # (because we have already scanned this diff at the previous step).
            # If `since_timestamp` is 0, we have reached the first commit of
            # the repo, and the diff here must be calculated with an empty tree
            if since_timestamp == 0:
                diff = curr_commit.diff(NULL_TREE,
                                        create_patch=True,
                                        ignore_submodules='all',
                                        ignore_all_space=True)

                discoveries = discoveries + self._diff_worker(diff,
                                                              prev_commit)

        # Delete repo folder
        shutil.rmtree(project_path)

        now_timestamp = int(datetime.now(timezone.utc).timestamp())
        # Generate a list of discoveries and return it.
        # N.B.: This may become inefficient when the discoveries are many.
        return now_timestamp, discoveries

    def _diff_worker(self, diff, commit):
        """ Compute the diff between two commits.

        Parameters
        ----------
        diff: string
            The diff introduced by a commit
        commit: string
            The commit the diff is calculated on

        Returns
        -------
        list of dictionaries
            A list of discoveries
        """
        detections = []
        for blob in diff:
            # new file: a_path is None, deleted file: b_path is None
            old_path = blob.b_path if blob.b_path else blob.a_path

            printable_diff = blob.diff.decode('utf-8', errors='replace')

            if printable_diff.startswith('Binary files'):
                # Do not scan binary files
                continue

            detections = detections + self._regex_check(printable_diff,
                                                        old_path,
                                                        commit.hexsha)
        return detections

    def _regex_check(self, printable_diff, filename, commit_hash):
        """ Scan the diff with regexes.

        Here the scan is performed.
        Lines that are either longer than 500 characters or that are not newly
        added are not scanned. Indeed, if a line is scanned as soon as it is
        added to the file, there is no need to need to re-scan the same line
        when (and if) it gets deleted.
        In addition to this, lines longer than 500 characters usually represent
        the content of an entire file on the same line. This (almost always)
        produces a false positive discovery (thus we assume we can avoid
        scanning them).

        Parameters
        ----------
        printable_diff: string
            The diff of two commits
        filename: string
            The name of the file that contains the diff
        commit_hash: string
            The hash of the commit (from git)

        Returns
        -------
        list
            A list of dictionaries (each dictionary is a discovery)
        """
        detections = []
        r_hunkheader = re.compile(r"@@\s*\-\d+(\,\d+)?\s\+(\d+)((\,\d+)?).*@@")
        r_hunkaddition = re.compile(r"^\+\s*(\S(.*\S)?)\s*$")
        rows = printable_diff.splitlines()
        line_number = 1
        for row in rows:
            if row.startswith('-') or len(row) > 500:
                # Take into consideration only added lines that are shorter
                # than 500 characters
                continue
            if row.startswith('@@'):
                # If the row is a git diff hunk header, get the first addition
                # line number in the header and go to the next line
                r_groups = re.search(r_hunkheader, row)
                if r_groups is not None:
                    line_number = int(r_groups.group(2))
                    continue
            elif row.startswith('+'):
                # Remove '+' character from diff hunk and trim row
                r_groups = re.search(r_hunkaddition, row)
                if r_groups is not None:
                    row = r_groups.group(1)

            rh = ResultHandler()
            self.stream.scan(row,
                             match_event_handler=rh.handle_results,
                             context=[row, filename, commit_hash, line_number])
            if rh.result:
                detections.append(rh.result)
            line_number += 1
        return detections


class ResultHandler:

    def __init__(self):
        self.result = None

    def handle_results(self, eid, start, end, flags, context):
        """ Give a structure to the discovery and store it in a variable.

        This method is needed in order to process the result of a scan (it is
        used as a callback function).

        Parameters
        ----------
        eid: int
            The id of the regex that produced the discovery
        start: int
            The start index of the match
        end: int
            The end index of the match
        flags
            Not implemented by the library
        context: list
            Metadata (composed by snippet, filename, hash, line_number)
        """
        snippet, filename, commit_hash, line_number = context

        meta_data = {'file_name': filename,
                     'commit_id': commit_hash,
                     'line_number': line_number,
                     'snippet': snippet,
                     'rule_id': eid,
                     'state': 'new'}

        self.result = meta_data
