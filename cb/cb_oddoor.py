import logging
import os
import time

import psutil
import RPi.GPIO as GPIO
from evdev import InputDevice, categorize, ecodes

from oddoor import Oddoor
from oot import OotMultiProcessing

dev = InputDevice("/dev/input/event0")
_logger = logging.getLogger(__name__)

RELAY = 15
volume = 99
duration = 0.1
hz = 440
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(RELAY, GPIO.OUT)
GPIO.output(RELAY, GPIO.LOW)

scancodes = {
    # Scancode: ASCIICode
    0: None,
    1: u"ESC",
    2: u"1",
    3: u"2",
    4: u"3",
    5: u"4",
    6: u"5",
    7: u"6",
    8: u"7",
    9: u"8",
    10: u"9",
    11: u"0",
    12: u"-",
    13: u"=",
    14: u"BKSP",
    15: u"TAB",
    16: u"q",
    17: u"w",
    18: u"e",
    19: u"r",
    20: u"t",
    21: u"y",
    22: u"u",
    23: u"i",
    24: u"o",
    25: u"p",
    26: u"[",
    27: u"]",
    28: u"CRLF",
    29: u"LCTRL",
    30: u"a",
    31: u"s",
    32: u"d",
    33: u"f",
    34: u"g",
    35: u"h",
    36: u"j",
    37: u"k",
    38: u"l",
    39: u";",
    40: u'"',
    41: u"`",
    42: u"LSHFT",
    43: u"\\",
    44: u"z",
    45: u"x",
    46: u"c",
    47: u"v",
    48: u"b",
    49: u"n",
    50: u"m",
    51: u",",
    52: u".",
    53: u"/",
    54: u"RSHFT",
    56: u"LALT",
    57: u" ",
    100: u"RALT",
}

capscodes = {
    0: None,
    1: u"ESC",
    2: u"!",
    3: u"@",
    4: u"#",
    5: u"$",
    6: u"%",
    7: u"^",
    8: u"&",
    9: u"*",
    10: u"(",
    11: u")",
    12: u"_",
    13: u"+",
    14: u"BKSP",
    15: u"TAB",
    16: u"Q",
    17: u"W",
    18: u"E",
    19: u"R",
    20: u"T",
    21: u"Y",
    22: u"U",
    23: u"I",
    24: u"O",
    25: u"P",
    26: u"{",
    27: u"}",
    28: u"CRLF",
    29: u"LCTRL",
    30: u"A",
    31: u"S",
    32: u"D",
    33: u"F",
    34: u"G",
    35: u"H",
    36: u"J",
    37: u"K",
    38: u"L",
    39: u":",
    40: u"'",
    41: u"~",
    42: u"LSHFT",
    43: u"|",
    44: u"Z",
    45: u"X",
    46: u"C",
    47: u"V",
    48: u"B",
    49: u"N",
    50: u"M",
    51: u"<",
    52: u">",
    53: u"?",
    54: u"RSHFT",
    56: u"LALT",
    57: u" ",
    100: u"RALT",
}
dev.grab()


def get_data_scanner(**kwargs):
    result = ""
    caps = False
    for event in dev.read_loop():
        if event.type == ecodes.EV_KEY:
            data = categorize(event)
            if data.scancode == 42:
                if data.keystate == 1:
                    caps = True
                if data.keystate == 0:
                    caps = False
            if data.keystate == 1:
                if caps:
                    key_lookup = u"{}".format(
                        capscodes.get(data.scancode)
                    ) or u"UNKNOWN:[{}]".format(data.scancode)
                else:
                    key_lookup = u"{}".format(
                        scancodes.get(data.scancode)
                    ) or u"UNKNOWN:[{}]".format(data.scancode)
                if data.scancode not in [42, 28]:
                    result += key_lookup
                if data.scancode == 28:
                    _logger.info(result)
                    return result


def get_data_mfrc522(reader, **kwargs):
    time.sleep(5.0)
    while True:
        uid = reader.scan_card()
        if uid:
            return uid


def get_data_keypad(keypad, buzzer, **kwargs):
    time.sleep(1)
    text = ""
    pressed = False
    while True:
        key = keypad.getKey()
        if not key:
            pressed = False
        elif pressed:
            pass
        elif key == "#":
            if len(text) > 0:
                return text, {"force_key": True}
            buzzer.play([(volume, hz * 2, duration)])
        elif key == "*":
            text = ""
            buzzer.play([(volume, hz * 2, duration)])
        else:
            text += key
            buzzer.play([(volume, hz, duration)])
            pressed = True
        time.sleep(0.1)


class OddoorCB(OotMultiProcessing, Oddoor):
    fields = {
        "force_key": {
            "name": "Static Key for Key Board",
            "placeHolder": "Key that must be a number",
        }
    }

    def __init__(self, connection, rdr, keypad, buzzer):
        super().__init__(connection)
        self.reader = rdr
        self.keypad = keypad
        self.buzzer = buzzer
        self.functions = [
            [get_data_scanner],
            [get_data_mfrc522, self.reader],
            [get_data_keypad, self.keypad, self.buzzer],
        ]

    @staticmethod
    def start_execute_function(function, *args, queue=False, **kwargs):
        p = psutil.Process(os.getpid())
        # set to lowest priority, this is windows only, on Unix use ps.nice(19)
        p.nice(6)

    def no_key(self, **kwargs):
        time.sleep(0.5)

    def check_key(self, key, **kwargs):
        if kwargs.get("force_key", False):
            return {
                "access_granted": key == self.connection_data.get("force_key", False)
            }
        return super().check_key(key, **kwargs)

    def access_granted(self, key, **kwargs):
        GPIO.output(RELAY, GPIO.HIGH)
        self.buzzer.play([(volume, hz, duration), (volume, hz * 1.28, duration)])
        time.sleep(1)
        GPIO.output(RELAY, GPIO.LOW)

    def access_rejected(self, key, **kwargs):
        self.buzzer.play([(volume, hz * 1.26, duration), (volume, hz, duration)])
        time.sleep(1)

    def exit(self, **kwargs):
        self.keypad.exit()
        GPIO.cleanup()
