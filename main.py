import os
import json
from nypl_py_utils.functions.log_helper import create_log
from nypl_py_utils.functions.config_helper import load_env_file

from redis_client import RedisClient, RedisClientError

logger = create_log('lambda_function')


def handler(event, context):
    logger.info('Connecting to redis')
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
    except Exception   as e:
        logger.error('error in RedisClient :{}'.format(e))
    return {
            "statusCode": response['status'],
            "body": json.dumps(response),
            "headers": {
            "Content-type": "application/json"
            }
    }