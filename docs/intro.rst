Welcome to TMDbAPIs Documentation!
==========================================================

.. image:: https://img.shields.io/github/v/release/Kometa-Team/TMDbAPIs?style=plastic
    :target: https://github.com/Kometa-Team/TMDbAPIs/releases
    :alt: GitHub release (latest by date)

.. image:: https://img.shields.io/github/actions/workflow/status/Kometa-Team/TMDbAPIs/tests.yml?branch=master&style=plastic
    :target: https://github.com/Kometa-Team/TMDbAPIs/actions/workflows/tests.yml
    :alt: Build Testing

.. image:: https://img.shields.io/codecov/c/github/Kometa-Team/TMDbAPIs?color=greenred&style=plastic
    :target: https://codecov.io/gh/Kometa-Team/TMDbAPIs
    :alt: Build Coverage

.. image:: https://img.shields.io/github/commits-since/Kometa-Team/TMDbAPIs/latest?style=plastic
    :target: https://github.com/Kometa-Team/TMDbAPIs/commits/master
    :alt: GitHub commits since latest release (by date) for a branch

.. image:: https://img.shields.io/pypi/v/TMDbAPIs?style=plastic
    :target: https://pypi.org/project/tmdbapis/
    :alt: PyPI

.. image:: https://img.shields.io/pypi/dm/tmdbapis.svg?style=plastic
    :target: https://pypi.org/project/tmdbapis/
    :alt: Downloads

|

.. image:: https://img.shields.io/readthedocs/tmdbapis?color=%2300bc8c&style=plastic
    :target: https://tmdbapis.kometa.wiki/en/latest/
    :alt: Wiki

.. image:: https://img.shields.io/discord/822460010649878528?color=%2300bc8c&label=Discord&style=plastic
    :target: https://kometa.wiki/en/latest/discord/
    :alt: Discord

.. image:: https://img.shields.io/reddit/subreddit-subscribers/Kometa?color=%2300bc8c&label=r%2FKometa&style=plastic
    :target: https://www.reddit.com/r/Kometa/
    :alt: Reddit

.. image:: https://img.shields.io/github/sponsors/meisnate12?color=%238a2be2&style=plastic
    :target: https://github.com/sponsors/meisnate12
    :alt: GitHub Sponsors

.. image:: https://img.shields.io/badge/-Sponsor_or_Donate-blueviolet?style=plastic
    :target: https://github.com/sponsors/meisnate12
    :alt: Sponsor or Donate


Overview
----------------------------------------------------------
Unofficial Python bindings for the TMDb API. The goal is to make interaction with the API as easy as possible while emulating the endpoints as much as possible


Installation & Documentation
----------------------------------------------------------

.. code-block:: python

    pip install tmdbapis

Documentation_ can be found at Read the Docs.

.. _Documentation: https://tmdbapis.kometa.wiki


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

To authenticate your TMDb V3 API Token you can either authenticate your TMDb V4 Token or use the :meth:`~tmdbapis.tmdb.TMDbAPIs.authenticate` method.

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

To load the authenticated session use the ``session_id`` Parameter of the :class:`~tmdbapis.tmdb.TMDbAPIs` constructor.

.. code-block:: python

    from tmdbapis import TMDbAPIs

    apikey = "0010843563404748808d3fc9c562c05e"

    session_id = None
    with open("session_id.txt") as text_file:
        session_id = text_file.readline()

    tmdb = TMDbAPIs(apikey, session_id=session_id)


Adding TMDb V4 API Read Access Token
----------------------------------------------------------

To gain read access to TMDb V4's API just provide you're TMDb V4 Access Token either using the ``v4_access_token`` Parameter of the :class:`~tmdbapis.tmdb.TMDbAPIs` constructor or by using the :meth:`~tmdbapis.tmdb.TMDbAPIs.v4_access_token` method.

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
    2. Authenticate the URL returned from :meth:`~tmdbapis.tmdb.TMDbAPIs.v4_authenticate`.
    3. Once the URL has been authenticated you must approve it by running :meth:`~tmdbapis.tmdb.TMDbAPIs.v4_approved`.

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

To load the authenticated token use the ``v4_access_token`` Parameter of the :class:`~tmdbapis.tmdb.TMDbAPIs` constructor or the :meth:`~tmdbapis.tmdb.TMDbAPIs.v4_access_token` method.

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
* Source is available on the `Github Project Page <https://github.com/Kometa-Team/TMDbAPIs>`_.
* Contributors to TMDbAPIs own their own contributions and may distribute that code under
  the `MIT license <https://github.com/Kometa-Team/TMDbAPIs/blob/master/LICENSE.txt>`_.
