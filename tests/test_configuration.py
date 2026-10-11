import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from tmdbapis.objs.reload import Configuration
from tmdbapis.tmdb import TMDbAPIs


class ConfigurationTests(unittest.TestCase):

    def test_date_parser_accepts_tmdb_timestamp_variants(self):
        tmdb = TMDbAPIs.__new__(TMDbAPIs)
        expected = datetime(2026, 10, 11, 12, 30, 45)

        for value in (
            "2026-10-11 12:30:45 UTC",
            "2026-10-11 12:30:45 UT",
            "2026-10-11T12:30:45Z",
            "2026-10-11T12:30:45.123Z",
        ):
            self.assertEqual(tmdb._parse(data=value, value_type="date"), expected)
        self.assertEqual(tmdb._parse(data="2026-10-11", value_type="date"), datetime(2026, 10, 11))
        self.assertIsNone(tmdb._parse(data="not-a-date", value_type="date"))

    def test_genre_requests_use_the_client_language(self):
        tmdb = TMDbAPIs.__new__(TMDbAPIs)
        tmdb._api = MagicMock()
        tmdb._parse = MagicMock(side_effect=[["movie"], ["tv"]])
        tmdb._language = "fr-FR"
        tmdb._movie_genres = None
        tmdb._tv_genres = None

        self.assertEqual(tmdb.movie_genres(), ["movie"])
        self.assertEqual(tmdb.tv_genres(), ["tv"])
        tmdb._api.genres_get_movie_list.assert_called_once_with(language="fr-FR")
        tmdb._api.genres_get_tv_list.assert_called_once_with(language="fr-FR")

    def test_language_change_invalidates_genre_caches(self):
        tmdb = TMDbAPIs.__new__(TMDbAPIs)
        tmdb._language = "en"
        tmdb._iso_639_1 = {"en": object()}
        tmdb._translations = {"fr-fr": "fr-FR"}
        tmdb._movie_genres = object()
        tmdb._movie_genre_lookups = object()
        tmdb._tv_genres = object()
        tmdb._tv_genre_lookups = object()

        tmdb.language = "fr-FR"

        self.assertEqual(tmdb.language, "fr-FR")
        self.assertIsNone(tmdb._movie_genres)
        self.assertIsNone(tmdb._movie_genre_lookups)
        self.assertIsNone(tmdb._tv_genres)
        self.assertIsNone(tmdb._tv_genre_lookups)

    def test_full_load_fetches_configuration_resources_separately(self):
        configuration = Configuration.__new__(Configuration)
        configuration._api = MagicMock()
        configuration._api.configuration_get_api_configuration.return_value = {
            "change_keys": ["adult"],
            "images": {"base_url": "http://image/"}
        }
        configuration._api.configuration_get_countries.return_value = [
            {"iso_3166_1": "US", "english_name": "United States"}
        ]
        configuration._api.configuration_get_jobs.return_value = [
            {"department": "Directing", "jobs": ["Director"]}
        ]
        configuration._api.configuration_get_languages.return_value = [
            {"iso_639_1": "en", "english_name": "English", "name": "English"}
        ]
        configuration._api.configuration_get_primary_translations.return_value = ["en-US"]
        configuration._api.configuration_get_timezones.return_value = [
            {"iso_3166_1": "US", "zones": ["America/New_York"]}
        ]

        data = configuration._full_load()

        configuration._api.configuration_get_api_configuration.assert_called_once_with()
        configuration._api.configuration_get_countries.assert_called_once_with()
        configuration._api.configuration_get_jobs.assert_called_once_with()
        configuration._api.configuration_get_languages.assert_called_once_with()
        configuration._api.configuration_get_primary_translations.assert_called_once_with()
        configuration._api.configuration_get_timezones.assert_called_once_with()

        self.assertEqual(data["countries"][0]["iso_3166_1"], "US")
        self.assertEqual(data["jobs"][0]["department"], "Directing")
        self.assertEqual(data["languages"][0]["iso_639_1"], "en")
        self.assertEqual(data["primary_translations"], ["en-US"])
        self.assertEqual(data["timezones"][0]["zones"], ["America/New_York"])
        self.assertIn("images", data)
        self.assertIn("change_keys", data)


    @patch("tmdbapis.tmdb.API3")
    def test_valid_language_initializes_from_separate_configuration_endpoints(self, api3_class):
        api = api3_class.return_value
        api.configuration_get_api_configuration.return_value = {
            "change_keys": ["adult"],
            "images": {
                "base_url": "http://image/",
                "secure_base_url": "https://image/",
                "backdrop_sizes": [],
                "logo_sizes": [],
                "poster_sizes": [],
                "profile_sizes": [],
                "still_sizes": []
            }
        }
        api.configuration_get_countries.return_value = [
            {"iso_3166_1": "US", "english_name": "United States"}
        ]
        api.configuration_get_jobs.return_value = [
            {"department": "Directing", "jobs": ["Director"]}
        ]
        api.configuration_get_languages.return_value = [
            {"iso_639_1": "en", "english_name": "English", "name": "English"}
        ]
        api.configuration_get_primary_translations.return_value = ["en-US"]
        api.configuration_get_timezones.return_value = [
            {"iso_3166_1": "US", "zones": ["America/New_York"]}
        ]

        tmdb = TMDbAPIs("test-api-key", language="en")

        self.assertEqual(tmdb.language, "en")
        self.assertIn("en", tmdb._iso_639_1)
        self.assertIn("en-us", tmdb._translations)
        self.assertEqual(tmdb._translations["en-us"], "en-US")

        tmdb.language = "en-US"
        self.assertEqual(tmdb.language, "en-US")


if __name__ == "__main__":
    unittest.main()
