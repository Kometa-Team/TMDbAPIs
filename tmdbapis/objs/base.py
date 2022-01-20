from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from tmdbapis.tmdb import TMDbAPIs
    from tmdbapis.api3 import API3
    from tmdbapis.api4 import API4


class TMDbObj(ABC):
    """ Base Class for TMDb Objects. """

    def __init__(self, tmdb: "TMDbAPIs", data):
        self._loading = True
        self._partial = False
        self._name = None
        self._tmdb = tmdb
        self._api: "API3" = tmdb._api if tmdb else None
        self._api4: "API4" = tmdb._api4 if tmdb else None
        self._load(data)

    @abstractmethod
    def _load(self, data):
        self._data = data
        self._loading = True
        self.id = None

    def _finish(self, name):
        self._name = name
        self._loading = False

    def _image_url(self, image_path):
        return f"{self._tmdb._image_url}{image_path}" if image_path else None

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        if self.id:
            return f"[{self.id}:{self._name}]"
        else:
            return self._name

    def __eq__(self, other):
        if type(self) is type(other):
            if self.id is None and other.id is None:
                return self._name == other._name
            elif self.id is not None and other.id is not None:
                return self.id == other.id
            else:
                return False
        elif isinstance(other, int) and self.id is not None:
            return self.id == other
        else:
            return str(self._name) == str(other)

    def __getattribute__(self, item):
        value = super().__getattribute__(item)
        if item.startswith("_") or self._loading or not self._partial or value is not None:
            return value
        self._load(None)
        return super().__getattribute__(item)

    def __setattr__(self, key, value):
        if key.startswith("_") or self._loading:
            super().__setattr__(key, value)
        else:
            raise AttributeError("Attributes cannot be edited")

    def __delattr__(self, key):
        raise AttributeError("Attributes cannot be deleted")

    def _parse(self, data=None, attrs: Optional[Union[str, list]] = None, value_type: str = "str",
               default_is_none: bool = False, is_list: bool = False, is_dict: bool = False, extend: bool = False,
               key: Any = None):
        """ Validate the value given from the options given.
    
            Parameters:
                attrs (Optional[Union[str, list]]): check data for these attributes.
                value_type (str): Type that the value is.
                default_is_none (bool): Makes default None.
                is_list (bool): value is list of values.
                is_dict (bool): value is dict of values.
                extend (bool): value is list of values.
                key (Any): extra key.

            Returns:
                Any: Parsed Value
        """

        if default_is_none is False and value_type in ["int", "float"]:
            default = 0
        elif default_is_none is False and is_list:
            default = []
        else:
            default = None

        value = self._data if data is None else data
        if attrs:
            if not isinstance(attrs, list):
                attrs = [attrs]
            for attr in attrs:
                if attr in value:
                    value = value[attr]
                else:
                    return default

        if value is None:
            return default
        elif extend:
            export_list = []
            for v in value:
                export_list.extend(self._parse(data=v, value_type=value_type, default_is_none=default_is_none, key=key))
            return export_list
        elif is_list:
            return [self._parse(data=v, value_type=value_type, default_is_none=default_is_none, key=key) for v in value]
        elif is_dict:
            return {k: self._parse(data=v, value_type=value_type, default_is_none=default_is_none, key=k)
                    for k, v in value.items()}
        elif value_type == "int":
            return int(value)
        elif value_type == "float":
            return float(value)
        elif value_type == "bool":
            if isinstance(value, bool):
                return value
            elif str(value).lower() in ["t", "true"]:
                return True
            elif str(value).lower() in ["f", "false"]:
                return False
            else:
                return default
        elif value_type == "date":
            if not value:
                return None
            elif "T" in value:
                return datetime.strptime(value[:-1].split(".")[0], "%Y-%m-%dT%H:%M:%S")
            else:
                return datetime.strptime(value, "%Y-%m-%d")
        elif value_type == "dict":
            return value
        elif value_type == "alternative_name":
            return tmdbapis.objs.simple.AlternativeName(self._tmdb, value)
        elif value_type == "alternative_title":
            return tmdbapis.objs.simple.AlternativeTitle(self._tmdb, value)
        elif value_type == "certification":
            return tmdbapis.objs.simple.Certification(self._tmdb, value)
        elif value_type == "load_country":
            return tmdbapis.objs.simple.Country(self._tmdb, value)
        elif value_type == "country_certification":
            return tmdbapis.objs.simple.CountryCertifications(self._tmdb, value, key)
        elif value_type == "country_watch_provider":
            return tmdbapis.objs.simple.CountryWatchProviders(self._tmdb, value, key)
        elif value_type == "load_department":
            return tmdbapis.objs.simple.Department(self._tmdb, value)
        elif value_type == "load_genre":
            return tmdbapis.objs.simple.Genre(self._tmdb, value)
        elif value_type == "group":
            return tmdbapis.objs.simple.Group(self._tmdb, value)
        elif value_type == "load_language":
            return tmdbapis.objs.simple.Language(self._tmdb, value)
        elif value_type == "release_date":
            return tmdbapis.objs.simple.ReleaseDate(self._tmdb, value)
        elif value_type == "load_timezone":
            return tmdbapis.objs.simple.Timezones(self._tmdb, value)
        elif value_type == "trailer":
            return tmdbapis.objs.simple.Trailer(self._tmdb, value)
        elif value_type == "translation":
            return tmdbapis.objs.simple.Translation(self._tmdb, value)
        elif value_type == "user":
            return tmdbapis.objs.simple.User(self._tmdb, value)
        elif value_type == "video":
            return tmdbapis.objs.simple.Video(self._tmdb, value)
        elif value_type == "watch_provider":
            return tmdbapis.objs.simple.WatchProvider(self._tmdb, value)
        elif value_type == "backdrop":
            return tmdbapis.objs.image.Backdrop(self._tmdb, value)
        elif value_type == "logo":
            return tmdbapis.objs.image.Logo(self._tmdb, value)
        elif value_type == "poster":
            return tmdbapis.objs.image.Poster(self._tmdb, value)
        elif value_type == "profile":
            return tmdbapis.objs.image.Profile(self._tmdb, value)
        elif value_type == "still":
            return tmdbapis.objs.image.Still(self._tmdb, value)
        elif value_type == "tagged":
            return tmdbapis.objs.image.Tagged(self._tmdb, value)
        elif value_type == "collection":
            return tmdbapis.objs.reload.Collection(self._tmdb, value)
        elif value_type == "company":
            return tmdbapis.objs.reload.Company(self._tmdb, value)
        elif value_type == "movie_cast":
            return tmdbapis.objs.reload.Credit(self._tmdb, value, credit_type="cast", media_type="movie")
        elif value_type == "movie_crew":
            return tmdbapis.objs.reload.Credit(self._tmdb, value, credit_type="crew", media_type="movie")
        elif value_type == "tv_cast":
            return tmdbapis.objs.reload.Credit(self._tmdb, value, credit_type="cast", media_type="tv")
        elif value_type == "tv_crew":
            return tmdbapis.objs.reload.Credit(self._tmdb, value, credit_type="crew", media_type="tv")
        elif value_type == "agg_tv_cast":
            cast = []
            for role in value["roles"]:
                new_dict = value.copy()
                for k, v in role.items():
                    new_dict[k] = v
                cast.append(tmdbapis.objs.reload.Credit(self._tmdb, new_dict, credit_type="cast", media_type="tv"))
            return cast
        elif value_type == "agg_tv_crew":
            crew = []
            for role in value["jobs"]:
                new_dict = value.copy()
                for k, v in role.items():
                    new_dict[k] = v
                crew.append(tmdbapis.objs.reload.Credit(self._tmdb, new_dict, credit_type="crew", media_type="tv"))
            return crew
        elif value_type == "keyword":
            return tmdbapis.objs.reload.Keyword(self._tmdb, value)
        elif value_type == "movie":
            return tmdbapis.objs.reload.Movie(self._tmdb, value)
        elif value_type == "network":
            return tmdbapis.objs.reload.Network(self._tmdb, value)
        elif value_type == "person":
            return tmdbapis.objs.reload.Person(self._tmdb, value)
        elif value_type == "review":
            return tmdbapis.objs.reload.Review(self._tmdb, value)
        elif value_type == "tv":
            return tmdbapis.objs.reload.TVShow(self._tmdb, value)
        elif value_type == "season":
            return tmdbapis.objs.reload.Season(self._tmdb, value, key)
        elif value_type == "episode":
            return tmdbapis.objs.reload.Episode(self._tmdb, value, key)
        elif value_type == "episode_group":
            return tmdbapis.objs.reload.EpisodeGroup(self._tmdb, value, key)
        elif value_type == "media_type":
            if value["media_type"] == "movie":
                return tmdbapis.objs.reload.Movie(self._tmdb, value)
            elif value["media_type"] == "tv":
                return tmdbapis.objs.reload.TVShow(self._tmdb, value)
            elif value["media_type"] == "person":
                return tmdbapis.objs.reload.Person(self._tmdb, value)
        elif value_type == "list":
            return tmdbapis.objs.pagination.TMDbList(self._tmdb, value)
        elif value_type == "movie_reviews":
            return tmdbapis.objs.pagination.MovieReviews(self._tmdb, value, key)
        elif value_type == "lists":
            return tmdbapis.objs.pagination.MovieLists(self._tmdb, value, key)
        elif value_type == "recommended_movies":
            return tmdbapis.objs.pagination.RecommendedMovies(self._tmdb, value, key)
        elif value_type == "similar_movies":
            return tmdbapis.objs.pagination.SimilarMovies(self._tmdb, value, key)
        elif value_type == "recommended_tv":
            return tmdbapis.objs.pagination.RecommendedTVShows(self._tmdb, value, key)
        elif value_type == "similar_tv":
            return tmdbapis.objs.pagination.SimilarTVShows(self._tmdb, value, key)
        elif value_type == "tagged_images":
            return tmdbapis.objs.pagination.TaggedImages(self._tmdb, value, key)
        elif value_type == "content_rating":
            return {v["iso_3166_1"]: v["rating"] for v in value}
        elif value_type in ["country", "language", "movie_genre", "tv_genre"]:
            return self._tmdb._get_object(value, value_type)
        else:
            return str(value)


import tmdbapis.objs.simple
import tmdbapis.objs.image
import tmdbapis.objs.reload
import tmdbapis.objs.pagination
