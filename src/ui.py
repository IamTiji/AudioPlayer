from tkinter import *
from tkinter import filedialog
from PIL import Image, ImageTk

from threading import Thread, Event
from time import time
from pydub import playback
import math
import numpy as np
import colorsys as cs
import sys
import os

try: import src.utils as ut
except ModuleNotFoundError: import utils as ut

WIN_WIDTH =     800   #Window width
WIN_HEIGHT =    600   #Window height
IMG_BASE_SIZE = 150   #Base image size
IMG_SIZE_DIVD = 70    #Amplitude divider
IMG_ROTATION =  20    #Image rotation speed
IMG_ROT_SP =    2     #Image rotation speed
MAX_FPS =       30    #Maximum FPS
COLOR_SPETM_DV =4     #Color saturation speed divider
SLOWBAR_SP =    5     #Slowbar speed
BAR_SPER =      5     #Bar seperator
PLAYBAR_RES =   50    #Playbar resolution
PLAYBAR_WIDTH = 600   #Playbar width
DEBUGMODE =     True  #Debug on rendering

class AudioPlayer:
    def __init__(self):
        self.tk = Tk()
        self.t = Canvas(self.tk,background='black')
        self.t.pack(fill=BOTH, expand=YES)
        
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

        self.load()
        self.start()

        self.tk.geometry(f"{WIN_WIDTH}x{WIN_HEIGHT}")
        self.tk.resizable(0, 0)
        self.tk.after(1000, self.tk.event_generate('<<Start>>'))
        self.tk.deiconify()
        self.tk.mainloop()

        if DEBUGMODE:
            print(f"{self.framedrop} frame dropped out of {round((time()-self.audiostarttime)*MAX_FPS)}")
            print(f"Average FPS: {(MAX_FPS*(time()-self.audiostarttime)-self.framedrop)/(time()-self.audiostarttime):.2f}")

    def load(self):
        if len(sys.argv) > 1:
            self.path = sys.argv[1]
        else:
            self.path = filedialog.askopenfilename(filetypes=[("MP3 files","*.mp3")])

        self.tk.title(os.path.basename(self.path))
        
        self.a, self.data = ut.read_audio(self.path)
        icon = ut.get_icon(self.path)
        self.icon = ut.mask(self.mask, icon)

        self.audiovitwhole = ut.data_to_xy(self.data, PLAYBAR_WIDTH, WIN_WIDTH/2 - PLAYBAR_WIDTH/2, 50, PLAYBAR_RES)

    def start(self):
        audioThread = Thread(daemon=True, target=self.play_audio)
        renderThread = Thread(target=self.render)

        self.audiostarttime = time()
        self.audioT = self.tk.bind('<<Start>>', lambda e:self.startevent.set())

        #audioThread.start()
        renderThread.start()

    def play_audio(self):
        self.startevent.wait()

        playback._play_with_pyaudio(self.a)
    
    def render(self):
        self.startevent.wait()
        
        if self.a.duration_seconds < time()-self.audiostarttime:
            #self.tk.destroy()
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

        if (1 / MAX_FPS - (time() - renderstarttime)) < 0 and DEBUGMODE:
            self.framedrop += 1

        self.t.after(max(round((1 / MAX_FPS - (time() - renderstarttime)) * 1000), 0), self.render)

if __name__ == "__main__":
    AudioPlayer()