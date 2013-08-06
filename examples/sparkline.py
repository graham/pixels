import redis
import random
import time
import cPickle

from pixelpusher import pixel, build_strip, send_strip, bound
from service import Service

MAX = 128
MID = 128
OFF = 0

FRAME_KEY = 'frame'

def main():
    client = redis.Redis()
    s = Service(width=120, height=8)

    def update():
        new_frame = s.step()
        client.rpush(FRAME_KEY, cPickle.dumps(new_frame))        

    level = 0
    while True:
        time.sleep(0.01)

        level += random.randint(-1, 1)
        level = bound(level, 0, 8)
        s.shift_left()
        
        for i in range(7, -1, -1):
            if s.height - i == level:
                s.set_pixel(s.width-1, i, MAX, MAX, MAX)
            elif s.height - i < level:
                s.set_pixel(s.width-1, i, 2*level, 2*level, 2*level)
            else:
                s.set_pixel(s.width-1, i, OFF, OFF, OFF)
        update()

if __name__ == "__main__":
    main()
