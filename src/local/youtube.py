import time
import subprocess
import json

def search(video_title):
    
    results = []
    #is_playlist = 'playlist' in video_title
    video_ids = subprocess.run(['youtube-dl','-j','ytsearch2:%s' % video_title], stdout=subprocess.PIPE)

    for video in video_ids.stdout.splitlines():
        video = json.loads(video)
        
        results.append({'id': video['id'], 'playlist_id': False})

    #Haven't figured out how to detect a playlist

    return results
