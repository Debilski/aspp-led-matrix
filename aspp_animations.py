#!/usr/bin/env python

from pathlib import Path
import queue
import random
import time

import zmq
from PIL import Image

from rgbmatrix import graphics
from samplebase import SampleBase

animation_queue = queue.Queue(maxsize=10)

import numpy as np
import colorsys

IMAGES = {}

class Fire:
    def __init__(self):
        self.fire = np.zeros((18, 32), dtype=np.uint8)
        self.palette = np.zeros((256, 3), dtype=np.uint8)
        for idx, rgb in enumerate(self.palette):
            h = idx / 6. / 256. + 0.5
            s = 1
            l = min(1, idx / 2 / 256.)
            rgb = colorsys.hls_to_rgb(h, l, s)
            self.palette[idx] = (int(rgb[0] * 256), int(rgb[1] * 256), int(rgb[2] * 256))
        self.fire_ = np.empty_like(self.fire)
        self.anim = MixedAnimations('ghost.png', 'snow.png')

    def draw(self, canvas, tick):
        self.fire[16, :] = np.random.randint(0, 255, size=32)
        self.fire[17, :] = np.random.randint(0, 255, size=32)
        for idx in np.ndindex(*self.fire.shape):
            r, g, b = self.palette[self.fire[idx]]
            canvas.SetPixel(idx[1], 16 - idx[0], r, g, b)

        for idx in np.ndindex(*self.fire.shape):
            y, x = idx
            try:
                val = int((
                    int(self.fire[y + 2, x]) +
                    int(self.fire[y + 1, x + 1]) +
                    int(self.fire[y + 1, x - 1]) +
                    int(self.fire[y + 1, x])) / 4.7)
            except IndexError:
                val = 0
            self.fire_[idx] = val

        self.fire, self.fire_ = self.fire_, self.fire
        self.anim.draw(canvas, tick)
        time.sleep(0.1)
        return True

class Snow:
    def __init__(self):
        self.snow = np.zeros((17, 32), dtype=np.uint8)
        self.palette = np.zeros((256, 3), dtype=np.uint8)
        for idx, rgb in enumerate(self.palette):
            h = 1
            s = 0
            l = min(1, idx / 2 / 256.)
            rgb = colorsys.hls_to_rgb(h, l, s)
            self.palette[idx] = (int(rgb[0] * 256), int(rgb[1] * 256), int(rgb[2] * 256))
        self.snow_ = np.empty_like(self.snow)
        self.anim = MixedAnimations()

    def draw(self, canvas, tick):
        # Initialise new snow 
        self.snow[16, :] = 0
        num_snow = np.random.randint(0, 5)
        for _ in range(num_snow):
            snow_pos = np.random.randint(0, 32)
            self.snow[16, snow_pos] = np.random.randint(0, 255)

        for idx in np.ndindex(*self.snow.shape):
            r, g, b = self.palette[self.snow[idx]]
            canvas.SetPixel(idx[1], 15 - idx[0], r, g, b)


        # starting from the bottom, we move all snow flakes down one pixel
        # with a certain chance, the pixel may move to the left or the right
        # also, its palette colour may be changed slightly
        for row in range(self.snow.shape[0]):
            if row == 0:
#                self.snow_[row, :] = 0
                continue
            for col in range(self.snow.shape[1]):
                val = self.snow[row, col]
                if val != 0:
                    val += int(np.random.randn() * 20)
                    val = max(1, val)
                    val = min(255, val)
                # shift?
                dice = np.random.randint(0, 20)
                if dice == 0:
                    col = (col - 1) % 32
                if dice == 1:
                    col = (col + 1) % 32
                self.snow_[row - 1, col] = val
            self.snow_[idx] = val

        self.snow, self.snow_ = self.snow_, self.snow
        self.anim.draw(canvas, tick)
        time.sleep(0.2)
        return True



class Tick:
    def __init__(self):
        self.reset()

    def reset(self):
        self._t_start = time.time()

    def tick(self):
        return 1000 * (time.time() - self._t_start)

    def sleep_to_next_msec(self, msec):
        """ Sleep until the next modulo. """
        remainder = msec - (self.tick() % msec)
        time.sleep(remainder / 1000.)


class Animation:
    def __init__(self, *args, **kwargs):
        pass

    def step(self):
        """ Execute step and return True when the animation is finished. """
        return True

class RunText(Animation):
    def __init__(self, text, color, num_times, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text
        self.font = graphics.Font()
        self.font.LoadFont("clR6x12.bdf")
        self.textColor = graphics.Color(*color)
        self.pos = None
        self.num_times = num_times

    def draw(self, canvas, tick):
        if self.pos is None:
            self.pos = canvas.width
        l = graphics.DrawText(canvas, self.font, self.pos, 10, self.textColor, self.text)
        self.pos -= 1
        if (self.pos + l < 0):
            self.num_times -= 1
            if self.num_times == 0:
                return True
            self.pos = canvas.width


class FullFlicker(Animation):
    def draw(self, canvas, tick):
        if tick % 100 > 30:
            canvas.Fill(255, 255, 255)
        else:
            canvas.Clear()
        if tick > 1000:
            canvas.Clear()
        if tick > 1200:
            return True

# Will draw one step and exit
# Useful for default animation when nothing else should be running
class Pacman(Animation):
    def __init__(self):
        self.image = Image.open('7x7.png').convert('RGB')
        self.pos = None
        self.slowdown = 10

    def draw(self, canvas, tick):
        if self.pos is None:
            self.pos = canvas.width

        canvas.SetImage(self.image, -self.pos, 3)
        canvas.SetImage(self.image, -self.pos + 32, 3)
        if self.slowdown == 0:
            self.pos -= 1
            self.slowdown = 10
        self.slowdown -= 1
        if (self.pos <= 0):
            self.pos = canvas.width
        return True

def SetImageT(canvas, image, offset_x, offset_y):
    img_width, img_height = image.size
    pixels = image.load()
    for x in range(max(0, -offset_x), min(img_width, canvas.width - offset_x)):
        for y in range(max(0, -offset_y), min(img_height, canvas.height - offset_y)):
            (r, g, b, a) = pixels[x, y]
            if a:
                canvas.SetPixel(x + offset_x, y + offset_y, r, g, b)


class MixedAnimations(Animation):
    def __init__(self, *images):
        files = list(Path('imgs').glob('*.png'))
        file = random.choice(files)
        print("Playing", file)
        self.image = Image.open(file).convert('RGBA')
        self.image_next = None
        self.pos = None
        self.pos_next = None
        self.slowdown = 10
        self.idx = 0

    def draw(self, canvas, tick):
        if self.pos is None:
            self.pos = canvas.width

        if self.image is None:
            files = list(Path('imgs').glob('*.png'))
            file = random.choice(files)
            print("Playing", file)
            self.image = Image.open(file).convert('RGBA')

        h = (canvas.height - self.image.height) // 2

        SetImageT(canvas, self.image, self.pos, h)

        if self.slowdown == 0:
            self.pos -= 1
            self.slowdown = 5
        self.slowdown -= 1
        if self.pos < - self.image.width:
            self.pos = None
            self.image = None
        return True


class Countdown(Animation):
    def __init__(self, color, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.font = graphics.Font()
        self.font.LoadFont("../../../fonts/6x13.bdf")
        self.textColor = graphics.Color(*color)
        self.pos = 1

    def draw(self, canvas, tick):
        import datetime
        now = datetime.datetime.now()
        if now.hour != 16:
            return True
        seconds = 60 * now.minute + now.second
        remainder = 3600 - seconds
        mins = remainder // 60
        secs = remainder % 60
        text = f'{mins:02d}:{secs:02d}'
        l = graphics.DrawText(canvas, self.font, self.pos, 12, self.textColor, text)
        return True


orange = (255, 150, 0)
pink = (155, 0, 144)
yellow = (255, 255, 0)
blue = (0, 0, 255)
green = (0, 255, 0)

def parse_command(command):
    print(command)
    if command == '/flicker':
        return [FullFlicker()]
    if command == '/addimage':
        rep, image_id, path, *rest = command.split()
        if Path(path).exists():
            IMAGES[image_id] = path

    if command.startswith('/text '):
        return [RunText(command[5:], (200, 200, 0), 1)]
    if command.startswith('/alert '):
        return [RunText(command[6:], (200, 0, 0), 1)]
    if command.startswith('/rep '):
        rep, num, *rest = command.split()
        try:
            return [RunText(' '.join(rest), (250, 0, 250), int(num))]
        except:
            return [FullFlicker()]
    if 'to group0:' in command:
        return [
            FullFlicker(),
            RunText('group0', green, 1)
        ]
    if 'to group1:' in command:
        return [
            FullFlicker(),
            RunText('group1', blue, 1)
        ]
    if 'to group2:' in command:
        return [
            FullFlicker(),
            RunText('group2', orange, 1)
        ]
    if 'to group3:' in command:
        return [
            FullFlicker(),
            RunText('group3', yellow, 1)
        ]
    if 'to group4:' in command:
        return [
            FullFlicker(),
            RunText('group4', pink, 1)
        ]
    return []


class Animator(SampleBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser.add_argument("-t", "--text", help="The text to scroll on the RGB LED panel", default="Hello world!")
        self.parser.add_argument("--color", help="Comma separated RGB value", default="120,30,30")
        self.parser.add_argument("--socket", help="Socket")

    def run(self):
        self.ctx = zmq.Context()
        self.socket = self.ctx.socket(zmq.SUB)
        self.socket.connect(self.args.socket)
        self.socket.setsockopt(zmq.SUBSCRIBE, b'')
        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)

        offscreen_canvas = self.matrix.CreateFrameCanvas()

        tick = Tick()

        current_animation = None
        default_animation = Snow() # MixedAnimations('7x7.png', 'pumpkin.png', 'ghost.png')

        while True:
            socks = dict(self.poller.poll(5))
            if self.socket in socks and socks[self.socket] == zmq.POLLIN:
                my_text = self.socket.recv_json()
                parsed = parse_command(my_text)
                try:
                    if parsed is None:
                        parsed = []
                    for p in parsed:
                        print(p)
                        animation_queue.put(p)
                except queue.Full:
                    print("Full queue")

            if not current_animation:
                try:
                    current_animation = animation_queue.get(block=False, timeout=0)
                    tick.reset()
                except queue.Empty:
                    current_animation = default_animation
                    #current_animation = Countdown((200, 0, 0))
#               if my_text.startswith('/'):
#                   if my_text == '/stop':
#                       my_text = ''
#                   if my_text.startswith('/col'):
#                       col_regex = r'''/col\((\d+,\d+,\d+)\) (.*)'''
#                       import re
#                       res = re.search(col_regex, my_text)
#                       try:
#                           col = graphics.Color(*list(map(int, res.group(1).split(","))))
#                           my_text = res.group(2)
#                       except Exception as e:
#                           print(e)
#                           my_text = ''
#                           col = textColor
#               else:
#                   col = textColor
            if current_animation:
                offscreen_canvas.Clear()

                ret = current_animation.draw(offscreen_canvas, tick.tick())
                if ret:
                    current_animation = None
    #            len = graphics.DrawText(offscreen_canvas, font, pos, 9, col, my_text)
    #            pos -= 1
    #            if (pos + len < 0):
    #                pos = offscreen_canvas.width

            tick.sleep_to_next_msec(50)
            offscreen_canvas = self.matrix.SwapOnVSync(offscreen_canvas)


# Main function
if __name__ == "__main__":
    run_text = Animator()
    if (not run_text.process()):
        run_text.print_help()
