import datetime
import re


# https://stackoverflow.com/a/77332099/2630074
def parse_iso8601_duration(duration: str) -> datetime.timedelta:
    pattern = r"^P(?:(?P<days>\d+\.\d+|\d*?)D)?T?(?:(?P<hours>\d+\.\d+|\d*?)H)?(?:(?P<minutes>\d+\.\d+|\d*?)M)?(?:(?P<seconds>\d+\.\d+|\d*?)S)?$"
    match = re.match(pattern, duration)
    if not match:
        raise ValueError(f"Invalid ISO 8601 duration: {duration}")
    parts = {k: float(v) for k, v in match.groupdict("0").items()}
    return datetime.timedelta(**parts)
