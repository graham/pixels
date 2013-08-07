import redis
import os

def redis_conn():
    host = os.environ.get('REDISHOST', '127.0.0.1')
    return redis.Redis(host=host)
