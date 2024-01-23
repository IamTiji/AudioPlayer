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

import src.utils as ut

global WIN_WIDTH

WIN_WIDTH=         0         
WIN_HEIGHT=        0        
IMG_BASE_SIZE=     0     
IMG_SIZE_DIVD=     0     
IMG_ROTATION=      0      
IMG_ROT_SP=        0        
MAX_FPS=           0           
COLOR_SPETM_DV=    0    
SLOWBAR_SP=        0        
BAR_SPER=          0          
PLAYBAR_RES=       0       
PLAYBAR_WIDTH=     0     
PLAYBAR_LINE_WIDTH=0

cfg = cp.ConfigParser()
cfg.read("config.ini")

def cfg_fix():
    cfg.add_section('SETTINGS')

    cfg.set('SETTINGS', 'WIN_WIDTH',          '800')
    cfg.set('SETTINGS', 'WIN_HEIGHT',         '600')
    cfg.set('SETTINGS', 'IMG_BASE_SIZE',      '150')
    cfg.set('SETTINGS', 'IMG_SIZE_DIVD',      '70' )
    cfg.set('SETTINGS', 'IMG_ROTATION',       '20' )
    cfg.set('SETTINGS', 'IMG_ROT_SP',         '2'  )
    cfg.set('SETTINGS', 'MAX_FPS',            '30' )
    cfg.set('SETTINGS', 'COLOR_SPETM_DV',     '4'  )
    cfg.set('SETTINGS', 'SLOWBAR_SP',         '5'  )
    cfg.set('SETTINGS', 'BAR_SPER',           '5'  )
    cfg.set('SETTINGS', 'PLAYBAR_RES',        '800')
    cfg.set('SETTINGS', 'PLAYBAR_WIDTH',      '800')
    cfg.set('SETTINGS', 'PLAYBAR_LINE_WIDTH', '4'  )

    cfg.write(open("config.ini", "w"))

try:
    WIN_WIDTH =          int(cfg['SETTINGS']['WIN_WIDTH'         ])
    WIN_HEIGHT =         int(cfg['SETTINGS']['WIN_HEIGHT'        ])
    IMG_BASE_SIZE =      int(cfg['SETTINGS']['IMG_BASE_SIZE'     ])
    IMG_SIZE_DIVD =      int(cfg['SETTINGS']['IMG_SIZE_DIVD'     ])
    IMG_ROTATION =       int(cfg['SETTINGS']['IMG_ROTATION'      ])
    IMG_ROT_SP =         int(cfg['SETTINGS']['IMG_ROT_SP'        ])
    MAX_FPS =            int(cfg['SETTINGS']['MAX_FPS'           ])
    COLOR_SPETM_DV =     int(cfg['SETTINGS']['COLOR_SPETM_DV'    ])
    SLOWBAR_SP =         int(cfg['SETTINGS']['SLOWBAR_SP'        ])
    BAR_SPER =           int(cfg['SETTINGS']['BAR_SPER'          ])
    PLAYBAR_RES =        int(cfg['SETTINGS']['PLAYBAR_RES'       ])
    PLAYBAR_WIDTH =      int(cfg['SETTINGS']['PLAYBAR_WIDTH'     ])
    PLAYBAR_LINE_WIDTH = int(cfg['SETTINGS']['PLAYBAR_LINE_WIDTH'])
except (ValueError, KeyError):
    cfg_fix()
    WIN_WIDTH =          int(cfg['SETTINGS']['WIN_WIDTH'         ])
    WIN_HEIGHT =         int(cfg['SETTINGS']['WIN_HEIGHT'        ])
    IMG_BASE_SIZE =      int(cfg['SETTINGS']['IMG_BASE_SIZE'     ])
    IMG_SIZE_DIVD =      int(cfg['SETTINGS']['IMG_SIZE_DIVD'     ])
    IMG_ROTATION =       int(cfg['SETTINGS']['IMG_ROTATION'      ])
    IMG_ROT_SP =         int(cfg['SETTINGS']['IMG_ROT_SP'        ])
    MAX_FPS =            int(cfg['SETTINGS']['MAX_FPS'           ])
    COLOR_SPETM_DV =     int(cfg['SETTINGS']['COLOR_SPETM_DV'    ])
    SLOWBAR_SP =         int(cfg['SETTINGS']['SLOWBAR_SP'        ])
    BAR_SPER =           int(cfg['SETTINGS']['BAR_SPER'          ])
    PLAYBAR_RES =        int(cfg['SETTINGS']['PLAYBAR_RES'       ])
    PLAYBAR_WIDTH =      int(cfg['SETTINGS']['PLAYBAR_WIDTH'     ])
    PLAYBAR_LINE_WIDTH = int(cfg['SETTINGS']['PLAYBAR_LINE_WIDTH'])

del cfg, cfg_fix

class AudioPlayer:
    def __init__(self):
        self.tk = Tk()
        self.t = Canvas(self.tk, background='black', width=WIN_WIDTH, height=WIN_HEIGHT)
        self.t.pack()

        self.startevent = Event()
        self.slowbar = None

        try: self.mask = Image.open("assets/mask.png")
        except FileNotFoundError: sys.exit()
        self.mask = self.mask.convert('L')
        
        self.tk.title('Audio Player')

        try: self.ico = ImageTk.PhotoImage(Image.open("assets/placeholder.png"))
        except FileNotFoundError: sys.exit()

        self.tk.wm_iconphoto(False, self.ico)

        self.load()
        self.audio()
        self.render()

        self.tk.geometry(f"{WIN_WIDTH}x{WIN_HEIGHT}")
        self.tk.resizable(0, 0)
        self.tk.deiconify()
        self.tk.mainloop()

    def load(self):
        if len(sys.argv) > 1:
            self.path = sys.argv[1]
        else:
            self.path = filedialog.askopenfilename(filetypes=[("MP3 files","*.mp3")])
            if self.path == '':
                sys.exit()

        self.tk.title(os.path.basename(self.path))
        
        self.a, self.data = ut.read_audio(self.path)
        icon = ut.get_icon(self.path)
        if icon is None: sys.exit()

        self.ico = ImageTk.PhotoImage(icon)
        self.tk.wm_iconphoto(False, self.ico)

        self.icon = ut.mask(self.mask, icon)

        self.wholeaudioamplitude = ut.data_to_xy(self.data, PLAYBAR_WIDTH, WIN_WIDTH/2 - PLAYBAR_WIDTH/2, 100, PLAYBAR_RES)
        
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
            self.tk.event_generate('<<Start>>')
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

        self.t.create_polygon(self.wholeaudioamplitude, fill=color)
        playbarpos = PLAYBAR_WIDTH/self.a.duration_seconds*(time()-self.audiostarttime)
        self.t.create_line(playbarpos, 0, playbarpos, 150, fill="black", width=PLAYBAR_LINE_WIDTH)

        self.t.after(max(round((1 / MAX_FPS - (time() - renderstarttime)) * 1000), 0), self.render)

if __name__ == "__main__":
    AudioPlayer()