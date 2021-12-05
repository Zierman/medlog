from enum import Enum, auto
from typing import Optional, Collection, Callable, Union, List, Tuple, Any, overload

from parse import parse


class StrCaseConversion(Enum):
    no_conversion = auto()
    to_lower = auto()
    to_upper = auto()
    capitalize = auto()
    casefold = auto()

    def convert(self, s: str):
        return {StrCaseConversion.no_conversion: s,
                StrCaseConversion.to_lower: s.lower(),
                StrCaseConversion.to_upper: s.upper(),
                StrCaseConversion.capitalize: s.capitalize(),
                StrCaseConversion.casefold: s.casefold()}[self]

    def __call__(self, s):
        return self.convert(s)


def parsed_input(prompt,
                 *,
                 pattern='{}',
                 help_msg=None,
                 validation: Optional[Union[dict, tuple]] = None,
                 input_func: Callable = input,
                 allow_none: bool = False,
                 should_strip: bool = True,
                 case_conversion: Optional[StrCaseConversion] = StrCaseConversion.no_conversion,
                 default: Any = None):
    """Gets parsed input

    Args:
        prompt: The message shown to the user.
        pattern: The pattern used to parse the input. See parser.parse for information.
        help_msg: A message to be displayed if the parser could not find a match.
        validation: A collection of validation callables that return true if the value is valid.
        input_func: The function to be called to get input from user.
        allow_none: A bool indicating if an empty input string will result in None being returned.
        should_strip: A bool indicating if an input string should be stripped before parsing.
        case_conversion: A enum value that represents what kind of pre-parsing conversion should be done on the input
            string.
        default: The result that will be returned if allow_none is True and input was empty.

    Returns:
        The Result object from parse call or the default.
    """
    while True:
        input_str: str = input_func(prompt)

        # perform pre-parse operations
        if should_strip:
            input_str = input_str.strip()
        input_str = case_conversion(input_str)

        if not input_str and allow_none:
            return default
        elif input_str:
            result = parse(pattern, input_str)
            if result and validation:
                if isinstance(validation, dict):
                    for name, validate in validation.items():
                        if name in result.named:
                            r = result.named[name]
                            if not validate(r):
                                print(f'{r!r} is not valid.')
                                result = None
                        else:
                            print(f'result name {name!r} not found.')
                else:
                    for r, validate in zip(result.fixed, validation):
                        if not validate(r):
                            print(f'{r!r} is not valid.')
                            result = None
            if result is not None:
                return result if len(result.fixed) > 1 else result.fixed[0]
            elif help_msg:
                print(help_msg)


def select(question: str,
           options: Union[list, tuple, dict],
           *,
           should_strip: bool = True,
           option_separator: str = '/',
           option_enclosure: str = '()',
           input_func: Callable = input,
           allow_none: bool = False,
           case_conversion: StrCaseConversion = StrCaseConversion.casefold,
           options_are_abbreviations:bool = False) -> Optional[str]:
    while True:
        prompt_option_str = f'{option_enclosure[0]}{option_separator.join(options)}{option_enclosure[1]}'
        result = input_func(f'{question} {prompt_option_str}: ')

        result = case_conversion(result.strip()) if should_strip else case_conversion(result)
        if not result and allow_none:
            return None

        if isinstance(options, dict):
            found = [v for k, v in options.items() if k.startswith(result)]
        else:
            found = [o for o in options if o.startswith(result) or (options_are_abbreviations and result.startswith(o))]
        if len(found) == 1:
            return found[0]
        else:  # check for exact match
            for s in found:
                if s is result:
                    return s


@overload
def yn(question: str,
       *,
       should_strip: bool = True,
       option_separator: str = '/',
       option_enclosure: str = '()',
       input_func: Callable = input,
       allow_none: bool = False,
       case_conversion: StrCaseConversion = StrCaseConversion.casefold):
    ...


def yn(question: str, *args, **kwargs) -> str:
    options = ('y', 'n')
    return select(question, options, *args, **kwargs)


