from datetime import datetime

from .objs.simple import Language, Country
from .exceptions import Invalid

discover_movie_options = [
    "region", "sort_by", "certification_country", "certification", "certification.lte",
    "certification.gte", "include_adult", "include_video", "primary_release_year",
    "primary_release_date.gte", "primary_release_date.lte", "release_date.gte", "release_date.lte",
    "with_release_type", "year", "vote_count.gte", "vote_count.lte", "vote_average.gte", "vote_average.lte",
    "with_cast", "with_crew", "with_people", "with_companies", "with_genres", "without_genres",
    "with_keywords", "without_keywords", "with_runtime.gte", "with_runtime.lte", "with_original_language",
    "with_watch_providers", "watch_region", "with_watch_monetization_types"
]

discover_movie_sort_options = [
    "popularity.asc", "popularity.desc", "release_date.asc", "release_date.desc", "revenue.asc", "revenue.desc",
    "primary_release_date.asc", "primary_release_date.desc", "original_title.asc", "original_title.desc",
    "vote_average.asc", "vote_average.desc", "vote_count.asc", "vote_count.desc"
]

discover_tv_options = [
    "sort_by", "air_date.gte", "air_date.lte", "first_air_date.gte", "first_air_date.lte", "first_air_date_year",
    "timezone", "vote_average.gte", "vote_average.lte", "vote_count.gte", "vote_count.lte", "with_genres",
    "with_networks", "without_genres", "with_runtime.gte", "with_runtime.lte", "include_null_first_air_dates",
    "with_original_language", "without_keywords", "screened_theatrically", "with_companies", "with_keywords",
    "with_watch_providers", "watch_region", "with_watch_monetization_types"
]

discover_tv_sort_options = [
    "popularity.asc", "popularity.desc", "first_air_date.desc",
    "first_air_date.asc", "vote_average.asc", "vote_average.desc"
]

v3_sorts = ["created_at.asc", "created_at.desc"]
v4_movie_sorts = ["created_at.asc", "created_at.desc", "release_date.asc", "release_date.desc",
                  "title.asc", "title.desc", "vote_average.asc", "vote_average.desc"]
v4_show_sorts = ["created_at.asc", "created_at.desc", "first_air_date.asc", "first_air_date.desc",
                 "name.asc", "name.desc", "vote_average.asc", "vote_average.desc"]
v4_list_sorts = ["original_order.asc", "original_order.desc", "vote_average.asc", "vote_average.desc",
                 "primary_release_date.asc", "primary_release_date.desc", "title.asc", "title.desc"]

def validate_sort(sort_by, v3, is_movie):
    if not sort_by:
        return None
    elif v3 and sort_by not in v3_sorts:
        raise Invalid(f"sort_by not in {v3_sorts}")
    elif not v3 and is_movie and sort_by not in v4_movie_sorts:
        raise Invalid(f"sort_by not in {v4_movie_sorts}")
    elif not v3 and not is_movie and sort_by not in v4_show_sorts:
        raise Invalid(f"sort_by not in {v4_show_sorts}")
    else:
        return sort_by

def validate_items(items, comment=False):
    json = {"items": []}
    for item in items:
        if "media_type" not in item or "media_id" not in item or item["media_type"] not in ["movie", "tv"] or \
                (comment and "comment" not in item):
            error = "'media_type', 'media_id', and 'comment'" if comment else "'media_type' and 'media_id'"
            raise Invalid(f"Each object must have {error}. 'media_type' must be either 'movie' or 'tv'")
        json["items"].append({"media_type": item["media_type"], "media_id": int(item["media_id"])})
    return json

def validate_language(language, languages):
    if isinstance(language, Language):
        return language.iso_639_1
    elif str(language).lower() in languages:
        return str(language).lower()
    else:
        raise Invalid(f"Language: {language} is invalid see Configuration.languages for the options.")

def validate_country(country, countries):
    if not country:
        return None
    elif isinstance(country, Country):
        return country.iso_3166_1
    elif str(country).lower() in countries:
        return str(country).lower()
    else:
        raise Invalid(f"Country: {country} is invalid see Configuration.countries for the options.")

def validate_discover(is_movie, **kwargs):
    validated = {}
    for k, v in kwargs.items():
        if is_movie and k not in discover_movie_options or not is_movie and k not in discover_tv_options:
            raise Invalid(f"{k} is not a valid parameter")
        elif k == "sort_by":
            if is_movie and v not in discover_movie_sort_options or not is_movie and v not in discover_tv_sort_options:
                raise Invalid(f"{v} is not a valid sort_by option")
            validated[k] = v
        elif k == "region":
            if len(v) != 2:
                raise Invalid(f"{v} is not a region option it can only be two characters")
            validated[k] = str(v).upper()
        elif k == "certification_country":
            if "certification" not in kwargs and "certification.lte" not in kwargs and "certification.gte" not in kwargs:
                raise Invalid("certification_country must be used with either certification, certification.lte, or certification.gte")
            validated[k] = str(v)
        elif k in ["certification", "certification.lte", "certification.gte"]:
            if "certification_country" not in kwargs:
                raise Invalid("certification must be used with certification_country")
            validated[k] = str(v)
        elif k in ["include_adult", "include_video", "include_null_first_air_dates", "screened_theatrically"]:
            if not isinstance(v, bool):
                raise Invalid(f"{k} must be either True or False")
            validated[k] = v
        elif k in ["primary_release_date.gte", "primary_release_date.lte", "release_date.gte", "release_date.lte",
                   "air_date.gte", "air_date.lte", "first_air_date.gte", "first_air_date.lte"]:
            if isinstance(v, datetime):
                date_obj = v
            else:
                try:
                    date_obj = datetime.strptime(str(v), "%Y-%m-%d")
                except ValueError:
                    raise Invalid(f"{k} must be a datetime object or match pattern YYYY-MM-DD (e.g. 2020-12-25)")
            validated[k] = datetime.strftime(date_obj, "%Y-%m-%d")
        elif k in ["primary_release_year", "first_air_date_year", "vote_count.gte", "vote_count.lte",
                   "with_runtime.gte", "with_runtime.lte"]:
            if not isinstance(v, int) or v < 1:
                raise Invalid(f"{k} must be an integer greater then 0")
            validated[k] = v
        elif k in ["vote_average.gte", "vote_average.lte"]:
            if not isinstance(v, float) or v < 1:
                raise Invalid(f"{k} must be a number greater then 0.0")
            validated[k] = v
        elif k == "with_watch_monetization_types":
            if "watch_region" not in kwargs:
                raise Invalid("with_watch_monetization_types must be used with watch_region")
            if v not in ["flatrate", "free", "ads", "rent", "buy"]:
                raise Invalid(f"{v} is not a valid with_watch_monetization_types option. Options: [flatrate, free, ads, rent, or buy]")
            validated[k] = v
        else:
            validated[k] = ",".join([str(x) for x in v]) if isinstance(v, list) else str(v)
    return validated

def validate_date(data, date_format="%Y-%m-%d"):
    if not data:
        return None
    elif isinstance(data, datetime):
        return data.strftime(date_format)
    else:
        try:
            return datetime.strptime(str(data), date_format).strftime(date_format)
        except ValueError:
            raise Invalid(f"date: {data} must be a datetime or in the format YYYY-MM-DD")
