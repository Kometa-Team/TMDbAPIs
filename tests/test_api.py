import os, unittest

from tmdbapis import NotFound, Movie, Person, TVShow
from tmdbapis.tmdb import TMDbAPIs
"""
import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())
"""
class APITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        session_id = os.environ["TMDB_SESSION"]
        apikey = os.environ["TMDB_APIKEY"]
        access = os.environ["TMDB_V4"]
        cls.api = TMDbAPIs(apikey, v4_access_token=access, session_id=session_id)

    def test_ab_variables(self):
        self.assertEqual(self.api.account_id, 8568268)
        self.assertEqual(self.api.v4_account_id, "5d339fb42f8d097bccd118c7")

    def test_account(self):
        account = self.api.account()
        self.assertEqual(account.id, 8568268)
        self.assertEqual(account.username, "meisnate12")
        self.assertGreater(len(account.created_lists(v3=True).results), 0)
        self.assertGreater(len(account.created_lists().results), 0)
        self.assertGreater(len(account.favorite_movies(v3=True).results), 0)
        self.assertGreater(len(account.favorite_movies().results), 0)
        self.assertGreater(len(account.favorite_tv_shows(v3=True).results), 0)
        self.assertGreater(len(account.favorite_tv_shows().results), 0)
        self.assertGreater(len(account.rated_movies(v3=True).results), 0)
        self.assertGreater(len(account.rated_movies().results), 0)
        self.assertGreater(len(account.rated_tv_shows(v3=True).results), 0)
        self.assertGreater(len(account.rated_tv_shows().results), 0)
        self.assertGreater(len(account.rated_episodes().results), 0)
        self.assertGreater(len(account.movie_watchlist(v3=True).results), 0)
        self.assertGreater(len(account.movie_watchlist().results), 0)
        self.assertGreater(len(account.tv_show_watchlist(v3=True).results), 0)
        self.assertGreater(len(account.tv_show_watchlist().results), 0)
        self.assertGreater(len(account.movie_recommendations().results), 0)
        self.assertGreater(len(account.tv_show_recommendations().results), 0)

    def test_certifications(self):
        movie = self.api.movie_certifications()
        tv = self.api.tv_certifications()
        self.assertIn("US", movie)
        self.assertIn("US", tv)

    def test_changes(self):
        self.assertGreater(len(self.api.movie_change_list()), 0)
        self.assertGreater(len(self.api.tv_change_list()), 0)
        self.assertGreater(len(self.api.person_change_list()), 0)

    def test_collections(self):
        collection = self.api.collection(10)
        self.assertEqual(collection.name, "Star Wars Collection")
        self.assertGreater(len(collection.movies), 0)

    def test_companies(self):
        company = self.api.company(1)
        self.assertEqual(company.name, "Lucasfilm")
        self.assertGreater(len(company.movies), 0)

    def test_credit(self):
        credit = self.api.credit("52fe420dc3a36847f8000441")
        self.assertEqual(credit.name, "Mark Hamill")
        self.assertEqual(credit.person_id, 2)
        self.assertEqual(credit.character, "Luke Skywalker")

    def test_discover(self):
        movies = self.api.discover_movies(with_companies=1)
        self.assertGreater(len(movies), 0)
        tv_shows = self.api.discover_tv_shows(with_companies=1)
        self.assertGreater(len(tv_shows), 0)

    def test_find(self):
        results = self.api.find_by_id(imdb_id="tt0076759")
        self.assertGreater(len(results.movie_results), 0)

    def test_genres(self):
        self.assertGreater(len(self.api.movie_genres(reload=True)), 0)
        self.assertGreater(len(self.api.tv_genres(reload=True)), 0)

    def test_keyword(self):
        keyword = self.api.keyword(4270)
        self.assertEqual(keyword.name, "galaxy")

    def test_list(self):
        test_list = self.api.create_list("PMM Test", "en", load=True)
        test_list.add_items([(524434, "movie")])
        test_list.reload()
        self.assertGreater(len(test_list), 0)
        self.assertTrue(test_list.has_item((524434, "movie")))
        test_list.remove_items([(524434, "movie")])
        self.assertFalse(test_list.has_item((524434, "movie")))
        test_list.add_items([(524434, "movie")])
        test_list.clear()
        self.assertFalse(test_list.has_item((524434, "movie")))
        test_list.reload()
        self.assertEqual(len(test_list), 0)
        test_list.delete()
        with self.assertRaises(NotFound):
            test_list.reload()
            
    def test_movie(self):
        movie = self.api.movie(11)
        self.assertEqual(movie.title, "Star Wars")
        self.assertIsInstance(self.api.latest_movie(), Movie)
        self.assertGreater(len(self.api.now_playing_movies()), 0)
        self.assertGreater(len(self.api.popular_movies()), 0)
        self.assertGreater(len(self.api.top_rated_movies()), 0)
        self.assertGreater(len(self.api.upcoming_movies()), 0)
        

    def test_network(self):
        network = self.api.network(1)
        self.assertEqual(network.name, "Fuji TV")
        
    def test_trending(self):
        self.assertGreater(len(self.api.trending("movie", "day")), 0)
        self.assertGreater(len(self.api.trending("tv", "day")), 0)
        self.assertGreater(len(self.api.trending("movie", "week")), 0)
        self.assertGreater(len(self.api.trending("tv", "week")), 0)

    def test_person(self):
        person = self.api.person(1)
        self.assertEqual(person.name, "George Lucas")
        self.assertIsInstance(self.api.latest_person(), Person)
        self.assertGreater(len(self.api.popular_people()), 0)

    def test_review(self):
        review = self.api.review("58a231c5925141179e000674")
        self.assertEqual(review.author, "Cat Ellington")

    def test_tv_show(self):
        show = self.api.tv_show(4194)
        self.assertEqual(show.name, "Star Wars: The Clone Wars")
        self.assertIsInstance(self.api.latest_tv(), TVShow)
        self.assertGreater(len(self.api.tv_airing_today()), 0)
        self.assertGreater(len(self.api.tv_on_the_air()), 0)
        self.assertGreater(len(self.api.popular_tv()), 0)
        self.assertGreater(len(self.api.top_rated_tv()), 0)

    def test_tv_season(self):
        season = self.api.tv_season(4194, 1)
        self.assertEqual(season.name, "Season 1")

    def test_tv_episode(self):
        episode = self.api.tv_episode(4194, 1, 1)
        self.assertEqual(episode.name, "Ambush")

    def test_episode_group(self):
        episode_group = self.api.episode_group("5b11ba820e0a265847002c6e")
        self.assertEqual(episode_group.name, "Chronological Order")

    def test_providers(self):
        self.assertGreater(len(self.api.provider_regions()), 0)
        self.assertGreater(len(self.api.movie_providers()), 0)
        self.assertGreater(len(self.api.tv_providers()), 0)