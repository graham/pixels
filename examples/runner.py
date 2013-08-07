import sys
import select
import tty
import termios
import redis
import random
import time
import cPickle

from pixelpusher import pixel, build_strip, send_strip, bound
from service import Service
from util import redis_conn

BUTTON_END = '\x1b'
FRAME_TIME = 0.05
FRAME_KEY = 'frame'

def setup():
    old_settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())
    return old_settings

def teardown(old_settings):
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

def get_input():
    if is_data():
        c = sys.stdin.read(1)
        return c

def handle_input():
    c = get_input()
    if c == BUTTON_END:
        return True

    if c == ' ':
        jump()

    return False

def is_data():
    return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

def jump():
    print "Jump"

def step_world(delta_time):
    pass

def update_buffer(service, client):
    new_frame = service.step()
    client.rpush(FRAME_KEY, cPickle.dumps(new_frame))
    pass

def main():
    client = redis_conn()
    service = Service(width=120, height=8)

    service.set_pixel(5, 5, 255, 0, 0)

    last_frame_time = time.time()
    while 1:
        current_time = time.time()
        delta_time = (current_time - last_frame_time)
        if delta_time < FRAME_TIME:
            continue

        last_frame_time = current_time

        handle_input()
        step_world(delta_time)
        update_buffer(service, client)

try:
    old_settings = setup()
    main()

finally:
    teardown(old_settings)