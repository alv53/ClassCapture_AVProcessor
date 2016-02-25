# This script will be run at a set interval (say every night at 3am)
import ConfigParser
import requests
import json
import sys
import time
import pysftp
import shutil, os

# Urls and logins
# API Server
API_url = "http://classcapture.cs.illinois.edu"
API_username = "ajou2@illinois.edu"
API_password = "CCpassword1"
# API_url = "http://classcapture.ncsa.illinois.edu"
# sftp to DL files
sftp_username = "vmuser"
sftp_password = "freshhook19"
sftp_url = "classcapture1.cs.illinois.edu"

# Delete all locally stored files in the 2 video directories
def Cleanup(folder):
	for the_file in os.listdir(folder):
		file_path = os.path.join(folder, the_file)
		try:
			if os.path.isfile(file_path):
				os.unlink(file_path)
		except Exception, e:
			print e
# Write to log in format timestampe: message
def writeToLog(message):
	currTime = time.strftime("%H:%M:%S")
	logger.write(currTime + ": " + message + "\n")

def updateConfigTime():
	# Update time
	currTime = time.strftime("%m-%d-%Y-%H:%M:%S")
	config.set('Independent Video Stabilization', 'last update', currTime)
	with open("config.cfg", "w") as configfile:
		config.write(configfile)

# Get a list of files that have not been processed by independent video stabilization
def getUnprocessedIndep(recordings):
	# Open config file (used to store update times of recordings)
	config = ConfigParser.RawConfigParser()
	config.read("config.cfg")
	processedVideos = config.get('Independent Video Stabilization', 'files').split(',')
	# Return the list of recordings not already processed
	return list(set(recordings) - set(processedVideos))

# Download file from server
def DownloadVideo(filename):
	writeToLog("Performing download for file: " + filename)
	path = "classcapture_videos/" + filename
	localpath = "UnprocessedVideos/" + filename
	with pysftp.Connection(sftp_url, username=sftp_username, password=sftp_password) as sftp:
		# Put file into UnprocessedVideos/ directory
		sftp.get(path, localpath)
		writeToLog("\tCompleted download for file: " + filename)

# Process video, stored in UnprocessedVideos/ and puts results in ProcessedVideos/
def ProcessVideo(filename):
	#TODO: Tim put your algorithm for independent video stabilization here.
	writeToLog("Performing stabilization for file: " + filename)
	shutil.copyfile("UnprocessedVideos/" + filename, "ProcessedVideos/" + filename)
	writeToLog("\tCompleted stabilization for file: " + filename)
	
# Update video in API
def UpdateVideo(filename):
	writeToLog("Performing update for file: " + filename)
	config = ConfigParser.RawConfigParser()
	config.read("config.cfg")
	processedVideos = config.get('Independent Video Stabilization', 'files').split(',')
	print processedVideos
	# If there are no files, just make the config value the current file, else append the file to the list
	if len(processedVideos) == 1 and processedVideos[0] == '':
		processedVideos = [filename]
	else:
		processedVideos.append(filename)
	config.set('Independent Video Stabilization', 'files', ','.join(processedVideos))
	with open('config.cfg', 'w+') as configfile:
		config.write(configfile)
	writeToLog("\tCompleted update for file: " + filename)

# Login with a valid classcapture account
def LoginToCC():
	writeToLog("Attempting to login to ClassCapture")
	login_url = API_url + "/api/user/login"
	data = {"email":API_username ,"password":API_password}
	headers = {'Content-type': 'application/json', 'Accept': 'text/plain', 'consumer-device-id': 123}
	r = s.post(login_url, data=json.dumps(data), headers=headers)

	# Check for correct login
	if r.status_code != 200:
		writeToLog("Failure to login to " + API_url)
		return False
	writeToLog("\tLogged into " + API_url)
	return True

def GetRecordingsJson():
	# Grab all of the recordings from classcapture
	recordings_url = API_url + "/api/recording"
	headers = {'Content-type': 'application/json', 'Accept': 'text/plain', 'consumer-device-id': 123}
	r = s.get(recordings_url, headers=headers)
	return r.content

# Start a session to save cookies 
s = requests.Session()
# Setup logging
logfile = time.strftime("%m-%d-%Y-%H:%M:%S")
# logging.basicConfig(filename='Logs/' + logfile + '.log', level=logging.DEBUG)
logger = open('Logs/' + logfile + ".log", 'w')
# Login to classcapture
loggedIn = LoginToCC()
if loggedIn:
	# Get all of the recording
	recordings = json.loads(GetRecordingsJson())
	# First we will run independent video stabilization on videos that have not been processed before
	videos = [recording['filename'] for recording in recordings]
	videos = getUnprocessedIndep(videos)
	writeToLog("Will now download, process, and update " + str(len(videos)) + " files")
	# Three seperate loops to make log file cleaner (all the downloads + all the processing + all the updating)
	# Download videos
	for video in videos:
		DownloadVideo(video)
	# Process videos
	for video in videos:
		ProcessVideo(video)
	# Update videos in API
	for video in videos:
		UpdateVideo(video)
	Cleanup('ProcessedVideos')
	Cleanup('UnprocessedVideos')
