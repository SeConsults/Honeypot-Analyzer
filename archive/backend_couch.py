# The back-end file for the Honeypot Analyzer.
# This program reads in records from a HoneyD log file,
# parses them, and stores them in a SQLite database.
#
# Command line usage:
#       python backend_couch.py --log <logfile name> --db <database name>
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
import requests
from time import time


def process_args():
	"""Returns the names of the database and log file."""
	
	# A small description of the application for the manual
	about_app = 'Process a HoneyD log file and store it into a database.'


	# Parse the command line arguments (if specified) and 
	# assign their values to some variables.
	arg_parser = argparse.ArgumentParser(description = about_app)

	arg_parser.add_argument('-l', '--log', type=str, default='logfile.log',
							help='the log file\'s name. Default: logfile.log')
							
	arg_parser.add_argument('-d', '--db', type=str, default='logs',
							help='the database\'s name. Default: logs')
	
	args = vars( arg_parser.parse_args() )
	
	db_name, log_name = args.values()

	return (log_name, db_name)


def process_log(log_name, db_name):
	"""Processes the log entries and inserts them into the database.
	
	Keyword arguments:
	log_name -- the log file's name
	db_name  -- the database file's name
	"""

	url = 'http://localhost:5984/' + str(db_name)
	headers = {'content-type': 'application/json'}
	
	
	
	with open(log_name, 'r') as log:
		
		# Time this function's runtime
		start = time()
		
		csv_data = csv.reader(log, delimiter=' ')
		
		for row in csv_data:

			entry = {"type":"entry"}
						
			if "honeyd" in row[1]:
				continue
				
				
			elif "icmp" in row[1]:
			
				entry["date"], entry["time_of_day"] = rreplace(row[0], '-', ' ', 1).split()

				entry["protocol"], entry["connection"], entry["src_ip"], \
				entry["dst_ip"] = row[1:5]
				
				entry["info"] = ''.join(row[5] + " " + row[6])
				
				if '[' in row[-1]:
					entry["environment"] = row[-1]
				#else:
				#	entry["environment"] = ''
				
				req = requests.post(url, data=json.dumps(entry,separators=(',', ': ')),
							headers=headers)

				print(req)

				
				
				#cursor.execute('Insert into Log Values(?,?,?,?,?,?,?,?,?,?);',\
				#		[date, time_of_day, protocol, connection, src_ip,\
				#		'', dst_ip, '', info, environment])
							  
		
			elif "udp" in row[1] or "tcp" in row[1]:
					
				entry["date"], entry["time_of_day"] = rreplace(row[0], '-', ' ', 1).split()							
				entry["protocol"], entry["connection"], entry["src_ip"], \
				entry["src_port"], entry["dst_ip"], entry["dst_port"] = row[1:7]
				
				if len(row) >= 9:
					entry["info"] = ''.join(row[7] + " " + row[8])
				elif len(row) >= 8:
					entry["info"] = ''.join(row[7])
									
				if '[' in row[-1]:
					entry["environment"] = row[-1]
				#else:
				#	environment = ''
				
				req = requests.post(url, data=json.dumps(entry,separators=(',', ': ')),
							headers=headers)

				print(req)	
				
				#cursor.execute('Insert into Log Values(?,?,?,?,?,?,?,?,?,?);',\
				#		[date, time_of_day, protocol, connection, src_ip,\
				#		src_port, dst_ip, dst_port, info, environment])
				
	end = time()
	print("Program Complete.")
	print("Processing time: " + str(end-start))
	
		
		
def rreplace(s, old, new, occurrence):
	"""Returns new string with the replaced character(s).
	
	Credit goes to "mg." from StackOverflow, Question ID: 2556108
	
	Keyword arguments:
	s   -- the string to parse
	old -- the character to find and replace
	new -- the new character to replace the old one(s) with
	"""
	
	li = s.rsplit(old, occurrence)
	return new.join(li)
		

# Main code below
if __name__ == "__main__":
	log_name, db_name = process_args()	
	process_log(log_name, db_name)
