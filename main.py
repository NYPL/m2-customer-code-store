import os
import json
from nypl_py_utils.functions.log_helper import create_log
from nypl_py_utils.functions.config_helper import load_env_file

from redis_client import RedisClient, RedisClientError


class ParameterError(Exception):
    def __init__(self, message=None):
        self.message = message


def handler(event, context):
    return Main.instance().handle(event)


class Main:
    _instance = None
    logger = None

    def __init__(self):
        self.logger = create_log("main", json=True)

        try:
            load_env_file(os.environ.get("ENVIRONMENT", "qa"), "config/{}.yaml")
            endpoint = os.environ["REDIS_ENDPOINT"]
            self.redis_client = RedisClient(endpoint)
        except Exception as e:
            error_message = "Error connecting to redis: {}".format(e)
            self.logger.error(error_message)

    def handle(self, event):
        if "docs" in event["path"]:
            with open("swagger.json", "r") as swagger_doc:
                response = json.loads(swagger_doc.read())
        else:
            try:
                self.logger.debug("Handling event: {}".format(event))
                if event.get("queryStringParameters", None) is None:
                    raise ParameterError("Missing queryStringParameters")
                if event["queryStringParameters"].get("barcodes", None) is None:
                    raise ParameterError("Missing barcodes parameter")

                barcodes = event["queryStringParameters"]["barcodes"].split(",")

                response = {
                    'data': self.redis_client.get_customer_codes(barcodes),
                    'status': 200
                }
            except ParameterError as e:
                self.logger.info("Parameter error: {}".format(e))
                return self.error_response(400, e.message)

            except RedisClientError as e:
                # In this context, the only RedisClientErrors that may be raised are user error
                self.logger.info("RedisClient error: {}".format(e))
                return self.error_response(400, e.message)

            except Exception as e:
                self.logger.error("Unknown error: {}".format(e))
                error_message = "Error getting barcodes: {}".format(e)
                return self.error_response(500, error_message)
        return {
            "statusCode": 200,
            "body": json.dumps(response),
            "headers": {"Content-type": "application/json"},
        }

    def error_response(self, status, message):
        return {
            "statusCode": status,
            "body": json.dumps({"error": message, "status": status}),
            "headers": {"Content-type": "application/json"},
        }

    def instance(reset=False):
        if Main._instance is None or reset:
            Main._instance = Main()
        return Main._instance
