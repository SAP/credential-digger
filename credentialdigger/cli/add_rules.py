"""
The 'add_rules' module adds scanning rules from a file to the database.
This module supports both Sqlite & Postegres databases.

This command takes multiple arguments:
path_to_rules       <Required> The path of the file that contains the rules.

--sqlite DB_PATH    <Optional> If specified, use the sqlite client and
                        the db passed as argument (otherwise use postgres)

Usage:
python -m credentialdigger add_rules /path/rules.yml

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


def run(args, client):
    """
    Add rules to the database

    Parameters
    ----------
    args: `argparse.Namespace`
        Arguments from command line parser.
    client: `credentialdigger.Client`
        Instance of the client on which to save results

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
