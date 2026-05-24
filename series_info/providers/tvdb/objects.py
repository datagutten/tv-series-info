from typing import Optional

from series_info.data import Episode, Series


class TVDBEpisode(Episode):
    id: int = None
    """
    TVDB id
    """

    production_code: Optional[str] = None

    image: Optional[str] = None
    """
    Episode image
    """

    @property
    def translation_url(self):
        return 'https://thetvdb.com/series/%s/episodes/%d/translate/%s/0/single' % (self.series_slug, self.id,
                                                                                    self.language)


class TVDBSeries(Series):
    id: int = None
    """
    TVDB id
    """
