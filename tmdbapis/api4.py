import logging
from json.decoder import JSONDecodeError
from typing import Dict, Optional, Union, List

from requests import Session, Response
from requests.exceptions import RequestException

from tmdbapis import util
from tmdbapis.exceptions import TMDbException, NotFound, Unauthorized, WritePermission, PrivateResource, Authentication

logger = logging.getLogger(__name__)

base_url = "https://api.themoviedb.org/4"

class API4:
    """ Raw V4 API Class containing all `TMDb API4 calls <https://developers.themoviedb.org/4/getting-started/authorization>`__.

        Parameters:
            access_token (str): TMDb V4 Access Token.
            session (Optional[Session]): :class:`requests.Session` object.
            validate (bool): Validate the TMDb V4 Access Token on creation.

        Attributes:
            access_token (str): TMDb V4 Access Token.
            has_write_token (bool): Does the provided TMDb V4 Access Token have write access.
            account_id (str): TMDb V4 Account ID.
            response (Response): TMDb V4 most recent full :class:`requests.Response` object.
    """
    def __init__(self, access_token: str, session: Optional[Session] = None, validate: bool = True):
        self.access_token = access_token
        self._account_id = None
        self._session = Session() if session is None else session
        self.response = None
        if validate:
            try:
                self.auth_create_access_token(self.access_token)
            except TMDbException:
                self.auth_create_request_token()

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
        url_params = {k: v for k, v in kwargs.items() if v is not None}
        body_json = {k: v for k, v in json.items() if v is not None} if json else None
        request_url = f"{base_url}{path}"
        logger.debug(f"Request URL: {request_url}")
        headers = {"Authorization": f"Bearer {self.access_token}"}
        if body_json is not None:
            logger.debug(f"Request JSON: {body_json}")
        logger.debug(f"Headers: {headers}")
        try:
            if request_type == "delete":
                self.response = self._session.delete(request_url, json=body_json, headers=headers, params=url_params)
            elif request_type == "post":
                self.response = self._session.post(request_url, json=body_json, headers=headers, params=url_params)
            elif request_type == "put":
                self.response = self._session.put(request_url, json=body_json, headers=headers, params=url_params)
            else:
                self.response = self._session.get(request_url, headers=headers, params=url_params)
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
    def has_write_token(self):
        return self._account_id is not None

    @property
    def account_id(self):
        if not self._account_id:
            raise Authentication(f"Requires V4 API Write Access Token, use tmdbapis.v4_access_token(access_token)")
        return self._account_id

    def account_get_lists(self, account_id: Optional[str] = None, page: Optional[int] = None) -> Dict:
        """ `Account Get Lists <https://developers.themoviedb.org/4/account/get-account-lists>`__

            Get all of the lists you've created.

            Parameters:
                account_id (Optional[str]): Account ID.
                page (Optional[int]): Specify which page to query.
        """
        return self._get(f"/account/{account_id if account_id else self.account_id}/lists", page=page)

    def account_get_favorite_movies(
            self, account_id: Optional[str] = None,
            sort_by: Optional[str] = None,
            page: Optional[str] = None
    ) -> Dict:
        """ `Account Get Favorite Movies <https://developers.themoviedb.org/3/account/get-favorite-movies>`__

            Get the list of movies you have marked as a favorite.

            Parameters:
                account_id (Optional[str]): Account ID.
                sort_by (Optional[str]): Choose a sort option for the list of results. Allowed Values: ``created_at.asc``, ``created_at.desc``, ``release_date.asc``, ``release_date.desc``, ``title.asc``, ``title.desc``, ``vote_average.asc``, ``vote_average.desc``
                page (Optional[int]): Specify which page to query.
        """
        return self._get(f"/account/{account_id if account_id else self.account_id}/movie/favorites", sort_by=sort_by, page=page)

    def account_get_favorite_tv_shows(
            self, account_id: Optional[str] = None,
            sort_by: Optional[str] = None,
            page: Optional[str] = None
    ) -> Dict:
        """ `Account Get Favorite TV Shows <https://developers.themoviedb.org/4/account/get-account-favorite-tv-shows>`__

            Get the list of TV shows you have marked as a favorite.

            Parameters:
                account_id (Optional[str]): Account ID.
                sort_by (Optional[str]): Choose a sort option for the list of results. Allowed Values: ``first_air_date.asc``, ``first_air_date.desc``, ``name.asc``, ``name.desc``, ``vote_average.asc``, ``vote_average.desc``
                page (Optional[int]): Specify which page to query.
        """
        return self._get(f"/account/{account_id if account_id else self.account_id}/tv/favorites", sort_by=sort_by, page=page)

    def account_get_movie_recommendations(
            self, account_id: Optional[str] = None,
            sort_by: Optional[str] = None,
            page: Optional[str] = None
    ) -> Dict:
        """ `Account Get Movie Recommendations <https://developers.themoviedb.org/4/account/get-account-movie-recommendations>`__

            Get a list of your personal movie recommendations.

            Parameters:
                account_id (Optional[str]): Account ID.
                sort_by (Optional[str]): Choose a sort option for the list of results. Allowed Values: ``created_at.asc``, ``created_at.desc``, ``release_date.asc``, ``release_date.desc``, ``title.asc``, ``title.desc``, ``vote_average.asc``, ``vote_average.desc``
                page (Optional[int]): Specify which page to query.
        """
        return self._get(f"/account/{account_id if account_id else self.account_id}/movie/recommendations", sort_by=sort_by, page=page)

    def account_get_tv_show_recommendations(
            self, account_id: Optional[str] = None,
            sort_by: Optional[str] = None,
            page: Optional[str] = None
    ) -> Dict:
        """ `Account Get TV Show Recommendations <https://developers.themoviedb.org/4/account/get-account-tv-show-recommendations>`__

            Get a list of your personal TV show recommendations.

            Parameters:
                account_id (Optional[str]): Account ID.
                sort_by (Optional[str]): Choose a sort option for the list of results. Allowed Values: ``first_air_date.asc``, ``first_air_date.desc``, ``name.asc``, ``name.desc``, ``vote_average.asc``, ``vote_average.desc``
                page (Optional[int]): Specify which page to query.
        """
        return self._get(f"/account/{account_id if account_id else self.account_id}/tv/rated", sort_by=sort_by, page=page)

    def account_get_movie_watchlist(
            self, account_id: Optional[str] = None,
            sort_by: Optional[str] = None,
            page: Optional[str] = None
    ) -> Dict:
        """ `Account Get Movie Watchlist <https://developers.themoviedb.org/4/account/get-account-movie-watchlist>`__

            Get the list of movies you have added to your watchlist.

            Parameters:
                account_id (Optional[str]): Account ID.
                sort_by (Optional[str]): Choose a sort option for the list of results. Allowed Values: ``created_at.asc``, ``created_at.desc``, ``release_date.asc``, ``release_date.desc``, ``title.asc``, ``title.desc``, ``vote_average.asc``, ``vote_average.desc``
                page (Optional[int]): Specify which page to query.
        """
        return self._get(f"/account/{account_id if account_id else self.account_id}/movie/watchlist", sort_by=sort_by, page=page)

    def account_get_tv_show_watchlist(
            self, account_id: Optional[str] = None,
            sort_by: Optional[str] = None,
            page: Optional[str] = None
    ) -> Dict:
        """ `Account Get TV Show Watchlist <https://developers.themoviedb.org/4/account/get-account-tv-show-watchlist>`__

            Get the list of TV shows you have added to your watchlist.

            Parameters:
                account_id (Optional[str]): Account ID.
                sort_by (Optional[str]): Choose a sort option for the list of results. Allowed Values: ``first_air_date.asc``, ``first_air_date.desc``, ``name.asc``, ``name.desc``, ``vote_average.asc``, ``vote_average.desc``
                page (Optional[int]): Specify which page to query.
        """
        return self._get(f"/account/{account_id if account_id else self.account_id}/tv/watchlist", sort_by=sort_by, page=page)

    def account_get_rated_movies(
            self, account_id: Optional[str] = None,
            sort_by: Optional[str] = None,
            page: Optional[str] = None
    ) -> Dict:
        """ `Account Get Rated Movies <https://developers.themoviedb.org/4/account/get-account-rated-movies>`__

            Get the list of movies you have rated.

            Parameters:
                account_id (Optional[str]): Account ID.
                sort_by (Optional[str]): Choose a sort option for the list of results. Allowed Values: ``created_at.asc``, ``created_at.desc``, ``release_date.asc``, ``release_date.desc``, ``title.asc``, ``title.desc``, ``vote_average.asc``, ``vote_average.desc``
                page (Optional[int]): Specify which page to query.
        """
        return self._get(f"/account/{account_id if account_id else self.account_id}/movie/rated", sort_by=sort_by, page=page)

    def account_get_rated_tv_shows(
            self, account_id: Optional[str] = None,
            sort_by: Optional[str] = None,
            page: Optional[str] = None
    ) -> Dict:
        """ `Account Get Rated TV Shows <https://developers.themoviedb.org/4/account/get-account-rated-tv-shows>`__

            Get the list of TV shows you have rated.

            Parameters:
                account_id (Optional[str]): Account ID.
                sort_by (Optional[str]): Choose a sort option for the list of results. Allowed Values: ``first_air_date.asc``, ``first_air_date.desc``, ``name.asc``, ``name.desc``, ``vote_average.asc``, ``vote_average.desc``
                page (Optional[int]): Specify which page to query.
        """
        return self._get(f"/account/{account_id if account_id else self.account_id}/tv/rated", sort_by=sort_by, page=page)

    def auth_create_request_token(self, redirect_to: Optional[str] = None) -> Dict:
        """ `Auth Create Request Token <https://developers.themoviedb.org/4/auth/create-request-token>`__

            This method generates a new request token that you can ask a user to approve. This is the first step in
            getting permission from a user to read and write data on their behalf. You can read more about this system
            `here <https://developers.themoviedb.org/4/auth/user-authorization-1>`__.

            Parameters:
                redirect_to (Optional[str]): Redirect URL or callback that will be executed once a request token has been approved on TMDb.
        """
        return self._post("/auth/request_token", json={"redirect_to": redirect_to} if redirect_to else None)

    def auth_create_access_token(self, request_token: str) -> Dict:
        """ `Auth Create Access Token <https://developers.themoviedb.org/4/auth/create-access-token>`__

            This method will finish the user authentication flow and issue an official user access token. The request
            token in this request is sent along as part of the POST body. You should still use your standard API read
            access token for authenticating this request.

            Parameters:
                request_token (str): Request Token
        """
        response = self._post("/auth/access_token", json={"request_token": request_token})
        self.access_token = response["access_token"]
        self._account_id = response["account_id"]
        return response

    def auth_delete_access_token(self, access_token: str) -> Dict:
        """ `Auth Delete Access Token <https://developers.themoviedb.org/4/auth/delete-access-token>`__

            This method gives your users the ability to log out of a session.

            Parameters:
                access_token (str): Access Token
        """
        return self._delete("/auth/access_token", json={"access_token": access_token})

    def list_get_list(
            self, list_id: int,
            language: Optional[str] = None,
            sort_by: Optional[str] = None,
            page: Optional[str] = None
    ) -> Dict:
        """ `List Get List <https://developers.themoviedb.org/4/list/get-list>`__

            This method will retrieve a list by id.

            Private lists can only be accessed by their owners and therefore require a valid user access token.

            Parameters:
                list_id (int): List ID
                language (Optional[str]): ISO-639-1 or ISO-3166-1 value to display translated data for the fields that support it.
                sort_by (Optional[str]): Choose a sort option for the list of results. Allowed Values: ``original_order.asc``, ``original_order.desc``, ``release_date.asc``, ``release_date.desc``, ``title.asc``, ``title.desc``, ``vote_average.asc``, ``vote_average.desc``
                page (Optional[int]): Specify which page to query.
        """
        return self._get(f"/list/{list_id}", language=language, sort_by=sort_by, page=page)

    def list_create_list(
            self, name: str,
            iso_639_1: str,
            description: Optional[str] = None,
            public: Optional[bool] = None,
            iso_3166_1: Optional[str] = None
    ) -> Dict:
        """ `List Create List <https://developers.themoviedb.org/4/list/create-list>`__

            This method will create a new list.

            You will need to have valid user access token in order to create a new list.

            Parameters:
                name (str): Set the name of your list.
                iso_639_1 (str): Set the ISO-639-1 variant for your list.
                description (Optional[str]): Set the description of your list.
                public (Optional[bool]): Toggle the public status of your list.
                iso_3166_1 (Optional[int]): Set the ISO-3166-1 variant for your list.
        """
        return self._post(
            "/list",
            json={
                "name": name,
                "iso_639_1": iso_639_1,
                "description": description,
                "public": public,
                "iso_3166_1": iso_3166_1
            }
        )

    def list_update_list(
            self, list_id: int,
            name: Optional[str] = None,
            description: Optional[str] = None,
            public: Optional[bool] = None,
            sort_by: Optional[str] = None
    ) -> Dict:
        """ `List Update List <https://developers.themoviedb.org/4/list/update-list>`__

            This method will let you update the details of a list.

            You must be the owner of the list and therefore have a valid user access token in order to edit it.

            Parameters:
                list_id (int): List ID
                name (Optional[str]): Set the name of your list.
                description (Optional[str]): Set the description of your list.
                public (Optional[bool]): Toggle the public status of your list.
                sort_by (Optional[str]): Choose a sort option for the list of results. Allowed Values: ``original_order.asc``, ``original_order.desc``, ``vote_average.asc``, ``vote_average.desc``, ``primary_release_date.asc``, ``primary_release_date.desc``, ``title.asc``, ``title.desc``
        """
        return self._put(
            f"/list/{list_id}",
            json={
                "name": name,
                "description": description,
                "public": public,
                "sort_by": sort_by
            }
        )

    def list_clear_list(self, list_id: int) -> Dict:
        """ `List Clear List <https://developers.themoviedb.org/4/list/clear-list>`__

            This method lets you clear all of the items from a list in a single request. This action cannot be reversed so use it with caution.

            You must be the owner of the list and therefore have a valid user access token in order to clear a list.

            Parameters:
                list_id (int): List ID
        """
        return self._get(f"/list/{list_id}/clear")

    def list_delete_list(self, list_id: int) -> Dict:
        """ `List Clear List <https://developers.themoviedb.org/4/list/delete-list>`__

            This method will delete a list by id. This action is not reversible so take care when issuing it.

            You must be the owner of the list and therefore have a valid user access token in order to delete it.

            Parameters:
                list_id (int): List ID
        """
        return self._delete(f"/list/{list_id}")

    def list_add_items(self, list_id: int, items: List[Dict[str, Union[str, int]]]) -> Dict:
        """ `List Add Items <https://developers.themoviedb.org/4/list/add-items>`__

            This method will let you add items to a list. We support essentially an unlimited number of items to be
            posted at a time. Both movie and TV series are support.

            The results of this query will return a ``results`` array. Each result includes a ``success`` field. If a
            result is ``false`` this will usually indicate that the item already exists on the list. It may also
            indicate that the item could not be found.

            You must be the owner of the list and therefore have a valid user access token in order to add items to a
            list.

            Parameters:
                list_id (int): List ID
                items (List[Dict[str, Union[str, int]]]): List of items to add. Each item is a dictionary with the format {"media_type": str, "media_id": int}. ``media_type`` can either be ``movie`` or ``tv``.
        """
        return self._post(f"/list/{list_id}/items", json=util.validate_items(items))

    def list_update_items(self, list_id: int, items: List[Dict[str, Union[str, int]]]) -> Dict:
        """ `List Update Items <https://developers.themoviedb.org/4/list/update-items>`__

            This method will let you update an individual item on a list. Currently, only adding a comment is supported.

            You must be the owner of the list and therefore have a valid user access token in order to edit items.

            Parameters:
                list_id (int): List ID
                items (List[Dict[str, Union[str, int]]]): List of items to update. Each item is a dictionary with the format {"media_type": str, "media_id": int, "comment": str}. ``media_type`` can either be ``movie`` or ``tv``.
        """
        return self._put(f"/list/{list_id}/items", json=util.validate_items(items, comment=True))

    def list_remove_items(self, list_id: int, items: List[Dict[str, Union[str, int]]]) -> Dict:
        """ `List Remove Items <https://developers.themoviedb.org/4/list/remove-items>`__

            This method will let you remove items from a list. You can remove multiple items at a time.

            You must be the owner of the list and therefore have a valid user access token in order to delete items from it.

            Parameters:
                list_id (int): List ID
                items (List[Dict[str, Union[str, int]]]): List of items to remove. Each item is a dictionary with the format {"media_type": str, "media_id": int}. ``media_type`` can either be ``movie`` or ``tv``.
        """
        return self._delete(f"/list/{list_id}/items", json=util.validate_items(items))

    def list_check_item_status(self, list_id: int, media_id: int, media_type: str) -> Dict:
        """ `List Check Item Status <https://developers.themoviedb.org/4/list/check-item-status>`__

            This method lets you quickly check if the item is already added to the list.

            You must be the owner of the list and therefore have a valid user access token in order to check an item status.

            Parameters:
                list_id (int): List ID
                media_id (int): Media ID
                media_type (str): Set the kind of media object are you checking. Allowed Values: ``movie``, ``tv``
        """
        return self._get(f"/list/{list_id}/item_status", media_id=media_id, media_type=media_type)
