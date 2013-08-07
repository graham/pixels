import struct
import socket

def bound(value, bottom, top):
    if value < bottom:
        return bottom
    if value > top:
        return top
    return value

## Doing things the functional way.

def pixel(red, green, blue):
    red = bound(red, 0, 255)
    green = bound(green, 0, 255)
    blue = bound(blue, 0, 255)

    return struct.pack('!BBB', red, green, blue)

def is_pixel_blank(pixel):
    return pixel == '\x00\x00\x00'

def multiply_pixel(pix, mult): 
    p = struct.unpack('!BBB', pix)
    r = p[0] * mult
    g = p[1] * mult
    b = p[2] * mult
    return pixel(r, g, b)

def build_strip(id=0):
    return [struct.pack('!xxxxB', id)]

def send_strip(strip, ip):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(''.join(strip), ip)

## End functional stuff.


## Do things the Object way.
## This is a little less efficient if you want to update multiple strips
## in a single packet, but it also means you can think of strips as separate
## from their controllers.

class Strip(object):
    def __init__(self, ip, sid):
        self.ip = ip
        self.sid = sid
        self.pixel_map = [pixel(0, 0, 0) for i in range(0, 240)]
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.dirty = False
    
    def update(self):
        strip = build_strip(self.sid)
        self.sock.sendto(''.join(strip + self.pixel_map), self.ip)
        self.dirty = False

    def set_pixel(self, index, red, green, blue):
        self.pixel_map[index] = pixel(red, green, blue)
        self.dirty = True

## That's really the end of the OO stuff.

