import pychromecast
import pymysql
import os
import subprocess
import re
import sched, time
from subprocess import call
from decimal import *
from difflib import SequenceMatcher
from threading import Thread

conn = pymysql.connect("RASP_PI_DNS", user="MYSQL_USER", passwd="MYSQL_PASS", db="DB_NAME")
chromecast_name = "YOUR_CHROMECAST_NAME"
def setup(chromecast_name):
	chromecastList = list(pychromecast.get_chromecasts_as_dict().keys())
	if chromecastList == []:
		print("Shit, we didn't find any Chromecasts...")
		setup(chromecast_name)
	else:
		print ("Found ChromeCast: " + str(chromecastList))

	
	cast = pychromecast.get_chromecast(friendly_name=chromecast_name)

setup("YOUR_CHROMECAST_NAME")

def sendVideo(url):
	try:
		goThrough = False
	except:
		pass
	try:
		cast.wait()
	except:
		print ("There was a problem connecting to the Chromecast.")
		setup(chromecast_name)
		return "error"
	else:
		mc = cast.media_controller
		p = subprocess.check_output("youtube-dl -g " + url, shell=True)
		mc.play_media(p, 'video/mp4')
		print ("Video sent to Chromecast!")
		return "success"
def dbConnect():
	cur = conn.cursor()

	cur.execute("SELECT * FROM commands ORDER BY TIMESTAMP DESC LIMIT 1 ;")

	for row in cur.fetchall():
	    if row[1] == "play":
	    	url = row[2]
	    	print ("user wants to watch: " + url)
	    	idOfQuert = row[0]
	    	status = sendVideo(url)

	    if row[1] == "pause":
	    	idOfQuert = row[0]
	    	print("user wants to pause playback")
	    	status = pauseVideo()

	    if row[1] == "resume":
	    	idOfQuert = row[0]
	    	print("user wants to resume playback")
	    	status = resumeVideo()	

	    if row[1] == "volume":
	    	idOfQuert = row[0]
	    	volume = row[2]
	    	print("user wants to set volume to " + str(volume))
	    	status = volumeSet(volume)	

	    if row[1] == "connectToChromeCast":
	    	idOfQuert = row[0]
	    	castName = row[2]
	    	print("user wants to switch to Chromecast: " + castName)
	    	status = setup(chromecast_name)(castName)

	    if row[1] == "gPlayMusic":
	    	idOfQuert = row[0]
	    	songName = row[2]
	    	type_of_media = row[3]
	    	print("user wants to play song: " + songName)
	    	status = gpMusicPlaySong(songName, type_of_media)
	    	if status == "errorNoSong":
	    		cur.execute("DELETE FROM commands WHERE id=" + str(idOfQuert))
	    		print("Song Deleted, since we can't find it.")

		if status == "success":
			cur.execute("DELETE FROM commands WHERE id=" + str(idOfQuert))
			print("Command Completed.")

while True:
    dbConnect()
    time.sleep(2)


