from oot import OotAmqp, api, Field
import os
import logging
import time

_logger = logging.getLogger(__name__)


class FileReader:
    def __init__(self, file_path, delay=15):
        self.file_path = file_path
        self.delay = delay

    def scan(self):
        while True:
            if not os.path.exists(self.file_path):
                time.sleep(0.1)
                continue
            if os.path.getmtime(self.file_path) > time.time() - self.delay:
                time.sleep(0.1)
                continue
            with open(self.file_path, "r") as f:
                data = f.read()
            os.remove(self.file_path)
            return data


class DemoOot(OotAmqp):
    """We are using AMQP as it allows to define some extra configuration"""
    template = "demo_template"
    # Template to be used on odoo
    oot_input = "demo_input"
    _ignore_access_point = True
    # Input to be used on odoo

    # Now we define the configuration fields
    admin_id = Field(name="Admin key", required=True)

    def __init__(self, connection, file_path):
        super(DemoOot, self).__init__(connection)
        self.reader = FileReader(file_path)

    @api.oot
    def get_data_mfrc522(self, **kwargs):
        """We will return the card if a card is readed. Otherwise, we will wait"""
        time.sleep(5.0)
        while True:
            uid = self.reader.scan()
            if uid:
                _logger.info("Sending %s" % uid)
                return uid

    def process_result(self, key, result, **kwargs):
        _logger.info("For %s, we received the following result: %s" % (key, result))
        return super(DemoOot, self).process_result(key, result, **kwargs)
