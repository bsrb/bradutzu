# At a minimum your file must contain this function
# You will receive a NeoPixel object through the pixels argument
# You can only import math, time, or random
import time

def animation(pixels):
    while True:
        for i in range(pixels.n):
            pixels.fill((0, 0, 0))
            pixels[i] = (255, 0, 0)
            pixels.show()
            time.sleep(0.002)

        pixels.fill((255, 0, 0))
        pixels.show()
        time.sleep(1)

        for i in reversed(range(pixels.n)):
            pixels.fill((0, 0, 0))
            pixels[i] = (0, 0, 255)
            pixels.show()
            time.sleep(0.002)

        pixels.fill((0, 0, 255))
        pixels.show()
        time.sleep(1)