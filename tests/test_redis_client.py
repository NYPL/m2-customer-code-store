import os
import pytest
from redis_client import RedisClient, RedisClientError


class TestRedisClient:
    @pytest.fixture
    def test_redis_client(self, mocker):
        mock_logger = mocker.MagicMock()
        mock_logger.patch("error")
        mocker.patch("redis_client.create_log", return_value=mock_logger)
        mocker.patch("redis_client.StrictRedis")
        return RedisClient("test.net")

    def test_connect(self, test_redis_client):
        test_redis_client.client.ping.assert_called_once()

    def test_get_customer_code_success(self, test_redis_client):
        codes = ["ab", "cd", "ef"]
        barcodes = ["123", "456", "789"]
        test_redis_client.client.mget.return_value = codes
        resp = test_redis_client.get_customer_codes(barcodes)
        assert resp == [
            {"barcode": "123", "m2CustomerCode": "ab"},
            {"barcode": "456", "m2CustomerCode": "cd"},
            {"barcode": "789", "m2CustomerCode": "ef"},
        ]

    def test_get_customer_code_failure_none_barcodes(self, test_redis_client):
        test_redis_client.client.get.return_value = "xyz"
        with pytest.raises(RedisClientError, match=r"No barcode supplied"):
            test_redis_client.get_customer_codes(None)

    def test_get_customer_code_one_failure(self, test_redis_client):
        codes = ["ab", None, "ef"]
        barcodes = ["123", "456", "789"]
        test_redis_client.client.mget.return_value = codes
        resp = test_redis_client.get_customer_codes(barcodes)
        assert resp == [
            {"barcode": "123", "m2CustomerCode": "ab"},
            {"barcode": "456", "m2CustomerCode": None},
            {"barcode": "789", "m2CustomerCode": "ef"},
        ]

    def test_get_customer_code_no_response(self, test_redis_client):
        barcodes = ["123", "456", "789"]
        test_redis_client.client.mget.return_value = [None, None, None]
        with pytest.raises(
            RedisClientError,
            match=r"Customer codes not found for barcodes: 123, 456, 789",
        ):
            test_redis_client.get_customer_codes(barcodes)

    def test_get_customer_code_empty_barcodes(self, test_redis_client):
        test_redis_client.client.mget.return_value = "spaghetti"
        with pytest.raises(RedisClientError, match=r"No barcode supplied"):
            test_redis_client.get_customer_codes([])

    def test_monitor_failed_lookups(self, test_redis_client):
        # Keep track of last 5 lookups:
        os.environ["MONITOR_LOOKUPS_COUNT"] = "5"
        # Log error if lookup failure rises above 20%:
        os.environ["MONITOR_FAILURE_RATE"] = "0.21"

        # Simulate 3 successful lookups & one failure:
        test_redis_client.monitor_failed_lookups(
            [
                {"barcode": "123", "m2CustomerCode": "ab"},
                {"barcode": "234", "m2CustomerCode": "ab"},
                {"barcode": "345", "m2CustomerCode": "ab"},
                {"barcode": "987", "m2CustomerCode": None},
            ]
        )
        test_redis_client.logger.assert_not_called()

        # Simulate one additional failed lookup:
        test_redis_client.monitor_failed_lookups(
            [
                {"barcode": "789", "m2CustomerCode": None},
            ]
        )
        # 2 of last 5 requests failed, so expect an error log:
        test_redis_client.logger.error.assert_called_with(
            "Lookup failure rate is 40.0%"
        )
        test_redis_client.logger.error.reset_mock()

        # Simulate another 4 successful lookups:
        test_redis_client.monitor_failed_lookups(
            [
                {"barcode": "789", "m2CustomerCode": "cd"},
                {"barcode": "123", "m2CustomerCode": "ab"},
                {"barcode": "234", "m2CustomerCode": "ab"},
                {"barcode": "345", "m2CustomerCode": "ab"},
            ]
        )
        # Now only 1 of last 5 requests failed, so expect no error log:
        test_redis_client.logger.error.assert_not_called()
