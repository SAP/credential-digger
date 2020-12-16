import sys
import logging
import argparse

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class customParser(argparse.ArgumentParser):
    def error(self, message):
        logger.error(f'{message}\n')
        self.print_help()
        exit()


if __name__ == "__main__":
    from credentialdigger import add_rules, download, scan

    # Main parser configuration
    main_parser = customParser('credentialdigger')
    subparsers = main_parser.add_subparsers()

    # region: common parsers configuration
    parser_dotenv = customParser(add_help=False)
    parser_dotenv.add_argument(
        '--dotenv', type=str, default=None,
        help='The path to the .env file which will be used in all \
            commands. If not specified, the one in the current directory will \
            be used (if present).')
    parser_sqlite = customParser(add_help=False)
    parser_sqlite.add_argument(
        '--sqlite', type=str, default=None,
        help='If specified, scan the repo using the sqlite client \
            passing as argument the path of the db. Otherwise, use postgres \
            (must be up and running)')
    # endregion

    # region: download subparser configuration
    parser_download = subparsers.add_parser(
        'download', parents=[parser_dotenv],
        help='Download and link a machine learning model')
    parser_download.set_defaults(func=download)
    parser_download.add_argument(
        'model', type=str,
        help='The name of the model. It must be an environment variable.')
    parser_download.add_argument(
        'pip_args', nargs='*', default=None, help='Keyword arguments for pip.')
    # endregion

    # region: add_rules subparser configuration
    parser_add_rules = subparsers.add_parser(
        'add_rules', help='Add scanning rules from a file to the database',
        parents=[parser_dotenv, parser_sqlite])
    parser_add_rules.set_defaults(func=add_rules)
    parser_add_rules.add_argument(
        'path_to_rules', type=str,
        help='The path of the file that contains the rules.')
    # endregion

    # region: scan subparser configuration
    parser_scan = subparsers.add_parser(
        'scan', help='Scan a git repository',
        parents=[parser_dotenv, parser_sqlite])
    parser_scan.set_defaults(func=scan)
    parser_scan.add_argument(
        'repo_url', type=str,
        help='The URL of the git repository to be scanned.')
    parser_scan.add_argument(
        '--category', default=None, type=str,
        help=' If specified, scan the repo using all the rules of this \
            category, otherwise use all the rules in the db')
    parser_scan.add_argument(
        '--models', default=None, nargs='+',
        help='A list of models for the ML false positives detection.\n Cannot \
            accept empty lists.')
    parser_scan.add_argument(
        '--exclude', default=None, nargs='+',
        help='A list of rules to exclude')
    parser_scan.add_argument(
        '--force', action='store_true',
        help='Force a complete re-scan of the repository, in case it has \
            already been scanned previously')
    parser_scan.add_argument(
        '--debug', action='store_true',
        help='Flag used to decide whether to visualize the progressbars \
            during the scan (e.g., during the insertion of the detections in \
            the db)')
    parser_scan.add_argument(
        '--generate_snippet_extractor',
        action='store_true',
        help='Generate the extractor model to be used in the SnippetModel. \
            The extractor is generated using the ExtractorGenerator. If \
            `False`, use the pre-trained extractor model')
    # endregion

    # Run the parser
    if len(sys.argv) == 1:
        main_parser.print_help()
        exit()

    args = main_parser.parse_args(sys.argv[1:])
    load_dotenv(dotenv_path=args.dotenv, verbose=True)
    args.func(args)
