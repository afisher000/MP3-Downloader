# -*- coding: utf-8 -*-
"""
Created on Sun Dec  5 11:12:36 2021

@author: afish
"""

from pytube import Search
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from subprocess import call
from os import mkdir, remove, path, environ
from tkinter import Tk, Button, Frame, Canvas, IntVar, Entry, Scrollbar, Label, Checkbutton
import re
from functools import partial
from urllib import request
from PIL import ImageTk, Image
from numpy import log10
from mutagen import File


environ['SPOTIPY_CLIENT_ID'] = '36fea8a4d7a04483a1e4440e9f7eff95'
environ['SPOTIPY_CLIENT_SECRET'] = '8bbeba13692748ba86958768462f9909'


def get_spotipy():
    auth_manager = SpotifyClientCredentials()
    return Spotify(auth_manager=auth_manager)



def clean_name(track):
    track = re.sub('(\/|\\|\||\?)[ ]?','',track) # remove bad file chars
    track = re.sub(' - .*','',track)
    track = re.sub('\(.*\)','',track).strip() # remove parentheticals
    return track
    
    
def check_album_name(album_name):
    # Take out albums with parentheticals for now
    if re.search('\(.*\)',album_name):
        return False
    if re.search(' - .*',album_name):
        return False
    return True


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
        self.iconbitmap('downloader.ico')
        
        # Color scheme
        self.button_color = '#999999'
        self.artist_pic_flag = 0
        self.searchlist = []
        
        ## Create Frames
        self.create_search_frame()
        self.create_add_song_frame()
        self.create_picture_frame()
        self.create_searchlist_frame()
        
        ## Confirm 'Downloaded Music' exists
        try:
            mkdir('Downloaded Music')
        except:
            pass

        
    def create_add_song_frame(self):
        frame = Frame(self)
        frame.grid(row=0,column=2,sticky='news')
        Button(frame,text='Add to searchlist',bg=self.button_color, font=('TkTextFont',18),command=self.add_songs_to_queue).grid(row=1,column=1,pady=10,padx=10)
        Button(frame,text='Clear searchlist',bg=self.button_color,font=('TkTextFont',18),command=self.clear_queue).grid(row=1,column=0,pady=10,padx=10)
        Button(frame,text='Download',bg=self.button_color,font=('TkTextFont',22),command=self.download_queue).grid(row=0,column=0,pady=30,columnspan=2)
        return frame
    
    
    
    def onFrameConfigure(self,event):
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
   
    def create_searchlist_frame(self):
        self.searchlist_canvas = Canvas(self,borderwidth=2,width = 200,bg=self.button_color)
        self.searchlist_frame = Frame(self.searchlist_canvas)
        self.vsb = Scrollbar(self,orient='vertical',command=self.searchlist_canvas.yview)
        self.searchlist_canvas.configure(yscrollcommand=self.vsb.set)
        
        self.vsb.grid(row=1,column=2,sticky='nse')
        self.searchlist_canvas.grid(row=1,column=2,sticky='news')
        self.searchlist_canvas.create_window((0,0),window=self.searchlist_frame,anchor='nw')
        self.searchlist_frame.bind('<Configure>',self.onSearchlistConfigure)
        
        self.searchlist_labels = []
        for row,search_entry in enumerate(self.searchlist):
            self.searchlist_labels.append(Label(self.searchlist_frame,bg=self.button_color, anchor='w', text=f'{row+1}: {search_entry}'))
            self.searchlist_labels[-1].grid(row=row,column=0,sticky='we')
        
    def onSearchlistConfigure(self,event):
        self.searchlist_canvas.configure(scrollregion=self.searchlist_canvas.bbox('all'))
        
    def create_data_frame(self):
        self.canvas = Canvas(self,borderwidth=0,background='#ffffff')
        self.albums_frame = Frame(self.canvas)
        self.data_hsb = Scrollbar(self,orient='horizontal',command=self.canvas.xview)
        self.data_vsb = Scrollbar(self,orient='vertical',command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=self.data_hsb.set, yscrollcommand=self.data_vsb.set)
        
        self.data_hsb.grid(row=1,column=0, sticky='wes',columnspan=2)
        self.data_vsb.grid(row=1,column=1, sticky='nse')
        self.canvas.grid(row=1,column=0,columnspan=2,sticky='news',padx=(0,15),pady=(0,15))
        self.canvas.create_window((0,0),window=self.albums_frame,anchor='nw')
        self.albums_frame.bind('<Configure>',self.onFrameConfigure)
       
        if not self.data:
            return
        
        num_cols = len(self.data['albums'])
        self.checkboxes = {}
        self.buttons = {}
        album_frames = {}
        for self.icol,self.album_name in enumerate(self.data['albums']):
            album_frames[self.album_name] = self.create_album_frame(self.albums_frame)
            album_frames[self.album_name].grid(row=1,column=self.icol,sticky='n,w')
        return
            
        
    def create_album_frame(self,container):
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
        states = list(map(lambda x: x.get(),self.checkboxes[album_name]))
        if False in states:
            new_state = True
        else:
            new_state = False
        for checkbox in self.checkboxes[album_name]:
            checkbox.set(new_state)
            
    def clear_checkboxes(self):
        [checkbox.set(0) for album_name in self.data['albums'] for checkbox in self.checkboxes[album_name]]
        return

    def create_search_frame(self):
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
        
        self.error_label = Label(frame,width=20,text='Errors')
        self.error_label.grid(row=0,rowspan=3,column=1)
        return frame
    
    def get_artist_info(self,event=None):
        search_artist = self.artist_entry.get()
        data = {}
        ## Grab artist and image
        try:
            artist = sp.search(search_artist,type='artist')['artists']['items'][0]
        except:
            self.error_log('No artist found')
            self.data = {}
            self.rebuild_artist_frames(0)
            return
        
        try:
            request.urlretrieve(artist['images'][0]['url'],'artist_image.jpg')
            data['artist'] = artist['name']
        except:
            self.error_log('Trouble getting image from url')
        
        # Get albums and tracks
        albums = sp.artist_albums(artist['uri'])['items']
        album_set = set()
        singles_set = set()
        for album in albums: #take out unnecessary albums ('Deluxe','Foreign Versions')
            if check_album_name(album['name']):
                track_set = {clean_name(track['name']) for track in sp.album(album['uri'])['tracks']['items']}
                if len(track_set)<3:
                    singles_set.update(track_set)
                else:
                    album_set.add(album['name'])
                    data[album['name']]= {'tracks':list(track_set),'length':len(track_set),'year':album['release_date'][:4]}
        
        album_list = list(album_set)
        album_years = [data[album_name]['year'] for album_name in album_list]
        data['albums'] = [album_name for year,album_name in sorted(zip(album_years,album_list),reverse=True)]

        
        
        # Get top tracks and singles
        top_tracks = list({clean_name(track['name']) for track in sp.artist_top_tracks(artist['uri'])['tracks']})
        if len(singles_set)>0:
            data['Singles'] = {'name':'Singles','tracks':list(singles_set)}
            data['albums'].insert(0,'Singles')
        data['Top Tracks'] = {'name':'Top Tracks','tracks':top_tracks}
        data['albums'].insert(0,'Top Tracks')
        
        self.data = data
        self.rebuild_artist_frames(1)
        return

    def rebuild_artist_frames(self,pic_flag):
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
        ## Figure this out!
        frame = Frame(self)
        frame.grid(row=0,column=0,sticky='w')
        try:
            if self.artist_pic_flag:
                self.img = ImageTk.PhotoImage(Image.open('artist_image.jpg').resize((200,200)))
            else:
                self.img = ImageTk.PhotoImage(Image.open('no artist.jpg').resize((200,200)))
            label = Label(frame,image=self.img,anchor='w')
            label.grid(row=0,column=0)
        except:
            self.error_log('Trouble showing artist cover photo')
        return frame


    def add_songs_to_queue(self):
        new_searches = set()
        for album_name in self.data['albums']:
            track_names = self.data[album_name]['tracks']
            new_searches.update({f"{self.data['artist']} - {track_names[i]}" for (i,checkbox) in enumerate(self.checkboxes[album_name]) if checkbox.get()})
        self.searchlist.extend(list(new_searches))
        self.searchlist = list(set(self.searchlist))
        self.searchlist_canvas.destroy()
        self.create_searchlist_frame()
        self.clear_checkboxes()
        return
    
    def clear_queue(self):
        self.searchlist=[]
        self.searchlist_canvas.destroy()
        self.create_searchlist_frame()
        return
    
    def download_queue(self):
        # Actually download
        
        # Print color based on time difference
        for idx,search in enumerate(self.searchlist):
            yt = self.best_youtube_result(search)
            status = self.download_song(search,yt)
            if status:
                self.searchlist_labels[idx].config(bg='green')
            else:
                self.searchlist_labels[idx].config(bg='red')
            self.update()
        self.clear_queue()
        
    def best_youtube_result(self,search):
        # Consider first 3 results
        yt_results = Search(search + ' lyrics').results[1:3]
        sp_time = sp.search(search,type='track')['tracks']['items'][0]['duration_ms'] / 1000
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
            return 0

        try:
            # Modify tag
            file = File(filename)
            file.add_tags()
            file['\xa9nam']=cur_track
            file['\xa9alb']='Main' #default album
            file['\xa9ART']=cur_artist
            file.save()
        except:
            self.error_log(f'!! Error changing file tags of {filename}')
            return 0
    
        try:
            # ffmpeg necessary to fix bug doubling audio length
            call(['ffmpeg','-i',filename,'Downloaded Music/'+filename],shell=True)
            remove(filename)
        except:
            self.error_log(f'!! Error copying {filename}')
            return 0
            
        return 1

    def error_log(self,errormsg):
        with open('error_log.txt','a') as f:
            print(errormsg)
            f.write(f'{errormsg}\n')
        self.error_label.configure(text = errormsg)
            
            
        
if __name__ == "__main__":
    sp = get_spotipy()
    app = App()
    app.mainloop()
