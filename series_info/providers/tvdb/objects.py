import dataclasses

from series_info.data import Episode, Series


@dataclasses.dataclass
class TVDBEpisode(Episode):
    id: int = None
    """
    TVDB id
    """

    production_code: str = None

    image: str = None
    """
    Episode image
    """

    @property
    def url(self):
        return 'https://thetvdb.com/series/%s/episodes/%d' % (self.series_slug, self.id)

    @url.setter
    def url(self, value):
        pass

    @property
    def translation_url(self):
        return 'https://thetvdb.com/series/%s/episodes/%d/translate/%s/0/single' % (self.series_slug, self.id,
                                                                                    self.language)


@dataclasses.dataclass
class TVDBSeries(Series):
    id: int = None
    """
    TVDB id
    """
