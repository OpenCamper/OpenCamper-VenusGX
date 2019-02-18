#!/usr/bin/python3
###############################################
# Copyright by Road IT (www.roadit.de) 2019   #
# Author: Dennis Eisold			      #
# Created: 11.02.2019			      #
###############################################

import os, json, time, threading
import paho.mqtt.client as mqtt

mqtt_server = '10.10.31.3'
mqtt_port = 1883
mqtt_topic = 'N/9884e3983b8a/sonoff/Esszimmer/TV/'
last_power = 1000
last_state = 1
timestamp = int(time.time())
off_power = 20
off_time = 60

def on_message(client, userdata, msg):
	global last_power, last_state, timestamp
	if msg.topic == mqtt_topic+"SENSOR":
		json_data = json.loads(msg.payload)

		if json_data['ENERGY']['Power'] < off_power:
			if last_power < off_power and last_state == 1 and (int(time.time()) - timestamp) > off_time:
				client.publish(mqtt_topic+'cmnd/Power1', 'off')
				last_power = 1000
				last_state = 0
			else:
				last_power = json_data['ENERGY']['Power']
	elif msg.topic == mqtt_topic+"POWER":
		if msg.payload == 'on':
			timestamp = int(time.time())
			last_state = 1

def on_subscribe(client, userdata, mid, granted_qos):
	print("Subscribed: "+str(mid)+" "+str(granted_qos))

while True:
	client = mqtt.Client()
	client.on_subscribe = on_subscribe
	client.on_message = on_message
	client.connect(mqtt_server, mqtt_port, 5)
	client.subscribe(mqtt_topic+'#', qos=0)
	client.loop_forever()
