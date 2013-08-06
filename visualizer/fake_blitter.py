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
    result = client.blpop(FRAME_KEY, 10)
    if result == None:
        return json.dumps(None)

    frame_name, frame = result
    frame = cPickle.loads(frame)
    frame = ''.join(frame)
    frame = map(lambda x: struct.unpack('!B', x)[0], frame)

    dump = []

    for i in range(0, len(frame), 3):
        dump.append([frame[i], frame[i+1], frame[i+2]])

    return json.dumps(dump)

run(host='localhost', port=8080)
