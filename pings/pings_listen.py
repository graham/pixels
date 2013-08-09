import redis
import time
import cPickle

from pixelfont import PixelFont
from service import Service, Ping
from util import redis_conn

PING_KEY = 'ping'
FRAME_KEY = 'frame'

FRAME_TIME = 0.02

def main():
    client = redis.Redis()
    s = Service(width=Service.DEFAULT_WIDTH, height=Service.DEFAULT_HEIGHT)

    def update(delta_time=0):
        while client.llen(FRAME_KEY) > 50:
            time.sleep(0.05)

        new_frame = s.step(delta_time)
        client.rpush(FRAME_KEY, cPickle.dumps(new_frame))

    while True:
        ping = client.lpop(PING_KEY)
        if ping:
            s.add(Ping)
        update()
        time.sleep(FRAME_TIME)

if __name__ == "__main__":
    main()
