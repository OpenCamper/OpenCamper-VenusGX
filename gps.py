#!/usr/bin/python3
# -*- coding: utf-8 -*-

###############################################
# Copyright by Road IT (www.roadit.de) 2019   #
# Author:   Dennis Eisold		      #
# Created:  07.02.2019			      #
###############################################

import datetime, time, json, subprocess, sys, time, os, pprint
from influxdb import InfluxDBClient

sys.path.insert(1, os.path.join(os.path.dirname(__file__), 'lib', 'velib_python'))
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from vedbus import VeDbusItemExport, VeDbusItemImport

# Load config file
try:
	with open(os.path.dirname(os.path.abspath(__file__))+'/config.json') as f:
		config = json.load(f)
except KeyError:
	print("No config file found")
	exit()

# load configset
config_set = "gps"

def jprint(j):
    print(json.dumps(j, indent=2, sort_keys=True))

#Connection to Influx
influx_server = config[config_set]['influxdb_setting']

# DBus Connection
DBusGMainLoop(set_as_default=True)
dbusObjects = {}

gps = config["gps"]['dbus_name']

#a list of  strings that will be addressed and queried for the substrings
query = {
 gps : ['/Altitude',
		'/Fix',
		'/Position/Latitude',
		'/Position/Longitude',
		'/NrOfSatellites',
		'/Speed',
		'/Position/Course']
}

resp = {}

dbusConn = dbus.SessionBus() if 'DBUS_SESSION_BUS_ADDRESS' in os.environ else dbus.SystemBus()

for bus,list in query.items():
    resp[bus] = {}
    for path in list:
        resp[bus][path] = VeDbusItemImport(dbusConn, bus, path).get_value()

data = resp[gps]

# Set up a client for InfluxDB
dbclient = InfluxDBClient(config[influx_server]['host'], config[influx_server]['port'], config[influx_server]['username'], config[influx_server]['password'], config[influx_server]['database'])

json_body = [{
	"measurement": "gps",
	"fields": {
		"alt": float(data['/Altitude']),
		"lat": float(data['/Position/Latitude']),
		"lon": float(data['/Position/Longitude']),
		"sats": float(data['/NrOfSatellites']),
		"speed": float(data['/Speed']),
	}
}]
dbclient.write_points(json_body)
