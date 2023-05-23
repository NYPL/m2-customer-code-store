import argparse
import csv
import os
from redis_client import RedisClient

from nypl_py_utils.functions.config_helper import load_env_file, ConfigHelperError

parser = argparse.ArgumentParser(description='Write CSV to Redis')
parser.add_argument('csvpath', metavar='CSVPATH', type=str,
                    help='Path to the CSV')
parser.add_argument('--batchsize', metavar='N', action='store', type=int, default=1000,
                    help='Set batch size for commits. Default 1000')
parser.add_argument('--dryrun', action='store_true',
                    help='Enable dry-run mode (talk about things; don\'t do them')
args = parser.parse_args()


class CsvWriter:
    def __init__(self):
        if os.environ.get('ENVIRONMENT') is None:
            print('Set ENVIORNMENT=(qa|production) e.g.:')
            print('  ENVIRONMENT=qa python write_csv_to_redis.py CSVPATH')
            exit()

        try:
            load_env_file(os.environ.get('ENVIRONMENT'), 'config/{}.yaml')
            endpoint = os.environ['REDIS_ENDPOINT']
        except ConfigHelperError as e:
            print(f'error: {e}')
            print('error loading environment file: {}'.format(e))
        self.input_path = args.csvpath
        self.batch_size = args.batchsize

        print(f'Loading {self.input_path} with batch-size {self.batch_size}, writing to {endpoint}')
        if args.dryrun:
            print('Operating in dry-run mode')
        self.redis = RedisClient(endpoint)
        self.pipe = self.redis.pipeline()
        self.csv_length = self._get_csv_length()

    def _get_csv_length(self):
        with open(self.input_path, newline='') as in_file:
            csv_rows = self._csv_enumerator(in_file)
            return sum(1 for row in csv_rows)

    def _csv_enumerator(self, in_file):
        reader = csv.reader(in_file, delimiter=',')
        # Skip header:
        next(reader)
        return enumerate(reader)

    def upload_csv(self):
        """
        Reads CSV file, updating Redis for each barcode/customer-code pair found
        """
        with open(self.input_path, newline='') as in_file:
            csv_rows = self._csv_enumerator(in_file)
            for i, [barcode, date, customer_code, deleted] in csv_rows:
                key = 'm2-barcode-store-by-barcode-' + barcode

                # In dry-run mode, just print summary of writes:
                if args.dryrun:
                    if i <= 10:
                        print(f'  {barcode} => {customer_code}')
                    elif i == 11:
                        print(f'  ... and {self.csv_length - 10} more')
                    continue

                self.pipe.set(key, customer_code)
                if (i % self.batch_size == 0 or i == self.csv_length - 1):
                    self.pipe.execute()
                    print(f'  Updated {i}')

    def run(self):
        """
        Run the upload script and report on success.
        """
        before_count = self.redis.get_size()
        self.upload_csv()
        after_count = self.redis.get_size()

        print(f'Done. Updated {self.csv_length} barcodes.')
        print('Redis key/value pair counts:\n  Before: {}\n  After: {}\n  Added: {}'
              .format(before_count, after_count, after_count - before_count))


if __name__ == '__main__':
    CsvWriter().run()
