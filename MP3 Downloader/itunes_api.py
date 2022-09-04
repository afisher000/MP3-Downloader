# -*- coding: utf-8 -*-
"""
Created on Sun Jul  3 22:32:43 2022

@author: afisher
"""

import requests
import pandas as pd
import re



class API():
    def __init__(self, search, progressbar):
        self.search_url = 'https://itunes.apple.com/search?'
        self.lookup_url = 'https://itunes.apple.com/lookup?'
        self.progressbar = progressbar
        
        # Get artist, album, and track data as dataframes
        self.get_artist(search)
        if self.artist_data is not None:
            self.get_albums()
            self.get_tracks()
        
        
    def get_tracks(self):
        self.progressbar.setValue(0)
        self.progressbar.show()
        
        # Return None if no albums
        if len(self.album_data)==0:
            self.track_data = None
            return
            
        self.tracks = {}
        for index, album_id in self.album_data.collectionId.iteritems():
            self.progressbar.setValue(round(100*(index+1)/len(self.album_data)))
            url = self.lookup_url + f'id={int(album_id)}&entity=song'
            results = requests.get(url).json()['results']
            track_data = pd.DataFrame(results)
            
            
            # Drop non-album entries
            non_track_entries = track_data.index[track_data.wrapperType!='track']
            track_data.drop(non_track_entries, inplace=True)
            track_data.reset_index(drop=True, inplace=True)
            track_data['trackNumber'] = track_data.index
        
            # If no songs (search collection instead), remove album
            if len(track_data)==0:
                self.album_data.drop(index, inplace=True)
                continue
            
            # Add 'cleaned' track column
            track_data['cleanName'] = track_data.trackName.apply(self.clean_name)
            track_data = track_data[track_data.cleanName.notna()]
        
            # Remove duplicate clean song names
            track_data.sort_values(by='cleanName', key=lambda x: x.str.len())
            track_data.drop_duplicates(subset=['trackName'], inplace=True)
            
            # Remove if fewer than 4 unique songs
            if len(track_data)<4:
                self.album_data.drop(index, inplace=True)
                continue
                
            # Add to multiindex dataframe
            if not hasattr(self, 'track_data'):
                self.track_data = track_data
            else:
                self.track_data = pd.concat([self.track_data, track_data])
        
        # Reset the indices of track_data and album_data
        self.track_data.set_index(['collectionId','trackNumber'], drop=True, inplace=True)
        self.album_data.reset_index(drop=True, inplace=True)
        self.progressbar.hide()
        return 
        
        
    def get_artist(self, search):
        url = self.search_url + f"limit=1&entity=musicArtist&attribute=artistTerm&term={search.replace(' ','+')}"
        result = requests.get(url).json()['results']
        
        if len(result)==0:
            self.artist_data = None
            self.album_data = None
            self.track_data = None
            return
            
        # Save results to Series
        self.artist_data = pd.Series(result[0])
        return
    
    def get_albums(self):
        url = self.lookup_url + f'entity=album&id={self.artist_data.artistId}'
        results = requests.get(url).json()['results']
        
        # Save results to dataframe
        album_data = pd.DataFrame(results)
        
        # Drop non-album entries
        non_album_entries = album_data.index[album_data.wrapperType!='collection']
        album_data.drop(non_album_entries, inplace=True)
        
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
        if name.endswith(' - Single'):
            return None
        name = re.sub('\(.*\)','',name)
        name = re.sub('(\/|\\|\||\?)[ ]?','',name)
        name = re.sub(' - .*','',name).strip()
        return name
        






