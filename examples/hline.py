import redis
import random
import time
import cPickle

from pixelpusher import pixel, build_strip, send_strip, bound
from service import Service
import util

MAX = 128
MID = 128
OFF = 0

FRAME_KEY = 'frame'

def main():
    client = util.redis_conn()
    s = Service(width=120, height=8)

    def safe_check():
        while client.llen(FRAME_KEY) > 50:
            time.sleep(0.05)

    def update():
        new_frame = s.step()
        client.rpush(FRAME_KEY, cPickle.dumps(s.get_pixel_map()))

    level = 0
    red, green, blue = 32,32,32
    index = 0

    while True:
        index += 1
        time.sleep(0.01)
        safe_check()

        if index % 20 == 0:
            i = random.randint(0, 7)
            s.set_pixel(s.width-1, i, 255, 255, 255)

        s.shift_left()
        update()

if __name__ == "__main__":
    main()
