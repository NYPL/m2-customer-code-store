import csv
from redis_client import RedisClient

class CsvWriter:
    def __init__(self, input_path, output_path, batch_size):
        self.input_path = input_path
        self.output_path = output_path
        self.file_reader_object = None
        self.batch_size = batch_size
        self.redis = RedisClient()

    def create_reader(self):
        with open(self.input_path, newline = '', ) as in_file:
            self.file_reader_object = csv.reader(in_file, delimiter=',')
    
    def consume_reader(self):
        pipe = self.redis.pipeline()
        for i, key, value in enumerate(self.file_reader_object):
            if i % self.batch_size == 0:
                pipe.execute()
            else:
                pipe.set(key, value)

    
    def the_thing(self):
        self.collect_key_value_pairs() 
        self.write_redis_commands()

x = CsvWriter('test.csv', 'bulk_load.csv')
x.the_thing()

# create reader
# consume reader