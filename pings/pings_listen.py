import redis
import time
import cPickle
import json

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
            ping = json.loads(ping)

            ping_animation = Ping(s)
            ping_animation.init(s, ping['r'], ping['g'], ping['b'])
            s.add_instance(ping_animation)

        update()
        time.sleep(FRAME_TIME)

if __name__ == "__main__":
    main()
