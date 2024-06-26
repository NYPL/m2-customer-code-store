import pytest
import main
import os
import json


class TestLambdaFunction:
    @pytest.fixture
    def mock_redis_client(self, mocker):
        client = mocker.MagicMock()
        mocker.patch('main.RedisClient', return_value=client)
        return client

    @pytest.fixture
    def mock_py_utils(self, mocker):
        mock_load_env_file = mocker.MagicMock()
        mocker.patch('main.load_env_file', return_value=mock_load_env_file)
        return mock_load_env_file

    def test_lambda_handler_required_params(self, mock_redis_client, mock_py_utils):
        os.environ['REDIS_ENDPOINT'] = 'abc'
        resp = main.handler({"path": "/api/v0.1/m2-customer-codes"}, {})
        assert json.loads(resp['body'])['error'] == 'Missing queryStringParameters'
        resp = main.handler({"path": "/api/v0.1/m2-customer-codes", "queryStringParameters": {}}, {})
        assert json.loads(resp['body'])['error'] == 'Missing barcodes parameter'

    def test_lambda_handler_string_parse(self, mock_redis_client, mock_py_utils, mocker):
        os.environ['REDIS_ENDPOINT'] = 'abc'
        event = {
            "path": "api/v0.1/m2-customer-code-store",
            "queryStringParameters": {
                "barcodes": "33433101372807,33433132050471,33433131096251"
            }
        }
        mock_redis_client.get_customer_codes.return_value = {"data": [], "status": []}
        main.handler(event, {})
        mock_redis_client.get_customer_codes.assert_called_with([
            'm2-barcode-store-by-barcode-33433101372807',
            'm2-barcode-store-by-barcode-33433132050471',
            'm2-barcode-store-by-barcode-33433131096251'])

    def test_docs_endpoint(self, mock_redis_client, mock_py_utils, mocker):
        resp = main.handler({"path": "api/v0.1/docs"}, {})
        swagger_doc = json.loads(resp['body'])
        assert swagger_doc['swagger'] == '2.0'
        
