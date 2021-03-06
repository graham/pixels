import redis
import random
import time
import cPickle
from postprocess import BlurLeft, BlurRight

from pixelpusher import pixel, build_strip, send_strip, bound
from service import Service
from util import redis_conn

MAX = 128
MID = 128
OFF = 0

FRAME_KEY = 'frame'

def main():
    client = redis_conn()
    s = Service(width=Service.DEFAULT_WIDTH, height=Service.DEFAULT_HEIGHT)
    s.add_post_process(BlurRight)

    def safe_check():
        while client.llen(FRAME_KEY) > 50:
            time.sleep(0.05)

    def update():
        new_frame = s.step(.01)
        client.rpush(FRAME_KEY, cPickle.dumps(new_frame))

    level = 0
    red, green, blue = 32,32,32

    while True:
        time.sleep(0.01)
        safe_check()

        level += random.randint(-1, 1)
        level = bound(level, 0, 8)
        s.shift_left()

        for i in range(7, -1, -1):
            if s.height - i == level:
                red = bound(red + random.randint(-8, 8), 0, 255)
                blue = bound(blue + random.randint(-8, 8), 0, 255)
                green = bound(green + random.randint(-8, 8), 0, 255)
                s.set_pixel(s.width-1, i, red, blue, green)
            elif s.height - i < level:
                s.set_pixel(s.width-1, i, red*0.3, blue*0.3, green*0.3)
            else:
                s.set_pixel(s.width-1, i, OFF, OFF, OFF)
        update()

if __name__ == "__main__":
    main()
