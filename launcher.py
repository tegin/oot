import logging.config
import os

from cb.cb_oddoor import OddoorCB
from oot.device import Buzzer, CardReader, KeyPad

log_folder = os.getcwd() + "/log"

if not os.path.isdir(log_folder):
    os.mkdir(log_folder)

logging.config.fileConfig("oddoor.logging.conf")

_logger = logging.getLogger(__name__)

data_folder = os.getcwd() + "/data"

if not os.path.isdir(data_folder):
    os.mkdir(data_folder)

OddoorCB(data_folder + "/data_iot.json", CardReader(), KeyPad(), Buzzer(7, 13)).run()
