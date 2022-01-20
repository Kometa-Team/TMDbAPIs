from abc import ABC, abstractmethod

from tmdbapis.exceptions import Invalid
from tmdbapis.objs.base import TMDbObj


class Favorite(ABC):
    def mark_as_favorite(self: TMDbObj):
        """ Mark as a Favorite (Authentication Required) """
        self._api.account_mark_as_favorite(self._media_type(), self.id, True)

    def remove_as_favorite(self: TMDbObj):
        """ Remove as a Favorite (Authentication Required) """
        self._api.account_mark_as_favorite(self._media_type(), self.id, False)

    @abstractmethod
    def _media_type(self):
        pass


class Rate(ABC):
    def rate(self, rating: float):
        """ Add a Rating (Authentication Required)

            Parameters:
                rating (float): Rating to use.
        """
        try:
            if float(rating) < 0.5 or float(rating) > 10.0:
                raise TypeError
        except TypeError:
            raise Invalid("Rating must be between 0.5 and 10.0")
        self._rate(rating)

    def delete_rating(self):
        """ Delete a Rating (Authentication Required) """
        self._delete_rate()

    @abstractmethod
    def _rate(self, rating):
        pass

    @abstractmethod
    def _delete_rate(self):
        pass


class Watchlist(ABC):
    def add_to_watchlist(self: TMDbObj):
        """ Add to your Watchlist (Authentication Required) """
        self._api.account_add_to_watchlist(self._media_type(), self.id, True)

    def remove_from_watchlist(self: TMDbObj):
        """ Remove from your Watchlist (Authentication Required) """
        self._api.account_add_to_watchlist(self._media_type(), self.id, False)

    @abstractmethod
    def _media_type(self):
        pass
