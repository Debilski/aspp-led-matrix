

from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image
import numpy as np
import zmq
import math

ADDRESS='tcp://[fe80::dea6:32ff:fe08:286%eth0]:12346'

ctx = zmq.Context()
sock = ctx.socket(zmq.PAIR)
sock.setsockopt(zmq.IPV6, True)
sock.bind(ADDRESS)

# configuration for the matrix
options = RGBMatrixOptions()
options.rows = 16
options.chain_length = 1
options.parallel = 1
options.hardware_mapping = 'regular' 
options.gpio_slowdown = 3

matrix = RGBMatrix(options = options)

pixels = [None] * 32
i = 0

def low_pass_filter(l, tau, dt):
    P = np.exp(-dt/tau)
    l_filtered = [l[0]]
    for i in range(1, len(l)):
        l_filtered.append(P * l_filtered[i - 1] + (1. - P) * l[i])
    return l_filtered


freq = np.fft.fftfreq(32)

def lp(pixels):
    return np.fft.ifft(np.fft.fft(pixels) / (1 + 12 * 1j * freq))

while True:
    byte = sock.recv()
    if pixels[i] is not None:
        pixels[i] = None
    try:
        val = int(math.atan(( int(byte) - 128 ) / 3.0) / math.pi * 2 * 8) + 8
    except Exception as e:
        continue
    pixels[i] = val
    i += 1
    i = i % 32

    if i == 0:
        # rescale and show
        max_val = max(p for p in pixels if p is not None)
        matrix.Clear()
#        pixels =  low_pass_filter(pixels, 4, 1)
        pixels = lp(pixels)
        for p in range(32):
#            pixels[p] = pixels[p] / max_val * 8
            matrix.SetPixel(p, pixels[p], 220, 0, 0)

#hile True:
#   byte = sock.recv()
#   if pixels[i] is not None:
#       matrix.SetPixel(i, pixels[i], 0, 0, 0)
#       pixels[i] = None
#   try:
#       val = int(byte) / 16
#   except:
#       continue
#   pixels[i] = val
#   matrix.SetPixel(i, val, 220, 0, 0)
#   i += 1
#   i = i % 32

