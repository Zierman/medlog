#!/usr/bin/env python3
import datetime
from typing import List, Optional

# Help Documentation Constants
from parse import parse

from input_stuff import parsed_input, yn, select
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

        # run in interactive mode
        main(['--interactive'])

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

        if not _SCRIPT_IS_INTERACTIVE_BY_DEFAULT:
            ap.add_argument('--interactive', action='store_true', help='Allow user interaction during execution.')

        # Parse the args
        args = ap.parse_args(args)

        # Use the parsed args to set variables
        is_verbose = args.verbose
        is_quiet = args.quiet
        if not _SCRIPT_IS_INTERACTIVE_BY_DEFAULT:
            is_interactive = args.interactive

        med_name = args.medicine
        dosage = args.dosage
        if dosage:
            dosage = parse(DOSAGE_PARSE_FORMAT, dosage)
        time_str = args.time
        time_format = args.format
        meds_dir = args.meds_dir
        log_file = args.output_file

        # get needed input if in interactive mode
        if is_interactive:
            med = None
            while not med_name:
                med_name = input('Medicine: ')
                if med_name:
                    try:
                        med = MedRegistry.get(med_name, directory=meds_dir)
                    except KeyError as e:
                        selected = None
                        matches = MedRegistry.find_near_matches(med_name, directory=meds_dir)
                        print(f'An exact match was not found. {len(matches)} similarly named results where found.')
                        for match in matches:
                            reply = select(f'Did you mean {match.med.name}?', ('yes','no','stop asking'))
                            if reply == 'stop asking':
                                break
                            elif reply == 'yes':
                                selected = match.med
                                break
                        if selected is not None:
                            med = selected
                        else:  # See if the user wants to register a new Med
                            answer = yn(f'Do you want to register {med_name}')
                            if answer == 'y':
                                med = MedRegistry.interactice_register(med_name)
                            else:
                                med_name = None

            if not dosage:
                default_str = f'{med.standard_dose_amount}{med.standard_dose_unit}'
                dosage = parsed_input(f'Dose administered (default: {default_str}): ',
                                      pattern=DOSAGE_PARSE_FORMAT,
                                      validation=(lambda x: x >= 0, lambda x: True),
                                      allow_none=True,
                                      default=None)
            if not time_format:
                time_format = DEFAULT_DATE_TIME_FORMAT
            if not time_str:
                time_str = parsed_input(f'Time administered (default: current time): ',
                                        validation=(lambda x: x >= 0, lambda x: True),
                                        allow_none=True)
        else:  # not interactive
            med = MedRegistry.get(med_name, directory=meds_dir)

        if dosage:
            dosage_amount, dosage_unit = dosage
        else:
            dosage_amount = None
            dosage_unit = None
        time = datetime.datetime.strptime(time_str, time_format) if time_str else None
        kwargs = dict(med=med,
                      dose_administrated_amount=dosage_amount,
                      dose_administrated_unit=dosage_unit,
                      dose_administrated_date_time=time,
                      log_file=log_file)
        for k, v in kwargs.copy().items():
            if v is None:
                del kwargs[k]
        log(**kwargs)
        print(next_dose(med))


if __name__ == '__main__':
    from sys import argv
    main(argv[1:])
