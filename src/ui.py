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
MAX_FPS =       30    #Maximum FPS
COLOR_SPETM_SP =2     #Color saturation speed
PLAYBAR_RES =   500   #Playbar resolution

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

        try: self.mask = Image.open("assets/mask.png")
        except FileNotFoundError: self.mask = Image.open("../assets/mask.png")
        self.mask = self.mask.convert('L')

        self.load()
        self.start()

        self.tk.geometry(f"{WIN_WIDTH}x{WIN_HEIGHT}")
        self.tk.resizable(0, 0)
        self.tk.event_generate('<<Start>>')
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

    def start(self):
        audioThread = Thread(target=self.play_audio)
        renderThread = Thread(target=self.render)

        self.audiostarttime = time()
        self.audioT = self.tk.bind('<<Start>>', lambda e:self.startevent.set())

        audioThread.start()
        renderThread.start()

    def play_audio(self):
        self.startevent.wait()

        playback._play_with_pyaudio(self.a)
    
    def render(self):
        self.startevent.wait()
        
        renderstarttime = time()

        self.t.delete("all")

        bar = ut.fft(self.data, time()-self.audiostarttime)
        barthickness = WIN_WIDTH/bar.shape[0]

        if self.slowbar is None:
            self.slowbar = np.zeros(bar.shape)

        self.slowbar = ut.compute_slowbar(bar, self.slowbar)

        for i in range(bar.shape[0]):
            self.t.create_rectangle(i*barthickness, WIN_HEIGHT, (i+1)*barthickness, WIN_HEIGHT-bar[i],
                                     fill="black", outline=ut.rgb_values_to_hex(cs.hsv_to_rgb(((time()-self.audiostarttime)/COLOR_SPETM_SP)%1, 1, 1)))
            self.t.create_line(i*barthickness, WIN_HEIGHT-self.slowbar[i], (i+1)*barthickness, WIN_HEIGHT-self.slowbar[i], 
                               fill=ut.rgb_values_to_hex(cs.hsv_to_rgb(((time()-self.audiostarttime)/COLOR_SPETM_SP)%1, 1, 1)))

        ampilitude = ut.get_ampiltude(self.data, time()-self.audiostarttime, 50)

        self.tkimage = ImageTk.PhotoImage(image=self.icon
                                          .resize((round(IMG_BASE_SIZE*(ampilitude/IMG_SIZE_DIVD)), round(IMG_BASE_SIZE*(ampilitude/IMG_SIZE_DIVD))))
                                          .rotate(math.sin(time()-self.audiostarttime)*IMG_ROTATION, Image.BICUBIC))
        self.t.create_image(WIN_WIDTH / 2, WIN_HEIGHT / 2, image=self.tkimage)

        self.t.after(max(round((1 / MAX_FPS - (time() - renderstarttime)) * 1000), 0), self.render)

if __name__ == "__main__":
    AudioPlayer()