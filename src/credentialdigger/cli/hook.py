"""
The 'hook' module can be used to run credential digger as a pre-commit hook.
It detects hardcoded secrets in staged files blocking the commit before the
code gets public.

usage: credentialdigger hook [-h] [--dotenv DOTENV] [--sqlite SQLITE]
                             [--rules RULES] [--no_interaction]

optional arguments:
  -h, --help         show this help message and exit
  --dotenv DOTENV    The path to the .env file which will be used in all
                     commands. If not specified, the one in the current
                     directory will be used (if present).
  --sqlite SQLITE    If specified, scan the repo using the sqlite client
                     passing as argument the path of the db.
                     Otherwise, use postgres (must be up and running)
  --rules RULES      Specify the yaml file path containing the scan rules
                     e.g., /path/to/rules.yaml
  --no_interaction   Flag used to remove the interaction i.e.,
                     do not prompt if the commit should continue
                     in case of discoveries. If specified, the hook will
                     fail in case of discoveries.
"""

import subprocess
import sys
import os
from pathlib import Path

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
    """Print a message to /dev/tty."""
    subprocess.run(f'echo \"\n{msg}\n\" > /dev/tty',
                   shell=True,
                   stdout=subprocess.PIPE)


def ask_commit(str_discoveries):
    """Ask for the commit confirmation in case of possible leaks.

    Parameters
    ----------
    str_discoveries: str
        Discoveries formatted as a string
    """

    msg = 'You have the following disoveries:\n\n' \
          f'{str_discoveries}\nWould you like to commit anyway? (y/N)'
    print_msg(msg)

    sys.stdin = open('/dev/tty', 'r')
    # Create a process on /dev/tty to capture the input (commit or not)
    # It reads the input, saves it in userinput and echos it
    # subprocess.check_output return the output of the command i.e., userinpput
    user_input = subprocess.check_output('read -p \"\" userinput && echo '
                                         '\"$userinput\"',
                                         shell=True, stdin=sys.stdin).rstrip()

    return user_input.decode('utf-8')

def rmdir(directory):
    directory = Path(directory)
    for item in directory.iterdir():
        if item.is_dir():
            rmdir(item)
        else:
            item.unlink()
    directory.rmdir()

def run(client, args):
    """Run Credential Digger on staged files.

    Parameters
    ----------
    client: `credentialdigger.Client`
        Instance of the client on which to save results
    args: `argparse.Namespace`
        Arguments from command line parser.

    Returns
    -------
        While this function returns nothing, it gives an exit status (integer)
        that is equal to the number of discoveries causing the hook to fail.
        If it exits with a value that is equal to 0, then it means
        that the scan detected no leaks in the staged files, or it means,
        in case interaction, that the user choosed to commit even
        in case of leaks. If the exit value is 0 the hook is successful.
    """
    diff_path = os.path.join(os.path.expanduser('~'), '.credentialdigger' ,'diff')
    try:
        os.makedirs(diff_path, exist_ok=True)
        files_status = system('git', 'diff', '--name-status', '--staged'
                              ).decode('utf-8').splitlines()
        files = []
        for fs in files_status:
            stats = fs.split('\t')
            status = stats[0]
            # Check status using the first char
            # D = deleted files
            # R = renamed files
            if status[0] not in 'DR':
                # Get the name of the staged file
                filename = stats[1]
                files.append(filename)
        for staged_file in files:
            staged_file_path = os.path.join(diff_path, staged_file)
            os.makedirs(os.path.dirname(staged_file_path), exist_ok=True)
            with open(staged_file_path, 'w') as diff_file:
                proc = subprocess.Popen(['git', 'diff', '--cached', '--unified=0', staged_file],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, _ = proc.communicate()
                for line in stdout.decode('utf-8').splitlines():
                    if line.startswith('+') and not line.startswith('+++'):
                        diff_file.write(line[1:] + '\n')


        if args.rules:
            client.add_rules_from_file(args.rules)
        elif not client.get_rules():
            client.add_rules_from_file(os.path.join('.', 'ui', 'backend', 'rules.yml'))

        new_discoveries = []
        subprocess.run(f'echo \"\nChecking files={files} \" > /dev/tty',
                       shell=True,
                       stdout=subprocess.PIPE)

        # For optimization purposes, the PathModel and the PasswordModel are
        # separated, otherwise scan_path will call both models for each file
        # With this implementation the discoveries are accumulated and the
        # PasswordModel will be run only once for the password discoveries
        for staged_file in files:
            new_discoveries += client.scan_path(scan_path=os.path.join(diff_path, staged_file),
                                                models=['PathModel'],
                                                force=True,
                                                debug=False)

        if not new_discoveries:
            print_msg('No hardcoded secrets found in your commit')
            sys.exit(0)

        rules = client.get_rules()
        password_rules = set([
            r['id'] for r in rules if r['category'] == 'password'])
        password_discoveries = []
        no_password_discoveries = []
        for d in new_discoveries:
            disc = client.get_discovery(d)
            if disc['rule_id'] in password_rules:
                password_discoveries.append(disc)
            else:
                no_password_discoveries.append(disc)

        # Run the PasswordModel
        disc = []
        if password_discoveries:
            mm = ModelManager('PasswordModel')
            disc = mm.launch_model_batch(password_discoveries)

        list_of_discoveries = []
        for d in disc:
            if d['state'] == 'new':
                list_of_discoveries.append(d)

        # There may be also discoveries other than passwords
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
        elif len(str_discoveries) > 0:
            print_msg(f'You have the following disoveries:\n\n{str_discoveries}\n')
            sys.exit(1)
    except Exception as e:
        print_msg(f'An error occurred: {str(e)}')
        sys.exit(1)
    finally:
        if os.path.exists(diff_path):
            rmdir(diff_path)
