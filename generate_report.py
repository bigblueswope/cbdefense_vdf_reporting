#!/usr/bin/env python

import os
import sys
import datetime
import time
import requests
import json
import pprint
import requests.packages.urllib3
from auth import CredentialStore
from errors import CredentialError

requests.packages.urllib3.disable_warnings()
pp = pprint.PrettyPrinter(indent=4)

class CredStore(object):
    def __init__(self, *args, **kwargs):
        credential_file = kwargs.pop("credential_file", None)
        self.credential_store = CredentialStore(credential_file=credential_file)

        self.credential_profile_name = kwargs.pop("profile", None)
        self.credentials = self.credential_store.get_credentials(self.credential_profile_name)

try:
    my_creds = CredStore(profile='default')
except CredentialError, e:
    print e
    sys.exit()

api_key,conn_id = my_creds.credentials.api_key, my_creds.credentials.conn_id
token = "%s/%s" % (api_key, conn_id)

url = my_creds.credentials.cbd_api_url

if not url.lower().startswith('https://'):
	print "cbd_api_url in the credentials file must begin with 'https://'"
	sys.exit(1)

#dict to track the distinct vdf versions and their dates
vdf_versions = {}

host_info = {}

#Request all sensors
uri = '%s/integrationServices/v3/device' % (url)
headers = {'X-Auth-Token': token}
r = requests.get(uri, headers=headers)
foo = r.json()


# Iterate over the results 
for bar in foo['results']:
	#Get the eventId for each result
	try:
		host_info[bar['deviceId']] = {}
		host_info[bar['deviceId']]['avEngine'] = bar['avEngine']
		host_info[bar['deviceId']]['avStatus'] = bar['avStatus']
		host_info[bar['deviceId']]['lastContact'] = bar['lastContact']
		host_info[bar['deviceId']]['name'] = bar['name']
		host_info[bar['deviceId']]['sensorStates'] = bar['sensorStates']
		host_info[bar['deviceId']]['status'] = bar['status']
		host_info[bar['deviceId']]['policyName'] = bar['policyName']
	
		# avEngine': u'4.5.2.234-ave.8.3.44.80:avpack.8.4.2.64:vdf.8.14.10.126'	
		if bar['avEngine']:
			vdf_version = bar['avEngine'].split(':')[2]
			vdf_version = vdf_version.replace('vdf.','')
			if vdf_version in vdf_versions.keys():
				vdf_date_diff = vdf_versions[vdf_version]
			else:
				vdf_url = 'http://vdf.carbonblackse.com'
				vdf_uri = '%s/api/%s' % (vdf_url, vdf_version)
			
				vdf_r = requests.get(vdf_uri)
			
				if vdf_r.status_code == 200:
					vdf_date = vdf_r.json().values()[0]
					vdf_list = vdf_date.split('-')
					today = datetime.date.today()
					a = datetime.date(int(vdf_list[0]), int(vdf_list[1]), int(vdf_list[2]))
					vdf_date_diff = (today - a).days
					vdf_versions[vdf_version] = vdf_date_diff
				else:
					vdf_date_diff = None
		else:
			vdf_date_diff = None
		
		host_info[bar['deviceId']]['vdfDateDiff'] = vdf_date_diff
		
	except KeyError:
		pass
	
pp.pprint(host_info)
