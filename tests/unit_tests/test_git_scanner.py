import unittest

from credentialdigger.scanners.git_scanner import GitScanner


class TestGitScanner(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Instantiate the scanner with only the password-related rules
        rules = [{'id': 9, 'regex': 'sshpass|password|pwd|passwd|pass',
                  'category': 'password', 'description': 'password keywords'}]
        cls.git_scanner = GitScanner(rules)

    def test_regex_check_line_number(self):
        """ Test the line number of a discovery """
        diff = "\n".join(["@@ -120 +109,2 @@",
                          "- some_removed_text",
                          "+ some_added_text",
                          "+ password",
                          "@@ -130 +130 @@",
                          "+ another password"])
        discoveries = self.git_scanner._regex_check(diff, "", "")
        first_discovery = discoveries[0]
        second_discovery = discoveries[1]
        self.assertEqual(first_discovery['line_number'], 110)
        self.assertEqual(second_discovery['line_number'], 130)

    def test_regex_check_deletion(self):
        """ Test that a deletion should not generate a discovery """
        diff = "\n".join(["@@ -120,1 +120 @@",
                          "- some_removed_text"])
        discoveries = self.git_scanner._regex_check(diff, "", "")
        self.assertEqual(len(discoveries), 0)
