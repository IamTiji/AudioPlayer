from tkinter import *
from tkinter import filedialog
from PIL import Image, ImageTk

from pydub import playback

from threading import Thread, Event
from time import time

import math
import numpy as np
import colorsys as cs

import sys
import os

import configparser as cp

try: import src.utils as ut
except ModuleNotFoundError: import utils as ut

cfg = cp.ConfigParser()
cfg.read("../config.ini")
cfg.read("config.ini")

WIN_WIDTH =          int(cfg['SETTINGS']['WIN_WIDTH'])
WIN_HEIGHT =         int(cfg['SETTINGS']['WIN_HEIGHT'])
IMG_BASE_SIZE =      int(cfg['SETTINGS']['IMG_BASE_SIZE'])
IMG_SIZE_DIVD =      int(cfg['SETTINGS']['IMG_SIZE_DIVD'])
IMG_ROTATION =       int(cfg['SETTINGS']['IMG_ROTATION'])
IMG_ROT_SP =         int(cfg['SETTINGS']['IMG_ROT_SP'])
MAX_FPS =            int(cfg['SETTINGS']['MAX_FPS'])
COLOR_SPETM_DV =     int(cfg['SETTINGS']['COLOR_SPETM_DV'])
SLOWBAR_SP =         int(cfg['SETTINGS']['SLOWBAR_SP'])
BAR_SPER =           int(cfg['SETTINGS']['BAR_SPER'])
PLAYBAR_RES =        int(cfg['SETTINGS']['PLAYBAR_RES'])
PLAYBAR_WIDTH =      int(cfg['SETTINGS']['PLAYBAR_WIDTH'])
PLAYBAR_LINE_WIDTH = int(cfg['SETTINGS']['PLAYBAR_LINE_WIDTH'])

class AudioPlayer:
    def __init__(self):
        self.tk = Tk()
        self.t = Canvas(self.tk, background='black', width=WIN_WIDTH, height=WIN_HEIGHT)
        self.t.pack()

        self.targetforder = ''
        self.listtoplay = []
        self.targetsource = ''
        self.audioindex = 0
        self.startevent = Event()
        self.slowbar = None
        self.framedrop = 0

        try: self.mask = Image.open("assets/mask.png")
        except FileNotFoundError: self.mask = Image.open("../assets/mask.png")
        self.mask = self.mask.convert('L')
        
        self.tk.title('Audio Player')

        self.load()
        self.audio()
        self.render()

        self.tk.geometry(f"{WIN_WIDTH}x{WIN_HEIGHT}")
        self.tk.resizable(0, 0)
        self.tk.after(1000, self.tk.event_generate('<<Start>>'))
        self.tk.deiconify()
        self.tk.mainloop()

    def load(self):
        if len(sys.argv) > 1:
            self.path = sys.argv[1]
        else:
            self.path = filedialog.askopenfilename(filetypes=[("MP3 files","*.mp3")])

        self.tk.title(os.path.basename(self.path))
        
        self.a, self.data = ut.read_audio(self.path)
        icon = ut.get_icon(self.path)
        self.icon = ut.mask(self.mask, icon)

        self.audiovitwhole = ut.data_to_xy(self.data, PLAYBAR_WIDTH, WIN_WIDTH/2 - PLAYBAR_WIDTH/2, 100, PLAYBAR_RES)
        
    def audio(self):
        audioThread = Thread(daemon=True, target=self.play_audio)

        self.audiostarttime = time()
        self.tk.bind('<<Start>>', lambda e:self.startevent.set())

        audioThread.start()
        
    def play_audio(self):
        self.startevent.wait()

        playback._play_with_pyaudio(self.a)
    
    def render(self):
        if self.a.duration_seconds < time()-self.audiostarttime:
            self.tk.destroy()
            return
        
        renderstarttime = time()

        self.t.delete("all")

        bar = ut.fft(self.data, time()-self.audiostarttime)
        barthickness = WIN_WIDTH/bar.shape[0]

        if self.slowbar is None:
            self.slowbar = np.zeros(bar.shape)

        self.slowbar = ut.compute_slowbar(bar, self.slowbar, SLOWBAR_SP)

        color = ut.rgb_values_to_hex(cs.hsv_to_rgb(((time()-self.audiostarttime)/COLOR_SPETM_DV)%1, 1, 1))

        for i in range(bar.shape[0]):
            self.t.create_rectangle(i*barthickness, WIN_HEIGHT, (i+1)*barthickness-BAR_SPER, WIN_HEIGHT-bar[i], fill="black", outline=color)
            self.t.create_line(i*barthickness, WIN_HEIGHT-self.slowbar[i], (i+1)*barthickness-BAR_SPER, WIN_HEIGHT-self.slowbar[i], fill=color)

        ampilitude = ut.get_ampiltude(self.data, time()-self.audiostarttime, 50)

        self.midimg = ImageTk.PhotoImage(image=self.icon
                                          .resize((round(IMG_BASE_SIZE*(ampilitude/IMG_SIZE_DIVD)), round(IMG_BASE_SIZE*(ampilitude/IMG_SIZE_DIVD))))
                                          .rotate(math.sin((time()-self.audiostarttime)*IMG_ROT_SP)*IMG_ROTATION, Image.BICUBIC))
        self.t.create_image(WIN_WIDTH / 2, WIN_HEIGHT / 2, image=self.midimg)

        self.t.create_polygon(self.audiovitwhole, fill=color)
        playbarpos = PLAYBAR_WIDTH/self.a.duration_seconds*(time()-self.audiostarttime)
        self.t.create_line(playbarpos, 0, playbarpos, 150, fill="black", width=PLAYBAR_LINE_WIDTH)

        self.t.after(max(round((1 / MAX_FPS - (time() - renderstarttime)) * 1000), 0), self.render)

if __name__ == "__main__":
    AudioPlayer()