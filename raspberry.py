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

# Default ChromeCast Name
chromecast_name = "CHROMECAST_NAME"

#Connect String
db = pymysql.connect("RASP_PI_DNS", user="MYSQL_USER", passwd="MYSQL_PASS", db="DB_NAME")

#Sets up The Chromecast For Use (Will Run any time there is an issue connecting to the Chromecast)
def setup(chromecast_name):
	chromecastList = list(pychromecast.get_chromecasts_as_dict().keys())
	if chromecastList == []:
		print("We didn't find any Chromecasts...")
		setup(chromecast_name)
	else:
		print ("Found ChromeCast: " + str(chromecastList))

	
	cast = pychromecast.get_chromecast(friendly_name=chromecast_name)

#Runs Inital Setup for Default Chromecast
setup(chromecast_name)

#Send Video Function
def sendVideo(url):
	#Tries to wait until the Chromecast is ready (Simply Tests for Chromecast Connection)
	try:
		cast.wait()
	except:
		print ("There was a problem connecting to the Chromecast.")
		setup(chromecast_name)
		return "error"
	else:
		#Sets up the Chromecast's Media Controller
		mc = cast.media_controller
		#Uses Youtube-Dl to get the Stream URL for the Video to send to Chromecast
		p = subprocess.check_output("youtube-dl -g -- " + url, shell=True)
		#Sends the Video
		mc.play_media(p, 'video/mp4')
		print ("Video sent to Chromecast!")
		return "success"


def volumeSet(Volnum):
	try:
		cast.wait()
	except:
		print ("There was a problem connecting to the Chromecast.")
		setup(chromecast_name)
		return "error"
	else:
		#Tries to wait until the Chromecast is ready (Simply Tests for Chromecast Connection)
		mc = cast.media_controller
		#Set's the Decimal Modules Rounding
		getcontext().prec = 3
		#Puts the Volume into something the ChromeCast can Understand
		actual_volume = Decimal(int(Volnum)) / Decimal(100)
		#Converts it to a float
		actual_volume = float(actual_volume)

		#Sends the set volume command to the Chromecast
		cast.set_volume(actual_volume)
		print ("Volume set to: " + str(Decimal(int(Volnum)) / Decimal(100)))
		return "success"


def pauseVideo():
	try:
		cast.wait()
	except:
		print ("There was a problem connecting to the Chromecast.")
		setup(chromecast_name)
		return "error"
	else:
		mc = cast.media_controller

		#Sends Pause Command To Chromecast
		mc.pause()
		print ("Video Paused.")
		return "success"



def resumeVideo():
	try:
		cast.wait()
	except:
		print ("There was a problem connecting to the Chromecast.")
		setup(chromecast_name)
		return "error"
	else:
		mc = cast.media_controller

		#Resumes Playback
		mc.play()
		print ("Video Resumed.")
		return "success"

def dbConnect():

	#Set's up the connection to run commands
	cur = db.cursor()

	#MySQL Query that selects the most recent command
	cur.execute("SELECT * FROM commands ORDER BY TIMESTAMP DESC LIMIT 1 ;")

	#Loops through the row to see what command it was to send it to the right function
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

		if status == "success":
			#Deletes the Row when Done
			cur.execute("DELETE FROM commands WHERE id=" + str(idOfQuert))
			print("Command Completed.")

#Loops Continuously to get new commands.
while True:
    dbConnect()
    time.sleep(2)


