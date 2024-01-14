import typing
import numpy as np
import scipy as sp
import pydub as pb
from PIL import Image, ImageOps
from mutagen import mp3
import io
import math

global SAMPLERATE

BARDIV =       80
SLOWBARSPEED = 8
BL =           1024
SAMPLERATE =   44100

def read_audio(path) -> typing.Any:
    """
    Read audio file and return numpy array with sound object
    """

    a = pb.AudioSegment.from_mp3(path)
    SAMPLERATE = a.frame_rate
    outarray = np.array(a.get_array_of_samples(), np.int16)
    outarray = outarray[math.floor(len(outarray)/a.channels):]
    return a, outarray

def fft(data: np.ndarray, time: float) -> np.ndarray:
    """
    Compute FFT
    """

    tmp = (SAMPLERATE / BL)

    h = (sp.fft.rfft(data[math.floor(time*SAMPLERATE):(math.floor(time*SAMPLERATE)+math.floor(tmp))])/BARDIV)

    w = np.hanning(len(h)+2)

    return np.abs(h)*w[1:len(h)+1]

def compute_slowbar(data: np.ndarray, slowbar: np.ndarray) -> np.ndarray:
    """
    Compute slow bar
    """

    slowbar = slowbar - SLOWBARSPEED
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
        return Image.new("RGBA", (1000, 1000), (255, 255, 255, 255))

def rgb_values_to_hex(rgb: typing.Tuple[int, int, int]) -> str:
    """
    Convert RGB values to hex
    """
    
    return f"#{math.floor(rgb[0]*255):02x}{math.floor(rgb[1]*255):02x}{math.floor(rgb[2]*255):02x}"