from pixelpusher import pixel, bound
from pixelfont import PixelFont
import random
import time
import redis
import cPickle

FRAME_KEY = 'frame'
MAX = 255
MID = 128
OFF = 0

class Animation(object):
    def __init__(self, service):
        self.loc = [0, 0]
    def init(self, service):
        pass
    def step(self, service):
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

    def step(self, service):
        service.set_pixel(self.loc[0], self.loc[1], int(self.red * self.level), int(self.green * self.level), int(self.blue * self.level))

        ## change the decay based on power.
        self.level -= 0.05

        if self.level > 0.0:
            return True
        else:
            service.set_pixel(self.loc[0], self.loc[1],OFF,OFF,OFF)
            return False            
        
class Service(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.pixel_map = [ pixel(0, 0, 0) for i in range( width * height ) ]
        self.animations = []
        
    def set_pixel(self, x, y, red, green, blue):
        index = (y * self.width) + x
        self.pixel_map[index] = pixel(red, green, blue)

    def add(self, ani):
        c = ani(self)
        c.init(self)
        self.animations.append(c)

    def step(self):
        remain = []
        drop = []
        for i in self.animations:
            if i.step(self):
                remain.append(i)
            else:
                i.finish(self)
                drop.append(i)

        self.animations = remain
        return self.pixel_map

if __name__ == '__main__':
    client = redis.Redis()
    s = Service(width=120, height=8)

    font = PixelFont("font.tif")

    offset = 0

    while True:
        time.sleep(0.03)
#        s.add(Ping)
    
        offset = (offset + 1) % (s.width * 2)
        render_offset = (offset - s.width)

        font.draw("IT ", render_offset + 0, 0, s, 255, 255, 255)
        font.draw("JUST WORK", render_offset + 18, 0, s, 0, 0, 255)
        font.draw("S", render_offset + 72, 0, s, 255, 255, 255)
        new_frame = s.step()
        client.rpush(FRAME_KEY, cPickle.dumps(new_frame))
