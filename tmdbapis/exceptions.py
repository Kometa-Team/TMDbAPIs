class TMDbException(Exception):
    """ Base class for all TMDbAPIs exceptions. """
    pass


class Invalid(TMDbException):
    """ Invalid Selection. """
    pass


class NotFound(TMDbException):
    """ Item not found. """
    pass


class Unauthorized(TMDbException):
    """ Invalid apikey. """
    pass


class Authentication(TMDbException):
    """ Operation requires Authentication """
    pass


class PrivateResource(TMDbException):
    """ Operation requires Private Resource """
    pass


class WritePermission(TMDbException):
    """ Operation requires Write Permission """
    pass
