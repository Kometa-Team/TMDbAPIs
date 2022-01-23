import logging
from datetime import datetime
from typing import Optional, Union, List, Dict

import requests
from requests import Session

from tmdbapis import util
from tmdbapis.api3 import API3
from tmdbapis.api4 import API4
from tmdbapis.exceptions import Authentication, Invalid
from tmdbapis.objs.pagination import NowPlayingMovies, PopularMovies, TopRatedMovies, UpcomingMovies, Trending, PopularPeople, \
    TVShowsAiringToday, TVShowsOnTheAir, PopularTVShows, TopRatedTVShows, MovieRecommendations, TVShowRecommendations, \
    SearchCompanies, SearchCollections, SearchKeywords, SearchMovies, SearchMulti, SearchPeople, SearchTVShows, \
    CreatedLists, FavoriteMovies, FavoriteTVShows, RatedMovies, RatedTVShows, RatedEpisodes, MovieWatchlist, \
    TVShowWatchlist, DiscoverMovies, DiscoverTVShows
from tmdbapis.objs.pagination import TMDbList
from tmdbapis.objs.reload import Account, Collection, Configuration, Company, Credit, Keyword, Movie, \
    Network, Person, Review, TVShow, Season, Episode, EpisodeGroup
from tmdbapis.objs.simple import Country, CountryCertifications, Genre, WatchProvider, FindResults, Language

logger = logging.getLogger(__name__)


class TMDbAPIs:
    """ Main Object Class

        Parameters:
            apikey (str): TMDb V3 API Key.
            session_id (Optional[str]): TMDb V3 Session ID.
            v4_access_token (Optional[str]): TMDb V4 Access Token.
            language (str): Default TMDb language.
            session (Optional[Session]): Use you're own Session object

        Attributes:
            language (str): TMDb Language
            account_id (int): TMDb V3 Account ID.
            session_id (str): TMDb V3 Session ID.
            v4_account_id (str): TMDb V4 Account ID.
            v4_access_token (str):  TMDb V4 Access Token.
    """
    def __init__(self, apikey: str, session_id: Optional[str] = None, v4_access_token: Optional[str] = None, language="en", session: Optional[Session] = None):
        self._language = None
        self._session = Session() if session is None else session
        self._api4 = API4(v4_access_token, session=self._session) if v4_access_token else None
        self._api = API3(apikey, session_id=session_id, api4=self._api4, session=self._session, validate=False)
        self._request_token = None
        self._movie_certifications = None
        self._tv_certifications = None
        self._movie_genres = None
        self._movie_genre_lookups = None
        self._tv_genres = None
        self._tv_genre_lookups = None
        self._provider_regions = None
        self._movie_providers = None
        self._tv_providers = None
        self._config = None
        self._config = self.configuration()
        self._iso_3166_1 = {v.iso_3166_1: v for v in self._config.countries}
        self._iso_639_1 = {v.iso_639_1: v for v in self._config.languages}
        self._languages = self._config.primary_translations + [v.iso_639_1 for k, v in self._iso_639_1.items()]
        self._image_url = f"{self._config.secure_base_image_url}original"
        self.language = language
        self._include_language = f"{self.language[:2]},null" if len(self.language) > 2 else "null"

    @property
    def _movie_genre_lookup(self):
        if self._movie_genre_lookups is None:
            self._movie_genre_lookups = {g.id: g for g in self.movie_genres()}
        return self._movie_genre_lookups

    @property
    def _tv_genre_lookup(self):
        if self._tv_genre_lookups is None:
            self._tv_genre_lookups = {g.id: g for g in self.tv_genres()}
        return self._tv_genre_lookups

    def _get_object(self, lookup, obj_type):
        def object_check(lookup_obj, key, lookup_dict, is_int=False):
            if isinstance(lookup_obj, dict):
                lookup_obj = lookup_obj[key] if key in lookup_obj else None
            if is_int:
                lookup_obj = int(lookup_obj)
            return lookup_dict[lookup_obj] if lookup_obj in lookup_dict else None
        if obj_type == "country":
            return object_check(lookup, "iso_3166_1", self._iso_3166_1)
        elif obj_type == "language":
            return object_check(lookup, "iso_639_1", self._iso_639_1)
        elif obj_type == "movie_genre":
            return object_check(lookup, "id", self._movie_genre_lookup, is_int=True)
        elif obj_type == "tv_genre":
            return object_check(lookup, "id", self._tv_genre_lookup, is_int=True)
        else:
            return None

    @property
    def language(self):
        return self._language

    @language.setter
    def language(self, language):
        if language in self._languages:
            self._language = language
        else:
            raise Invalid(f"Language: {language} Invalid")

    @property
    def account_id(self):
        return self._api.account_id

    @property
    def session_id(self):
        return self._api.session_id

    @property
    def v4_account_id(self):
        return self._v4_check().account_id

    @property
    def v4_access_token(self):
        return self._v4_check().access_token

    def authenticate(self, username: str, password: str):
        """ Use this to authenticate the TMDb V3 Session.

            Parameters:
                username (str): TMDb Username.
                password (str): TMDb Password.
        """
        request_token = self._api.authentication_create_request_token()["request_token"]
        self._api.authentication_create_session_with_login(username, password, request_token)
        self._api.authentication_create_session(request_token)

    def v4_access(self, access_token: str):
        """ Use this method to set up TMDb's V4 API

            To gain read access to TMDb V4's API just provide you're TMDb V4 Access Token either with this method or by using the ``v4_access_token`` Parameter of the :class:`~tmdbapis.tmdb.TMDbAPIs` constructor.

            To gain write access to TMDb V4's API

                1. Gain Read Access
                2. Authenticate the URL returned from :meth:`v4_authenticate`.
                3. Approve the authentication using :meth:`v4_approved`.

            To get you're TMDb V3 Write Access Token use :attr:`TMDbAPIs.v4_access_token` After it's been approved.

            Parameters:
                access_token (str): TMDb V4 Access Token
        """
        self._api4 = API4(access_token, session=self._session)
        self._api._api4 = self._api4

    def _v4_check(self, write=False):
        if not self._api4:
            raise Authentication(f"Requires V4 API Read Access Token, use tmdbapis.v4_access(access_token)")
        if write and not self._api4.has_write_token:
            raise Authentication(f"Requires V4 API Write Access Token, use tmdbapis.v4_authenticate() and approve the returned URL then use tmdbapis.v4_approved()")
        return self._api4

    def v4_authenticate(self):
        """ Use this method to get the authentication URL for write access to TMDb V4 API """
        self._request_token = self._v4_check().auth_create_request_token()["request_token"]
        return f"https://www.themoviedb.org/auth/access?request_token={self._request_token}"

    def v4_approved(self):
        """ Use this method once the URL from :meth:`v4_authenticate` has been authenticated to gain write access to TMDb V4 API """
        if not self._request_token:
            raise Authentication("Requires V4 Authentication, use tmdbapis.v4_authenticate() and approve the returned URL")
        self._v4_check().auth_create_access_token(self._request_token)

    def account(self):
        """ :class:`~tmdbapis.objs.reload.Account` Object with your account details.

            Returns:
                :class:`~tmdbapis.objs.reload.Account`

            Raises:
                :class:`~tmdbapis.exceptions.Authentication`: When you haven't authenticated a session yet.
        """
        return Account(self)

    def created_lists(self, v3: bool = False):
        """ Paginated Object of all the lists created by an account. Will include private lists if you are the owner.

            Parameters:
                v3 (bool): Force List V3 Usage

            Returns:
                :class:`~tmdbapis.objs.pagination.CreatedLists`
        """
        return CreatedLists(self, v3=v3)

    def favorite_movies(self, sort_by: Optional[str] = None, v3: bool = False):
        """ Paginated Object of movies you have marked as a favorite.

            Parameters:
                sort_by (Optional[str]): How the results are sorted.
                v3 (bool): Force List V3 Usage

            .. list-table:: Sort Options
               :header-rows: 0

               * - ``created_at.asc``
                 - ``created_at.desc``
               * - ``release_date.asc`` *
                 - ``release_date.desc`` *
               * - ``title.asc`` *
                 - ``title.desc`` *
               * - ``vote_average.asc`` *
                 - ``vote_average.desc`` *

            \\* V4 Lists Only

            Returns:
                :class:`~tmdbapis.objs.pagination.FavoriteMovies`

            Raises:
                :class:`~tmdbapis.exceptions.Invalid`: When ``sort_by`` is not a valid option.
        """
        return FavoriteMovies(self, sort_by=util.validate_sort(sort_by, v3, True), v3=v3)

    def favorite_tv_shows(self, sort_by: Optional[str] = None, v3: bool = False):
        """ Paginated Object of TV shows you have marked as a favorite.

            Parameters:
                sort_by (Optional[str]): How the results are sorted.
                v3 (bool): Force List V3 Usage

            .. list-table:: Sort Options
               :header-rows: 0

               * - ``created_at.asc``
                 - ``created_at.desc``
               * - ``first_air_date.asc`` *
                 - ``first_air_date.desc`` *
               * - ``name.asc`` *
                 - ``name.desc`` *
               * - ``vote_average.asc`` *
                 - ``vote_average.desc`` *

            \\* V4 Lists Only

            Returns:
                :class:`~tmdbapis.objs.pagination.FavoriteTVShows`

            Raises:
                :class:`~tmdbapis.exceptions.Invalid`: When ``sort_by`` is not a valid option.
        """
        return FavoriteTVShows(self, sort_by=util.validate_sort(sort_by, v3, False), v3=v3)

    def rated_movies(self, sort_by: Optional[str] = None, v3: bool = False):
        """ Paginated Object of movies you have rated.

            Parameters:
                sort_by (Optional[str]): How the results are sorted.
                v3 (bool): Force List V3 Usage

            .. list-table:: Sort Options
               :header-rows: 0

               * - ``created_at.asc``
                 - ``created_at.desc``
               * - ``release_date.asc`` *
                 - ``release_date.desc`` *
               * - ``title.asc`` *
                 - ``title.desc`` *
               * - ``vote_average.asc`` *
                 - ``vote_average.desc`` *

            \\* V4 Lists Only

            Returns:
                :class:`~tmdbapis.objs.pagination.RatedMovies`

            Raises:
                :class:`~tmdbapis.exceptions.Invalid`: When ``sort_by`` is not a valid option.
        """
        return RatedMovies(self, sort_by=util.validate_sort(sort_by, v3, True), v3=v3)

    def rated_tv_shows(self, sort_by: Optional[str] = None, v3: bool = False):
        """ Paginated Object of TV shows you have rated.

            Parameters:
                sort_by (Optional[str]): How the results are sorted.
                v3 (bool): Force List V3 Usage

            .. list-table:: Sort Options
               :header-rows: 0

               * - ``created_at.asc``
                 - ``created_at.desc``
               * - ``first_air_date.asc`` *
                 - ``first_air_date.desc`` *
               * - ``name.asc`` *
                 - ``name.desc`` *
               * - ``vote_average.asc`` *
                 - ``vote_average.desc`` *

            \\* V4 Lists Only

            Returns:
                :class:`~tmdbapis.objs.pagination.RatedTVShows`

            Raises:
                :class:`~tmdbapis.exceptions.Invalid`: When ``sort_by`` is not a valid option.
        """
        return RatedTVShows(self, sort_by=util.validate_sort(sort_by, v3, False), v3=v3)

    def rated_episodes(self, sort_by: Optional[str] = None):
        """ Paginated Object of TV episodes you have rated.

            Parameters:
                sort_by (Optional[str]): How the results are sorted.

            .. list-table:: Sort Options
               :header-rows: 0

               * - ``created_at.asc``
                 - ``created_at.desc``

            Returns:
                :class:`~tmdbapis.objs.pagination.RatedEpisodes`

            Raises:
                :class:`~tmdbapis.exceptions.Invalid`: When ``sort_by`` is not a valid option.
        """
        return RatedEpisodes(self, sort_by=util.validate_sort(sort_by, True, False))

    def movie_watchlist(self, sort_by: Optional[str] = None, v3: bool = False):
        """ Paginated Object of movies you have added to your watchlist.

            Parameters:
                sort_by (Optional[str]): How the results are sorted.
                v3 (bool): Force List V3 Usage

            .. list-table:: Sort Options
               :header-rows: 0

               * - ``created_at.asc``
                 - ``created_at.desc``
               * - ``release_date.asc`` *
                 - ``release_date.desc`` *
               * - ``title.asc`` *
                 - ``title.desc`` *
               * - ``vote_average.asc`` *
                 - ``vote_average.desc`` *

            \\* V4 Lists Only

            Returns:
                :class:`~tmdbapis.objs.pagination.MovieWatchlist`

            Raises:
                :class:`~tmdbapis.exceptions.Invalid`: When ``sort_by`` is not a valid option.
        """
        return MovieWatchlist(self, sort_by=util.validate_sort(sort_by, v3, True), v3=v3)

    def tv_show_watchlist(self, sort_by: Optional[str] = None, v3: bool = False):
        """ Paginated Object of TV shows you have added to your watchlist.

            Parameters:
                sort_by (Optional[str]): How the results are sorted.
                v3 (bool): Force List V3 Usage

            .. list-table:: Sort Options
               :header-rows: 0

               * - ``created_at.asc``
                 - ``created_at.desc``
               * - ``first_air_date.asc`` *
                 - ``first_air_date.desc`` *
               * - ``name.asc`` *
                 - ``name.desc`` *
               * - ``vote_average.asc`` *
                 - ``vote_average.desc`` *

            \\* V4 Lists Only

            Returns:
                :class:`~tmdbapis.objs.reload.TVShowWatchlist`

            Raises:
                :class:`~tmdbapis.exceptions.Invalid`: When ``sort_by`` is not a valid option.
        """
        return TVShowWatchlist(self, sort_by=util.validate_sort(sort_by, v3, False), v3=v3)

    def movie_recommendations(self, sort_by: Optional[str] = None):
        """ Paginated Object of your personal movie recommendations. (V4 Lists Only)

            Parameters:
                sort_by (Optional[str]): How the results are sorted.

            .. list-table:: Sort Options
               :header-rows: 0

               * - ``created_at.asc``
                 - ``created_at.desc``
               * - ``release_date.asc`` 
                 - ``release_date.desc`` 
               * - ``title.asc`` 
                 - ``title.desc`` 
               * - ``vote_average.asc`` 
                 - ``vote_average.desc``

            Returns:
                :class:`~tmdbapis.objs.pagination.MovieRecommendations`

            Raises:
                :class:`~tmdbapis.exceptions.Invalid`: When ``sort_by`` is not a valid option.
        """
        return MovieRecommendations(self, sort_by=util.validate_sort(sort_by, False, True))

    def tv_show_recommendations(self, sort_by: Optional[str] = None):
        """ Paginated Object of your personal TV show recommendations. (V4 Lists Only)

            Parameters:
                sort_by (Optional[str]): How the results are sorted.

            .. list-table:: Sort Options
               :header-rows: 0

               * - ``created_at.asc``
                 - ``created_at.desc``
               * - ``first_air_date.asc``
                 - ``first_air_date.desc``
               * - ``name.asc``
                 - ``name.desc``
               * - ``vote_average.asc``
                 - ``vote_average.desc``

            Returns:
                :class:`~tmdbapis.objs.reload.TVShowRecommendations`

            Raises:
                :class:`~tmdbapis.exceptions.Invalid`: When ``sort_by`` is not a valid option.
        """
        return TVShowRecommendations(self, sort_by=util.validate_sort(sort_by, False, False))

    def logout(self):
        """ End all V3 and V4 Authenticated Sessions """
        if self._api._session_id:
            self._api.authentication_delete_session(self._api._session_id)
        if self._api4:
            if self._api4.has_write_token:
                self._api4.auth_delete_access_token(self._api4.access_token)

    def movie_certifications(self, reload: bool = False) -> Dict[str, CountryCertifications]:
        """ Get an up to date list of the officially supported movie certifications on TMDB.

            Parameters:
                reload (bool): Reload the cached movie certifications

            Returns:
                Dict[str, :class:`~tmdbapis.objs.simple.CountryCertifications`]
        """
        if reload or self._movie_certifications is None:
            self._movie_certifications = {
                k: CountryCertifications(self, v, k) for k, v in
                self._api.certifications_get_movie_certifications()["certifications"].items()
            }
        return self._movie_certifications

    def tv_certifications(self, reload: bool = False) -> Dict[str, CountryCertifications]:
        """ Get an up to date list of the officially supported TV show certifications on TMDB.

            Parameters:
                reload (bool): Reload the cached tv certifications

            Returns:
                Dict[str, :class:`~tmdbapis.objs.simple.CountryCertifications`]
        """
        if reload or self._tv_certifications is None:
            self._tv_certifications = {
                k: CountryCertifications(self, v, k) for k, v in
                self._api.certifications_get_tv_certifications()["certifications"].items()
            }
        return self._tv_certifications

    def movie_change_list(self,
                          start_date: Optional[Union[datetime, str]] = None,
                          end_date: Optional[Union[datetime, str]] = None
                          ) -> List[Movie]:
        """ Get a list of :class:`~tmdbapis.objs.reload.Movie` that have been changed in the past 24 hours.

            You can query it for up to 14 days worth of changed Movies at a time with the ``start_date`` and ``end_date``
            query parameters.

            Parameters:
                start_date (Optional[Union[datetime, str]]): Filter the results with a start date. Format: YYYY-MM-DD
                end_date (Optional[Union[datetime, str]]): Filter the results with an end date. Format: YYYY-MM-DD

            Returns:
                List[:class:`~tmdbapis.objs.reload.Movie`]

            Raises:
                :class:`~tmdbapis.exceptions.Invalid`: When ``start_date`` or ``end_date`` is in an incorrect format.
        """
        return [Movie(self, data) for data in self._api.changes_get_movie_change_list(
            start_date=util.validate_date(start_date),
            end_date=util.validate_date(end_date)
        )["results"]]

    def tv_change_list(self,
                       start_date: Optional[Union[datetime, str]] = None,
                       end_date: Optional[Union[datetime, str]] = None
                       ) -> List[TVShow]:
        """ Get a list of :class:`~tmdbapis.objs.reload.TV` that have been changed in the past 24 hours.

            You can query it for up to 14 days worth of changed Shows at a time with the ``start_date`` and ``end_date``
            query parameters.

            Parameters:
                start_date (Optional[Union[datetime, str]]): Filter the results with a start date. Format: YYYY-MM-DD
                end_date (Optional[Union[datetime, str]]): Filter the results with an end date. Format: YYYY-MM-DD

            Returns:
                List[:class:`~tmdbapis.objs.reload.TVShow`]

            Raises:
                :class:`~tmdbapis.exceptions.Invalid`: When ``start_date`` or ``end_date`` is in an incorrect format.
        """
        return [TVShow(self, data) for data in self._api.changes_get_tv_change_list(
            start_date=util.validate_date(start_date),
            end_date=util.validate_date(end_date)
        )["results"]]

    def person_change_list(self,
                           start_date: Optional[Union[datetime, str]] = None,
                           end_date: Optional[Union[datetime, str]] = None
                           ) -> List[Person]:
        """ Get a list of :class:`~tmdbapis.objs.pagination.Person` that have been changed in the past 24 hours.

            You can query it for up to 14 days worth of changed People at a time with the ``start_date`` and ``end_date``
            query parameters.

            Parameters:
                start_date (Optional[Union[datetime, str]]): Filter the results with a start date. Format: YYYY-MM-DD
                end_date (Optional[Union[datetime, str]]): Filter the results with an end date. Format: YYYY-MM-DD

            Returns:
                List[:class:`~tmdbapis.objs.pagination.Person`]

            Raises:
                :class:`~tmdbapis.exceptions.Invalid`: When ``start_date`` or ``end_date`` is in an incorrect format.
        """
        return [Person(self, data) for data in self._api.changes_get_person_change_list(
            start_date=util.validate_date(start_date),
            end_date=util.validate_date(end_date)
        )["results"]]

    def collection(self, collection_id: int, load: bool = True) -> Collection:
        """ Gets the :class:`~tmdbapis.objs.reload.Collection` for the given id.

            Parameters:
                collection_id (int): Collection ID of the collection you want.
                load (bool): Load the data on creation.

            Returns:
                :class:`~tmdbapis.objs.reload.Collection`

            Raises:
                :class:`~tmdbapis.exceptions.NotFound`: When no collection is found for the given id.
        """
        return Collection(self, {"id": collection_id}, load=load)

    def company(self, company_id: int, load: bool = True) -> Company:
        """ Gets the :class:`~tmdbapis.objs.reload.Company` for the given id.

            Parameters:
                company_id (int): Company ID of the company you want.
                load (bool): Load the data on creation.

            Returns:
                :class:`~tmdbapis.objs.reload.Company`

            Raises:
                :class:`~tmdbapis.exceptions.NotFound`: When no company is found for the given id.
        """
        return Company(self, {"id": company_id}, load=load)

    def configuration(self, reload: bool = False) -> Configuration:
        """ Gets the TMDb :class:`~tmdbapis.objs.reload.Configuration`.

            Parameters:
                reload (bool): Reload the cached :class:`~tmdbapis.objs.reload.Configuration`.

            Returns:
                :class:`~tmdbapis.objs.reload.Configuration`
        """
        if reload or self._config is None:
            self._config = Configuration(self)
        return self._config

    def credit(self, credit_id: str, load: bool = True) -> Credit:
        """ Gets the :class:`~tmdbapis.objs.reload.Credit` for the given id.

            Parameters:
                credit_id (str): Credit ID of the credit you want.
                load (bool): Load the data on creation.

            Returns:
                :class:`~tmdbapis.objs.reload.Credit`

            Raises:
                :class:`~tmdbapis.exceptions.NotFound`: When no credit is found for the given id.
        """
        return Credit(self, {"id": credit_id, "person": {}}, load=load)

    def discover_movies(self, **kwargs) -> DiscoverMovies:
        """ Discover movies by different types of data like average rating, number of votes, genres and certifications.
            You can get a valid list of certifications from the :meth:`movie_certifications` method.

            Discover also supports a nice list of sort options. See below for all of the available options.

            Please note, when using ``certification`` \\ ``certification.lte`` you must also specify
            ``certification_country``. These two parameters work together in order to filter the results. You can only
            filter results with the countries added to :meth:`movie_certifications`.

            If you specify the ``region`` parameter, the regional release date will be used instead of the primary
            release date. The date returned will be the first date based on your query (ie. if a ``with_release_type``
            is specified). It's important to note the order of the release types that are used. Specifying "2|3" would
            return the limited theatrical release date as opposed to "3|2" which would return the theatrical date.

            Also note that a number of filters support being comma (``,``) or pipe (``|``) separated. Comma's are
            treated like an ``AND`` and query while pipe's are an ``OR``.

            ``.`` cannot be included directly in the function parameters so the parameters must be provided as a
            kwargs dictionary.

            Parameters:
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                region (Optional[str]): ISO-3166-1 code to filter release dates. Must be uppercase.
                sort_by (Optional[str]): Allowed Values: ``popularity.asc``, ``popularity.desc``, ``release_date.asc``, ``release_date.desc``, ``revenue.asc``, ``revenue.desc``, ``primary_release_date.asc``, ``primary_release_date.desc``, ``original_title.asc``, ``original_title.desc``, ``vote_average.asc``, ``vote_average.desc``, ``vote_count.asc``, ``vote_count.desc``
                certification_country (Optional[str]): Used in conjunction with the ``certification`` filter, use this to specify a country with a valid certification.
                certification (Optional[str]): Filter results with a valid certification from the ``certification_country`` field.
                certification.lte (Optional[str]): Filter and only include movies that have a certification that is less than or equal to the specified value.
                certification.gte (Optional[str]): Filter and only include movies that have a certification that is greater than or equal to the specified value.
                include_adult (Optional[bool]): A filter and include or exclude adult movies.
                include_video (Optional[bool]): A filter to include or exclude videos.
                page (Optional[int]): Specify the page of results to query.
                primary_release_year (Optional[int): A filter to limit the results to a specific primary release year.
                primary_release_date.gte (Optional[str]): Filter and only include movies that have a primary release date that is greater or equal to the specified value. Format: YYYY-MM-DD
                primary_release_date.lte (Optional[str]): Filter and only include movies that have a primary release date that is less than or equal to the specified value. Format: YYYY-MM-DD
                release_date.gte (Optional[str]): Filter and only include movies that have a release date (looking at all release dates) that is greater or equal to the specified value. Format: YYYY-MM-DD
                release_date.lte (Optional[str]): Filter and only include movies that have a release date (looking at all release dates) that is less than or equal to the specified value. Format: YYYY-MM-DD
                with_release_type (Optional[int]): Specify a comma (AND) or pipe (OR) separated value to filter release types by. These release types map to the same values found on the movie release date method.
                year (Optional[int]): A filter to limit the results to a specific year (looking at all release dates).
                vote_count.gte (Optional[int]): Filter and only include movies that have a vote count that is greater or equal to the specified value.
                vote_count.lte (Optional[int]): Filter and only include movies that have a vote count that is less than or equal to the specified value.
                vote_average.gte (Optional[float]): Filter and only include movies that have a rating that is greater or equal to the specified value.
                vote_average.lte (Optional[float]): Filter and only include movies that have a rating that is less than or equal to the specified value.
                with_cast (Optional[str]): A comma separated list of person ID's. Only include movies that have one of the ID's added as an actor.
                with_crew (Optional[str]): A comma separated list of person ID's. Only include movies that have one of the ID's added as a crew member.
                with_people (Optional[str]): A comma separated list of person ID's. Only include movies that have one of the ID's added as a either a actor or a crew member.
                with_companies (Optional[str]): A comma separated list of production company ID's. Only include movies that have one of the ID's added as a production company.
                with_genres (Optional[str]): Comma separated value of genre ids that you want to include in the results.
                without_genres (Optional[str]): Comma separated value of genre ids that you want to exclude from the results.
                with_keywords (Optional[str]): A comma separated list of keyword ID's. Only includes movies that have one of the ID's added as a keyword.
                without_keywords (Optional[str]): Exclude items with certain keywords. You can comma and pipe separate these values to create an 'AND' or 'OR' logic.
                with_runtime.gte (Optional[int]): Filter and only include movies that have a runtime that is greater or equal to a value.
                with_runtime.lte (Optional[int]): Filter and only include movies that have a runtime that is less than or equal to a value..000
                with_original_language (Optional[str]): Specify an ISO 639-1 string to filter results by their original language value.
                with_watch_providers (Optional[str]): A comma or pipe separated list of watch provider ID's. Combine this filter with ``watch_region`` in order to filter your results by a specific watch provider in a specific region.
                watch_region (Optional[str]): An ISO 3166-1 code. Combine this filter with ``with_watch_providers`` in order to filter your results by a specific watch provider in a specific region.
                with_watch_monetization_types (Optional[str]): In combination with ``watch_region``, you can filter by monetization type. Allowed Values: ``flatrate``, ``free``, ``ads``, ``rent``, ``buy``

            Returns:
                :class:`~tmdbapis.objs.pagination.DiscoverMovies`

            Raises:
                :class:`~tmdbapis.exceptions.Invalid`: When one of the attributes given is Invalid.
        """
        return DiscoverMovies(self, **util.validate_discover(True, **kwargs))

    def discover_tv_shows(self, **kwargs) -> DiscoverTVShows:
        """ Discover TV shows by different types of data like average rating, number of votes, genres, the network they
            aired on and air dates.

            Discover also supports a nice list of sort options. See below for all of the available options.

            Also note that a number of filters support being comma (``,``) or pipe (``|``) separated. Comma's are
            treated like an ``AND`` and query while pipe's are an ``OR``.

            ``.`` cannot be included directly in the function parameters so the parameters must be provided as a
            kwargs dictionary.

            Parameters:
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                sort_by (Optional[str]): Allowed Values: ``vote_average.desc``, ``vote_average.asc``, ``first_air_date.desc``, ``first_air_date.asc``, ``popularity.desc``, ``popularity.asc``
                air_date.gte (Optional[str]): Filter and only include TV shows that have a air date (by looking at all episodes) that is greater or equal to the specified value. Format: YYYY-MM-DD
                air_date.lte (Optional[str]): Filter and only include TV shows that have a air date (by looking at all episodes) that is less than or equal to the specified value. Format: YYYY-MM-DD
                first_air_date.gte (Optional[str]): Filter and only include TV shows that have a original air date that is greater or equal to the specified value. Can be used in conjunction with the ``include_null_first_air_dates`` filter if you want to include items with no air date. Format: YYYY-MM-DD
                first_air_date.lte (Optional[str]): Filter and only include TV shows that have a original air date that is less than or equal to the specified value. Can be used in conjunction with the ``include_null_first_air_dates`` filter if you want to include items with no air date. Format: YYYY-MM-DD
                first_air_date_year (Optional[int]): Filter and only include TV shows that have a original air date year that equal to the specified value. Can be used in conjunction with the ``include_null_first_air_dates`` filter if you want to include items with no air date.
                page (Optional[int]): Specify the page of results to query.
                timezone (Optional[str]): Used in conjunction with the ``air_date.gte``/``air_date.lte`` filter to calculate the proper UTC offset.
                vote_average.gte (Optional[float]): Filter and only include TV shows that have a rating that is greater or equal to the specified value.
                vote_average.lte (Optional[float]): Filter and only include TV shows that have a rating that is less than or equal to the specified value.
                vote_count.gte (Optional[int]): Filter and only include TV shows that have a vote count that is greater or equal to the specified value.
                vote_count.lte (Optional[int]): Filter and only include TV shows that have a vote count that is less than or equal to the specified value.
                with_genres (Optional[str]): Comma separated value of genre ids that you want to include in the results.
                with_networks (Optional[str]): Comma separated value of network ids that you want to include in the results.
                without_genres (Optional[str]): Comma separated value of genre ids that you want to exclude from the results.
                with_runtime.gte (Optional[int]): Filter and only include TV shows with an episode runtime that is greater than or equal to a value.
                with_runtime.lte (Optional[int]): Filter and only include TV shows with an episode runtime that is less than or equal to a value.
                include_null_first_air_dates (Optional[bool]): Use this filter to include TV shows that don't have an air date while using any of the ``first_air_date`` filters.
                with_original_language (Optional[str]): Specify an ISO 639-1 string to filter results by their original language value.
                without_keywords (Optional[str]): Exclude items with certain keywords. You can comma and pipe separate these values to create an 'AND' or 'OR' logic.
                screened_theatrically (Optional[bool]): Filter results to include items that have been screened theatrically.
                with_companies (Optional[str]): A comma separated list of production company ID's. Only include movies that have one of the ID's added as a production company.
                with_keywords (Optional[str]): A comma separated list of keyword ID's. Only includes TV shows that have one of the ID's added as a keyword.
                with_watch_providers (Optional[str]): A comma or pipe separated list of watch provider ID's. Combine this filter with ``watch_region`` in order to filter your results by a specific watch provider in a specific region.
                watch_region (Optional[str]): An ISO 3166-1 code. Combine this filter with ``with_watch_providers`` in order to filter your results by a specific watch provider in a specific region.
                with_watch_monetization_types (Optional[str]): In combination with ``watch_region``, you can filter by monetization type. Allowed Values: ``flatrate``, ``free``, ``ads``, ``rent``, ``buy``

            Returns:
                :class:`~tmdbapis.objs.pagination.DiscoverTVShows`

            Raises:
                :class:`~tmdbapis.exceptions.Invalid`: When one of the attributes given is Invalid.
        """
        return DiscoverTVShows(self, **util.validate_discover(False, **kwargs))

    def find_by_id(self, imdb_id: Optional[str] = None, freebase_mid: Optional[str] = None, freebase_id: Optional[str] = None,
                   tvdb_id: Optional[str] = None, tvrage_id: Optional[str] = None, facebook_id: Optional[str] = None,
                   twitter_id: Optional[str] = None, instagram_id: Optional[str] = None) -> FindResults:
        """ Gets the :class:`~tmdbapis.objs.simple.FindResults` for the given external id.

            Parameters:
                imdb_id (str): IMDb ID to find.
                freebase_mid (str): Freebase MID to find.
                freebase_id (str): Freebase ID to find.
                tvdb_id (str): TVDb ID to find.
                tvrage_id (str): TVRage ID to find.
                facebook_id (str): Facebook ID to find.
                twitter_id (str): Twitter ID to find.
                instagram_id (str): Instagram ID to find.

            Returns:
                :class:`~tmdbapis.objs.simple.FindResults`

            Raises:
                :class:`~tmdbapis.exceptions.NotFound`: When no results are returned.
                :class:`~tmdbapis.exceptions.Invalid`: When no external id is given.
        """
        if imdb_id:
            return FindResults(self, imdb_id, "imdb_id")
        elif freebase_mid:
            return FindResults(self, freebase_mid, "freebase_mid")
        elif freebase_id:
            return FindResults(self, freebase_id, "freebase_id")
        elif tvdb_id:
            return FindResults(self, tvdb_id, "tvdb_id")
        elif tvrage_id:
            return FindResults(self, tvrage_id, "tvrage_id")
        elif facebook_id:
            return FindResults(self, facebook_id, "facebook_id")
        elif twitter_id:
            return FindResults(self, twitter_id, "twitter_id")
        elif instagram_id:
            return FindResults(self, instagram_id, "instagram_id")
        else:
            raise Invalid("At least one ID is required")

    def movie_genres(self, reload: bool = False) -> List[Genre]:
        """ Gets a list of all movie :class:`~tmdbapis.objs.simple.Genre`.

            Parameters:
                reload (bool): Reload the cached movie genres.

            Returns:
                List[:class:`~tmdbapis.objs.simple.Genre`]
        """
        if reload or self._movie_genres is None:
            self._movie_genres = [Genre(self, g) for g in self._api.genres_get_movie_list()["genres"]]
        return self._movie_genres

    def tv_genres(self, reload: bool = False) -> List[Genre]:
        """ Gets a list of all TV show :class:`~tmdbapis.objs.simple.Genre`.

            Parameters:
                reload (bool): Reload the cached movie genres.

            Returns:
                List[:class:`~tmdbapis.objs.simple.Genre`]
        """
        if reload or self._tv_genres is None:
            self._tv_genres = [Genre(self, g) for g in self._api.genres_get_tv_list()["genres"]]
        return self._tv_genres

    def keyword(self, keyword_id: int, load: bool = True) -> Keyword:
        """ Gets the :class:`~tmdbapis.objs.reload.Keyword` for the given id.

            Parameters:
                keyword_id (int): Keyword ID of the keyword you want.
                load (bool): Load the data on creation.

            Returns:
                :class:`~tmdbapis.objs.reload.Keyword`

            Raises:
                :class:`~tmdbapis.exceptions.NotFound`: When no keyword is found for the given id.
        """
        return Keyword(self, {"id": keyword_id}, load=load)

    def list(self, list_id: int, load: bool = True) -> TMDbList:
        """ Gets the :class:`~tmdbapis.objs.pagination.TMDbList` for the given id.

            Parameters:
                list_id (str): Keyword ID of the list you want.
                load (bool): Load the data on creation.

            Returns:
                :class:`~tmdbapis.objs.pagination.TMDbList`

            Raises:
                :class:`~tmdbapis.exceptions.NotFound`: When no list is found for the given id.
        """
        return TMDbList(self, {"id": list_id}, load=load)

    def create_list(self, name: str, iso_639_1: Union[Language, str], description: Optional[str] = "",
                    public: bool = True, iso_3166_1: Optional[Union[Country, str]] = None, load: bool = True) -> Union[TMDbList, int]:
        """ Creates a new List on TMDb and returns either a :class:`~tmdbapis.objs.pagination.TMDbList` Object or the List ID.

            Parameters:
                name (str): Name of the List.
                iso_639_1 (Union[Language, str]): ISO 639-1 Language Code of the List or :class:`tmdbapis.objs.simple.Language` Object.
                description (Optional[str]): Description of the List.
                public (bool): Determine if the list is a public list. (V4 Lists Only)
                iso_3166_1 (Optional[Union[Country, str]]): ISO 3166-1 Alpha-2 Country Code of the List or :class:`tmdbapis.objs.simple.Country` Object. (V4 Lists Only)
                load (bool): Load the list to return after creating it or just return the created List ID.

            Returns:
                Union[:class:`~tmdbapis.objs.pagination.TMDbList`, int]
        """
        if self._api4 and self._api4.has_write_token:
            list_id = self._v4_check(write=True).list_create_list(
                name,
                util.validate_language(iso_639_1, self._iso_639_1),
                description=description,
                public=public,
                iso_3166_1=util.validate_country(iso_3166_1, self._iso_3166_1)
            )["id"]
        else:
            list_id = self._api.lists_create_list(
                name=name, description=description, language=util.validate_language(iso_639_1, self._iso_639_1)
            )["list_id"]
        return self.list(list_id) if load else int(list_id)

    def movie(self, movie_id: int, load: bool = True) -> Movie:
        """ Gets the :class:`~tmdbapis.objs.reload.Movie` for the given id.

            Parameters:
                movie_id (str): Movie ID of the movie you want.
                load (bool): Load the data on creation.

            Returns:
                :class:`~tmdbapis.objs.reload.Movie`

            Raises:
                :class:`~tmdbapis.exceptions.NotFound`: When no keyword is found for the given id.
        """
        return Movie(self, {"id": movie_id}, load=load)

    def latest_movie(self) -> Movie:
        """ Gets the latest :class:`~tmdbapis.objs.reload.Movie` added on TMDb.

            Returns:
                :class:`~tmdbapis.objs.reload.Movie`
        """
        return Movie(self, self._api.movies_get_latest(language=self.language))

    def now_playing_movies(self, region: Optional[Union[Country, str]] = None) -> NowPlayingMovies:
        """ Paginated Object of Movies Now playing in theaters.

            Parameters:
                region (Optional[Union[Country, str]]): ISO 3166-1 Alpha-2 Country Code or :class:`tmdbapis.objs.simple.Country` Object to narrow the search to only look for theatrical release dates within the specified country.

            Returns:
                :class:`~tmdbapis.objs.pagination.NowPlayingMovies`

            Raises:
                :class:`~tmdbapis.exceptions.Invalid`: When the Country provided is not valid.
        """
        return NowPlayingMovies(self, region=util.validate_country(region, self._iso_3166_1))

    def popular_movies(self, region: Optional[Union[Country, str]] = None) -> PopularMovies:
        """ Paginated Object of Popular Movies on TMDb.

            Parameters:
                region (Optional[Union[Country, str]]): ISO 3166-1 Alpha-2 Country Code or :class:`tmdbapis.objs.simple.Country` Object to narrow the search to only look for theatrical release dates within the specified country.

            Returns:
                :class:`~tmdbapis.objs.pagination.PopularMovies`

            Raises:
                :class:`~tmdbapis.exceptions.Invalid`: When the Country provided is not valid.
        """
        return PopularMovies(self, region=util.validate_country(region, self._iso_3166_1))

    def top_rated_movies(self, region: Optional[Union[Country, str]] = None) -> TopRatedMovies:
        """ Paginated Object of the Top Rated Movies on TMDb.

            Parameters:
                region (Optional[Union[Country, str]]): ISO 3166-1 Alpha-2 Country Code or :class:`tmdbapis.objs.simple.Country` Object to narrow the search to only look for theatrical release dates within the specified country.

            Returns:
                :class:`~tmdbapis.objs.pagination.TopRatedMovies`

            Raises:
                :class:`~tmdbapis.exceptions.Invalid`: When the Country provided is not valid.
        """
        return TopRatedMovies(self, region=util.validate_country(region, self._iso_3166_1))

    def upcoming_movies(self, region: Optional[Union[Country, str]] = None) -> UpcomingMovies:
        """ Paginated Object of Upcoming Movies.

            Parameters:
                region (Optional[Union[Country, str]]): ISO 3166-1 Alpha-2 Country Code or :class:`tmdbapis.objs.simple.Country` Object to narrow the search to only look for theatrical release dates within the specified country.

            Returns:
                :class:`~tmdbapis.objs.pagination.UpcomingMovies`

            Raises:
                :class:`~tmdbapis.exceptions.Invalid`: When the Country provided is not valid.
        """
        return UpcomingMovies(self, region=util.validate_country(region, self._iso_3166_1))

    def network(self, network_id: int, load: bool = True) -> Network:
        """ Gets the :class:`~tmdbapis.objs.reload.Network` for the given id.

            Parameters:
                network_id (int): Network ID of the network you want.
                load (bool): Load the data on creation.

            Returns:
                :class:`~tmdbapis.objs.reload.Network`

            Raises:
                :class:`~tmdbapis.exceptions.NotFound`: When no network is found for the given id.
        """
        return Network(self, {"id": network_id}, load=load)

    def trending(self, media_type: str, time_window: str) -> Trending:
        """ Gets the :class:`~tmdbapis.objs.pagination.Trending` for the given id.

            Parameters:
                media_type (str): Trending media type. Allowed Values: ``all``, ``movie``, ``tv``, and ``person``
                time_window (str): Trending list time window. Allowed Values: ``day`` and ``week``

            Returns:
                :class:`~tmdbapis.objs.pagination.Trending`

            Raises:
                :class:`~tmdbapis.exceptions.Invalid`: When ``media_type`` or ``time_window`` is given an invalid option.
        """
        if media_type not in ["all", "movie", "tv", "person"]:
            raise Invalid(f"media_type: {media_type} Invalid. Options: all, movie, tv, or person")
        if time_window not in ["day", "week"]:
            raise Invalid(f"time_window: {time_window} Invalid. Options: day or week")
        return Trending(self, media_type, time_window)

    def person(self, person_id: int, load: bool = True) -> Person:
        """ Gets the :class:`~tmdbapis.objs.reload.Person` for the given id.

            Parameters:
                person_id (int): Person ID of the person you want.
                load (bool): Load the data on creation.

            Returns:
                :class:`~tmdbapis.objs.reload.Person`

            Raises:
                :class:`~tmdbapis.exceptions.NotFound`: When no person is found for the given id.
        """
        return Person(self, {"id": person_id}, load=load)

    def latest_person(self) -> Person:
        """ Gets the latest :class:`~tmdbapis.objs.reload.Person` added on TMDb.

            Returns:
                :class:`~tmdbapis.objs.reload.Person`
        """
        return Person(self, self._api.people_get_latest(language=self.language))

    def popular_people(self) -> PopularPeople:
        """ Paginated Object of Popular People on TMDb.

            Returns:
                :class:`~tmdbapis.objs.pagination.PopularPeople`
        """
        return PopularPeople(self)

    def review(self, review_id: str, load: bool = True) -> Review:
        """ Gets the :class:`~tmdbapis.objs.reload.Review` for the given id.

            Parameters:
                review_id (str): Review ID of the review you want.
                load (bool): Load the data on creation.

            Returns:
                :class:`~tmdbapis.objs.reload.Review`

            Raises:
                :class:`~tmdbapis.exceptions.NotFound`: When no review is found for the given id.
        """
        return Review(self, {"id": review_id}, load=load)

    def company_search(self, query: str) -> SearchCompanies:
        """ Searches TMDb for companies.

            Parameters:
                query (str): Query to search for.

            Returns:
                :class:`~tmdbapis.objs.pagination.SearchCompanies`

            Raises:
                :class:`~tmdbapis.exceptions.NotFound`: When no results are found for the search.
        """
        return SearchCompanies(self, query)

    def collection_search(self, query: str) -> SearchCollections:
        """ Searches TMDb for collections.

            Parameters:
                query (str): Query to search for.

            Returns:
                :class:`~tmdbapis.objs.pagination.SearchCollections`

            Raises:
                :class:`~tmdbapis.exceptions.NotFound`: When no results are found for the search.
        """
        return SearchCollections(self, requests.utils.quote(query))

    def keyword_search(self, query: str) -> SearchKeywords:
        """ Searches TMDb for keywords.

            Parameters:
                query (str): Query to search for.

            Returns:
                :class:`~tmdbapis.objs.pagination.SearchKeywords`

            Raises:
                :class:`~tmdbapis.exceptions.NotFound`: When no results are found for the search.
        """
        return SearchKeywords(self, requests.utils.quote(query))

    def movie_search(self, query: str, include_adult: Optional[bool] = None,
                     region: Optional[Union[Country, str]] = None, year: Optional[int] = None,
                     primary_release_year: Optional[int] = None) -> SearchMovies:
        """ Searches TMDb for movies.

            Parameters:
                query (str): Query to search for.
                include_adult (Optional[bool]): Choose whether to include adult (pornography) content in the results.
                region (Optional[Union[Country, str]]): Specify a ISO 3166-1 code or :class:`tmdbapis.objs.simple.Country` Object to filter release dates. Must be uppercase.
                year (Optional[int]): Specify a year for the search.
                primary_release_year (Optional[int]): Specify a primary release year for the search.

            Returns:
                :class:`~tmdbapis.objs.pagination.SearchMovies`

            Raises:
                :class:`~tmdbapis.exceptions.NotFound`: When no results are found for the search.
        """
        return SearchMovies(self, requests.utils.quote(query), include_adult=include_adult,
                            region=util.validate_country(region, self._iso_3166_1),
                            year=year, primary_release_year=primary_release_year)

    def multi_search(self, query: str, include_adult: Optional[bool] = None,
                     region: Optional[Union[Country, str]] = None) -> SearchMulti:
        """ Searches TMDb for movies, tv shows, and people.

            Parameters:
                query (str): Query to search for.
                include_adult (Optional[bool]): Choose whether to include adult (pornography) content in the results.
                region (Optional[Union[Country, str]]): Specify a ISO 3166-1 code or :class:`tmdbapis.objs.simple.Country` Object to filter release dates. Must be uppercase.

            Returns:
                :class:`~tmdbapis.objs.pagination.SearchMulti`

            Raises:
                :class:`~tmdbapis.exceptions.NotFound`: When no results are found for the search.
        """
        return SearchMulti(self, requests.utils.quote(query), include_adult=include_adult,
                           region=util.validate_country(region, self._iso_3166_1))

    def people_search(self, query: str, include_adult: Optional[bool] = None,
                      region: Optional[Union[Country, str]] = None) -> SearchPeople:
        """ Searches TMDb for people.

            Parameters:
                query (str): Query to search for.
                include_adult (Optional[bool]): Choose whether to include adult (pornography) content in the results.
                region (Optional[Union[Country, str]]): Specify a ISO 3166-1 code or :class:`tmdbapis.objs.simple.Country` Object to filter release dates. Must be uppercase.

            Returns:
                :class:`~tmdbapis.objs.pagination.SearchPeople`

            Raises:
                :class:`~tmdbapis.exceptions.NotFound`: When no results are found for the search.
        """
        return SearchPeople(self, requests.utils.quote(query), include_adult=include_adult,
                            region=util.validate_country(region, self._iso_3166_1))

    def tv_search(self, query: str, include_adult: Optional[bool] = None,
                  first_air_date_year: Optional[int] = None) -> SearchTVShows:
        """ Searches TMDb for tv shows.

            Parameters:
                query (str): Query to search for.
                include_adult (Optional[bool]): Choose whether to include adult (pornography) content in the results.
                first_air_date_year (Optional[int]): Specify a first air date year for the search.

            Returns:
                :class:`~tmdbapis.objs.pagination.SearchTVShows`

            Raises:
                :class:`~tmdbapis.exceptions.NotFound`: When no results are found for the search.
        """
        return SearchTVShows(self, requests.utils.quote(query), include_adult=include_adult,
                             first_air_date_year=first_air_date_year)

    def tv_show(self, tv_id: int, load: bool = True) -> TVShow:
        """ Gets the :class:`~tmdbapis.objs.reload.TVShow` for the given id.

            Parameters:
                tv_id (int): TV ID of the show you want.
                load (bool): Load the data on creation.

            Returns:
                :class:`~tmdbapis.objs.reload.TVShow`

            Raises:
                :class:`~tmdbapis.exceptions.NotFound`: When no keyword is found for the given id.
        """
        return TVShow(self, {"id": tv_id}, load=load)

    def latest_tv(self) -> TVShow:
        """ Gets the latest :class:`~tmdbapis.objs.reload.TVShow` added on TMDb.

            Returns:
                :class:`~tmdbapis.objs.reload.TVShow`
        """
        return TVShow(self, self._api.tv_get_latest(language=self.language))

    def tv_airing_today(self) -> TVShowsAiringToday:
        """ Paginated Object of TV Shows Airing Today.

            Returns:
                :class:`~tmdbapis.objs.reload.TVShowsAiringToday`
        """
        return TVShowsAiringToday(self)

    def tv_on_the_air(self) -> TVShowsOnTheAir:
        """ Paginated Object of TV Shows On the Air.

            Returns:
                :class:`~tmdbapis.objs.reload.TVShowsOnTheAir`
        """
        return TVShowsOnTheAir(self)

    def popular_tv(self) -> PopularTVShows:
        """ Paginated Object of Popular TV Shows.

            Returns:
                :class:`~tmdbapis.objs.pagination.PopularTVShows`
        """
        return PopularTVShows(self)

    def top_rated_tv(self) -> TopRatedTVShows:
        """ Paginated Object of Top Rated TV Shows On.

            Returns:
                :class:`~tmdbapis.objs.reload.TVShowsOnTheAir`
        """
        return TopRatedTVShows(self)

    def tv_season(self, tv_id: int, season_number: int, load: bool = True) -> Season:
        """ Gets the :class:`~tmdbapis.objs.reload.Movie` for the given id.

            Parameters:
                tv_id (int): TV ID of the show the contains the season you want.
                season_number (int): Season number to grab.
                load (bool): Load the data on creation.

            Returns:
                :class:`~tmdbapis.objs.reload.Season`

            Raises:
                :class:`~tmdbapis.exceptions.NotFound`: When no season is found for the given id.
        """
        return Season(self, {"season_number": season_number}, tv_id, load=load)

    def tv_episode(self, tv_id: int, season_number: int, episode_number: int, load: bool = True) -> Episode:
        """ Gets the :class:`~tmdbapis.objs.reload.Episode` for the given id.

            Parameters:
                tv_id (int): TV ID of the show the contains the season you want.
                season_number (int): Season number to grab.
                episode_number (int): Episode number to grab.
                load (bool): Load the data on creation.

            Returns:
                :class:`~tmdbapis.objs.reload.Episode`

            Raises:
                :class:`~tmdbapis.exceptions.NotFound`: When no keyword is found for the given id.
        """
        return Episode(self, {"season_number": season_number, "episode_number": episode_number}, tv_id, load=load)

    def episode_group(self, episode_group_id: str, load: bool = True) -> EpisodeGroup:
        """ Gets the :class:`~tmdbapis.objs.reload.EpisodeGroup` for the given id.

            Parameters:
                episode_group_id (str): Episode Group ID that you want.
                load (bool): Load the data on creation.

            Returns:
                :class:`~tmdbapis.objs.reload.EpisodeGroup`

            Raises:
                :class:`~tmdbapis.exceptions.NotFound`: When no keyword is found for the given id.
        """
        return EpisodeGroup(self, {"id": episode_group_id}, load=load)

    def provider_regions(self, reload: bool = False) -> List[Country]:
        """ Gets a List of :class:`~tmdbapis.objs.simple.Country`.

            Parameters:
                reload (bool): Reload the cached data.

            Returns:
                :class:`~tmdbapis.objs.reload.List[Country]`
        """
        if reload or self._provider_regions is None:
            self._provider_regions = [
                Country(self, c) for c in
                self._api.watch_providers_get_available_regions(self.language)
            ]
        return self._provider_regions

    def movie_providers(self, watch_region: Optional[Union[Country, str]] = None, reload: bool = False) -> List[WatchProvider]:
        """ Gets a List of :class:`~tmdbapis.objs.simple.WatchProvider` for movies.

            Parameters:
                watch_region (Optional[Union[Country, str]]): Specify a ISO 3166-1 code or :class:`tmdbapis.objs.simple.Country` Object to filter release dates. Must be uppercase.
                reload (bool): Reload the cached data.

            Returns:
                :class:`~tmdbapis.objs.reload.List[WatchProvider]`
        """
        if reload or self._movie_providers is None:
            self._movie_providers = [
                WatchProvider(self, w) for w in
                self._api.watch_providers_get_movie_providers(self.language, watch_region=watch_region)["results"]
            ]
        return self._movie_providers

    def tv_providers(self, watch_region: Optional[Union[Country, str]] = None, reload: bool = False) -> List[WatchProvider]:
        """ Gets a List of :class:`~tmdbapis.objs.simple.WatchProvider` for shows.

            Parameters:
                watch_region (Optional[Union[Country, str]]): Specify a ISO 3166-1 code or :class:`tmdbapis.objs.simple.Country` Object to filter release dates. Must be uppercase.
                reload (bool): Reload the cached data.

            Returns:
                :class:`~tmdbapis.objs.reload.List[Country]`
        """
        if reload or self._tv_providers is None:
            self._tv_providers = [
                WatchProvider(self, w) for w in
                self._api.watch_providers_get_tv_providers(self.language, watch_region=watch_region)["results"]
            ]
        return self._tv_providers
