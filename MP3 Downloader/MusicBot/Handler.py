# -*- coding: utf-8 -*-
"""
Created on Sun Sep  4 11:53:55 2022

@author: afish
"""

import requests
import re
import pandas as pd
import numpy as np
from Blocks import Blocks
from collections import OrderedDict
import os
from pytube import Search
import mutagen
import subprocess
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pickle


# TO IMPLEMENT

class Handler():
    def __init__(self, app, SLACK_BOT_TOKEN, SLACK_BOT_USER_TOKEN):
        self.app = app
        self.SLACK_BOT_TOKEN = SLACK_BOT_TOKEN
        self.SLACK_BOT_USER_TOKEN = SLACK_BOT_USER_TOKEN
        self.Blocks = Blocks()
        
        self.song_url = 'https://itunes.apple.com/search?term={}&media=music&entity=song&limit={}'
        self.album_url = 'https://itunes.apple.com/search?term={}&media=music&entity=album&limit={}'
        
        self.download_folder = '../Downloads'
        
        CLIENT_ID = os.environ['SPOTIFY_CLIENT_ID']
        CLIENT_SECRET = os.environ['SPOTIFY_CLIENT_SECRET']
        credentials = SpotifyClientCredentials(client_id=CLIENT_ID,
                                               client_secret=CLIENT_SECRET)
        self.sp = spotipy.Spotify(client_credentials_manager=credentials)
        self.possible_commands = '''Possible commands:
            topten(artist_query)
            song(song_query)'''
        
    def parse_call(self, text, say):
        regex = re.compile('^([\w\s]*)\(([^\)]*)\)$')
        try:
            groups = regex.search(text).groups()
            keyword, item = [group.strip().lower() for group in groups]
        except:
            keyword = None
            item = None
        
        return keyword, item
    
    def clean_name(self, name):
        name = re.sub('\(.*\)','',name)
        name = re.sub('(\/|\\|\||\?)[ ]?','',name)
        name = re.sub(' - .*','',name).strip()
        return name
    
    def new_song(self, channel, search):
        # Get songs from Itunes API
        limit = 5
        url = self.song_url.format(search, limit)
        song_results = [f"{r['artistName']} - {self.clean_name(r['trackName'])} ({r['trackTimeMillis']} ms)"
                        for r in requests.get(url).json()['results']]
        song_results = list(OrderedDict.fromkeys(song_results))
        
        if len(song_results)==0:
            self.app.client.chat_postMessage(
                token=self.SLACK_BOT_USER_TOKEN,
                channel=channel,
                text = 'No results found'
            )
            return
        
        # Build blocks
        blocks = [
            self.Blocks.checkboxes('checkbox_id', "Song Results", song_results),
            self.Blocks.actions(self.Blocks.button('cancel_id','','Cancel', action_id='cancel_message')['accessory'],
                                self.Blocks.button('submit_id','','Download', action_id='download_song')['accessory'])
            ]
        
        # Display
        self.app.client.chat_postMessage(
            token=self.SLACK_BOT_USER_TOKEN,
            channel=channel,
            text = 'Default text',
            blocks = blocks
            )
        
    def top_ten(self, channel, search):
        # Get top ten from spotify api
        artist = self.sp.search(search, limit=1, type='artist')['artists']['items'][0]
        ['uri']
        topten = self.sp.artist_top_tracks(artist_id = artist['uri'])
        song_results = [f"{artist['name']} - {self.clean_name(track['name'])} ({track['duration_ms']} ms)"
                        for track in topten['tracks']]

        # Build blocks
        blocks = [
            self.Blocks.checkboxes('checkbox_id', "Top Tracks", song_results),
            self.Blocks.actions(self.Blocks.button('cancel_id','','Cancel', action_id='cancel_message')['accessory'],
                                self.Blocks.button('submit_id','','Download', action_id='download_song')['accessory'])
            ]
        
        # Display
        self.app.client.chat_postMessage(
            token=self.SLACK_BOT_USER_TOKEN,
            channel=channel,
            text = 'Default text',
            blocks = blocks
            )
        
    def handle_song_download(self, ack, body, logger, say):
        ack()

        # Grab selected songs
        selected_options = body['state']['values']['checkbox_id']['checkboxes-action']['selected_options']
        songs = [option['value'] for option in selected_options]
        
        # Download songs
        regex = re.compile('(.*) - (.*) \((.*) ms\)')
        for song in songs:
            track = dict(zip(['artist','song','time_ms'], regex.search(song).groups()))
            error = self.download_song(track)
            say(token=self.SLACK_BOT_USER_TOKEN,
                text=f'{song}: ' + error['message'])
            
        self.handle_cancellation(ack, body, logger)
        logger.info(body)
        
    def handle_cancellation(self, ack, body, logger):
        ack()
        ts = body['message']['ts']
        channel_id = body['channel']['id']
        self.app.client.chat_delete(token=self.SLACK_BOT_USER_TOKEN,
                                   channel=channel_id, 
                                   ts=ts,
                                   blocks=None)
        return
        
        
    def handle_message_events(self, event, say, ack):
        ack()
        # Musicbot only for Andrew
        if event['user']!='U041KR1G9TJ':
            return
        
        if 'text' not in event.keys():
            return
        
        if event['channel'][0] != 'D':
            print('Not a direct message')
            return
        
        keyword, item = self.parse_call(event['text'], say)
        
        # new game
        if keyword=='song':
            self.new_song(event['channel'], item)
        elif keyword=='topten':
            self.top_ten(event['channel'], item)
        elif keyword=='help':
            say(token = self.SLACK_BOT_USER_TOKEN,
                text=self.possible_commands)
            
    def download_song(self, track):
        '''Track_data needs to have song name, artist name, track length'''
        error = {'state':False, 'message':''}
        track["artist"] = track["artist"].replace('"','')
        
        # Check if file already exists
        filename = f'{track["artist"]} - {track["song"]}.mp4'
        path = os.path.join(self.download_folder, filename)
        if filename in os.listdir(self.download_folder):
            error = {'state':True, 
                     'message':f'Song already exists in {self.download_folder}'}
            return error
        
        query = f'{track["artist"]} - {track["song"]} lyrics'
        yts = Search(query).results[:3]
        
        yt_data = pd.DataFrame(columns=['length','title','views','rating'])
        for yt in yts:
            yt_data.loc[len(yt_data)] = [yt.length*1000 - int(track["time_ms"]),
                                         yt.title, yt.views, yt.rating]
        print('Compiled data on results')
        
        # Title must contain track name
        yt_data = yt_data[yt_data.title.str.lower().str.contains(track["song"].lower())]
        print('Requiring track name present')
        
        # Track must have correct length
        min_length = -10*1000
        max_length = 10*1000
        print(f'Time differences: {yt_data.length.values/1000} sec')
        yt_data = yt_data[yt_data.length.between(min_length, max_length)]
        print('Requiring correct length')
        
        # Sort by views
        yt_data.sort_values(by='views', ascending=False, inplace=True)
        print(f'Length of results: {len(yt_data)}')
        
        # Check if no download options
        if len(yt_data)==0:
            error = {'state':True, 
                     'message':f'No satisfactory youtube results'}
            return error
            
            
        print('Getting audio')
        audios = yts[yt_data.index[0]].streams.filter(only_audio=True, 
                                                           mime_type='audio/mp4')
        if len(audios)==0:
            error = {'state':True, 
                     'message':f'No audio download options'}
            return error
        
        try:        
            audios[-1].download(filename='temp.mp4')
            print('Downloaded audio')
        except Exception as e:
            error = {'state':True, 
                     'message':f'Download failed: {e}'}
            return error

        # Hack to fix time doubling
        try:
            ffmpeg_call = ['ffmpeg', '-i', 'temp.mp4', path]
            cmd = subprocess.run(ffmpeg_call, capture_output=True, encoding='UTF-8', shell=True)
            if cmd.returncode!=0:
                error = {'state':True, 
                         'message':cmd.stderr}
                return error
            os.remove('temp.mp4')
            print('finished ffmpeg call')
        except Exception as e:
            error = {'state':True, 
                     'message':f'ffmpeg call failed: {e}'}
            return error
        
        # Update song tags
        try:
            file = mutagen.File(path)
            #file.add_tags()
            file['\xa9nam']=track["song"]
            file['\xa9alb']='Main' #default album
            file['\xa9ART']=track["artist"].replace('"','')
            file.save()
            print('finished changing tags')
        except Exception as e:
            error = {'state':True, 
                     'message':f'Renaming song tags failed: {e}'}
            return error
        
        error['message'] = 'Downloaded successfully'
        return error
