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

## Command line arguments
- Required arguments:
	- CCuser: username to login to classcapture.
	- CCpass: password to login to classcapture.
	- CCurl: url for classcapture
	- sftpuser: username to login to the VM hosting the API server.
	- sftppass: password to login to the VM hosting the API server.
	- sftpurl: address of VM hosting API.
- Optional flags:
	- -i, --ignoreConfig: Ignores the config.cfg when checking which files need to be updates. Will update every file instead.
	- -n, --noUpdate: Will run the AVProcessor without updating the config.cfg.

## A/V Algorithms
- These are the algorithms that will be run on the videos stored in the API server.
- Stored under Algs/ where each algorithm has it's own directory.
- To add a new algorithm:
	1. Create a subdirectory under Algs/ with the necessary files for your algorithm.
	2. Add an import to import from the Algs/\<subdirectory\>/, importing the necessary python function. The python function should take 2 parameters, the input file, and the resulting output file from the algorithm.
	3. Add an empty \_\_init\_\_.py file into the Algs/\<subdirectory\>/
	4. Add to the algs dictionary, mapping the algorithm name to the given 2 parameter function from above. For example, if I had an a file AlvinsAlg.py, which contained a function myStabilize(inname, outname). The resulting changes to AVProcessor.py would look like this:
	
	```
	# Added this import line
	from Alg/<subdirectory>/ import AlvinsAlg
	...
	algs = { 
		...
		# Added this line to the algs dict
		"AlvinsAlgorithmThingy" : AlvinsAlg.myStabilize,
		...
		}
	```
- Algorithms included:
	- TimsVstab: \<Tim put your description of the algorithm here\>
	- DirectCopy: Creates an exact copy of the video, more for testing purposes
	- DirectCopy2: Same as DirectCopy
