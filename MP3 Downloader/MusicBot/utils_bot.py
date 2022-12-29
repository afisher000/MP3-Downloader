
import re
import requests
from collections import OrderedDict
import Blocks
import spotipy as sp
import os
import subprocess
import mutagen
import pytube
import pandas as pd
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy



def parse_slackbot_call(text):
    regex = re.compile('^([\w\s]*)\(([^\)]*)\)$')
    try:
        groups = regex.search(text).groups()
        keyword, item = [group.strip().lower() for group in groups]
    except:
        keyword = ''
        item = ''
    
    return keyword, item

def clean_name(name):
    name = re.sub('"','',name)
    name = re.sub('\(.*\)','',name)
    name = re.sub('(\/|\\|\||\?)[ ]?','',name)
    name = re.sub(' - .*','',name).strip()
    return name

def function_song(search):
    # Get songs from Itunes API
    song_url = 'https://itunes.apple.com/search?term={}&media=music&entity=song&limit={}'
    limit = 5
    url = song_url.format(search, limit)
    song_results = [f"{r['artistName']} - {clean_name(r['trackName'])} ({r['trackTimeMillis']} ms)"
                    for r in requests.get(url).json()['results']]
    song_results = list(OrderedDict.fromkeys(song_results))

    if len(song_results)==0:
        post_object = {'text': 'No results found'}
    else:
        post_object = { 
            'blocks':[
                Blocks.checkboxes('checkbox_id', "Song Results", song_results),
                Blocks.actions(
                    Blocks.button('cancel_id','','Cancel', action_id='cancel_message')['accessory'],
                    Blocks.button('submit_id','','Download', action_id='download_song')['accessory']
                )
            ],
            'text':'Error showing blocks' 
        }
    return post_object

    
def function_topten(search):
    # Get access to spotipy api
    SPOTIPY_CLIENT_ID = os.environ['SPOTIFY_CLIENT_ID']
    SPOTIPY_CLIENT_SECRET = os.environ['SPOTIFY_CLIENT_SECRET']
    credentials = SpotifyClientCredentials(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET
    )
    sp = spotipy.Spotify(client_credentials_manager=credentials)

    # Get top ten songs from spotify api
    artist = sp.search(search, limit=1, type='artist')['artists']['items'][0]
    topten = sp.artist_top_tracks(artist_id = artist['uri'])
    song_results = [f"{artist['name']} - {clean_name(track['name'])} ({track['duration_ms']} ms)"
                    for track in topten['tracks']]

    if len(song_results)==0:
        post_object = {'text': 'No results found'}
    else:
        post_object = { 
            'blocks':[
                Blocks.checkboxes('checkbox_id', "Top Tracks", song_results),
                Blocks.actions(
                    Blocks.button('cancel_id','','Cancel', action_id='cancel_message')['accessory'],
                    Blocks.button('submit_id','','Download', action_id='download_song')['accessory']
                    )        
            ],
            'text':'Error showing blocks' 
        }
    return post_object

def function_help(argument):
    post_object = { 
        'text': ( 
            'Possible commands:\n' 
            '\ttopten(artist_query)\n'
            '\tsong(song_query)'
        )
    }
    return post_object


def download_song(song_description):
    # Parse song_name into track object
    regex = re.compile('(.*) - (.*) \((.*) ms\)')
    artist, track, time_ms_str = regex.search(song_description).groups()

    # Check if file already exists
    filename = f'{artist} - {track}.mp4'
    download_folder = '../Downloads'
    path = os.path.join(download_folder, filename)
    if filename in os.listdir(download_folder):
        return {'text':f'{filename} already exists in {download_folder}'}
    

    # Search youtube
    query = f'{artist} - {track} lyrics'
    limit = 3
    yts = pytube.Search(query).results[:limit]
    
    # Compile data
    yt_data = pd.DataFrame(columns=['length','title','views','rating'])
    for yt in yts:
        yt_data.loc[len(yt_data)] = [yt.length*1000 - int(time_ms_str),
                                        yt.title, yt.views, yt.rating]
    
    # Title must contain track name
    yt_data = yt_data[yt_data.title.str.lower().str.contains(track.lower())]
    
    # Track must have correct length
    min_length = -10*1000
    max_length = 10*1000
    yt_data = yt_data[yt_data.length.between(min_length, max_length)]
    
    # Sort by views
    yt_data.sort_values(by='views', ascending=False, inplace=True)
    
    # Check if no download options
    if len(yt_data)==0:
        return {'text':f'No satisfactory youtube results for {filename}'}
        
    # Get audios
    audios = yts[yt_data.index[0]].streams.filter(only_audio=True, mime_type='audio/mp4')
    if len(audios)==0:
        return {'text':f'No audio download options for {filename}'}
    
    try:        
        audios[-1].download(filename='temp.mp4')
    except Exception as e:
        return {'text':f'{filename} pytube download failed with Exception: {e}'}

    # Use fmmpeg to fix bug where song length doubles
    try:
        ffmpeg_call = ['ffmpeg', '-i', 'temp.mp4', path]
        cmd = subprocess.run(ffmpeg_call, capture_output=True, encoding='UTF-8', shell=True)
        if cmd.returncode!=0:
            raise ValueError(cmd.stderr)
        os.remove('temp.mp4')
    except Exception as e:
        return {'text':f'{filename} ffmpeg conversion failed with Exception: {e}'}
    
    # Update song tags
    try:
        file = mutagen.File(path)
        file['\xa9nam']=track
        file['\xa9alb']='Main' # Default album
        file['\xa9ART']=artist
        file.save()
    except Exception as e:
        return {'text':f'{filename} metadata conversion with mutagen failed with Exception: {e}'}

    return {'text':f'{filename} downloaded successfully'}

