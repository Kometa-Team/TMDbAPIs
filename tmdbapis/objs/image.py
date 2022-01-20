from tmdbapis.objs.base import TMDbObj


class TMDbImage(TMDbObj):
    """ Represents a single Image.

        Attributes:
            aspect_ratio (float): Image Aspect Ratio.
            file_path (str): Image Path.
            file_type (str): File type of the Image.
            height (int): Image Height.
            id (str): Image ID.
            iso_639_1 (str): ISO 639-1 Language Code of the Image.
            language (:class:`~tmdbapis.objs.simple.Language`): Language object for the ISO 639-1 Language Code.
            url (str): Image Full URL.
            width (int): Image Width.
            vote_average (float): Image Vote Average.
            vote_count (int): Image Vote Count.
    """

    def __init__(self, tmdb, data, image_type):
        super().__init__(tmdb, data)
        self._image_type = image_type

    def _load(self, data):
        super()._load(data)
        self.aspect_ratio = self._parse(attrs="aspect_ratio", value_type="float")
        self.file_path = self._parse(attrs="file_path")
        self.file_type = self._parse(attrs="file_type")
        self.height = self._parse(attrs="height", value_type="int")
        self.id = self._parse(attrs="id", value_type="str")
        self.iso_639_1 = self._parse(attrs="iso_639_1")
        self.language = self._tmdb._get_object(self._data, "language")
        self.url = self._image_url(self.file_path)
        self.vote_average = self._parse(attrs="vote_average", value_type="float")
        self.vote_count = self._parse(attrs="vote_count", value_type="int")
        self.width = self._parse(attrs="width", value_type="int")
        self._finish(self.file_path)

    def __str__(self):
        return f"[{self._image_type}:{self.file_path}]"


class Backdrop(TMDbImage):
    """ Represents a single Backdrop Image. """

    def __init__(self, tmdb, data):
        super().__init__(tmdb, data, "Backdrop")


class Logo(TMDbImage):
    """ Represents a single Logo Image. """

    def __init__(self, tmdb, data):
        super().__init__(tmdb, data, "Logo")


class Poster(TMDbImage):
    """ Represents a single Poster Image. """

    def __init__(self, tmdb, data):
        super().__init__(tmdb, data, "Poster")


class Profile(TMDbImage):
    """ Represents a single Profile Image. """

    def __init__(self, tmdb, data):
        super().__init__(tmdb, data, "Profile")


class Still(TMDbImage):
    """ Represents a single Still Image. """

    def __init__(self, tmdb, data):
        super().__init__(tmdb, data, "Still")


class Tagged(TMDbImage):
    """ Represents a single Tagged Image.

        Attributes:
            image_type (str): Image Type.
            media (Union[:class:`~tmdbapis.objs.reload.Movie`, :class:`~tmdbapis.objs.reload.TVShow`]): Media object associated with the Image.
            media_type (str): Media Type for Image.
    """

    def __init__(self, tmdb, data):
        super().__init__(tmdb, data, "Tagged")

    def _load(self, data):
        super()._load(data)
        self._loading = True
        self.image_type = self._parse(attrs="image_type")
        self.media_type = self._parse(attrs="media_type")
        self.media = self._parse(attrs="media", value_type=self.media_type)
        self._loading = False
