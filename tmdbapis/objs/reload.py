from abc import abstractmethod
from typing import Optional

from tmdbapis.objs.base import TMDbObj
from tmdbapis.objs.mixin import Favorite, Rate, Watchlist


class TMDbReload(TMDbObj):
    """ Base object for objects that Reload. """
    def __init__(self, tmdb, data, load=False):
        super().__init__(tmdb, data)
        if load:
            self._load(None)

    @abstractmethod
    def _load(self, data):
        self._partial = data is not None
        super()._load(self._full_load() if data is None else data)

    @abstractmethod
    def _full_load(self):
        pass

    def reload(self):
        """ Reloads the full object. """
        self._load(None)


class Account(TMDbReload):
    """ Represents a single User Account.

        Attributes:
            avatar_hash (str): Avatar Hash Value.
            avatar_path (str): Avatar Path.
            avatar_url (str): Avatar Full URL.
            country (:class:`~tmdbapis.objs.simple.Country`): Country object for the ISO 3166-1 Country Code.
            id (str): v3 User Account ID.
            include_adult (bool): Default include adult items in search results
            iso_3166_1 (str): Default ISO 3166-1 Alpha-2 Country Code of the User Account.
            iso_639_1 (str): Default ISO 639-1 Language Code of the User Account.
            language (:class:`~tmdbapis.objs.simple.Language`): Language object for the ISO 639-1 Language Code.
            name (str): User Account Name.
            username (str): User Account Username.
    """

    def __init__(self, tmdb):
        super().__init__(tmdb, None)

    def _load(self, data):
        super()._load(None)
        self.avatar_hash = self._parse(attrs=["avatar", "gravatar", "hash"])
        self.avatar_path = self._parse(attrs=["avatar", "tmdb", "avatar_path"])
        self.avatar_url = self._image_url(self.avatar_path)
        self.country = self._tmdb._get_object(self._data, "country")
        self.id = self._parse(attrs="id", value_type="int")
        self.include_adult = self._parse(attrs="include_adult")
        self.iso_3166_1 = self._parse(attrs="iso_3166_1")
        self.iso_639_1 = self._parse(attrs="iso_639_1")
        self.language = self._tmdb._get_object(self._data, "language")
        self.name = self._parse(attrs="name")
        self.username = self._parse(attrs="username")
        self._finish(self.name)

    def _full_load(self):
        return self._api.account_get_details()

    def created_lists(self, v3: bool = False):
        """ Alias for :meth:`~.tmdb.TMDbAPIs.created_lists` """
        return self._tmdb.created_lists(v3=v3)

    def favorite_movies(self, sort_by: str = None, v3: bool = False):
        """ Alias for :meth:`~.tmdb.TMDbAPIs.favorite_movies` """
        return self._tmdb.favorite_movies(sort_by=sort_by, v3=v3)

    def favorite_tv_shows(self, sort_by: Optional[str] = None, v3: bool = False):
        """ Alias for :meth:`~.tmdb.TMDbAPIs.favorite_tv_shows` """
        return self._tmdb.favorite_tv_shows(sort_by=sort_by, v3=v3)

    def movie_recommendations(self, sort_by: Optional[str] = None):
        """ Alias for :meth:`~.tmdb.TMDbAPIs.movie_recommendations` """
        return self._tmdb.movie_recommendations(sort_by=sort_by)

    def movie_watchlist(self, sort_by: Optional[str] = None, v3: bool = False):
        """ Alias for :meth:`~.tmdb.TMDbAPIs.movie_watchlist` """
        return self._tmdb.movie_watchlist(sort_by=sort_by, v3=v3)

    def rated_episodes(self, sort_by: Optional[str] = None):
        """ Alias for :meth:`~.tmdb.TMDbAPIs.rated_episodes` """
        return self._tmdb.rated_episodes(sort_by=sort_by)

    def rated_movies(self, sort_by: Optional[str] = None, v3: bool = False):
        """ Alias for :meth:`~.tmdb.TMDbAPIs.rated_movies` """
        return self._tmdb.rated_movies(sort_by=sort_by, v3=v3)

    def rated_tv_shows(self, sort_by: Optional[str] = None, v3: bool = False):
        """ Alias for :meth:`~.tmdb.TMDbAPIs.rated_tv_shows` """
        return self._tmdb.rated_tv_shows(sort_by=sort_by, v3=v3)

    def tv_show_recommendations(self, sort_by: Optional[str] = None):
        """ Alias for :meth:`~.tmdb.TMDbAPIs.tv_show_recommendations` """
        return self._tmdb.tv_show_recommendations(sort_by=sort_by)

    def tv_show_watchlist(self, sort_by: Optional[str] = None, v3: bool = False):
        """ Alias for :meth:`~.tmdb.TMDbAPIs.tv_show_watchlist` """
        return self._tmdb.tv_show_watchlist(sort_by=sort_by, v3=v3)


class Collection(TMDbReload):
    """ Represents a single Collection.

        Attributes:
            backdrop_path (str): Backdrop Path.
            backdrop_url (str): Backdrop Full URL.
            backdrops (List[:class:`~tmdbapis.objs.image.Backdrop`]): List of other Backdrops for the Collection.
            id (int): Collection ID.
            movies (List[:class:`~tmdbapis.objs.reload.Movie`]): Movies within the Collection.
            name (str): Collection Name.
            overview (str): Collection Overview.
            poster_path (str): Poster Path.
            poster_url (str): Poster Full URL.
            posters (List[:class:`~tmdbapis.objs.image.Poster`]): List of other Posters for the Collection.
            translations (List[:class:`~tmdbapis.objs.simple.Translation`]): List of Translations for the Collection.
    """

    def _load(self, data):
        super()._load(data)
        self.backdrop_path = self._parse(attrs="backdrop_path")
        self.backdrop_url = self._image_url(self.backdrop_path)
        self.backdrops = self._parse(attrs=["images", "backdrops"], value_type="backdrop", is_list=True)
        self.id = self._parse(attrs="id", value_type="int")
        self.movies = self._parse(attrs="parts", value_type="movie", is_list=True)
        self.name = self._parse(attrs="name")
        self.overview = self._parse(attrs="overview")
        self.poster_path = self._parse(attrs="poster_path")
        self.poster_url = self._image_url(self.poster_path)
        self.posters = self._parse(attrs=["images", "posters"], value_type="poster", is_list=True)
        self.translations = self._parse(attrs=["translations", "translations"], value_type="translation", is_list=True)
        self._finish(self.name)

    def _full_load(self):
        return self._api.collections_get_details(
            self.id,
            language=self._tmdb.language,
            append_to_response="images,translations",
            include_image_language=self._tmdb._include_language
        )


class Company(TMDbReload):
    """ Represents a single Company.

        Attributes:
            alternative_names (List[:class:`~tmdbapis.objs.simple.AlternativeName`]): Company Alternative Names.
            description (str): Company Description.
            headquarters (str): Company Headquarters.
            homepage (str): Company Homepage.
            id (int): Company ID.
            logo_path (str): Logo Path.
            logo_url (str): Logo Full URL.
            logos (List[:class:`~tmdbapis.objs.image.Logo`]): List of other Logos for the Company.
            name (str): Company Name.
            movies (:class:`~tmdbapis.objs.pagination.DiscoverMovies`): Pagination Object of Company Movies.
            origin_country (str): Company Origin Country.
            parent_company (:class:`~tmdbapis.objs.reload.Company`): Parent Company.
            tv_shows (:class:`~tmdbapis.objs.pagination.DiscoverTVShows`): Pagination Object of Company TV Shows.
    """

    def _load(self, data):
        super()._load(data)
        self._movies = None
        self._tv_shows = None
        self.alternative_names = self._parse(attrs=["alternative_names", "results"],
                                             value_type="alternative_name", is_list=True)
        self.description = self._parse(attrs="description")
        self.headquarters = self._parse(attrs="headquarters")
        self.homepage = self._parse(attrs="homepage")
        self.id = self._parse(attrs="id", value_type="int")
        self.logo_path = self._parse(attrs="logo_path")
        self.logo_url = self._image_url(self.logo_path)
        self.logos = self._parse(attrs=["images", "logos"], value_type="logo", is_list=True)
        self.name = self._parse(attrs="name")
        self.origin_country = self._parse(attrs="origin_country")
        self.parent_company = self._parse(attrs="parent_company", value_type="company")
        self._finish(self.name)

    def _full_load(self):
        return self._api.companies_get_details(
            self.id,
            language=self._tmdb.language,
            append_to_response="alternative_names,images"
        )

    @property
    def movies(self):
        if not self._movies:
            self._movies = self._tmdb.discover_movies(with_companies=self.id)
        return self._movies

    @property
    def tv_shows(self):
        if not self._tv_shows:
            self._tv_shows = self._tmdb.discover_tv_shows(with_companies=self.id)
        return self._tv_shows


class Configuration(TMDbReload):
    """ Represents TMDb's Configuration.

        Attributes:
            backdrop_sizes (List[str]): Backdrop sizes.
            base_image_url (str): Base Image URL.
            change_keys (List[str]): Change Keys.
            countries (List[:class:`~tmdbapis.objs.simple.Country`]): Countries in TMDb.
            departments (List[:class:`~tmdbapis.objs.simple.Department`]): Departments in TMDb.
            languages (List[:class:`~tmdbapis.objs.simple.Language`]): Languages in TMDb.
            logo_sizes (List[str]): Logo Sizes.
            poster_sizes (List[str]): Poster Sizes.
            primary_translations (List[str]): Primary Translations in TMDb.
            profile_sizes (List[str]): Profile Sizes.
            secure_base_image_url (str): Secure Base Image URL.
            still_sizes (List[str]): Still Sizes
            timezones (List[str]): Timezones in TMDb.
    """

    def __init__(self, tmdb):
        super().__init__(tmdb, None)

    def _load(self, data):
        super()._load(data)
        self.backdrop_sizes = self._parse(attrs=["images", "backdrop_sizes"], is_list=True)
        self.base_image_url = self._parse(attrs=["images", "base_url"])
        self.change_keys = self._parse(attrs="change_keys", is_list=True)
        self.countries = self._parse(attrs="countries", value_type="load_country", is_list=True)
        self.departments = self._parse(attrs="jobs", value_type="load_department", is_list=True)
        self.languages = self._parse(attrs="languages", value_type="load_language", is_list=True)
        self.logo_sizes = self._parse(attrs=["images", "logo_sizes"], is_list=True)
        self.poster_sizes = self._parse(attrs=["images", "poster_sizes"], is_list=True)
        self.primary_translations = self._parse(attrs="primary_translations", is_list=True)
        self.profile_sizes = self._parse(attrs=["images", "profile_sizes"], is_list=True)
        self.secure_base_image_url = self._parse(attrs=["images", "secure_base_url"])
        self.still_sizes = self._parse(attrs=["images", "still_sizes"], is_list=True)
        self.timezones = self._parse(attrs="timezones", value_type="load_timezone", is_list=True)
        self._finish("API3 Configuration")

    def _full_load(self):
        return self._api.configuration_get_api_configuration(
            append_to_response="countries,jobs,languages,primary_translations,timezones"
        )


class Credit(TMDbReload):
    """ Represents a single Credit.

        Attributes:
            adult (bool): Is the Actor an adult actor.
            character (str): Character Name.
            credit_type (str): Credit Type.
            department (str): Credit Department
            episode_count (int): Number of Episodes the Actor appeared in.
            episodes (List[:class:`~tmdbapis.objs.reload.Episode`]): Episodes of credit. Only exists when media_type == "tv".
            gender (int): Actor's Gender. (1: Women, 2: Men)
            id (str): The Credit ID.
            job (str): Job in Department.
            known_for (List[Union[:class:`~tmdbapis.objs.reload.Movie`, :class:`~tmdbapis.objs.reload.TVShow`]]):
            known_for_department (str): Department Actor is known for.
            media_type (str): Media Type of the Credit.
            movie (:class:`~tmdbapis.objs.reload.Movie`): Movie of credit. Only exists when media_type == "movie" .
            name (str): Actor Name.
            order (int): Order of the Credits.
            original_name (str): Actor Original Name.
            person_id (int): Person ID of the Actor.
            popularity (float): Popularity of the Credit.
            profile_path (str): Profile Path.
            profile_url (str): Profile Full URL.
            seasons (List[:class:`~tmdbapis.objs.reload.Season`]): Season of credit. Only exists when media_type == "tv".
            tv_show (:class:`~tmdbapis.objs.reload.TVShow`): TV Show of credit. Only exists when media_type == "tv".
    """

    def __init__(self, tmdb, data, credit_type=None, media_type=None, load=False):
        self._credit_type = credit_type
        self._media_type = media_type
        super().__init__(tmdb, data=data, load=load)

    def _load(self, data):
        super()._load(data)

        def dict_check(dict_attr, attr):
            return [dict_attr, attr] if dict_attr in self._data else attr

        self.adult = self._parse(attrs=dict_check("person", "adult"), value_type="bool")
        self.character = self._parse(attrs=dict_check("media", "character"))
        self.credit_type = self._parse(attrs="credit_type")
        if not self.credit_type:
            self.credit_type = self._credit_type
        self.department = self._parse(attrs="department")
        if "episode_count" in self._data:
            self.episode_count = self._parse(attrs="episode_count", value_type="int")
        self.gender = self._parse(attrs=dict_check("person", "gender"), value_type="int")
        self.id = self._parse(attrs="credit_id" if "credit_id" in self._data else "id")
        self.job = self._parse(attrs="job")
        self.known_for = self._parse(attrs=["person", "known_for"], value_type="media_type", is_list=True)
        self.known_for_department = self._parse(attrs=dict_check("person", "known_for_department"))
        self.media_type = self._parse(attrs="media_type")
        if not self.media_type:
            self.media_type = self._media_type
        self.name = self._parse(attrs=dict_check("person", "name"))
        self.order = self._parse(attrs="order", value_type="int")
        self.original_name = self._parse(attrs="original_name")
        self.person_id = self._parse(attrs=dict_check("person", "id"), value_type="int")
        self.popularity = self._parse(attrs=dict_check("person", "popularity"), value_type="int")
        self.profile_path = self._parse(attrs=dict_check("person", "profile_path"))
        self.profile_url = self._image_url(self.profile_path)
        if "media" in self._data:
            if self.media_type == "movie":
                self.movie = self._parse(attrs="media", value_type="movie")
            elif self.media_type == "tv":
                self.tv_show = self._parse(attrs="media", value_type="tv")
                self.seasons = self._parse(attrs=["media", "seasons"], value_type="season", is_list=True)
                self.episodes = self._parse(attrs=["media", "episodes"], value_type="episode", is_list=True)
        elif "credit_id" in self._data:
            if self.media_type == "movie":
                self.movie = self._tmdb.movie(self._parse(attrs="id", value_type="int"), load=False)
            elif self.media_type == "tv":
                self.tv_show = self._tmdb.tv_show(self._parse(attrs="id", value_type="int"), load=False)

    def _full_load(self):
        return self._api.credits_get_details(self.id)


class Episode(TMDbReload, Rate):
    """ Represents a single Episode.

        Attributes:
            air_date (datetime): Episode Air Date.
            cast (List[:class:`~tmdbapis.objs.reload.Credit`]): List of Episode Cast Credits.
            crew (List[:class:`~tmdbapis.objs.reload.Credit`]): List of Episode Crew Credits.
            episode_number (int): Episode in Season Number.
            freebase_id (str): Freebase ID for the Episode.
            freebase_mid (str): Freebase MID for the Episode.
            guest_stars (List[:class:`~tmdbapis.objs.reload.Credit`]): List of Episode Guest Stars Credits.
            id (int): Episode ID.
            imdb_id (str): Episode IMDb ID.
            name (str): Episode Name.
            order (int): Episode Order in Group.
            overview (str): Episode Overview.
            production_code (str): Episode Production Code.
            rated (Union[float, bool]): Either your TMDb Rating for the Episode or False if there is no rating.
            season_number (int): Season the Episode is in.
            still_path (str): Still Path.
            still_url (str): Still Full URL.
            stills (List[:class:`~tmdbapis.objs.image.Still`]): List of other Stills for the Episode.
            title (str): alias of name.
            translations (List[:class:`~tmdbapis.objs.simple.Translation`]): List of Translations for the Episode.
            tv_id (int): TMDb TV Show ID the contains the Episode.
            tvdb_id (int): TVDB ID of the Episode.
            tvrage_id (int): TVRage ID of the Episode.
            videos (List[:class:`~tmdbapis.objs.simple.Video`]): List of Videos associated with the Episode.
            vote_average (float): Vote Average for the Episode.
            vote_count (int): Number of Votes for the Episode.
    """

    def __init__(self, tmdb, data, tv_id=None, load=False):
        self._tv_id = tv_id
        super().__init__(tmdb, data=data, load=load)

    def _load(self, data):
        super()._load(data)
        self.air_date = self._parse(attrs="air_date", value_type="date")
        self.cast = self._parse(attrs=["credits", "cast"], value_type="tv_cast", is_list=True)
        self.crew = self._parse(attrs="crew", value_type="tv_crew", is_list=True)
        self.episode_number = self._parse(attrs="episode_number", value_type="int")
        self.freebase_id = self._parse(attrs=["external_ids", "freebase_id"])
        self.freebase_mid = self._parse(attrs=["external_ids", "freebase_mid"])
        self.guest_stars = self._parse(attrs="guest_stars", value_type="tv_cast", is_list=True)
        self.id = self._parse(attrs="id", value_type="int")
        self.imdb_id = self._parse(attrs=["external_ids", "imdb_id"])
        self.name = self._parse(attrs="name")
        self.order = self._parse(attrs="order", value_type="int") if "order" in self._data else None
        self.overview = self._parse(attrs="overview")
        self.production_code = self._parse(attrs="production_code")
        try:
            self.rated = self._parse(attrs=["account_states", "rated"], value_type="float")
        except ValueError:
            self.rated = self._parse(attrs=["account_states", "rated"], value_type="bool")
        self.season_number = self._parse(attrs="season_number", value_type="int")
        self.still_path = self._parse(attrs="still_path")
        self.still_url = self._image_url(self.still_path)
        self.stills = self._parse(attrs=["images", "stills"], value_type="still", is_list=True)
        self.title = self.name
        self.translations = self._parse(attrs=["translations", "translations"], value_type="translation", is_list=True)
        self.tv_id = self._parse(attrs="show_id", value_type="int") if self._tv_id is None else self._tv_id
        self.tvdb_id = self._parse(attrs=["external_ids", "tvdb_id"], value_type="int")
        self.tvrage_id = self._parse(attrs=["external_ids", "tvrage_id"], value_type="int")
        self.videos = self._parse(attrs=["videos", "results"], value_type="video", is_list=True)
        self.vote_average = self._parse(attrs="vote_average", value_type="float")
        self.vote_count = self._parse(attrs="vote_count", value_type="int")
        self._finish(self.name)

    def _full_load(self):
        return self._api.tv_episodes_get_details(
            self.tv_id, self.season_number, self.episode_number,
            language=self._tmdb.language,
            include_image_language=self._tmdb._include_language,
            include_video_language=self._tmdb._include_language,
            append_to_response="account_states,credits,external_ids,images,translations,videos"
        )

    def _rate(self, rating):
        self._api.tv_episodes_rate_tv_episode(self.tv_id, self.season_number, self.episode_number, rating)

    def _delete_rate(self):
        self._api.tv_episodes_delete_rating(self.tv_id, self.season_number, self.episode_number)


class EpisodeGroup(TMDbReload):
    """ Represents a single Episode Group.

        Attributes:
            description (str): Episode Group Description.
            episode_count (int): Episode Group Episode Count.
            group_count (int): Number of Groups in the Episode Group.
            groups (List[:class:`~tmdbapis.objs.simple.Group`]): Groups in the Episode Group.
            id (str): Episode Group ID.
            name (str): Episode Group Name.
            network (:class:`~tmdbapis.objs.reload.Network`): Episode Group Network.
            type (int): Episode Group Type.
    """

    def _load(self, data):
        super()._load(data)
        self.description = self._parse(attrs="description")
        self.episode_count = self._parse(attrs="episode_count", value_type="int")
        self.group_count = self._parse(attrs="group_count", value_type="int")
        self.groups = self._parse(attrs="groups", value_type="group", is_list=True)
        self.id = self._parse(attrs="id")
        self.name = self._parse(attrs="name")
        self.network = self._parse(attrs="network", value_type="network")
        self.type = self._parse(attrs="type", value_type="int")
        self._finish(self.name)

    def _full_load(self):
        return self._api.tv_episode_groups_get_details(self.id, language=self._tmdb.language)


class Keyword(TMDbReload):
    """ Represents a single Keyword.

        Attributes:
            id (int): Keyword ID.
            name (str): Keyword Name.
            movies (:class:`~tmdbapis.objs.pagination.DiscoverMovies`): Keyword Movies.
            tv_shows (:class:`~tmdbapis.objs.pagination.DiscoverTVShows`): Keyword TV Shows.
    """

    def _load(self, data):
        super()._load(data)
        self._movies = None
        self._tv_shows = None
        self.id = self._parse(attrs="id", value_type="int")
        self.name = self._parse(attrs="name")
        self._finish(self.name)

    def _full_load(self):
        return self._api.keywords_get_details(self.id, language=self._tmdb.language)

    @property
    def movies(self):
        if not self._movies:
            self._movies = self._tmdb.discover_movies(with_keywords=self.id)
        return self._movies

    @property
    def tv_shows(self):
        if not self._tv_shows:
            self._tv_shows = self._tmdb.discover_tv_shows(with_keywords=self.id)
        return self._tv_shows


class Movie(TMDbReload, Favorite, Rate, Watchlist):
    """ Represents a single Episode.

        Attributes:
            adult (bool): Is the Movie an adult movie.
            alternative_titles (List[:class:`~tmdbapis.objs.simple.AlternativeTitle`]): Movie Alternative Titles.
            backdrop_path (str): Backdrop Path.
            backdrop_url (str): Backdrop Full URL.
            backdrops (List[:class:`~tmdbapis.objs.image.Still`]): List of other Backdrops for the Movie.
            budget (int): Movie Budget.
            cast (List[:class:`~tmdbapis.objs.reload.Credit`]): List of Movie Cast Credits.
            collection (:class:`~tmdbapis.objs.reload.Collection`): Movie's Collection.
            companies (List[:class:`~tmdbapis.objs.reload.Company`]): List of Production Companies for the Movie.
            countries (List[:class:`~tmdbapis.objs.simple.Country`]): List of Production Countries for the Movie.
            crew (List[:class:`~tmdbapis.objs.reload.Credit`]): List of Movie Crew Credits.
            facebook_id (str): Facebook ID for the Movie.
            favorite (bool): If this Movie has been marked as a favorite. (Authentication Required)
            genres (List[:class:`~tmdbapis.objs.simple.Genre`]): List of Genres for the Movie.
            homepage (str): Homepage for the Movie.
            id (str): Movie ID.
            imdb_id (str): IMDb ID for the Movie.
            instagram_id (str): Instagram ID for the Movie.
            keywords (List[:class:`~tmdbapis.objs.reload.Keyword`]): List of Keywords for the Movie.
            spoken_languages (List[:class:`~tmdbapis.objs.simple.Language`]): List of Spoken Languages for the Movie.
            lists (:class:`~tmdbapis.objs.pagination.MovieLists`): Pagination Object of Lists containing the Movie.
            logos (List[:class:`~tmdbapis.objs.image.Logo`]): List of other Logos for the Movie.
            name (str): alias of title.
            original_language (:class:`~tmdbapis.objs.simple.Language`): Original Language of the Movie.
            original_title (str): Movie's Original Title.
            overview (str): Movie Overview.
            popularity (float): Movie's Popularity.
            poster_path (str): Poster Path.
            poster_url (str): Poster Full URL.
            posters (List[:class:`~tmdbapis.objs.image.Poster`]): List of other Posters for the Movie.
            rated (Union[float, bool]): Your rating for this Movie or false if you have not rated it. (Authentication Required)
            recommendations (:class:`~tmdbapis.objs.pagination.RecommendedMovies`): Pagination Object of Recommended Movies based on this Movie.
            release_date (datetime): Movie's Primary Release Date.
            release_dates (Dict[str, :class:`~tmdbapis.objs.simple.ReleaseDate`]): Dictionary of Release Dates where the keys are the ISO 3166-1 Alpha-2 Country Codes.
            revenue (int): Movie's Revenue.
            reviews (class:`~tmdbapis.objs.pagination.MovieReviews`): Pagination Object of Movie Reviews for this Movie.
            runtime (int) Movie's Runtime.
            similar (class:`~tmdbapis.objs.pagination.SimilarMovies`): Pagination Object of Similar Movie to this Movie.
            status (str): Movie's Status.
            tagline (str): Movie's Tagline.
            title (str): Movie's Title.
            trailers (List[:class:`~tmdbapis.objs.simple.Trailer`]): List of Trailers for the Movie.
            translations (List[:class:`~tmdbapis.objs.simple.Translation`]): List of Translations for the Movie.
            twitter_id (str): Twitter ID for the Movie.
            video (bool): Unsure when this is true.
            videos (List[:class:`~tmdbapis.objs.simple.Video`]): List of Videos associated with the Movie.
            vote_average (float): Vote Average for the Movie.
            vote_count (int): Number of Votes for the Movie.
            watch_providers (Dict[str, :class:`~tmdbapis.objs.simple.CountryWatchProviders`]): Dictionary of Watch Providers where the keys are the ISO 3166-1 Alpha-2 Country Codes.
            watchlist (bool): If this Movie has been added to your watchlist. (Authentication Required)
    """

    def _load(self, data):
        super()._load(data)
        self.adult = self._parse(attrs="adult", value_type="bool")
        self.alternative_titles = self._parse(attrs=["alternative_titles", "titles"], value_type="alternative_title",
                                              is_list=True)
        self.backdrop_path = self._parse(attrs="backdrop_path")
        self.backdrop_url = self._image_url(self.backdrop_path)
        self.backdrops = self._parse(attrs=["images", "backdrops"], value_type="backdrop", is_list=True)
        self.budget = self._parse(attrs="budget", value_type="int")
        self.cast = self._parse(attrs=["credits", "cast"], value_type="movie_cast", is_list=True)
        self.collection = self._parse(attrs="belongs_to_collection", value_type="collection")
        self.companies = self._parse(attrs="production_companies", value_type="company", is_list=True)
        self.countries = self._parse(attrs="production_countries", value_type="country", is_list=True)
        self.crew = self._parse(attrs=["credits", "crew"], value_type="movie_crew", is_list=True)
        self.facebook_id = self._parse(attrs=["external_ids", "facebook_id"])
        self.favorite = self._parse(attrs=["account_states", "favorite"], value_type="bool")
        self.genres = self._parse(attrs="genres" if "genres" in self._data else "genre_ids", value_type="movie_genre",
                                  is_list=True)
        self.homepage = self._parse(attrs="homepage")
        self.id = self._parse(attrs="id", value_type="int")
        self.imdb_id = self._parse(attrs="imdb_id")
        self.instagram_id = self._parse(attrs=["external_ids", "instagram_id"])
        self.keywords = self._parse(attrs=["keywords", "keywords"], value_type="keyword", is_list=True)
        self.spoken_languages = self._parse(attrs="spoken_languages", value_type="language", is_list=True)
        self.lists = self._parse(attrs="lists", value_type="lists", key=self.id)
        self.logos = self._parse(attrs=["images", "logos"], value_type="logo", is_list=True)
        self.original_language = self._parse(attrs="original_language", value_type="language")
        self.original_title = self._parse(attrs="original_title")
        self.overview = self._parse(attrs="overview")
        self.popularity = self._parse(attrs="popularity", value_type="float")
        self.poster_path = self._parse(attrs="poster_path")
        self.poster_url = self._image_url(self.poster_path)
        self.posters = self._parse(attrs=["images", "posters"], value_type="poster", is_list=True)
        try:
            self.rated = self._parse(attrs=["account_states", "rated"], value_type="float")
        except ValueError:
            self.rated = self._parse(attrs=["account_states", "rated"], value_type="bool")
        self.recommendations = self._parse(attrs="recommendations", value_type="recommended_movies", key=self.id)
        self.release_date = self._parse(attrs="release_date", value_type="date")
        self.release_dates = {}
        if "release_dates" in self._data and "results" in self._data["release_dates"]:
            for iso in self._data["release_dates"]["results"]:
                self.release_dates[iso["iso_3166_1"]] = self._parse(data=iso, attrs="release_dates",
                                                                    value_type="release_date", is_list=True)
        self.revenue = self._parse(attrs="revenue", value_type="int")
        self.reviews = self._parse(attrs="reviews", value_type="movie_reviews", key=self.id)
        self.runtime = self._parse(attrs="runtime", value_type="int")
        self.similar = self._parse(attrs="similar", value_type="similar_movies", key=self.id)
        self.status = self._parse(attrs="status")
        self.tagline = self._parse(attrs="tagline")
        self.title = self._parse(attrs="title")
        self.name = self.title
        self.trailers = self._parse(attrs=["trailers", "youtube"], value_type="trailer", is_list=True)
        self.translations = self._parse(attrs=["translations", "translations"], value_type="translation", is_list=True)
        self.twitter_id = self._parse(attrs=["external_ids", "twitter_id"])
        self.video = self._parse(attrs="video", value_type="bool")
        self.videos = self._parse(attrs=["videos", "results"], value_type="video", is_list=True)
        self.vote_average = self._parse(attrs="vote_average", value_type="float")
        self.vote_count = self._parse(attrs="vote_count", value_type="int")
        self.watch_providers = self._parse(attrs=["watch/providers", "results"], value_type="country_watch_provider",
                                           is_dict=True)
        self.watchlist = self._parse(attrs=["account_states", "watchlist"], value_type="bool")
        self._finish(self.title)

    def _full_load(self):
        return self._api.movies_get_details(
            self.id,
            language=self._tmdb.language,
            include_image_language=self._tmdb._include_language,
            include_video_language=self._tmdb._include_language,
            append_to_response="account_states,alternative_titles,credits,external_ids,images,"
                               "keywords,lists,recommendations,release_dates,reviews,similar,"
                               "trailers,translations,videos,watch/providers"
        )

    def _rate(self, rating):
        self._api.movies_rate_movie(self.id, rating)

    def _delete_rate(self):
        self._api.movies_delete_rating(self.id)

    def _media_type(self):
        return "movie"


class Network(TMDbReload):
    """ Represents a single Network.

        Attributes:
            alternative_names (List[:class:`~tmdbapis.objs.simple.AlternativeName`]): Network Alternative Names.
            country (:class:`~tmdbapis.objs.simple.Country`): Network Country.
            headquarters (str): Network Headquarters.
            homepage (str): Network Homepage.
            id (int): Network ID.
            logo_path (str): Logo Path.
            logo_url (str): Logo Full URL.
            logos (List[:class:`~tmdbapis.objs.image.Logo`]): List of other Logos for the Network.
            name (str): Network Name.
            tv_shows (:class:`~tmdbapis.objs.pagination.DiscoverTVShows`): Network TV Shows.
    """

    def _load(self, data):
        super()._load(data)
        self._tv_shows = None
        self.alternative_names = self._parse(attrs=["alternative_names", "results"],
                                             value_type="alternative_name", is_list=True)
        self.country = self._parse(attrs="origin_country", value_type="country")
        self.headquarters = self._parse(attrs="headquarters")
        self.homepage = self._parse(attrs="homepage")
        self.id = self._parse(attrs="id", value_type="int")
        self.logo_path = self._parse(attrs="logo_path")
        self.logo_url = self._image_url(self.logo_path)
        self.logos = self._parse(attrs=["images", "logos"], value_type="logo", is_list=True)
        self.name = self._parse(attrs="name")
        self._finish(self.name)

    def _full_load(self):
        return self._api.networks_get_details(self.id, append_to_response="alternative_names,images")

    @property
    def tv_shows(self):
        if not self._tv_shows:
            self._tv_shows = self._tmdb.discover_tv_shows(with_networks=self.id)
        return self._tv_shows


class Person(TMDbReload):
    """ Represents a single Person.

        Attributes:
            adult (bool): Is the Person an adult actor.
            also_known_as (List[str]): Name's this Person is also known as.
            biography (str): Person's Biography.
            birthday (datetime): Person's Birthday.
            deathday (datetime): Person's Deathday.
            facebook_id (str): Facebook ID for the Person.
            freebase_id (str): Freebase ID for the Person.
            freebase_mid (str): Freebase MID for the Person.
            gender (int): Person's Gender. (1: Women, 2: Men)
            homepage (str): Homepage for the Person.
            id (str): Person ID.
            imdb_id (str): IMDb ID for the Person.
            instagram_id (str): Instagram ID for the Person.
            known_for_department (str): Department the Person is best known for.
            name (str): Person's Name.
            place_of_birth (str): Person's Place of Birth.
            popularity (float): Person's Popularity.
            profile_path (str): Profile Path.
            profile_url (str): Profile Full URL.
            profiles (List[:class:`~tmdbapis.objs.image.Profile`]): List of other Profiles for the Person.
            movie_cast (List[:class:`~tmdbapis.objs.reload.Credit`]): List of Movie Cast Credits for the Person.
            movie_crew (List[:class:`~tmdbapis.objs.reload.Credit`]): List of Movie Crew Credits for the Person.
            tagged (class:`~tmdbapis.objs.pagination.TaggedImages`): Pagination Object of Tagged Images of this Person.
            translations (List[:class:`~tmdbapis.objs.simple.Translation`]): List of Translations for the Person.
            tv_cast (List[:class:`~tmdbapis.objs.reload.Credit`]): List of TV Cast Credits for the Person.
            tv_crew (List[:class:`~tmdbapis.objs.reload.Credit`]): List of TV Crew Credits for the Person.
            tvrage_id (str): TVRage ID for the Person.
            twitter_id (str): Twitter ID for the Person.
    """

    def _load(self, data):
        super()._load(data)
        self.adult = self._parse(attrs="adult", value_type="bool")
        self.also_known_as = self._parse(attrs="also_known_as", is_list=True)
        self.biography = self._parse(attrs="biography")
        self.birthday = self._parse(attrs="birthday", value_type="date")
        self.deathday = self._parse(attrs="deathday", value_type="date")
        self.facebook_id = self._parse(attrs=["external_ids", "facebook_id"])
        self.freebase_id = self._parse(attrs=["external_ids", "freebase_id"])
        self.freebase_mid = self._parse(attrs=["external_ids", "freebase_mid"])
        self.gender = self._parse(attrs="gender", value_type="int")
        self.homepage = self._parse(attrs="homepage")
        self.id = self._parse(attrs="id", value_type="int")
        self.imdb_id = self._parse(attrs="imdb_id")
        self.instagram_id = self._parse(attrs=["external_ids", "instagram_id"])
        self.known_for_department = self._parse(attrs="known_for_department")
        self.name = self._parse(attrs="name")
        self.place_of_birth = self._parse(attrs="place_of_birth")
        self.popularity = self._parse(attrs="popularity", value_type="float")
        self.profile_path = self._parse(attrs="profile_path")
        self.profile_url = self._image_url(self.profile_path)
        self.profiles = self._parse(attrs=["images", "profiles"], value_type="profile", is_list=True)
        self.movie_cast = self._parse(attrs=["movie_credits", "cast"], value_type="movie_cast", is_list=True)
        self.movie_crew = self._parse(attrs=["movie_credits", "crew"], value_type="movie_crew", is_list=True)
        self.tagged = self._parse(attrs="tagged_images", value_type="tagged_images", key=self.id)
        self.translations = self._parse(attrs=["translations", "translations"], value_type="translation", is_list=True)
        self.tv_cast = self._parse(attrs=["tv_credits", "cast"], value_type="tv_cast", is_list=True)
        self.tv_crew = self._parse(attrs=["tv_credits", "crew"], value_type="tv_crew", is_list=True)
        self.tvrage_id = self._parse(attrs=["external_ids", "tvrage_id"], value_type="int")
        self.twitter_id = self._parse(attrs=["external_ids", "twitter_id"])
        self._finish(self.name)

    def _full_load(self):
        return self._api.people_get_details(
            self.id,
            language=self._tmdb.language,
            append_to_response="movie_credits,tv_credits,external_ids,images,tagged_images,translations"
        )


class Review(TMDbReload):
    """ Represents a single Review.

        Attributes:
            author (str): Review Author.
            avatar_path (str): Review Author Avatar Path.
            avatar_url (str): Review Author Avatar Full URL.
            content (str): Review content.
            created_at (datetime): Date Review was Created.
            id (str): Review ID.
            iso_639_1 (str): Default ISO 639-1 Language Code of the Review.
            language (:class:`~tmdbapis.objs.simple.Language`): Language object for the ISO 639-1 Language Code.
            media_id (int): Media ID of the Review.
            media_title (str): Media Title of the Review.
            media_type (str): Media Type of the Media ID.
            rating (float): Review Rating.
            updated_at (datetime): Date Review was Updated.
            url (str): Review URL.
            username (str): Review Author Username.
    """

    def _load(self, data):
        super()._load(data)
        self.author = self._parse(attrs="author")
        self.avatar_path = self._parse(attrs=["author_details", "avatar_path"])
        self.avatar_url = self._image_url(self.avatar_path)
        self.content = self._parse(attrs="content")
        self.created_at = self._parse(attrs="created_at", value_type="date")
        self.id = self._parse(attrs="review_id" if "review_id" in self._data else "id")
        self.iso_639_1 = self._parse(attrs="iso_639_1")
        self.language = self._tmdb._get_object(self._data, "language")
        self.media_id = self._parse(attrs="media_id", value_type="int")
        self.media_title = self._parse(attrs="media_title")
        self.media_type = self._parse(attrs="media_type")
        self.rating = self._parse(attrs=["author_details", "rating"], value_type="float")
        self.updated_at = self._parse(attrs="updated_at", value_type="date")
        self.url = self._parse(attrs="url")
        self.username = self._parse(attrs=["author_details", "username"])
        self._finish(self.author)

    def _full_load(self):
        return self._api.reviews_get_details(self.id)


class Season(TMDbReload):
    """ Represents a single Season.

        Attributes:
            aggregate_cast (List[:class:`~tmdbapis.objs.reload.Credit`]): List of Season Aggregate Crew Credits.
            aggregate_crew (List[:class:`~tmdbapis.objs.reload.Credit`]): List of Season Aggregate Crew Credits.
            air_date (datetime): Season Air Date.
            cast (List[:class:`~tmdbapis.objs.reload.Credit`]): List of Season Cast Credits.
            crew (List[:class:`~tmdbapis.objs.reload.Credit`]): List of Season Crew Credits.
            episodes (List[:class:`~tmdbapis.objs.reload.Episode`]): List of Episodes in the Season.
            freebase_id (str): Freebase ID for the Season.
            freebase_mid (str): Freebase MID for the Season.
            id (int): Season ID.
            name (str): Season Name.
            poster_path (str): Poster Path.
            poster_url (str): Poster Full URL.
            posters (List[:class:`~tmdbapis.objs.image.Poster`]): List of other Posters for the Season.
            overview (str): Season Overview.
            season_number (int): Season Number.
            title (str): alias of name.
            translations (List[:class:`~tmdbapis.objs.simple.Translation`]): List of Translations for the Season.
            tv_id (int): TMDb TV Show ID the contains the Season.
            tvdb_id (int): TVDB ID of the Season.
            tvrage_id (int): TV Rage ID of the Season.
            videos (List[:class:`~tmdbapis.objs.simple.Video`]): List of Videos associated with the Season.
    """

    def __init__(self, tmdb, data, tv_id, load=False):
        self._tv_id = tv_id
        super().__init__(tmdb, data=data, load=load)

    def _load(self, data):
        super()._load(data)
        self.aggregate_cast = self._parse(attrs=["aggregate_credits", "cast"], value_type="agg_tv_cast", extend=True)
        self.aggregate_crew = self._parse(attrs=["aggregate_credits", "crew"], value_type="agg_tv_crew", extend=True)
        self.air_date = self._parse(attrs="air_date", value_type="date")
        self.cast = self._parse(attrs=["credits", "cast"], value_type="tv_cast", is_list=True)
        self.crew = self._parse(attrs=["credits", "crew"], value_type="tv_crew", is_list=True)
        self.tv_id = self._tv_id
        self.episodes = self._parse(attrs="episodes", value_type="episode", is_list=True, key=self.tv_id)
        self.freebase_id = self._parse(attrs=["external_ids", "freebase_id"])
        self.freebase_mid = self._parse(attrs=["external_ids", "freebase_mid"])
        self.id = self._parse(attrs="id", value_type="int")
        self.name = self._parse(attrs="name")
        self.overview = self._parse(attrs="overview")
        self.poster_path = self._parse(attrs="poster_path")
        self.poster_url = self._image_url(self.poster_path)
        self.posters = self._parse(attrs=["images", "posters"], value_type="poster", is_list=True)
        self.season_number = self._parse(attrs="season_number", value_type="int")
        self.title = self.name
        self.translations = self._parse(attrs=["translations", "translations"], value_type="translation", is_list=True)
        self.tvdb_id = self._parse(attrs=["external_ids", "tvdb_id"], value_type="int")
        self.tvrage_id = self._parse(attrs=["external_ids", "tvrage_id"], value_type="int")
        self.videos = self._parse(attrs=["videos", "results"], value_type="video", is_list=True)
        self._finish(self.name)

    def _full_load(self):
        return self._api.tv_seasons_get_details(
            self.tv_id, self.season_number,
            language=self._tmdb.language,
            include_image_language=self._tmdb._include_language,
            include_video_language=self._tmdb._include_language,
            append_to_response="account_states,aggregate_credits,credits,external_ids,images,translations,videos"
        )


class TVShow(TMDbReload, Favorite, Rate, Watchlist):
    """ Represents a single TV Show.

        Attributes:
            aggregate_cast (List[:class:`~tmdbapis.objs.reload.Credit`]): List of Aggregate Crew Credits.
            aggregate_crew (List[:class:`~tmdbapis.objs.reload.Credit`]): List of Aggregate Crew Credits.
            alternative_titles (List[:class:`~tmdbapis.objs.simple.AlternativeTitle`]): TV Show Alternative Titles.
            backdrop_path (str): Backdrop Path.
            backdrop_url (str): Backdrop Full URL.
            backdrops (List[:class:`~tmdbapis.objs.image.Still`]): List of other Backdrops for the TV Show.
            cast (List[:class:`~tmdbapis.objs.reload.Credit`]): List of TV Show Cast Credits.
            companies (List[:class:`~tmdbapis.objs.reload.Company`]): List of Production Companies for the TV Show.
            content_ratings (Dict[str, str]): Dictionary of Content Ratings where the keys are the ISO 3166-1 Alpha-2 Country Codes.
            countries (List[:class:`~tmdbapis.objs.simple.Country`]): List of Production Countries for the TV Show.
            created_by (List[:class:`~tmdbapis.objs.reload.Credit`]): List of Credits of who Created the TV Show.
            crew (List[:class:`~tmdbapis.objs.reload.Credit`]): List of TV Show Crew Credits.
            episode_groups (List[:class:`~tmdbapis.objs.reload.EpisodeGroup`]): List of TV Show Episode Groups.
            episode_run_time (List[int]): List of Episode Run Times in this TV Show.
            facebook_id (str): Facebook ID for the TV Show.
            favorite (bool): If this TV Show has been marked as a favorite. (Authentication Required)
            first_air_date (datetime): Date TV Show was First Aired.
            freebase_id (str): Freebase ID for the TV Show.
            freebase_mid (str): Freebase MID for the TV Show.
            genres (List[:class:`~tmdbapis.objs.simple.Genre`]): List of Genres for the TV Show.
            homepage (str): Homepage for the TV Show.
            id (str): TV Show ID.
            imdb_id (str): IMDb ID for the TV Show.
            in_production (bool): If the TV Show is in Production or not.
            instagram_id (str): Instagram ID for the TV Show.
            keywords (List[:class:`~tmdbapis.objs.reload.Keyword`]): List of Keywords for the TV Show.
            languages (List[:class:`~tmdbapis.objs.simple.Language`]): List of Languages for the TV Show.
            last_air_date (datetime): Date TV Show was Last Aired.
            last_episode_to_air (:class:`~tmdbapis.objs.reload.Episode`): Last Episode to Air.
            logos (List[:class:`~tmdbapis.objs.image.Logo`]): List of other Logos for the TV Show.
            name (str): TV Show's Name.
            networks (List[:class:`~tmdbapis.objs.reload.Network`]): List of Networks for the TV Show.
            next_episode_to_air (:class:`~tmdbapis.objs.reload.Episode`): Next Episode to Air.
            number_of_episodes (int): Number of Episodes in the TV Show.
            number_of_seasons (int): Number of Seasons in the TV Show.
            origin_countries (:class:`~tmdbapis.objs.simple.Country`): Origin Countries of the TV Show.
            original_language (:class:`~tmdbapis.objs.simple.Language`): Original Language of the TV Show.
            original_name (str): TV Show's Original Name.
            overview (str): TV Show Overview.
            popularity (float): TV Show's Popularity.
            poster_path (str): Poster Path.
            poster_url (str): Poster Full URL.
            posters (List[:class:`~tmdbapis.objs.image.Poster`]): List of other Posters for the TV Show.
            rated (Union[float, bool]): Your rating for this TV Show or false if you have not rated it. (Authentication Required)
            recommendations (:class:`~tmdbapis.objs.pagination.RecommendedTVShows`): Pagination Object of Recommended TV Show based on this TV Show.
            seasons (List[:class:`~tmdbapis.objs.reload.Season`]): List of Seasons in the TV Show.
            similar (class:`~tmdbapis.objs.pagination.SimilarTVShows`): Pagination Object of Similar TV Show to this TV Show.
            spoken_languages (List[:class:`~tmdbapis.objs.simple.Language`]): List of Spoken Languages for the TV Show.
            status (str): TV Show's Status.
            tagline (str): TV Show's Tagline.
            title (str): alias of name.
            translations (List[:class:`~tmdbapis.objs.simple.Translation`]): List of Translations for the TV Show.
            tvdb_id (int): TVDB ID of the TV Show.
            tvrage_id (int): TV Rage ID of the TV Show.
            twitter_id (str): Twitter ID for the TV Show.
            type (str): Type of TV Show.
            videos (List[:class:`~tmdbapis.objs.simple.Video`]): List of Videos associated with the TV Show.
            vote_average (float): Vote Average for the TV Show.
            vote_count (int): Number of Votes for the TV Show.
            watch_providers (Dict[str, :class:`~tmdbapis.objs.simple.CountryWatchProviders`]): Dictionary of Watch Providers where the keys are the ISO 3166-1 Alpha-2 Country Codes.
            watchlist (bool): If this TV Show has been added to your watchlist. (Authentication Required)
    """

    def _load(self, data):
        super()._load(data)
        self.aggregate_cast = self._parse(attrs=["aggregate_credits", "cast"], value_type="agg_tv_cast", extend=True)
        self.aggregate_crew = self._parse(attrs=["aggregate_credits", "crew"], value_type="agg_tv_crew", extend=True)
        self.alternative_titles = self._parse(attrs=["alternative_titles", "results"],
                                              value_type="alternative_title", is_list=True)
        self.backdrop_path = self._parse(attrs="backdrop_path")
        self.backdrop_url = self._image_url(self.backdrop_path)
        self.backdrops = self._parse(attrs=["images", "backdrops"], value_type="backdrop", is_list=True)
        self.cast = self._parse(attrs=["credits", "cast"], value_type="tv_cast", is_list=True)
        self.companies = self._parse(attrs="production_companies", value_type="company", is_list=True)
        self.content_ratings = self._parse(attrs=["content_ratings", "results"], value_type="content_rating")
        self.countries = self._parse(attrs="production_countries", value_type="country", is_list=True)
        self.created_by = self._parse(attrs="created_by", value_type="tv_cast", is_list=True)
        self.crew = self._parse(attrs=["credits", "crew"], value_type="tv_crew", is_list=True)
        self.episode_groups = self._parse(attrs=["episode_groups", "results"], value_type="episode_group", is_list=True)
        self.episode_run_time = self._parse(attrs="episode_run_time", value_type="int", is_list=True)
        self.facebook_id = self._parse(attrs=["external_ids", "facebook_id"])
        self.favorite = self._parse(attrs=["account_states", "favorite"], value_type="bool")
        self.first_air_date = self._parse(attrs="first_air_date", value_type="date")
        self.freebase_id = self._parse(attrs=["external_ids", "freebase_id"])
        self.freebase_mid = self._parse(attrs=["external_ids", "freebase_mid"])
        self.genres = self._parse(attrs="genres" if "genres" in self._data else "genre_ids", value_type="tv_genre", is_list=True)
        self.homepage = self._parse(attrs="homepage")
        self.id = self._parse(attrs="id", value_type="int")
        self.imdb_id = self._parse(attrs=["external_ids", "imdb_id"])
        self.in_production = self._parse(attrs="in_production", value_type="bool")
        self.instagram_id = self._parse(attrs=["external_ids", "instagram_id"])
        self.keywords = self._parse(attrs=["keywords", "results"], value_type="keyword", is_list=True)
        self.languages = self._parse(attrs="languages", value_type="language", is_list=True)
        self.last_air_date = self._parse(attrs="last_air_date", value_type="date")
        self.last_episode_to_air = self._parse(attrs="last_episode_to_air", value_type="episode", key=self.id)
        self.logos = self._parse(attrs=["images", "logos"], value_type="logo", is_list=True)
        self.name = self._parse(attrs="name")
        self.networks = self._parse(attrs="networks", value_type="network", is_list=True)
        self.next_episode_to_air = self._parse(attrs="next_episode_to_air", value_type="episode", key=self.id)
        self.number_of_episodes = self._parse(attrs="number_of_episodes", value_type="int")
        self.number_of_seasons = self._parse(attrs="number_of_seasons", value_type="int")
        self.origin_countries = self._parse(attrs="origin_country", value_type="country", is_list=True)
        self.original_language = self._parse(attrs="original_language", value_type="language")
        self.original_name = self._parse(attrs="original_name")
        self.overview = self._parse(attrs="overview")
        self.popularity = self._parse(attrs="popularity", value_type="float")
        self.poster_path = self._parse(attrs="poster_path")
        self.poster_url = self._image_url(self.poster_path)
        self.posters = self._parse(attrs=["images", "posters"], value_type="poster", is_list=True)
        try:
            self.rated = self._parse(attrs=["account_states", "rated"], value_type="float")
        except ValueError:
            self.rated = self._parse(attrs=["account_states", "rated"], value_type="bool")
        self.recommendations = self._parse(attrs="recommendations", value_type="recommended_tv", key=self.id)
        self.seasons = self._parse(attrs="seasons", value_type="season", is_list=True, key=self.id)
        self.similar = self._parse(attrs="similar", value_type="similar_tv", key=self.id)
        self.spoken_languages = self._parse(attrs="spoken_languages", value_type="language", is_list=True)
        self.status = self._parse(attrs="status")
        self.tagline = self._parse(attrs="tagline")
        self.title = self.name
        self.translations = self._parse(attrs=["translations", "translations"], value_type="translation", is_list=True)
        self.tvdb_id = self._parse(attrs=["external_ids", "tvdb_id"], value_type="int")
        self.tvrage_id = self._parse(attrs=["external_ids", "tvrage_id"], value_type="int")
        self.twitter_id = self._parse(attrs=["external_ids", "twitter_id"])
        self.type = self._parse(attrs="type")
        self.videos = self._parse(attrs=["videos", "results"], value_type="video", is_list=True)
        self.vote_average = self._parse(attrs="vote_average", value_type="float")
        self.vote_count = self._parse(attrs="vote_count", value_type="int")
        self.watch_providers = self._parse(attrs=["watch/providers", "results"],
                                           value_type="country_watch_provider", is_dict=True)
        self.watchlist = self._parse(attrs=["account_states", "watchlist"], value_type="bool")
        self._finish(self.name)

    def _full_load(self):
        return self._api.tv_get_details(
            self.id,
            language=self._tmdb.language,
            include_image_language=self._tmdb._include_language,
            include_video_language=self._tmdb._include_language,
            append_to_response="account_states,aggregate_credits,alternative_titles,content_ratings,"
                               "credits,episode_groups,external_ids,images,keywords,recommendations,"
                               "similar,translations,videos,watch/providers"
        )

    def _rate(self, rating):
        self._api.tv_rate_tv_show(self.id, rating)

    def _delete_rate(self):
        self._api.tv_delete_rating(self.id)

    def _media_type(self):
        return "tv"
