import logging
import math

from aurora_server.lights import platform

is_a_raspberryPi = platform.platform_detect() == 1
logger = logging.getLogger('device')

if is_a_raspberryPi:
    import wiringpi
else:
    import aurora_server.lights.wiring_pi as wiringpi
    logger.info("Detected: Not running on a Raspberry Pi")

wiringpi.wiringPiSetup()


class Device(object):

    def __init__(self, name, channels):
        self.name = name
        self.enabled = False
        self.preset = {'type': 'none'}
        self.data = channels

        # Convenience Variables
        self.pins = []
        self.pin_types = []
        self.labels = []

        self.pwm_pins = []
        self.switch_pins = []

        dtypes = list()
        for ch in channels:
            if 'type' in ch:
                dtypes.append(ch.pop('type'))
            for label, value in ch.items():
                if value['type'] == 'pwm':
                    self.pwm_pins.append(int(value['pin']))
                    self.pin_types.append('pwm')
                elif value['type'] == 'switch':
                    self.switch_pins.append(int(value['pin']))
                    self.pin_types.append('switch')
                self.pins.append(int(value['pin']))
                self.labels.append(label)
        self.device_type = dtypes[0] if len(dtypes) == 1 else 'other'

    def enable(self):
        """Attempts to take hold of the gpio from wiring pi."""

        for pin in self.pwm_pins:
            wiringpi.softPwmCreate(pin, 0, 100)
        for pin in self.switch_pins:
            wiringpi.pinMode(pin, wiringpi.OUTPUT)
        self.enabled = True

    def disable(self):
        """Releases hold on gpio, so other programs can use it"""

        self.set_off()
        for pin in self.pwm_pins:
            wiringpi.softPwmStop(pin)
        for pin in self.pwm_pins:
            wiringpi.digitalWrite(pin, 0)
        self.enabled = False

    def set_off(self):
        for pin in self.pwm_pins:
            wiringpi.softPwmWrite(pin, 0)
        for pin in self.switch_pins:
            wiringpi.digitalWrite(pin, 0)

    def set_label_level(self, label, value):
        if label in self.labels and 0 <= value <= 100:
            indexes = [i for i, x in enumerate(self.labels) if x == label]
            for i in indexes:
                if self.pin_types[i] == 'pwm':
                    wiringpi.softPwmWrite(self.pins[i], value)
                elif self.pin_types[i] == 'switch':
                    wiringpi.digitalWrite(self.pins[i], round(value))
        else:
            logger.warning('Label ' + label + ' not registered in device ' + self.name + ".")

    def set_pin_level(self, pin_index, value):
        if math.isnan(value):
            value = 0.0
        if 0 <= pin_index <= len(self.pins):
            if self.pin_types[pin_index] == 'pwm':
                wiringpi.softPwmWrite(self.pins[pin_index], int(value * 100))
            elif self.pin_types[pin_index] == 'switch':
                wiringpi.digitalWrite(self.pins[pin_index], round(value))
