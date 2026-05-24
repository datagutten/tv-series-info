from series_info.data import Episode, Series


class DisneyPlusEpisode(Episode):
    id: str | None = None


class DisneyPlusSeries(Series):
    id: str | None = None
