import csv
from redis_client import RedisClient
import sys


class CsvWriter:
    def __init__(self, batch_size=1000):
        self.input_path = sys.argv[1]
        self.batch_size = int(sys.argv[2])
        if not isinstance(self.batch_size, int):
            self.batch_size = batch_size
        self.redis = RedisClient()
        self.pipe = self.redis.pipeline()
        self.csv_length = self._get_csv_length()

    def _get_csv_length(self):
        with open(self.input_path, newline='') as in_file:
            return sum(1 for line in in_file)

    def create_reader(self):
        with open(self.input_path, newline='') as in_file:
            reader = csv.reader(in_file, delimiter=',')
            csv_iterator = enumerate(reader)
            for i, [barcode, date, customer_code, deleted] in csv_iterator:
                self.pipe.set('m2-barcode-store-by-barcode-'+barcode, customer_code)
                if (i % self.batch_size == 0 or i == self.csv_length - 1):
                    print('exectuting ', i)
                    self.pipe.execute()

    def the_thing(self):
        self.create_reader()
        self.redis.get_em()
