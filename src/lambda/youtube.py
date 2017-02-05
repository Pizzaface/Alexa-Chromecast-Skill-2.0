#!/usr/bin/env python

from urllib import quote
import os
import requests

YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', 'AIzaSyB4DdmAkhKtJ6NMgSJIgMCFkVJ8KD1uBk0')
YOUTUBE_API_URI = "https://www.googleapis.com/youtube/v3/search?q={}&key={}&part=snippet&type=video"

def search(video):
    uri = YOUTUBE_API_URI.format(quote(video.encode("utf8")), YOUTUBE_API_KEY)
    response = requests.get(uri)
    result = response.json()["items"][0]

    return {
        "id": result["id"]["videoId"],
        "title": result["snippet"]["title"]
    }

