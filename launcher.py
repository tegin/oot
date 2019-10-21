import logging.config
import os

import psutil

from cb.cb_oddoor import OddoorCB
from oot.device import Buzzer, CardReader, KeyPad

p = psutil.Process(os.getpid())
p.nice(6)  # give the launcher process a low priority


path = os.path.dirname(os.path.realpath(__file__))

log_folder = path + "/log"

if not os.path.isdir(log_folder):
    os.mkdir(log_folder)

logging.config.fileConfig(path + "/oddoor.logging.conf")

data_folder = path + "/data"

if not os.path.isdir(data_folder):
    os.mkdir(data_folder)
OddoorCB(
    data_folder + "/data.json", CardReader(spd=200), KeyPad(), Buzzer(7, 13)
).run()
