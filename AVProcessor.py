# This script will be run at a set interval (say every night at 3am)
import ConfigParser
import requests
import json
import sys
import time
import pysftp
import shutil, os
from argparse import ArgumentParser

# command line flag parser
parser = ArgumentParser()
parser.add_argument("--CCuser", dest="API_username", help="Username to login to ClassCapture")
parser.add_argument("--CCpass", dest="API_password", help="Password to login to ClassCapture")
parser.add_argument("--sftpuser", dest="sftp_username", help="Username to login to VM hosting API")
parser.add_argument("--sftppass", dest="sftp_password", help="Password to login to VM hosting API")
parser.add_argument("-c", "--clearConfig", action="store_const", const=True, help="Clears local config for which videos have been processed")
parser.add_argument("-i", "--ignoreConfig", action="store_const", const=True, help="Clears local config for which videos have been processed")
parser.add_argument("-n", "--noUpdate", action="store_const", const=True, help="Clears local config for which videos have been processed")
args = parser.parse_args()

if args.clearConfig:
	print "Clearing local config"
	#TODO: Clear local config :)
	sys.exit()

# Urls and logins
# API Server
API_url = "http://classcapture.cs.illinois.edu"
API_username =  args.API_username
API_password =  args.API_password
# API_url = "http://classcapture.ncsa.illinois.edu"
# sftp to DL files
sftp_username = args.sftp_username
sftp_password = args.sftp_password
sftp_url = "classcapture1.cs.illinois.edu"

if API_username is None or API_password is None or sftp_username is None or sftp_password is None:
	print "Make sure to pass in login information for ClassCapture and the sftp destination"
	sys.exit()

# Delete all locally stored files in the 2 video directories
def Cleanup(fileToDelete):
	# delete ProcessedVideos/*file*
	writeToLog("Cleanup for " + fileToDelete)
	try:
		filename = "ProcessedVideos/" + fileToDelete
		if os.path.isfile(filename):
			os.remove(filename)
			writeToLog("\tDeleted " + fileToDelete + " from ProcessedVideos.")
	except Exception, e:
		print e
		writeToLog("\tFailed to delete " + fileToDelete + " from ProcessedVideos.")
	# delete UnprocessedVideos/*file*
	try:
		filename = "UnprocessedVideos/" + fileToDelete
		if os.path.isfile(filename):
			os.remove(filename)
			writeToLog("\tDeleted " + fileToDelete + " from UnprocessedVideos.")
	except Exception, e:
		print e
		writeToLog("\tFailed to delete " + fileToDelete + " from UnprocessedVideos.")
# Write to log in format timestampe: message
def writeToLog(message):
	currTime = time.strftime("%H:%M:%S")
	logMsg = currTime + ": " + message
	logger.write(logMsg + "\n")
	print logMsg

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
	writeToLog("Performing stabilization for file: " + filename)
	#TODO: Tim put your algorithm for independent video stabilization here.
	shutil.copyfile("UnprocessedVideos/" + filename, "ProcessedVideos/" + filename)
	writeToLog("\tCompleted stabilization for file: " + filename)
	
# Update video in API
def UpdateVideo(filename):
	writeToLog("Performing update for file: " + filename)

	# sftp in and update video
	localpath = "ProcessedVideos/" + filename
	with pysftp.Connection(sftp_url, username=sftp_username, password=sftp_password) as sftp:
		with sftp.cd('classcapture_videos/'):
			sftp.put(localpath)
			writeToLog("\tUploaded to API, file: " + filename)

	#Update config
	config = ConfigParser.RawConfigParser()
	config.read("config.cfg")
	processedVideos = config.get('Independent Video Stabilization', 'files').split(',')
	# If there are no files, just make the config value the current file, else append the file to the list
	if len(processedVideos) == 1 and processedVideos[0] == '':
		processedVideos = [filename]
	else:
		processedVideos.append(filename)
	config.set('Independent Video Stabilization', 'files', ','.join(processedVideos))
	# Update time
	currTime = time.strftime("%m-%d-%Y-%H:%M:%S")
	config.set('Independent Video Stabilization', 'last update', currTime)
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
logger = open('Logs/' + logfile + ".log", 'w+')
# Login to classcapture
loggedIn = LoginToCC()
if loggedIn:
	# Get all of the recording
	recordings = json.loads(GetRecordingsJson())
	# First we will run independent video stabilization on videos that have not been processed before
	videos = [recording['filename'] for recording in recordings]
	videos = getUnprocessedIndep(videos)
	writeToLog("Will now download, process, and update " + str(len(videos)) + " files")
	for video in videos:
		# Download videos
		DownloadVideo(video)
		# Process videos
		ProcessVideo(video)
		# Update videos in API
		UpdateVideo(video)
		# delete unprocessed and processed videos
		Cleanup(video)
logger.close()
