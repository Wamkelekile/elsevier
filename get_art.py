#!/usr/bin/env python
# -*- coding: utf-8 -*-


import json
import requests
import time
from pymongo import MongoClient


def get_token(platform='SCIDIR'):
    print platform
    url0 = "https://api.elsevier.com/authenticate?platform=" + platform
    key = "9112857d6d401183ef646c7917250913"  # SCOPUS
    # key = "ff6537ee32af208fe3669fa329000ab5"  # SCIDIR
    resp = requests.get(url0, headers={'Accept': 'application/json', 'X-ELS-APIKey': key})
    json_data = resp.json()
    if resp.status_code == 200:
        print('Authentication success.')
    else: 
        print('Authentication error!!')
        print resp.text
    token = json_data['authenticate-response']['authtoken']
    return token, key


def walk_through_json(text_json, file_to_save):
    for i in text_json:
        if type(text_json[i]) is list:
            items = []
            for j in text_json[i]:
                items.extend(list(j.values()))
            file_to_save[i] = items
        elif type(text_json[i]) is dict:
            walk_through_json(text_json[i], file_to_save)
        else:
            file_to_save[i] = text_json[i]





