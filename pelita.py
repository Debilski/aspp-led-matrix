#!/usr/bin/env python
from samplebase import SampleBase
import time


import json
import zmq



class GrayscaleBlock(SampleBase):
    def __init__(self, *args, **kwargs):
        super(GrayscaleBlock, self).__init__(*args, **kwargs)
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect('tcp://127.0.0.1:13579')
        self.socket.setsockopt(zmq.SUBSCRIBE, b"")

    def run(self):
        sub_blocks = 16
        width = self.matrix.width
        height = self.matrix.height
        x_step = max(1, width / sub_blocks)
        y_step = max(1, height / sub_blocks)
        count = 0

        while True:
            data = self.socket.recv_json()['__data__']
            for y in range(0, height):
                for x in range(0, width):
                    #reset all
                    self.matrix.SetPixel(x, y, 0, 0, 0)

            for x, y in data['walls']:
                self.matrix.SetPixel(x, y, 100, 1, 100)
            for x, y in data['food']:
                self.matrix.SetPixel(x, y, 150, 150, 150)
            for idx, (x, y) in enumerate(data['bots']):
                if idx % 2 == 0:
                    self.matrix.SetPixel(x, y, 0, 0, 200)
                else:
                    self.matrix.SetPixel(x, y, 200, 0, 0)
#                   if count % 4 == 0:
#                       self.matrix.SetPixel(x, y, c, c, c)
#                   elif count % 4 == 1:
#                       self.matrix.SetPixel(x, y, c, 0, 0)
#                   elif count % 4 == 2:
#                       self.matrix.SetPixel(x, y, 0, c, 0)
#                   elif count % 4 == 3:
#                       self.matrix.SetPixel(x, y, 0, 0, c)

            count += 1
            time.sleep(0.03)


# Main function
if __name__ == "__main__":
    grayscale_block = GrayscaleBlock()
    if (not grayscale_block.process()):
        grayscale_block.print_help()
