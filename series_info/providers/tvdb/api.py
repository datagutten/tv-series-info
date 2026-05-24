import datetime
import os
import re
from typing import List

import langcodes
import tvdb_v4_official

from series_info.data import Provider
from series_info.providers.tvdb.objects import TVDBSeries, TVDBEpisode


def language_names(codes: list) -> dict:
    names = {}
    for code in codes:
        lang_obj = langcodes.Language.get(code)
        names[code] = lang_obj.display_name()

    return names


class TVDB(Provider):
    slug = "tvdb"
    name = "TVDB"
    has_translations = True
    has_orders = True
    has_search = True
    tvdb: tvdb_v4_official.TVDB

    def __init__(self, **kwargs):
        self.tvdb = tvdb_v4_official.TVDB(os.getenv("TVDB_API_KEY"))
        super().__init__(**kwargs)

    def series_id(self, slug: str) -> int:
        response = self._get('https://thetvdb.com/series/%s' % slug)
        matches = re.search(r'data-type="series" data-id="(\d+)"', response.text)
        return int(matches.group(1))

    @staticmethod
    def _season_types(series: dict):
        types = {}
        for season in series['seasons']:
            if season['type']['type'] not in types:
                types[season['type']['type']] = season['type']['name']
        return types

    def series(self, slug: str, language: str = 'eng', order='official') -> TVDBSeries:
        series = self.tvdb.get_series_extended(self.series_id(slug))
        series_obj = TVDBSeries(
            id=series.get('id'),
            slug=series.get('slug'),
            title=series.get('name'),
            image=series.get('image'),
            languages=language_names(series.get('nameTranslations')),
            original_language=series.get('originalLanguage'),
            description=series.get('overview'),
            year=series.get('year'),
            orders=self._season_types(series),
        )
        return series_obj

    def episodes(self, slug, language='eng', order='official') -> List[TVDBEpisode]:
        if order == 'official':
            order = 'default'
        info_original = self.tvdb.get_series_episodes(self.series_id(slug), season_type=order, page=0)
        if info_original['series']['originalLanguage'] == language:
            info = info_original
            original_titles = {}
        else:
            original_titles = {episode['id']: episode['name'] for episode in info_original['episodes']}
            try:
                series = self.tvdb.get_series_translation(self.series_id(slug), lang=language)
                info = self.tvdb.get_series_episodes(self.series_id(slug), season_type=order, page=0, lang=language)
            except ValueError as e:
                if 'error fetching translation' in str(e):
                    if language != info_original['series']['originalLanguage']:
                        return self.episodes(slug, info_original['series']['originalLanguage'], order)
                    return self.episodes(slug, '', order)
                else:
                    raise e
            info['series'] = series
            # info={'series': series, 'episodes': episodes}
            pass
        episodes = []

        for episode in info['episodes']:

            episode_obj = TVDBEpisode(
                id=episode['id'],
                series=info['series']['name'],
                series_slug=slug,
                season=episode.get('seasonNumber'),
                episode=episode.get('number'),
                title=episode.get('name'),
                description=episode.get('overview'),
                original_title=episode.get('original_title'),
                production_code=episode.get('production_code'),
                season_name=episode.get('seasonName'),
                year=episode.get('year'),
                url='https://thetvdb.com/series/%s/episodes/%d' % (slug, episode['id']),
                language=language,
            )

            if episode['image'] is not None:
                if episode['image'][0:4] == 'http':
                    episode_obj.image = episode['image']
                else:
                    episode_obj.image = 'https://thetvdb.com%s' % episode['image']

            try:
                episode_obj.date = datetime.datetime.fromisoformat(episode['aired']).date()
            except (ValueError, TypeError):
                pass

            if episode['runtime'] is not None:
                episode_obj.runtime = int(datetime.timedelta(minutes=episode['runtime']).total_seconds())

            if episode_obj.id in original_titles:
                episode_obj.original_title = original_titles[episode_obj.id]

            episodes.append(episode_obj)
        return episodes

    def search(self, search: str, language='en'):
        results = []
        matches = self.tvdb.search(search)
        for match in matches:
            series_obj = TVDBSeries(
                id=match.get('id'),
                slug=match.get('slug'),
                title=match.get('name'),
                description=match.get('overview'),
                image=match.get('thumbnail'),
                language=match.get('primary_language'),
                languages=language_names(match.get('translations').keys()),
                original_language=match.get('primary_language'),
                year=match.get('year'),
            )
            results.append(series_obj)
        return results
