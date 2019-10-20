from PyAccessPoint import pyaccesspoint
import logging
_logger = logging.getLogger(__name__)

config = '''
#sets the wifi interface to use, is wlan0 in most cases
interface={1}
#driver to use, nl80211 works in most cases
driver=nl80211
#sets the ssid of the virtual wifi access point
ssid={0}
#sets the mode of wifi, depends upon the devices you will be using. It can be a,b,g,n. Setting to g ensures backward compatiblity.
hw_mode=g
#sets the channel for your wifi
channel=6
#macaddr_acl sets options for mac address filtering. 0 means "accept unless in deny list"
macaddr_acl=0
#setting ignore_broadcast_ssid to 1 will disable the broadcasting of ssid
ignore_broadcast_ssid=0
#Sets authentication algorithm
#1 - only open system authentication
#2 - both open system authentication and shared key authentication
auth_algs=1
#sets encryption used by WPA2
rsn_pairwise=CCMP
'''


class OotAccessPoint(pyaccesspoint.AccessPoint):
    def _write_hostapd_config(self):
        with open(self.hostapd_config_path, 'w') as hostapd_config_file:
            hostapd_config_file.write(config.format(self.ssid, self.wlan))
        _logger.debug("Hostapd config saved to %s", self.hostapd_config_path)
