"""
The 'get_discoveries' module can be used to retrieve the discoveries on the fly
from the terminal. It supports both the Sqlite and Postgres clients.

NOTE: Postgres is used by default. Please make sure that the environment
variables are exported.

usage: credentialdigger get_discoveries [-h] [--dotenv DOTENV]
                                        [--sqlite SQLITE]
                                        [--save SAVE]
                                        repo_url

positional arguments:
    repo_url            The url of the repo we want to retrieve the discoveries
                        from. Please make sure it has been scanned beforehand.

optional arguments:
    -h, --help          Show this help message and exit
    --dotenv DOTENV     The path to the .env file which will be used in all
                        commands. If not specified, the one in the current
                        directory will be used (if present)
    --sqlite SQLITE     If specified, scan the repo using the sqlite client
                        passing as argument the path of the db. Otherwise, use
                        postgres (must be up and running)
    --filename FILENAME The filename to filter discoveries on
    --save SAVE         If specified, export the discoveries to the path passed
                        as an argument instead of showing them on the terminal

"""

import logging
import os

import pandas as pd

from rich.console import Console
from rich.table import Table

# Maximum number of discoveries to print. If repo has more discoveries,
# the user will be given the option to export said discoveries.
MAX_NUMBER_DISCOVERIES = 30

logger = logging.getLogger(__name__)
console = Console()


def configure_parser(parser):
    """
    Configure arguments for command line parser.

    Parameters
    ----------
    parser: `credentialdigger.cli.customParser`
        Command line parser
    """
    parser.set_defaults(func=run)
    parser.add_argument(
        'repo_url', type=str,
        help='The url of the repo we want to retrieve the discoveries from')
    parser.add_argument(
        '--filename', default=None, type=str,
        help='The filename to filter discoveries on')
    parser.add_argument(
        '--save', default=None, type=str,
        help='Path of the .csv file to which we export the discoveries')


def print_discoveries(discoveries, repo_url):
    with console.status(f'[bold]Processing {len(discoveries)} discoveries...'):
        discoveries_list = pd.DataFrame(discoveries)
        # Remove the repo_url column since it has been passed as an argument
        del discoveries_list['repo_url']
        # Remove timestamp and rule_id columns because they are not
        # quite relevant
        del discoveries_list['timestamp']
        del discoveries_list['rule_id']

        # Convert `int` columns to `str` to be eventually rendered.
        discoveries_list['id'] = discoveries_list['id'].astype(str)
        int_to_str = discoveries_list['line_number'].astype(str)
        discoveries_list['line_number'] = int_to_str

        # Convert to list and insert column names
        discoveries_list = discoveries_list.values.tolist()
        columns = ['id', 'file_name', 'commit_id', 'line_number',
                   'snippet', 'state']

        table = Table(
            title=f'Discoveries found in "{repo_url}"',
            pad_edge=False, show_lines=True)

        for c in columns:
            table.add_column(c)
        for row in discoveries_list:
            table.add_row(*row)

        console.print(table)


def export_csv(discoveries, client, save=False):
    # Check if --save is specified
    if save is False:
        path = ''
        # Read the export path from the console's input
        while path == '':
            path = console.input('Path to export CSV:')
    else:
        # if --save argument is set, we use it as an export path
        path = save

    try:
        with open(path, newline='', mode='w') as csv_file:
            with console.status('[bold]Exporting the discoveries..'):
                data = client.export_discoveries_csv(discoveries)
                csv_file.writelines(data)
                console.print(
                    '[bold][!] The discoveries have been exported \
successfully.')
    except Exception as e:
        console.print(f'[red]{e}[/]')
        try:
            os.remove(path)
        except OSError as osE:
            console.print(f'[red]{osE}[/]')

def assign_categories(client, discoveries):
        """ Add category to each discovery

        Parameters
        ----------
        discoveries: list
            List of discoveries without assigned categories to them

        """
        rulesdict = client.get_rules()
        for discovery in discoveries:
            if discovery['rule_id']:
                category = rulesdict[discovery['rule_id'] - 1]['category']
                discovery['category'] = category
            else:
                discovery['category'] = '(rule deleted)'
                
def filter_discoveries(discoveries, states='all'):
    """ Filter discoveries based on state

    Parameters
    ----------
    discoveries: list
        List of discoveries to be filtered
    states: str | list
            - str: if it equals 'all', then return all discoveries.
                   return chosen state otherwise (i.e 'false_positive')
            - list: return all the discoveries that have states contained
                    in this list (i.e ['new', 'false_positive'])
    Returns
    -------
    list
        Filtered list of discoveries
    """
    if states == 'all':
        states = ['new', 'false_positive',
                  'addressing', 'not_relevant', 'fixed']

    filtered_discoveries = list(
        filter(lambda d: d.get('state') in states, discoveries))

    return filtered_discoveries

def run(client, args):
    """
    Retrieve discoveries of a git repository.

    Parameters
    ----------
    client: `credentialdigger.Client`
        Instance of the client from which we retrieve results
    args: `argparse.Namespace`
        Arguments from command line parser.
    """

    try:
        discoveries = client.get_discoveries(
            repo_url=args.repo_url, file_name=args.filename)
    except Exception as e:
        console.print(f'[red]{e}[/]')

    # if --save is specified, export the discoveries and exit
    if args.save is not None:
        export_csv(discoveries, client, save=args.save)
        return True

    if len(discoveries) == 0:
        # if repo has no discoveries, exit
        console.print(f'[bold] {args.repo_url} has 0 discoveries.')
    elif len(discoveries) > MAX_NUMBER_DISCOVERIES:
        response = ''
        while response.upper() not in ['Y', 'N', 'YES', 'NO']:
            response = console.input(
                f'[bold]This repository has more than {MAX_NUMBER_DISCOVERIES} \
discoveries, export them as .csv instead? (Y/N)')
        if response.upper() in ['N', 'NO']:
            print_discoveries(discoveries, args.repo_url)
        else:
            export_csv(discoveries, client)
    else:
        print_discoveries(discoveries, args.repo_url)
        console.print(
            f'[bold] {args.repo_url} has {len(discoveries)} discoveries.')
