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
from dnac import *
from env import *
import json
from jinja2 import Template

#open file with mac addresses
with open("mac_addresses.json") as f:
    data = json.load(f) #data structure is a dictionary with key "mac_addresses" and the value is a list of all the mac addresses of the clients

#open file with the mapping of which vlan each client is associated with
with open("mac_to_vlan.json") as f:
    mac_to_vlan = json.load(f) #data structure is a dictionary with mac addresses as the keys and the corresponding vlan number as the values

#open file with the Jinja template of the configuration
with open("base_template.txt", "r") as f:
    template_lines = f.readlines()
    base_template = ''.join(template_lines) #base template is one long string

#retrieve DNAC token to authenticate future requests
token = getAuthToken(env)
env["token"] = token #save token in the env dictionary that also contains the base url, username, and password of the DNAC instance

device_to_client = {} #device_to_client maps which network device each client is connected to
device_id_to_name = {} #device_id_to_name maps the device id to its name

#loop through the mac addresses from mac_addresses.json
for mac in data["mac_addresses"]:
    client = getClientDetails(env, mac) #getClientDetails retrieves specific information about the client indicated by the mac address

    device_name = client["connectionInfo"]["nwDeviceName"] #device name of network device client is connected to
    device_id = client["detail"]["connectedDevice"][0]["id"] #device id of network device client is connected to
    device_port = client["detail"]["port"] #port where the client is connected to the device

    #check if device id has been added to the device_to_client dictionary yet and add it if it hasn't been
    if device_id not in device_to_client.keys():
        device_to_client[device_id] = []

    #add the mac address of the client and the port where its connected to the device to the device_to_client dictionary
    client_info = {"mac": mac, "port": device_port}
    device_to_client[device_id].append(client_info)

    #check if device if has been added to the device_id_to_name dictionary yet and add it if it hasn't been
    if device_id not in device_id_to_name.keys():
        device_id_to_name[device_id] = device_name

#find the project id of the project name in env.py
project = getProjectByName(env, project_name)
project_id = project[0]["id"]
template = Template(base_template) #create Jinja Template object from template in base_template.txt

#create template specific to each client and group together all templates according to which device they're being applied to
#then deploy the template to the device
for device_id, clients in device_to_client.items():
    client_templates = []
    device_name = device_id_to_name[device_id]

    for client in clients:
        vlan = mac_to_vlan[client["mac"]]
        client_template = template.render(port=client["port"], vlan=vlan)
        client_templates.append(client_template)

    deploy_template = '\n'.join(client_templates)
    template_name = device_name + " Template"

    resp = createTemplate(env, project_id, template_name, deploy_template) #create Template in DNAC according to Jinja Template
    template_resp = resp.json()["response"]
    pprint.pprint(template_resp)

    task_id = template_resp["taskId"] #need to track the task to get the template id, which will be used for deployment
    task = getTask(env, task_id)
    pprint.pprint(task)
    #check if task is complete or still in progress; once task is complete, "data" will be a key in the repsonse
    while "data" not in task["response"].keys():
        print()
        print()
        pprint.pprint(task)
        time.sleep(1)
        task = getTask(env, task_id)

    template_id = task["response"]["data"]
    versionTemplate(env, template_id) #version template to commit it so it can be deployed

    response = deployTemplate(env, device_name, device_id, template_id) #deploy template; it requires the device name, device id, and template id
