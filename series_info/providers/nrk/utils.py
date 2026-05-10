import datetime

from series_info.EpisodeFormat import EpisodeFormat

import re

patterns = [
    re.compile(r'([0-9]+)[\.\s]*(.+)'),
    re.compile(r'(.+?)[\.\s]*([0-9]+)')
]
pattern_epdesc = re.compile(r'Sesong ([0-9]+) \(([0-9]+):[0-9]+\)')


def parse_season_episode(program):
    season = int(program['seasonNumber'])
    episode = program['episodeNumber']
    title = program['episodeTitle']

    # if episode.series is not None and program['title'] != episode.series:
    #     episode.title = program['title']

    for pattern in patterns:
        match = pattern.search(program['episodeTitle'])
        if match:
            if match.group(1) == program['episodeNumber'] and match.group(2) != 'episode':
                title = match.group(2)
            elif match.group(2) == program['episodeNumber'] and match.group(1) != 'episode':
                title = match.group(1)

    # Parse season and episode from description if season is not set or is a year
    if (season is None or len(str(season)) == 4) and program['shortDescription'] is not None:
        matches = pattern_epdesc.search(program['shortDescription'])
        if matches:
            season = int(matches.group(1))
            episode = int(matches.group(2))
            pass
    if re.match(r'\d+\. episode', title):
        title = None

    return season, episode, title


def parse_date(timestamp: str) -> datetime.datetime:
    matches = re.search(r'Date\((-?[0-9]+)([+-][0-9]+)\)', timestamp)
    if not matches:
        raise RuntimeError('Could not parse timestamp')
    timestamp = int(matches.group(1)) / 1000
    return datetime.datetime.fromtimestamp(timestamp)
