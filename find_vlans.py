#!/usr/bin/env python3
"""Copyright (c) 2020 Cisco and/or its affiliates.

This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at

               https://developer.cisco.com/docs/licenses

All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied."""
from env import env
from dnac import *
import json
import pprint
import time


#get DNAC token for authentication of future requests
token = getAuthToken(env)
env["token"] = token #add token to env that already contains the base_url, username, and password of the DNAC instance

devices = getDnacDevices(env)
switches = []
for device in devices:
    if device["family"] == "Switches and Hubs":
        switches.append(device["id"])
commands = ["show mac address-table"]
show_mac_task = commandRunner(env, commands, switches)
time.sleep(2)

task_id = show_mac_task["response"]["taskId"]
task = getTask(env, task_id)
pprint.pprint(task)
while "fileId" not in task["response"]["progress"]:
    task = getTask(env, task_id)
    pprint.pprint(task)

task_progress = json.loads(task["response"]["progress"])
file_id = task_progress["fileId"]
file_json = getFileById(env, file_id)
mac_table_lines = file_json[0]["commandResponses"]["SUCCESS"][commands[0]].splitlines()
mac_table_lines = mac_table_lines[6:-3]

#create a dictionary that will map every client to the VLAN it is currently associates with
mac_to_vlan = {}
for line in mac_table_lines:
    table_entry = line.split()
    vlan = table_entry[0]
    mac = table_entry[1]
    if vlan != "All":
        mac_to_vlan[mac] = vlan

mac_addresses = { "mac_addresses": [] }
keys = mac_to_vlan.keys()

mac_to_vlan_formatted = {}
for key in keys:
    mac_chars = key.replace('.', '')
    mac = mac_chars[:2] + ":" + mac_chars[2:4] + ":" + mac_chars[4:6] + ":" + mac_chars[6:8] + ":" + mac_chars[8:10] + ":" + mac_chars[10:12]
    mac_to_vlan_formatted[mac] = mac_to_vlan[key]
    mac_addresses["mac_addresses"].append(mac)

#save dictionary created above into a json file
mac_to_vlan_file = open("mac_to_vlan.json", "w")
json.dump(mac_to_vlan_formatted, mac_to_vlan_file, indent=4)
mac_to_vlan_file.close()

#mac_address.json contains all the mac addresses of the clients in the network
mac_file = open("mac_addresses.json", "w")
json.dump(mac_addresses, mac_file, indent=4)
mac_file.close()
