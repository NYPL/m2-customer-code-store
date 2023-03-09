import pytest
import os
import main

class TestLambdaFunction:
    @pytest.fixture
    def mock_redis_client(self, mocker):
        client = mocker.MagicMock()
        mocker.patch('main.RedisClient', return_value = client)
        return client
    
    def test_lambda_handler_string_parse(self, mock_redis_client, mocker):
        event = {
                    "queryStringParameters": {
                        "barcodes": "33433101372807,33433132050471,33433131096251"
                    }
                }
        mock_redis_client.get_customer_codes.return_value = {"data": [], "status": [] }
        main.handler(event, {})
        mock_redis_client.get_customer_codes.assert_called_with(['m2-barcode-store-by-barcode-33433101372807', 'm2-barcode-store-by-barcode-33433132050471', 'm2-barcode-store-by-barcode-33433131096251'])
    