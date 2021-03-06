# The back-end file for the Honeypot Analyzer.
# This program reads in records from a HoneyD log file,
# parses them, and sends them to our web application over HTTPS.
#
# Command line usage:
#       python parser.py 
#
#	Arguments:
#		--user <username> 
#			What's your username on our website?
#		--log <logfile name> 
#		--update <True or False>
#		--static <True or False>
#	   
# You can find out more about HoneyD here: http://www.honeyd.org
#
# Authors: 
# 	Thai-Son Le
# 	Stephen Antalis
# 	Stephen Finney

import argparse
import csv
import json
import os
import requests
from time import time


def process_args():
	"""Returns the values of the command line arguments from the user."""
	
	# A small description of the application for the manual
	about_app = 'Process a HoneyD log file and send it to a database.'


	# Parse the command line arguments (if specified) and 
	# assign their values to some variables.
	arg_parser = argparse.ArgumentParser(description = about_app)


	# The list of arguments to add to the program.
	# Current list:
	#	User name		- The user's name on the website
	#	Log filename		- The logfile's name
	#	Static file boolean 	- Is this log static, i.e. not being updated by HoneyD?
	#	Update file boolean	- Is this file an update of a previously entered log?
	arg_list = [ 
		     ['--user', str, 'user', 'the user\'s name. Default: user'],
		     ['--log', str, 'logfile.log', 'the log file\'s name. Default: logfile.log'],
		     ['--update', bool, False, 'is this an update of an earlier log file? Default: False'],
		     ['--static', bool, True, 'is this log file static? If HoneyD is updating this file, choose False. Default: True'],
	           ]

	for arg in arg_list:
		arg_parser.add_argument(arg[0], type=arg[1], default=arg[2], help=arg[3])


	# Parse and retrieve the command line arguments given.
	args = vars( arg_parser.parse_args() )

	# The parser returns the arguments in this particular order.
	update_bool, static_bool, user_name, log_name = args.values()

	# Let's return the arguments like this; it makes more sense
	return user_name, log_name, static_bool, update_bool


def process_log(log_name, user_name, last_update = 0):
	"""
	Processes the log entries and inserts them into the database.
	
	Keyword arguments:
	log_name    -- The log file's name.
	user_name   -- The user's name on the website.
	last_update -- The last update of this logfile, if it exists.
	"""

	# The below information is needed for the HTTP POST request
	post_log_name = log_name.split('/')[-1]

	url = 'http://localhost:3000/users/logs/entries/create_many.json'
	headers = {'content-type': 'application/json'}
	user_email = "test@test.com"

	new_log = {"name":post_log_name, "user_email":user_email}

	make_log = requests.post('http://localhost:3000/users/logs.json',
				data=json.dumps( new_log, separators=(',', ': ') ), 
				headers=headers)

	if make_log.status_code not in (200,201):
		print("There was a problem creating the new log file. Try again later.")
		print("HTTP status code: " + str(make_log.status_code))
		return
	
	with open(log_name, 'r') as log:

		# Seek to position of last update
		# If last update is the end of the file, quit.
		if log.seek(os.SEEK_END) == last_update:
			return last_update
		else:
			log.seek(last_update)

		
		# Time this function's runtime
		start = time()
		
		csv_data = csv.reader(log, delimiter=' ')

		# Each batch of entries is an array
		batch = []
		
		for row in csv_data:

			# Each entry is a dictionary
			entry = {}
						
			if "honeyd" in row[1]:
				continue

			else:
				# Do the parsing common to all protocol types
				entry["date"], entry["time"] = rreplace(row[0], '-', ' ', 1).split()
				
				entry["conn_type"], entry["src_ip"] = row[2:4]

				if '[' in row[-1]:
					entry["environment"] = row[-1]
				else:
					entry["environment"] = "-"
				

			# Parse the record as an ICMP packet	
			if "icmp" in row[1]:
			
				entry["protocol"] = row[1][:4]

				entry["dest_ip"] = row[4]
				
				entry["info"] = ''.join(row[5] + " " + row[6])

				batch.append(entry)

				if len(batch) >= 5000 and save_data(url, post_log_name, user_email, headers, batch):
					batch = []


			# Parse the record as a TCP/UDP packet
			elif "udp" in row[1] or "tcp" in row[1]:
					
				entry["protocol"] = row[1][:3]

				entry["src_port"], entry["dest_ip"], entry["dest_port"] = row[4:7]
				
				if len(row) >= 9:
					entry["info"] = ''.join(row[7] + " " + row[8])
				elif len(row) >= 8:
					entry["info"] = ''.join(row[7])
									
				batch.append(entry)

				if len(batch) >= 5000 and save_data(url, post_log_name, user_email, headers, batch):
					batch = []


		# Save one last time for the remainder of the records
		if len(batch) > 0:
			if not save_data(url, post_log_name, user_email, headers, batch):
				print("ERROR! Last batch of saves didn't POST to the server.")


		last_update = log.tell()
		with open(log_name[:-3] + "txt", 'w') as pointers:
			pointers.write(str(last_update))	
				

	end = time()
	print("Program Complete.")
	print("Processing time: " + str(end-start))
		
	return last_update
		
		
def rreplace(s, old, new, occurrence):
	"""
	Returns new string with the replaced character(s).
	
	Credit goes to "mg." from StackOverflow, Question ID: 2556108
	
	Keyword arguments:
	s   -- the string to parse
	old -- the character to find and replace
	new -- the new character to replace the old one(s) with
	"""
	
	li = s.rsplit(old, occurrence)
	return new.join(li)


def main():
	"""The main function for the program. It'll drive the methods and data."""

	user_name, log_name, static_bool, update_bool = process_args()

	# We will use the front end to create our unique client folders which will be contained inside the Clients folder
	# We will store usernames and passwords in a database controlled by the frontend
	
	if static_bool:

		path = ("Users/" + str(user_name) + "/" + (log_name))
	
		if update_bool:

			with open("Users/" + user_name + "/" + log_name[:-3] + "txt", 'r') as pointers:
				last_update = int(pointers.readline())
			
			process_log(path, user_name, last_update) 
		else:
			process_log(path, user_name)

	else:
		# Assume log file is on program server (will probably change later)
		path = ("Users/" + user_name + "/" + log_name)

		try:
			with open(path[:-3] + "txt", 'r') as pointers:
				last_update = int(pointers.readline())
				
		except IOError:
			last_update = 0

		while True:
			last_update = process_log(path, user_name, last_update)
			

def save_data(url, log_name, user_email, headers, batch):
	"""
	Saves the given payload into our web application's database over HTTPS

	Keyword arguments:
	url        -- The url to send the HTTP POST request to.
	log_name   -- The name of the log to save to
	user_email -- The email for the user
	headers    -- The headers to send along with the POST.
	batch      -- The collection of records to send to the web application.
	"""

	# Insert the entries
	payload = {"entries":batch, "log_name":log_name, "user_email":user_email}

	for i in range(5,0,-1):
		req = requests.post(url, 
			data=json.dumps( payload, separators=(',', ': ') ), 
			headers=headers)

		if req.status_code in (200,201):
			print("Record save successful.")
			batch = []
			return True

		else:
			print("A problem occurred when saving records to the database.")
			print("HTTP Response: " + str(req.status_code))
			print("Retrying..." + str(i) + " attempts remaining\n")

			req = requests.post(url, 
				data=json.dumps( payload, separators=(',', ': ') ), 
				headers=headers)


	# If the records can't be saved, return False
	if not req.status_code in (200,201):
		print("Record save failed! We'll try again next time around.")
		return False

	# If all goes well, return True
	return True



# Call the main method to run the program
if __name__ == "__main__":
	main()

