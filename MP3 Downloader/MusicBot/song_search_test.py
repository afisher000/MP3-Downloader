# -*- coding: utf-8 -*-
"""
Created on Sun Sep 11 11:01:05 2022

@author: afisher
"""
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import requests

# search = 'read my mind'
# limit = 1
# # Search for a song
# stub = 'https://itunes.apple.com/search?'
# url = 'https://itunes.apple.com/search?term={}&media=music&entity=song&limit={}'
# results = requests.get(url.format(search, limit)).json()['results']

client_id = '36fea8a4d7a04483a1e4440e9f7eff95'
client_secret = '8bbeba13692748ba86958768462f9909'

credentials = SpotifyClientCredentials(client_id=client_id,
                                       client_secret=client_secret)

query = 'the killers'
sp = spotipy.Spotify(client_credentials_manager=credentials)
artist_id = sp.search(query, limit=1, type='artist')['artists']['items'][0]['uri']

tops = sp.artist_top_tracks(artist_id = artist_id)

for track in tops['tracks']:
    print(track['name'])


