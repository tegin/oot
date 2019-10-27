import json
import logging

import requests

from .odoo_connection import OdooConnection

_logger = logging.getLogger(__name__)


class OdooConnectionIot(OdooConnection):
    def set_params(self):
        self.url = self.j_data["host"]

    def execute_action(self, key, oot_input="", **kwargs):
        try:
            input_vals = self.j_data["inputs"][oot_input]
            request = requests.post(
                "{}/iot/{}/action".format(self.url, input_vals["serial"]),
                data={"passphrase": input_vals["passphrase"], "value": key},
            )
            request.raise_for_status()
            result = json.loads(request.content.decode("utf-8"))
            if result.get("status", "ko") == "ok":
                return result
        except Exception as e:
            _logger.exception(e)
        return False
