"""
Script for ingesting a report CSV (presumably an accessions report) from M2

Usage:
    python ingest_csv_report.py PATHTOCSV [--batchsize 1000]
"""
import argparse
import csv
import os
from redis_client import RedisClient

from nypl_py_utils.functions.config_helper import load_env_file, ConfigHelperError


class CsvIngester:
    def __init__(self, csv_path, **kwargs):
        self.csv_path = csv_path
        self.batch_size = kwargs.get('batchsize', 1000)

        endpoint = os.environ["REDIS_ENDPOINT"]
        self.redis = RedisClient(endpoint)
        self.pipe = self.redis.pipeline()
        self.csv_length = self._get_csv_length()

    def _get_csv_length(self):
        with open(self.csv_path, newline="") as in_file:
            csv_rows = self._csv_enumerator(in_file)
            return sum(1 for row in csv_rows)

    def _csv_enumerator(self, in_file):
        reader = csv.reader(in_file, delimiter=",")
        # Skip header:
        next(reader)
        return enumerate(reader)

    def current_count(self):
        return self.redis.get_size()

    def ingest(self, **kwargs):
        """
        Reads CSV file, updating Redis for each barcode/customer-code pair found
        """
        dryrun = kwargs.get('dryrun', False)

        if dryrun:
            print('DRYRUN')

        with open(self.csv_path, newline="") as in_file:
            csv_rows = self._csv_enumerator(in_file)
            for i, [barcode, date, customer_code, deleted] in csv_rows:
                key = RedisClient.KEY_PREFIX + barcode

                # In dry-run mode, just print summary of writes:
                if dryrun:
                    if i <= 10:
                        print(f"  {barcode} => {customer_code}")
                    elif i == 11:
                        print(f"  ... and {self.csv_length - 10} more")
                    continue

                self.pipe.set(key, customer_code)

                row_num = i + 1
                if row_num % self.batch_size == 0 or row_num == self.csv_length:
                    self.pipe.execute()
                    print(f"  Updated {row_num}")


def init():
    if os.environ.get("ENVIRONMENT") is None:
        print("Set ENVIORNMENT=(qa|production) e.g.:")
        print("  ENVIRONMENT=qa python write_csv_to_redis.py CSVPATH")
        exit()

    try:
        load_env_file(os.environ.get("ENVIRONMENT"), "config/{}.yaml")
    except ConfigHelperError as e:
        print(f"error: {e}")
        print("error loading environment file: {}".format(e))


def ingest_csv(path, **kwargs):
    ingester = CsvIngester(path, batchsize=kwargs.get('batchsize', 1000))

    # Capture starting and ending key counts
    starting_count = ingester.current_count()
    ingester.ingest(**kwargs)
    ending_count = ingester.current_count()

    csv_length = ingester.csv_length
    added = ending_count - starting_count

    # Return numbers representing additions & totals
    return (added, csv_length, ending_count)

def parse_args():
    parser = argparse.ArgumentParser(description="Write CSV to Redis")
    parser.add_argument("csvpath", metavar="CSVPATH", type=str, help="Path to the CSV")
    parser.add_argument(
        "--batchsize",
        metavar="N",
        action="store",
        type=int,
        default=1000,
        help="Set batch size for commits. Default 1000",
    )
    parser.add_argument(
        "--dryrun",
        action="store_true",
        help="Enable dry-run mode (talk about things; don't do them",
    )
    args = parser.parse_args()

    return args


if __name__ == "__main__":
    init()
    args = parse_args()

    print(
        f"Loading {args.csvpath} with batch-size {args.batchsize}"
    )
    added, csv_size = ingest_csv(args.csvpath, batchsize=args.batchsize, dryrun=args.dryrun)

    print(f'Done. Ingested {csv_size} line CSV. Added {added} entries')
