from logging import Logger, getLogger
from typing import Dict, List

from aurora_server.lights import platform
from aurora_server.log import setup_logger

is_a_raspberryPi = platform.platform_detect() == 1
log: Logger = setup_logger('pins')

if is_a_raspberryPi:
    import wiringpi
else:
    from aurora_server.lights import wiring_pi as wiringpi
    log.warning("Detected: Not running on a Raspberry Pi")

wiringpi.wiringPiSetup()

pins: List[int] = []


def enable(pins_list: List[int]):
    global pins
    pins = pins_list

    log.info("Enabling Pins: " + str(pins_list))
    for pin in pins:
        wiringpi.softPwmCreate(pin, 0, 100)


def disable():
    global pins

    for pin in pins:
        wiringpi.softPwmWrite(pin, 0)
        wiringpi.softPwmStop(pin)


def set_pwm(pin: int, level: int):
    global pins

    if pin in pins and 0 <= level <= 100:
        wiringpi.softPwmWrite(pin, level)
    else:
        log.error('Cannot write level %d to pin %s' % (level, pin))


class Device(object):

    def __init__(self, name: str, mapping: Dict[int, str]):
        self.name: str = name
        self.pins: List[int] = list(mapping.keys())
        self.pin_mapping: Dict[int, str] = mapping

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.name == other.name
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def conflicts_with(self, device):
        for pin in self.pins:
            if pin in device.pins:
                return True
        return False

    def set_pin_at_index(self, index: int, level: int):
        if 0 <= index <= len(self.pins):
            set_pwm(self.pins[index], level)

    def set_pins_with_label(self, label: str, level: int):
        for pin, p_label in self.pin_mapping.items():
            if label == p_label:
                set_pwm(pin, level)
