import time

from RPi import GPIO


class Buzzer:
    def __init__(self, power_pin, device_pin):
        self.power_pin = power_pin
        self.device_pin = device_pin
        self.buzz = False

    def play(self, msg):
        self._init_buzz()
        data = msg
        while data:
            self._play_buzz(*data[0])
            data = data[1:]
        self._reset_buzz()
        return True

    def _play_buzz(self, duty, frequency, buzz_time):
        GPIO.output(self.power_pin, 1)

        self.buzz.ChangeDutyCycle(duty)  # Duty goes from 0 to 99(% of PWM)
        # Duty regulates thevolume
        self.buzz.ChangeFrequency(frequency)  # Frequency of the note
        # 440Hz is A4 for example
        time.sleep(buzz_time)  # Duration of the note in seconds
        GPIO.output(self.power_pin, 0)

    def _init_buzz(self):
        GPIO.setup(self.power_pin, GPIO.OUT)  # set pin as output
        GPIO.setup(self.device_pin, GPIO.OUT)  # set pin as output
        self.buzz = GPIO.PWM(self.device_pin, 5)  # initial frequency.
        self.buzz.start(99)  # initial duty rate

    def _reset_buzz(self):
        self.buzz.stop()
        GPIO.output(self.power_pin, 0)
        GPIO.output(self.device_pin, 0)
