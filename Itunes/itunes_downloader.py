# -*- coding: utf-8 -*-
"""
Created on Mon Jul  4 10:06:03 2022

@author: afish
"""

import sys
from itunes_api import API
from PyQt5 import QtCore as qtc
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5.Qt import Qt as qt
from PyQt5 import uic
import requests
from PIL import Image
from io import BytesIO
from functools import partial
from pytube import Search
import pandas as pd
import os
import mutagen
import subprocess
import time
import sounddevice as sd
import soundfile as sf

# Include singles or top tracks?
# Include sample of song

mw_Ui, mw_Base = uic.loadUiType('main_window.ui')
class Main_Window(mw_Base, mw_Ui):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Import Layout
        self.setupUi(self)
        self.progressbar.hide()
        self.queue_strings = []
        self.queue_ids = []

        # Connect signals and slots
        self.search_text.returnPressed.connect(self.search_artist)
        self.search_artist_button.clicked.connect(self.search_artist)
        self.add_songs_button.clicked.connect(self.add_songs)
        self.clear_queue_button.clicked.connect(self.clear_queue)
        self.download_button.clicked.connect(self.download_queue)
        self.stop_preview_button.clicked.connect(sd.stop)

        # Downloads
        self.download_folder = 'Downloads'
        self.search_text.setText('the killers')
        self.search_artist()
    
    
    def error_log(self,errormsg):
        ''' Write message to error_log '''
        with open('error_log.txt','a') as f:
            print(errormsg)
            f.write(f'{errormsg}\n\n')

            
    def download_song(self, track_data):
        # Check if file already exists
        filename = f'{track_data.artistName} - {track_data.cleanName}.mp4'
        path = os.path.join(self.download_folder, filename)
        if filename in os.listdir(self.download_folder):
            self.error_log(f'{filename} already exists in {self.download_folder}')
            return 1
        
        
        query = f'{track_data.cleanName} - {track_data.artistName} lyrics'
        yts = Search(query).results[:3]
        print(f'Search query: {query}')
        
        yt_data = pd.DataFrame(columns=['length','title','views','rating'])
        for yt in yts:
            yt_data.loc[len(yt_data)] = [yt.length*1000 - track_data.trackTimeMillis,
                                         yt.title, yt.views, yt.rating]
        print('Compiled data on results')
        
        # Title must contain track name
        yt_data = yt_data[yt_data.title.str.lower().str.contains(track_data.cleanName.lower())]
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
            self.error_log(f'Length of yt_data is zero for {query}')
            return 1
            
            
        print('Getting audio')
        audios = yts[yt_data.index[0]].streams.filter(only_audio=True, 
                                                           mime_type='audio/mp4')
        if len(audios)==0:
            self.error_log(f'Length of audios is zero for {query}')
            return 1
        
        try:        
            audios[-1].download(filename='temp.mp4')
            print('Downloaded audio')
        except Exception as e:
            self.error_log(f'Download for query {query} failed: {e}')
            return 1

        
        # Hack to fix time doubling
        try:
            ffmpeg_call = ['ffmpeg', '-i', 'temp.mp4', path]
            cmd = subprocess.run(ffmpeg_call, capture_output=True, encoding='UTF-8', shell=True)
            if cmd.returncode!=0:
                print(cmd.stderr)
                return 1
            os.remove('temp.mp4')
            print('finished ffmpeg call')
        except Exception as e:
            self.error_log(f'ffmpeg call failed for query {query}: {e}')
            return 1
        
        # Update song tags
        try:
            file = mutagen.File(path)
            #file.add_tags()
            file['\xa9nam']=track_data.cleanName
            file['\xa9alb']='Main' #default album
            file['\xa9ART']=track_data.artistName
            file.save()
            print('finished changing tags')
        except Exception as e:
            self.error_log(f'Renaming song tags with mutagen failed for {filename}: {e}')
            return 1
        
        return 0
    

    def download_queue(self):
        # Make download folder if does not exist
        if not os.path.isdir(self.download_folder):
            os.mkdir(self.download_folder)
            
        for index, track_id in enumerate(self.queue_ids):
            # Download song from youtube
            # Save/change data and write error log from another class
            # Change queue label colors for success/failure
            track_data = self.api.track_data[self.api.track_data.trackId==track_id].iloc[0]
            self.test = track_data
            error_status = self.download_song(track_data)
            error_to_color = {0:'green', 1:'red'}
            label = self.queue_list.itemAt(index).widget()
            label.setStyleSheet(f"background-color: {error_to_color[error_status]}")
            label.repaint()
            time.sleep(0.1)
            
        return

    def add_songs(self):
        for i in range(len(self.track_checkboxes)):
            for j, box in enumerate(self.track_checkboxes[i]):
                if box.isChecked():
                    box.setChecked(False)
                    album_id = int(self.api.album_data.collectionId[i])
                    track_name = self.api.track_data.loc[(album_id, j), 'cleanName']
                    track_id = int(self.api.track_data.loc[(album_id, j), 'trackId'])
                    album_name = self.api.album_data.cleanName[i]
                    artist_name = self.api.artist_data.artistName
                    entry = f'{artist_name} - {track_name}'
                    if entry not in self.queue_strings:
                        self.queue_strings.append(entry)
                        self.queue_ids.append(track_id)
            if self.album_checkboxes[i].isChecked():
                self.album_checkboxes[i].setChecked(False)
        self.update_queue()
        return

    def clear_queue(self):
        self.queue_strings = []
        self.queue_ids = []
        self.update_queue()
        return
    
    def update_queue(self):
        # Clear previous entries
        for j in reversed(range(self.queue_list.count()-1)):
            self.queue_list.itemAt(j).widget().setParent(None)
        
        # Rebuild queue
        for j, entry in enumerate(self.queue_strings):
            label = qtw.QLabel(entry)
            self.queue_list.insertWidget(self.queue_list.count()-1, label)
        return
        
    def toggle_album(self, idx):
        # Check if any in track_checkboxes[idx] is true
        if self.album_checkboxes[idx].isChecked():
            [box.setChecked(True) for box in self.track_checkboxes[idx]]
        else:
            [box.setChecked(False) for box in self.track_checkboxes[idx]]
        return

    def preview_song(self, track_id):
        track = self.api.track_data[self.api.track_data.trackId==track_id].iloc[0]
        preview_url = track.previewUrl
        
        r = requests.get(preview_url)
        
        # Read to mp4
        with open('temp.mp4', 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        
        # Convert to wav
        ffmpeg_call = ['ffmpeg', '-i', 'temp.mp4', 'temp.wav']
        cmd = subprocess.run(ffmpeg_call, capture_output=True, encoding='UTF-8', shell=True)
        if cmd.returncode!=0:
            print(cmd.stderr)
        os.remove('temp.mp4')
        # Play
        data, fs = sf.read('temp.wav')
        sd.play(data, fs)
        os.remove('temp.wav')
        
    def search_artist(self):
        self.api = API(self.search_text.text(), self.progressbar)
        
        if self.api.track_data is None:
            self.search_text.setText('No artist found...')
            return
        
        # Update search_box to artist name
        self.search_text.setText(self.api.artist_data.artistName)
        
        # Delete song container widget
        if hasattr(self, 'songcnt'):
            self.songcnt.setParent(None)
            
        # Create song container widget
        self.songcnt = qtw.QWidget()
        self.scrollArea.setWidget(self.songcnt)
        columns = qtw.QHBoxLayout(self.songcnt)
        
        # Loop over albums
        self.track_checkboxes = []
        self.album_checkboxes = []
        for icol, album in self.api.album_data.iterrows():
            self.track_checkboxes.append([]) #add new list
            
            # Create widgets and layouts
            column = qtw.QVBoxLayout()
            
            # Create header
            header = qtw.QHBoxLayout()
            
            album_checkbox = qtw.QCheckBox(album.cleanName)
            album_title_font = qtg.QFont()
            album_title_font.setPointSize(14)
            album_checkbox.setFont(album_title_font)
            album_checkbox.setSizePolicy(qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Preferred)
            album_checkbox.stateChanged.connect(partial(self.toggle_album, icol))
            self.album_checkboxes.append(album_checkbox)
            header.addWidget(album_checkbox)
            
            album_img = qtw.QLabel()
            response = requests.get(album.artworkUrl60)
            Image.open(BytesIO(response.content)).save('test.jpg')
            album_img.setPixmap(qtg.QPixmap('test.jpg'))
            album_img.setSizePolicy(qtw.QSizePolicy.Minimum, qtw.QSizePolicy.Preferred)
            header.addWidget(album_img)
            
            column.addLayout(header)
            
            # Populate tracks
            for irow, track in self.api.track_data.loc[album.collectionId].iterrows():
                track_checkbox = qtw.QCheckBox(track.cleanName)
                track_checkbox.setSizePolicy(qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Preferred)
                self.track_checkboxes[-1].append(track_checkbox)
                preview = qtw.QPushButton('Preview')
                preview.clicked.connect(partial(self.preview_song, track.trackId))
                preview.setSizePolicy(qtw.QSizePolicy.Minimum,qtw.QSizePolicy.Preferred)
                
                row = qtw.QHBoxLayout()
                row.addWidget(track_checkbox)
                row.addWidget(preview)
                
                column.addLayout(row)
            column.addStretch()
            columns.addLayout(column)
        return

    
if __name__=='__main__':
    if not qtw.QApplication.instance():
        app = qtw.QApplication(sys.argv)
    else:
        app = qtw.QApplication.instance()
    w = Main_Window()
    w.show()

    #app.exec_()
    
    