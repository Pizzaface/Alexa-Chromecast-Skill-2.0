import datetime


def get_iso_split(s, split):
    if split in s:
        n, s = s.split(split)
    else:
        n = 0
    return n, s


def parse_iso_duration(s):
    # Remove prefix
    s = s.split('P')[-1]

    # Step through letter dividers
    days, s = get_iso_split(s, 'D')
    _, s = get_iso_split(s, 'T')
    hours, s = get_iso_split(s, 'H')
    minutes, s = get_iso_split(s, 'M')
    seconds, s = get_iso_split(s, 'S')

    # Convert all to seconds
    dt = datetime.timedelta(days=int(days), hours=int(hours), minutes=int(minutes), seconds=int(seconds))
    return int(dt.total_seconds())
