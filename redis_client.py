from redis import StrictRedis
from nypl_py_utils.functions.log_helper import create_log

class RedisClient:
    def __init__(self, endpoint):
        self.host = endpoint
        self.logger = create_log('redis_client')
        self.client = self._connect()

    def _connect(self):
        try:
            client = StrictRedis(host = self.host, decode_responses=True)
            client.ping()
        except ConnectionError as e:
            self.logger.error('Error connecting to redis at endpoint: ' + self.host)
            raise RedisClientError(f'Connected to redis at: {self.host}'.format(e))
        self.logger.info('Connected to redis at:' + self.host)
        return client

    def pipeline(self):
        return self.client.pipeline()
    
    def get_size(self):
        return self.client.dbsize()
    
    def get_customer_code(self, key):
        resp = {}
        code = self.client.get(key)
        if code == None or key == None:
            resp['status'] = 400 
            if key == None:
                resp['message'] = 'No barcode supplied'
            else:
                resp['message'] = 'Customer code not found for barcode: ' + key 
        else:
            resp['status'] = 200
            resp['barcode'] = key 
            resp['m2CustomerCode'] = code
        return resp

    def _danger_delete(self, *, pattern='', key=''):
        if len(pattern) > 0:
            for key in self.client.scan_iter(pattern):
                self.client.delete(key)
        if len(key) > 0:
            self.client.delete('key')

class RedisClientError(Exception):
    def __init__(self, message = None):
        self.message = message