import json
from nypl_py_utils import KmsClient
from nypl_py_utils.functions.log_helper import create_log

from dotenv import dotenv_values

from redis_client import RedisClient, RedisClientError

logger = create_log('lambda_function')

def handler(event, context):
    logger.info('Connecting to redis')
    kms_client = KmsClient()
    try:
        config = dotenv_values('config/local.env')
        endpoint = kms_client.decrypt(config['REDIS_ENDPOINT'])
        redis_client = RedisClient(endpoint)
    except RedisClientError as e:
        kms_client.close()
        logger.error('error connecting to redis', e)
    try:
        barcodes = event['queryStringParameters']['barcodes'].split(',')
        barcodes_with_prefix = ['m2-barcode-store-by-barcode-' + barcode for barcode in barcodes]
        response = redis_client.get_customer_codes(barcodes_with_prefix)
        return response
    except Exception as e:
        logger.error('error getting barcode ', e)
    return {
        "statusCode": response.status,
        "body": json.dumps({
            response
        })
    }