"""
The 'hook' module can be used to run credential digger as a pre-commit hook.
It detects hardcoded secrets in staged files.

NOTE: It uses SQLite and the discoveries are saved (by default)
in /home/USER/.local/data.db

usage: credentialdigger hook [-h] [--dotenv DOTENV] [--rules RULES]
                             [--db_path DB_PATH] [--no_interaction]

optional arguments:
  -h, --help         show this help message and exit
  --dotenv DOTENV    The path to the .env file which will be used in all
                     commands. If not specified, the one in the current
                     directory will be used (if present).
  --rules RULES      Specify the yaml file path containing the scan rules
                     e.g., /path/to/rules.yaml
  --db_path DB_PATH  Specify the database file path where to save the results
                     e.g., /path/to/data.db
  --no_interaction   Flag used to remove the interaction i.e.,
                     do not prompt if the commit should continue
                     in case of discoveries. If specified, the hook will
                     fail in case of discoveries.
"""

import subprocess
import sys
from pathlib import Path

from credentialdigger import SqliteClient
from credentialdigger.models.model_manager import ModelManager


def configure_parser(parser):
    """ Configure arguments for command line parser.

    Parameters
    ----------
    parser: `credentialdigger.cli.customParser`
        Command line parser
    """
    parser.set_defaults(func=run)


def system(*args, **kwargs):
    """Run a command and get the result."""
    kwargs.setdefault('stdout', subprocess.PIPE)
    proc = subprocess.Popen(args, **kwargs)
    out, err = proc.communicate()
    return out


def print_msg(msg):
    """Print messages to /dev/tty"""
    subprocess.run(f'echo \"\n{msg}\n\" > /dev/tty',
                   shell=True,
                   stdout=subprocess.PIPE)


def ask_commit(str_discoveries):
    """Ask for the commit confirmation in case of possible leaks"""

    msg = 'You have the following disoveries:\n' \
          f'{str_discoveries}\ncontinue? (y/n)'
    print_msg(msg)

    sys.stdin = open('/dev/tty', 'r')
    # Create a process on /dev/tty to capture the input (commit or not)
    # It reads the input, saves it in userinput and echos it
    # subprocess.check_output return the output of the command i.e., userinpput
    user_input = subprocess.check_output('read -p \"\" userinput && echo '
                                         '\"$userinput\"',
                                         shell=True, stdin=sys.stdin).rstrip()

    return user_input.decode('utf-8')


def run(args):
    """Run credential digger on staged files

    Parameters
    ----------
    args: `argparse.Namespace`
        Arguments from command line parser.

    Returns
    -------
        It exits with success code 0 if there are no discoveries, otherwise
        it exits with an error code != 0 printing the leaks
    """

    files_status = system('git', 'diff', '--name-status', '--staged'
                          ).decode('utf-8').splitlines()
    files = []
    for fs in files_status:
        stats = fs.split()
        status = stats[0]
        # Takes the last filename which is, in case of renamed files,
        # the new name
        filename = stats[-1]
        # D = deleted files
        # R = renamed files
        # It considers the first char because the renamed files are displayed
        # as Rxxx where xxx is a number
        if status[0] not in 'DR':
            files.append(filename)

    if args.db_path:
        db_path = args.db_path
    else:
        db_path = str(Path.home() / '.local' / 'data.db')

    c = SqliteClient(path=db_path)

    if args.rules:
        c.add_rules_from_file(args.rules)
    elif not c.get_rules():
        c.add_rules_from_file('./ui/backend/rules.yml')

    new_discoveries = []
    subprocess.run(f'echo \"\nChecking files={files} \" > /dev/tty',
                   shell=True,
                   stdout=subprocess.PIPE)

    # For optimization purposes, the PathModel and the PasswordModel are
    # separated, otherwise scan_path will call both models for each file
    # With this implementation the discoveries are accumulated and the
    # PasswordModel will be used only once for the password discoveries
    for file in files:
        new_discoveries += c.scan_path(scan_path=file,
                                       models=['PathModel'],
                                       force=True,
                                       debug=False)

    if not new_discoveries:
        print_msg('No hardcoded secrets found in your commit')
        sys.exit(0)

    rules = c.get_rules()
    password_rules = set([
        r['id'] for r in rules if r['category'] == 'password'])
    password_discoveries = []
    no_password_discoveries = []
    for d in new_discoveries:
        disc = c.get_discovery(d)
        if disc['rule_id'] in password_rules:
            password_discoveries.append(disc)
        else:
            no_password_discoveries.append(disc)

    # Run the PasswordModel
    disc = []
    if password_discoveries:
        mm = ModelManager('PasswordModel')
        disc = c._analyze_discoveries(mm, password_discoveries, debug=False)

    list_of_discoveries = []
    for d in disc:
        if d['state'] == 'new':
            list_of_discoveries.append(d)

    # If there are keys, token ...
    list_of_discoveries += no_password_discoveries
    # If all the discoveries were false positive discoveries
    if not list_of_discoveries:
        print_msg('No hardcoded secrets found in your commit')
        sys.exit(0)

    str_discoveries = ''
    for d in list_of_discoveries:
        str_discoveries += (f'file: {d["file_name"]}\n'
                            f'secret: {d["snippet"]}\n'
                            f'line number: {d["line_number"]}\n' +
                            40 * '-')

    if not args.no_interaction and \
       ask_commit(str_discoveries).startswith(('y', 'Y')):
        print_msg('Committing...')
        sys.exit(0)
    sys.exit(1)
