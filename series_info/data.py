from __future__ import annotations

import dataclasses
import datetime
import os
from pathlib import Path
from typing import Optional

import requests
import requests_cache
from video_tools import EpisodeFormat


@dataclasses.dataclass
class Episode(EpisodeFormat):
    # series: str | None = None
    # """
    # Series name
    # """

    series_slug: str | None = None
    """
    Series slug
    """

    original_title: str | None = None
    """
    Episode original title
    """

    _runtime: int | None = None
    """
    Episode runtime in seconds
    """

    runtime_obj: datetime.timedelta = None
    """
    Episode runtime as timedelta
    """

    image: str | None = None
    """
    Episode image URL
    """

    url: str | None = None
    """
    Episode URL
    """

    id: str | None = None
    """Episode unique ID"""

    language: Optional[str] = None
    """Episode language code"""

    @property
    def runtime(self):
        """
        Episode runtime in seconds
        """
        if self._runtime:
            return self._runtime
        elif self.runtime_obj:
            self._runtime = int(self.runtime_obj.total_seconds())
            return self._runtime
        else:
            return None

    @runtime.setter
    def runtime(self, value):
        if type(value) in (int, float):
            self._runtime = int(value)
        elif type(value) is datetime.timedelta:
            self.runtime_obj = value


class Provider:
    slug: str
    """Slug for use in urls"""
    name: str
    """Friendly name for display"""
    has_translations: bool = False
    has_orders: bool = False
    """Does the provider have alternate episode orders?"""
    has_search = False

    def __init__(self, cache=True, **kwargs):
        self._session = requests_cache.CachedSession(cache_file(self.slug))

    def _get(self, url, **kwargs) -> requests.Response:
        r"""Sends a GET request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :rtype: requests.Response
        """
        response = self._session.get(url, **kwargs)
        response.raise_for_status()
        return response

    def episodes(self, slug: str, **kwargs) -> list[Episode]:
        raise NotImplementedError

    def series(self, slug: str, **kwargs) -> Series:
        return Series(slug, **kwargs)

    def search(self, search: str, language='en') -> list[Series]:
        raise NotImplementedError


@dataclasses.dataclass
class Series:
    slug: str
    """Slug for use in urls"""
    title: str | None = None
    """Series title for display"""
    description: str | None = None
    image: str | None = None
    url: str | None = None
    language: str | None = None
    languages: dict | None = None
    original_language: str | None = None
    year: int | None = None
    orders: dict[str, str] | None = None
    """Season orders"""


def cache_file(key: str):
    path = Path(os.environ.get('PROVIDER_CACHE_PATH', 'provider_cache'))
    return path.joinpath(key).with_suffix('.sqlite')
