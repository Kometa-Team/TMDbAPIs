import pkg_resources

from tmdbapis.tmdb import TMDbAPIs
from tmdbapis.objs.simple import AlternativeName, AlternativeTitle, Certification, Country, CountryCertifications, \
    CountryWatchProviders, Department, FindResults, Genre, Group, Language, ReleaseDate, Timezones, Trailer, \
    Translation, User, Video, WatchProvider
from tmdbapis.objs.image import TMDbImage, Backdrop, Logo, Poster, Profile, Still, Tagged
from tmdbapis.objs.reload import TMDbReload, Account, Collection, Company, Configuration, Credit, Episode, \
    EpisodeGroup, Keyword, Movie, Network, Person, Review, Season, TVShow
from tmdbapis.exceptions import TMDbException, Invalid, NotFound, Unauthorized, Authentication

try:
    __version__ = pkg_resources.get_distribution("tmdbapis").version
except pkg_resources.DistributionNotFound:
    __version__ = ""
__author__ = "Nathan Taggart"
__credits__ = "meisnate12"
__package_name__ = "tmdbapis"
__project_name__ = "TMDbAPIs"
__description__ = "A lightweight Python library for The V3 and V4 TMDb APIs."
__url__ = "https://github.com/meisnate12/TMDbAPIs"
__email__ = "meisnate12@gmail.com"
__license__ = "MIT License"
__all__ = [
    "TMDbAPIs",
    "AlternativeName",
    "AlternativeTitle",
    "Certification",
    "Country",
    "CountryCertifications",
    "CountryWatchProviders",
    "Department",
    "FindResults",
    "Genre",
    "Group",
    "Language",
    "ReleaseDate",
    "Timezones",
    "Trailer",
    "Translation",
    "User",
    "Video",
    "WatchProvider",
    "TMDbImage",
    "Backdrop",
    "Logo",
    "Poster",
    "Profile",
    "Still",
    "Tagged",
    "TMDbReload",
    "Account",
    "Collection",
    "Company",
    "Configuration",
    "Credit",
    "Episode",
    "EpisodeGroup",
    "Keyword",
    "Movie",
    "Network",
    "Person",
    "Review",
    "Season",
    "TVShow",
    "TMDbException",
    "Invalid",
    "NotFound",
    "Unauthorized",
    "Authentication"
]
