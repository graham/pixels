from pixelpusher import Strip, bound
import random
import time

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
        service.release_dot(self.strip, self.dot)

class Ping(Animation):
    def init(self):
        self.level = 1.0
        self.red = bound(random.randint(-64, 255), 0, 255)
        self.green = bound(random.randint(-64, 255), 0, 255)
        self.blue = bound(random.randint(-64, 255), 0, 255)        

    def step(self):
        self.strip.set_pixel(self.dot, int(self.red * self.level), int(self.green * self.level), int(self.blue * self.level))

        ## change the decay based on power.
        if self.level > 0.25:
            self.level -= 0.02
        elif self.level <= 0.25:
            self.level -= 0.001

        if self.level > 0.0:
            return True
        else:
            self.strip.set_pixel(self.dot,0,0,0)
            return False

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

        dot = random.randint(0, 240)
        dot = bound(dot, 0, 239)
        used = self.used_pairs[small_index]

        self.used_pairs[small_index].append(dot)
        return self.strips[small_index], dot

    def release_dot(self, strip, dot):
        self.used_pairs[strip.sid].remove(dot)

    def step(self):
        self.animations = filter(lambda x: x.step(), self.animations)

if __name__ == '__main__':
    ip = ('192.168.0.99', 9897)
    x, y = Strip(ip, 0), Strip(ip, 1)
    s = Service([x, y])

    index = 0
    while True:
        index += 1
        s.step()
        time.sleep(0.003)

        if index % 2 == 0:
            s.animations.append( Ping(s) )

        for strip in s.strips:
            strip.update()

