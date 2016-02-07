# This script will be run at a set interval (say every night at 3am)
import ConfigParser, requests, json, sys

def GetSectionsJson():
	# Start a session to save cookies 
	s = requests.Session()

	login_url = "http://classcapture.cs.illinois.edu/api/user/login"
	data = {"email":"ajou2@illinois.edu","password":"CCpassword1"}
	headers = {'Content-type': 'application/json', 'Accept': 'text/plain', 'consumer-device-id': 123}

	r = s.post(login_url, data=json.dumps(data), headers=headers)

	if r.status_code != 200:
		print "Failure to login."
		# TODO: Change this to log a failure instead of printing
		return None

	cookie = r.headers['set-cookie']
	# Move through the cookie to find the user and sails.sid
	stripped_cookie = cookie

	# Grab the user first
	user_start = stripped_cookie.index("user=") + len("user=")
	stripped_cookie = stripped_cookie[user_start:]
	user_end = stripped_cookie.index(";")
	user = stripped_cookie[:user_end]
	stripped_cookie = stripped_cookie[user_end:]

	# Grab the sails.sid
	sails_sid_start = stripped_cookie.index("sails.sid=") + len("sails.sid=")
	stripped_cookie = stripped_cookie[sails_sid_start:]
	sails_sid_end = stripped_cookie.index(";")
	sails_sid = stripped_cookie[:sails_sid_end]

	sections_url = "http://classcapture.cs.illinois.edu/api/section"
	cookies = {'user': user, 'sails.sid': sails_sid}
	headers = {'Content-type': 'application/json', 'Accept': 'text/plain', 'consumer-device-id': 123}

	r = s.get(sections_url, headers=headers)
	return r.content

print GetSectionsJson()
