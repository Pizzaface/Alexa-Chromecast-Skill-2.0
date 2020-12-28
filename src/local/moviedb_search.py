import urllib
import json
import requests
import os
import logging

MOVIEDB_API_KEY = os.getenv("MOVIEDB_API_KEY", False)
MOVIEDB_API_URI = "https://api.themoviedb.org/3"

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = False

def moviedb_search_movies(movie):
    if not MOVIEDB_API_KEY:
        logger.error('You need to set a moviedb API key. e.g. export MOVIEDB_API_KEY=xxxxxx')
        logger.error('You can request this at: %s' % MOVIEDB_API_URI)
        raise Exception("No MovieDb API Key")

    query = {
        "api_key": MOVIEDB_API_KEY,
        "language": 'es-ES',
        "query": movie,
        "page": 1,
        "include_adult": False
    }

    uri = "{}/search/movie?{}".format(MOVIEDB_API_URI, urllib.parse.urlencode(query))

    r = requests.get(uri)
    response = r.json()

    if response["total_results"] > 0:
        first_result = response["results"][0]
        return first_result
    else:
        raise Exception("No Results")

def moviedb_search_movie_videos(moviedb_id):
    query = {
        "api_key": MOVIEDB_API_KEY,
        "language": 'es-ES'
    }
    url = "{}/movie/{}/videos?{}".format(MOVIEDB_API_URI, moviedb_id, urllib.parse.urlencode(query))
    r = requests.get(url)
    response = r.json()

    print (url, response)

    try:
        return response["results"][0]["key"]
    except Exception as err:
        logger.exception('Unexpected error parsing MovieDb response')
        raise err


def get_movie_trailer_youtube_id(movie_name):
    moviedb_movie = moviedb_search_movies(movie_name)
    youtube_id = moviedb_search_movie_videos(moviedb_movie["id"])
    return {
        "youtube_id": youtube_id,
        "title": moviedb_movie["title"]
    }

