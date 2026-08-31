"""
Trigger Evaluation and Scheduling Engines (Cron and Timer).
Provides standard 5-field CronTrigger parsing and TimerTrigger duration offset calculation.
"""

from __future__ import annotations

import calendar
import datetime
import logging
import time
from typing import Dict, Optional, Set, Union

logger = logging.getLogger("antigravity.scheduler.triggers")


class CronTrigger:
    """
    Standard 5-field cron expression parser and future trigger timestamp calculator.

    Format:
        minute (0-59), hour (0-23), day of month (1-31), month (1-12), day of week (0-7, 0/7=Sun)

    Supports:
        - Wildcard: '*'
        - Step values: '*/n'
        - Number lists: '1,2,5'
        - Ranges: '1-5'
        - Range with step: '1-10/2'
        - Month names: 'JAN-DEC'
        - Day names: 'SUN-SAT'
    """

    MONTH_NAMES: Dict[str, int] = {
        "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
        "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
    }
    DOW_NAMES: Dict[str, int] = {
        "SUN": 0, "MON": 1, "TUE": 2, "WED": 3, "THU": 4, "FRI": 5, "SAT": 6,
    }

    def __init__(self, expression: str) -> None:
        if not isinstance(expression, str):
            raise TypeError(f"Cron expression must be a string, got {type(expression).__name__}")

        self.expression = expression.strip()
        parts = self.expression.split()
        if len(parts) != 5:
            raise ValueError(
                f"Invalid cron expression: expected 5 fields, got {len(parts)} ('{expression}')"
            )

        self.raw_parts = parts
        self.dom_is_wildcard = parts[2] == "*"
        self.dow_is_wildcard = parts[4] == "*"

        self.minutes = self._parse_field(parts[0], 0, 59, "minute")
        self.hours = self._parse_field(parts[1], 0, 23, "hour")
        self.days = self._parse_field(parts[2], 1, 31, "day of month")
        self.months = self._parse_field(parts[3], 1, 12, "month", self.MONTH_NAMES)
        self.days_of_week = self._parse_field(parts[4], 0, 7, "day of week", self.DOW_NAMES)

    def _parse_field(
        self,
        field_str: str,
        min_val: int,
        max_val: int,
        field_name: str,
        name_map: Optional[Dict[str, int]] = None,
    ) -> Set[int]:
        """Parse a single cron field into a set of integer values."""
        res: Set[int] = set()
        items = field_str.split(",")

        for item in items:
            item = item.strip().upper()
            if not item:
                raise ValueError(f"Empty element in {field_name} field of cron expression")

            if item == "*":
                res.update(range(min_val, max_val + 1))
            elif item.startswith("*/"):
                try:
                    step = int(item[2:])
                except ValueError as e:
                    raise ValueError(f"Invalid step value '{item}' in {field_name}") from e
                if step <= 0:
                    raise ValueError(f"Step must be > 0 in {field_name}, got {step}")
                res.update(range(min_val, max_val + 1, step))
            elif "-" in item:
                parts = item.split("/")
                range_part = parts[0]
                step = 1
                if len(parts) > 1:
                    try:
                        step = int(parts[1])
                    except ValueError as e:
                        raise ValueError(f"Invalid step in range '{item}' in {field_name}") from e
                    if step <= 0:
                        raise ValueError(f"Step must be > 0 in {field_name}, got {step}")

                range_bounds = range_part.split("-")
                if len(range_bounds) != 2:
                    raise ValueError(f"Invalid range format '{range_part}' in {field_name}")

                s_str, e_str = range_bounds[0].strip(), range_bounds[1].strip()
                try:
                    start = name_map[s_str] if name_map and s_str in name_map else int(s_str)
                    end = name_map[e_str] if name_map and e_str in name_map else int(e_str)
                except (KeyError, ValueError) as e:
                    raise ValueError(f"Invalid range bound in '{item}' for {field_name}") from e

                if start < min_val or end > max_val or start > end:
                    raise ValueError(
                        f"Range {start}-{end} out of valid bounds ({min_val}-{max_val}) for {field_name}"
                    )
                res.update(range(start, end + 1, step))
            else:
                try:
                    val = name_map[item] if name_map and item in name_map else int(item)
                except (KeyError, ValueError) as e:
                    raise ValueError(f"Invalid value '{item}' for {field_name}") from e

                if val < min_val or val > max_val:
                    raise ValueError(
                        f"Value {val} out of bounds ({min_val}-{max_val}) for {field_name}"
                    )
                res.add(val)

        return res

    def next_fire_time(self, from_time: Optional[float] = None) -> float:
        """
        Calculate the next timestamp (epoch seconds) matching the cron schedule,
        strictly greater than from_time.
        """
        base_t = time.time() if from_time is None else float(from_time)
        base_dt = datetime.datetime.fromtimestamp(base_t)
        dt = base_dt.replace(second=0, microsecond=0) + datetime.timedelta(minutes=1)

        max_years = 5
        start_year = dt.year

        while dt.year <= start_year + max_years:
            if dt.month not in self.months:
                if dt.month == 12:
                    dt = dt.replace(year=dt.year + 1, month=1, day=1, hour=0, minute=0)
                else:
                    dt = dt.replace(month=dt.month + 1, day=1, hour=0, minute=0)
                continue

            _, max_day = calendar.monthrange(dt.year, dt.month)
            if dt.day > max_day:
                if dt.month == 12:
                    dt = dt.replace(year=dt.year + 1, month=1, day=1, hour=0, minute=0)
                else:
                    dt = dt.replace(month=dt.month + 1, day=1, hour=0, minute=0)
                continue

            cron_dow = 0 if dt.weekday() == 6 else dt.weekday() + 1
            dow_match = (cron_dow in self.days_of_week) or (7 in self.days_of_week and cron_dow == 0)

            if self.dom_is_wildcard and self.dow_is_wildcard:
                day_match = True
            elif not self.dom_is_wildcard and not self.dow_is_wildcard:
                day_match = (dt.day in self.days) or dow_match
            elif not self.dom_is_wildcard:
                day_match = (dt.day in self.days)
            else:
                day_match = dow_match

            if not day_match:
                dt = (dt + datetime.timedelta(days=1)).replace(hour=0, minute=0)
                continue

            if dt.hour not in self.hours:
                dt = (dt + datetime.timedelta(hours=1)).replace(minute=0)
                continue

            if dt.minute not in self.minutes:
                dt = dt + datetime.timedelta(minutes=1)
                continue

            return dt.timestamp()

        raise ValueError(
            f"No matching cron schedule found within {max_years} years for expression '{self.expression}'"
        )

    def get_next_run(self, after_timestamp: Optional[float] = None) -> float:
        """Alias for next_fire_time."""
        return self.next_fire_time(from_time=after_timestamp)


class TimerTrigger:
    """
    Timer trigger calculating next trigger time based on duration offset or recurring interval.
    """

    def __init__(
        self,
        interval_seconds: Union[float, int, str],
        one_shot: bool = False,
    ) -> None:
        try:
            self.interval_seconds = float(interval_seconds)
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Invalid interval_seconds for TimerTrigger: {interval_seconds}"
            ) from e
        self.one_shot = one_shot

    def next_fire_time(self, from_time: Optional[float] = None) -> float:
        """
        Calculate next fire timestamp given a base reference time.
        If interval_seconds <= 0, clamps to ensure next_fire_time >= from_time.
        """
        base = time.time() if from_time is None else float(from_time)
        delta = max(0.0, self.interval_seconds)
        return base + delta

    def get_next_run(self, after_timestamp: Optional[float] = None) -> float:
        """Alias for next_fire_time."""
        return self.next_fire_time(from_time=after_timestamp)
