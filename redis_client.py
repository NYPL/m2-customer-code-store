import os
from redis import StrictRedis
from nypl_py_utils.functions.log_helper import create_log


class RedisClient:
    KEY_PREFIX = "m2-barcode-store-by-barcode-"

    def __init__(self, endpoint):
        self.host = endpoint
        self.logger = create_log("redis_client", json=True)
        self.client = self._connect()

        self._last_n_lookups = []

    def _connect(self):
        try:
            client = StrictRedis(host=self.host, decode_responses=True)
            client.ping()
        except ConnectionError as e:
            self.logger.error("Error connecting to redis at endpoint: " + self.host)
            raise RedisClientError(f"Connected to redis at: {self.host}".format(e))
        self.logger.info("Connected to redis at:" + self.host)
        return client

    def pipeline(self):
        return self.client.pipeline()

    def get_size(self):
        return self.client.dbsize()

    def _remove_prefix(self, barcode):
        return barcode.replace("m2-barcode-store-by-barcode-", "")

    def barcodes_with_customer_codes(self, barcodes):
        barcodes_length = len(barcodes) if barcodes is not None else 0

        barcodes_with_prefix = [self.KEY_PREFIX + barcode for barcode in barcodes]
        customer_codes = self.client.mget(barcodes_with_prefix)

        return [
            {"barcode": barcodes[i], "m2CustomerCode": customer_codes[i]}
            for i in range(barcodes_length)
        ]

    def get_customer_codes(self, barcodes):
        if barcodes is None or len(barcodes) == 0:
            raise RedisClientError("No barcode supplied")

        pairs = self.barcodes_with_customer_codes(barcodes)

        found = [pair for pair in pairs if pair["m2CustomerCode"] is not None]
        if len(found) == 0:
            raise RedisClientError(
                f'Customer codes not found for barcodes: {", ".join(barcodes)}'
            )

        failed = [pair["barcode"] for pair in pairs if pair["m2CustomerCode"] is None]
        if len(failed) > 0:
            self.logger.debug(
                "Barcodes {} returned no customer codes".format(", ".join(failed))
            )

        self.monitor_failed_lookups(pairs)

        return pairs

    def monitor_failed_lookups(self, pairs):
        """
        Given a recently fetched set of cc/barcode pairs,
        updates a running queue of the most recently executed lookups
        to analyze the lookup success/failure rate as an indicator of
        a deeper issue with missing data.
        """

        max_lookups = 100
        try:
            max_lookups = int(os.environ.get("MONITOR_LOOKUPS_COUNT", "100"))
        except:
            self.logger.error(
                f"Failure to parse MONITOR_FAILURE_RATE: {os.environ['MONITOR_FAILURE_RATE']}"
            )

        self._last_n_lookups = pairs + self._last_n_lookups

        if len(self._last_n_lookups) > max_lookups:
            self._last_n_lookups = self._last_n_lookups[0:max_lookups]

        monitor_failure_rate = 0.1
        try:
            monitor_failure_rate = float(os.environ.get("MONITOR_FAILURE_RATE", "0.10"))
        except:
            self.logger.error(
                f"Failure to parse MONITOR_FAILURE_RATE: {os.environ['MONITOR_FAILURE_RATE']}"
            )

        failed = len(
            [pair for pair in self._last_n_lookups if pair["m2CustomerCode"] is None]
        )
        requested = len(self._last_n_lookups)
        failure_rate = failed / requested

        # If we've collected enough samples and failure rate exceeds threshold, log error:
        sufficient_data = requested >= min(max_lookups, 10)
        if sufficient_data and failure_rate > monitor_failure_rate:
            self.logger.error(
                f'Lookup failure rate is {"{:2.1f}".format(failure_rate * 100)}%'
            )

    def _danger_delete(self, *, pattern="", key=""):
        if len(pattern) > 0:
            for key in self.client.scan_iter(pattern):
                self.client.delete(key)
        if len(key) > 0:
            self.client.delete("key")


class RedisClientError(Exception):
    def __init__(self, message=None):
        self.message = message
