from tmdbapis.exceptions import NotFound
from tmdbapis.objs.base import TMDbObj


class AlternativeName(TMDbObj):
    """ Represents a single Alternative Name.

        Attributes:
            name (str): Alternative Name.
            type (str): Type of Alternative Name.
    """

    def _load(self, data):
        super()._load(data)
        self.name = self._parse(attrs="name")
        self.type = self._parse(attrs="type")
        self._finish(self.name)


class AlternativeTitle(TMDbObj):
    """ Represents a single Alternative Title.

        Attributes:
            title (str): Alternative Title.
            type (str): Type of Alternative Title.
    """

    def _load(self, data):
        super()._load(data)
        self.title = self._parse(attrs="title")
        self.type = self._parse(attrs="type")
        self._finish(self.title)


class Certification(TMDbObj):
    """ Represents a single Certification.

        Attributes:
            certification (str): Certification text.
            meaning (str): Certification meaning.
            order (int): Certification Order.
    """

    def _load(self, data):
        super()._load(data)
        self.certification = self._parse(attrs="certification")
        self.meaning = self._parse(attrs="meaning")
        self.order = self._parse(attrs="order", value_type="int")
        self._finish(self.certification)


class Country(TMDbObj):
    """ Represents a single Country.

        Attributes:
            iso_3166_1 (str): ISO 3166-1 Alpha-2 Code of the Country.
            name (str): Country name.
            native_name (str): Country native name.
    """

    def _load(self, data):
        super()._load(data)
        self.iso_3166_1 = self._parse(attrs="iso_3166_1")
        self.name = self._parse(attrs="name" if "name" in self._data else "english_name")
        self.native_name = self._parse(attrs="native_name")
        self._finish(self.name)


class CountryCertifications(TMDbObj):
    """ Represents a Country's Certifications.

        Attributes:
            certifications (List[:class:`~tmdbapis.objs.simple.Certification`]): List of Certifications.
            country (str): Certification country.
    """

    def __init__(self, tmdb, data, country):
        self._country = country
        super().__init__(tmdb, data)

    def _load(self, data):
        super()._load(data)
        self.certifications = self._parse(value_type="certification", is_list=True)
        self.certifications.sort(key=lambda x: x.order)
        self.country = self._country
        self._finish(self.country)

    def __str__(self):
        return f"{self._name} Certifications"


class CountryWatchProviders(TMDbObj):
    """ Represents the Watch Providers for an item in the Country.

        Attributes:
            buy (List[:class:`~tmdbapis.objs.simple.WatchProvider`]): Watch Provider's that can sell this item in the Country.
            country (:class:`~tmdbapis.objs.simple.Country`): Country object for the ISO 3166-1 Country Code.
            flatrate (List[:class:`~tmdbapis.objs.simple.WatchProvider`]): Watch Provider's that have this as part of their service's flatrate in the Country.
            iso_3166_1 (str): ISO 3166-1 Alpha-2 Country Code of the Video.
            link (int): Link to the Countries Watch Provider page for the item.
            rent (List[:class:`~tmdbapis.objs.simple.WatchProvider`]): Watch Provider's that can rent this item in the Country.
    """

    def __init__(self, tmdb, data, country):
        self._country = country
        super().__init__(tmdb, data)

    def _load(self, data):
        super()._load(data)
        self.buy = self._parse(attrs="buy", value_type="watch_provider", is_list=True)
        self.country = self._tmdb._get_object(self._data, "country")
        self.flatrate = self._parse(attrs="flatrate", value_type="watch_provider", is_list=True)
        self.iso_3166_1 = self._country
        self.link = self._parse(attrs="link")
        self.rent = self._parse(attrs="rent", value_type="watch_provider", is_list=True)
        self._finish(self.country)

    def __str__(self):
        return f"{self._name} Watch Providers"


class Department(TMDbObj):
    """ Represents a single Department.

        Attributes:
            department (int): Department name.
            jobs (List[str]): List of jobs within the department.
    """

    def _load(self, data):
        super()._load(data)
        self.department = self._parse(attrs="department")
        self.jobs = self._parse(attrs="jobs", is_list=True)
        self._finish(self.department)


class FindResults(TMDbObj):
    """ Represents a Find search result.

        Attributes:
            movie_results (List[:class:`~tmdbapis.objs.reload.Movie`]): Movie results found.
            person_results (List[:class:`~tmdbapis.objs.reload.Person`]): Person results found.
            tv_episode_results (List[:class:`~tmdbapis.objs.reload.Episode`]): Episode results found.
            tv_results (List[:class:`~tmdbapis.objs.reload.TVShow`]): TV Show results found.
            tv_season_results (List[:class:`~tmdbapis.objs.reload.Season`]): Season results found.
    """

    def __init__(self, tmdb, external_id, external_source):
        self._external_id = external_id
        self._external_source = external_source
        super().__init__(tmdb, None)

    def _load(self, data):
        super()._load(self._api.find_find_by_id(self._external_id, self._external_source, language=self._tmdb.language))
        self.movie_results = self._parse(attrs="movie_results", value_type="movie", is_list=True)
        self.person_results = self._parse(attrs="person_results", value_type="person", is_list=True)
        self.tv_episode_results = self._parse(attrs="tv_episode_results", value_type="episode", is_list=True)
        self.tv_results = self._parse(attrs="tv_results", value_type="tv", is_list=True)
        self.tv_season_results = self._parse(attrs="tv_season_results", value_type="season", is_list=True)
        if not self.movie_results and not self.person_results and not self.tv_results and not self.tv_episode_results and not self.tv_season_results:
            raise NotFound(f"No Results were found for {self._external_source}: {self._external_id}")
        self._finish("FindResults Results")


class Genre(TMDbObj):
    """ Represents a single Genre.

        Attributes:
            id (int): Genre ID
            name (str): Genre name.
    """

    def _load(self, data):
        super()._load(data)
        self.id = self._parse(attrs="id", value_type="int")
        self.name = self._parse(attrs="name")
        self._finish(self.name)


class Group(TMDbObj):
    """ Represents a single Group of Episodes.

        Attributes:
            episode_group_id (int): Episode Group ID.
            episodes (List[:class:`~tmdbapis.objs.reload.Episode`]): List of episodes in the group.
            locked (bool): Is Locked.
            name (str): Group name.
            order (str): Group order in the Episode Group.
    """

    def _load(self, data):
        super()._load(data)
        self.episode_group_id = self._parse(attrs="id")
        self.episodes = self._parse(attrs="episodes", value_type="episode", is_list=True)
        self.locked = self._parse(attrs="locked", value_type="bool")
        self.name = self._parse(attrs="name")
        self.order = self._parse(attrs="order", value_type="int")
        self._finish(self.name)


class Language(TMDbObj):
    """ Represents a single Language.

        Attributes:
            english_name (str): Language's english name.
            iso_639_1 (str): ISO 639-1 Code of the Language.
            name (str): Language name.
    """

    def _load(self, data):
        super()._load(data)
        self.english_name = self._parse(attrs="english_name")
        self.iso_639_1 = self._parse(attrs="iso_639_1")
        self.name = self._parse(attrs="name")
        self._finish(self.english_name)


class ReleaseDate(TMDbObj):
    """ Represents a Movie's Release Date.

        Release dates support different types:

            1. Premiere
            2. Theatrical (limited)
            3. Theatrical
            4. Digital
            5. Physical
            6. TV

        Attributes:
            certification (str): Movie's Certification.
            iso_639_1 (str): ISO 639-1 Language Code of the Release Date.
            language (:class:`~tmdbapis.objs.simple.Language`): Language object for the ISO 639-1 Language Code.
            note (str): Note about the release date.
            release_date (datetime): Movie's release date.
            type (int): Type of release.
    """

    def _load(self, data):
        super()._load(data)
        self.certification = self._parse(attrs="certification")
        self.iso_639_1 = self._parse(attrs="iso_639_1")
        self.language = self._tmdb._get_object(self._data, "language")
        self.note = self._parse(attrs="note")
        self.release_date = self._parse(attrs="release_date", value_type="date")
        self.type = self._parse(attrs="type", value_type="int")
        self._finish(self.release_date)


class Timezones(TMDbObj):
    """ Represents the Timezones of a Country.

        Attributes:
            iso_3166_1 (str): ISO 3166-1 Alpha-2 Country Code of the Timezones.
            zones (List[str]): List of timezones.
    """

    def _load(self, data):
        super()._load(data)
        self.iso_3166_1 = self._parse(attrs="iso_3166_1")
        self.zones = self._parse(attrs="zones", is_list=True)
        self._finish(self.iso_3166_1)


class Trailer(TMDbObj):
    """ Represents a single Trailer.

        Attributes:
            name (str): Trailer name.
            size (str): Trailer size.
            source (str): Trailer source.
            type (str): Trailer type.
    """

    def _load(self, data):
        super()._load(data)
        self.name = self._parse(attrs="name")
        self.size = self._parse(attrs="size")
        self.source = self._parse(attrs="source")
        self.type = self._parse(attrs="type")
        self._finish(self.name)


class Translation(TMDbObj):
    """ Represents a single Translation.

        Attributes:
            biography (str): Translated Biography of :class:`~tmdbapis.objs.reload.Person`
            country (:class:`~tmdbapis.objs.simple.Country`): Country object for the ISO 3166-1 Country Code.
            english_language_name (str): Language English Name.
            homepage (str): Translated Homepage of :class:`~tmdbapis.objs.reload.Collection`, :class:`~tmdbapis.objs.reload.Movie`, and :class:`~tmdbapis.objs.reload.TVShow`
            iso_3166_1 (str): ISO 3166-1 Alpha-2 Country Code of the Translation.
            iso_639_1 (str): ISO 639-1 Language Code of the Translation.
            language (:class:`~tmdbapis.objs.simple.Language`): Language object for the ISO 639-1 Language Code.
            language_name (str): Language Native Name.
            name (str): Translated Name of :class:`~tmdbapis.objs.reload.TVShow`, :class:`~tmdbapis.objs.reload.Season`, and :class:`~tmdbapis.objs.reload.Episode`.
            overview (str): Translated Overview of :class:`~tmdbapis.objs.reload.Collection`, :class:`~tmdbapis.objs.reload.Movie`, :class:`~tmdbapis.objs.reload.TVShow`, :class:`~tmdbapis.objs.reload.Season`, and :class:`~tmdbapis.objs.reload.Episode`.
            title (str): Translated Title of :class:`~tmdbapis.objs.reload.Collection` and :class:`~tmdbapis.objs.reload.Movie`.
    """

    def _load(self, data):
        super()._load(data)
        self.country = self._tmdb._get_object(self._data, "country")
        self.english_language_name = self._parse(attrs="english_name")
        self.iso_3166_1 = self._parse(attrs="iso_3166_1")
        self.iso_639_1 = self._parse(attrs="iso_639_1")
        self.language = self._tmdb._get_object(self._data, "language")
        self.language_name = self._parse(attrs="name")
        if "data" in self._data and self._data["data"]:
            if "biography" in self._data["data"]:
                self.biography = self._parse(attrs=["data", "biography"])
            if "homepage" in self._data["data"]:
                self.homepage = self._parse(attrs=["data", "homepage"])
            if "name" in self._data["data"]:
                self.name = self._parse(attrs=["data", "name"])
            if "overview" in self._data["data"]:
                self.overview = self._parse(attrs=["data", "overview"])
            if "title" in self._data["data"]:
                self.title = self._parse(attrs=["data", "title"])

        self._finish(self.english_language_name)


class User(TMDbObj):
    """ Represents a single User.

        Attributes:
            id (str): V4 User ID.
            gravatar_hash (str): User's gravatar hash.
            name (str) User's name.
            username (str) User's username.
    """

    def _load(self, data):
        super()._load(data)
        self.id = self._parse(attrs="id")
        self.gravatar_hash = self._parse(attrs="gravatar_hash")
        self.name = self._parse(attrs="name")
        self.username = self._parse(attrs="username")
        self._finish(self.username)


class Video(TMDbObj):
    """ Represents a single Video.

        Attributes:
            country (:class:`~tmdbapis.objs.simple.Country`): Country object for the ISO 3166-1 Country Code.
            id (str): Video ID.
            iso_3166_1 (str): ISO 3166-1 Alpha-2 Country Code of the Video.
            iso_639_1 (str): ISO 639-1 Language Code of the Video.
            key (str): Video Key.
            language (:class:`~tmdbapis.objs.simple.Language`): Language object for the ISO 639-1 Language Code.
            name (str): Video Name.
            official (bool): Official Video.
            published_at (datetime): Date video was published at.
            site (str): Video Site.
            size (str): Video Size.
            type (str): Video Type.
    """

    def _load(self, data):
        super()._load(data)
        self.country = self._tmdb._get_object(self._data, "country")
        self.id = self._parse(attrs="id")
        self.iso_3166_1 = self._parse(attrs="iso_3166_1")
        self.iso_639_1 = self._parse(attrs="iso_639_1")
        self.key = self._parse(attrs="key")
        self.language = self._tmdb._get_object(self._data, "language")
        self.name = self._parse(attrs="name")
        self.official = self._parse(attrs="official", value_type="bool")
        self.published_at = self._parse(attrs="published_at", value_type="date")
        self.site = self._parse(attrs="site")
        self.size = self._parse(attrs="size", value_type="int")
        self.type = self._parse(attrs="type")
        self._finish(self.name)


class WatchProvider(TMDbObj):
    """ Represents a single Watch Provider.

        Attributes:
            display_priority (int): Watch Provider display priority.
            id (int): Watch Provider ID.
            logo_path (str): Watch Provider logo path.
            logo_url (str): Watch Provider full logo url.
            name (str): WatchProvider Name.
    """

    def _load(self, data):
        self._data = data
        self._loading = True
        self.display_priority = self._parse(attrs="display_priority", value_type="int")
        self.id = self._parse(attrs="provider_id", value_type="int")
        self.logo_path = self._parse(attrs="logo_path")
        self.logo_url = self._image_url(self.logo_path)
        self.name = self._parse(attrs="provider_name")
        self._finish(self.name)
