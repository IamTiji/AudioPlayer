import numpy as np
import scipy as sp
import pydub as pb
from PIL import Image, ImageOps, ImageDraw
from mutagen import mp3
import io
import math

global SAMPLERATE

BARDIV =       80
BL =           1024
SAMPLERATE =   44100

def read_audio(path) -> tuple[pb.AudioSegment, np.ndarray]:
    """
    Read audio file and return numpy array with sound object
    """

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

    w = np.hanning(len(h)+2)

    return np.abs(h)*w[1:len(h)+1]

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
        except FileNotFoundError: return Image.open("../assets/placeholder.png")

def rgb_values_to_hex(rgb: tuple[int, int, int]) -> str:
    """
    Convert RGB values to hex
    """
    
    return f"#{math.floor(rgb[0]*255):02x}{math.floor(rgb[1]*255):02x}{math.floor(rgb[2]*255):02x}"

def data_to_img(data: np.ndarray, color: tuple[int,int,int] | str, w:int, h:int, linei:int) -> Image.Image:
    out = Image.new('RGBA', (w,h), (0,0,0,255))
    data = np.abs(data)
    modified_data = np.zeros((w), dtype=np.int16)

    for x in range(w):
        modified_data[x] = np.mean(data[w*x:w*(x+1)])
    modified_data = modified_data/300

    draw=ImageDraw.Draw(out)
    for x in range(w):
        draw.rectangle((x,modified_data[x]*-1+w/2,x+1,modified_data[x]+w/2), fill="white")
        
    out.show()
    return out

if __name__ == "__main__":
    data_to_img(read_audio(r"C:\Users\junes_18xqzji\Music\song\Disfigure - Blank [NCS Release].mp3")[1], (255, 255, 255, 255), 600, 100, 20)