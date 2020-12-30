import os
import logging.config
from ootdemo import DemoOot

path = os.path.dirname(os.path.realpath(__file__))

log_folder = path + "/log"

if not os.path.isdir(log_folder):
    os.mkdir(log_folder)

logging.config.fileConfig(path + "/logging.conf")

data_folder = path + "/data"

if not os.path.isdir(data_folder):
    os.mkdir(data_folder)

DemoOot(data_folder + "/data.json", data_folder + "/read").run()
