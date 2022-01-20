from abc import abstractmethod
from typing import Optional, Union, List, Tuple
from urllib.parse import urlparse, parse_qs

from tmdbapis.objs.base import TMDbObj
from tmdbapis.objs.reload import Movie, TVShow
from tmdbapis import util
from tmdbapis.exceptions import NotFound, Invalid


class TMDbPagination(TMDbObj):
    """ Represents a Pagination Object. The standard iterator only loops through the current page.

        Attributes:
            page (int): Current Page.
            results (int): Current Page's Results.
            total_pages (int): Total Pages.
            total_results (int): Total Results.
    """
    def __init__(self, tmdb, data, value_type, page_type):
        self._value_type = value_type
        self._page_type = page_type
        self._results_text = None
        self._total_results_text = None
        self._single_load = False
        self._page_storage = {}
        self._params = parse_qs(urlparse(tmdb._api.response.url).query)
        super().__init__(tmdb=tmdb, data=data)

    def _load(self, data):
        self._partial = data is not None
        super()._load(self._get_page(1) if data is None else data)
        self.page = 1 if self._single_load else self._parse(attrs="page", value_type="int")
        self.total_pages = 1 if self._single_load else self._parse(attrs="total_pages", value_type="int")
        if self._total_results_text:
            self.total_results = self._parse(attrs=self._total_results_text, value_type="int")
            setattr(self, self._total_results_text, self.total_results)
        else:
            self.total_results = self._parse(attrs="total_results", value_type="int")
        if self._results_text:
            self.results = self._parse(attrs=self._results_text, value_type=self._value_type, is_list=True)
            setattr(self, self._results_text, self.results)
        else:
            self.results = self._parse(attrs="results", value_type=self._value_type, is_list=True)
        self._page_storage[self.page] = self.results
        self._finish(self._page_type)

    def load_next(self):
        """ Loads the next page of the Paginated Object.

            Returns:
                List[:class:`~tmdbapis.objs.pagination.Movie`]: List of Movies that changed.

            Raises:
                :class:`~tmdbapis.exceptions.Invalid`: When ``start_date`` or ``end_date`` is in an incorrect format.
        """
        if self.page + 1 > self.total_pages:
            raise NotFound("No Next Page")
        self.load_page(self.page + 1)

    def load_page(self, page: int):
        """ Loads the page of the Paginated Object.

            Parameters:
                page (int): page number to load.

            Raises:
                :class:`~tmdbapis.exceptions.Invalid`: When ``page`` is not in the range of valid page numbers.
        """
        page = int(page)
        if page < 1 or page > self.total_pages:
            raise Invalid(f"Page must be an integer 1-{self.total_pages}")
        if page in self._page_storage:
            self._loading = True
            self.results = self._page_storage[page]
            self.page = page
            self._loading = False
        else:
            self._load(self._get_page(page))

    def __iter__(self):
        return (o for o in self.results)

    def __len__(self):
        return self.total_results

    @abstractmethod
    def _get_page(self, page):
        pass

    def get_results(self, amount: int):
        """ Gets the amount of results asked for from multiple pages. This method can make alot of calls to the API if you're not careful.

            Parameters:
                amount (int): Amount of Items you want returned.

            Raises:
                :class:`~tmdbapis.exceptions.Invalid`: When ``amount`` is not greater than zero.
         """
        if int(amount) > self.total_results:
            amount = self.total_results
        if amount < 1:
            raise Invalid("amount must be greater then 0")
        results = []
        current_page = 0
        while len(results) < amount and current_page < self.total_pages:
            current_page += 1
            self.load_page(current_page)
            if len(results) + len(self.results) < amount:
                results.extend(self.results)
            else:
                results.extend(self.results[:amount-len(results)])
        return results


class CreatedLists(TMDbPagination):
    """ Paginated Object of the lists created by an account. Will include private lists if you are the owner. """
    def __init__(self, tmdb, v3=False):
        self._v3 = v3 or tmdb._api4 is None
        super().__init__(tmdb, None, "list", "CreatedLists")

    def _get_page(self, page):
        if self._v3 or not self._api4.has_write_token:
            return self._api.account_get_created_lists(language=self._tmdb.language, page=page)
        else:
            return self._api4.account_get_lists(page=page)


class DiscoverMovies(TMDbPagination):
    """ Paginated Object of the Movie Discover search results. """
    def __init__(self, tmdb, **kwargs):
        self._kwargs = kwargs
        self._kwargs["language"] = tmdb.language
        super().__init__(tmdb, None, "movie", "DiscoverMovies")

    def _get_page(self, page):
        self._kwargs["page"] = page
        return self._api.discover_movie_discover(**self._kwargs)


class DiscoverTVShows(TMDbPagination):
    """ Paginated Object of the TV Discover search results. """
    def __init__(self, tmdb, **kwargs):
        self._kwargs = kwargs
        self._kwargs["language"] = tmdb.language
        super().__init__(tmdb, None, "tv", "DiscoverTVShows")

    def _get_page(self, page):
        self._kwargs["page"] = page
        return self._api.discover_tv_discover(**self._kwargs)


class FavoriteMovies(TMDbPagination):
    """ Paginated Object of your favorite movies.

        Attributes:
            sort_by (str): How the paginated object is sorted.
    """
    def __init__(self, tmdb, sort_by=None, v3=False):
        self._v3 = v3 or tmdb._api4 is None
        self._loading = True
        self.sort_by = util.validate_sort(sort_by, self._v3, True)
        self._loading = False
        super().__init__(tmdb, None, "movie", "FavoriteMovies")

    def _get_page(self, page):
        if self._v3 or not self._api4.has_write_token:
            return self._api.account_get_favorite_movies(language=self._tmdb.language, sort_by=self.sort_by, page=page)
        else:
            return self._api4.account_get_favorite_movies(sort_by=self.sort_by, page=page)


class FavoriteTVShows(TMDbPagination):
    """ Paginated Object of your favorite TV shows.

        Attributes:
            sort_by (str): How the paginated object is sorted.
    """
    def __init__(self, tmdb, sort_by=None, v3=False):
        self._v3 = v3 or tmdb._api4 is None
        self._loading = True
        self.sort_by = util.validate_sort(sort_by, self._v3, False)
        self._loading = False
        super().__init__(tmdb, None, "tv", "FavoriteTVShows")

    def _get_page(self, page):
        if self._v3 or not self._api4.has_write_token:
            return self._api.account_get_favorite_tv_shows(language=self._tmdb.language, sort_by=self.sort_by, page=page)
        else:
            return self._api4.account_get_favorite_tv_shows(sort_by=self.sort_by, page=page)


class RatedEpisodes(TMDbPagination):
    """ Paginated Object of the TV episodes you have rated.

        Attributes:
            sort_by (str): How the paginated object is sorted.
    """
    def __init__(self, tmdb, sort_by=None):
        self._loading = True
        self.sort_by = util.validate_sort(sort_by, True, False)
        self._loading = False
        super().__init__(tmdb, None, "episode", "RatedEpisodes")

    def _get_page(self, page):
        return self._api.account_get_rated_tv_episodes(language=self._tmdb.language, sort_by=self.sort_by, page=page)


class RatedMovies(TMDbPagination):
    """ Paginated Object of the movies you have rated.

        Attributes:
            sort_by (str): How the paginated object is sorted.
    """
    def __init__(self, tmdb, sort_by=None, v3=False):
        self._v3 = v3 or tmdb._api4 is None
        self._loading = True
        self.sort_by = util.validate_sort(sort_by, self._v3, True)
        self._loading = False
        super().__init__(tmdb, None, "movie", "RatedMovies")

    def _get_page(self, page):
        if self._v3 or not self._api4.has_write_token:
            return self._api.account_get_rated_movies(language=self._tmdb.language, sort_by=self.sort_by, page=page)
        else:
            return self._api4.account_get_rated_movies(sort_by=self.sort_by, page=page)


class RatedTVShows(TMDbPagination):
    """ Paginated Object of the TV shows you have rated.

        Attributes:
            sort_by (str): How the paginated object is sorted.
    """
    def __init__(self, tmdb, sort_by=None, v3=False):
        self._v3 = v3 or tmdb._api4 is None
        self._loading = True
        self.sort_by = util.validate_sort(sort_by, self._v3, False)
        self._loading = False
        super().__init__(tmdb, None, "tv", "RatedTVShows")

    def _get_page(self, page):
        if self._v3 or not self._api4.has_write_token:
            return self._api.account_get_rated_tv_shows(language=self._tmdb.language, sort_by=self.sort_by, page=page)
        else:
            return self._api4.account_get_rated_tv_shows(sort_by=self.sort_by, page=page)


class MovieLists(TMDbPagination):
    """ Paginated Object of the lists that this movie belongs to.

        Attributes:
            movie_id (int): Movie ID referenced by this Paginated Object.
    """
    def __init__(self, tmdb, data, movie_id):
        self._loading = True
        self.movie_id = movie_id
        self._loading = False
        super().__init__(tmdb, data, "list", "MovieLists")

    def _get_page(self, page):
        return self._api.movies_get_lists(self.movie_id, language=self._tmdb.language, page=page)


class MovieRecommendations(TMDbPagination):
    """ Paginated Object of your personal movie recommendations.

        Attributes:
            sort_by (str): How the paginated object is sorted.
    """
    def __init__(self, tmdb, sort_by=None):
        self._loading = True
        self.sort_by = util.validate_sort(sort_by, False, True)
        self._loading = False
        super().__init__(tmdb, None, "movie", "MovieRecommendations")

    def _get_page(self, page):
        return self._tmdb._v4_check(write=True).account_get_movie_recommendations(sort_by=self.sort_by, page=page)


class MovieReviews(TMDbPagination):
    """ Paginated Object of user reviews for a movie.

        Attributes:
            movie_id (int): Movie ID referenced by this Paginated Object.
    """
    def __init__(self, tmdb, data, movie_id):
        self._loading = True
        self.movie_id = movie_id
        self._loading = False
        super().__init__(tmdb, data, "review", "MovieReviews")

    def _get_page(self, page):
        return self._api.movies_get_reviews(self.movie_id, language=self._tmdb.language, page=page)


class MovieWatchlist(TMDbPagination):
    """ Paginated Object of the movies you have added to your watchlist.

        Attributes:
            sort_by (str): How the paginated object is sorted.
    """
    def __init__(self, tmdb, sort_by=None, v3=False):
        self._v3 = v3 or tmdb._api4 is None
        self._loading = True
        self.sort_by = util.validate_sort(sort_by, self._v3, True)
        self._loading = False
        super().__init__(tmdb, None, "movie", "MovieWatchlist")

    def _get_page(self, page):
        if self._v3 or not self._api4.has_write_token:
            return self._api.account_get_movie_watchlist(language=self._tmdb.language, sort_by=self.sort_by, page=page)
        else:
            return self._api4.account_get_movie_watchlist(sort_by=self.sort_by, page=page)


class NowPlayingMovies(TMDbPagination):
    """ Paginated Object of movies in theatres.

        Attributes:
            region (str): ISO 3166-1 code used to filter release dates.
            maximum_date (datetime): Maximum Date.
            minimum_date (datetime): Minimum Date.
    """
    def __init__(self, tmdb, region=None):
        self._loading = True
        self.region = region
        self._loading = False
        super().__init__(tmdb, None, "movie", "NowPlayingMovies")

    def _load(self, data):
        super()._load(data)
        self._loading = True
        self.maximum_date = self._parse(attrs=["dates", "maximum"], value_type="date")
        self.minimum_date = self._parse(attrs=["dates", "minimum"], value_type="date")
        self._loading = False

    def _get_page(self, page):
        return self._api.movies_get_now_playing(language=self._tmdb.language, region=self.region, page=page)


class PopularMovies(TMDbPagination):
    """ Paginated Object of the current popular movies on TMDB.

        Attributes:
            region (str): ISO 3166-1 code used to filter release dates.
    """
    def __init__(self, tmdb, region=None):
        self._loading = True
        self.region = region
        self._loading = False
        super().__init__(tmdb, None, "movie", "PopularMovies")

    def _get_page(self, page):
        return self._api.movies_get_popular(language=self._tmdb.language, region=self.region, page=page)


class PopularPeople(TMDbPagination):
    """ Paginated Object of the list of popular people on TMDB. """
    def __init__(self, tmdb):
        super().__init__(tmdb, None, "person", "PopularPerson")

    def _get_page(self, page):
        return self._api.people_get_popular(self._tmdb.language, page=page)


class PopularTVShows(TMDbPagination):
    """ Paginated Object of the current popular TV shows on TMDB. """
    def __init__(self, tmdb):
        super().__init__(tmdb, None, "tv", "PopularTVShows")

    def _get_page(self, page):
        return self._api.tv_get_popular(language=self._tmdb.language, page=page)


class RecommendedMovies(TMDbPagination):
    """ Paginated Object of recommended movies for a movie.

        Attributes:
            movie_id (int): Movie ID referenced by this Paginated Object.
    """
    def __init__(self, tmdb, data, movie_id):
        self._loading = True
        self.movie_id = movie_id
        self._loading = False
        super().__init__(tmdb, data, "movie", "RecommendedMovies")

    def _get_page(self, page):
        return self._api.movies_get_recommendations(self.movie_id, language=self._tmdb.language, page=page)


class RecommendedTVShows(TMDbPagination):
    """ Paginated Object of recommended TV shows for a TV show.

        Attributes:
            tv_id (int): TV ID referenced by this Paginated Object.
    """
    def __init__(self, tmdb, data, tv_id):
        self._loading = True
        self.tv_id = tv_id
        self._loading = False
        super().__init__(tmdb, data, "tv", "RecommendedTVShows")

    def _get_page(self, page):
        return self._api.tv_get_recommendations(self.tv_id, language=self._tmdb.language, page=page)


class SearchCollections(TMDbPagination):
    """ Paginated Object of the Collections Search Results.

        Attributes:
            query (str): Query of the search.
    """
    def __init__(self, tmdb, query):
        self._loading = True
        self.query = query
        self._loading = False
        super().__init__(tmdb, None, "collection", "SearchCollections")

    def _get_page(self, page):
        results = self._api.search_search_collections(self.query, language=self._tmdb.language, page=self.page)
        if int(results["total_results"]) > 0:
            return results
        raise NotFound("No Results Found")


class SearchCompanies(TMDbPagination):
    """ Paginated Object of the Companies Search Results.

        Attributes:
            query (str): Query of the search.
    """
    def __init__(self, tmdb, query):
        self._loading = True
        self.query = query
        self._loading = False
        super().__init__(tmdb, None, "company", "SearchCompanies")

    def _get_page(self, page):
        results = self._api.search_search_companies(self.query, page=self.page)
        if int(results["total_results"]) > 0:
            return results
        raise NotFound("No Results Found")


class SearchKeywords(TMDbPagination):
    """ Paginated Object of the Keywords Search Results.

        Attributes:
            query (str): Query of the search.
    """
    def __init__(self, tmdb, query):
        self._loading = True
        self.query = query
        self._loading = False
        super().__init__(tmdb, None, "keyword", "SearchKeywords")

    def _get_page(self, page):
        results = self._api.search_search_keywords(self.query, page=self.page)
        if int(results["total_results"]) > 0:
            return results
        raise NotFound("No Results Found")


class SearchMovies(TMDbPagination):
    """ Paginated Object of the Movies Search Results.

        Attributes:
            query (str): Query of the search.
            include_adult (bool): Adult results in the search.
            region (str): ISO 3166-1 code used to filter the search.
            year (int): Year used to filter the search.
            primary_release_year (int): Primary Release Year used to filter the search.
    """
    def __init__(self, tmdb, query, include_adult=None, region=None, year=None, primary_release_year=None):
        self._loading = True
        self.query = query
        self.include_adult = include_adult
        self.region = region
        self.year = year
        self.primary_release_year = primary_release_year
        self._loading = False
        super().__init__(tmdb, None, "movie", "SearchMovies")

    def _get_page(self, page):
        results = self._api.search_search_movies(
            self.query,
            language=self._tmdb.language,
            page=self.page,
            include_adult=self.include_adult,
            region=self.region,
            year=self.year,
            primary_release_year=self.primary_release_year
        )
        if int(results["total_results"]) > 0:
            return results
        raise NotFound("No Results Found")


class SearchMulti(TMDbPagination):
    """ Paginated Object of the Multi Search Results.

        Attributes:
            query (str): Query of the search.
            include_adult (bool): Adult results in the search.
            region (str): ISO 3166-1 code used to filter the search.
    """
    def __init__(self, tmdb, query, include_adult=None, region=None):
        self._loading = True
        self.query = query
        self.include_adult = include_adult
        self.region = region
        self._loading = False
        super().__init__(tmdb, None, "media_type", "SearchMulti")

    def _get_page(self, page):
        results = self._api.search_multi_search(
            self.query,
            language=self._tmdb.language,
            page=self.page,
            include_adult=self.include_adult,
            region=self.region
        )
        if int(results["total_results"]) > 0:
            return results
        raise NotFound("No Results Found")


class SearchPeople(TMDbPagination):
    """ Paginated Object of the People Search Results.

        Attributes:
            query (str): Query of the search.
            include_adult (bool): Adult results in the search.
            region (str): ISO 3166-1 code used to filter the search.
    """
    def __init__(self, tmdb, query, include_adult=None, region=None):
        self._loading = True
        self.query = query
        self.include_adult = include_adult
        self.region = region
        self._loading = False
        super().__init__(tmdb, None, "person", "SearchPeople")

    def _get_page(self, page):
        results = self._api.search_search_people(
            self.query,
            language=self._tmdb.language,
            page=self.page,
            include_adult=self.include_adult,
            region=self.region
        )
        if int(results["total_results"]) > 0:
            return results
        raise NotFound("No Results Found")


class SearchTVShows(TMDbPagination):
    """ Paginated Object of the TV Show Search Results.

        Attributes:
            query (str): Query of the search.
            include_adult (bool): Adult results in the search.
            first_air_date_year (int): First Air Date Year used to filter the search.
    """
    def __init__(self, tmdb, query, include_adult=None, first_air_date_year=None):
        self._loading = True
        self.query = query
        self.include_adult = include_adult
        self.first_air_date_year = first_air_date_year
        self._loading = False
        super().__init__(tmdb, None, "tv", "SearchTVShows")

    def _get_page(self, page):
        results = self._api.search_search_tv_shows(
            self.query,
            language=self._tmdb.language,
            page=self.page,
            include_adult=self.include_adult,
            first_air_date_year=self.first_air_date_year
        )
        if int(results["total_results"]) > 0:
            return results
        raise NotFound("No Results Found")


class SimilarMovies(TMDbPagination):
    """ Paginated Object of similar movies for a movie.

        Attributes:
            movie_id (int): Movie ID referenced by this Paginated Object.
    """
    def __init__(self, tmdb, data, movie_id):
        self._loading = True
        self.movie_id = movie_id
        self._loading = False
        super().__init__(tmdb, data, "movie", "SimilarMovies")

    def _get_page(self, page):
        return self._api.movies_get_similar_movies(self.movie_id, language=self._tmdb.language, page=page)


class SimilarTVShows(TMDbPagination):
    """ Paginated Object of similar TV shows for a TV show.

        Attributes:
            tv_id (int): TV ID referenced by this Paginated Object.
    """
    def __init__(self, tmdb, data, tv_id):
        self._loading = True
        self.tv_id = tv_id
        self._loading = False
        super().__init__(tmdb, data, "tv", "SimilarTVShows")

    def _get_page(self, page):
        return self._api.tv_get_similar_tv_shows(self.tv_id, language=self._tmdb.language, page=page)


class TaggedImages(TMDbPagination):
    """ Paginated Object of tagged images for a person.

        Attributes:
            person_id (int): Person ID referenced by this Paginated Object.
    """
    def __init__(self, tmdb, data, person_id):
        self._loading = True
        self.person_id = person_id
        self._loading = False
        super().__init__(tmdb, data, "tagged", "TaggedImages")

    def _get_page(self, page):
        return self._api.people_get_tagged_images(self.person_id, language=self._tmdb.language, page=page)


class TMDbList(TMDbPagination):
    """ Paginated Object of the items in a list.

        Attributes:
            average_rating (float): Average Rating of the items in the List. (v4 Only)
            backdrop_path (str): List backdrop path. (v4 Only)
            backdrop_url (str): List full backdrop url. (v4 Only)
            comments (Dict[str, str]): Dictionary of the comment for each item. (v4 Only)
            country (:class:`~tmdbapis.objs.simple.Country`): Country object for the ISO 3166-1 Country Code. (v4 Only)
            created_by (Union[str, :class:`~tmdbapis.objs.simple.User`]): User who created the list (str for v3 and :class:`~tmdbapis.objs.simple.User` for v4).
            description (str): List Description.
            favorite_count (int): Number of users who have marked this list as a favorite. (v3 Only)
            id (int): List ID.
            iso_3166_1 (str): ISO 3166-1 Alpha-2 Country Code of the List. (v4 Only)
            iso_639_1 (str): ISO 639-1 Language Code of the List.
            language (:class:`~tmdbapis.objs.simple.Language`): Language object for the ISO 639-1 Language Code.
            name (int): List Name.
            object_ids (Dict[str, str]): Dictionary of the object ids for each item. (v4 Only)
            poster_path (str): List poster path.
            poster_url (str): List full poster url.
            public (bool): List Public. (v4 Only)
            revenue (int): Total revenue of the items in the List. (v4 Only)
            runtime (int): Total runtime of the items in the List. (v4 Only)
            sort_by (str): How the List is sorted. (v4 Only)
    """
    def __init__(self, tmdb, data, sort_by=None, load=False):
        self._sort_by = sort_by
        super().__init__(tmdb, data, "media_type", "List")
        if load:
            self._load(None)

    def _load(self, data):
        self._partial = data is not None
        if self._api4:
            self._results_text = None
            self._total_results_text = None
            self._single_load = False
        else:
            self._results_text = "items"
            self._total_results_text = "item_count"
            self._single_load = True
        super()._load(self._get_page(1) if data is None else data)
        self._loading = True
        self.description = self._parse(attrs="description")
        self.id = self._parse(attrs="id", value_type="int")
        self.iso_639_1 = self._parse(attrs="iso_639_1")
        self.language = self._tmdb._get_object(self._data, "language")
        self.name = self._parse(attrs="name")
        self.poster_path = self._parse(attrs="poster_path")
        self.poster_url = self._image_url(self.poster_path)
        if self._api4:
            self.average_rating = self._parse(attrs="average_rating", value_type="float")
            self.backdrop_path = self._parse(attrs="backdrop_path")
            self.backdrop_url = self._image_url(self.backdrop_path)
            self.comments = self._parse(attrs="comments", value_type="dict")
            self.country = self._tmdb._get_object(self._data, "country")
            self.created_by = self._parse(attrs="created_by", value_type="user")
            self.iso_3166_1 = self._parse(attrs="iso_3166_1")
            self.object_ids = self._parse(attrs="object_ids", value_type="dict")
            self.public = self._parse(attrs="public", value_type="bool")
            self.revenue = self._parse(attrs="revenue", value_type="int")
            self.runtime = self._parse(attrs="runtime", value_type="int")
            self.sort_by = self._parse(attrs="sort_by")
        else:
            self.created_by = self._parse(attrs="created_by")
            self.favorite_count = self._parse(attrs="favorite_count", value_type="int")
        self._loading = False

    def _get_page(self, page):
        if self._api4:
            return self._api4.list_get_list(
                self.id,
                language=self._tmdb.language,
                sort_by=self._sort_by,
                page=page
            )
        else:
            return self._api.lists_get_details(
                self.id,
                language=self._tmdb.language
            )

    def reload(self):
        """ Reloads the full object. """
        self._load(None)

    def update(self, name: Optional[str] = None, description: Optional[str] = None,
               public: Optional[bool] = None, sort_by: Optional[str] = None):
        """ Updates the list's metadata.

            Parameters:
                name (Optional[str]): Updates the list name.
                description (Optional[str]): Updates the list description.
                public (Optional[bool]): Updates whether the list is public.
                sort_by (Optional[str]): Updates the list sort_by.

            Raises:
                :class:`~tmdbapis.exceptions.Invalid`: When no attribute is given or the ``sort_by`` given is invalid.
        """
        if name is None and description is None and public is None and sort_by is None:
            raise Invalid("Must have at least one parameter to update (name, description, public, or sort_by)")
        if sort_by and sort_by not in util.v4_list_sorts:
            raise Invalid(f"sort_by not in {util.v4_list_sorts}")
        self._tmdb._v4_check().list_update_list(
            self.id,
            name=name,
            description=description,
            public=public,
            sort_by=sort_by
        )

    def _check_item(self, item):
        if isinstance(item, Movie):
            item_id = item.id
            item_type = "movie"
        elif isinstance(item, TVShow):
            item_id = item.id
            item_type = "tv"
        elif isinstance(item, tuple):
            item_id = int(item[0])
            item_type = item[1]
            if item_type not in ["movie", "tv"]:
                raise Invalid("Tuple must have either 'movie' or 'tv'.")
        else:
            raise Invalid("Item must be either a Movie Object, a TV Show object, or a Tuple of the ID and either 'movie' or 'tv'.")
        if item_type == "tv":
            self._tmdb._v4_check()
        return item_id, item_type

    def has_item(self, item: Union[Movie, TVShow, Tuple[int, str]]) -> bool:
        """ Check to see if the Item given is in the List.

            Parameters:
                item (Union[Movie, TVShow, Tuple[int, str]]): Item you want to check if it's on the list. If not using a Movie or Show object then you must use a Tuple with the ID and either ``movie`` or ``tv``.

            Raises:
                :class:`~tmdbapis.exceptions.Invalid`: When the item given isn't in a valid format.

            Returns:
                bool: Whether the list has the Item or not.
        """
        item_id, item_type = self._check_item(item)
        if self._api4 and self._api4.has_write_token:
            try:
                self._api4.list_check_item_status(self.id, item_id, item_type)
                return True
            except NotFound:
                return False
        else:
            return self._api.lists_check_item_status(self.id, item_id)["item_present"]

    def add_items(self, items: List[Union[Movie, TVShow, Tuple[int, str]]]):
        """ Adds the items given to the list.

            Parameters:
                items (List[Union[Movie, TVShow, Tuple[int, str]]]): Items you want to add to the list. If not using a Movie or Show object then you must use a Tuple with the ID and either ``movie`` or ``tv``.

            Raises:
                :class:`~tmdbapis.exceptions.Invalid`: When the item given isn't in a valid format.

            Returns:
                bool: Whether the list has the Item or not.
        """
        item_ids = []
        if not isinstance(items, list):
            items = [items]
        for item in items:
            item_id, item_type = self._check_item(item)
            item_ids.append({"media_type": item_type, "media_id": item_id})

        if self._api4 and self._api4.has_write_token:
            self._api4.list_add_items(self.id, item_ids)
        else:
            for item_id in item_ids:
                self._api.lists_add_movie(self.id, item_id["media_id"])

    def remove_items(self, items: List[Union[Movie, TVShow, Tuple[int, str]]]):
        """ Adds the items given to the list.

            Parameters:
                items (List[Union[Movie, TVShow, Tuple[int, str]]]): Item you want to remove from the list. If not using a Movie or Show object then you must use a Tuple with the ID and either ``movie`` or ``tv``.

            Raises:
                :class:`~tmdbapis.exceptions.Invalid`: When the item given isn't in a valid format.
        """
        item_ids = []
        if not isinstance(items, list):
            items = [items]
        for item in items:
            item_id, item_type = self._check_item(item)
            item_ids.append({"media_type": item_type, "media_id": item_id})

        if self._api4 and self._api4.has_write_token:
            self._api4.list_remove_items(self.id, item_ids)
        else:
            for item_id in item_ids:
                self._api.lists_remove_movie(self.id, item_id["media_id"])

    def update_items(self, items: List[Tuple[Union[Movie, TVShow, Tuple[int, str]], str]]):
        """ Updates the items on the list.

            Parameters:
                items (List[Tuple[Union[Movie, TVShow, Tuple[int, str]], str]]): Tuples of the items you want updated on the list and their description. If not using a Movie or Show object then you must use a Tuple of the ID and either ``movie`` or ``tv``.

            Raises:
                :class:`~tmdbapis.exceptions.Invalid`: When the item given isn't in a valid format.
        """
        item_ids = []
        if not isinstance(items, list):
            items = [items]
        for item in items:
            item_id, item_type = self._check_item(item[0])
            comment = item[1]
            item_ids.append({"media_type": item_type, "media_id": item_id, "comment": comment})
        self._tmdb._v4_check(write=True).list_update_items(self.id, item_ids)

    def clear(self):
        """ Clear all items from the list. """
        if self._api4 and self._api4.has_write_token:
            self._api4.list_clear_list(self.id)
        else:
            self._api.lists_clear_list(self.id, True)

    def delete(self):
        """ Delete the list. """
        if self._api4 and self._api4.has_write_token:
            self._api4.list_delete_list(self.id)
        else:
            self._api.lists_delete_list(self.id)


class TopRatedMovies(TMDbPagination):
    """ Paginated Object of the top rated movies on TMDB.

        Attributes:
            region (str): ISO 3166-1 code used to filter release dates.
    """
    def __init__(self, tmdb, region=None):
        self._loading = True
        self.region = region
        self._loading = False
        super().__init__(tmdb, None, "movie", "TopRatedMovies")

    def _get_page(self, page):
        return self._api.movies_get_top_rated(language=self._tmdb.language, region=self.region, page=page)


class TopRatedTVShows(TMDbPagination):
    """ Paginated Object of the top rated TV shows on TMDB. """
    def __init__(self, tmdb):
        super().__init__(tmdb, None, "tv", "TopRatedTVShows")

    def _get_page(self, page):
        return self._api.tv_get_top_rated(language=self._tmdb.language, page=page)


class Trending(TMDbPagination):
    """ Paginated Object of daily or weekly trending items.

        Attributes:
            media_type (str): Media type of the Paginated Object.
            time_window (str): Time Window for the Trending.
    """
    def __init__(self, tmdb, media_type, time_window):
        self._loading = True
        self.media_type = media_type
        self.time_window = time_window
        self._loading = False
        super().__init__(tmdb, None, "media_type", "Trending")

    def _get_page(self, page):
        return self._api.trending_get_trending(self.media_type, self.time_window, page=page)


class TVShowRecommendations(TMDbPagination):
    """ Paginated Object of your personal TV show recommendations.

        Attributes:
            sort_by (str): How the paginated object is sorted.
    """
    def __init__(self, tmdb, sort_by=None):
        self._loading = True
        self.sort_by = util.validate_sort(sort_by, False, False)
        self._loading = False
        super().__init__(tmdb, None, "tv", "TVShowRecommendations")

    def _get_page(self, page):
        return self._tmdb._v4_check(write=True).account_get_tv_show_recommendations(sort_by=self.sort_by, page=page)


class TVShowsAiringToday(TMDbPagination):
    """ Paginated Object of TV shows that are airing today. """
    def __init__(self, tmdb):
        super().__init__(tmdb, None, "tv", "TopRatedMovies")

    def _get_page(self, page):
        return self._api.tv_get_tv_airing_today(language=self._tmdb.language, page=page)


class TVShowsOnTheAir(TMDbPagination):
    """ Paginated Object of shows that are currently on the air. """
    def __init__(self, tmdb):
        super().__init__(tmdb, None, "tv", "TVShowsOnTheAir")

    def _get_page(self, page):
        return self._api.tv_get_tv_on_the_air(language=self._tmdb.language, page=page)


class TVShowWatchlist(TMDbPagination):
    """ Paginated Object of the TV shows you have added to your watchlist.

        Attributes:
            sort_by (str): How the paginated object is sorted.
    """
    def __init__(self, tmdb, sort_by=None, v3=False):
        self._v3 = v3 or tmdb._api4 is None
        self._loading = True
        self.sort_by = util.validate_sort(sort_by, self._v3, False)
        self._loading = False
        super().__init__(tmdb, None, "tv", "TVShowWatchlist")

    def _get_page(self, page):
        if self._v3 or not self._api4.has_write_token:
            return self._api.account_get_tv_show_watchlist(language=self._tmdb.language, sort_by=self.sort_by, page=page)
        else:
            return self._api4.account_get_tv_show_watchlist(sort_by=self.sort_by, page=page)


class UpcomingMovies(TMDbPagination):
    """ Paginated Object of upcoming movies in theatres.

        Attributes:
            maximum_date (datetime): Maximum Date.
            minimum_date (datetime): Minimum Date.
    """
    def __init__(self, tmdb, region=None):
        self._loading = True
        self.region = region
        self._loading = False
        super().__init__(tmdb, None, "movie", "UpcomingMovies")

    def _load(self, data):
        super()._load(data)
        self._loading = True
        self.maximum_date = self._parse(attrs=["dates", "maximum"], value_type="date")
        self.minimum_date = self._parse(attrs=["dates", "minimum"], value_type="date")
        self._loading = False

    def _get_page(self, page):
        return self._api.movies_get_upcoming(language=self._tmdb.language, region=self.region, page=page)
