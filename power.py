#!/usr/bin/python3
# -*- coding: utf-8 -*-

###############################################
# Copyright by Road IT (www.roadit.de) 2019   #
# Author:   Dennis Eisold		      #
# Created:  07.02.2019			      #
###############################################

import datetime, time, json, subprocess, sys, time, os, pprint
from influxdb import InfluxDBClient
from astral import Astral, Location

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
config_set = "solar"

def jprint(j):
    print(json.dumps(j, indent=2, sort_keys=True))

#Connection to Influx
influx_server = config[config_set]['influxdb_setting']

# Astral Data
data = {}
latitude = 50.123102
longitude = 10.527879
date = datetime.date.today()
dateandtime = datetime.datetime.now() + datetime.timedelta(hours=1)

# DBus Connection
DBusGMainLoop(set_as_default=True)
dbusObjects = {}

mppt = config["solar"]['dbus_name']
battery = config["battery"]['dbus_name']
multiplus = config["multiplus"]['dbus_name']

#a list of  strings that will be addressed and queried for the substrings
query = {
	mppt : [
		'/Pv/V',
		'/Pv/I',
		'/State'
	],
	battery : [
		'/Dc/0/Current',
		'/Dc/0/Power',
		'/Dc/0/Voltage',
		'/Dc/0/MidVoltage',
		'/Soc',
		'/TimeToGo',
		'/ConsumedAmphours',
	],
	multiplus : [
		'/Leds/Absorption',
		'/Leds/Bulk',
		'/Leds/Float',
		'/Leds/Inverter',
		'/Leds/LowBattery',
		'/Leds/Mains',
		'/Leds/Overload',
		'/Leds/Temperature',
		'/Mode',
		'/State',
		'/Ac/ActiveIn/L1/I',
		'/Ac/ActiveIn/L1/P',
		'/Ac/ActiveIn/L1/V',
		'/Ac/ActiveIn/L1/S',
		'/Ac/ActiveIn/L1/F'
	]
}

resp = {}

dbusConn = dbus.SessionBus() if 'DBUS_SESSION_BUS_ADDRESS' in os.environ else dbus.SystemBus()

for bus,list in query.items():
    resp[bus] = {}
    for path in list:
        resp[bus][path] = VeDbusItemImport(dbusConn, bus, path).get_value()

if resp[battery]['/TimeToGo'] is None:
	resp[battery]['/TimeToGo'] = 0

jprint(resp)

data = resp[mppt]
data['/Pv/W'] = float(data['/Pv/V']) * float(data['/Pv/I'])

# Calculate solar Data
solar = Astral()
solar.solar_depression = 'civil'
#l = Location()
#l.name = 'Wohnwagen'
#l.latitude = latitude
#l.longitude = longitude
#l.timezone = 'Europe/Berlin'
#l.elevation = 0
#sun = l.sun()

#data['sunrise'] = str(sun['sunrise'])
#data['sunset'] = str(sun['sunset'])
data['azimuth'] = solar.solar_azimuth(dateandtime, latitude, longitude)
data['elevation'] = solar.solar_elevation(dateandtime, latitude, longitude)
if data['elevation'] < 0:
	data['elevation'] = 0
data['zenith'] = solar.solar_zenith(dateandtime, latitude, longitude)

# Set up a client for InfluxDB
dbclient = InfluxDBClient(config[influx_server]['host'], config[influx_server]['port'], config[influx_server]['username'], config[influx_server]['password'], config[influx_server]['database'])

json_body = [{
	"measurement": "power",
	"fields": {
		"pv_w": float(data['/Pv/W']),
		"pv_v": float(data['/Pv/V']),
		"pv_a": float(data['/Pv/I']),
		"pv_state": float(data['/State']),
		"elev": float(data['elevation']),
		"bat_a": float(resp[battery]['/Dc/0/Current']),
		"bat_w": float(resp[battery]['/Dc/0/Power']),
		"bat_v": float(resp[battery]['/Dc/0/Voltage']),
		"bat_mv": float(resp[battery]['/Dc/0/MidVoltage']),
		"bat_soc": float(resp[battery]['/Soc']),
		"bat_ttg": float(resp[battery]['/TimeToGo']),
		"bat_ca": float(resp[battery]['/ConsumedAmphours']),
		"wr_led_absorption": float(resp[multiplus]['/Leds/Absorption']),
		"wr_led_bulk": float(resp[multiplus]['/Leds/Bulk']),
		"wr_led_float": float(resp[multiplus]['/Leds/Float']),
		"wr_led_inverter": float(resp[multiplus]['/Leds/Inverter']),
		"wr_led_lowbattery": float(resp[multiplus]['/Leds/LowBattery']),
		"wr_led_mains": float(resp[multiplus]['/Leds/Mains']),
		"wr_led_overload": float(resp[multiplus]['/Leds/Overload']),
		"wr_led_temperature": float(resp[multiplus]['/Leds/Temperature']),
		"wr_mode": float(resp[multiplus]['/Mode']),
		"wr_state": float(resp[multiplus]['/State']),
		"wr_a": float(resp[multiplus]['/Ac/ActiveIn/L1/I']),
		"wr_w": float(resp[multiplus]['/Ac/ActiveIn/L1/P']),
		"wr_v": float(resp[multiplus]['/Ac/ActiveIn/L1/V']),
		"wr_s": float(resp[multiplus]['/Ac/ActiveIn/L1/S']),
		"wr_f": float(resp[multiplus]['/Ac/ActiveIn/L1/F'])
	}
}]
dbclient.write_points(json_body)
