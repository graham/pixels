import sys
import select
import tty
import termios
import redis
import random
import time
import math
import cPickle

from pixelfont import PixelFont
from pixelpusher import pixel, build_strip, send_strip, bound
from service import Service
from util import redis_conn

BUTTON_END = '\x1b'
FRAME_TIME = 0.01
FRAME_KEY = 'frame'

PLAYER_MOVE_TIME = 1.0
PLAYER_JUMP_TIME = 0.4
PLAYER_START_X   = 15.0
PLAYER_START_Y   = 1.0
PLAYER_JUMP_HEIGHT  = 5

COUNT_DOWN_TIME = 3.0

GROUND_MOVE_TIME = 0.03
GROUND_ADJUST_TIME = 1500

BACKGROUND_MOVE_MULTIPLIER = 7.0

GROUND_MIN = 10
GROUND_MAX = 25

GAP_MIN = 3
GAP_MAX = 5

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
    def __init__(self, num_first_ground=None):
        self.index = 0
        self.width = 0
        self.max_width = 256
        self.data = [ 0 for i in range(self.max_width) ]
        self.generate_ground(num_first_ground)

    def generate_ground(self, num_first_ground=None):
        self.index = 0
        self.width = 0

        update_index = 0

        while True:
            ground_length = random.randint(GROUND_MIN, GROUND_MAX)
            gap_length = random.randint(GAP_MIN, GAP_MAX)

            if num_first_ground:
                ground_length = num_first_ground
                num_first_ground = None

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
        self.arrays = [ GroundArray(32), GroundArray() ]
        self.index = 0
        self.lead = lead
        self.time_since_move = 0
        self.move_time = GROUND_MOVE_TIME

    def step(self, delta_time):
        self.time_since_move += delta_time
        if self.time_since_move < self.move_time:
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

class Background(object):
    def __init__(self):
        self.index = 0
        self.width = 256
        self.array = [ 0 for i in range(self.width) ]
        self.generate_background()
        self.move_time = BACKGROUND_MOVE_MULTIPLIER * GROUND_MOVE_TIME
        self.time_since_move = 0

    def generate_background(self):
        previous_level = 0

        for i in range(self.width):
            level = previous_level
            level += random.randint(-1, 1)
            level = bound(level, 1, 8)

            self.array[i] = level
            previous_level = level

    def step(self, delta_time):
        self.time_since_move += delta_time
        if self.time_since_move < self.move_time:
            return

        self.time_since_move = 0

        previous_index = self.index
        self.index = (self.index + 1) % self.width

        self.calculate_index(previous_index)

    def data(self, index):
        return self.array[(self.index + index) % self.width]

    def calculate_index(self, index):
        previous_index = ((index - 1) % self.width)
        previous_level = self.array[previous_index]
        level = previous_level
        level += random.randint(-1, 1)
        level = bound(level, 1, 8)
        self.array[index] = level

    def draw(self, service):
        for i in range(service.width):
            level = self.data(i)
            for h in range(8):
                green = 0
                if h >= level and h != 7: 
                    green = 1 * (7 - (h - level))
                service.set_pixel(i, h, 0, green, 0)

class Player(object):
    def __init__(self):
        self.position = [PLAYER_START_X, PLAYER_START_Y]
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
            return

        inner = (2 / PLAYER_JUMP_TIME * self.jump_time - 1)
        y = (-(inner * inner) + 1) * PLAYER_JUMP_HEIGHT + 1
        self.position[1] = y

    def jump(self, air_time):
        if self.is_jumping: 
            return 

        self.jump_time = 0
        self.is_jumping = True
        self.air_time = air_time

class Game(object):
    def __init__(self):
        self.background = Background()
        self.ground = Ground(120)
        self.player = Player()
        self.font = PixelFont("images/font.tif")
        self.is_over = False
        self.total_time = 0.0

    def step(self, delta_time):
        self.total_time += delta_time

        if self.is_in_countdown():
            return

        self.ground.move_time = (GROUND_ADJUST_TIME - self.get_score()) * GROUND_MOVE_TIME / 1000.0
        self.background.move_time = (self.ground.move_time * BACKGROUND_MOVE_MULTIPLIER)

        self.background.step(delta_time)
        self.ground.step(delta_time)
        self.player.step(delta_time)

        if self.is_player_dead():
            self.is_over = True

    def is_in_countdown(self):
        return self.total_time < COUNT_DOWN_TIME

    def is_player_dead(self):
        if self.player.is_jumping:
            return False

        player_x = int(math.floor(self.player.position[0]))
        ground = self.ground.data(player_x)

        return (ground == 0)

    def get_number(self):
        if self.is_in_countdown():
            return self.get_countdown()
        return self.get_score()

    def get_countdown(self):
        return int(math.ceil(COUNT_DOWN_TIME - self.total_time))

    def get_score(self): 
        return (self.player.position[0] - PLAYER_START_X) * 10

    def update_service(self, service):
        active_array = self.ground.arrays[self.ground.index]

        self.background.draw(service)

        for i in range(service.width):
            if self.ground.data(i) == 1:
                service.set_pixel(i, 7, 128, 128, 128)

        player_x = int(math.floor(self.player.position[0]))
        player_y = int(math.floor(7 - self.player.position[1]))

        if self.is_over:
            player_y = 7

        service.set_pixel(player_x, player_y, 0, 0, 255)

        number = self.get_number()
        self.font.draw(str(int(number)), 0, 0, service, 255, 0, 0)

    def jump(self):
        self.player.jump(PLAYER_JUMP_TIME)

def main():
    client = redis_conn()
    service = Service(width=116, height=8)
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

        if game.is_over:
            break

try:
    old_settings = setup()
    main()

finally:
    teardown(old_settings)