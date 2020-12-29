import json
import logging
import os
import subprocess
import traceback
from inspect import getmembers
from io import StringIO

from .connection import OdooConnectionIot
from .fields import Field
from .server.server import initialize

_logger = logging.getLogger(__name__)

current_folder = os.path.dirname(os.path.realpath(__file__))


class Oot:
    """Base class for Oot definition

    It will instantiate an Access Point if it does not find a configuration.
    In it we will be able to define all the necessary information and configure it.

    Otherwise, it will be used to send information to a Odoo System
    """
    connection_class = OdooConnectionIot
    oot_input = False
    template = False
    folder = current_folder
    form_template = "form.html"
    extra_tools_template = "extra_tools.html"
    result_template = "result.html"
    ssid = "OotDevice"
    _ignore_access_point = False

    fields = {}
    connection = False
    connection_data = {}
    connection_path = False

    def extra_tools(self):
        return {
            "ssh": {
                "name": ("Disable" if self.check_service("ssh") else "Enable") + " SSH",
                "function": self.toggle_service_function("ssh"),
            },
            "reboot": {"name": "Reboot", "function": self.reboot},
        }

    def __init__(self, connection):
        self._fields = {}
        for clss in self.__class__.mro():
            if Oot in clss.mro():
                for key in clss.fields:
                    if key not in self._fields:
                        self._fields[key] = clss.fields[key]

        def is_field(item):
            return not callable(item) and isinstance(item, Field)

        cls = type(self)
        for attr, item in getmembers(cls, is_field):
            self._fields[attr] = item.generate()
        if isinstance(connection, dict):
            self.connection_data = connection
            self.generate_connection()
        elif isinstance(connection, str):
            self.connection_path = connection

    def initialize(self):
        initialize(self, no_access_point=self._ignore_access_point)

    def get_data(self, **kwargs):
        """This is intended to be overridden by each configuration.
        It must return the data for odoo.
        If a tuple is returned, it will send the first value and use the second one
        as extra arguments, so it must be a dictionary
        """
        pass

    def process_result(self, key, result, **kwargs):
        """To be executed after sending the information to odoo.
        This is the function that checks that the response is valid.

        :param key: The sent value to odoo
        :param result: Result from odoo. Usually a dict
        """
        pass

    def exit(self, **kwargs):
        """Executed when exiting the loop"""
        pass

    def no_key(self, **kwargs):
        """Executed if `get_data` returns no value"""
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
        """Checks the result from the Oot to Odoo"""
        return self.connection.execute_action(
            key, oot_input=kwargs.get("oot_input", self.oot_input)
        )

    def generate_connection(self):
        """Initializes the connection configuraton to odoo"""
        self.connection = self.connection_class(self.connection_data)
        for field in self._fields:
            setattr(self, field, self.connection_data.get(field))
        self.name = self.connection_data.get("name")

    def run(self, **kwargs):
        """Loop to execute"""
        if not self.connection and self.connection_path:
            if not os.path.exists(self.connection_path):
                self.initialize()
            with open(self.connection_path, "r") as f:
                self.connection_data = json.loads(f.read())
        if not self.connection:
            self.generate_connection()
            _logger.info("Connection has been initialized successfully")
        self._run(**kwargs)

    def _run(self, **kwargs):
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

    def _check_service(self, service, **kwargs):
        """Checks if a service is active. Only works on debian"""
        stat = subprocess.Popen(
            "systemctl is-active --quiet %s; echo $?" % service,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
        ).communicate()
        return stat[0] == b"0\n"

    def toggle_service_function(self, service, **kwargs):
        """Returns the function that changes the state of a service"""
        def toggle(**kwtargs):
            return self._toggle_service(service, **kwtargs)

        return toggle

    def _toggle_service(self, service, **kwargs):
        if self._check_service(service):
            self._stop_service(service)
        else:
            self._start_service(service)

    def _stop_service(self, service, disable=True, **kwargs):
        subprocess.Popen(["systemctl", "stop", service]).communicate()
        if disable:
            subprocess.Popen(["systemctl", "disable", service]).communicate()

    def _start_service(self, service, enable=True, **kwargs):
        subprocess.Popen(["systemctl", "enable", service]).communicate()
        if enable:
            subprocess.Popen(["systemctl", "start", service]).communicate()

    def reboot(self, **kwargs):
        subprocess.Popen(["reboot"])
