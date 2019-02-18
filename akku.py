#!/usr/bin/python3
# -*- coding: utf-8 -*-

###############################################
# Copyright by Road IT (www.roadit.de) 2019   #
# Author:   Dennis Eisold		      #
# Created:  07.02.2019			      #
###############################################

#import logging
#logging.basicConfig()
#log = logging.getLogger()
#log.setLevel(logging.DEBUG)

from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.transaction import ModbusRtuFramer
from decimal import Decimal
import datetime, time, json, subprocess, sys, time, os, pprint
sys.path.insert(1, os.path.join(os.path.dirname(__file__), 'lib', 'velib_python'))
from influxdb import InfluxDBClient

config_set = "bms"
data = {}

# Load config file
try:
	with open(os.path.dirname(os.path.abspath(__file__))+'/config.json') as f:
		config = json.load(f)
except KeyError:
	print("No config file found")
	exit()

try:
    if(config[config_set]['protocol'] is not ""):
        with open(os.path.dirname(os.path.abspath(__file__))+'/lib/protocols/'+config[config_set]['protocol']+'.json') as f:
            cell_protocol = json.load(f)
except KeyError:
    print("No protocol in config specified")
    exit()

#Connection to Influx
influx_server = config[config_set]['influxdb_setting']

# Set up a client for InfluxDB
dbclient = InfluxDBClient(config[influx_server]['host'], config[influx_server]['port'], config[influx_server]['username'], config[influx_server]['password'], config[influx_server]['database'])

modbus_client = ModbusClient(config[config_set]["modbus_gw_ip"], port=config[config_set]["modbus_gw_port"], timeout=config[config_set]["modbus_gw_timeout"], framer=ModbusRtuFramer)
modbus_client.connect()

def jprint(j):
    print(json.dumps(j, indent=2, sort_keys=True))

def get_cell(cell):
	registers = cell_protocol['Device'][cell['type']]['Registers']
	address = cell['address']
	data[cell['id']] = {}

	#get Cell Voltage
	response = modbus_client.read_holding_registers(registers['ZELL_VOLTAGE']['Id'], registers['ZELL_VOLTAGE']['Count'], unit=address)
	data[cell['id']]['voltage'] = format(Decimal(response.registers[0])/1000, '.2f')

	#get Cell Max. Voltage
	response = modbus_client.read_holding_registers(registers['MAX_VOLTAGE']['Id'], registers['ZELL_VOLTAGE']['Count'], unit=address)
	data[cell['id']]["voltage_max"] = format(Decimal(response.registers[0]) / 1000, '.2f')

	#get Cell Min. Voltage
	response = modbus_client.read_holding_registers(registers['MIN_VOLTAGE']['Id'], registers['ZELL_VOLTAGE']['Count'], unit=address)
	data[cell['id']]["voltage_min"] = format(Decimal(response.registers[0]) / 1000, '.2f')

	#get Cell Temperature
	response = modbus_client.read_holding_registers(registers['TEMPERATURE']['Id'], registers['ZELL_VOLTAGE']['Count'], unit=address)
	data[cell['id']]["temperature"] = format(((Decimal(response.registers[0])-600) / 10), '.2f')
	
	#get Cell Max. Temperature
	response = modbus_client.read_holding_registers(registers['MAX_TEMPERATURE']['Id'], registers['ZELL_VOLTAGE']['Count'], unit=address)
	data[cell['id']]["temperature_max"] = format(((Decimal(response.registers[0])-600) / 10), '.2f')
	
	#get Cell Min. Temperature
	response = modbus_client.read_holding_registers(registers['MIN_TEMPERATURE']['Id'], registers['ZELL_VOLTAGE']['Count'], unit=address)
	data[cell['id']]["temperature_min"] = format(((Decimal(response.registers[0])-600) / 10), '.2f')
	
	#get balance Power
	response = modbus_client.read_holding_registers(registers['BALANCER_POWER']['Id'], registers['ZELL_VOLTAGE']['Count'], unit=address)
	data[cell['id']]["balancer_power"] = format(Decimal(response.registers[0]) / 1000, '.2f')

	json_body = [{
		"measurement": "cells",
		"fields": {
			str(cell['id'])+"_voltage": (data[cell['id']]['voltage']),
			str(cell['id'])+"_temperature": (data[cell['id']]['temperature']),
			str(cell['id'])+"_balancer_power": (data[cell['id']]['balancer_power'])
		}
	}]
	dbclient.write_points(json_body)

for cell in config[config_set]['cells']:
	get_cell(cell)

modbus_client.close()
