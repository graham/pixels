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
FRAME_TIME = 0.02
FRAME_KEY = 'frame'

PLAYER_MOVE_TIME = 1.0
PLAYER_JUMP_TIME = 1.0
GROUND_MOVE_TIME = 0.025

GROUND_MIN = 10
GROUND_MAX = 25

GAP_MIN = 2
GAP_MAX = 6

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

def handle_input(game):
    c = get_input()
    if c == BUTTON_END:
        return True

    if c == ' ':
        game.jump()

    return False

def is_data():
    return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

class GroundArray(object):
    def __init__(self):
        self.index = 0
        self.width = 0
        self.max_width = 256
        self.data = [ 0 for i in range(self.max_width) ]
        self.generate_ground()

    def generate_ground(self):
        self.index = 0
        self.width = 0

        update_index = 0

        while True:
            ground_length = random.randint(GROUND_MIN, GROUND_MAX)
            gap_length = random.randint(GAP_MIN, GAP_MAX)

            if (self.width + (ground_length + gap_length)) > self.max_width:
                break

            for i in range(ground_length):
                self.data[update_index] = 1
                update_index += 1

            for i in range(gap_length):
                self.data[update_index] = 0
                update_index += 1

            self.width += (ground_length + gap_length)

    def step(self, delta_time):
        self.index += 1

    def steps_left(self): 
        return (self.width - self.index)

class Ground(object):
    def __init__(self, lead):
        self.arrays = [ GroundArray(), GroundArray() ]
        self.index = 0
        self.lead = lead
        self.time_since_move = 0

    def step(self, delta_time):
        self.time_since_move += delta_time
        if self.time_since_move < GROUND_MOVE_TIME:
            return

        self.time_since_move = 0

        active_array = self.arrays[self.index]
        active_array.step(delta_time)
        next_index = (self.index + 1) % 2

        if active_array.steps_left() == self.lead:
            self.arrays[next_index].generate_ground()
        if active_array.steps_left() == 0:
            self.index = next_index

    def data(self, index):
        active_array = self.arrays[self.index]
        if (active_array.index + index) < active_array.width: 
            return active_array.data[active_array.index + index]

        next_index = (self.index + 1) % 2
        other_array = self.arrays[next_index]
        offset_index = (index - active_array.steps_left())
        return other_array.data[offset_index]

class Player(object):
    def __init__(self):
        self.position = [5.0, 1.0]
        self.jump_time = 0
        self.air_time = 0
        self.is_jumping = False

    def step(self, delta_time):
        self.position[0] += (PLAYER_MOVE_TIME * delta_time)

        if self.is_jumping:
            self.step_jump(delta_time)

    def step_jump(self, delta_time):
        self.jump_time += delta_time
        if self.jump_time > self.air_time:
            self.position[1] = 1.0
            self.is_jumping = False

        inner = (2 * self.jump_time - 1)
        y = (-(inner * inner) + 1) * 6 + 1
        self.position[1] = y

    def jump(self, air_time):
        if self.is_jumping: 
            return 

        self.jump_time = 0
        self.is_jumping = True
        self.air_time = air_time

class Game(object):
    def __init__(self):
        self.ground = Ground(120)
        self.player = Player()

    def step(self, delta_time):
        self.ground.step(delta_time)
        self.player.step(delta_time)

    def update_service(self, service):
        active_array = self.ground.arrays[self.ground.index]

        service.fill(0, 0, 0)
        for i in range(service.width):
            if self.ground.data(i) == 1:
                service.set_pixel(i, 7, 128, 128, 128)

        player_x = int(self.player.position[0])
        player_y = int(7 - self.player.position[1])
        service.set_pixel(player_x, player_y, 0, 0, 255)

    def jump(self):
        self.player.jump(PLAYER_JUMP_TIME)

def main():
    client = redis_conn()
    service = Service(width=120, height=8)
    game = Game()

    def update_buffer():
        game.update_service(service)
        new_frame = service.step()
        client.rpush(FRAME_KEY, cPickle.dumps(new_frame))

    last_frame_time = time.time()
    while 1:
        current_time = time.time()
        delta_time = (current_time - last_frame_time)
        if delta_time < FRAME_TIME:
            continue

        last_frame_time = current_time

        handle_input(game)
        game.step(delta_time)
        update_buffer()

try:
    old_settings = setup()
    main()

finally:
    teardown(old_settings)