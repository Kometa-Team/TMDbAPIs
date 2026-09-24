import unittest
from unittest.mock import MagicMock, patch

from tmdbapis.objs.reload import Configuration
from tmdbapis.tmdb import TMDbAPIs


class ConfigurationTests(unittest.TestCase):

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
        self.assertIn("en-US", tmdb._translations)

        tmdb.language = "en-US"
        self.assertEqual(tmdb.language, "en-US")


if __name__ == "__main__":
    unittest.main()
