import os
import json
from nypl_py_utils.functions.log_helper import create_log
from nypl_py_utils.functions.config_helper import load_env_file

from redis_client import RedisClient, RedisClientError

logger = create_log('lambda_function')


class ParameterError(Exception):
    def __init__(self, message=None):
        self.message = message


def handler(event, context):
    # Establish defaults in case of error:
    status = 500
    response = {}

    if 'docs' in event['path']:
        with open('swagger.json', 'r') as swagger_doc:
            response = json.loads(swagger_doc.read())
            status = 200
    else:
        try:
            load_env_file(os.environ.get('ENVIRONMENT', 'qa'), 'config/{}.yaml')
            endpoint = os.environ['REDIS_ENDPOINT']
            redis_client = RedisClient(endpoint)
        except RedisClientError as e:
            logger.error('error connecting to redis: {}'.format(e))

        try:
            logger.debug('Handling event: {}'.format(event))
            if event.get('queryStringParameters', None) is None:
                raise ParameterError('Missing queryStringParameters')
            if event['queryStringParameters'].get('barcodes', None) is None:
                raise ParameterError('Missing barcodes parameter')

            barcodes = event['queryStringParameters']['barcodes'].split(',')
            barcodes_with_prefix = ['m2-barcode-store-by-barcode-' + barcode for barcode in barcodes]
            logger.debug('Querying {}'.format(barcodes_with_prefix))

            response = redis_client.get_customer_codes(barcodes_with_prefix)
            status = response['status']
        except ParameterError as e:
            logger.error('Parameter error: {}'.format(e))
            status = 400
            response = {
                "status": 200,
                "error": e.message
            }

        except Exception as e:
            logger.error('Error getting barcodes: {}'.format(e))
    return {
          "statusCode": status,
          "body": json.dumps(response),
          "headers": {
            "Content-type": "application/json"
          }
      }
