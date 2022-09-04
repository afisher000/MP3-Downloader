# -*- coding: utf-8 -*-
"""
Created on Sun Jul  3 22:32:43 2022

@author: afisher
"""

import requests
import pandas as pd
import re
import time
import concurrent.futures


class API():
    def __init__(self, search, progressbar=None):
        self.search_url = 'https://itunes.apple.com/search?'
        self.lookup_url = 'https://itunes.apple.com/lookup?'
        if progressbar is not None:
            self.progressbar = progressbar
        
        # Get artist, album, and track data as dataframes
        t1 = time.perf_counter()
        self.get_artist_data(search)
        self.get_album_data()
        self.get_track_data()
        t2 = time.perf_counter()
        print(f'API time: {t2-t1:.1f} seconds')
        
        
    def get_tracks(self, album_id):
        url = self.lookup_url + f'id={int(album_id)}&entity=song'
        results = requests.get(url).json()['results']
        track_data = pd.DataFrame(results)
        
        track_data = track_data.iloc[1:] #Remove first-row album entry
        if len(track_data)==0:
            return
            
            
        # Add 'cleaned' track column
        track_data['cleanName'] = track_data.trackName.apply(self.clean_name)
        track_data = track_data[track_data.cleanName.notna()]
    
        # Remove duplicate clean song names
        track_data.sort_values(by='cleanName', key=lambda x: x.str.len())
        track_data = track_data.drop_duplicates(subset=['cleanName']).reset_index()
        track_data['trackNumber'] = track_data.index
        

        # Must have 4 or more songs
        if len(track_data)<4:
            return 
            

        return track_data
            
    def get_track_data(self):
        # Return early if no artist or albums
        if self.album_data is None or len(self.album_data)==0:
            self.track_data = None
            return
        
        

# ====== Useful for troubleshooting self.get_tracks ===========================
#         # dfs = []
#         # for album_id in self.album_data.collectionId.values:
#         #     dfs.append(self.get_tracks(album_id))
#         # self.track_data = pd.concat(dfs)
# =============================================================================
        
        # Multithreading
        self.progressbar.setValue(0)
        self.progressbar.show()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.get_tracks, id_) for id_ in self.album_data.collectionId.values]
            for future in concurrent.futures.as_completed(futures):
                new_value = self.progressbar.value() + 100/len(self.album_data)
                self.progressbar.setValue(round(new_value))
            droprows = [True if future.result() is None else False for future in futures]
            self.album_data.drop(self.album_data.index[droprows], inplace=True)
            self.track_data = pd.concat([future.result() for future in futures]) #join into dataframe
            self.progressbar.hide()
        

        # Reset the indices of track_data and album_data
        self.track_data.set_index(['collectionId','trackNumber'], drop=True, inplace=True)
        self.album_data.reset_index(drop=True, inplace=True)
        return 
        
        
    def get_artist_data(self, search):
        url = self.search_url + f"limit=1&entity=musicArtist&attribute=artistTerm&term={search.replace(' ','+')}"
        result = requests.get(url).json()['results']
        
        if len(result)!=0:
            self.artist_data = pd.Series(result[0]) #Save in series
        else:
            self.artist_data = None
        return
    
    def get_album_data(self):
        # Return early if no artist found
        if self.artist_data is None:
            self.album_data = None
            return
        
        url = self.lookup_url + f'entity=album&id={self.artist_data.artistId}'
        results = requests.get(url).json()['results']
        
        # Save results to dataframe
        album_data = pd.DataFrame(results)
        
        # Drop first-row artist entry
        album_data = album_data.iloc[1:]
        
        # Add 'cleaned' name column, drop singles
        album_data['cleanName'] = album_data.collectionName.apply(self.clean_name)
        album_data = album_data[album_data.cleanName.notna()]
        
        # Sort by year, drop duplicates, reset_index
        album_data.sort_values(by='releaseDate', inplace=True)
        album_data.drop_duplicates(subset=['cleanName'], inplace=True)
        album_data.reset_index(drop=True, inplace=True)
        self.album_data = album_data
        return 

    def clean_name(self, name):
        ''' Clean the string "name" by removing parentheticals, brackets, 
        punctuation, and hyphenations.'''
        if name.endswith(' - Single'):
            return None
        name = re.sub('\(.*\)','',name) #remove parentheticals
        name = re.sub('\[.*\]','',name) #remove brackets
        name = re.sub('(\/|\\|\||\?)[ ]?','',name)
        name = re.sub(' - .*','',name).strip() #remove hyphenations
        return name
        






