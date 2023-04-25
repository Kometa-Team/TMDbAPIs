from abc import ABC, abstractmethod
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
        if item.startswith("_") or self._loading or not self._partial or \
                (isinstance(value, (list, dict, int, float)) and value) or \
                (not isinstance(value, (list, dict, int, float)) and value is not None):
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
        return self._tmdb._parse(data=self._data if data is None else data, attrs=attrs, value_type=value_type,
                                 default_is_none=default_is_none, is_list=is_list, is_dict=is_dict, extend=extend, key=key)