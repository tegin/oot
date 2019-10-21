import logging

from oot import Oot

_logger = logging.getLogger(__name__)


class Oddoor(Oot):
    template = "oddoor"
    oot_input = "call_lock"

    def access_granted(self, key, **kwargs):
        pass

    def access_rejected(self, key, **kwargs):
        pass

    def check_result(self, key, result, **kwargs):
        return result.get("access_granted", False)

    def process_result(self, key, result, **kwargs):
        if self.check_result(key, result, **kwargs):
            _logger.info("Access Granted for %s" % key)
            self.access_granted(key, **kwargs)
        else:
            _logger.info("Access rejected for %s" % key)
            self.access_rejected(key, **kwargs)
