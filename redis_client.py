from redis import StrictRedis
from nypl_py_utils.functions.log_helper import create_log


class RedisClient:
    def __init__(self, endpoint):
        self.host = endpoint
        self.logger = create_log('redis_client')
        self.client = self._connect()

    def _connect(self):
        try:
            client = StrictRedis(host=self.host, decode_responses=True)
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

    def _remove_prefix(self, barcode):
        return barcode.replace("m2-barcode-store-by-barcode-", "")

# Expects a list of strings that look like this: m2-barcode-store-by-barcode-{barcode}
    def get_customer_codes(self, barcodes):
        resp = {}
        barcodes_with_customer_codes = []
        customer_codes = self.client.mget(barcodes)
        failed_barcodes = []
        barcodes_length = len(barcodes) if barcodes is not None else 0
        no_customer_codes = all(code is None for code in customer_codes)
        if no_customer_codes or barcodes_length == 0:
            resp['status'] = 400
            if barcodes is None or barcodes_length == 0:
                resp['message'] = 'No barcode supplied'
            else:
                resp['message'] = 'Customer codes not found for barcodes: ' \
                    + ', '.join(map(self._remove_prefix, barcodes))
        else:
            for i in range(barcodes_length):
                if customer_codes[i] is not None:
                    barcodes_with_customer_codes.append({
                        "barcode": self._remove_prefix(barcodes[i]),
                        "m2CustomerCode": customer_codes[i]})
                else:
                    failed_barcodes.append(barcodes[i])

            resp['status'] = 200
            resp['data'] = barcodes_with_customer_codes
            if len(failed_barcodes) > 0:
                self.logger.debug('Barcodes {} returned no customer codes'.format(', '.join(failed_barcodes)))
        return resp

    def _danger_delete(self, *, pattern='', key=''):
        if len(pattern) > 0:
            for key in self.client.scan_iter(pattern):
                self.client.delete(key)
        if len(key) > 0:
            self.client.delete('key')


class RedisClientError(Exception):
    def __init__(self, message=None):
        self.message = message
