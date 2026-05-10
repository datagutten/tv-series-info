import dataclasses
from typing import Optional

from series_info.data import Episode, Series


class DisneyImage:
    _image_id: Optional[str] = None

    @property
    def image(self):
        return 'https://disney.images.edge.bamgrid.com/ripcut-delivery/v2/variant/disney/%s/compose?width=300' % self._image_id

    @image.setter
    def image(self, value):
        self._image_id = value


@dataclasses.dataclass
class DisneyPlusEpisode(DisneyImage, Episode):
    id: str | None = None


@dataclasses.dataclass
class DisneyPlusSeries(DisneyImage, Series):
    id: str | None = None
