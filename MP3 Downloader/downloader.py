# -*- coding: utf-8 -*-
"""
Created on Mon Jul  4 10:06:03 2022

@author: afish
"""

import sys
from itunes_api_multithreading import API
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
import concurrent.futures

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

    
        self.download_folder = 'Downloads'
        self.search_text.setText('dua lipa')
        self.search_artist()
    
    
    def error_log(self,errormsg):
        ''' Write message to error_log '''
        with open('error_log.txt','a') as f:
            print(errormsg)
            f.write(f'{errormsg}\n\n')

            
    def download_song(self, track_data, queue_index):
        
        def change_label_color(queue_index, error_status):
            status_to_color = {0:'green', 1:'red'}
            color = status_to_color[error_status]
            label = self.queue_list.itemAt(queue_index).widget()
            label.setStyleSheet(f"background-color: {color}")
            label.repaint()
            return
            
            
        # Check if file already exists
        filename = f'{track_data.artistName} - {track_data.cleanName}.mp4'
        path = os.path.join(self.download_folder, filename)
        if filename in os.listdir(self.download_folder):
            self.error_log(f'{filename} already exists in {self.download_folder}')
            change_label_color(queue_index, 1)
            return 1

        query = f'{track_data.cleanName} - {track_data.artistName} lyrics'
        yts = Search(query).results[:5]
        # print(f'Search query: {query}')
        
        yt_data = pd.DataFrame(columns=['length','title','views','rating'])
        for yt in yts:
            yt_data.loc[len(yt_data)] = [yt.length*1000 - track_data.trackTimeMillis,
                                         yt.title, yt.views, yt.rating]
        
        # Title must contain track name
        yt_data = yt_data[yt_data.title.str.lower().str.contains(track_data.cleanName.lower())]

        
        # Track must have correct length
        min_length = -10*1000
        max_length = 10*1000
        yt_data = yt_data[yt_data.length.between(min_length, max_length)]
        
        # Sort by views
        yt_data.sort_values(by='views', ascending=False, inplace=True)
        
        # Check if no download options
        if len(yt_data)==0:
            self.error_log(f'Length of yt_data is zero for {query}')
            change_label_color(queue_index, 1)
            return 1
            
        audios = yts[yt_data.index[0]].streams.filter(only_audio=True, 
                                                           mime_type='audio/mp4')
        if len(audios)==0:
            self.error_log(f'Length of audios is zero for {query}')
            change_label_color(queue_index, 1)
            return 1
        
        try:        
            audios[-1].download(filename=filename)
        except Exception as e:
            self.error_log(f'Download for query {query} failed: {e}')
            change_label_color(queue_index, 1)
            return 1

        
        # Hack to fix time doubling
        try:
            ffmpeg_call = ['ffmpeg', '-i', filename, path]
            cmd = subprocess.run(ffmpeg_call, capture_output=True, encoding='UTF-8', shell=True)
            if cmd.returncode!=0:
                print(cmd.stderr)
                change_label_color(queue_index, 1)
                return 1
            os.remove(filename)
        except Exception as e:
            self.error_log(f'ffmpeg call failed for query {query}: {e}')
            change_label_color(queue_index, 1)
            return 1
        
        # Update song tags
        try:
            file = mutagen.File(path)
            #file.add_tags()
            file['\xa9nam']=track_data.cleanName
            file['\xa9alb']='Main' #default album
            file['\xa9ART']=track_data.artistName
            file.save()
        except Exception as e:
            self.error_log(f'Renaming song tags with mutagen failed for {filename}: {e}')
            change_label_color(queue_index, 1)
            return 1
        
        print(f'Successfully downloaded {filename}')
        change_label_color(queue_index, 0)
        return 0
    

    def download_queue(self):
        # Make download folder if does not exist
        if not os.path.isdir(self.download_folder):
            os.mkdir(self.download_folder)
            
        # Reset errorlog
        if os.path.exists('error_log.txt'):
            os.remove('error_log.txt')    
        
        t1 = time.perf_counter()

        # Multithreading
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for queue_index, track_id in enumerate(self.queue_ids):
                track_data = self.api.track_data[self.api.track_data.trackId==track_id].iloc[0]
                future = executor.submit(self.download_song, track_data, queue_index)

        t2 = time.perf_counter()
        print(f'Download time = {t2-t1:0f} seconds')
            
        self.clear_queue()
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
        ''' Retrieves preview from itunes. Saves the data to file then plays
        using the sounddevice library.'''
        
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
        t1 = time.perf_counter()
        if self.api.track_data is None:
            self.search_text.setText('No artist found...')
            self.songcnt.setParent(None)
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
            
            if isinstance(album.cleanName, float):
                print(album)
                
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
            Image.open(BytesIO(response.content)).save('temp.jpg')
            album_img.setPixmap(qtg.QPixmap('temp.jpg'))
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
        os.remove('temp.jpg')
        
        t2 = time.perf_counter()
        print(f'GUI Display time = {t2-t1:.1f} seconds')
        return
    
    
if __name__=='__main__':
    if not qtw.QApplication.instance():
        app = qtw.QApplication(sys.argv)
    else:
        app = qtw.QApplication.instance()
    w = Main_Window()
    w.show()

    #app.exec_()
    
    