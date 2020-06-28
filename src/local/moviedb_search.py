#!/usr/bin/env python3

import urllib
import json
import requests
import os

MOVIEDB_API_KEY = os.getenv("MOVIEDB_API_KEY", False)
MOVIEDB_API_URI = "https://api.themoviedb.org/3"


def moviedb_search_movies(movie):
    if not MOVIEDB_API_KEY:
        print('You need to set a moviedb API key. e.g. export MOVIEDB_API_KEY=xxxxxx')
        print('You can request this at: %s' % MOVIEDB_API_URI)

    query = {
        "api_key": MOVIEDB_API_KEY,
        "language": 'en-GB',
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
        "language": 'en-GB'
    }
    url = "{}/movie/{}/videos?{}".format(MOVIEDB_API_URI, moviedb_id, urllib.parse.urlencode(query))
    r = requests.get(url)
    response = r.json()

    print (url, response)

    try:
        return response["results"][0]["key"]
    except:
        print(response, MOVIEDB_API_KEY)
        raise Exception()


def get_movie_trailer_youtube_id(movie_name):
    moviedb_movie = moviedb_search_movies(movie_name)
    youtube_id = moviedb_search_movie_videos(moviedb_movie["id"])
    return {
        "youtube_id": youtube_id,
        "title": moviedb_movie["title"]
    }

def main():
    try:
        trailer = get_movie_trailer_youtube_id("The Big Lebowski")
        print(trailer)
    except Exception as e:
        print(e)

if __name__ == "__main__": main()
