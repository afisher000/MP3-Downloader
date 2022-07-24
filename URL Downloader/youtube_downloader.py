# -*- coding: utf-8 -*-
"""
Created on Sat Jul 16 19:46:53 2022

@author: afisher
"""
from PyQt5 import QtCore as qtc
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5.Qt import Qt as qt
from PyQt5 import uic
import sys
import os
from pytube import YouTube
import subprocess
url = 'https://www.youtube.com/watch?v=0iYsBnj2BUk'


mw_Ui, mw_Base = uic.loadUiType('youtube_downloader.ui')
class MainWindow(mw_Ui, mw_Base):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.progress.hide()
        
        # Connect signals to slots
        self.download_button.pressed.connect(self.download_url)
        self.file_entry.returnPressed.connect(self.download_url)
        self.downloads_folder = 'URL Downloads'
        
        self.show()
        
        
    def download_url(self):
        # Read values
        folder = self.downloads_folder
        file = self.file_entry.text()
        url = self.url_entry.text()
        path = os.path.join(folder, file)
        self.progress.show()
        
        # Make sure 'URL Downloads' is a folder
        if not os.path.isdir(self.downloads_folder):
            os.mkdir(self.downloads_folder)
            
        # Download mp4
        yt = YouTube(url=url)     
        self.progress.setValue(25)
        audio = yt.streams.filter(only_audio=True, mime_type='audio/mp4')[-1]
        self.progress.setValue(50)
        audio.download(filename = 'temp.mp4')
        self.progress.setValue(75)
        ffmpeg_call = ['ffmpeg', '-i', 'temp.mp4', path+'.wav']
        cmd = subprocess.run(ffmpeg_call, capture_output=True, encoding='UTF-8', shell=True )
        if cmd.returncode!=0:
            print(cmd.stderr)
        os.remove('temp.mp4')
        self.progress.setValue(100)
        
        # Reset entries
        self.progress.hide()
        self.url_entry.setText('')
        self.file_entry.setText('')
        
        return
        
if __name__=='__main__':
    app = qtw.QApplication(sys.argv)
    w = MainWindow()
    