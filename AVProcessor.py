# Modules used for the scheduler
import ConfigParser
import requests
import json
import sys
import time
import pysftp
import os
import shutil
from argparse import ArgumentParser

# Modules for AV processing here
from Algs.TimsVstab import vstab
from Algs.DirectCopy import DirectCopy
from Algs.DirectCopy2 import DirectCopy2

# List of algoritms here
# direct_copy and direct_copy2 are test algorithms. Delete when we have more working algorithms
algs = {
        #"Vstab" : vstab.stab,
        "direct_copy" : DirectCopy.createCopy,
        "direct_copy2" : DirectCopy2.createCopyTwo,
        }

# Command line flag parser
parser = ArgumentParser()
parser.add_argument("--CCuser", dest="API_username", help="Username to login to ClassCapture")
parser.add_argument("--CCpass", dest="API_password", help="Password to login to ClassCapture")
parser.add_argument("--CCurl", dest="API_url", help="ClassCapture URL")
parser.add_argument("--sftpuser", dest="sftp_username", help="Username to login to VM hosting API")
parser.add_argument("--sftppass", dest="sftp_password", help="Password to login to VM hosting API")
parser.add_argument("--sftpurl", dest="sftp_url", help="address to login to VM hosting API")
parser.add_argument("-i", "--ignoreConfig", action="store_const", const=True, help="Ignores the config.cfg when checking which files need to be updates. Will update every file instead.")
parser.add_argument("-n", "--noUpdate", action="store_const", const=True, help="Will run the AVProcessor without updating the config.cfg.")
args = parser.parse_args()

# Parse command line flags
ignoreConfig = args.ignoreConfig if args.ignoreConfig else False
noUpdate = args.noUpdate if args.noUpdate else False
# Urls and logins
# API Server
API_username =  args.API_username
API_password =  args.API_password
API_url = args.API_url
# sftp to DL files
sftp_username = args.sftp_username
sftp_password = args.sftp_password
sftp_url = args.sftp_url

# Verify that all required flags are provided
if API_username is None or API_password is None or API_url is None or sftp_username is None or sftp_password is None or sftp_url is None:
    print "Make sure to pass in login information for ClassCapture and the sftp destination"
    sys.exit()

# Delete all locally stored files in the 2 video directories
def Cleanup(fileToDelete):
    # delete ProcessedVideos/*file*
    WriteToLog("Cleanup for " + fileToDelete)
    try:
        filename = "ProcessedVideos/" + fileToDelete
        if os.path.isfile(filename):
            os.remove(filename)
            WriteToLog("\tDeleted " + fileToDelete + " from ProcessedVideos.")
    except Exception, e:
        print e
        WriteToLog("\tFailed to delete " + fileToDelete + " from ProcessedVideos.")
    # delete UnprocessedVideos/*file*
    try:
        filename = "UnprocessedVideos/" + fileToDelete
        if os.path.isfile(filename):
            os.remove(filename)
            WriteToLog("\tDeleted " + fileToDelete + " from UnprocessedVideos.")
    except Exception, e:
        print e
        WriteToLog("\tFailed to delete " + fileToDelete + " from UnprocessedVideos.")
# Write to log in format timestampe: message
def WriteToLog(message):
    currTime = time.strftime("%H:%M:%S")
    logMsg = currTime + ": " + message
    logger.write(logMsg + "\n")
    print logMsg

# Get a list of files that have not been processed by independent video stabilization
def GetUnprocessed(algName, recordings):
    # If the ignoreConfig flag is true or there is no config file, we will process all videos
    config = ConfigParser.RawConfigParser()
    config.read("config.cfg")
    if ignoreConfig or not config.has_section(algName):
        return recordings
    # Open config file (used to store update times of recordings)
    processedVideos = config.get(algName, 'files').split(',')
    # Return the list of recordings not already processed
    return list(set(recordings) - set(processedVideos))

# Download file from server
def DownloadVideo(filename):
    WriteToLog("Performing download for file: " + filename)
    path = "classcapture_videos/" + filename
    localpath = "UnprocessedVideos/" + filename
    with pysftp.Connection(sftp_url, username=sftp_username, password=sftp_password) as sftp:
        # Put file into UnprocessedVideos/ directory
        sftp.get(path, localpath)
        WriteToLog("\tCompleted download for file: " + filename)

# Process video, stored in UnprocessedVideos/ and puts results in ProcessedVideos/
def ProcessVideo(filename, algName, algFn):
    WriteToLog("Performing " + algName +" for file: " + filename)
    algFn('UnprocessedVideos/' + filename, 'ProcessedVideos/' + filename)
    #uncomment the bottom line and comment the above to have no processing done, just copy uploaded
    WriteToLog("\tCompleted " + algName + " for file: " + filename)

# Update video in API
def UpdateVideo(filename, algName):
    WriteToLog("Performing update for " + algName + " on file: " + filename)

    # sftp in and update video
    localpath = "ProcessedVideos/" + filename
    with pysftp.Connection(sftp_url, username=sftp_username, password=sftp_password) as sftp:
        with sftp.cd('classcapture_videos/'):
            sftp.put(localpath)
            WriteToLog("\tUploaded to API, file: " + filename)

    #Update config
    config = ConfigParser.RawConfigParser()
    config.read("config.cfg")
    if not config.has_section(algName):
        config.add_section(algName)
        config.set(algName, 'files', '')
        config.set(algName, 'last update', '')
    processedVideos = config.get(algName, 'files').split(',')
    # If there are no files, just make the config value the current file, else append the file to the list
    if len(processedVideos) == 1 and processedVideos[0] == '':
        processedVideos = [filename]
    else:
        processedVideos.append(filename)

    config.set(algName, 'files', ','.join(processedVideos))
    # Update time
    currTime = time.strftime("%m-%d-%Y-%H:%M:%S")
    if not noUpdate:
        config.set(algName, 'last update', currTime)
        with open('config.cfg', 'w+') as configfile:
            config.write(configfile)
    WriteToLog("\tCompleted update for file: " + filename)

# Login with a valid classcapture account
def LoginToCC():
    WriteToLog("Attempting to login to ClassCapture")
    login_url = API_url + "/api/user/login"
    data = {"email":API_username ,"password":API_password}
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain', 'consumer-device-id': 123}
    r = s.post(login_url, data=json.dumps(data), headers=headers)

    # Check for correct login
    if r.status_code != 200:
        WriteToLog("Failure to login to " + API_url)
        return False
    WriteToLog("\tLogged into " + API_url)
    return True

def GetRecordingsJson():
    # Grab all of the recordings from classcapture
    recordings_url = API_url + "/api/recording"
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain', 'consumer-device-id': 123}
    r = s.get(recordings_url, headers=headers)
    return r.content
# Create directories for local video processing
if not os.path.exists("ProcessedVideos"):
    os.makedirs("ProcessedVideos")
if not os.path.exists("UnprocessedVideos"):
    os.makedirs("UnprocessedVideos")

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
    allvideos = [recording['filename'] for recording in recordings]
    for name,alg in algs.iteritems():
        videos = GetUnprocessed(name, allvideos)
        WriteToLog("Will now perform " + str(name) + " on " + str(len(videos)) + " files.")
        for video in videos:
            # Download videos
            DownloadVideo(video)
            # Process videos
            ProcessVideo(video, name, alg)
            # Update videos in API
            UpdateVideo(video, name)
            # delete unprocessed and processed videos
            Cleanup(video)
logger.close()
# delete temp folders
shutil.rmtree("ProcessedVideos")
shutil.rmtree("UnprocessedVideos")
