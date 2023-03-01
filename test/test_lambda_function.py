import pytest
import lambda_function

class TestLambdaFunction:
    @pytest.fixture
    def mock_redis_client(self, mocker):
        client = mocker.MagicMock()
        mocker.patch('lambda_function.RedisClient', return_value = client)
        return client
    
    @pytest.fixture
    def mock_kms_client(self, mocker):
        client = mocker.MagicMock()
        mocker.patch('lambda_function.KmsClient', return_value = client)
        client.decrypt.return_value = 'whatever'
        return client

    def test_lambda_handler_string_parse(self, mock_redis_client, mock_kms_client, mocker):
        event = {
                    "queryStringParameters": {
                        "barcodes": "33433101372807,33433132050471,33433131096251"
                    }
                }
        mock_redis_client.get_customer_codes.return_value = {"data": [], "status": [] }
        lambda_function.handler(event, {})
        mock_redis_client.get_customer_codes.assert_called_with(['m2-barcode-store-by-barcode-33433101372807', 'm2-barcode-store-by-barcode-33433132050471', 'm2-barcode-store-by-barcode-33433131096251'])
    