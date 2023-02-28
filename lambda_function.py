import json
import os
from botocore.exceptions import ClientError
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
        redis_endpoint = config['REDIS_ENPOINT']
        redis_client = RedisClient(redis_endpoint)
    except RedisClientError as e:
        # do i need to catch the previous error here?
        kms_client.close()
        logger.error('error connecting to redis', e)
    try:
        response = redis_client.get_customer_code('m2-barcode-store-by-barcode-'+event['barcode'])
        return response
    except Exception as e:
        # what is the errorrr
        logger.error('error getting barcode ', e)
    return {
        "statusCode": response.status,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            "message": response.message
        })
    }