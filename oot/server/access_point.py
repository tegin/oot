from PyAccessPoint import pyaccesspoint
import logging
_logger = logging.getLogger(__name__)

config = '''
interface={1}
driver=nl80211
ssid={0}
hw_mode=g
channel=6
macaddr_acl=0
ignore_broadcast_ssid=0
auth_algs=1
'''


class OotAccessPoint(pyaccesspoint.AccessPoint):
    def _write_hostapd_config(self):
        with open(self.hostapd_config_path, 'w') as hostapd_config_file:
            hostapd_config_file.write(config.format(self.ssid, self.wlan))
        _logger.debug("Hostapd config saved to %s", self.hostapd_config_path)
