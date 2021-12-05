import dataclasses
import os
import pathlib
from dataclasses import dataclass
from datetime import timedelta
from functools import total_ordering
from pathlib import Path
from typing import Union, Optional, Any, Tuple, List, Callable
import json
from parse import parse

from input_stuff import parsed_input, select
from json_stuff import NewJSONEncoder, JSONSerializable, json_serializable, NewJSONDecoder

DOSAGE_PARSE_FORMAT = r'{:g}{}'

DEFAULT_MED_DIRECTORY = 'meds/'


@json_serializable
@dataclass
class Med(JSONSerializable):

    @classmethod
    def from_dict(cls, d: dict[str, Any]):
        return Med(**d)

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

    name: str
    standard_dose_amount: Union[int, float]
    standard_dose_unit: str
    time_between_standard_doses: timedelta
    max_standard_doses_per_day: Optional[int] = None
    must_take_with_meal: Optional[bool] = None
    must_take_with_water: Optional[bool] = None

    @classmethod
    def _load(cls, file):
        with open(file, 'r') as f:
            return json.load(f, cls=NewJSONDecoder)

    def retreive_from_registry(self):
        ...


class MedRegistry:

    @classmethod
    def _convert_name_to_filename(cls, name: str) -> str:
        s = name.strip().casefold()
        s = [c if c.isascii() and c.isalnum() else '_' for c in s]
        return ''.join([*s, '.json'])

    @classmethod
    def register(cls, med: Med, *, directory=DEFAULT_MED_DIRECTORY):
        assert Path(directory).is_dir(), f'{str(Path(directory).absolute())!r} is not a directory'
        filename = MedRegistry._convert_name_to_filename(med.name)
        with open(Path(directory, filename), 'w') as file:
            json.dump(med, file, cls=NewJSONEncoder, indent=4)

    @classmethod
    def get(cls,
            med_name: str,
            *,
            directory=None) -> Med:
        if directory is None:
            directory = DEFAULT_MED_DIRECTORY
        assert Path(directory).is_dir(), f'{str(Path(directory).absolute())!r} is not a directory'
        filename = MedRegistry._convert_name_to_filename(med_name)

        try:
            with open(Path(directory, filename), 'r') as file:
                return json.load(file, cls=NewJSONDecoder)
        except FileNotFoundError:
            raise KeyError(f'The medicine {med_name!r} is not registered.')

    @classmethod
    def interactice_register(cls, med_name) -> Med:

        name = med_name
        standard_dose_amount, standard_dose_unit = parsed_input('Standard dosage: ',
                                                                pattern=DOSAGE_PARSE_FORMAT,
                                                                help_msg='Format must be a number followed by a unit. '
                                                                         '\nExample: 30ml')
        delta_h, delta_m = parsed_input('Time between standard doses (hours:minutes): ',
                                        pattern='{:n}:{:g}',
                                        help_msg='Format must be an integer followed by a '
                                                 'collen followed by a number with no spaces. \n'
                                                 'Example: \'1:30.5\' means 1 hour and 30.5 minutes')
        time_between_standard_doses = timedelta(hours=delta_h, minutes=delta_m)
        max_standard_doses_per_day: Optional[int] = parsed_input('Maximum standard doses per day (optional): ',
                                                                 pattern='{:n}',
                                                                 help_msg='Must be a positive integer. \n'
                                                                          'Example: \'4\'',
                                                                 allow_none=True)

        must_take_with_meal: Optional[int] = select('Should this be taken with a meal',
                                                    options=('yes', 'no', '?'),
                                                    allow_none=True)
        if must_take_with_meal == '?':
            must_take_with_meal = None
        elif must_take_with_meal is not None:
            must_take_with_meal = must_take_with_meal == 'yes'

        must_take_with_water: Optional[int] = select('Should this be taken with water',
                                                     options=('yes', 'no', '?'),
                                                     allow_none=True)
        if must_take_with_water == '?':
            must_take_with_water = None
        elif must_take_with_water is not None:
            must_take_with_water = must_take_with_water == 'yes'

        med = Med(name=name,
                  standard_dose_amount=standard_dose_amount,
                  standard_dose_unit=standard_dose_unit,
                  time_between_standard_doses=time_between_standard_doses,
                  max_standard_doses_per_day=max_standard_doses_per_day,
                  must_take_with_meal=must_take_with_meal,
                  must_take_with_water=must_take_with_water)
        MedRegistry.register(med)

        return med

    @classmethod
    def find_near_matches(cls, med_name, directory=None, max_to_return=10, cutoff=4):

        if directory is None:
            directory = DEFAULT_MED_DIRECTORY

        if cutoff is not None:
            assert 0 < cutoff, f'cutoff must be None or a positive integer'

        def _dif(a: str, b: str, offset=0) -> int:
            max_offset = 3
            if offset > max_offset:
                return len(a) + len(b) + offset
            if a is b:
                return offset
            dif = abs(len(a) - len(b)) + offset
            for c_g, c_f in zip(b, a):
                if c_g is not c_f:
                    dif += 1

            recursive_a = min([_dif(f'{a[:i]}{a[i + 1:]}', b, offset + 1) for i in range(len(a))]) if a else dif
            recursive_b = min([_dif(a, f'{b[:i]}{b[i + 1:]}', offset + 1) for i in range(len(b))]) if b else dif

            return min(dif, recursive_a, recursive_b)

        @total_ordering
        class _Candidate:
            def __init__(self, name_given: str, med_found: Med):
                self.med = med_found
                name_given = name_given.casefold()
                name_found = med_found.name.casefold()
                self.difference = _dif(name_given, name_found)

            def __eq__(self, other):
                return isinstance(other, _Candidate) and self.difference.__eq__(self.difference)

            def __lt__(self, other):
                if not isinstance(other, _Candidate):
                    raise TypeError(f'{_Candidate.__name__} objects cannot be compared objects of any other type.')
                return self.difference.__lt__(other.difference)

        files = os.listdir(directory)
        meds = []
        for f in files:
            with open(Path(directory, f), 'r') as file:
                obj: Med = json.load(file, cls=NewJSONDecoder)
                if isinstance(obj, Med):
                    meds.append(obj)
        candidates = [_Candidate(med_name, m) for m in meds]
        candidates.sort()
        candidates = [c for c in candidates if cutoff is None or c.difference < cutoff]
        return candidates[:max_to_return]

