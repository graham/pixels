from bottle import route, run, template
import redis
import cPickle
import json
import struct

client = redis.Redis()
FRAME_KEY = 'frame'
pixel_width=120

@route('/')
def index():
    return open('main.html').read()

@route('/clear')
def data():
    client.delete(FRAME_KEY)
    return 'ok'

@route('/jquery.js')
def jquery():
    return open('jquery.js').read()

@route('/data')
def data():
    frame_name, frame = client.blpop(FRAME_KEY, 10)
    if frame == None:
        return json.dumps(None)

    frame = cPickle.loads(frame)
    frame = ''.join(frame)
    frame = map(lambda x: struct.unpack('!B', x)[0], frame)

    return json.dumps(frame)

run(host='localhost', port=8080)
