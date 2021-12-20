# -*- coding: utf-8 -*-
"""
Created on Sun Dec  5 11:12:36 2021

@author: afish
"""


import sys, os
def override_where():
    """ overrides certifi.core.where to return actual location of cacert.pem"""
    # in this case, I require cacert.pem to be in the same directory
    return 'cacert.pem'

# If program is compiled, 
if hasattr(sys, "frozen"):
    import certifi.core
    os.environ["REQUESTS_CA_BUNDLE"] = override_where()
    certifi.core.where = override_where

    # delay importing until after where() has been replaced
    import requests.utils
    import requests.adapters
    requests.utils.DEFAULT_CA_BUNDLE_PATH = override_where()
    requests.adapters.DEFAULT_CA_BUNDLE_PATH = override_where()


from pytube import Search
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from subprocess import call
from os import mkdir, remove, path
from tkinter import Tk, Button, Frame, Canvas, IntVar, Entry, Scrollbar, Label, Checkbutton
import re
from functools import partial
from urllib import request
from PIL import ImageTk, Image
from numpy import log10
import mutagen

# Set spotify API tokens
os.environ['SPOTIPY_CLIENT_ID'] = '36fea8a4d7a04483a1e4440e9f7eff95'
os.environ['SPOTIPY_CLIENT_SECRET'] = '8bbeba13692748ba86958768462f9909'


def clean_name(track):
    ''' Remove bad file chars, hyphen phrases, and parentheticals '''
    track = re.sub('(\/|\\|\||\?)[ ]?','',track)
    track = re.sub(' - .*','',track) 
    track = re.sub('\(.*\)','',track).strip()
    return track
    
    
def check_album_name(album_name):
    ''' Disregard albums with hyphen phrases and parentheticals for now'''
    #if re.search('\(.*\)',album_name):
    #    return False
    #if re.search(' - .*',album_name):
    #    return False
    return True

def get_spotipy():
    ''' Make connection to Spotify API'''
    auth_manager = SpotifyClientCredentials()
    return Spotify(auth_manager=auth_manager)
    
class App(Tk):
    def __init__(self):
        super().__init__()
        self.title('Youtube Downloader')
        self.geometry('1200x850')
        self.columnconfigure(0,weight=0)
        self.columnconfigure(1,weight=1)
        self.columnconfigure(2,weight=0)
        self.rowconfigure(0,weight=0)
        self.rowconfigure(1,weight=1)
        self.iconbitmap('icon.ico')
        
        # Color scheme
        self.button_color = '#999999'
        self.artist_pic_flag = 0
        self.queue = []
        
        ## Create Frames
        self.create_search_artist_frame()
        self.create_queue_options_frame()
        self.create_picture_frame()
        self.create_queue_frame()
        self.sp = get_spotipy()
        
        ## Confirm 'Downloaded Music' exists
        try:
            mkdir('Downloaded Music')
        except:
            pass

        
    def create_queue_options_frame(self):
        ''' Create frame with buttons that control the queue'''
        frame = Frame(self)
        frame.grid(row=0,column=2,sticky='news')
        Button(frame,text='Add to queue',bg=self.button_color, font=('TkTextFont',18),command=self.add_songs_to_queue).grid(row=1,column=1,pady=10,padx=10)
        Button(frame,text='Clear queue',bg=self.button_color,font=('TkTextFont',18),command=self.clear_queue).grid(row=1,column=0,pady=10,padx=10)
        Button(frame,text='Download',bg=self.button_color,font=('TkTextFont',22),command=self.download_queue).grid(row=0,column=0,pady=30,columnspan=2)
        return frame
    
    
    def onAlbumsConfigure(self,event):
        ''' Adapt scrollbars to match size of dataframe'''
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
   
    def create_queue_frame(self):
        ''' Create layout of queue and populate with songs in self.queue'''
        self.queue_canvas = Canvas(self,borderwidth=2,width = 200,bg=self.button_color)
        self.queue_frame = Frame(self.queue_canvas)
        self.queue_vsb = Scrollbar(self,orient='vertical',command=self.queue_canvas.yview)
        self.queue_canvas.configure(yscrollcommand=self.queue_vsb.set)
        
        self.queue_vsb.grid(row=1,column=2,sticky='nse')
        self.queue_canvas.grid(row=1,column=2,sticky='news')
        self.queue_canvas.create_window((0,0),window=self.queue_frame,anchor='nw')
        self.queue_frame.bind('<Configure>',self.onQueueConfigure)
        
        self.queue_labels = []
        for row,entry in enumerate(self.queue):
            self.queue_labels.append(Label(self.queue_frame,bg=self.button_color, anchor='w', text=f'{row+1}: {entry}'))
            self.queue_labels[-1].grid(row=row,column=0,sticky='we')
        
    def onQueueConfigure(self,event):
        ''' Adapt scrollbars to match size of queueframe'''
        self.queue_canvas.configure(scrollregion=self.queue_canvas.bbox('all'))
        
    def create_data_frame(self):
        ''' Create layout for display of albums by looping over calls to create_album_Frame'''
        self.canvas = Canvas(self,borderwidth=0,background='#ffffff')
        self.albums_frame = Frame(self.canvas)
        self.data_hsb = Scrollbar(self,orient='horizontal',command=self.canvas.xview)
        self.data_vsb = Scrollbar(self,orient='vertical',command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=self.data_hsb.set, yscrollcommand=self.data_vsb.set)
        
        self.data_hsb.grid(row=1,column=0, sticky='wes',columnspan=2)
        self.data_vsb.grid(row=1,column=1, sticky='nse')
        self.canvas.grid(row=1,column=0,columnspan=2,sticky='news',padx=(0,15),pady=(0,15))
        self.canvas.create_window((0,0),window=self.albums_frame,anchor='nw')
        self.albums_frame.bind('<Configure>',self.onAlbumsConfigure)
       
        if not self.data:
            return #No data
        
        num_cols = len(self.data['albums'])
        self.checkboxes = {}
        self.buttons = {}
        album_frames = {}
        for self.icol,self.album_name in enumerate(self.data['albums']):
            album_frames[self.album_name] = self.create_album_frame(self.albums_frame)
            album_frames[self.album_name].grid(row=1,column=self.icol,sticky='n,w')
        return
            
        
    def create_album_frame(self,container):
        '''Create frame for given album including button with album name and checkboxes for all tracks in the album'''
        frame = Frame(container)
        if self.album_name not in ['Top Tracks','Singles']:
            album_title = f'{self.album_name} ({str(self.data[self.album_name]["year"])})'
        else:
            album_title = f'{self.album_name}'
        
        self.buttons[self.album_name]= Button(frame,text=album_title, bg=self.button_color, command=partial(self.select_album_tracks,self.album_name)).grid(row=0,column=0,columnspan=2,pady=5,padx=5,sticky='W,E')
        self.checkboxes[self.album_name] = []
        for irow,track_name in enumerate(self.data[self.album_name]['tracks']):
            self.checkboxes[self.album_name].append(IntVar())
            Checkbutton(frame,variable = self.checkboxes[self.album_name][-1]).grid(column=0,row=irow+1,sticky='nw')
            Label(frame,text=track_name).grid(row=irow+1, column=1,sticky='w,n')
        return frame
    
    def select_album_tracks(self,album_name):
        ''' Selects all checkboxes when album button is pressed'''
        states = list(map(lambda x: x.get(),self.checkboxes[album_name]))
        if False in states:
            new_state = True
        else:
            new_state = False
        for checkbox in self.checkboxes[album_name]:
            checkbox.set(new_state)
            
    def clear_checkboxes(self):
        '''Clear all checkboxes for all albums'''
        [checkbox.set(0) for album_name in self.data['albums'] for checkbox in self.checkboxes[album_name]]
        return

    def create_search_artist_frame(self):
        ''' Create layout for artist search bar'''
        frame = Frame(self,bd=2,bg='#333333')
        frame.grid(row=0,column=1,sticky='wns')
        frame.rowconfigure(0,weight=1)
        frame.rowconfigure(1,weight=1)
        frame.rowconfigure(2,weight=1)
        Label(frame,width=20,text='Search Artist',bg = '#999999',font=('TkTextFont',20)).grid(row=0,column=0,sticky='w')
        self.artist_entry = Entry(frame, width=20,font=('TkTextFont',20))
        self.artist_entry.insert(0,'the killers')
        self.artist_entry.grid(row=1,column=0)
        self.artist_entry.bind('<Return>',self.get_artist_info)
        
        self.update_artist = Button(frame,width = 10,bg=self.button_color,  font=20, text='Update',command=self.get_artist_info)
        self.update_artist.grid(row=2,column=0)
        
        #self.error_label = Label(frame,width=100,height=30,text='Errors',wraplength=200,justify='left')
        #self.error_label.grid(row=0,rowspan=3,column=1)
        return frame
    
    def get_artist_info(self,event=None):
        '''Retrieve artist information from spotify including albums, top tracks, and singles.'''
        search_artist = self.artist_entry.get()
        data = {}
        ## Grab artist and image
        try:
            artist = self.sp.search(search_artist,type='artist')['artists']['items'][0]
        except Exception as e:
            self.error_log(e)
            self.data = {}
            self.rebuild_data_picture_frames(0)
            return
        
        try:
            request.urlretrieve(artist['images'][0]['url'],'artist_image.jpg')
            data['artist'] = artist['name']
        except:
            self.error_log('Trouble getting image from url')
        
        # Get albums and tracks
        albums = self.sp.artist_albums(artist['uri'])['items']
        album_set = set()
        singles_set = set()
        for album in albums: #take out unnecessary albums ('Deluxe','Foreign Versions')
            if check_album_name(album['name']):
                track_set = {clean_name(track['name']) for track in self.sp.album(album['uri'])['tracks']['items']}
                if len(track_set)<3:
                    singles_set.update(track_set)
                else:
                    album_set.add(album['name'])
                    data[album['name']]= {'tracks':list(track_set),'length':len(track_set),'year':album['release_date'][:4]}
        
        album_list = list(album_set)
        album_years = [data[album_name]['year'] for album_name in album_list]
        data['albums'] = [album_name for year,album_name in sorted(zip(album_years,album_list),reverse=True)]

        
        
        # Get top tracks and singles
        top_tracks = list({clean_name(track['name']) for track in self.sp.artist_top_tracks(artist['uri'])['tracks']})
        if len(singles_set)>0:
            data['Singles'] = {'name':'Singles','tracks':list(singles_set)}
            data['albums'].insert(0,'Singles')
        data['Top Tracks'] = {'name':'Top Tracks','tracks':top_tracks}
        data['albums'].insert(0,'Top Tracks')
        
        self.data = data
        self.rebuild_data_picture_frames(1)
        return

    def rebuild_data_picture_frames(self,pic_flag):
        ''' Updates frames to match the new searched artist '''
        try:
            self.data_frame.destroy()
            self.picture_frame.destroy()
        except:
            pass
        self.artist_pic_flag = pic_flag
        self.data_frame = self.create_data_frame()
        self.picture_frame = self.create_picture_frame()
        return
        
    
    def create_picture_frame(self):
        ''' Add cover photo for the searched artist '''
        frame = Frame(self)
        frame.grid(row=0,column=0,sticky='w')

        if self.artist_pic_flag:
            self.img = ImageTk.PhotoImage(Image.open('artist_image.jpg').resize((200,200)))
        else:
            self.img = ImageTk.PhotoImage(Image.open('no artist.jpg').resize((200,200)))
        label = Label(frame,image=self.img,anchor='w')
        label.grid(row=0,column=0)
        return frame

    def rebuild_queue(self):
        ''' Update queue to match the values in self.queue'''
        self.queue_canvas.destroy()
        self.create_queue_frame()
        return

    def add_songs_to_queue(self):
        ''' Add all songs with marked checkboxes to the queue. Then clear checkboxes'''
        new_searches = []
        for album_name in self.data['albums']:
            track_names = self.data[album_name]['tracks']
            new_searches.extend([f"{self.data['artist']} - {track_names[i]}" for (i,checkbox) in enumerate(self.checkboxes[album_name]) if checkbox.get()])
        self.queue.extend(new_searches)
        self.queue = list(set(self.queue)) #remove duplicates
        self.rebuild_queue()
        self.clear_checkboxes()
        return
    
    def clear_queue(self):
        ''' Clear all songs in self.queue and rebuilt the queue'''
        self.queue=[]
        self.rebuild_queue()
        return
    
    def download_queue(self):
        ''' Download all songs in queue to folder Downloaded Music '''
        for idx,entry in enumerate(self.queue):
            yt = self.best_youtube_result(entry)
            #status = self.download_song(entry,yt)
            color = 'green' if self.download_song(entry,yt) else 'red'
            self.queue_labels[idx].config(bg=color)
            #self.queue_labels[idx].config(bg='green')
            #if self.download_song(entry,yt):
            #    self.queue_labels[idx].config(bg='green')
            #else:
            #    self.queue_labels[idx].config(bg='red')
            self.update()
        self.clear_queue()
        
    def best_youtube_result(self,entry):
        ''' Return best youtube link as defined by time_socre, rating_score, and views_score '''
        # Consider first 3 results
        yt_results = Search(entry + ' lyrics').results[:3]
        sp_time = self.sp.search(entry,type='track')['tracks']['items'][0]['duration_ms'] / 1000
        #print(f'Spotify Time: {sp_time}')
        score = []
        for result in yt_results:
            time_score = -1*abs(result.length - sp_time)
            rating_score = 0 if result.rating is None else 2*result.rating
            views_score = 10*log10(result.views)
            score.append(time_score+rating_score+views_score)
            
        idx = score.index(max(score))
        return yt_results[idx]  
            
    def download_song(self,search,yt):
        ''' Download the youtube link. Create a file with correct info tags in Downloaded Music '''
        cur_artist = re.search('^.*(?= -)',search)[0]
        cur_track = re.search('(?<=- ).*',search)[0]
        filename = f'{cur_artist} - {cur_track}.mp4'
        
        if path.exists('Downloaded Music/'+filename):
            self.error_log(f'!! {filename} already exists in folder "Downloaded Music"')
            return
        
        # Download Audio file
        try:
            audio = yt.streams.filter(only_audio=True,mime_type='audio/mp4')[-1]
            if audio.filesize>1e6:
                audio.download(filename = filename)
                #print(f'Audio Time: {yt.length}\nRating: {yt.rating}\nViews: {yt.views}\n')
            else:
                self.error_log(f'!! "{filename}" is less than 1MB')
        except:
            self.error_log(f'!! Error downloading "{cur_track}" by "{cur_artist}"')
            return False

        try:
            # Modify tag
            file = mutagen.File(filename)
            file.add_tags()
            file['\xa9nam']=cur_track
            file['\xa9alb']='Main' #default album
            file['\xa9ART']=cur_artist
            file.save()
        except:
            self.error_log(f'!! Error changing file tags of {filename}')
            return False
    
        try:
            # ffmpeg necessary to fix bug doubling audio length
            call(['ffmpeg','-i',filename,'Downloaded Music/'+filename],shell=True)
            remove(filename)
        except:
            self.error_log(f'!! Error copying {filename}')
            return False
            
        return True

    def error_log(self,errormsg):
        ''' Write message to error_log '''
        with open('error_log.txt','a') as f:
            print(errormsg)
            f.write(f'{errormsg}\n')
            #self.error_label.configure(text = errormsg)
            
            
        
if __name__ == "__main__":
    app = App()
    app.mainloop()
