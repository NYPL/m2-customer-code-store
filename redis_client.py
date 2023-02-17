from redis import StrictRedis
from dotenv import dotenv_values

class RedisClient:
    def __init__(self):
        try:
            config = dotenv_values('config/local.env')
            self.host = config['REDIS_ENDPOINT']
        except KeyError:
            print('Missing/invalid configuration. Client expects REDIS_ENDPOINT')
        try:
            self.client = StrictRedis(host = self.host, decode_responses=True)
            self.client.ping()
        except ConnectionError:
            print('Connection failed')
        print('connected to redis')

    def pipeline(self):
        return self.client.pipeline()
    
    def get_em(self):
        for key in self.client.scan_iter(count=100):
            print(key)

    def _danger_delete(self, *, pattern='', key=''):
        if len(pattern) > 0:
            for key in self.client.scan_iter(pattern):
                self.client.delete(key)
        if len(key) > 0:
            self.client.delete('key')
