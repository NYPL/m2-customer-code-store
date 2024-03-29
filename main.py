import os
import json
from nypl_py_utils.functions.log_helper import create_log
from nypl_py_utils.functions.config_helper import load_env_file

from redis_client import RedisClient, RedisClientError
import json

logger = create_log('lambda_function')

def handler(event, context):
    logger.info('Connecting to redis')
    if 'docs' in event['path']:
        with open('swagger.json', 'r') as swagger_doc:
            response = json.loads(swagger_doc.read())
            status = 200
    else:
        try:
            load_env_file(os.environ['ENVIRONMENT'], 'config/{}.yaml')
            endpoint = os.environ['REDIS_ENDPOINT']
            redis_client = RedisClient(endpoint)
        except RedisClientError as e:
            logger.error('error connecting to redis: {}'.format(e))
        try:
            barcodes = event['queryStringParameters']['barcodes'].split(',')
            barcodes_with_prefix = ['m2-barcode-store-by-barcode-' + barcode for barcode in barcodes]
            response = redis_client.get_customer_codes(barcodes_with_prefix)
            status = response['status']
        except Exception as e:
            logger.error('error getting barcodes :{}'.format(e))
    return {
                "statusCode": status,
                "body": json.dumps(response),
                "headers": {
                "Content-type": "application/json"
                }
            }
