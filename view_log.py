#!/usr/bin/env python3
import datetime
from typing import List, Optional

# Help Documentation Constants
from parse import parse

import med_log
from input_stuff import parsed_input
from med import MedRegistry, DOSAGE_PARSE_FORMAT
from med_log import DEFAULT_DATE_TIME_FORMAT, log, next_dose

_SCRIPT_NAME: Optional[str] = None
_SCRIPT_USAGE: Optional[str] = None
_SCRIPT_DESCRIPTION: Optional[str] = None
_SCRIPT_EPILOG: Optional[str] = None

# Script Default Constants
_SCRIPT_IS_INTERACTIVE_BY_DEFAULT = False




def main(args: Optional[List[str]]):
    """Executes the script. Use '-h' argument to see help info."""

    if not args:  # Default operation if no arguments are received.

        # print the log
        med_log.print_log()

    else:  # Operation when processing arguments.
        import argparse

        # List of variables to be set by arguments and their default values
        is_verbose: bool = False
        is_quiet: bool = False
        is_interactive: bool = _SCRIPT_IS_INTERACTIVE_BY_DEFAULT

        # Setup the argument parser
        ap: argparse.ArgumentParser = argparse.ArgumentParser(prog=_SCRIPT_NAME,
                                                              usage=_SCRIPT_USAGE,
                                                              description=_SCRIPT_DESCRIPTION,
                                                              epilog=_SCRIPT_EPILOG)

        # setup normal args
        ap.add_argument('-m', '--medicine', action='store', default=None, help='Name of medicine administered.')
        ap.add_argument('-d', '--dosage', action='store', default=None, help='The amount of medicine administered.')
        ap.add_argument('-t', '--time',
                        action='store',
                        default=None,
                        help='The date-time that the medicine was administered.')
        ap.add_argument('-f', '--format',
                        action='store',
                        default=r'%m-%d-%Y_%H:%M',
                        help='The format to parse the date-time. default=\'%%m-%%d-%%Y_%%H:%%M\'. '
                             'See: https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior')
        ap.add_argument('--meds-dir',
                        action='store',
                        default=None,
                        help='The directory where medicine files are stored.')

        ap.add_argument('-o', '--output-file',
                        action='store',
                        default=None,
                        help='The directory where medicine files are stored.')

        # Setup output group
        ap.output_group = ap.add_mutually_exclusive_group()
        ap.output_group.add_argument('-v', '--verbose', action='store_true', help='Outputs more information.')
        ap.output_group.add_argument('-q', '--quiet', action='store_true', help='Reduces output.')

        # if not _SCRIPT_IS_INTERACTIVE_BY_DEFAULT:
        #     ap.add_argument('--interactive', action='store_true', help='Allow user interaction during execution.')

        # Parse the args
        args = ap.parse_args(args)

        # Use the parsed args to set variables
        is_verbose = args.verbose
        is_quiet = args.quiet
        # if not _SCRIPT_IS_INTERACTIVE_BY_DEFAULT:
        #     is_interactive = args.interactive

        med_name = args.medicine
        dosage = args.dosage
        time_str = args.time
        time_format = args.format
        meds_dir = args.meds_dir
        out_file = args.output_file

        # TODO - Use the arguments to filter output.
        med_log.print_log()



if __name__ == '__main__':
    from sys import argv
    main(argv[1:])
