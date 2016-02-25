# ClassCapture_AVProcessor
The audio video processor for interacting with the ClassCapture back end API. This contains the process AVProcessor.py, which will run every night on the secondary VM.

## Why Python
Since our audio/video processing algorithms were already being developed in Python, the most clear choice seemed to be for our processor to be written in Python as well.

## Contents of this repository
- AVProcessor.py
	- This file is the main process responsible for performing periodic processing of videos in the ClassCapture backend API.
- Logs
	- This file contains timestamped log files, with the various actions performed by the AV processor.
	- If the process runs once per night, we should get 1 file per day.
- ProcessedVideos / UnprocessedVideos
	- Both of these directories will remain empty 90% of the time, as they are temporary holding locations for files in the middle of being processed. 
	- It may be worth looking into just deleting and recreating these directories each time, but they don't hurt.
- config.cfg
	- This file is written using Python's [ConfigParser](https://docs.python.org/2/library/configparser.html) to keep track of which files have been processed, and with which algorithm.
