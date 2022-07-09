# -*- coding: utf-8 -*-
"""
Created on Mon Jul  4 10:06:03 2022

@author: afish
"""


import os
os.system('pyuic5 -x -o main_window.py main_window.ui')

import sys
from itunes_api import API
from pytube import Search
from main_window import Ui_Form
from PyQt5 import QtCore as qtc
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5.Qt import Qt as qt
from PIL import Image, ImageQt
import requests
from io import BytesIO
from functools import partial

# Add top songs list?
# Add loading icon (add window class to API?)

class Main_Window(qtw.QWidget):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Import Layout
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        
        self.queue = []
        self.ui.progressbar.hide()
        self.ui.add_songs_button.clicked.connect(self.add_to_queue)
        self.ui.clear_queue_button.clicked.connect(self.clear_queue)
        self.ui.search_button.clicked.connect(self.search_artist)
        self.ui.search_text.returnPressed.connect(self.search_artist)
        self.ui.search_text.setText('adele')
        
        #self.api = API('adele', self.ui.progressbar)
        #self.update_songs()


    def search_artist(self):
        self.api = API(self.ui.search_text.text(), self.ui.progressbar)
        self.update_songs()
        return
        
    def add_to_queue(self):
        for i,_id in enumerate(self.id_list):
            for j,box in enumerate(self.check_track[i]):
                if box.isChecked():
                    box.setChecked(False)
                    song = self.api.tracks[_id][j]
                    album = self.api.albums.name.loc[_id]
                    entry = f'{song} - {album}'
                    if entry not in self.queue:
                        self.queue.append(f'{song} - {album}')
            if self.check_album[i].isChecked():
                self.check_album[i].setChecked(False)
        self.update_queue()
        return

    def clear_queue(self):
        self.queue = []
        self.update_queue()
        return
    
    def update_queue(self):
        # Clear previous entries
        for j in reversed(range(self.ui.queue_list.count()-1)):
            self.ui.queue_list.itemAt(j).widget().setParent(None)
        
        # Rebuild queue
        for j, entry in enumerate(self.queue):
            label = qtw.QLabel(entry)
            self.ui.queue_list.insertWidget(self.ui.queue_list.count()-1, label)
        return
        
    def toggle_album(self, idx):
        # Check if any in check_track[idx] is true
        if self.check_album[idx].isChecked():
            [box.setChecked(True) for box in self.check_track[idx]]
        else:
            [box.setChecked(False) for box in self.check_track[idx]]
        return

        
    def update_songs(self):
        
        # Clear previous entries
        for j in reversed(range(self.ui.songs_grid.count())):
            self.ui.songs_grid.itemAt(j).widget().setParent(None)

        
        # Create grid
        self.check_track = []
        self.check_album = []
        self.id_list = self.api.tracks.keys()
        for col, key in enumerate(self.id_list):
            self.check_track.append([]) #add new list
            
            # Album checkbutton
            checkbutton = qtw.QCheckBox()
            #checkbutton.setFixedWidth(20)
            self.check_album.append(checkbutton)
            checkbutton.stateChanged.connect(partial(self.toggle_album,col))
            self.ui.songs_grid.addWidget(checkbutton, 0, col*3, 1, 1)
            
            # Album label
            label = qtw.QLabel(self.api.albums.name.loc[key])
            label.setFont(qtg.QFont('Times New Roman', 16))
            label.adjustSize()
            self.ui.songs_grid.addWidget(label, 0, col*3+1, 1, 1)
            #
            
            # Album image
            pixmap = qtw.QLabel()
            response = requests.get(self.api.albums.artwork_url.loc[key])
            Image.open(BytesIO(response.content)).save('test.jpg')
            pixmap.setPixmap(qtg.QPixmap('test.jpg'))
            self.ui.songs_grid.addWidget(pixmap, 0, col*3+2, 1, 1)
            
            for row, song in enumerate(self.api.tracks[key]):
                checkbutton = qtw.QCheckBox(song)
                self.check_track[-1].append(checkbutton)
                self.ui.songs_grid.addWidget(checkbutton, row+1, col*3, 1, 3)

        return
    

    
if __name__=='__main__':
    if not qtw.QApplication.instance():
        app = qtw.QApplication(sys.argv)
    else:
        app = qtw.QApplication.instance()
    w = Main_Window()
    w.show()

    #app.exec_()
    
    