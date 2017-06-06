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


class ElsevierAPI():

    def __init__(self, mongo_path="mongodb://localhost:27017", platform='SCIDIR'):
        # key, token = get_token(platform)
        # self.headers = {'Accept' : 'application/json', 'X-ELS-Authtoken' : token, 'X-ELS-APIKey' : key}
        self.client = MongoClient(mongo_path)
        self.db = self.client.elsevier
        self.text_downloaded = 0
        self.none_text_downloaded = 0
        self.token = 1
        self.key = 1
        print('Mongo connected')

    def proceed_search_result(self, result):
        for num, res in enumerate(result.json()['search-results']['entry']):
            if (num + 1) % 100 == 0:
                print('%d articles got' % num)
            if (num + 1) % 10 == 0:
                pass
            link = res['link'][0]['@href']
            print("THE LINK IS", link)

            try:
                full_text_resp = requests.get(link, headers=self.headers)
            except:
                print("There is no access to test of this article")
                continue
    #         text_json = full_text_resp.json()
            formatted_data = {}

            try:
                walk_through_json(full_text_resp.json(), formatted_data)
            except:
                print('parsing error')
                continue
            formatted_data.pop('$', None)
            self.save_search(data=formatted_data)


    def save_search(self, data):
        articles = self.db.articles
        try:
            articles.insert(data)
        except:
            print('Insert search error')

    def search_by_words(self, words, search_type):
        self.text_downloaded = 0
        self.none_text_downloaded = 0
        query = ''
        if search_type == "abstract":
            query += "abs(" + '+'.join(words) + ")"
        elif search_type == "all":
            query += "all(" + '+'.join(words) + ")"
        elif search_type == "keywords":
            query += "key(" + '+'.join(words) + ")"
        else:
            print('Incorrect search type')
            return 1

        self.token, self.key = get_token(platform='SCIDIR')
        token, key = self.token, self.key
        source_url = "https://api.elsevier.com/content/search/scidir"
        self.headers = {'Accept' : 'application/json', 'X-ELS-Authtoken' : token, 'X-ELS-APIKey' : key}

        count = 20#0 to debug ;)
        print "THIS IS AN searching query", query
        start = 0
        params = {'start': start, 'query': urllib.quote(query), 'count': count}
        resp_affilated_to_some_data = requests.get(source_url, headers=self.headers, params=params)
        # print(resp_affilated_to_some_data.text)
        # we need to get number of searched results and get all of them in for loop
        print('query', resp_affilated_to_some_data.json()['search-results']['opensearch:Query'])
        print('opensearch:totalResults', resp_affilated_to_some_data.json()['search-results']['opensearch:totalResults'])
        print('link', resp_affilated_to_some_data.json()['search-results']['link'])
        print(len(resp_affilated_to_some_data.json()['search-results']['entry']))
        res_count = int(resp_affilated_to_some_data.json()['search-results']['opensearch:totalResults'])
        if res_count == 0:
            print('Total results find 0, try to simplify request.')
            return  1
        else:

            for s in range(0, int(res_count), 200):
                self.get_batch(params=params, source_url=source_url, count=200, start=s, query=query)
                #We may get more (all) of them just comment the break
                break

        print('We downloaded %d full text articles with meta and %d no openaccess articles meta '
              'corresponding to your query' %
              (self.text_downloaded, self.none_text_downloaded))
        # self.proceed_search_result(resp_affilated_to_some_data)


    def download_subject(self, subj=423):
        self.text_downloaded = 0
        self.none_text_downloaded = 0
        source_url = "https://api.elsevier.com/content/search/scidir"
        self.token, self.key = get_token()
        token, key = self.token, self.key
        headers = {'Accept': 'application/json', 'X-ELS-Authtoken': token, 'X-ELS-APIKey': key}
        #adding subscribed content
        count=200
        start=0
        #delete subject (WE may add it and download all from subject)
        params = {'query': 'boolean',  'count': count, 'start': start, 'oa':'true'}
        # 423 is computer science general
        resp_affilated_to_some_data = requests.get(source_url, headers=headers, params=params)

        if resp_affilated_to_some_data.status_code == 200:
            print("search is OK")
            print('Total results:', resp_affilated_to_some_data.json()['search-results']['opensearch:totalResults'])
        else:
            print('download s search failed')
            print(resp_affilated_to_some_data.text)
        res_count = resp_affilated_to_some_data.json()['search-results']['opensearch:totalResults']
        for s in range(0, int(res_count), 200):
            self.get_batch(params=params, source_url=source_url, count=200, start=s)
            #We may get more (all) of them just comment the break
            break

        print('We downloaded %d full text articles with meta and %d no openaccess articles meta' %
              (self.text_downloaded, self.none_text_downloaded))

    def get_batch(self, params, source_url, count, start, delay=1, query=None): ##dounload some data by searching on subject
        token, key = self.token, self.key
        headers = {'Accept': 'application/json', 'X-ELS-Authtoken': token, 'X-ELS-APIKey': key}
        #adding subscribed content
        resp_affilated_to_some_data = requests.get(source_url, headers=headers, params=params)

        if resp_affilated_to_some_data.status_code == 200:
            print("Batch search is OK")
        else:
            print('Batch search failed')
            print(resp_affilated_to_some_data.text)
        print(resp_affilated_to_some_data.json()['search-results']['opensearch:totalResults'])
        print("We got ", start, 'count', count, 'len', len(resp_affilated_to_some_data.json()['search-results']['entry']))
        for num, res in enumerate(resp_affilated_to_some_data.json()['search-results']['entry']):
            if (num + 1) % 100 == 0:
                print('%d articles got' % (num + 1 + start))
            if (num + 1) % 10 == 0:
                #delay
                pass

            if int(res['openaccess']) == 1:
                source_link = res['link'][0]['@href']
                # [u'originalText', u'objects', u'link', u'coredata', u'scopus-eid', u'scopus-id'])
                resp = requests.get(source_link, headers=headers, params={})
                # We also may get meta from  scopus
                formatted_data = {}
                walk_through_json(resp.json()['full-text-retrieval-response'], formatted_data)
                if query: # save search result
                    formatted_data = {'data': formatted_data,'query': query}
                self.save_full_text_article(formatted_data)
                self.text_downloaded += 1

                # print('ITS OA!!!', resp.json()['full-text-retrieval-response'].keys())
            else:
                formatted_data = {}
                walk_through_json(res, formatted_data)
                if query: #save search result
                    formatted_data = {'data': formatted_data,'query': query}
                self.save_meta_article(formatted_data)
                self.none_text_downloaded += 1
                # print('its not OA, keys', res.keys())

    def save_full_text_article(self, data):
        articles = self.db.text_articles
        articles.insert(data)

    def save_meta_article(self, data):
        articles = self.db.meta_articles
        articles.insert(data)

# https://api.elsevier.com/content/abstract/EID:[]?apiKey=[]&view=REF
# EIDS for test
# 1-s2.0-S0213005X05749740
    def get_references(self, EID, option='print'): # 'print' 'save'
        source_url = "https://api.elsevier.com/content/abstract/eid/"
        token, key = get_token()
        headers = {'Accept': 'application/json', 'X-ELS-Authtoken': token, 'X-ELS-APIKey': key}
        params = {'view': 'REF'}
        resp_affilated_to_some_data = requests.get(source_url + EID, headers=headers, params=params)
        print("Getting references for article using eid", EID)

        if resp_affilated_to_some_data.status_code == 200:
            print("We got references OK")
        else:
            print('We dont got references FAIL')
            print(resp_affilated_to_some_data.text)
            return 1

        if option == 'save':
            print('TOTAL NUMBER OF REFERENCES', resp_affilated_to_some_data.json()['abstracts-retrieval-response']['references']['@total-references'])
            self.save_references(data={'eid': EID, 'references': resp_affilated_to_some_data.json()['abstracts-retrieval-response']['references']['reference']})

        elif option == 'print':
            # print('TOTAL NUMBER OF REFERENCES', resp_affilated_to_some_data.json()['abstracts-retrieval-response']['references']['@total-references'])
            print(resp_affilated_to_some_data.json()['abstracts-retrieval-response']['references'].keys())
            # print(resp_affilated_to_some_data.json()['abstracts-retrieval-response'].keys())
            # WE LOSE KEY REFERENCE!!!
            self.print_references(resp_affilated_to_some_data.json()['abstracts-retrieval-response']['references']['reference'])
        else:
            print('Incorrect option value')

    def print_references(self, data):
        for idx, ref in enumerate(data):
            print('NUMBER #', idx)
            print('TITLE:', ref['sourcetitle'])
            print('SCOPUS-ID:', ref['scopus-id'])
            try:
                print('CITEDBY-COUNT', ref['citedby-count'])
            except KeyError:
                print('CITEDBY-COUNT', 'MISSED')
            authors = []
            for i, a in enumerate(ref['author-list']['author']):
                authors.append([i])
                try:
                    authors[-1].append('ID: ' + a['@auid'])
                except KeyError:
                    authors[-1].append('ID: ' + 'MISSED')
                authors[-1].append("Name:" + a['ce:indexed-name'])
            print('AUTHORS:')
            print('\n'.join(map(lambda x: str(x), authors)))


    def save_references(self, data):
        refs = self.db.references
        try:
            refs.insert(data)
        except:
            print('Insert error')
        print('References saved')
        # save some result to table named t_name


def main():
    a = ElsevierAPI()
    # input: list of subjects
    #IT WORKS
    # a.download_subject()
    #IT DOESNOT WORK
    # a.search_by_words(['algorithm', 'graph', 'Dijkstra'], 'keywords')
    #getting some referenses using EID should work, but not

    a.get_references(EID='2-s2.0-0031442294', option='print')
    # a.get_references(EID='2-s2.0-0031442294', option='save')
    # 3-s2.0-B9781558607712500359
    # 3-s2.0-B9780123706164500045
    # 3-s2.0-B9780123725127000134
    # 3-s2.0-B9780124211803500139
    # 3-s2.0-B9780123705228500388

    # a.get_by_subdect() # this works a bit

if __name__ == '__main__':
    main()




