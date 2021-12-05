from __future__ import annotations
from dataclasses import dataclass, Field
from datetime import datetime, timedelta
from typing import Union, Optional, Tuple, List

from parse import parse

from med import Med, MedRegistry, DOSAGE_PARSE_FORMAT

DEFAULT_LOG_FILE = 'logs/med.log'
DEFAULT_DATE_TIME_FORMAT = r'%m/%d/%Y %H:%M'

class NextDose:
    def __init__(self, *, entry=None, med=None, t_override=None):
        if isinstance(entry, Med):
            med, entry = entry, None
        if entry is None:
            if med is None:
                raise TypeError("NextDose requires either an entry or med argument")
            self._d = {'time': datetime.now(), 'amount': f'{med.standard_dose_amount}{med.standard_dose_unit}'}
        else:
            t = max((entry.dose_administrated_date_time + entry.med.time_between_standard_doses), datetime.now())
            self._d = {'time': t,
                       'amount': f'{entry.med.standard_dose_amount}{entry.med.standard_dose_unit}'}

        if t_override is not None:
            self._d['time'] = t_override

    @property
    def time(self) -> datetime:
        return self._d['time']

    @property
    def amount(self) -> str:
        return self._d['amount']

    def __str__(self):
        return f"next dose: {self.amount} at {self.time.strftime(DEFAULT_DATE_TIME_FORMAT)}"


@dataclass
class MedLogEntry:
    med: Med
    dose_administrated_amount: float
    dose_administrated_unit: str
    dose_administrated_date_time: datetime

    def __str__(self):
        t = self.dose_administrated_date_time.strftime(DEFAULT_DATE_TIME_FORMAT)
        return f'{t} {self.med.name} {self.dose_administrated_amount}{self.dose_administrated_unit}'

    @classmethod
    def from_str(cls, s: str) -> MedLogEntry:
        words = s.split(' ')
        date, time = words[:2]
        datetime_obj = datetime.strptime(f'{date} {time}', DEFAULT_DATE_TIME_FORMAT)
        dose_amount, dose_unit = parse(DOSAGE_PARSE_FORMAT, ' '.join(words[-1:]))
        med_name = ' '.join(words[2:-1])
        return MedLogEntry(med=MedRegistry.get(med_name), dose_administrated_amount=dose_amount,
                           dose_administrated_unit=dose_unit, dose_administrated_date_time=datetime_obj)

    @property
    def next_dose(self):
        return NextDose(entry=self)


def log(med,
        dose_administrated_amount = None,
        dose_administrated_unit = None,
        dose_administrated_date_time=None,
        log_file=None) -> MedLogEntry:
    if not log_file:
        log_file = DEFAULT_LOG_FILE
    if dose_administrated_date_time is None:
        dose_administrated_date_time = datetime.now()
    if dose_administrated_unit is None:
        dose_administrated_unit = med.standard_dose_unit
    if dose_administrated_amount is None:
        dose_administrated_amount = med.standard_dose_amount
    entry = MedLogEntry(med=med,
                        dose_administrated_amount=dose_administrated_amount,
                        dose_administrated_unit=dose_administrated_unit,
                        dose_administrated_date_time=dose_administrated_date_time)

    with open(log_file, 'a') as file:
        file.write(f'{entry}\n')

    return entry


def next_dose(med: Med,
              log_file=None) -> NextDose:

    if not log_file:
        log_file = DEFAULT_LOG_FILE
    name = med.name
    matched_lines = []
    with open(log_file, 'r') as file:
        lines = file.readlines()
    for line in lines:
        entry = MedLogEntry.from_str(line)
        if med == entry.med:
            matched_lines.append(line)
    max_per_24hr = med.max_standard_doses_per_day
    if not matched_lines or not max_per_24hr:
        return NextDose(med=med)
    elif len(matched_lines) < max_per_24hr:
        return MedLogEntry.from_str(matched_lines[-1]).next_dose
    else:
        t = MedLogEntry.from_str(matched_lines[-max_per_24hr]).dose_administrated_date_time + timedelta(hours=24)
        last = MedLogEntry.from_str(matched_lines[-1])
        if t > last.next_dose.time:
            return NextDose(entry=last, t_override=t)
        else:
            return NextDose(entry=last)


def print_log(meds: Optional[Tuple[Med], List[Med]] = None,
              log_file=None, ignore_case=False):
    if not log_file:
        log_file = DEFAULT_LOG_FILE

    with open(log_file, 'r') as file:
        lines = file.readlines()

    is_filtered = bool(not meds)
    for line in lines:
        entry = MedLogEntry.from_str(line)
        if ignore_case and is_filtered:
            match_found = any(m.name.casefold() == entry.med.name.casefold() for m in meds)
        elif is_filtered:
            match_found = any(m == entry.med for m in meds)
        else:
            match_found = True
        if match_found:
            print(line, end='')
