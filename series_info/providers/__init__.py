from .disneyplus.disneyplus import DisneyPlus
from .nrk.nrk import NRKMeta
from .tvdb.api import TVDB

providers = {
    'disneyplus': DisneyPlus,
    'nrk': NRKMeta,
    'tvdb': TVDB,
}
