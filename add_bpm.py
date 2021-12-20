# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import os
import subprocess
from scipy.io import wavfile
from scipy.interpolate import interp1d
from scipy.fft import fft
import numpy as np
import mutagen

directory = 'C:/Users/afish/Music/Music - Python Download/'

def get_Fourier(data,Fs, fmin=1.5, fmax=3.5):
    ''' 
    Take fourier transform of data, return amplitudes and frequencies 
    in range [fmin,fmax].
    '''

    L = len(data)
    F = np.arange(int(L/2))/L*Fs
    DATA = fft(data)
    P = 2*abs(DATA[:int(L/2)]/L)
    
    if fmin>fmax:
        print(f'! Error: Fmin > Fmax (fmin={fmin}, fmax={fmax})')
    if fmin:
        mask = (F>fmin) * (F<fmax)
        return F[mask], P[mask]
    return F,P
    
def signal_envelope(data,Fs):
    ''' 
    Return upper envelope of audio signal.
    To avoid false maximums in data noise, potential maximums are 
    checked against a given decay per period from the previous maximum.
    '''
    
    decay_per_period = .05
    f0 = 100 # assumed central frequency
    decay_ratio = decay_per_period / (Fs/f0)
    
    # Add start points
    u_x = [0]
    u_y = [0]
    
    prevmax_y = 0
    prevmax_x = 0
    
    # Find all maximums
    for idx in np.arange(1,len(data)-1):
        if data[idx]>data[idx-1] and data[idx]>data[idx+1]:
            # Compare against decay from curmax
            if data[idx] > prevmax_y * ( 1 - decay_ratio * (idx-prevmax_x) ):
                u_x.append(idx)
                u_y.append(data[idx])
                prevmax_x = idx
                prevmax_y = data[idx]
            
    # Add endpoints
    u_x.append(len(data)-1)
    u_y.append(data[-1])
    
    # Interpolate maximums
    f_interp = interp1d(u_x, u_y)
    return f_interp(np.arange(len(data)))
            
def data_fragment(data,Fs,idx_skip=50):
    ''' 
    Returns a fragment of original data for fasting processing. 
    Standard sampling frequencies are much larger than necessary.
    idx_skip: Use 1/idx_skip of the datapoints
    '''
    mask = np.arange(0,len(data)-1,idx_skip)
    Fs_new = Fs/idx_skip
    fragment = data[mask,1]
    return fragment, Fs_new
    
def set_bpm_tag(song,bpm):
    ''' Add bpm to the file's tags'''
    global directory
    file = mutagen.File(directory+song)
    file['tmpo'] = [int(bpm)]
    file.save()

def check_bpm_tag(song):
    ''' Return true if song has bpm tag, false otherwise.'''
    global directory
    file = mutagen.File(directory+song)
    test = list(file.keys())
    return 'tmpo' in list(file.keys())


##-----##---- Main Code -----##------##
# Grab audio files in directory
songs = []
for file in os.listdir(directory):
    if file[-4:].lower() in ['.mp3','.mp4']:
        songs.append(file)        


for i,song in enumerate(songs):
    print(f'{i+1} of {len(songs)}: {song}')
    
    # Skip songs with bpm tag
    retag = 0
    if check_bpm_tag(song) and not retag:
        print('\tBPM tag already exists...')
        continue
    
    # Convert to wav
    
    subprocess.call(['ffmpeg','-y','-i',directory+song,'temp.wav'],shell=True)
    Fs, data = wavfile.read('temp.wav')

    # Get upper envelope for fragment of audio signal
    audio_clip, Fs = data_fragment(data,Fs)
    envelope = signal_envelope(audio_clip, Fs)
    
    # Return fourier transform, compute bpm
    freq, amp = get_Fourier(envelope, Fs)
    bpm = round(60 * freq[np.argmax(amp)])
    
    # Change bpm
    set_bpm_tag(song,bpm)
    os.remove('temp.wav')
