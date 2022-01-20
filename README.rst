Welcome to TMDbAPIs Documentation!
==========================================================

.. image:: https://img.shields.io/readthedocs/tmdbapis?style=plastic
    :target: https://tmdbapis.readthedocs.io/en/latest/?badge=latest
    :alt: Read the Docs

.. image:: https://img.shields.io/github/v/release/meisnate12/TMDbAPIs?style=plastic
    :target: https://github.com/meisnate12/TMDbAPIs/releases
    :alt: GitHub release (latest by date)

.. image:: https://img.shields.io/pypi/v/TMDbAPIs?style=plastic
    :target: https://pypi.org/project/tmdbapis/
    :alt: PyPI

.. image:: https://img.shields.io/pypi/dm/tmdbapis.svg?style=plastic
    :target: https://pypi.org/project/tmdbapis/
    :alt: Downloads

.. image:: https://img.shields.io/github/commits-since/meisnate12/TMDbAPIs/latest?style=plastic
    :target: https://github.com/meisnate12/TMDbAPIs/commits/master
    :alt: GitHub commits since latest release (by date) for a branch

.. image:: https://img.shields.io/badge/-Sponsor_or_Donate-blueviolet?style=plastic
    :target: https://github.com/sponsors/meisnate12
    :alt: GitHub Sponsor


Overview
----------------------------------------------------------
Unofficial Python bindings for the TMDb API. The goal is to make interaction with the API as easy as possible while emulating the endpoints as much as possible


Installation & Documentation
----------------------------------------------------------

.. code-block:: python

    pip install tmdbapis

Documentation_ can be found at Read the Docs.

.. _Documentation: http://tmdbapis.readthedocs.io/en/latest/


Using the Object API
==========================================================


Getting a TMDbAPIs Instance
----------------------------------------------------------

To create a TMDbAPIs Object you need your V3 API Key, which can be found following `this guide <https://developers.themoviedb.org/3/getting-started/introduction>`_.

.. code-block:: python

    from tmdbapis import TMDbAPIs

    apikey = "0010843563404748808d3fc9c562c05e"

    tmdb = TMDbAPIs(apikey)


Authenticating V3 API Token
----------------------------------------------------------

To authenticate your TMDb V3 API Token you can either authenticate your TMDb V4 Token or use the `authenticate() <https://tmdbapis.readthedocs.io/en/latest/objapi.html#tmdbapis.tmdb.TMDbAPIs.authenticate>`_ method.

.. code-block:: python

    from tmdbapis import TMDbAPIs

    apikey = "0010843563404748808d3fc9c562c05e"

    tmdb = TMDbAPIs(apikey)
    tmdb.authenticate(username, password)


Saving a V3 API Authenticated Session
----------------------------------------------------------

To save your authenticated session use the ``session_id`` Attribute.

.. code-block:: python

    from tmdbapis import TMDbAPIs

    apikey = "0010843563404748808d3fc9c562c05e"

    tmdb = TMDbAPIs(apikey)
    tmdb.authenticate(username, password)
    with open("session_id.txt", "w") as text_file:
        print(tmdb.session_id, file=text_file)

To load the authenticated session use the ``session_id`` Parameter of the `TMDbAPIs <https://tmdbapis.readthedocs.io/en/latest/objapi.html#tmdbapis.tmdb.TMDbAPIs>`_ constructor.

.. code-block:: python

    from tmdbapis import TMDbAPIs

    apikey = "0010843563404748808d3fc9c562c05e"

    session_id = None
    with open("session_id.txt") as text_file:
        session_id = text_file.readline()

    tmdb = TMDbAPIs(apikey, session_id=session_id)


Adding TMDb V4 API Read Access Token
----------------------------------------------------------

To gain read access to TMDb V4's API just provide you're TMDb V4 Access Token either using the ``v4_access_token`` Parameter of the `TMDbAPIs <https://tmdbapis.readthedocs.io/en/latest/objapi.html#tmdbapis.tmdb.TMDbAPIs>`_ constructor or by using the `v4_access_token() <https://tmdbapis.readthedocs.io/en/latest/objapi.html#tmdbapis.tmdb.TMDbAPIs.v4_access_token>`_ method.

To gain read access to TMDb V4's API need your TMDb V4 Access Token, which can be found following `this guide <https://developers.themoviedb.org/3/getting-started/introduction>`_.

.. code-block:: python

    from tmdbapis import TMDbAPIs

    apikey = "0010843563404748808d3fc9c562c05e"
    v4_access_token = "sohsnrfiemrsdvsavvt4h426GWEGW434gSgSdnjhcyuwbBYHBOSIYCBWgyNTYxNTY4OGQ5NTJjZCIsInN1YiI6IjVkMzM5ZmI0MmY4ZDAfdfdgegeGGregerfge34345BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIvfdvsdfveregrgqgfsfghjhOR0shmZZ_ZekFiuyl7o56921C0"

    tmdb = TMDbAPIs(apikey, v4_access_token=v4_access_token)


Authenticating TMDb V4 API Token
----------------------------------------------------------

To authenticate your TMDB V4 Read Access Token it is a multi step process.

1. Add your TMDb V4 API Read Access Token.
2. Authenticate the URL returned from `v4_authenticate() <https://tmdbapis.readthedocs.io/en/latest/objapi.html#tmdbapis.tmdb.TMDbAPIs.v4_authenticate>`_.
3. Once the URL has been authenticated you must approve it by running `v4_approved() <https://tmdbapis.readthedocs.io/en/latest/objapi.html#tmdbapis.tmdb.TMDbAPIs.v4_approved>`_.

.. code-block:: python

    from tmdbapis import TMDbAPIs

    apikey = "0010843563404748808d3fc9c562c05e"
    v4_access_token = "sohsnrfiemrsdvsavvt4h426GWEGW434gSgSdnjhcyuwbBYHBOSIYCBWgyNTYxNTY4OGQ5NTJjZCIsInN1YiI6IjVkMzM5ZmI0MmY4ZDAfdfdgegeGGregerfge34345BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIvfdvsdfveregrgqgfsfghjhOR0shmZZ_ZekFiuyl7o56921C0"

    tmdb = TMDbAPIs(apikey, v4_access_token=v4_access_token)

    print(tmdb.v4_authenticate())
    input("Navigate to the URL and then hit enter when Authenticated")
    tmdb.v4_approved()


Saving a V4 API Authenticated Token
----------------------------------------------------------

To save your authenticated token use the ``v4_access_token`` Attribute.

.. code-block:: python

    from tmdbapis import TMDbAPIs

    apikey = "0010843563404748808d3fc9c562c05e"
    v4_access_token = "sohsnrfiemrsdvsavvt4h426GWEGW434gSgSdnjhcyuwbBYHBOSIYCBWgyNTYxNTY4OGQ5NTJjZCIsInN1YiI6IjVkMzM5ZmI0MmY4ZDAfdfdgegeGGregerfge34345BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIvfdvsdfveregrgqgfsfghjhOR0shmZZ_ZekFiuyl7o56921C0"

    tmdb = TMDbAPIs(apikey, v4_access_token=v4_access_token)

    print(tmdb.v4_authenticate())
    input("Navigate to the URL and then hit enter when Authenticated")
    tmdb.v4_approved()
    with open("access_token.txt", "w") as text_file:
        print(tmdb.v4_access_token, file=text_file)

To load the authenticated token use the ``v4_access_token`` Parameter of the `TMDbAPIs <https://tmdbapis.readthedocs.io/en/latest/objapi.html#tmdbapis.tmdb.TMDbAPIs>`_ constructor or the `v4_access_token() <https://tmdbapis.readthedocs.io/en/latest/objapi.html#tmdbapis.tmdb.TMDbAPIs.v4_access_token>`_ method.

.. code-block:: python

    from tmdbapis import TMDbAPIs

    apikey = "0010843563404748808d3fc9c562c05e"

    v4_access_token = None
    with open("access_token.txt") as text_file:
        v4_access_token = text_file.readline()

    tmdb = TMDbAPIs(apikey, v4_access_token=v4_access_token)


Hyperlinks
----------------------------------------------------------

* `TMDb V3 API Docs <https://developers.themoviedb.org/3/getting-started/introduction>`_
* `TMDb V4 API Docs <https://developers.themoviedb.org/4/getting-started/authorization>`_

Usage & Contributions
----------------------------------------------------------
* Source is available on the `Github Project Page <https://github.com/meisnate12/tmdbapis>`_.
* Contributors to TMDbAPIs own their own contributions and may distribute that code under
  the `MIT license <https://github.com/meisnate12/tmdbapis/blob/master/LICENSE.txt>`_.
