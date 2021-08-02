"""
The 'get_discoveries' module can be used to retrieve the discoveries on the fly 
from the terminal. It supports both the Sqlite and Postgres clients.

NOTE: Postgres is used by default. Please make sure that the environment
variables are exported.

usage: credentialdigger get_discoveries [-h] [--dotenv DOTENV] [--sqlite SQLITE]
                                        [--save SAVE]
                                        repo_url

positional arguments:
  repo_url              The url of the repo we want to retrieve the discoveries
                        from. Please make sure it has been scanned beforehand.

optional arguments:
    -h, --help          Show this help message and exit
    --dotenv DOTENV     The path to the .env file which will be used in all
                        commands. If not specified, the one in the current
                        directory will be used (if present).
    --sqlite SQLITE     If specified, scan the repo using the sqlite client
                        passing as argument the path of the db. Otherwise, use
                        postgres (must be up and running)
    --save SAVE         If specified, export the discoveries to the path passed
                        as an argument instead of showing them on the terminal.
  
"""

import logging
import os
import pandas as pd

from rich.console import Console
from rich.table import Table
from rich import print
from rich.progress import track

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
        help='The location of a git repository (an url if --local is not set, \
            a local path otherwise)')
    parser.add_argument(
        '--save', default=None, type=str,
        help='Path of the .csv file to which we export the discoveries.')