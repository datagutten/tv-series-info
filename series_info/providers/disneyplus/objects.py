from typing import Optional

from series_info.data import Episode, Series


class DisneyPlusEpisode(Episode):
    id: str | None = None
    artwork: Optional[dict] = None
    """
    Dict with different artworks
    """
    resource_id: Optional[str] = None
    """
    base64 encoded info
    """


class DisneyPlusSeries(Series):
    id: str | None = None
