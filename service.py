from pixelpusher import pixel, bound
from pixelfont import PixelFont
from postprocess import BlurLeft, BlurRight
import random
import time
import redis
import cPickle
import Image

from util import redis_conn

FRAME_KEY = 'frame'
MAX = 255
MID = 128
OFF = 0
FRAME_TIME = 0.03

class Animation(object):
    def __init__(self, service):
        self.loc = [0, 0]
    def init(self, service):
        pass
    def step(self, service, delta_time):
        pass
    def finish(self, service):
        service.set_pixel(self.loc[0], self.loc[1], 0, 0, 0)

class Ping(Animation):
    def init(self, service):
        self.level = 1.0
        self.red = bound(random.randint(-MID, MAX), OFF, MID)
        self.blue = bound(random.randint(-MID, MAX), OFF, MID)
        self.green = bound(random.randint(-MID, MAX), OFF, MID)
        self.loc = [random.randint(0, service.width-1), random.randint(0, service.height-1)]

    def init(self, service, red, green, blue):
        self.level = 1.0
        self.red = bound(red, OFF, MID)
        self.blue = bound(blue, OFF, MID)
        self.green = bound(green, OFF, MID)
        self.loc = [random.randint(0, service.width-1), random.randint(0, service.height-1)]

    def step(self, service, delta_time=0):
        service.set_pixel(self.loc[0], self.loc[1], int(self.red * self.level), int(self.green * self.level), int(self.blue * self.level))

        outer_level = self.level * 0.05
        if self.loc[0] > 0: 
            service.set_pixel(self.loc[0] - 1, self.loc[1], int(self.red * outer_level), int(self.green * outer_level), int(self.blue * outer_level))            
        if self.loc[0] < (service.width - 1): 
            service.set_pixel(self.loc[0] + 1, self.loc[1], int(self.red * outer_level), int(self.green * outer_level), int(self.blue * outer_level))            
        if self.loc[1] > 0: 
            service.set_pixel(self.loc[0], self.loc[1] - 1, int(self.red * outer_level), int(self.green * outer_level), int(self.blue * outer_level))            
        if self.loc[1] < (service.height - 1): 
            service.set_pixel(self.loc[0], self.loc[1] + 1, int(self.red * outer_level), int(self.green * outer_level), int(self.blue * outer_level))            

        ## change the decay based on power.
        self.level -= 0.05

        if self.level > 0.0:
            return True
        else:
            service.set_pixel(self.loc[0], self.loc[1], OFF, OFF, OFF)
            if self.loc[0] > 0: 
                service.set_pixel(self.loc[0] - 1, self.loc[1], OFF, OFF, OFF)
            if self.loc[0] < (service.width - 1): 
                service.set_pixel(self.loc[0] + 1, self.loc[1], OFF, OFF, OFF)
            if self.loc[1] > 0: 
                service.set_pixel(self.loc[0], self.loc[1] - 1, OFF, OFF, OFF)
            if self.loc[1] < (service.height - 1): 
                service.set_pixel(self.loc[0], self.loc[1] + 1, OFF, OFF, OFF)
            return False

class SpriteAnimation(Animation):
    def init(self, filename, frame_width, frame_height, time_per_frame):
        image = Image.open(filename)
        self.image_data = image.getdata()
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.num_frames = int(self.image_data.size[0] / self.frame_width)
        width, height = image.size
        self.image_width = width
        self.time_per_frame = time_per_frame
        self.accumulated_time = self.time_per_frame
        self.current_frame = 0

    def step(self, service, delta_time):
        self.accumulated_time += delta_time
        if self.accumulated_time < self.time_per_frame:
            return True

        self.current_frame = (self.current_frame + 1) % self.num_frames
        self.accumulated_time = 0

        frame_start = (self.current_frame * self.frame_width)
        for x in range(0, self.frame_width):
            for y in range(0, self.frame_height):
                pixel_data = self.image_data[frame_start + x + (y * self.image_width)]
                if pixel_data[3] > 0:
                    alpha = (pixel_data[3] / 255.0)
                    service.set_pixel(x, y, (pixel_data[0] * alpha), (pixel_data[1] * alpha), (pixel_data[2] * alpha))
                else:
                    service.set_pixel(x, y, OFF, OFF, OFF)

        return True

class Service(object):
    DEFAULT_WIDTH = 116
    DEFAULT_HEIGHT = 8

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.pixel_map = [ pixel(0, 0, 0) for i in range( width * height ) ]
        self.animations = []
        self.post_process = []

    def set_pixel(self, x, y, red, green, blue):
        index = (y * self.width) + x
        self.pixel_map[index] = pixel(red, green, blue)

    def add(self, ani):
        c = ani(self)
        c.init(self)
        self.animations.append(c)

    def add_instance(self, ani_instance):
        self.animations.append(ani_instance)

    def add_post_process(self, post_process):
        self.post_process.append(post_process)

    def clear_post_process(self):
        self.post_process = []

    def step(self, delta_time=0):
        remain = []
        drop = []
        for i in self.animations:
            if i.step(self, delta_time):
                remain.append(i)
            else:
                i.finish(self)
                drop.append(i)

        self.animations = remain

        return_map = self.get_pixel_map()
        for i in self.post_process:
            return_map = i.apply(self, return_map)

        return return_map

    def shift_left(self):
        new_map = []

        for i in range(0, self.height):
            line = self.pixel_map[(self.width*i)+1:(self.width*(i+1))] + [pixel(0, 0, 0)]
            new_map += line

        self.pixel_map = new_map

    def shift_right(self):
        new_map = []

        for i in range(0, self.height):
            line = [pixel(0, 0, 0)] + self.pixel_map[(self.width*i):(self.width*(i+1))-1]
            new_map += line

        self.pixel_map = new_map

    def shift_up(self):
        new_map = self.pixel_map[:self.width*(self.height-1)]
        new_map += [pixel(0, 0, 0) for i in xrange(self.width)]
        self.pixel_map = new_map

    def shift_down(self):
        new_map = [pixel(0, 0, 0) for i in xrange(self.width)]
        new_map += self.pixel_map[:self.width*(self.height-1)]
        self.pixel_map = new_map


    def fill(self, red, green, blue):
        for x in range(0, self.width):
            for y in range(0, self.height):
                self.set_pixel(x, y, red, green, blue)

    def get_pixel_map(self):
        return self.pixel_map

if __name__ == '__main__':
    client = redis_conn()
    s = Service(width=Service.DEFAULT_WIDTH, height=Service.DEFAULT_HEIGHT)

    def add_blur_left():
        s.add_post_process(BlurLeft)
        update()

    def clear_post_process():
        s.clear_post_process()
        update()

    def safe_check():
        while client.llen(FRAME_KEY) > 50:
            time.sleep(0.05)

    def update(delta_time=0):
        safe_check()
        new_frame = s.step(delta_time)
        client.rpush(FRAME_KEY, cPickle.dumps(new_frame))

    font = PixelFont("images/font.tif")

    def justworks():
        render_offset = 20
        font.draw("IT ", render_offset + 0, 0, s, 255, 255, 255)
        font.draw("JUST WORK", render_offset + 18, 0, s, 0, 0, 255)
        font.draw("S", render_offset + 72, 0, s, 255, 255, 255)
        update()

    def print_text(text):
        render_offset = 20
        font.draw(text, render_offset + 0, 0, s, 255, 255, 255)
        update()

    def run():
        sprite_animation = SpriteAnimation(s)
        sprite_animation.init("images/run16.png", 16, 16, 0.025)
        s.add_instance(sprite_animation)

        last_frame_time = time.time()
        while True:
            current_time = time.time()
            delta_time = (current_time - last_frame_time)
            if delta_time < FRAME_TIME:
                continue
            
            last_frame_time = current_time
            update(delta_time)

    def wizard():
        sprite_animation = SpriteAnimation(s)
        sprite_animation.init("images/animation.png", 16, 8, 0.5)
        s.add_instance(sprite_animation)

        total_time = 5.0
        last_frame_time = time.time()
        while total_time > 0:
            current_time = time.time()
            delta_time = (current_time - last_frame_time)
            if delta_time < FRAME_TIME:
                continue

            last_frame_time = current_time
            update(delta_time)
            total_time -= delta_time

    def pings():
        while True:
            time.sleep(0.02)
            s.add(Ping)
            s.add(Ping)
            s.add(Ping)
            update()
