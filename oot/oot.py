import logging
import traceback
from io import StringIO
import os
from .server.server import initialize
import json
from .connection import OdooConnectionIot

_logger = logging.getLogger(__name__)

current_folder = os.path.dirname(os.path.realpath(__file__))


class Oot:
    connection_class = OdooConnectionIot
    oot_input = False
    template = False
    folder = current_folder
    form_template = "form.html"
    result_template = "result.html"
    ssid = "OotDevice"
    fields = {}
    connection = False
    connection_data = {}
    connection_path = False

    def __init__(self, connection):
        if isinstance(connection, OdooConnectionIot):
            self.connection = connection
        elif isinstance(connection, dict):
            self.connection_data = connection
            self.connection = self.connection_class(connection)
        elif isinstance(connection, str):
            self.connection_path = connection

    def initialize(self):
        initialize(self)

    def get_data(self, **kwargs):
        pass

    def process_result(self, key, result, **kwargs):
        pass

    def exit(self, **kwargs):
        pass

    def no_key(self, **kwargs):
        pass
        
    def checking_connection(self):
        pass
    
    def failure_connection(self):
        pass

    def finished_connection(self):
        pass

    def waiting_for_connection(self):
        pass

    def start_connection(self, server, access_point):
        pass

    def check_key(self, key, **kwargs):
        return self.connection.execute_action(
            key, oot_input=kwargs.get("oot_input", self.oot_input)
        )

    def run(self, **kwargs):
        if not self.connection:
            if not os.path.exists(self.connection_path):
                self.initialize()
            with open(self.connection_path, "r") as f:
                self.connection_data = json.loads(f.read())
            self.connection = self.connection_class(self.connection_data)
        try:
            while True:
                key_result = self.get_data(**kwargs)
                key = key_result
                key_vals = kwargs.copy()
                if isinstance(key, (list, tuple)):
                    key = key_result[0]
                    key_vals.update(key_result[1])
                if key:
                    result = self.check_key(key, **key_vals)
                    self.process_result(key, result, **key_vals)
                else:
                    self.no_key(**key_vals)
        except KeyboardInterrupt:
            _logger.info("Exiting process")
            self.exit(**kwargs)
        except Exception:
            buff = StringIO()
            traceback.print_exc(file=buff)
            _logger.error(buff.getvalue())
            _logger.info("Exiting process after error")
            self.exit(**kwargs)
            raise
