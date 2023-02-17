import csv
from redis_client import RedisClient

class CsvWriter:
    def __init__(self, input_path, batch_size = 100):
        self.input_path = input_path
        self.batch_size = batch_size
        self.redis = RedisClient()
        self.pipe = self.redis.pipeline()
        self.csv_length = self._get_csv_length()

    def _get_csv_length(self):
        with open(self.input_path, newline = '') as in_file:
            return sum(1 for line in in_file)

    def create_reader(self):
        with open(self.input_path, newline = '') as in_file:
            reader = csv.reader(in_file, delimiter=',')
            csv_iterator = enumerate(reader)
            for i, [key, value] in csv_iterator:
                self.pipe.set(key, value)
                if(i % self.batch_size == 0 or i == self.csv_length - 1):
                    self.pipe.execute()

    def the_thing(self):
        self.create_reader()
        self.redis.get_em()

x = CsvWriter('test.csv')
x.the_thing()

