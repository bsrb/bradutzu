from datetime import datetime
import os
import multiprocessing
import pytz
import random
import timeout_decorator
import threading

import brad.controller.animations as animations
import brad.controller.safe_run as safe_run

class DummyNeoPixel(object):
    _guarded_writes = True
    def __init__(self, n, debug):
        self.n = n
        self.debug = debug
    def show(self):
        if self.debug: print('pixels.show()')
    def fill(self, color):
        if self.debug: print(f'pixels.fill({color})')
    def __setitem__(self, key, value):
        if self.debug: print(f'pixels[{key}] = {value}')

class Controller(threading.Thread):
    def __init__(self, config):
        self.config = config
        self.number_of_pixels = config.NUMBER_OF_PIXELS

        self.ANIMATION_FILENAME = 'default'
        self.ANIMATION_TEST_BYTECODE = None
        self.ANIMATION_TEST_USER = None
        self.CTRL_IS_TESTING = False
        self.LOG = []

        if config.DEBUG:
            self.pixels = DummyNeoPixel(self.number_of_pixels, False)
        else:
            import board
            import neopixel
            self.pixels = neopixel.NeoPixel(board.D18, self.number_of_pixels, brightness=1.0, auto_write=False, pixel_order=neopixel.RGB)
            # Make it writable by restricted code
            self.pixels._guarded_writes = True
            # Clear the deinit() function so that client code cannot cause DoS by calling it
            self.pixels.deinit = None

        animations.startup(self.pixels)

        self.log_write(f'Initialized Controller with {self.number_of_pixels} pixels.')
        threading.Thread.__init__(self)

    def run(self):
        animation_mprocess, animation_result = self.run_animation(self.pixels)

        while True:
            if self.ANIMATION_TEST_BYTECODE is not None:
                self.log_write(f'Running test animation for {self.ANIMATION_TEST_USER}')

                # Signal animation mprocess to terminate
                animation_mprocess.terminate()
                animation_mprocess.join()

                self.CTRL_IS_TESTING = True

                animations.test_start(self.pixels)
                try:
                    safe_run.execute_test_bytecode(self.ANIMATION_TEST_BYTECODE, self.pixels)
                except timeout_decorator.timeout_decorator.TimeoutError:
                    pass
                except Exception as e:
                    self.LOG.append(f'{self.ANIMATION_TEST_USER} test error: {str(e)}')
                animations.test_stop(self.pixels)

                self.ANIMATION_TEST_BYTECODE = None
                self.CTRL_IS_TESTING = False
                self.log_write(f'Test animation for {self.ANIMATION_TEST_USER} finished running.')

            if not animation_mprocess.is_alive():
                result = animation_result.get()
                if result == 'KeyboardInterrupt':
                    # If mprocess died by KeyboardInterrupt then we must also exit
                    break
                if result != 'Success' and result != 'TimeoutError':
                    self.log_write(f'[AnimationProcess] {result}')
                animation_mprocess, animation_result = self.run_animation(self.pixels)

            animation_mprocess.join(timeout=0.5)

        self.log_write(f'Received KeyboardInterrupt, running exit animation and closing...')
        animations.shutdown(self.pixels)

    def run_animation(self, pixels):
        filename, filepath = self.random_animation()
        self.ANIMATION_FILENAME = filename
        self.log_write(f'Now playing {self.ANIMATION_FILENAME}')
        # Start new animation
        result_queue = multiprocessing.Queue()
        animation_mprocess = safe_run.AnimationProcess(pixels, filepath, result_queue)
        animation_mprocess.start()
        return animation_mprocess, result_queue

    def random_animation(self):
        animations_dir = os.path.join(os.getcwd(), self.config.FLASK_APP, 'animations')
        rand_file = random.choice(os.listdir(animations_dir))
        return rand_file, os.path.join(animations_dir, rand_file)

    def log_write(self, message):
        timezone = pytz.timezone('Europe/Bucharest')
        formatted_date = datetime.now(timezone).strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f'[{formatted_date}] {message}'
        self.LOG.append(formatted_message)
        print(formatted_message)
        self.LOG = self.LOG[-100:]
