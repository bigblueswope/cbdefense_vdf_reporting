#!/usr/bin/env python

import os
import sys
import datetime
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
reply = r.json()


# Iterate over the results 
for sensor in reply['results']:
	#Get the eventId for each result
	try:
		host_info[sensor['deviceId']] = {}
		host_info[sensor['deviceId']]['avEngine'] = sensor['avEngine']
		host_info[sensor['deviceId']]['avStatus'] = sensor['avStatus']
		host_info[sensor['deviceId']]['lastContact'] = sensor['lastContact']
		host_info[sensor['deviceId']]['name'] = sensor['name']
		host_info[sensor['deviceId']]['sensorStates'] = sensor['sensorStates']
		host_info[sensor['deviceId']]['status'] = sensor['status']
		host_info[sensor['deviceId']]['policyName'] = sensor['policyName']
	
		# Example: avEngine': u'4.5.2.234-ave.8.3.44.80:avpack.8.4.2.64:vdf.8.14.10.126'	
		if sensor['avEngine']:
			vdf_version = sensor['avEngine'].split(':')[2]
			vdf_version = vdf_version.replace('vdf.','')
			if vdf_version in vdf_versions.keys():
				vdf_age = vdf_versions[vdf_version]
			else:
				vdf_url = 'http://vdf.carbonblackse.com'
				vdf_uri = '%s/api/%s' % (vdf_url, vdf_version)
			
				vdf_r = requests.get(vdf_uri)
			
				if vdf_r.status_code == 200:
					vdf_date = vdf_r.json().values()[0]
					vdf_list = vdf_date.split('-')
					today = datetime.date.today()
					a = datetime.date(int(vdf_list[0]), int(vdf_list[1]), int(vdf_list[2]))
					vdf_age = (today - a).days
					vdf_versions[vdf_version] = vdf_age
				else:
					vdf_age = None
		else:
			vdf_age = None
		
		host_info[sensor['deviceId']]['vdfAge'] = vdf_age
		
	except KeyError:
		pass
	
pp.pprint(host_info)
