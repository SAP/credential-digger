"""
The 'add_rules' module adds scanning rules from a file to the database.
This module supports both Sqlite & Postegres databases.

usage: credentialdigger add_rules [-h] [--dotenv DOTENV] [--sqlite SQLITE]
                                  path_to_rules

positional arguments:
  path_to_rules    The path of the file that contains the rules.

optional arguments:
  -h, --help       show this help message and exit
  --dotenv DOTENV  The path to the .env file which will be used in all
                   commands. If not specified, the one in the current
                   directory will be used (if present).
  --sqlite SQLITE  If specified, scan the repo using the sqlite client passing
                   as argument the path of the db. Otherwise, use postgres
                   (must be up and running)

"""
import logging

logger = logging.getLogger(__name__)


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
        'path_to_rules', type=str,
        help='The path of the file that contains the rules.')


def run(client, args):
    """
    Add rules to the database

    Parameters
    ----------
    client: `credentialdigger.Client`
        Instance of the client on which to save results
    args: `argparse.Namespace`
        Arguments from command line parser.

    Raises
    ------
        FileNotFoundError
            If the file does not exist
        ParserError
            If the file is malformed
        KeyError
            If one of the required attributes in the file (i.e., rules, regex,
            and category) is missing
    """

    client.add_rules_from_file(args.path_to_rules)

    # This message will not be logged if the above operation fails,
    # hence raising an exception.
    logger.info('The rules have been added successfully.')
