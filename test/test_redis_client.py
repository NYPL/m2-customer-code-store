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
    
    def test_get_customer_code_success(self, test_redis_client, key = '123', code = 'vk'):
        test_redis_client.client.get.return_value = code
        resp = test_redis_client.get_customer_code(key)
        assert resp['status'] == 200
        assert resp['barcode'] == key
        assert resp['m2CustomerCode'] == code
    
    def test_get_customer_code_failure_no_key(self, test_redis_client, key = None):
        test_redis_client.client.get.return_value = 'xyz'
        resp = test_redis_client.get_customer_code(key)
        assert resp['status'] == 400
        assert resp['message'] == 'No barcode supplied'
    
    def test_get_customer_code_failure_no_code(self, test_redis_client, key = '123'):
        test_redis_client.client.get.return_value = None
        resp = test_redis_client.get_customer_code(key)
        assert resp['status'] == 400
        assert resp['message'] == 'Customer code not found for barcode: 123'
    