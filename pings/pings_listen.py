import redis
import time
import cPickle
import json
import os

from pixelfont import PixelFont
from service import Service, Ping
from util import redis_conn

PING_KEY = 'ping'
FRAME_KEY = 'frame'

FRAME_TIME = 0.02
NUM_PINGS = 10

def main():
    host = os.environ.get('REDISHOST', 'datalamb.com')
    ping_client = redis.Redis(host)
    client = redis.Redis()

    s = Service(width=Service.DEFAULT_WIDTH, height=Service.DEFAULT_HEIGHT)

    def update(delta_time=0):
        while client.llen(FRAME_KEY) > 50:
            time.sleep(0.05)

        new_frame = s.step(delta_time)
        client.rpush(FRAME_KEY, cPickle.dumps(new_frame))

    while True:
        ping = ping_client.lpop(PING_KEY)
        if ping:
            ping = json.loads(ping)

            for i in range(NUM_PINGS):
                ping_animation = Ping(s)
                ping_animation.init(s, ping['r'], ping['g'], ping['b'])
                s.add_instance(ping_animation)

        update()
        time.sleep(FRAME_TIME)

if __name__ == "__main__":
    main()
