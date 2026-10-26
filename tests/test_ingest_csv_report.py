import pytest
import os
import json
# from botocore.stub import Stubber
from unittest.mock import patch, mock_open

from ingest_csv_report import ingest_csv


class TestIngestCsvReport:
    @pytest.fixture
    def redis_client(self, mocker):
        client = mocker.MagicMock()
        mocker.patch("ingest_csv_report.RedisClient", return_value=client)
        return client

    @pytest.fixture(autouse=True)
    def setenvvar(monkeypatch):
        with patch.dict(os.environ, clear=True):
            os.environ['REDIS_ENDPOINT'] = 'https://example.com:123'
            yield

    def test_ingest_csv(self, redis_client, mocker):

        csv_path = '/tmp/foo.txt'
        mock_data = '\n'.join([
            'barcode,date,customer_code,deleted',
            "123,2026-10-22,NA,false",
            "456,2026-10-22,NF,false"
        ])

        with patch("builtins.open", mock_open(read_data=mock_data)) as mock_file:
            assert open(csv_path).read() == mock_data
        
            mock_pipeline = mocker.MagicMock()
            redis_client.pipeline.return_value = mock_pipeline

            ingest_csv(csv_path)
            mock_file.assert_called_with(csv_path, newline='')

            # Expect one batched call:
            mock_pipeline.execute.assert_called_once()
