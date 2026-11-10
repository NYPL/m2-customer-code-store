import pytest
import os
import json
# from botocore.stub import Stubber
from unittest.mock import patch

from fetch_csv_reports import fetch_reports


class TestFetchCsvReports:
    @pytest.fixture
    def s3_client(self, mocker):
        client = mocker.MagicMock()
        mocker.patch("fetch_csv_reports.boto3.client", return_value=client)
        return client

    def test_fetch_reports_raises_error_if_none_found(self, s3_client):
        s3_client.list_objects_v2.return_value = {
            'Contents': []
        }

        resp = s3_client.list_objects_v2()

        with pytest.raises(Exception):
            fetch_reports()

    def test_fetch_reports_retrieves_valid_report(self, s3_client):
        s3_client.list_objects_v2.return_value = {
            'Contents': [
                { "Key": "2026-10-22-accessions.txt" }
            ]
        }

        resp = s3_client.list_objects_v2()

        assert fetch_reports() == ['/tmp/2026-10-22-accessions.txt']

    def test_fetch_reports_discards_invalid_report(self, s3_client):
        s3_client.list_objects_v2.return_value = {
            'Contents': [
                { "Key": "2026-10-22-accessions.txt" },
                { "Key": "2026-10-22-accessionZ.txt" }
            ]
        }

        resp = s3_client.list_objects_v2()

        assert fetch_reports() == ['/tmp/2026-10-22-accessions.txt']

