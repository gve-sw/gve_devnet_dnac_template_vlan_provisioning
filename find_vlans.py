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

#mac_address.json contains all the mac addresses of the clients in the network
mac_file = open("mac_addresses.json", "r")
data = json.load(mac_file)
mac_addresses = data["mac_addresses"]
mac_file.close()

#get DNAC token for authentication of future requests
token = getAuthToken(env)
env["token"] = token #add token to env that already contains the base_url, username, and password of the DNAC instance

#create a dictionary that will map every client to the VLAN it is currently associates with
mac_to_vlan = {}
for mac in mac_addresses:
    client = getClientDetails(env, mac) #retrieve details of client, this information will contain the vlan the client is currently associated with

    client_vlan = client["detail"]["vlanId"]
    mac_to_vlan[mac] = client_vlan

#save dictionary created above into a json file
mac_to_vlan_file = open("mac_to_vlan.json", "w")
json.dump(mac_to_vlan, mac_to_vlan_file, indent=4)
mac_to_vlan_file.close()
