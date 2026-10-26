"""
Script for fetching csv reports from an S3 bucket holding 2wks of M2 reports

Usage:
    python fetch_csv_reports.py [--type accessions] [--days 3]
"""
from botocore.exceptions import ClientError
import argparse
import boto3
import re


class FetchCsvReportsError(Exception):
    def __init__(self, message=None):
        self.message = message


class S3Client:
    def __init__(self, s3_client, **kwargs):
        """
        :param s3_client: A Boto3 S3 client for setup and cleanup operations.
        """
        self.s3_client = s3_client
        self.bucket_name = kwargs.get('bucket')

    def list_contents(self, filter_fn = lambda o: True):
        """
        Display a list of the objects in the bucket.

        :param bucket_name: The name of the bucket.
        """
        try:
            list_response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            objs = list_response.get("Contents", [])

            if not objs:
                return []

            files = [obj["Key"] for obj in objs if filter_fn(obj['Key'])]
            sorted(files)
            
            return files
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            issue = f'Error listing bucket "{self.bucket_name}": {error_code}'
            raise FetchCsvReportsError(issue)

    def download(self, key):
        path = f'/tmp/{key}'
        self.s3_client.download_file(self.bucket_name, key, path)
        return path


def fetch_reports(type='accessions', days=3):
    client = S3Client(boto3.client("s3"), bucket='m2-las-reports')

    # The `type` argument will determine type of report to process. For now, we're just handling accessions:
    p = re.compile('\\d{4}-\\d{2}-\\d{2}-accessions.txt')
    key_matches = lambda f: p.fullmatch(f)

    files = client.list_contents(key_matches)

    # Hard error of no matching reports found since that shouldn't ever happen:
    if len(files) == 0:
        raise FetchCsvReportsError("Received no matching files from bucket")

    download_paths = []
    for file in files[-days:]:
        download_paths.append(client.download(file))
    
    return download_paths


def parse_args():
    parser = argparse.ArgumentParser(
        description="Fetch M2 reports from S3"
    )
    parser.add_argument(
        "--type",
        metavar="TYPE",
        type=str,
        default="accessions",
        help="Type of report to retrieve"
    )
    parser.add_argument(
        "--days",
        metavar="N",
        action="store",
        type=int,
        default=3,
        help="Days of reports to retrieve"
    )
    args = parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    paths = fetch_reports(type=args.type, days=args.days)

    print(f'Downloaded to {paths}')
