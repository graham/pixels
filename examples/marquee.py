import redis
import time
import cPickle

from pixelfont import PixelFont
from service import Service
from util import redis_conn

def main():
    client = redis_conn()
    s = Service(width=120, height=8)
    font = PixelFont("font.tif")
    text = 'IT JUST WORKS'
    client.set('message', text)
    width = font.draw(text, 120, 0, s, 0, 0, 255) - 120
    offset = 120
    while True:
        frame = s.step(0.05)
        client.rpush('frame', cPickle.dumps(frame))
        time.sleep(0.05)
        offset -= 1
        s.shift_left()
        if offset < 0:
            offset = 120
        if offset > 120 - width -1:
            new_text = client.get('message')
            if new_text != text:
                text = new_text
                width = font.draw(text, 120, 0, s, 0, 0, 255)
                offset = 120
            else:
                font.draw(text, offset, 0, s, 0, 0, 255)

if __name__ == "__main__":
    main()
