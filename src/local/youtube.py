import time
from youtube_search import YoutubeSearch

def search(video_title):
    attempts = 4
    results = []
    is_playlist = 'playlist' in video_title

    for _attempt in range(attempts):
        #Not found - sometimes we get an empty list - so try again
        results = YoutubeSearch(video_title, max_results=20)
        if len(results.videos) > 0:
            results = results.videos
            break
        time.sleep(2)

    for video in results:
        if '&list' in video['id']:
            vals = video['id'].split('&')
            video['id'] = vals[0]
            video['playlist_id'] = vals[1].replace('list=', '')
        else:
            video['playlist_id'] = None

    #Ok if the search was a playlist, or the the first result was a playlist just return this
    if is_playlist or (len(results) > 0 and results[0]['playlist_id']):
        results = next(([x] for x in results if x['playlist_id']), [])

    return results
