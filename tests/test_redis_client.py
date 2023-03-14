import pytest
import redis_client

class TestRedisClient:
    @pytest.fixture
    def test_redis_client(self, mocker):
        mocker.patch('redis_client.create_log')
        mocker.patch('redis_client.StrictRedis')
        return  redis_client.RedisClient('test.net')
    
    def test_connect(self, test_redis_client):
        test_redis_client.client.ping.assert_called_once()
    
    def test_get_customer_code_success(self, test_redis_client):
        codes = ['ab','cd', 'ef']
        barcodes = ['123','456','789']
        test_redis_client.client.mget.return_value = codes
        resp = test_redis_client.get_customer_codes(barcodes)
        assert resp['status'] == 200
        assert resp['data'] == [{ "barcode": "123", "m2CustomerCode": 'ab'},
                                { "barcode": "456", "m2CustomerCode": 'cd'},
                                { "barcode": "789", "m2CustomerCode": 'ef'}]
    
    def test_get_customer_code_failure_none_barcodes(self, test_redis_client):
        test_redis_client.client.get.return_value = 'xyz'
        resp = test_redis_client.get_customer_codes(None)
        assert resp['status'] == 400
        assert resp['message'] == 'No barcode supplied'
    
    def test_get_customer_code_one_failure(self, test_redis_client):
        codes = ['ab', None, 'ef']
        barcodes = ['123', '456', '789']
        test_redis_client.client.mget.return_value = codes
        resp = test_redis_client.get_customer_codes(barcodes)
        assert resp['status'] == 200
        assert resp['data'] == [{ "barcode": "123", "m2CustomerCode": 'ab'},
                                { "barcode": "789", "m2CustomerCode": 'ef'}]
    
    def test_get_customer_code_no_response(self, test_redis_client):
        barcodes = ['m2-barcode-store-by-barcode-123', 'm2-barcode-store-by-barcode-456', 'm2-barcode-store-by-barcode-789']
        test_redis_client.client.mget.return_value = [None,None,None]
        resp = test_redis_client.get_customer_codes(barcodes)
        assert resp['status'] == 400
        assert resp['message'] == 'Customer codes not found for barcodes: 123, 456, 789'
    
    def test_get_customer_code_empty_barcodes(self, test_redis_client):
        test_redis_client.client.mget.return_value = 'spaghetti'
        resp = test_redis_client.get_customer_codes([])
        assert resp['status'] == 400
        assert resp['message'] == 'No barcode supplied'