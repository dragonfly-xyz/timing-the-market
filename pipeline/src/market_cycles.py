from datetime import date
from typing import Optional


MARKET_CYCLES = [
    {"name": "Pre-2013 Early", "start": None, "end": date(2013, 1, 1), "type": "Early"},
    {"name": "2013 Bull", "start": date(2013, 1, 1), "end": date(2013, 12, 1), "type": "Bull"},
    {"name": "2014-2015 Bear", "start": date(2013, 12, 1), "end": date(2015, 8, 1), "type": "Bear"},
    {"name": "2015-2016 Recovery", "start": date(2015, 8, 1), "end": date(2016, 1, 1), "type": "Neutral"},
    {"name": "2016-2017 Bull", "start": date(2016, 1, 1), "end": date(2018, 1, 1), "type": "Bull"},
    {"name": "2018-2019 Bear", "start": date(2018, 1, 1), "end": date(2018, 12, 1), "type": "Bear"},
    {"name": "2019-2020 Recovery", "start": date(2018, 12, 1), "end": date(2020, 3, 1), "type": "Neutral"},
    {"name": "2020-2021 Bull", "start": date(2020, 3, 1), "end": date(2021, 11, 1), "type": "Bull"},
    {"name": "2022 Bear", "start": date(2021, 11, 1), "end": date(2022, 11, 1), "type": "Bear"},
    {"name": "2023 Recovery", "start": date(2022, 11, 1), "end": date(2023, 10, 1), "type": "Neutral"},
    {"name": "2023-2025 Bull", "start": date(2023, 10, 1), "end": date(2025, 11, 1), "type": "Bull"},
    {"name": "2025-2026 Bear", "start": date(2025, 11, 1), "end": None, "type": "Bear"},
]


def classify_launch_date(launch_date: date) -> dict:
    """Classify a launch date into a market cycle. Returns cycle dict or unknown."""
    for cycle in MARKET_CYCLES:
        start = cycle["start"]
        end = cycle["end"]
        if start is None and end is not None:
            if launch_date < end:
                return cycle
        elif start is not None and end is None:
            if launch_date >= start:
                return cycle
        elif start is not None and end is not None:
            if start <= launch_date < end:
                return cycle
    return {"name": "Unknown", "start": None, "end": None, "type": "Unknown"}


def get_cycle_type(launch_date: Optional[date]) -> str:
    """Get just the cycle type string for a launch date."""
    if launch_date is None:
        return "Unknown"
    return classify_launch_date(launch_date)["type"]


def get_cycle_name(launch_date: Optional[date]) -> str:
    """Get the cycle name for a launch date."""
    if launch_date is None:
        return "Unknown"
    return classify_launch_date(launch_date)["name"]


def get_all_cycles() -> list[dict]:
    """Return all market cycle definitions as serializable dicts."""
    result = []
    for c in MARKET_CYCLES:
        result.append({
            "name": c["name"],
            "start": c["start"].isoformat() if c["start"] else None,
            "end": c["end"].isoformat() if c["end"] else None,
            "type": c["type"],
        })
    return result
