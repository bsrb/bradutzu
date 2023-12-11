import time

def startup(pixels):
    def pushpx(i):
        pixels.fill((0, 0, 0))
        for j in range(i):
            pixels[j] = (0, 255, 0)
        pixels.show()
        time.sleep(0.002)

    for i in range(pixels.n):
        pushpx(i)
    for i in range(pixels.n, 0, -1):
        pushpx(i)
    pixels.fill((0, 0, 0))
    pixels.show()

def shutdown(pixels):
    def pushpx(i):
        pixels.fill((0, 0, 0))
        for j in range(i):
            pixels[j] = (255, 0, 0)
        pixels.show()
        time.sleep(0.002)

    for i in range(pixels.n):
        pushpx(i)
    for i in range(pixels.n, 0, -1):
        pushpx(i)
    pixels.fill((0, 0, 0))
    pixels.show()

def test_start(pixels):
    for i in range(pixels.n):
        pixels.fill((0, 0, 0))
        pixels[i] = (0, 255, 0)
        pixels.show()
        time.sleep(0.002)
    pixels.fill((0, 0, 0))
    pixels.show()

def test_stop(pixels):
    for i in reversed(range(pixels.n)):
        pixels.fill((0, 0, 0))
        pixels[i] = (255, 0, 0)
        pixels.show()
        time.sleep(0.002)
    pixels.fill((0, 0, 0))
    pixels.show()
