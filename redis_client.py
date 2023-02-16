from redis import Redis
from dotenv import dotenv_values

class RedisClient:
    def __init__(self):
        try:
            config = dotenv_values('config/local.env')
            self.host = config['REDIS_ENDPOINT']
        except KeyError:
            print('Missing/invalid configuration. Client expects REDIS_ENDPOINT')
        try:
            self.client = Redis(self.host)
            self.client.ping()
        except ConnectionError:
            print('Connection failed')

client = RedisClient()