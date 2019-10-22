import logging.config
import os

import psutil

from cb.cb_amqp import AmqpOot

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
AmqpOot(data_folder + "/data.json").run()
