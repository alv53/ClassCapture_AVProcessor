# This script will be run at a set interval (say every night at 3am)
import ConfigParser, requests, json, sys

# Replace this with live url when deploying
API_url = "http://classcapture.cs.illinois.edu"

def GetSectionsJson():
	# Start a session to save cookies 
	s = requests.Session()
	
	# Login with a valid classcapture account
	login_url = API_url + "/api/user/login"
	data = {"email":"ajou2@illinois.edu","password":"CCpassword1"}
	headers = {'Content-type': 'application/json', 'Accept': 'text/plain', 'consumer-device-id': 123}
	r = s.post(login_url, data=json.dumps(data), headers=headers)

	# Check for correct login
	if r.status_code != 200:
		print "Failure to login."
		# TODO: Change this to log a failure instead of printing
		return None

	# Grab all of the sections from classcapture
	sections_url = API_url + "/api/section"
	r = s.get(sections_url, headers=headers)
	return r.content

print GetSectionsJson()
