#!/usr/bin/env python
# -*- coding: utf-8 -*-
from get_art import get_token, walk_through_json
import json
import requests
import pprint
import urllib
from pymongo import MongoClient
# from requests.packages.urllib3.exceptions import InsecureRequestWarning
#
# requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# print get_token(platform='SCOPUS')

USER_KEY = '4f6db2f99f65019116fcb0f8756cd94b'

class SpringerAPI():

    def __init__(self, mongo_path="mongodb://localhost:27017", platform='SCIDIR'):
        # key, token = get_token(platform)
        # self.headers = {'Accept' : 'application/json', 'X-ELS-Authtoken' : token, 'X-ELS-APIKey' : key}
        self.client = MongoClient(mongo_path)
        self.db = self.client.springer
        self.meta_downloaded = 0
        print('Mongo connected')

    def get_meta_data(self, subject='Mathematics'):
        source_url = 'http://api.springer.com/metadata/json'
        q = ''
        q += 'subject:' + subject
        params = {'api_key': USER_KEY, 'q': q, 's': 1, 'p': 50}
        resp_affilated_to_some_data = requests.get(source_url, params=params)
        print('FIRST', len(resp_affilated_to_some_data.json()['records']))
        print('SECOND', resp_affilated_to_some_data.json()['result'])
        for i in range(20):
            params['s'] += 50
            resp_affilated_to_some_data = requests.get(source_url, params=params)
            self.proceed_search_result(result=resp_affilated_to_some_data.json()['records'])

    def proceed_search_result(self, result):
        for num, res in enumerate(result):
            self.meta_downloaded += 1
            if self.meta_downloaded % 100 == 0:
                print('%d meta downloaded' % self.meta_downloaded)
            springer_meta = self.db.springer
            springer_meta.insert(res)


def main():
    a = SpringerAPI()
    a.get_meta_data()
    
if __name__ == '__main__':
    main()