#!/usr/bin/env python
# -*- coding: utf-8 -*-


import json
import requests
import time
from pymongo import MongoClient


def get_token(platform='SCIDIR'):
    url0 = "http://api.elsevier.com/authenticate?platform=" + platform 
    key = "9112857d6d401183ef646c7917250913" 
    resp = requests.get(url0, headers={'Accept' : 'application/json', 'X-ELS-APIKey' : key}) 
    json_data = resp.json()
    if resp.status_code == 200:
        print('Authentication success.')
    else: 
        print('Authentication error!!')
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


def pull_data(count=200, start=0, subj=423):
    source_url = "http://api.elsevier.com/content/search/scidir"
    token, key = get_token()
    headers = {'Accept' : 'application/json', 'X-ELS-Authtoken' : token, 'X-ELS-APIKey' : key}
    #adding subscribed content
    params = {'query' : 'boolean', 'subscribed': 'true',  'count' : count, 'subj' : subj, 'oa': 'true', 'start' : start}
    # 423 is computer science general
    client = MongoClient("mongodb://localhost:27017")
    db = client.elsevier
    articles = db.articles
    # Запрос поиска, вернет список из 200 результатов в каждой ссылка на текст
    
    resp_affilated_to_some_data = requests.get(source_url, headers=headers, params=params)
    
    print(params)
    if resp_affilated_to_some_data.status_code == 200:
        print("search is OK")
    else:
        print('search failed')
    try:
    	art_count = int(resp_affilated_to_some_data.json()['search-results']['opensearch:totalResults']) - start
    except:
	return 10
    for num, res in enumerate(resp_affilated_to_some_data.json()['search-results']['entry']):
        if (num + 1) % 100 == 0:
            print('%d articles got' % num)
        if (num + 1) % 10 == 0:
            # print('SLEEPING...')
            time.sleep(60)
            # print('WOKE UP!')
        link = res['link'][0]['@href']
	try:
            full_text_resp = requests.get(link, headers=headers)
	except:
	    continue
#         text_json = full_text_resp.json()
        formatted_data = {}
	try:
            walk_through_json(full_text_resp.json(), formatted_data)
	except:
	    print('parsing error')
	    continue
        formatted_data.pop('$', None)
#         pprint(formatted_data)
        articles.insert(formatted_data)
    return art_count - count



def main():
    whole_counter = 0
# got , 420, 421, 422, 423, 424, 418, 419 (~400 штук)
# got 425, 426, 427, 126,135,199, 11
    subj = []
    for s in subj:
        start = 0
        count = 200
        while pull_data(count=count, start=start, subj=s) > count:
            start += count
	    whole_counter += count
            print('%d proceed' % start)
    print("%d articles got" % whole_counter)


if __name__ == '__main__':
    main()
