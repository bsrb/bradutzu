import time

def wheel(pos):
    if pos < 0 or pos > 255:
        r = g = b = 0
    elif pos < 85:
        r = int(pos * 3)
        g = int(255 - pos * 3)
        b = 0
    elif pos < 170:
        pos -= 85
        r = int(255 - pos * 3)
        g = 0
        b = int(pos * 3)
    else:
        pos -= 170
        r = 0
        g = int(pos * 3)
        b = int(255 - pos * 3)
    return (r, g, b)

def rainbow_cycle(pixels):
    for j in range(255):
        for i in range(pixels.n):
            pixel_index = (i * 256 // pixels.n) + j
            pixels[i] = wheel(pixel_index & 255)
        pixels.show()
        time.sleep(0.05)

def animation(pixels):
    rainbow_cycle(pixels)