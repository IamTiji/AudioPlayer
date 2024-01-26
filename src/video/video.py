import src.utils as ut
import configparser as cp
from moviepy.editor import *
from PIL import Image, ImageDraw
import numpy as np
import math

cfg = cp.ConfigParser()
cfg.read("config.ini")

def cfg_fix():
    if not cfg.has_section("VIDEO"):
        cfg.add_section('VIDEO')

    cfg.set('VIDEO', 'IMG_BASE_SIZE',      '150' )
    cfg.set('VIDEO', 'IMG_SIZE_DIVD',      '70'  )
    cfg.set('VIDEO', 'IMG_ROTATION',       '20'  )
    cfg.set('VIDEO', 'IMG_ROT_SP',         '2'   )
    cfg.set('VIDEO', 'MAX_FPS',            '60'  )
    cfg.set('VIDEO', 'SLOWBAR_SP',         '5'   )
    cfg.set('VIDEO', 'BAR_SPER',           '5'   )
    cfg.set('VIDEO', 'SLOWBAR_WIDTH'     , '4'   )
    cfg.set('VIDEO', 'VID_WIDTH'         , '1080')
    cfg.set('VIDEO', 'VID_HEIGHT'        , '1920')

    cfg.write(open("config.ini", "w"))
    
def cfg_load():
    global IMG_BASE_SIZE, IMG_SIZE_DIVD, IMG_ROTATION, IMG_ROT_SP, MAX_FPS, SLOWBAR_SP, BAR_SPER, SLOWBAR_WIDTH, VID_WIDTH, VID_HEIGHT
    
    IMG_BASE_SIZE =      int(cfg['VIDEO']['IMG_BASE_SIZE'     ])
    IMG_SIZE_DIVD =      int(cfg['VIDEO']['IMG_SIZE_DIVD'     ])
    IMG_ROTATION =       int(cfg['VIDEO']['IMG_ROTATION'      ])
    IMG_ROT_SP =         int(cfg['VIDEO']['IMG_ROT_SP'        ])
    MAX_FPS =            int(cfg['VIDEO']['MAX_FPS'           ])
    SLOWBAR_SP =         int(cfg['VIDEO']['SLOWBAR_SP'        ])
    BAR_SPER =           int(cfg['VIDEO']['BAR_SPER'          ])
    SLOWBAR_WIDTH =      int(cfg['VIDEO']['SLOWBAR_WIDTH'     ])
    VID_WIDTH =          int(cfg['VIDEO']['VID_WIDTH'         ])
    VID_HEIGHT =         int(cfg['VIDEO']['VID_HEIGHT'        ])

try:
    cfg_load()
except (ValueError, KeyError):
    cfg_fix()
    cfg_load()

del cfg, cfg_fix, cfg_load

vidsize = (1920, 1080)

class convert:
    def __init__(self, audio, linefill, barfill, backgroundimage, image, out):
        self.path = audio
        self.linefill = linefill
        self.barfill = barfill
        self.backgroundimage = Image.open(backgroundimage).resize(vidsize).convert('RGBA')
        self.image = Image.open(image).convert('RGBA')

        self.a, self.data = ut.read_audio(self.path)

        self.slowbar = None

        self.mask = Image.open("assets/mask.png").convert('L')
        self.image = ut.mask(self.mask, self.image)
        
        self.video = VideoClip(make_frame=self.getframe)
        self.video = self.video.set_duration(self.a.duration_seconds)
        self.video.write_videofile(out, fps=MAX_FPS, audio=self.path)
    
    def getframe(self, t):
        image = self.backgroundimage.copy()
        imagedraw = ImageDraw.ImageDraw(image)
        time = t

        bar = ut.fft(self.data, time)
        barthickness = VID_HEIGHT/bar.shape[0]

        if self.slowbar is None:
            self.slowbar = np.zeros(bar.shape)

        self.slowbar = ut.compute_slowbar(bar, self.slowbar, SLOWBAR_SP)

        for i in range(bar.shape[0]):
            imagedraw.rectangle((i*barthickness, VID_WIDTH, (i+1)*barthickness-BAR_SPER, VID_WIDTH-bar[i]), fill=self.barfill)
            imagedraw.line((i*barthickness, VID_WIDTH-self.slowbar[i], (i+1)*barthickness-BAR_SPER, VID_WIDTH-self.slowbar[i]), fill=self.linefill, width=SLOWBAR_WIDTH)

        ampilitude = ut.get_ampiltude(self.data, time, 50)
        ampilitude = round(IMG_BASE_SIZE*(ampilitude/IMG_SIZE_DIVD))

        image.alpha_composite(self.image
                              .resize((ampilitude, ampilitude))
                              .rotate(math.sin((time)*IMG_ROT_SP)*IMG_ROTATION, Image.BICUBIC), 
                              (math.floor(VID_HEIGHT/2-ampilitude/2), math.floor(VID_WIDTH/2-ampilitude/2)))
        
        return np.array(image.convert('RGB'))
    
        