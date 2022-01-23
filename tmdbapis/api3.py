import logging
from json.decoder import JSONDecodeError
from typing import Dict, Optional, Union

from requests import Session, Response
from requests.exceptions import RequestException

from tmdbapis.api4 import API4
from tmdbapis.exceptions import TMDbException, NotFound, Unauthorized, WritePermission, PrivateResource, Authentication

logger = logging.getLogger(__name__)

base_url = "https://api.themoviedb.org/3"

class API3:
    """ Raw V3 API Class containing all `TMDb API3 calls <https://developers.themoviedb.org/3/getting-started/introduction>`__.

        Parameters:
            apikey (str): TMDb V3 API Key.
            session_id (Optional[str]): TMDb V3 Session ID.
            api4 (Optional[API4]): :class:`tmdbapis.api4.API4` object.
            session (Optional[Session]): :class:`requests.Session` object.
            validate (bool): Validate the TMDb V3 API Key on creation.

        Attributes:
            apikey (str): TMDb V3 API Key.
            session_id (str): TMDb V3 Session ID.
            account_id (str): TMDb V3 Account ID.
            response (Response): TMDb V3 most recent full :class:`requests.Response` object.
    """
    def __init__(self, apikey: str, session_id: Optional[str] = None, api4: Optional[API4] = None,
                 session: Optional[Session] = None, validate: bool = True):
        self.apikey = apikey
        self._api4 = api4
        self._session_id = session_id
        self._account_id = None
        self._session = Session() if session is None else session
        self.response = None
        if validate:
            self.configuration_get_api_configuration()

    def _get(self, path, **kwargs):
        """ process get request. """
        return self._request("get", path, **kwargs)

    def _delete(self, path, json=None, **kwargs):
        """ process delete request. """
        return self._request("delete", path, json=json, **kwargs)

    def _post(self, path, json=None, **kwargs):
        """ process post request. """
        return self._request("post", path, json=json, **kwargs)

    def _put(self, path, json=None, **kwargs):
        """ process put request. """
        return self._request("put", path, json=json, **kwargs)

    def _request(self, request_type, path, json=None, **kwargs):
        """ process request. """
        url_params = {"api_key": f"{self.apikey}"}
        for key, value in kwargs.items():
            if value is not None:
                url_params[key] = value
        request_url = f"{base_url}{path}"
        logger.debug(f"Request URL: {request_url}")
        if json is not None:
            logger.debug(f"Request JSON {json}")
        try:
            if request_type == "delete":
                self.response = self._session.delete(request_url, json=json, params=url_params)
            elif request_type == "post":
                self.response = self._session.post(request_url, json=json, params=url_params)
            elif request_type == "put":
                self.response = self._session.put(request_url, json=json, params=url_params)
            else:
                self.response = self._session.get(request_url, params=url_params)
            response_json = self.response.json()
        except (RequestException, JSONDecodeError):
            raise TMDbException(f"Failed to Connect to {base_url}")
        logger.debug(f"Response ({self.response.status_code} [{self.response.reason}]) {response_json}")
        if self.response.status_code == 401:
            if "status_code" in response_json:
                if response_json["status_code"] == 36:
                    raise WritePermission("Requires V4 Authentication, use tmdbapis.v4_authenticate(), then approve the returned URL, and finally run tmdbapis.v4_approved()")
                elif response_json["status_code"] == 39:
                    raise PrivateResource(response_json["status_message"])
                elif response_json["status_code"] == 7:
                    raise Unauthorized(response_json["status_message"])
                else:
                    raise TMDbException(f"({response_json['status_code']}) {response_json['status_message']}")
            else:
                raise TMDbException(f"({self.response.status_code} [{self.response.reason}]) {response_json}")
        elif self.response.status_code == 404:
            raise NotFound(f"({self.response.status_code} [{self.response.reason}]) Requested Item Not Found")
        elif self.response.status_code >= 400:
            raise TMDbException(f"({self.response.status_code} [{self.response.reason}]) {response_json}")
        elif "errors" in response_json:
            raise TMDbException(response_json["errors"])
        elif "success" in response_json and response_json["success"] is False:
            raise TMDbException(response_json["status_message"])
        return response_json

    @property
    def session_id(self):
        if not self._session_id:
            if self._api4 and self._api4.has_write_token:
                self.authentication_create_session_from_v4(self._api4.access_token)
        if not self._session_id:
            raise Authentication("Requires Authentication, use tmdbapis.authenticate(username, password)")
        return self._session_id

    @property
    def account_id(self):
        if not self._account_id:
            self._account_id = self.account_get_details(self.session_id)["id"]
        return self._account_id

    def account_get_details(
            self,
            session_id: Optional[str] = None,
            append_to_response: Optional[str] = None
    ) -> Dict:
        """ `Account Get Details <https://developers.themoviedb.org/3/account/get-account-details>`__

            Get your account details.

            Supports ``append_to_response``. Read more about this `here <https://developers.themoviedb.org/3/getting-started/append-to-response>`__.

            Parameters:
                session_id (Optional[str]): Session ID.
                append_to_response (Optional[str]): Append other requests to the response.
        """
        return self._get(
            "/account",
            session_id=session_id if session_id else self.session_id,
            append_to_response=append_to_response
        )

    def account_get_created_lists(
            self,
            session_id: Optional[str] = None,
            account_id: Optional[str] = None,
            language: Optional[str] = None,
            page: Optional[int] = None
    ) -> Dict:
        """ `Account Get Created Lists <https://developers.themoviedb.org/3/account/get-created-lists>`__

            Get all of the lists created by an account. Will include private lists if you are the owner.

            Parameters:
                session_id (Optional[str]): Session ID.
                account_id (Optional[str]): Account ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                page (Optional[int]): Specify which page to query.
        """
        return self._get(
            f"/account/{account_id if account_id else self.account_id}/lists",
            session_id=session_id if session_id else self.session_id,
            language=language,
            page=page
        )

    def account_get_favorite_movies(
            self,
            session_id: Optional[str] = None,
            account_id: Optional[str] = None,
            language: Optional[str] = None, 
            sort_by: Optional[str] = None, 
            page: Optional[str] = None
    ) -> Dict:
        """ `Account Get Favorite Movies <https://developers.themoviedb.org/3/account/get-favorite-movies>`__

            Get the list of your favorite movies.

            Parameters:
                session_id (Optional[str]): Session ID.
                account_id (Optional[str]): Account ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                sort_by (Optional[str]): Sort the results. Allowed Values: ``created_at.asc`` and ``created_at.desc``
                page (Optional[int]): Specify which page to query.
        """
        return self._get(
            f"/account/{account_id if account_id else self.account_id}/favorite/movies",
            session_id=session_id if session_id else self.session_id,
            language=language,
            sort_by=sort_by,
            page=page
        )

    def account_get_favorite_tv_shows(
            self,
            session_id: Optional[str] = None,
            account_id: Optional[str] = None,
            language: Optional[str] = None, 
            sort_by: Optional[str] = None, 
            page: Optional[str] = None
    ) -> Dict:
        """ `Account Get Favorite TV Shows <https://developers.themoviedb.org/3/account/get-favorite-tv-shows>`__

            Get the list of your favorite TV shows.

            Parameters:
                session_id (Optional[str]): Session ID.
                account_id (Optional[str]): Account ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                sort_by (Optional[str]): Sort the results. Allowed Values: ``created_at.asc`` and ``created_at.desc``
                page (Optional[int]): Specify which page to query.
        """
        return self._get(
            f"/account/{account_id if account_id else self.account_id}/favorite/tv",
            session_id=session_id if session_id else self.session_id,
            language=language,
            sort_by=sort_by,
            page=page
        )

    def account_mark_as_favorite(
            self, media_type: str, media_id: int, favorite: bool,
            session_id: Optional[str] = None,
            account_id: Optional[str] = None
    ) -> Dict:
        """ `Account Mark as Favorite <https://developers.themoviedb.org/3/account/mark-as-favorite>`__

            This method allows you to mark a movie or TV show as a favorite item.

            Parameters:
                session_id (Optional[str]): Session ID.
                account_id (Optional[str]): Account ID.
                media_type (str): Media Type. Allowed Values: ``movie`` and ``tv``
                media_id (int): Media ID.
                favorite (bool): Mark or Remove as favorite.
        """
        return self._post(
            f"/account/{account_id if account_id else self.account_id}/favorite",
            json={
                "media_type": media_type,
                "media_id": media_id,
                "favorite": favorite
            },
            session_id=session_id if session_id else self.session_id
        )

    def account_get_rated_movies(
            self,
            session_id: Optional[str] = None,
            account_id: Optional[str] = None,
            language: Optional[str] = None,
            sort_by: Optional[str] = None,
            page: Optional[str] = None
    ) -> Dict:
        """ `Account Get Rated Movies <https://developers.themoviedb.org/3/account/get-rated-movies>`__

            Get a list of all the movies you have rated.

            Parameters:
                session_id (Optional[str]): Session ID.
                account_id (Optional[str]): Account ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                sort_by (Optional[str]): Sort the results. Allowed Values: ``created_at.asc`` and ``created_at.desc``
                page (Optional[int]): Specify which page to query.
        """
        return self._get(
            f"/account/{account_id if account_id else self.account_id}/rated/movies",
            session_id=session_id if session_id else self.session_id,
            language=language,
            sort_by=sort_by,
            page=page
        )

    def account_get_rated_tv_shows(
            self,
            session_id: Optional[str] = None,
            account_id: Optional[str] = None,
            language: Optional[str] = None,
            sort_by: Optional[str] = None,
            page: Optional[str] = None
    ) -> Dict:
        """ `Account Get Rated TV Shows <https://developers.themoviedb.org/3/account/get-rated-tv-shows>`__

            Get a list of all the TV shows you have rated.

            Parameters:
                session_id (Optional[str]): Session ID.
                account_id (Optional[str]): Account ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                sort_by (Optional[str]): Sort the results. Allowed Values: ``created_at.asc`` and ``created_at.desc``
                page (Optional[int]): Specify which page to query.
        """
        return self._get(
            f"/account/{account_id if account_id else self.account_id}/rated/tv",
            session_id=session_id if session_id else self.session_id,
            language=language,
            sort_by=sort_by,
            page=page
        )

    def account_get_rated_tv_episodes(
            self,
            session_id: Optional[str] = None,
            account_id: Optional[str] = None,
            language: Optional[str] = None,
            sort_by: Optional[str] = None,
            page: Optional[str] = None
    ) -> Dict:
        """ `Account Get Rated TV Episodes <https://developers.themoviedb.org/3/account/get-rated-tv-episodes>`__

            Get a list of all the TV episodes you have rated.

            Parameters:
                session_id (Optional[str]): Session ID.
                account_id (Optional[str]): Account ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                sort_by (Optional[str]): Sort the results. Allowed Values: ``created_at.asc`` and ``created_at.desc``
                page (Optional[int]): Specify which page to query.
        """
        return self._get(
            f"/account/{account_id if account_id else self.account_id}/rated/tv/episodes",
            session_id=session_id if session_id else self.session_id,
            language=language,
            sort_by=sort_by,
            page=page
        )

    def account_get_movie_watchlist(
            self,
            session_id: Optional[str] = None,
            account_id: Optional[str] = None,
            language: Optional[str] = None,
            sort_by: Optional[str] = None,
            page: Optional[str] = None
    ) -> Dict:
        """ `Account Get Movie Watchlist <https://developers.themoviedb.org/3/account/get-movie-watchlist>`__

            Get a list of all the movies you have added to your watchlist.

            Parameters:
                session_id (Optional[str]): Session ID.
                account_id (Optional[str]): Account ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                sort_by (Optional[str]): Sort the results. Allowed Values: ``created_at.asc`` and ``created_at.desc``
                page (Optional[int]): Specify which page to query.
        """
        return self._get(
            f"/account/{account_id if account_id else self.account_id}/watchlist/movies",
            session_id=session_id if session_id else self.session_id,
            language=language,
            sort_by=sort_by,
            page=page
        )

    def account_get_tv_show_watchlist(
            self,
            session_id: Optional[str] = None,
            account_id: Optional[str] = None,
            language: Optional[str] = None,
            sort_by: Optional[str] = None,
            page: Optional[str] = None
    ) -> Dict:
        """ `Account Get TV Show Watchlist <https://developers.themoviedb.org/3/account/get-tv-show-watchlist>`__

            Get a list of all the TV shows you have added to your watchlist.

            Parameters:
                session_id (Optional[str]): Session ID.
                account_id (Optional[str]): Account ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                sort_by (Optional[str]): Sort the results. Allowed Values: ``created_at.asc`` and ``created_at.desc``
                page (Optional[int]): Specify which page to query.
        """
        return self._get(
            f"/account/{account_id if account_id else self.account_id}/watchlist/tv",
            session_id=session_id if session_id else self.session_id,
            language=language,
            sort_by=sort_by,
            page=page
        )

    def account_add_to_watchlist(
            self, media_type: str, media_id: int, watchlist: bool,
            session_id: Optional[str] = None,
            account_id: Optional[str] = None
    ) -> Dict:
        """ `Account Add to Watchlist <https://developers.themoviedb.org/3/account/add-to-watchlist>`__

            Add a movie or TV show to your watchlist.

            Parameters:
                session_id (Optional[str]): Session ID.
                account_id (Optional[str]): Account ID.
                media_type (str): Media Type. Allowed Values: ``movie`` and ``tv``
                media_id (int): Media ID.
                watchlist (bool): Add or remove from your Watchlist.
        """
        return self._post(
            f"/account/{account_id if account_id else self.account_id}/watchlist",
            json={
                "media_type": media_type,
                "media_id": media_id,
                "watchlist": watchlist
            },
            session_id=session_id if session_id else self.session_id
        )

    def authentication_create_guest_session(self) -> Dict:
        """ `Authentication Create Guest Session <https://developers.themoviedb.org/3/authentication/create-guest-session>`__

            This method will let you create a new guest session. Guest sessions are a type of session that will let a
            user rate movies and TV shows but not require them to have a TMDB user account. More information about user 
            authentication can be found 
            `here <https://developers.themoviedb.org/3/authentication/how-do-i-generate-a-session-id>`__.
            
            Please note, you should only generate a single guest session per user (or device) as you will be able to 
            attach the ratings to a TMDB user account in the future. There is also IP limits in place so you should 
            always make sure it's the end user doing the guest session actions.
            
            If a guest session is not used for the first time within 24 hours, it will be automatically deleted.
        """
        return self._get("/authentication/guest_session/new")

    def authentication_create_request_token(self) -> Dict:
        """ `Authentication Create Request Token <https://developers.themoviedb.org/3/authentication/create-request-token>`__

            Create a temporary request token that can be used to validate a TMDB user login. More details about how this
            works can be found
            `here <https://developers.themoviedb.org/3/authentication/how-do-i-generate-a-session-id>`__.
        """
        return self._get("/authentication/token/new")

    def authentication_create_session(self, request_token: str) -> Dict:
        """ `Authentication Create Session <https://developers.themoviedb.org/3/authentication/create-session>`__

            You can use this method to create a fully valid session ID once a user has validated the request token. More
            information about how this works can be found
            `here <https://developers.themoviedb.org/3/authentication/how-do-i-generate-a-session-id>`__.

            Parameters:
                request_token (str): Request Token.
        """
        response = self._post("/authentication/session/new", json={"request_token": request_token})
        self._session_id = response["session_id"]
        return response

    def authentication_create_session_with_login(self, username, password, request_token) -> Dict:
        """ `Authentication Create Session With Login <https://developers.themoviedb.org/3/authentication/validate-request-token>`__

            This method allows an application to validate a request token by entering a username and password.

            Not all applications have access to a web view so this can be used as a substitute.

            Please note, the preferred method of validating a request token is to have a user authenticate the request
            via the TMDB website. You can read about that method
            `here <https://developers.themoviedb.org/3/authentication/how-do-i-generate-a-session-id>`__.

            Parameters:
                username (str): TMDb Username.
                password (str): TMDb Password.
                request_token (str): Request Token.
        """
        return self._post(
            "/authentication/token/validate_with_login",
            json={
                "username": username,
                "password": password,
                "request_token": request_token
            }
        )

    def authentication_create_session_from_v4(self, access_token: str) -> Dict:
        """ `Authentication Create Session (from v4 access token) <https://developers.themoviedb.org/3/authentication/create-session-from-v4-access-token>`__

            Use this method to create a v3 session ID if you already have a valid v4 access token. The v4 token needs to
            be authenticated by the user. Your standard "read token" will not validate to create a session ID.

            Parameters:
                access_token (str): V4 Approved Access Token.
        """
        response = self._post("/authentication/session/convert/4", json={"access_token": access_token})
        self._session_id = response["session_id"]
        return response

    def authentication_delete_session(self, session_id: Optional[str] = None) -> Dict:
        """ `Authentication Delete Session <https://developers.themoviedb.org/3/authentication/delete-session>`__

            If you would like to delete (or "logout") from a session, call this method with a valid session ID.

            Parameters:
                session_id (Optional[str]): Session ID.
        """
        return self._delete("/authentication/session", json={"session_id": session_id if session_id else self.session_id})

    def certifications_get_movie_certifications(self) -> Dict:
        """ `Certifications Get Movie Certifications <https://developers.themoviedb.org/3/certifications/get-movie-certifications>`__

            Get an up to date list of the officially supported movie certifications on TMDB.
        """
        return self._get("/certification/movie/list")

    def certifications_get_tv_certifications(self) -> Dict:
        """ `Certifications Get TV Certifications <https://developers.themoviedb.org/3/certifications/get-tv-certifications>`__

            Get an up to date list of the officially supported TV show certifications on TMDB.
        """
        return self._get("/certification/tv/list")

    def changes_get_movie_change_list(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict:
        """ `Changes Get Movie Change List <https://developers.themoviedb.org/3/changes/get-movie-change-list>`__

            Get a list of all of the movie ids that have been changed in the past 24 hours.

            You can query it for up to 14 days worth of changed IDs at a time with the ``start_date`` and ``end_date``
            query parameters.

            Parameters:
                start_date (Optional[str]): Filter the results with a start date. Format: YYYY-MM-DD
                end_date (Optional[str]): Filter the results with an end date. Format: YYYY-MM-DD
        """
        return self._get("/movie/changes", start_date=start_date, end_date=end_date)

    def changes_get_tv_change_list(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict:
        """ `Changes Get TV Change List <https://developers.themoviedb.org/3/changes/get-tv-change-list>`__

            Get a list of all of the TV show ids that have been changed in the past 24 hours.

            You can query it for up to 14 days worth of changed IDs at a time with the ``start_date`` and ``end_date``
            query parameters.

            Parameters:
                start_date (Optional[str]): Filter the results with a start date. Format: YYYY-MM-DD
                end_date (Optional[str]): Filter the results with an end date. Format: YYYY-MM-DD
        """
        return self._get("/tv/changes", start_date=start_date, end_date=end_date)

    def changes_get_person_change_list(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict:
        """ `Changes Get Person Change List <https://developers.themoviedb.org/3/changes/get-person-change-list>`__

            Get a list of all of the person ids that have been changed in the past 24 hours.

            You can query it for up to 14 days worth of changed IDs at a time with the ``start_date`` and ``end_date``
            query parameters.

            Parameters:
                start_date (Optional[str]): Filter the results with a start date. Format: YYYY-MM-DD
                end_date (Optional[str]): Filter the results with an end date. Format: YYYY-MM-DD
        """
        return self._get("/person/changes", start_date=start_date, end_date=end_date)

    def collections_get_details(
            self, collection_id: int,
            language: Optional[str] = None,
            append_to_response: Optional[str] = None,
            include_image_language: Optional[str] = None
    ) -> Dict:
        """ `Collections Get Details <https://developers.themoviedb.org/3/collections/get-collection-details>`__

            Get collection details by id.

            Supports ``append_to_response``. Read more about this `here <https://developers.themoviedb.org/3/getting-started/append-to-response>`__.

            Parameters:
                collection_id (int): Collection ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                append_to_response (Optional[str]): Comma-separated list of sub requests within the same namespace.
                include_image_language (Optional[str]): Comma-separated list of ISO-639-1 values or null to query for additional image languages. (Used with  ``images`` append_to_response)
        """
        return self._get(
            f"/collection/{collection_id}",
            language=language,
            append_to_response=append_to_response,
            include_image_language=include_image_language
        )

    def collections_get_images(
            self, collection_id: int,
            language: Optional[str] = None,
            include_image_language: Optional[str] = None
    ) -> Dict:
        """ `Collections Get Images <https://developers.themoviedb.org/3/collections/get-collection-images>`__

            Get the images for a collection by id.

            Parameters:
                collection_id (int): Collection ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                include_image_language (Optional[str]): Comma-separated list of ISO-639-1 values or null to query for additional image languages.
        """
        return self._get(
            f"/collection/{collection_id}/images",
            language=language,
            include_image_language=include_image_language
        )

    def collections_get_translations(
            self, collection_id: int,
            language: Optional[str] = None
    ) -> Dict:
        """ `Collections Get Translations <https://developers.themoviedb.org/3/collections/get-collection-translations>`__

            Get the list translations for a collection by id.

            Parameters:
                collection_id (int): Collection ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
        """
        return self._get(f"/collection/{collection_id}/translations", language=language)

    def companies_get_details(
            self, company_id: int,
            language: Optional[str] = None,
            append_to_response: Optional[str] = None,
            page: Optional[int] = None
    ) -> Dict:
        """ `Companies Get Details <https://developers.themoviedb.org/3/companies/get-company-details>`__

            Get a companies details by id.

            Supports ``append_to_response``. Read more about this `here <https://developers.themoviedb.org/3/getting-started/append-to-response>`__.

            Parameters:
                company_id (int): Company ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                append_to_response (Optional[str]): Comma-separated list of sub requests within the same namespace.
                page (Optional[int]): Specify which page to query. (Used with  ``movies`` append_to_response)
        """
        return self._get(
            f"/company/{company_id}",
            language=language,
            append_to_response=append_to_response,
            page=page
        )

    def companies_get_alternative_names(self, company_id: int) -> Dict:
        """ `Companies Get Alternative Names <https://developers.themoviedb.org/3/companies/get-company-alternative-names>`__

            Get the alternative names of a company.

            Parameters:
                company_id (int): Company ID.
        """
        return self._get(f"/company/{company_id}/alternative_names")

    def companies_get_images(self, company_id: int) -> Dict:
        """ `Companies Get Images <https://developers.themoviedb.org/3/companies/get-company-images>`__

            Get a companies logos by id.

            There are two image formats that are supported for companies, PNG's and SVG's. You can see which type the
            original file is by looking at the ``file_type`` field. We prefer SVG's as they are resolution independent and
            as such, the width and height are only there to reflect the original asset that was uploaded. An SVG can be
            scaled properly beyond those dimensions if you call them as a PNG.

            For more information about how SVG's and PNG's can be used, take a read through
            `this document <https://developers.themoviedb.org/3/getting-started/images>`__.

            Parameters:
                company_id (int): Company ID.
        """
        return self._get(f"/company/{company_id}/images")

    def companies_get_movies(
            self, company_id: int,
            language: Optional[str] = None,
            page: Optional[int] = None
    ) -> Dict:
        """ Companies Get Movies

            Get a companies movies by id.

            Parameters:
                company_id (int): Company ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                page (Optional[int]): Specify which page to query.
        """
        return self._get(f"/company/{company_id}/movies", language=language, page=page)

    def configuration_get_api_configuration(self, append_to_response: Optional[str] = None) -> Dict:
        """ `Configuration Get API3 Configuration <https://developers.themoviedb.org/3/configuration/get-api-configuration>`__

            Get the system wide configuration information. Some elements of the API3 require some knowledge of this
            configuration data. The purpose of this is to try and keep the actual API3 responses as light as possible.
            It is recommended you cache this data within your application and check for updates every few days.

            This method currently holds the data relevant to building image URLs as well as the change key map.

            To build an image URL, you will need 3 pieces of data. The ``base_url``, ``size`` and ``file_path``. Simply
            combine them all and you will have a fully qualified URL. Here’s an example URL:

                .. code-block::

                    https://image.tmdb.org/t/p/w500/8uO0gUM8aNqYLs1OsTBQiXu0fEv.jpg

            The configuration method also contains the list of change keys which can be useful if you are building an
            app that consumes data from the change feed.

            Supports ``append_to_response``. Read more about this `here <https://developers.themoviedb.org/3/getting-started/append-to-response>`__.

            Parameters:
                append_to_response (Optional[str]): Comma-separated list of sub requests within the same namespace.
        """
        return self._get("/configuration", append_to_response=append_to_response)

    def configuration_get_countries(self) -> Dict:
        """ `Configuration Get Countries <https://developers.themoviedb.org/3/configuration/get-countries>`__

            Get the list of countries (ISO 3166-1 tags) used throughout TMDB.
        """
        return self._get("/configuration/countries")

    def configuration_get_jobs(self) -> Dict:
        """ `Configuration Get Jobs <https://developers.themoviedb.org/3/configuration/get-jobs>`__

            Get a list of the jobs and departments we use on TMDB.
        """
        return self._get("/configuration/jobs")

    def configuration_get_languages(self) -> Dict:
        """ `Configuration Get Languages <https://developers.themoviedb.org/3/configuration/get-languages>`__

            Get the list of languages (ISO 639-1 tags) used throughout TMDB.
        """
        return self._get("/configuration/languages")

    def configuration_get_primary_translations(self) -> Dict:
        """ `Configuration Get Primary Translations <https://developers.themoviedb.org/3/configuration/get-primary-translations>`__

            Get a list of the officially supported translations on TMDB.

            While it's technically possible to add a translation in any one of the
            `languages <https://developers.themoviedb.org/3/configuration/get-languages>`__ we have added to TMDB
            (we don't restrict content), the ones listed in this method are the ones we also support for localizing
            the website with which means they are what we refer to as the "primary" translations.

            These are all specified as `IETF tags <https://en.wikipedia.org/wiki/IETF_language_tag>`__ to identify the
            languages we use on TMDB. There is one exception which is image languages. They are currently only
            designated by a ISO-639-1 tag. This is a planned upgrade for the future.

            We're always open to adding more if you think one should be added. You can ask about getting a new primary
            translation added by posting on
            `the forums <https://www.themoviedb.org/talk/category/5047951f760ee3318900009a>`__.

            One more thing to mention, these are the translations that map to our website translation project. You can
            view and contribute to that project `here <https://www.localeapp.com/projects/8267>`__
        """
        return self._get("/configuration/primary_translations")

    def configuration_get_timezones(self) -> Dict:
        """ `Configuration Get Timezones <https://developers.themoviedb.org/3/configuration/get-timezones>`__

            Get the list of timezones used throughout TMDB.
        """
        return self._get("/configuration/timezones")

    def credits_get_details(self, credit_id: str) -> Dict:
        """ `Credits Get Details <https://developers.themoviedb.org/3/credits/get-credit-details>`__

            Get a movie or TV credit details by id.

            Parameters:
                credit_id (int): Credit ID.
        """
        return self._get(f"/credit/{credit_id}")

    def discover_movie_discover(self, **kwargs) -> Dict:
        """ `Discover Movie Discover <https://developers.themoviedb.org/3/discover/movie-discover>`__

            Discover movies by different types of data like average rating, number of votes, genres and certifications.
            You can get a valid list of certifications from the
            `certifications list <https://developers.themoviedb.org/3/certifications/get-movie-certifications>`__
            method.

            Discover also supports a nice list of sort options. See below for all of the available options.

            Please note, when using ``certification`` \\ ``certification.lte`` you must also specify
            ``certification_country``. These two parameters work together in order to filter the results. You can only
            filter results with the countries we have added to our
            `certifications list <https://developers.themoviedb.org/3/certifications/get-movie-certifications>`__.

            If you specify the ``region`` parameter, the regional release date will be used instead of the primary
            release date. The date returned will be the first date based on your query (ie. if a ``with_release_type``
            is specified). It's important to note the order of the release types that are used. Specifying "2|3" would
            return the limited theatrical release date as opposed to "3|2" which would return the theatrical date.

            Also note that a number of filters support being comma (``,``) or pipe (``|``) separated. Comma's are
            treated like an ``AND`` and query while pipe's are an ``OR``.

            Some examples of what can be done with discover can be found
            `here <https://www.themoviedb.org/documentation/api/discover>`__.

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
                with_runtime.lte (Optional[int]): Filter and only include movies that have a runtime that is less than or equal to a value.
                with_original_language (Optional[str]): Specify an ISO 639-1 string to filter results by their original language value.
                with_watch_providers (Optional[str]): A comma or pipe separated list of watch provider ID's. Combine this filter with ``watch_region`` in order to filter your results by a specific watch provider in a specific region.
                watch_region (Optional[str]): An ISO 3166-1 code. Combine this filter with ``with_watch_providers`` in order to filter your results by a specific watch provider in a specific region.
                with_watch_monetization_types (Optional[str]): In combination with ``watch_region``, you can filter by monetization type. Allowed Values: ``flatrate``, ``free``, ``ads``, ``rent``, ``buy``
        """
        return self._get("/discover/movie", **kwargs)

    def discover_tv_discover(self, **kwargs) -> Dict:
        """ `Discover TV Discover <https://developers.themoviedb.org/3/discover/tv-discover>`__

            Discover TV shows by different types of data like average rating, number of votes, genres, the network they
            aired on and air dates.

            Discover also supports a nice list of sort options. See below for all of the available options.

            Also note that a number of filters support being comma (``,``) or pipe (``|``) separated. Comma's are
            treated like an ``AND`` and query while pipe's are an ``OR``.

            Some examples of what can be done with discover can be found
            `here <https://www.themoviedb.org/documentation/api/discover>`__.

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
        """
        return self._get("/discover/tv", **kwargs)

    def find_find_by_id(
            self,
            external_id: Union[int, str],
            external_source: str,
            language: Optional[str] = None
    ) -> Dict:
        """ `FindResults FindResults by ID <https://developers.themoviedb.org/3/find/find-by-id>`__

            The find method makes it easy to search for objects in our database by an external id.

            This method will search all objects (movies, TV shows and people) and return the results in a single response.

            The supported external sources for each object are as follows.

            .. list-table:: Media Databases
               :header-rows: 1

               * -
                 - Movies
                 - TV Shows
                 - TV Seasons
                 - TV Episodes
                 - People
               * - IMDb ID
                 - ✓
                 - ✓
                 - ✗
                 - ✓
                 - ✓
               * - TVDB ID
                 - ✗
                 - ✓
                 - ✓
                 - ✓
                 - ✗
               * - Freebase MID*
                 - ✗
                 - ✓
                 - ✓
                 - ✓
                 - ✓
               * - Freebase ID*
                 - ✗
                 - ✓
                 - ✓
                 - ✓
                 - ✓
               * - TVRage ID*
                 - ✗
                 - ✓
                 - ✓
                 - ✓
                 - ✓

            .. list-table:: Social IDs
               :header-rows: 1

               * -
                 - Movies
                 - TV Shows
                 - TV Seasons
                 - TV Episodes
                 - People
               * - Facebook
                 - ✓
                 - ✓
                 - ✗
                 - ✗
                 - ✓
               * - Instagram
                 - ✓
                 - ✓
                 - ✗
                 - ✗
                 - ✓
               * - Twitter
                 - ✓
                 - ✓
                 - ✗
                 - ✗
                 - ✓

            \\* Defunct or no longer available as a service.

            Parameters:
                external_id (Union[int, str]): External ID.
                external_source (str): External Source. Allowed Values: ``imdb_id``, ``freebase_mid``, ``freebase_id``, ``tvdb_id``, ``tvrage_id``, ``facebook_id``, ``twitter_id``, ``instagram_id``
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
        """
        return self._get(
            f"/find/{external_id}",
            external_source=external_source,
            language=language
        )

    def genres_get_movie_list(self, language: Optional[str] = None) -> Dict:
        """ `Genres Get Movie List <https://developers.themoviedb.org/3/genres/get-movie-list>`__

            Get the list of official genres for movies.

            Parameters:
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
        """
        return self._get("/genre/movie/list", language=language)

    def genres_get_tv_list(self, language: Optional[str] = None) -> Dict:
        """ `Genres Get TV List <https://developers.themoviedb.org/3/genres/get-tv-list>`__

            Get the list of official genres for TV shows.

            Parameters:
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
        """
        return self._get("/genre/tv/list", language=language)

    def guest_sessions_get_rated_movies(
            self, guest_session_id: str,
            language: Optional[str] = None,
            sort_by: Optional[str] = None,
            page: Optional[str] = None
    ) -> Dict:
        """ `Guest Sessions Get Rated Movies <https://developers.themoviedb.org/3/guest-sessions/get-guest-session-rated-movies>`__

            Get the rated movies for a guest session.

            Parameters:
                guest_session_id (str): Guest Session ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                sort_by (Optional[str]): Sort the results. Allowed Values: ``created_at.asc`` and ``created_at.desc``
                page (Optional[int]): Specify which page to query.
        """
        return self._get(
            f"/guest_session/{guest_session_id}/rated/movies",
            language=language,
            sort_by=sort_by,
            page=page
        )

    def guest_sessions_get_rated_tv_shows(
            self, guest_session_id: str,
            language: Optional[str] = None,
            sort_by: Optional[str] = None,
            page: Optional[str] = None
    ) -> Dict:
        """ `Guest Sessions Get Rated TV Shows <https://developers.themoviedb.org/3/guest-sessions/get-guest-session-rated-tv-shows>`__

            Get the rated TV shows for a guest session.

            Parameters:
                guest_session_id (str): Guest Session ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                sort_by (Optional[str]): Sort the results. Allowed Values: ``created_at.asc`` and ``created_at.desc``
                page (Optional[int]): Specify which page to query.
        """
        return self._get(
            f"/guest_session/{guest_session_id}/rated/tv",
            language=language,
            sort_by=sort_by,
            page=page
        )

    def guest_sessions_get_rated_tv_episodes(
            self, guest_session_id: str,
            language: Optional[str] = None,
            sort_by: Optional[str] = None,
            page: Optional[str] = None
    ) -> Dict:
        """ `Guest Sessions Get Rated TV Episodes <https://developers.themoviedb.org/3/guest-sessions/get-gest-session-rated-tv-episodes>`__

            Get the rated TV episodes for a guest session.

            Parameters:
                guest_session_id (str): Guest Session ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                sort_by (Optional[str]): Sort the results. Allowed Values: ``created_at.asc`` and ``created_at.desc``
                page (Optional[int]): Specify which page to query.
        """
        return self._get(
            f"/guest_session/{guest_session_id}/rated/tv/episodes",
            language=language,
            sort_by=sort_by,
            page=page
        )

    def keywords_get_details(
            self, keyword_id: int,
            language: Optional[str] = None,
            append_to_response: Optional[str] = None,
            include_adult: Optional[bool] = None
    ) -> Dict:
        """ `Keywords Get Details <https://developers.themoviedb.org/3/collections/get-collection-details>`__

            Get keyword details by id.

            Supports ``append_to_response``. Read more about this `here <https://developers.themoviedb.org/3/getting-started/append-to-response>`__.

            Parameters:
                keyword_id (int): Keyword ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                append_to_response (Optional[str]): Comma-separated list of sub requests within the same namespace.
                include_adult (Optional[bool]): Choose whether to include adult (pornography) content in the results. (Used with  ``movies`` append_to_response)
        """
        return self._get(
            f"/keyword/{keyword_id}",
            append_to_response=append_to_response,
            language=language,
            include_adult=include_adult
        )

    def keywords_get_movies(
            self, keyword_id: int,
            language: Optional[str] = None,
            include_adult: Optional[bool] = None
    ) -> Dict:
        """ `Keywords Get Movies <https://developers.themoviedb.org/3/keywords/get-movies-by-keyword>`__

            Get the movies that belong to a keyword.

            Parameters:
                keyword_id (int): Keyword ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                include_adult (Optional[bool]): Choose whether to include adult (pornography) content in the results.
        """
        return self._get(f"/keyword/{keyword_id}/movies", language=language, include_adult=include_adult)

    def lists_get_details(self, list_id: int, language: Optional[str] = None) -> Dict:
        """ `Lists Get Details <https://developers.themoviedb.org/3/lists/get-list-details>`__

            Get the details of a list.

            Parameters:
                list_id (int): List ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
        """
        return self._get(f"/list/{list_id}", language=language)

    def lists_check_item_status(self, list_id: int, movie_id: int) -> Dict:
        """ `Lists Check Item Status <https://developers.themoviedb.org/3/lists/check-item-status>`__

            You can use this method to check if a movie has already been added to the list.

            Parameters:
                list_id (int): List ID.
                movie_id (int): Movie ID to check list for.
        """
        return self._get(f"/list/{list_id}/item_status", movie_id=movie_id)

    def lists_create_list(
            self,
            session_id: Optional[str] = None,
            name: Optional[str] = "",
            description: Optional[str] = "",
            language: Optional[str] = ""
    ) -> Dict:
        """ `Lists Create List <https://developers.themoviedb.org/3/lists/create-list>`__

            Create a list.

            Parameters:
                session_id (Optional[str]): Session ID.
                name (Optional[str]): List Name.
                description (Optional[str]): List Description.
                language (Optional[str]): Set the ISO-639-1 variant for your list.
        """
        return self._post(
            "/list",
            json={
                "name": name,
                "description": description,
                "language": language
            },
            session_id=session_id if session_id else self.session_id
        )

    def lists_add_movie(
            self, list_id: int, movie_id: int,
            session_id: Optional[str] = None
    ) -> Dict:
        """ `Lists Add Movie <https://developers.themoviedb.org/3/lists/add-movie>`__

            Add a movie to a list.

            Parameters:
                list_id (int): List ID.
                movie_id (int): Movie ID to check list for.
                session_id (Optional[str]): Session ID.
        """
        return self._post(
            f"/list/{list_id}/add_item",
            json={"media_id": movie_id},
            session_id=session_id if session_id else self.session_id
        )

    def lists_remove_movie(self, list_id: int, movie_id: int, session_id: Optional[str] = None) -> Dict:
        """ `Lists Remove Movie <https://developers.themoviedb.org/3/lists/remove-movie>`__

            Remove a movie from a list.

            Parameters:
                list_id (int): List ID.
                movie_id (int): Movie ID to check list for.
                session_id (Optional[str]): Session ID.
        """
        return self._post(
            f"/list/{list_id}/remove_item",
            json={"media_id": movie_id},
            session_id=session_id if session_id else self.session_id
        )

    def lists_clear_list(self, list_id: int, confirm: bool, session_id: Optional[str] = None) -> Dict:
        """ `Lists Clear List <https://developers.themoviedb.org/3/lists/clear-list>`__

            Clear all of the items from a list.

            Parameters:
                list_id (int): List ID.
                confirm (bool): Confirm you want to clear the list.
                session_id (Optional[str]): Session ID.
        """
        return self._post(
            f"/list/{list_id}/clear",
            session_id=session_id if session_id else self.session_id,
            confirm=confirm
        )

    def lists_delete_list(self, list_id: int, session_id: Optional[str] = None) -> Dict:
        """ `Lists Delete List <https://developers.themoviedb.org/3/lists/delete-list>`__

            Delete a list.

            Parameters:
                list_id (int): List ID.
                session_id (Optional[str]): Session ID.
        """
        return self._delete(f"/list/{list_id}", session_id=session_id if session_id else self.session_id)

    def movies_get_details(
            self, movie_id: int,
            language: Optional[str] = None,
            append_to_response: Optional[str] = None,
            session_id: Optional[str] = None,
            guest_session_id: Optional[str] = None,
            country: Optional[str] = None,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            include_image_language: Optional[str] = None,
            include_video_language: Optional[str] = None,
            page: Optional[int] = None
    ) -> Dict:
        """ `Movies Get Details <https://developers.themoviedb.org/3/movies/get-movie-details>`__

            Get the primary information about a movie.

            Supports ``append_to_response``. Read more about this `here <https://developers.themoviedb.org/3/getting-started/append-to-response>`__.

            Parameters:
                movie_id (int): Movie ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                append_to_response (Optional[str]): Comma-separated list of sub requests within the same namespace.
                session_id (Optional[str]): Session ID. (Used with  ``account_states`` append_to_response)
                guest_session_id (Optional[str]): Guest Session ID. (Used with  ``account_states`` append_to_response)
                country (Optional[str]): ISO-3166-1 value to display alternative titles. (Used with  ``alternative_titles`` append_to_response)
                start_date (Optional[str]): Filter the results with a start date. Format: YYYY-MM-DD (Used with  ``changes`` append_to_response)
                end_date (Optional[str]): Filter the results with an end date. Format: YYYY-MM-DD (Used with  ``changes`` append_to_response)
                include_image_language (Optional[str]): Comma-separated list of ISO-639-1 values or null to query for additional image languages. (Used with  ``images`` append_to_response)
                include_video_language (Optional[str]): Comma-separated list of ISO-639-1 values or null to query for additional video languages. (Used with  ``videos`` append_to_response)
                page (Optional[int]): Specify which page to query. (Used with  ``lists`` append_to_response)
        """
        return self._get(
            f"/movie/{movie_id}",
            language=language,
            append_to_response=append_to_response,
            session_id=session_id if session_id else self._session_id,
            guest_session_id=guest_session_id,
            country=country,
            start_date=start_date,
            end_date=end_date,
            include_image_language=include_image_language,
            include_video_language=include_video_language,
            page=page
        )

    def movies_get_account_states(
            self, movie_id: int,
            session_id: Optional[str] = None,
            guest_session_id: Optional[str] = None
    ) -> Dict:
        """ `Movies Get Account States <https://developers.themoviedb.org/3/movies/get-movie-account-states>`__

            Grab the following account states for a session:

            * Movie rating
            * If it belongs to your watchlist
            * If it belongs to your favourite list

            Parameters:
                movie_id (int): Movie ID.
                session_id (Optional[str]): Session ID.
                guest_session_id (Optional[str]): Guest Session ID.
        """
        return self._get(
            f"/movie/{movie_id}/account_states",
            session_id=session_id if session_id else self.session_id,
            guest_session_id=guest_session_id
        )

    def movies_get_alternative_titles(self, movie_id: int, country: Optional[str] = None) -> Dict:
        """ `Movies Get Alternative Titles <https://developers.themoviedb.org/3/movies/get-movie-alternative-titles>`__

            Get all of the alternative titles for a movie.

            Parameters:
                movie_id (int): Movie ID.
                country (Optional[str]): Session ID.
        """
        return self._get(f"/movie/{movie_id}/alternative_titles", country=country)

    def movies_get_changes(
            self, movie_id: int,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            page: Optional[int] = None
    ) -> Dict:
        """ `Movies Get Changes <https://developers.themoviedb.org/3/movies/get-movie-changes>`__

            Get the changes for a movie. By default only the last 24 hours are returned.

            You can query up to 14 days in a single query by using the ``start_date`` and ``end_date`` query parameters.

            Parameters:
                movie_id (int): Movie ID.
                start_date (Optional[str]): Filter the results with a start date. Format: YYYY-MM-DD
                end_date (Optional[str]): Filter the results with an end date. Format: YYYY-MM-DD
                page (Optional[int]): Specify which page to query.
        """
        return self._get(f"/movie/{movie_id}/changes", start_date=start_date, end_date=end_date, page=page)

    def movies_get_credits(self, movie_id: int, language: Optional[str] = None) -> Dict:
        """ `Movies Get Credits <https://developers.themoviedb.org/3/movies/get-movie-credits>`__

            Get the cast and crew for a movie.

            Parameters:
                movie_id (int): Movie ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
        """
        return self._get(f"/movie/{movie_id}/credits", language=language)

    def movies_get_external_ids(self, movie_id: int) -> Dict:
        """ `Movies Get External IDs <https://developers.themoviedb.org/3/movies/get-movie-external-ids>`__

            Get the external ids for a movie. We currently support the following external sources.

            .. list-table::
               :header-rows: 1

               * - Media Databases
                 - Social IDs
               * - IMDb ID
                 - Facebook
               * -
                 - Instagram
               * -
                 - Twitter

            Parameters:
                movie_id (int): Movie ID.
        """
        return self._get(f"/movie/{movie_id}/external_ids")

    def movies_get_images(
            self, movie_id: int,
            language: Optional[str] = None,
            include_image_language: Optional[str] = None
    ) -> Dict:
        """ `Movies Get Images <https://developers.themoviedb.org/3/movies/get-movie-images>`__

            Get the images that belong to a movie.

            Querying images with a ``language`` parameter will filter the results. If you want to include a fallback
            language (especially useful for backdrops) you can use the ``include_image_language`` parameter. This should be
            a comma separated value like so: ``include_image_language=en,null``.

            Parameters:
                movie_id (int): Movie ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                include_image_language (Optional[str]): Comma-separated list of ISO-639-1 values or null to query for additional image languages.
        """
        return self._get(
            f"/movie/{movie_id}/images",
            language=language,
            include_image_language=include_image_language
        )

    def movies_get_keywords(self, movie_id: int) -> Dict:
        """ `Movies Get Keywords <https://developers.themoviedb.org/3/movies/get-movie-keywords>`__

            Get the keywords that have been added to a movie.

            Parameters:
                movie_id (int): Movie ID.
        """
        return self._get(f"/movie/{movie_id}/keywords")

    def movies_get_lists(self, movie_id: int, language: Optional[str] = None, page: Optional[int] = None) -> Dict:
        """ `Movies Get Lists <https://developers.themoviedb.org/3/movies/get-movie-lists>`__

            Get a list of lists that this movie belongs to.

            Parameters:
                movie_id (int): Movie ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                page (Optional[int]): Specify which page to query.
        """
        return self._get(f"/movie/{movie_id}/lists", language=language, page=page)

    def movies_get_recommendations(self, movie_id: int, language: Optional[str] = None, page: Optional[int] = None) -> Dict:
        """ `Movies Get Recommendations <https://developers.themoviedb.org/3/movies/get-movie-recommendations>`__

            Get a list of recommended movies for a movie.

            Parameters:
                movie_id (int): Movie ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                page (Optional[int]): Specify which page to query.
        """
        return self._get(f"/movie/{movie_id}/recommendations", language=language, page=page)

    def movies_get_release_dates(self, movie_id: int) -> Dict:
        """ `Movies Get Release Dates <https://developers.themoviedb.org/3/movies/get-movie-release-dates>`__

            Get the release date along with the certification for a movie.

            Release dates support different types:

                1. Premiere
                2. Theatrical (limited)
                3. Theatrical
                4. Digital
                5. Physical
                6. TV

            Parameters:
                movie_id (int): Movie ID.
        """
        return self._get(f"/movie/{movie_id}/release_dates")

    def movies_get_reviews(self, movie_id: int, language: Optional[str] = None, page: Optional[int] = None) -> Dict:
        """ `Movies Get Reviews <https://developers.themoviedb.org/3/movies/get-movie-reviews>`__

            Get the user reviews for a movie.

            Parameters:
                movie_id (int): Movie ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                page (Optional[int]): Specify which page to query.
        """
        return self._get(f"/movie/{movie_id}/reviews", language=language, page=page)

    def movies_get_similar_movies(self, movie_id: int, language: Optional[str] = None, page: Optional[int] = None) -> Dict:
        """ `Movies Get Similar Movies <https://developers.themoviedb.org/3/movies/get-similar-movies>`__

            Get a list of similar movies. This is not the same as the "Recommendation" system you see on the website.

            These items are assembled by looking at keywords and genres.

            Parameters:
                movie_id (int): Movie ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                page (Optional[int]): Specify which page to query.
        """
        return self._get(f"/movie/{movie_id}/similar", language=language, page=page)

    def movies_get_translations(self, movie_id: int) -> Dict:
        """ `Movies Get Translations <https://developers.themoviedb.org/3/movies/get-movie-translations>`__

            Get a list of translations that have been created for a movie.

            Parameters:
                movie_id (int): Movie ID.
        """
        return self._get(f"/movie/{movie_id}/translations")

    def movies_get_videos(
            self, movie_id: int,
            language: Optional[str] = None,
            include_video_language: Optional[str] = None
    ) -> Dict:
        """ `Movies Get Videos <https://developers.themoviedb.org/3/movies/get-movie-videos>`__

            Get the videos that have been added to a movie.

            Querying videos with a ``language`` parameter will filter the results. If you want to include a fallback
            language you can use the ``include_video_language`` parameter. This should be a comma separated value like so:
            ``include_video_language=en,null``.

            Parameters:
                movie_id (int): Movie ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                include_video_language (Optional[str]): Comma-separated list of ISO-639-1 values or null to query for additional video languages.
        """
        return self._get(
            f"/movie/{movie_id}/videos",
            language=language,
            include_video_language=include_video_language
        )

    def movies_get_watch_providers(self, movie_id: int) -> Dict:
        """ `Movies Get Watch Providers <https://developers.themoviedb.org/3/movies/get-movie-watch-providers>`__

            Powered by our partnership with JustWatch, you can query this method to get a list of the availabilities per country by provider.

            This is not going to return full deep links, but rather, it's just enough information to display what's available where.

            You can link to the provided TMDB URL to help support TMDB and provide the actual deep links to the content.

            Please note: In order to use this data you must attribute the source of the data as JustWatch. If we find any usage not complying with these terms we will revoke access to the API.

            Parameters:
                movie_id (int): Movie ID.
        """
        return self._get(f"/movie/{movie_id}/watch/providers")

    def movies_rate_movie(
            self, movie_id: int, value: float,
            session_id: Optional[str] = None,
            guest_session_id: Optional[str] = None
    ) -> Dict:
        """ `Movies Rate Movie <https://developers.themoviedb.org/3/movies/rate-movie>`__

            Rate a movie.

            Parameters:
                movie_id (int): Movie ID.
                value (float): Rating for the Movie.
                session_id (Optional[str]): Session ID.
                guest_session_id (Optional[str]): Guest Session ID.
        """
        return self._post(
            f"/movie/{movie_id}/rating",
            json={"value": value},
            session_id=session_id if session_id else self.session_id,
            guest_session_id=guest_session_id
        )

    def movies_delete_rating(
            self, movie_id: int,
            session_id: Optional[str] = None,
            guest_session_id: Optional[str] = None
    ) -> Dict:
        """ `Movies Delete Rating <https://developers.themoviedb.org/3/movies/delete-movie-rating>`__

            Remove your rating for a movie.

            Parameters:
                movie_id (int): Movie ID.
                session_id (Optional[str]): Session ID.
                guest_session_id (Optional[str]): Guest Session ID.
        """
        return self._delete(
            f"/movie/{movie_id}/rating",
            session_id=session_id if session_id else self.session_id,
            guest_session_id=guest_session_id
        )

    def movies_get_latest(self, language: Optional[str] = None) -> Dict:
        """ `Movies Get Latest <https://developers.themoviedb.org/3/movies/get-latest-movie>`__

            Get the most newly created movie. This is a live response and will continuously change.

            Parameters:
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
        """
        return self._get("/movie/latest", language=language)

    def movies_get_now_playing(self, language: Optional[str] = None, page: Optional[str] = None, region: Optional[str] = None) -> Dict:
        """ `Movies Get Now Playing <https://developers.themoviedb.org/3/movies/get-now-playing>`__

            Get a list of movies in theatres. This is a release type query that looks for all movies that have a release type of 2 or 3 within the specified date range.

            You can optionally specify a ``region`` parameter which will narrow the search to only look for theatrical release dates within the specified country.

            Parameters:
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                page (Optional[int]): Specify which page to query.
                region (Optional[str]): ISO-3166-1 value to filter the search to only look for now playing dates within the specified country.
        """
        return self._get("/movie/now_playing", language=language, page=page, region=region)

    def movies_get_popular(self, language: Optional[str] = None, page: Optional[str] = None, region: Optional[str] = None) -> Dict:
        """ `Movies Get Popular <https://developers.themoviedb.org/3/movies/get-popular-movies>`__

            Get a list of the current popular movies on TMDB. This list updates daily.

            Parameters:
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                page (Optional[int]): Specify which page to query.
                region (Optional[str]): ISO-3166-1 value to filter the search to only look for popular release dates within the specified country.
        """
        return self._get("/movie/popular", language=language, page=page, region=region)

    def movies_get_top_rated(self, language: Optional[str] = None, page: Optional[str] = None, region: Optional[str] = None) -> Dict:
        """ `Movies Get Top Rated <https://developers.themoviedb.org/3/movies/get-top-rated-movies>`__

            Get the top rated movies on TMDB.

            Parameters:
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                page (Optional[int]): Specify which page to query.
                region (Optional[str]): ISO-3166-1 value to filter the search to only look for top rated release dates within the specified country.
        """
        return self._get("/movie/top_rated", language=language, page=page, region=region)

    def movies_get_upcoming(self, language: Optional[str] = None, page: Optional[str] = None, region: Optional[str] = None) -> Dict:
        """ `Movies Get Upcoming <https://developers.themoviedb.org/3/movies/get-upcoming>`__

            Get a list of upcoming movies in theatres. This is a release type query that looks for all movies that have a release type of 2 or 3 within the specified date range.

            You can optionally specify a ``region`` parameter which will narrow the search to only look for theatrical release dates within the specified country.

            Parameters:
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                page (Optional[int]): Specify which page to query.
                region (Optional[str]): ISO-3166-1 value to filter the search to only look for upcoming release dates within the specified country.
        """
        return self._get("/movie/upcoming", language=language, page=page, region=region)

    def networks_get_details(self, network_id: int, append_to_response: Optional[str] = None) -> Dict:
        """ `Networks Get Details <https://developers.themoviedb.org/3/movies/get-network-details>`__

            Get the details of a network.

            Supports ``append_to_response``. Read more about this `here <https://developers.themoviedb.org/3/getting-started/append-to-response>`__.

            Parameters:
                network_id (int): Network ID.
                append_to_response (Optional[str]): Comma-separated list of sub requests within the same namespace.
        """
        return self._get(f"/network/{network_id}", append_to_response=append_to_response)

    def networks_get_alternative_names(self, network_id: int) -> Dict:
        """ `Networks Get Alternative Names <https://developers.themoviedb.org/3/networks/get-network-alternative-names>`__

            Get the alternative names of a network.

            Parameters:
                network_id (int): Network ID.
        """
        return self._get(f"/network/{network_id}/alternative_names")

    def networks_get_images(self, network_id: int) -> Dict:
        """ `Networks Get Images <https://developers.themoviedb.org/3/networks/get-network-images>`__

            Get the TV network logos by id.

            There are two image formats that are supported for networks, PNG's and SVG's. You can see which type the
            original file is by looking at the ``file_type`` field. We prefer SVG's as they are resolution independent and
            as such, the width and height are only there to reflect the original asset that was uploaded. An SVG can be
            scaled properly beyond those dimensions if you call them as a PNG.

            For more information about how SVG's and PNG's can be used, take a read through
            `this document <https://developers.themoviedb.org/3/getting-started/images>`__.

            Parameters:
                network_id (int): Network ID.
        """
        return self._get(f"/network/{network_id}/images")

    def trending_get_trending(self, media_type: str, time_window: str, page: Optional[str] = None) -> Dict:
        """ `Trending Get Trending <https://developers.themoviedb.org/3/trending/get-trending>`__

            Get the daily or weekly trending items. The daily trending list tracks items over the period of a day while
            items have a 24 hour half life. The weekly list tracks items over a 7 day period, with a 7 day half life.

            .. list-table:: Valid Media Types
               :header-rows: 1

               * - Media Type
                 - Description
               * - all
                 - Include all movies, TV shows and people in the results as a global trending list.
               * - movie
                 - Show the trending movies in the results.
               * - tv
                 - Show the trending TV shows in the results.
               * - person
                 - Show the trending people in the results.

            .. list-table:: Valid Time Windows
               :header-rows: 1

               * - Time Window
                 - Description
               * - day
                 - View the trending list for the day.
               * - week
                 - View the trending list for the week.

            Parameters:
                media_type (str): Trending media type. Allowed Values: ``all``, ``movie``, ``tv``, and ``person``
                time_window (str): Trending list time window. Allowed Values: ``day`` and ``week``
                page (Optional[int]): Specify which page to query.
        """
        return self._get(f"/trending/{media_type}/{time_window}", page=page)

    def people_get_details(
            self,
            person_id: int,
            language: Optional[str] = None,
            append_to_response: Optional[str] = None,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            page: Optional[int] = None
    ) -> Dict:
        """ `People Get Details <https://developers.themoviedb.org/3/people/get-person-details>`__

            Get the primary person details by id.

            Supports ``append_to_response``. Read more about this `here <https://developers.themoviedb.org/3/getting-started/append-to-response>`__.

            Parameters:
                person_id (int): Person ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                append_to_response (Optional[str]): Comma-separated list of sub requests within the same namespace.
                start_date (Optional[str]): Filter the results with a start date. Format: YYYY-MM-DD (Used with  ``changes`` append_to_response)
                end_date (Optional[str]): Filter the results with an end date. Format: YYYY-MM-DD (Used with  ``changes`` append_to_response)
                page (Optional[int]): Specify which page to query. (Used with  ``changes`` append_to_response)
        """
        return self._get(
            f"/person/{person_id}",
            language=language,
            append_to_response=append_to_response,
            start_date=start_date,
            end_date=end_date,
            page=page
        )

    def people_get_changes(
            self,
            person_id: int,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            page: Optional[int] = None
    ) -> Dict:
        """ `People Get Changes <https://developers.themoviedb.org/3/people/get-person-changes>`__

            Get the changes for a person. By default only the last 24 hours are returned.

            You can query up to 14 days in a single query by using the ``start_date`` and ``end_date`` query parameters.

            Parameters:
                person_id (int): Person ID.
                start_date (Optional[str]): Filter the results with a start date. Format: YYYY-MM-DD
                end_date (Optional[str]): Filter the results with an end date. Format: YYYY-MM-DD
                page (Optional[int]): Specify which page to query.
        """
        return self._get(f"/person/{person_id}/changes", start_date=start_date, end_date=end_date, page=page)

    def people_get_movie_credits(self, person_id: int, language: Optional[str] = None) -> Dict:
        """ `People Get Movie Credits <https://developers.themoviedb.org/3/people/get-person-movie-credits>`__

            Get the movie credits for a person.

            Parameters:
                person_id (int): Person ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
        """
        return self._get(f"/person/{person_id}/movie_credits", language=language)

    def people_get_tv_credits(self, person_id: int, language: Optional[str] = None) -> Dict:
        """ `People Get TV  Credits <https://developers.themoviedb.org/3/people/get-person-tv-credits>`__

            Get the TV show credits for a person.

            Parameters:
                person_id (int): Person ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
        """
        return self._get(f"/person/{person_id}/tv_credits", language=language)

    def people_get_combined_credits(self, person_id: int, language: Optional[str] = None) -> Dict:
        """ `People Get Combined Credits <https://developers.themoviedb.org/3/people/get-person-combined-credits>`__

            Get the movie and TV credits together in a single response.

            Parameters:
                person_id (int): Person ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
        """
        return self._get(f"/person/{person_id}/combined_credits", language=language)

    def people_get_external_ids(self, person_id: int, language: Optional[str] = None) -> Dict:
        """ `People Get External IDs <https://developers.themoviedb.org/3/people/get-person-external-ids>`__

            Get the external ids for a person. We currently support the following external sources.

            .. list-table::
               :header-rows: 1

               * - External Sources
               * - IMDb ID
               * - Facebook
               * - Freebase MID*
               * - Freebase ID*
               * - Instagram
               * - TVRage ID*
               * - Twitter

            \\* Defunct or no longer available as a service.

            Parameters:
                person_id (int): Person ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
        """
        return self._get(f"/person/{person_id}/external_ids", language=language)

    def people_get_images(self, person_id: int) -> Dict:
        """ `People Get Images <https://developers.themoviedb.org/3/movies/get-person-images>`__

            Get the images for a person.

            Parameters:
                person_id (int): Person ID.
        """
        return self._get(f"/person/{person_id}/images")

    def people_get_tagged_images(self, person_id: int, language: Optional[str] = None, page: Optional[int] = None) -> Dict:
        """ `People Get Tagged Images <https://developers.themoviedb.org/3/people/get-tagged-images>`__

            Get the images that this person has been tagged in.

            Parameters:
                person_id (int): Person ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                page (Optional[int]): Specify which page to query.
        """
        return self._get(f"/person/{person_id}/tagged_images", language=language, page=page)

    def people_get_translations(self, person_id: int, language: Optional[str] = None) -> Dict:
        """ `People Get Movie Credits <https://developers.themoviedb.org/3/movies/get-person-movie-credits>`__

            Get a list of translations that have been created for a person.

            Parameters:
                person_id (int): Person ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
        """
        return self._get(f"/person/{person_id}/translations", language=language)

    def people_get_latest(self, language: Optional[str] = None) -> Dict:
        """ `People Get Latest <https://developers.themoviedb.org/3/people/get-latest-person>`__

            Get the most newly created person. This is a live response and will continuously change.

            Parameters:
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
        """
        return self._get(f"/person/latest", language=language)

    def people_get_popular(self, language: Optional[str] = None, page: Optional[str] = None) -> Dict:
        """ `People Get Popular <https://developers.themoviedb.org/3/people/get-popular-people>`__

            Get the list of popular people on TMDB. This list updates daily.

            Parameters:
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                page (Optional[int]): Specify which page to query.
        """
        return self._get(f"/person/popular", language=language, page=page)

    def reviews_get_details(self, review_id: str) -> Dict:
        """ `Reviews Get Details <https://developers.themoviedb.org/3/reviews/get-review-details>`__

            Retrieve the details of a movie or TV show review.

            Parameters:
                review_id (str): Review ID.
        """
        return self._get(f"/review/{review_id}")

    def search_search_companies(self, query: str, page: Optional[int] = None) -> Dict:
        """ `Search Search Companies <https://developers.themoviedb.org/3/search/search-companies>`__

            Search for companies.

            Parameters:
                query (str): Pass a text query to search. This value should be URI encoded.
                page (Optional[int]): Specify which page to query.
        """
        return self._get("/search/company", query=query, page=page)

    def search_search_collections(self, query: str, language: Optional[str] = None, page: Optional[int] = None) -> Dict:
        """ `Search Search Collections <https://developers.themoviedb.org/3/search/search-collections>`__

            Search for collections.

            Parameters:
                query (str): Pass a text query to search. This value should be URI encoded.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                page (Optional[int]): Specify which page to query.
        """
        return self._get("/search/collection", query=query, language=language, page=page)

    def search_search_keywords(self, query: str, page: Optional[int] = None) -> Dict:
        """ `Search Search Keywords <https://developers.themoviedb.org/3/search/search-keywords>`__

            Search for keywords.

            Parameters:
                query (str): Pass a text query to search. This value should be URI encoded.
                page (Optional[int]): Specify which page to query.
        """
        return self._get("/search/keyword", query=query, page=page)

    def search_search_movies(
            self, 
            query: str, 
            language: Optional[str] = None, 
            page: Optional[int] = None,
            include_adult: Optional[bool] = None, 
            region: Optional[str] = None,
            year: Optional[int] = None, 
            primary_release_year: Optional[int] = None
    ) -> Dict:
        """ `Search Search Movies <https://developers.themoviedb.org/3/search/search-movies>`__

            Search for movies.

            Parameters:
                query (str): Pass a text query to search. This value should be URI encoded.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                page (Optional[int]): Specify which page to query.
                include_adult (Optional[bool]): Choose whether to include adult (pornography) content in the results.
                region (Optional[str]): Specify a ISO 3166-1 code to filter release dates. Must be uppercase.
                year (Optional[int]): Specify a year for the search.
                primary_release_year (Optional[int]): Specify a primary release year for the search.
        """
        return self._get(
            "/search/movie",
            query=query,
            language=language,
            page=page,
            include_adult=include_adult,
            region=region,
            year=year,
            primary_release_year=primary_release_year
        )

    def search_multi_search(
            self, 
            query: str, 
            language: Optional[str] = None, 
            page: Optional[int] = None,
            include_adult: Optional[bool] = None, 
            region: Optional[str] = None
    ) -> Dict:
        """ `Search Multi Search <https://developers.themoviedb.org/3/search/multi-search>`__

            Search multiple models in a single request. Multi search currently supports searching for movies, tv shows and people in a single request.

            Parameters:
                query (str): Pass a text query to search. This value should be URI encoded.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                page (Optional[int]): Specify which page to query.
                include_adult (Optional[bool]): Choose whether to include adult (pornography) content in the results.
                region (Optional[str]): Specify a ISO 3166-1 code to filter release dates. Must be uppercase.
        """
        return self._get(
            "/search/multi",
            query=query,
            language=language,
            page=page,
            include_adult=include_adult,
            region=region
        )

    def search_search_people(
            self, 
            query: str, 
            language: Optional[str] = None, 
            page: Optional[int] = None,
            include_adult: Optional[bool] = None, 
            region: Optional[str] = None
    ) -> Dict:
        """ `Search Search People <https://developers.themoviedb.org/3/search/search-people>`__

            Search for people.

            Parameters:
                query (str): Pass a text query to search. This value should be URI encoded.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                page (Optional[int]): Specify which page to query.
                include_adult (Optional[bool]): Choose whether to include adult (pornography) content in the results.
                region (Optional[str]): Specify a ISO 3166-1 code to filter release dates. Must be uppercase.
        """
        return self._get(
            "/search/person",
            query=query,
            language=language,
            page=page,
            include_adult=include_adult,
            region=region
        )

    def search_search_tv_shows(
            self, 
            query: str, 
            language: Optional[str] = None, 
            page: Optional[int] = None,
            include_adult: Optional[bool] = None, 
            first_air_date_year: Optional[int] = None
    ) -> Dict:
        """ `Search Search TV Shows <https://developers.themoviedb.org/3/search/search-tv-shows>`__

            Search for TV show.

            Parameters:
                query (str): Pass a text query to search. This value should be URI encoded.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                page (Optional[int]): Specify which page to query.
                include_adult (Optional[bool]): Choose whether to include adult (pornography) content in the results.
                first_air_date_year (Optional[int]): Specify a first air date year for the search.
        """
        return self._get(
            "/search/tv",
            query=query,
            language=language,
            page=page,
            include_adult=include_adult,
            first_air_date_year=first_air_date_year
        )

    def tv_get_details(
            self, tv_id: int,
            language: Optional[str] = None, 
            append_to_response: Optional[str] = None, 
            session_id: Optional[str] = None,
            guest_session_id: Optional[str] = None, 
            start_date: Optional[str] = None, 
            end_date: Optional[str] = None,
            include_image_language: Optional[str] = None, 
            include_video_language: Optional[str] = None, 
            page: Optional[int] = None
    ) -> Dict:
        """ `TV Get Details <https://developers.themoviedb.org/3/tv/get-tv-details>`__

            Get the primary TV show details by id.

            Supports ``append_to_response``. Read more about this `here <https://developers.themoviedb.org/3/getting-started/append-to-response>`__.

            Parameters:
                tv_id (int): TV show ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                append_to_response (Optional[str]): Comma-separated list of sub requests within the same namespace.
                session_id (Optional[str]): Session ID. (Used with  ``account_states`` append_to_response)
                guest_session_id (Optional[str]): Guest Session ID. (Used with  ``account_states`` append_to_response)
                start_date (Optional[str]): Filter the results with a start date. Format: YYYY-MM-DD (Used with  ``changes`` append_to_response)
                end_date (Optional[str]): Filter the results with an end date. Format: YYYY-MM-DD (Used with  ``changes`` append_to_response)
                include_image_language (Optional[str]): Comma-separated list of ISO-639-1 values or null to query for additional image languages. (Used with  ``images`` append_to_response)
                include_video_language (Optional[str]): Comma-separated list of ISO-639-1 values or null to query for additional video languages. (Used with  ``videos`` append_to_response)
                page (Optional[int]): Specify which page to query. (Used with  ``lists`` append_to_response)
        """
        return self._get(
            f"/tv/{tv_id}",
            language=language,
            append_to_response=append_to_response,
            session_id=session_id if session_id else self._session_id,
            guest_session_id=guest_session_id,
            start_date=start_date,
            end_date=end_date,
            include_image_language=include_image_language,
            include_video_language=include_video_language,
            page=page
        )

    def tv_get_account_states(
            self, tv_id: int,
            language: Optional[str] = None,
            session_id: Optional[str] = None,
            guest_session_id: Optional[str] = None
    ) -> Dict:
        """ `TV Get Account States <https://developers.themoviedb.org/3/tv/get-tv-account-states>`__

            Grab the following account states for a session:

            * TV rating
            * If it belongs to your watchlist
            * If it belongs to your favourite list

            Parameters:
                tv_id (int): TV ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                session_id (Optional[str]): Session ID.
                guest_session_id (Optional[str]): Guest Session ID.
        """
        return self._get(
            f"/tv/{tv_id}/account_states",
            language=language,
            session_id=session_id if session_id else self.session_id,
            guest_session_id=guest_session_id
        )

    def tv_get_aggregate_credits(self, tv_id: int, language: Optional[str] = None) -> Dict:
        """ `TV Get Aggregate Credits <https://developers.themoviedb.org/3/tv/get-tv-aggregate-credits>`__

            Get the aggregate credits (cast and crew) that have been added to a TV show.

            This call differs from the main ``credits`` call in that it does not return the newest season but rather, is a view of all the entire cast & crew for all episodes belonging to a TV show.

            Parameters:
                tv_id (int): TV ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
        """
        return self._get(f"/tv/{tv_id}/aggregate_credits", language=language)

    def tv_get_alternative_titles(self, tv_id: int) -> Dict:
        """ `TV Get Alternative Titles <https://developers.themoviedb.org/3/tv/get-tv-alternative-titles>`__

            Returns all of the alternative titles for a TV show.

            Parameters:
                tv_id (int): TV ID.
        """
        return self._get(f"/tv/{tv_id}/alternative_titles")

    def tv_get_changes(
            self, tv_id: int,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            page: Optional[int] = None
    ) -> Dict:
        """ `TV Get Changes <https://developers.themoviedb.org/3/tv/get-tv-changes>`__

            Get the changes for a TV show. By default only the last 24 hours are returned.

            You can query up to 14 days in a single query by using the ``start_date`` and ``end_date`` query parameters.

            TV show changes are different than movie changes in that there are some edits on seasons and episodes that
            will create a change entry at the show level. These can be found under the season and episode keys. These
            keys will contain a ``series_id`` and ``episode_id``. You can use the :meth:`tv_seasons_get_changes`
            and :meth:`tv_episodes_get_changes` methods to look these up individually.

            Parameters:
                tv_id (int): TV ID.
                start_date (Optional[str]): Filter the results with a start date. Format: YYYY-MM-DD
                end_date (Optional[str]): Filter the results with an end date. Format: YYYY-MM-DD
                page (Optional[int]): Specify which page to query.
        """
        return self._get(f"/tv/{tv_id}/changes", start_date=start_date, end_date=end_date, page=page)

    def tv_get_content_ratings(self, tv_id: int, language: Optional[str] = None) -> Dict:
        """ `TV Get Content Ratings <https://developers.themoviedb.org/3/tv/get-tv-content-ratings>`__

            Get the list of content ratings (certifications) that have been added to a TV show.

            Parameters:
                tv_id (int): TV ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
        """
        return self._get(f"/tv/{tv_id}/content_ratings", language=language)

    def tv_get_credits(self, tv_id: int, language: Optional[str] = None) -> Dict:
        """ `TV Get Credits <https://developers.themoviedb.org/3/tv/get-tv-credits>`__

            Get the credits (cast and crew) that have been added to a TV show.

            Parameters:
                tv_id (int): TV ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
        """
        return self._get(f"/tv/{tv_id}/credits", language=language)

    def tv_get_episode_groups(self, tv_id: int, language: Optional[str] = None) -> Dict:
        """ `TV Get Episode Groups <https://developers.themoviedb.org/3/tv/get-tv-episode-groups>`__

            Get all of the episode groups that have been created for a TV show. With a group ID you can call the :meth:`tv_episode_groups_get_details` method.

            Parameters:
                tv_id (int): TV ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
        """
        return self._get(f"/tv/{tv_id}/episode_groups", language=language)

    def tv_get_external_ids(self, tv_id: int) -> Dict:
        """ `TV Get External IDs <https://developers.themoviedb.org/3/tv/get-tv-external-ids>`__

            Get the external ids for a TV show. We currently support the following external sources.

            .. list-table::
               :header-rows: 1

               * - Media Databases
                 - Social IDs
               * - IMDb ID
                 - Facebook
               * - TVDB ID
                 - Instagram
               * - Freebase MID*
                 - Twitter
               * - Freebase ID*
                 -
               * - TVRage ID*
                 -

            \\* Defunct or no longer available as a service.

            Parameters:
                tv_id (int): TV ID.
        """
        return self._get(f"/tv/{tv_id}/external_ids")

    def tv_get_images(
            self, tv_id: int,
            language: Optional[str] = None,
            include_image_language: Optional[str] = None
    ) -> Dict:
        """ `TV Get Images <https://developers.themoviedb.org/3/tv/get-tv-images>`__

            Get the images that belong to a TV show.

            Querying images with a ``language`` parameter will filter the results. If you want to include a fallback
            language (especially useful for backdrops) you can use the ``include_image_language`` parameter. This should be
            a comma separated value like so: ``include_image_language=en,null``.

            Parameters:
                tv_id (int): TV ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                include_image_language (Optional[str]): Comma-separated list of ISO-639-1 values or null to query for additional image languages.
        """
        return self._get(f"/tv/{tv_id}/images", language=language, include_image_language=include_image_language)

    def tv_get_keywords(self, tv_id: int) -> Dict:
        """ `TV Get Keywords <https://developers.themoviedb.org/3/tv/get-tv-keywords>`__

            Get the keywords that have been added to a TV show.

            Parameters:
                tv_id (int): TV ID.
        """
        return self._get(f"/tv/{tv_id}/keywords")

    def tv_get_recommendations(self, tv_id: int, language: Optional[str] = None, page: Optional[int] = None) -> Dict:
        """ `TV Get Recommendations <https://developers.themoviedb.org/3/tv/get-tv-recommendations>`__

            Get the list of TV show recommendations for this item.

            Parameters:
                tv_id (int): TV ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                page (Optional[int]): Specify which page to query.
        """
        return self._get(f"/tv/{tv_id}/recommendations", language=language, page=page)

    def tv_get_reviews(self, tv_id: int, language: Optional[str] = None, page: Optional[int] = None) -> Dict:
        """ `TV Get Reviews <https://developers.themoviedb.org/3/tv/get-tv-reviews>`__

            Get the reviews for a TV show.

            Parameters:
                tv_id (int): TV ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                page (Optional[int]): Specify which page to query.
        """
        return self._get(f"/tv/{tv_id}/reviews", language=language, page=page)

    def tv_get_screened_theatrically(self, tv_id: int) -> Dict:
        """ `TV Get Screened Theatrically <https://developers.themoviedb.org/3/tv/get-tv-screened-theatrically>`__

            Get a list of seasons or episodes that have been screened in a film festival or theatre.

            Parameters:
                tv_id (int): TV ID.
        """
        return self._get(f"/tv/{tv_id}/screened_theatrically")

    def tv_get_similar_tv_shows(self, tv_id: int, language: Optional[str] = None, page: Optional[int] = None) -> Dict:
        """ `TV Get Similar TV Shows <https://developers.themoviedb.org/3/tv/get-similar-tv-shows>`__

            Get a list of similar TV shows. These items are assembled by looking at keywords and genres.

            Parameters:
                tv_id (int): TV ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                page (Optional[int]): Specify which page to query.
        """
        return self._get(f"/tv/{tv_id}/similar", language=language, page=page)

    def tv_get_translations(self, tv_id: int) -> Dict:
        """ `TV Get Translations <https://developers.themoviedb.org/3/tv/get-tv-translations>`__

            Get a list of the translations that exist for a TV show.

            Parameters:
                tv_id (int): TV ID.
        """
        return self._get(f"/tv/{tv_id}/translations")

    def tv_get_videos(
            self, tv_id: int,
            language: Optional[str] = None,
            include_video_language: Optional[str] = None
    ) -> Dict:
        """ `TV Get Similar TV Shows <https://developers.themoviedb.org/3/tv/get-similar-tv-shows>`__

            Get the videos that have been added to a TV show.

            Querying videos with a ``language`` parameter will filter the results. If you want to include a fallback
            language you can use the ``include_video_language`` parameter. This should be a comma separated value like so:
            ``include_video_language=en,null``.

            Parameters:
                tv_id (int): TV ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                include_video_language (Optional[str]): Comma-separated list of ISO-639-1 values or null to query for additional video languages.
        """
        return self._get(f"/tv/{tv_id}/videos", language=language, include_video_language=include_video_language)

    def tv_get_watch_providers(self, tv_id: int) -> Dict:
        """ `TV Get Watch Providers <https://developers.themoviedb.org/3/tv/get-tv-watch-providers>`__

            Powered by our partnership with JustWatch, you can query this method to get a list of the availabilities per country by provider.

            This is not going to return full deep links, but rather, it's just enough information to display what's available where.

            You can link to the provided TMDB URL to help support TMDB and provide the actual deep links to the content.

            Please note: In order to use this data you must attribute the source of the data as JustWatch. If we find any usage not complying with these terms we will revoke access to the API.

            Parameters:
                tv_id (int): TV ID.
        """
        return self._get(f"/tv/{tv_id}/watch/providers")

    def tv_rate_tv_show(
            self, tv_id: int, value: float,
            session_id: Optional[str] = None,
            guest_session_id: Optional[str] = None
    ) -> Dict:
        """ `TV Rate TV Show <https://developers.themoviedb.org/3/tv/rate-tv-show>`__

            Rate a TV show.

            Parameters:
                tv_id (int): TV ID.
                value (float): Rating for the TV show.
                session_id (Optional[str]): Session ID.
                guest_session_id (Optional[str]): Guest Session ID.
        """
        return self._post(
            f"/tv/{tv_id}/rating",
            json={"value": value},
            session_id=session_id if session_id else self.session_id,
            guest_session_id=guest_session_id
        )

    def tv_delete_rating(
            self, tv_id: int,
            session_id: Optional[str] = None,
            guest_session_id: Optional[str] = None
    ) -> Dict:
        """ `TV Delete Rating <https://developers.themoviedb.org/3/tv/delete-tv-show-rating>`__

            Remove your rating for a TV show.

            Parameters:
                tv_id (int): TV ID.
                session_id (Optional[str]): Session ID.
                guest_session_id (Optional[str]): Guest Session ID.
        """
        return self._delete(
            f"/tv/{tv_id}/rating",
            session_id=session_id if session_id else self.session_id,
            guest_session_id=guest_session_id
        )

    def tv_get_latest(self, language: Optional[str] = None) -> Dict:
        """ `TV Get Latest <https://developers.themoviedb.org/3/tv/get-latest-tv>`__

            Get the most newly created TV show. This is a live response and will continuously change.

            Parameters:
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
        """
        return self._get("/tv/latest", language=language)

    def tv_get_tv_airing_today(self, language: Optional[str] = None, page: Optional[int] = None) -> Dict:
        """ `TV Get TV Airing Today <https://developers.themoviedb.org/3/tv/get-tv-airing-today>`__

            Get a list of TV shows that are airing today. This query is purely day based as we do not currently support airing times. (Eastern Time UTC-05:00)

            Parameters:
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                page (Optional[int]): Specify which page to query.
        """
        return self._get("/tv/airing_today", language=language, page=page)

    def tv_get_tv_on_the_air(self, language: Optional[str] = None, page: Optional[int] = None) -> Dict:
        """ `TV Get TV On The Air <https://developers.themoviedb.org/3/tv/get-tv-on-the-air>`__

            Get a list of shows that are currently on the air.

            This query looks for any TV show that has an episode with an air date in the next 7 days.

            Parameters:
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                page (Optional[int]): Specify which page to query.
        """
        return self._get("/tv/on_the_air", language=language, page=page)

    def tv_get_popular(self, language: Optional[str] = None, page: Optional[int] = None) -> Dict:
        """ `TV Get Popular <https://developers.themoviedb.org/3/tv/get-popular-tv-shows>`__

            Get a list of the current popular TV shows on TMDB. This list updates daily.

            Parameters:
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                page (Optional[int]): Specify which page to query.
        """
        return self._get("/tv/popular", language=language, page=page)

    def tv_get_top_rated(self, language: Optional[str] = None, page: Optional[int] = None) -> Dict:
        """ `TV Get Top Rated <https://developers.themoviedb.org/3/tv/get-top-rated-tv>`__

            Get a list of the top rated TV shows on TMDB.

            Parameters:
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                page (Optional[int]): Specify which page to query.
        """
        return self._get("/tv/top_rated", language=language, page=page)

    def tv_seasons_get_details(
            self, tv_id: int, season_number: int,
            language: Optional[str] = None,
            append_to_response: Optional[str] = None,
            session_id: Optional[str] = None,
            guest_session_id: Optional[str] = None,
            include_image_language: Optional[str] = None,
            include_video_language: Optional[str] = None
    ) -> Dict:
        """ `TV Seasons Get Details <https://developers.themoviedb.org/3/tv-seasons/get-tv-season-details>`__

            Get the TV season details by id.`

            Supports ``append_to_response``. Read more about this `here <https://developers.themoviedb.org/3/getting-started/append-to-response>`__.

            Parameters:
                tv_id (int): TV show ID.
                season_number (int): Season Number of TV show.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                append_to_response (Optional[str]): Comma-separated list of sub requests within the same namespace.
                session_id (Optional[str]): Session ID. (Used with  ``account_states`` append_to_response)
                guest_session_id (Optional[str]): Guest Session ID. (Used with  ``account_states`` append_to_response)
                include_image_language (Optional[str]): Comma-separated list of ISO-639-1 values or null to query for additional image languages. (Used with  ``images`` append_to_response)
                include_video_language (Optional[str]): Comma-separated list of ISO-639-1 values or null to query for additional video languages. (Used with  ``videos`` append_to_response)
        """
        return self._get(
            f"/tv/{tv_id}/season/{season_number}",
            language=language,
            append_to_response=append_to_response,
            session_id=session_id if session_id else self._session_id,
            guest_session_id=guest_session_id,
            include_image_language=include_image_language,
            include_video_language=include_video_language
        )

    def tv_seasons_get_account_states(
            self, tv_id: int, season_number: int,
            language: Optional[str] = None,
            session_id: Optional[str] = None,
            guest_session_id: Optional[str] = None
    ) -> Dict:
        """ `TV Seasons Get Account States <https://developers.themoviedb.org/3/tv-seasons/get-tv-season-account-states>`__

            Returns all of the user ratings for the season's episodes.

            Parameters:
                tv_id (int): TV show ID.
                season_number (int): Season Number of TV show.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                session_id (Optional[str]): Session ID.
                guest_session_id (Optional[str]): Guest Session ID.
        """
        return self._get(
            f"/tv/{tv_id}/season/{season_number}/account_states",
            language=language,
            session_id=session_id if session_id else self.session_id,
            guest_session_id=guest_session_id
        )

    def tv_seasons_get_aggregate_credits(self, tv_id: int, season_number: int, language: Optional[str] = None) -> Dict:
        """ `TV Seasons Get Aggregate Credits <https://developers.themoviedb.org/3/tv-seasons/get-tv-season-aggregate-credits>`__

            Get the aggregate credits for TV season.

            This call differs from the main ``credits`` call in that it does not only return the season credits, but rather is a view of all the cast & crew for all of the episodes belonging to a season.

            Parameters:
                tv_id (int): TV show ID.
                season_number (int): Season Number of TV show.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
        """
        return self._get(f"/tv/{tv_id}/season/{season_number}/aggregate_credits", language=language)

    def tv_seasons_get_changes(
            self, season_id: int,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            page: Optional[int] = None
    ) -> Dict:
        """ `TV Seasons Get Changes <https://developers.themoviedb.org/3/tv-seasons/get-tv-season-changes>`__

            Get the changes for a TV season. By default only the last 24 hours are returned.

            You can query up to 14 days in a single query by using the ``start_date`` and ``end_date`` query parameters.

            Parameters:
                season_id (int): Season ID.
                start_date (Optional[str]): Filter the results with a start date. Format: YYYY-MM-DD
                end_date (Optional[str]): Filter the results with an end date. Format: YYYY-MM-DD
                page (Optional[int]): Specify which page to query.
        """
        return self._get(
            f"/tv/season/{season_id}/changes",
            start_date=start_date,
            end_date=end_date,
            page=page
        )

    def tv_seasons_get_credits(self, tv_id: int, season_number: int, language: Optional[str] = None) -> Dict:
        """ `TV Seasons Get Credits <https://developers.themoviedb.org/3/tv-seasons/get-tv-season-credits>`__

            Get the credits for TV season.

            Parameters:
                tv_id (int): TV show ID.
                season_number (int): Season Number of TV show.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
        """
        return self._get(f"/tv/{tv_id}/season/{season_number}/credits", language=language)

    def tv_seasons_get_external_ids(self, tv_id: int, season_number: int) -> Dict:
        """ `TV Seasons Get Credits <https://developers.themoviedb.org/3/tv-seasons/get-tv-season-credits>`__

            Get the external ids for a TV season. We currently support the following external sources.

            .. list-table::
               :header-rows: 1

               * - Media Databases
               * - TVDB ID
               * - Freebase MID*
               * - Freebase ID*
               * - TVRage ID*

            \\* Defunct or no longer available as a service.

            Parameters:
                tv_id (int): TV show ID.
                season_number (int): Season Number of TV show.
        """
        return self._get(f"/tv/{tv_id}/season/{season_number}/external_ids")

    def tv_seasons_get_images(
            self, tv_id: int, season_number: int,
            language: Optional[str] = None,
            include_image_language: Optional[str] = None
    ) -> Dict:
        """ `TV Seasons Get Images <https://developers.themoviedb.org/3/tv-seasons/get-tv-season-images>`__

            Get the images that belong to a TV season.

            Querying images with a ``language`` parameter will filter the results. If you want to include a fallback
            language (especially useful for backdrops) you can use the ``include_image_language`` parameter. This should be
            a comma separated value like so: ``include_image_language=en,null``.

            Parameters:
                tv_id (int): TV ID.
                season_number (int): Season Number of TV show.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                include_image_language (Optional[str]): Comma-separated list of ISO-639-1 values or null to query for additional image languages.
        """
        return self._get(
            f"/tv/{tv_id}/season/{season_number}/images",
            language=language,
            include_image_language=include_image_language
        )

    def tv_seasons_get_translations(self, tv_id: int, season_number: int) -> Dict:
        """ `TV Seasons Get Translations <https://developers.themoviedb.org/3/tv-seasons/get-tv-season-translations>`__

            Get the translation data for a TV season.

            Parameters:
                tv_id (int): TV ID.
                season_number (int): Season Number of TV show.
        """
        return self._get(f"/tv/{tv_id}/season/{season_number}/translations")

    def tv_seasons_get_videos(
            self, tv_id: int, season_number,
            language: Optional[str] = None,
            include_video_language: Optional[str] = None
    ) -> Dict:
        """ `TV Seasons Get Videos <https://developers.themoviedb.org/3/tv-seasons/get-tv-season-videos>`__

            Get the videos that have been added to a TV season.

            Querying videos with a ``language`` parameter will filter the results. If you want to include a fallback
            language you can use the ``include_video_language`` parameter. This should be a comma separated value like so:
            ``include_video_language=en,null``.

            Parameters:
                tv_id (int): TV ID.
                season_number (int): Season Number of TV show.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                include_video_language (Optional[str]): Comma-separated list of ISO-639-1 values or null to query for additional video languages.
        """
        return self._get(
            f"/tv/{tv_id}/season/{season_number}/videos",
            language=language,
            include_video_language=include_video_language
        )

    def tv_episodes_get_details(
            self, tv_id: int, season_number: int, episode_number: int,
            language: Optional[str] = None,
            append_to_response: Optional[str] = None,
            session_id: Optional[str] = None,
            guest_session_id: Optional[str] = None,
            include_image_language: Optional[str] = None,
            include_video_language: Optional[str] = None
    ) -> Dict:
        """ `TV Episodes Get Details <https://developers.themoviedb.org/3/tv-episodes/get-tv-episode-details>`__

            Get the TV episode details by id.

            Supports ``append_to_response``. Read more about this `here <https://developers.themoviedb.org/3/getting-started/append-to-response>`__.

            Parameters:
                tv_id (int): TV show ID.
                season_number (int): Season Number of TV show.
                episode_number (int): Episode Number of the Season in the TV show.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                append_to_response (Optional[str]): Comma-separated list of sub requests within the same namespace.
                session_id (Optional[str]): Session ID. (Used with  ``account_states`` append_to_response)
                guest_session_id (Optional[str]): Guest Session ID. (Used with  ``account_states`` append_to_response)
                include_image_language (Optional[str]): Comma-separated list of ISO-639-1 values or null to query for additional image languages. (Used with  ``images`` append_to_response)
                include_video_language (Optional[str]): Comma-separated list of ISO-639-1 values or null to query for additional video languages. (Used with  ``videos`` append_to_response)
        """
        return self._get(
            f"/tv/{tv_id}/season/{season_number}/episode/{episode_number}",
            language=language,
            append_to_response=append_to_response,
            session_id=session_id if session_id else self._session_id,
            guest_session_id=guest_session_id,
            include_image_language=include_image_language,
            include_video_language=include_video_language
        )

    def tv_episodes_get_account_states(
            self, tv_id: int, season_number: int, episode_number: int,
            session_id: Optional[str] = None,
            guest_session_id: Optional[str] = None
    ) -> Dict:
        """ `TV Episodes Get Account States <https://developers.themoviedb.org/3/tv-episodes/get-tv-episode-account-states>`__

            Get your rating for a episode.

            Parameters:
                tv_id (int): TV show ID.
                season_number (int): Season Number of TV show.
                episode_number (int): Episode Number of the Season in the TV show.
                session_id (Optional[str]): Session ID.
                guest_session_id (Optional[str]): Guest Session ID.
        """
        return self._get(
            f"/tv/{tv_id}/season/{season_number}/episode/{episode_number}/account_states",
            session_id=session_id if session_id else self.session_id,
            guest_session_id=guest_session_id
        )

    def tv_episodes_get_changes(
            self, episode_id,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            page: Optional[int] = None
    ) -> Dict:
        """ `TV Episodes Get Changes <https://developers.themoviedb.org/3/tv-episodes/get-tv-episode-details>`__

            Get the changes for a TV episode. By default only the last 24 hours are returned.

            You can query up to 14 days in a single query by using the ``start_date`` and ``end_date`` query parameters.

            Parameters:
                episode_id (int): Episode ID.
                start_date (Optional[str]): Filter the results with a start date. Format: YYYY-MM-DD
                end_date (Optional[str]): Filter the results with an end date. Format: YYYY-MM-DD
                page (Optional[int]): Specify which page to query.
        """
        return self._get(
            f"/tv/episode/{episode_id}/changes",
            start_date=start_date,
            end_date=end_date,
            page=page
        )

    def tv_episodes_get_credits(
            self, tv_id: int, season_number: int, episode_number: int,
            language: Optional[str] = None
    ) -> Dict:
        """ `TV Episodes Get Credits <https://developers.themoviedb.org/3/tv-episodes/get-tv-episode-credits>`__

            Get the credits (cast, crew and guest stars) for a TV episode.

            Parameters:
                tv_id (int): TV show ID.
                season_number (int): Season Number of TV show.
                episode_number (int): Episode Number of the Season in the TV show.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
        """
        return self._get(f"/tv/{tv_id}/season/{season_number}/episode/{episode_number}/credits", language=language)

    def tv_episodes_get_external_ids(self, tv_id: int, season_number: int, episode_number: int) -> Dict:
        """ `TV Episodes Get External IDs <https://developers.themoviedb.org/3/tv-episodes/get-tv-episode-external-ids>`__

            Get the external ids for a TV episode. We currently support the following external sources.

            .. list-table::
               :header-rows: 1

               * - External Sources
               * - IMDb ID
               * - TVDB ID
               * - Freebase MID*
               * - Freebase ID*
               * - TVRage ID*

            \\* Defunct or no longer available as a service.

            Parameters:
                tv_id (int): TV show ID.
                season_number (int): Season Number of TV show.
                episode_number (int): Episode Number of the Season in the TV show.
        """
        return self._get(f"/tv/{tv_id}/season/{season_number}/episode/{episode_number}/external_ids")

    def tv_episodes_get_images(
            self, tv_id: int, season_number: int, episode_number: int,
            language: Optional[str] = None,
            include_image_language: Optional[str] = None
    ) -> Dict:
        """ `TV Episodes Get Images <https://developers.themoviedb.org/3/tv-episodes/get-tv-episode-images>`__

            Get the images that belong to a TV episode.

            Querying images with a ``language`` parameter will filter the results. If you want to include a fallback
            language (especially useful for backdrops) you can use the ``include_image_language`` parameter. This should be
            a comma separated value like so: ``include_image_language=en,null``.

            Parameters:
                tv_id (int): TV show ID.
                season_number (int): Season Number of TV show.
                episode_number (int): Episode Number of the Season in the TV show.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                include_image_language (Optional[str]): Comma-separated list of ISO-639-1 values or null to query for additional image languages.
        """
        return self._get(
            f"/tv/{tv_id}/season/{season_number}/episode/{episode_number}/images",
            language=language,
            include_image_language=include_image_language
        )

    def tv_episodes_get_translations(self, tv_id: int, season_number: int, episode_number: int) -> Dict:
        """ `TV Episodes Get Translations <https://developers.themoviedb.org/3/tv-episodes/get-tv-episode-translations>`__

            Get the translation data for an episode.

            Parameters:
                tv_id (int): TV show ID.
                season_number (int): Season Number of TV show.
                episode_number (int): Episode Number of the Season in the TV show.
        """
        return self._get(f"/tv/{tv_id}/season/{season_number}/episode/{episode_number}/translations")

    def tv_episodes_rate_tv_episode(
            self, tv_id: int, season_number: int, episode_number: int, value: float,
            session_id: Optional[str] = None,
            guest_session_id: Optional[str] = None
    ) -> Dict:
        """ `TV Episodes Rate TV Episode <https://developers.themoviedb.org/3/tv-episodes/rate-tv-episode>`__

            Rate a TV episode.

            Parameters:
                tv_id (int): TV show ID.
                season_number (int): Season Number of TV show.
                episode_number (int): Episode Number of the Season in the TV show.
                value (float): Rating for the TV show.
                session_id (Optional[str]): Session ID.
                guest_session_id (Optional[str]): Guest Session ID.
        """
        return self._post(
            f"/tv/{tv_id}/season/{season_number}/episode/{episode_number}/rating",
            json={"value": value},
            session_id=session_id if session_id else self.session_id,
            guest_session_id=guest_session_id
        )

    def tv_episodes_delete_rating(
            self, tv_id: int, season_number: int, episode_number: int,
            session_id: Optional[str] = None,
            guest_session_id: Optional[str] = None
    ) -> Dict:
        """ `TV Episodes Delete Rating <https://developers.themoviedb.org/3/tv-episodes/delete-tv-episode-rating>`__

            Remove your rating for a TV episode.

            Parameters:
                tv_id (int): TV show ID.
                season_number (int): Season Number of TV show.
                episode_number (int): Episode Number of the Season in the TV show.
                session_id (Optional[str]): Session ID.
                guest_session_id (Optional[str]): Guest Session ID.
        """
        return self._delete(
            f"/tv/{tv_id}/season/{season_number}/episode/{episode_number}/rating",
            session_id=session_id if session_id else self.session_id,
            guest_session_id=guest_session_id
        )

    def tv_episodes_get_videos(
            self, tv_id: int, season_number: int, episode_number: int,
            language: Optional[str] = None,
            include_video_language: Optional[str] = None
    ) -> Dict:
        """ `TV Episodes Get Videos <https://developers.themoviedb.org/3/tv-episodes/get-tv-episode-videos>`__

            Get the videos that have been added to a TV episode.

            Querying videos with a ``language`` parameter will filter the results. If you want to include a fallback
            language you can use the ``include_video_language`` parameter. This should be a comma separated value like so:
            ``include_video_language=en,null``.

            Parameters:
                tv_id (int): TV show ID.
                season_number (int): Season Number of TV show.
                episode_number (int): Episode Number of the Season in the TV show.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                include_video_language (Optional[str]): Comma-separated list of ISO-639-1 values or null to query for additional video languages. (Used with  ``videos`` append_to_response)
        """
        return self._get(
            f"/tv/{tv_id}/season/{season_number}/episode/{episode_number}/videos",
            language=language,
            include_video_language=include_video_language
        )

    def tv_episode_groups_get_details(self, episode_group_id: str, language: Optional[str] = None) -> Dict:
        """ `TV Episode Groups Get Details <https://developers.themoviedb.org/3/tv-episode-groups/get-tv-episode-group-details>`__

            Get the details of a TV episode group. Groups support 7 different types which are enumerated as the following:

                1. Original air date
                2. Absolute
                3. DVD
                4. Digital
                5. Story arc
                6. Production
                7. TV

            Parameters:
                episode_group_id (str): Episode Group ID.
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
        """
        return self._get(f"/tv/episode_group/{episode_group_id}", language=language)

    def watch_providers_get_available_regions(self, language: Optional[str] = None) -> Dict:
        """ `Watch Providers Get Available Regions <https://developers.themoviedb.org/3/watch-providers/get-available-regions>`__

            Returns a list of all of the countries we have watch provider (OTT/streaming) data for.

            Parameters:
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
        """
        return self._get("/watch/providers/regions", language=language)

    def watch_providers_get_movie_providers(self, language: Optional[str] = None, watch_region: Optional[str] = None) -> Dict:
        """ `Watch Providers Get Movie Providers <https://developers.themoviedb.org/3/watch-providers/get-movie-providers>`__

            Returns a list of the watch provider (OTT/streaming) data we have available for movies. You can specify a ``watch_region`` param if you want to further filter the list by country.

            Parameters:
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                watch_region (Optional[str]): Use the ISO-3166-1 code to filter the providers that are available in a particular country.
        """
        return self._get("/watch/providers/movie", language=language, watch_region=watch_region)

    def watch_providers_get_tv_providers(self, language: Optional[str] = None, watch_region: Optional[str] = None) -> Dict:
        """ `Watch Providers Get TV Providers <https://developers.themoviedb.org/3/watch-providers/get-tv-providers>`__

            Returns a list of the watch provider (OTT/streaming) data we have available for TV series. You can specify a ``watch_region`` param if you want to further filter the list by country.

            Parameters:
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                watch_region (Optional[str]): Use the ISO-3166-1 code to filter the providers that are available in a particular country.
        """
        return self._get("/watch/providers/tv", language=language, watch_region=watch_region)
