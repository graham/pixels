from pixelpusher import Strip, bound
import random
import time

MAX = 255
MID = 128
OFF = 0
STRIP_LENGTH = 240

class Animation(object):
    def __init__(self, service):
        self.strip, self.dot = service.get_open_dot()
        self.init()
    def __str__(self):
        return "<Animation: %s strip:%i | %i>" % (
            self.__class__.__name__, self.strip.sid, self.dot)
    def init(self):
        pass
    def step(self):
        pass
    def finish(self, service):
        self.strip.set_pixel(self.dot, OFF, OFF, 0)
        service.release_dot(self.strip, self.dot)

class Ping(Animation):
    def init(self):
        self.level = 1.0
        self.red = bound(random.randint(-MID, MAX), OFF, MID)
        self.blue = bound(random.randint(-MID, MAX), OFF, MID)
        self.green = bound(random.randint(-MID, MAX), OFF, MID)

    def step(self):
        self.strip.set_pixel(self.dot, int(self.red * self.level), int(self.green * self.level), int(self.blue * self.level))

        ## change the decay based on power.
        if self.level > 0.45:
            self.level -= 0.025
        elif self.level <= 0.45 and self.level > 0.2:
            self.level -= 0.01
        elif self.level <= 0.2:
            self.level -= 0.005

        if self.level > 0.0:
            return True
        else:
            self.strip.set_pixel(self.dot,OFF,OFF,0)
            return False

class Dots(Animation):
    def init(self):
        self.red = bound(random.randint(-MID, MID), OFF, MID)
        self.blue = bound(random.randint(-MID, MID), OFF, MID)
        self.green = bound(random.randint(-MID, MID), OFF, MID)
        self.index = 0

    def step(self):
        self.index += 1
        if self.index % 50 < 25:
            self.strip.set_pixel(self.dot, OFF, OFF, 0)
        else:
            self.strip.set_pixel(self.dot, self.red, self.green, self.blue)

        if self.index < (50 * 3):
            return True
        else:
            return False

class CrossFade(Animation):
    def init(self):
        self.color_start = [random.randint(0,MAX),random.randint(0,MAX),random.randint(0,MAX)]
        self.color_end = [random.randint(0,MAX),random.randint(0,MAX),random.randint(0,MAX)]

        self.color_diff = [
            self.color_start[0] - self.color_end[0],
            self.color_start[1] - self.color_end[1],
            self.color_start[2] - self.color_end[2]]

        self.value = 0.0
        self.count = 0

    def step(self):
        self.value += 0.01 * (-1 if self.count % 2 == 0 else 1)
        
        new_color = map(lambda x: self.value * x, self.color_diff)
        newr = int(self.color_start[0] + new_color[0])
        newg = int(self.color_start[1] + new_color[1])
        newb = int(self.color_start[2] + new_color[2])


        self.strip.set_pixel(self.dot,
                             bound(newr if new_color[0] >= 0 else MAX + newr, OFF, MAX),
                             bound(newg if new_color[1] >= 0 else MAX + newg, OFF, MAX),
                             bound(newb if new_color[2] >= 0 else MAX + newb, OFF, MAX))

        if self.count >= 4:
            return False
        else:
            if self.value > 1 or self.value < 0.0:
                self.count += 1
                self.value = bound(self.value, 0.01, 0.99)
                return True
        return True

class Service(object):
    def __init__(self, strips):
        self.strips = strips
        self.animations = []
        self.used_pairs = [[] for i in strips]

    def get_open_dot(self):
        small_index = 0
        for index, i in enumerate(self.used_pairs):
            if len(i) < len(self.used_pairs[small_index]):
                small_index = index

        dot = random.randint(OFF, STRIP_LENGTH)
        dot = bound(dot, OFF, STRIP_LENGTH - 1)
        used = self.used_pairs[small_index]

        self.used_pairs[small_index].append(dot)
        return self.strips[small_index], dot

    def release_dot(self, strip, dot):
        self.used_pairs[strip.sid].remove(dot)

    def step(self):
        remain = []
        drop = []
        for i in self.animations:
            if i.step():
                remain.append(i)
            else:
                i.finish(self)
                drop.append(i)

        self.animations = remain
                

if __name__ == '__main__':
    ip = ('192.168.0.99', 9897)
    w, z = Strip(ip, 0), Strip(ip, 1)

    s = Service([w, z])

    index = 0
    while True:
        index += 1
        s.step()
        time.sleep(0.01)

        if index % 2 == 0:
            s.animations.append( Ping(s) )
        for strip in s.strips:
            strip.update()

