import json
import re
import warnings

import lxml.html

from series_info.data import Episode, Provider, Series
from . import utils
from .utils import parse_season_episode


class NRKMeta(Provider):
    slug = 'nrk'
    name = 'NRK'

    def _psapi(self, uri) -> dict:
        return self._get('https://psapi.nrk.no/%s' % uri).json()

    def series(self, slug: str, **kwargs):
        series = self._get('https://psapi.nrk.no/tv/catalog/series/%s' % slug).json()
        series_type = series['seriesType']
        series_obj = Series(
            slug=slug,
            title=series[series_type]['titles']['title'],
            description=series[series_type]['titles']['subtitle'],
            image=series[series_type]['image'][-1]['url'],
            url='https://psapi.nrk.no' + series['_links']['self']['href'],
        )

        return series_obj

    def episodes(self, slug: str, **kwargs) -> list[Episode]:
        series = self._get('https://psapi.nrk.no/tv/catalog/series/%s' % slug).json()
        episodes = []
        for season_info in series['_embedded']['seasons']:
            season_info = self._get('https://psapi.nrk.no' + season_info['_links']['self']['href']).json()
            if '_embedded' not in season_info:
                warnings.warn('Season info not found')
                continue
            if 'instalments' in season_info['_embedded']:
                nrk_episodes = season_info['_embedded']['instalments']
            elif 'episodes' in season_info['_embedded']:
                nrk_episodes = season_info['_embedded']['episodes']
            else:
                raise RuntimeError('No episodes found')
            series_type = series['seriesType']

            for episode_info in nrk_episodes:
                program = self._psapi('/programs/%s' % episode_info['prfId'])
                season, episode, title = parse_season_episode(program)
                episode_obj = Episode(
                    series=series[series_type]['titles']['title'],
                    series_slug=slug,
                    season=season,
                    episode=episode,
                    id=episode_info['prfId'],
                    title=title,
                    year=episode_info['productionYear'],
                    original_title=episode_info['originalTitle'],
                    # runtime_obj=parse_iso8601_duration(episode_info['duration']),
                    date=utils.parse_date(program['firstTimeTransmitted']['actualTransmissionDate']).date(),
                    image=program['image']['webImages'][-1]['imageUrl'],
                    description=program['shortDescription'],
                    url=program['_links']['share']['href'],
                )
                if episode_obj.original_title == episode_obj.series:
                    matches = re.search(r'\((.+?)\)\s+(?:Sesong (\d+)\s+)?\((\d+):(\d+)\)$', episode_obj.description)
                    if matches:
                        episode_obj.original_title = matches.group(1)

                episodes.append(episode_obj)
        return episodes

    def episodes_scrape(self, slug: str):
        response = self._get('https://tv.nrk.no/serie/%s' % slug)

        root = lxml.html.fromstring(response.content)
        script = root.find('.//script[@id="pageData"]').text
        data = json.loads(script)
        episodes = []
        slug = data['initialState']['series']['id']

        for season in data['initialState']['seasons']:
            for episode in season['episodes']:

                matches = re.search(r'^(\d+)\.\s(.+)', episode['title'])

                if not matches:
                    title = episode['title']
                else:
                    epnum, title = matches.groups()

                if title == 'episode':
                    title = None

                ep_obj = Episode(
                    series=data['initialState']['series']['title'],
                    series_slug=data['initialState']['series']['id'],
                    title=title,
                    description=episode['description'],
                )
                # try:
                #     ep_obj.runtime_obj = parse_iso8601_duration(episode['duration']['ISO8601'])
                # except ValueError:
                #     pass

                if 'originalTitle' in episode:
                    ep_obj.original_title = episode['originalTitle']

                if 'productionYear' in episode:
                    ep_obj.year = episode['productionYear']

                if 'sequenceNumber' in episode:
                    ep_obj.episode = episode['sequenceNumber']
                for title in season['titles'].values():
                    if not title or re.match(r'Sesong \d+', title):
                        continue
                    ep_obj.season_name = title
                    break

                try:
                    ep_obj.season = int(season['id'])
                except ValueError:
                    ep_obj.season_name = season['id']

                width = 0
                for image in episode['images']:
                    if image['width'] > width:
                        ep_obj.image = image['url']

                episodes.append(ep_obj)

        return episodes
