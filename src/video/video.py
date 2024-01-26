import src.utils as ut
import configparser as cp
from moviepy.editor import *
from PIL import Image, ImageDraw
import numpy as np
import math

cfg = cp.ConfigParser()
cfg.read("config.ini")

def cfg_fix():
    cfg.add_section('VIDEO')

    cfg.set('VIDEO', 'IMG_BASE_SIZE',      '150')
    cfg.set('VIDEO', 'IMG_SIZE_DIVD',      '70' )
    cfg.set('VIDEO', 'IMG_ROTATION',       '20' )
    cfg.set('VIDEO', 'IMG_ROT_SP',         '2'  )
    cfg.set('VIDEO', 'MAX_FPS',            '30' )
    cfg.set('VIDEO', 'SLOWBAR_SP',         '5'  )
    cfg.set('VIDEO', 'BAR_SPER',           '5'  )
    cfg.set('VIDEO', 'SLOWBAR_WIDTH'     , '4'  )

    cfg.write(open("config.ini", "w"))
    
def cfg_load():
    global IMG_BASE_SIZE, IMG_SIZE_DIVD, IMG_ROTATION, IMG_ROT_SP, MAX_FPS, SLOWBAR_SP, BAR_SPER, SLOWBAR_WIDTH
    
    IMG_BASE_SIZE =      int(cfg['VIDEO']['IMG_BASE_SIZE'     ])
    IMG_SIZE_DIVD =      int(cfg['VIDEO']['IMG_SIZE_DIVD'     ])
    IMG_ROTATION =       int(cfg['VIDEO']['IMG_ROTATION'      ])
    IMG_ROT_SP =         int(cfg['VIDEO']['IMG_ROT_SP'        ])
    MAX_FPS =            int(cfg['VIDEO']['MAX_FPS'           ])
    SLOWBAR_SP =         int(cfg['VIDEO']['SLOWBAR_SP'        ])
    BAR_SPER =           int(cfg['VIDEO']['BAR_SPER'          ])
    SLOWBAR_WIDTH =      int(cfg['VIDEO']['SLOWBAR_WIDTH'     ])

try:
    cfg_load()
except (ValueError, KeyError):
    cfg_fix()
    cfg_load()

del cfg, cfg_fix, cfg_load

vidsize = (1920, 1080)

class convert:
    def __init__(self, audio, baroutline, barfill, backgroundimage, image):
        self.path = audio
        self.baroutline = baroutline
        self.barfill = barfill
        self.backgroundimage = Image.open(backgroundimage).resize(vidsize)
        self.image = Image.open(image).convert('RGBA')

        self.a, self.data = ut.read_audio(self.path)

        self.slowbar = None

        self.mask = Image.open("assets/mask.png").convert('L')
        self.image = ut.mask(self.mask, self.image)
        
        self.video = VideoClip(make_frame=self.getframe)
        self.video = self.video.set_duration(self.a.duration_seconds)
        self.video.write_videofile("output.mp4", fps=MAX_FPS, audio=self.path)
    
    def getframe(self, t):
        image = self.backgroundimage.copy()
        imagedraw = ImageDraw.ImageDraw(image)
        time = t

        bar = ut.fft(self.data, time)
        barthickness = vidsize[0]/bar.shape[0]

        if self.slowbar is None:
            self.slowbar = np.zeros(bar.shape)

        self.slowbar = ut.compute_slowbar(bar, self.slowbar, SLOWBAR_SP)

        for i in range(bar.shape[0]):
            imagedraw.rectangle((i*barthickness, vidsize[0], (i+1)*barthickness-BAR_SPER, vidsize[0]-bar[i]), fill=self.barfill, outline=self.baroutline)
            imagedraw.line((i*barthickness, vidsize[0]-self.slowbar[i], (i+1)*barthickness-BAR_SPER, vidsize[0]-self.slowbar[i]), fill=self.baroutline, width=SLOWBAR_WIDTH)

        ampilitude = ut.get_ampiltude(self.data, time, 50)

        image.paste(self.image
                              .resize((round(IMG_BASE_SIZE*(ampilitude/IMG_SIZE_DIVD)), round(IMG_BASE_SIZE*(ampilitude/IMG_SIZE_DIVD))))
                              .rotate(math.sin((time)*IMG_ROT_SP)*IMG_ROTATION, Image.BICUBIC), (math.floor(vidsize[0]/2), math.floor(vidsize[1]/2)))
        
        return np.array(image)
    
        