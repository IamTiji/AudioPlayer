import numpy as np
import scipy as sp
import pydub as pb
from PIL import Image, ImageOps
from mutagen import mp3
import io
import math
import configparser as cp

SAMPLERATE:int

cfg = cp.ConfigParser()
cfg.read("config.ini")

def cfg_fix():
    if not cfg.has_section("EXTRAS"):
        cfg.add_section('EXTRAS')

    cfg.set('EXTRAS','BARDIV'            , '80'  )
    cfg.set('EXTRAS','BL',                 '1024')
    cfg.set('EXTRAS','PLAYBAR_HEIGHT_DIV', '300' )
    cfg.set('EXTRAS','MAXBARHEIGHT',       '400' )

    cfg.write(open("config.ini", "w"))
    
def cfg_load():
    global BARDIV, BL, PLAYBAR_HEIGHT_DIV, MAXBARHEIGHT
    
    BARDIV =                   int(cfg['EXTRAS']['BARDIV'            ])
    BL =                       int(cfg['EXTRAS']['BL'                ])
    PLAYBAR_HEIGHT_DIV =       int(cfg['EXTRAS']['PLAYBAR_HEIGHT_DIV'])
    MAXBARHEIGHT =             int(cfg['EXTRAS']['MAXBARHEIGHT'      ])

try:
    cfg_load()
except (ValueError, KeyError):
    cfg_fix()
    cfg_load()

def read_audio(path) -> tuple[pb.AudioSegment, np.ndarray]:
    """
    Read audio file and return numpy array with sound object
    """

    global SAMPLERATE

    a = pb.AudioSegment.from_mp3(path)
    SAMPLERATE = a.frame_rate
    outarray = np.array(a.get_array_of_samples(), np.int16)
    outarray = outarray[math.floor(len(outarray)/a.channels):]

    if len(outarray) == 0:
        raise ValueError("Audio file is empty")
    
    return a, outarray

def fft(data: np.ndarray, time: float) -> np.ndarray:
    """
    Compute FFT
    """

    tmp = (SAMPLERATE / BL)
    
    h = (sp.fft.rfft(data[math.floor(time*SAMPLERATE):(math.floor(time*SAMPLERATE)+math.floor(tmp))])/BARDIV)

    hanning = np.hanning(len(h)+2)

    return np.minimum(np.abs(h)*hanning[1:len(h)+1], np.full(h.shape, MAXBARHEIGHT))

def compute_slowbar(data: np.ndarray, slowbar: np.ndarray, speed: int) -> np.ndarray:
    """
    Compute slow bar
    """

    slowbar = slowbar - speed
    return np.maximum(data, slowbar)

def get_ampiltude(data: np.ndarray, time: float, min_value: float) -> int:
    """
    Get amplitude
    """

    tmp = (SAMPLERATE / BL)
    
    return max(math.sqrt(
        np.mean(
            np.abs(
                data[math.floor(time*SAMPLERATE):(math.floor(time*SAMPLERATE)+math.floor(tmp))]**2))), min_value)

def mask(mask: Image.Image, image: Image.Image) -> Image.Image:
    """
    Apply mask to image
    """

    out = ImageOps.fit(image, mask.size)
    out.putalpha(mask)
    
    return out

def get_icon(path: str) -> Image.Image:
    """
    Get icon from image
    """

    audio = mp3.MP3(path)
    try:
        image = audio.tags['APIC:']
        return Image.open(io.BytesIO(image.data))
    except (KeyError, TypeError):
        try: return Image.open("assets/placeholder.png")
        except FileNotFoundError: return

def rgb_values_to_hex(rgb: tuple[int, int, int]) -> str:
    """
    Convert RGB values to hex
    """
    
    return f"#{math.floor(rgb[0]*255):02x}{math.floor(rgb[1]*255):02x}{math.floor(rgb[2]*255):02x}"

def data_to_xy(data: np.ndarray, w:int, x:int, y:int, res:int) -> list:
    index = np.arange(x, w+x, w//res, dtype=np.int16)
    out1 = np.zeros((2, res), dtype=np.int16)
    out2 = np.zeros((2, res), dtype=np.int16)

    data = np.abs(data)
    modified_data = np.zeros(res, dtype=np.int16)

    for i in range(res):
        modified_data[i] = np.mean(data[(len(data)//res)*i:(len(data)//res)*(i+1)])

    modified_data = modified_data//PLAYBAR_HEIGHT_DIV
    
    out1[1] = y/2+modified_data
    out1[0] = index
    out2[1] = y/2-modified_data[::-1]
    out2[0] = index[::-1]
    
    out1 = np.rot90(out1, 1)
    out1 = np.reshape(out1, (res*2))
    out2 = np.rot90(out2, 1)
    out2 = np.reshape(out2, (res*2))
    
    return list(np.concatenate((out1, out2)))
