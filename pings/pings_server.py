from bottle import route, run, template
import redis
import cPickle
import json
import struct
import os

def redis_conn():
    host = os.environ.get('REDISHOST', '127.0.0.1')
    return redis.Redis(host=host)

client = redis_conn()
PING_KEY = 'ping'
pixel_width=116

@route('/')
def index():
    return open('pings.html').read()

@route('/clear')
def data():
    client.delete(PING_KEY)
    return 'ok'

@route('/ping')
def ping():
    print "PING"
    client.rpush(PING_KEY, "1")

run(host='localhost', port=8080, debug=True)
