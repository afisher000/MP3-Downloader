# -*- coding: utf-8 -*-
"""
Created on Sun Jul  3 22:32:43 2022

@author: afisher
"""

import requests
import pandas as pd
import re


class API():
    def __init__(self, search):
        self.search_url = 'https://itunes.apple.com/search?'
        self.lookup_url = 'https://itunes.apple.com/lookup?'

        self.get_artist(search)
        self.get_albums()
        self.get_tracks()

    def get_tracks(self):
        self.tracks = {}
        for album_id in self.albums.id:
            url = f'{self.lookup_url}id={album_id}&entity=song'
            results = requests.get(url).json()['results']
            track_list = [self.clean_name(result['trackName'])
                      for result in results if result['wrapperType']=='track']
            if len(set(track_list))>4:
                self.tracks[album_id] = track_list
        print(f'{len(self.tracks)} important albums')
        return 
        
        
    def get_artist(self, search):
        search_params = {'term':search.replace(' ','+'),
               'limit':'1',
               'entity':'musicArtist',
               'attribute':'artistTerm'}
        params = [key+'='+value for key,value in search_params.items()]
        r = requests.get(self.search_url + '&'.join(params)).json()['results'][0]
        
        self.artist_name = r['artistName']
        self.artist_id = r['artistId']
        return
    
    def get_albums(self):
        url = f'{self.lookup_url}id={self.artist_id}&entity=album'
        results = requests.get(url).json()['results']
        
        albums = pd.DataFrame(columns=['id','raw_name','name','tracks'])
        for entry in results:
            if 'collectionName' in entry.keys():
                album_id = entry['collectionId']
                raw_name = entry['collectionName']
                tracks = entry['trackCount']
                name = self.clean_name(raw_name)
                if name is not None:
                    albums.loc[len(albums)] = [album_id, raw_name, name, tracks]
        print(f'{len(albums)} raw albums')
        
        # Munge duplicates
        albums['name_len'] = albums.raw_name.apply(len)
        albums.sort_values(by=['name','name_len'], ascending = True, inplace=True)
        self.albums = albums.drop_duplicates(subset=['name'])
        print(f'{len(self.albums)} clean albums')
        return 

    def clean_name(self, name):
        if name.endswith(' - Single'):
            return None
        name = re.sub('\(.*\)','',name)
        name = re.sub('(\/|\\|\||\?)[ ]?','',name)
        name = re.sub(' - .*','',name).strip()
        return name
        

data = API('the killers')







