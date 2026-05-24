import datetime
import os
import re
import shutil
from pathlib import Path
from typing import List

from requests_cache import patcher

from series_info.data import Provider, cache_file

patcher.install_cache(cache_file('disneyplus'))
from pydisney import DisneyAPI
from pydisney import models
from pydisney.Auth import Auth
from pydisney.Config import APIConfig
from pydisney.models.Episode import Episode as DisneyEpisode

from pydisney import utils as disney_utils
from pydisney.models.Hit import Hit

from .objects import DisneyPlusEpisode, DisneyPlusSeries


def image(image_id: str, width: int = 300):
    return f'https://disney.images.edge.bamgrid.com/ripcut-delivery/v2/variant/disney/{image_id}/compose?width={width}'


class DisneyPlus(Provider):
    # has_translations = True
    has_search = True
    slug = "disneyplus"
    name = "Disney+"

    def __init__(self, email=None, password=None, profile: str = None, pin: int = None, language='en'):
        super().__init__()
        self.api = DisneyAPI(email=os.getenv('DISNEY_EMAIL', email), password=os.getenv('DISNEY_PASSWORD', password))
        self.pin = os.getenv('DISNEY_PIN', pin)
        profile = os.getenv('DISNEY_PROFILE', profile)
        language = os.getenv('DISNEY_LANGUAGE', language)
        self.language = language

        active_profile = self.api.get_active_profile()
        if profile and active_profile.name != profile:
            profiles = self.api.get_profiles()
            self.profiles = profiles
            for profile_iter in profiles:
                if profile_iter.name == profile:
                    self.api.set_active_profile(profile_iter.id, self.pin)
                    self.profile = profile_iter
        else:
            self.profile = active_profile

        if language and self.profile.language_preferences.app != language:
            self.set_language(language)

    def _token_file(self, language=None):
        return 'token_%s.json' % language or self.profile.language_preferences.app

    def get_entity(self, guid) -> models.Hit.Hit:
        res = Auth.make_pagination_request("GET",
                                           'https://disney.api.edge.bamgrid.com/explore/v1.7/page/entity-%s' % guid)

        return models.Hit.Hit(res[0]['data']['page'])

    def images(self, hit: dict, base_path=None) -> list:
        data = []
        if not base_path:
            base_path = Path('images')
        for key, value in hit.items():
            if key == 'imageId':
                path = base_path
                url = image(value)
                response = self._session.get(url)
                path.mkdir(parents=True, exist_ok=True)
                path = path.joinpath(value).with_suffix('.png')
                path.write_bytes(response.content)
                data.append(path)
            else:
                path = base_path.joinpath(key)
                if type(value) is dict:
                    data += self.images(value, path)
                    continue

        return data

    def set_language(self, language: str):
        if language == self.language:
            return
        file = self._token_file(language)
        if os.path.exists(file):
            shutil.copy(file, '../token.json')
            self.api._auth.get_auth_token()
        else:
            language_obj = models.Language.Language(language)
            set_result = self.profile.set_profile_language(language_obj)
            if not set_result:
                self.profile = self.api.get_active_profile()
                self.api.set_active_profile(self.profile.id, self.pin)
            else:
                APIConfig.token = set_result['extensions']['sdk']['token']['accessToken']
                APIConfig.refresh = set_result['extensions']['sdk']['token']['refreshToken']

        disney_utils.helper.update_file()
        shutil.copy('../token.json', file)
        self.language = language

    @staticmethod
    def convert_hit(hit: Hit) -> DisneyPlusSeries | None:
        if hit.is_movie:
            return None
        series_obj = DisneyPlusSeries(
            description=hit.full_desc,
            slug=hit.id,
            id=hit.id,
            year=int(hit.startYear),
            image=image(hit.artwork['standard']['tile']['1.00']['imageId']),
            title=hit.title,
        )
        return series_obj

    @staticmethod
    def convert_hit_episode(hit: Hit) -> List[DisneyPlusEpisode]:
        if hit.is_movie:
            return []

        episodes = []

        for season in hit.seasons:
            episode: models.Episode.Episode
            for episode in season.episodes:
                # disney_episode_obj = DisneyEpisode(episode)
                matches_epnum = re.search(r'S(\d+):E(\d+)', episode.fullEpisodeTitle)
                if matches_epnum:
                    season = int(matches_epnum.group(1))
                else:
                    season = season.number + 1

                episode_obj = DisneyPlusEpisode(
                    id=episode.id,
                    series=hit.title,
                    season=season,
                    episode=int(episode.episodeNumber),
                    title=episode.episodeTitle,
                    description=episode.full_description,
                    year=int(hit.startYear),
                    runtime_obj=datetime.timedelta(milliseconds=episode.durationMs),
                    # runtime=int(episode.durationMs / 1000),
                    image=image(episode.artwork['standard']['thumbnail']['1.78']['imageId']),
                    url=f'https://www.disneyplus.com/play/{episode.id}'
                )

                episodes.append(episode_obj)

        return episodes

    def episodes(self, guid, language: str = 'en'):
        if language != self.language:
            self.set_language(language)

        hit = self.get_entity(guid)
        image_lst = self.images(hit.artwork)
        # for season in hit.seasons:
        #     episode: models.Episode.Episode
        #     for episode in season.episodes:
        #         self.images(episode.artwork)
        return self.convert_hit_episode(hit)

    def search(self, search: str, language='en'):
        self.set_language(language)
        result = self.api.search(search)
        return list(map(lambda hit: self.convert_hit(hit), result))


if __name__ == '__main__':
    obj = DisneyPlus(email=os.getenv('DISNEY_EMAIL'),
                     password=os.getenv('DISNEY_PASSWORD'),
                     profile=os.getenv('DISNEY_PROFILE', None),
                     pin=os.getenv('DISNEY_PIN', None),
                     language=os.getenv('DISNEY_LANGUAGE', None))
    series = obj.episodes('5a9fbaf9-15a7-4266-94e4-5693883842ab')
    pass
