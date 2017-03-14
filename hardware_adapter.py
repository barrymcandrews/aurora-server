import math
import Platform
from log import setup_logger

PINS = [5, 0, 3]
RED_PIN = PINS[0]
GREEN_PIN = PINS[1]
BLUE_PIN = PINS[2]

is_a_raspberryPi = Platform.platform_detect() == 1
is_gpio_enabled = False
logger = setup_logger("Hardware Adapter")

if is_a_raspberryPi:
    import wiringpi
else:
    # if this is not a RPi you can't run wiringpi so lets load
    # something in its place
    import wiring_pi as wiringpi
    logger.info("Detected: Not running on a Raspberry Pi")

wiringpi.wiringPiSetup()


def enable_gpio():
    global is_gpio_enabled
    """Attempts to take hold of the gpio from wiring pi."""

    wiringpi.softPwmCreate(RED_PIN, 0, 100)
    wiringpi.softPwmCreate(GREEN_PIN, 0, 100)
    wiringpi.softPwmCreate(BLUE_PIN, 0, 100)
    is_gpio_enabled = True


def disable_gpio():
    global is_gpio_enabled
    """Releases hold on gpio, so other programs can use it"""

    wiringpi.softPwmStop(RED_PIN)
    wiringpi.softPwmStop(GREEN_PIN)
    wiringpi.softPwmStop(BLUE_PIN)
    is_gpio_enabled = False


# High Level GPIO Functions

def set_pin_level(pin, value):
    if math.isnan(value):
        value = 0.0

    if 0 <= pin <= 2:
        wiringpi.softPwmWrite(PINS[pin], int(value * 100))


def set_color(color):
    if is_gpio_enabled:
        if 0 <= color['red'] < 100:
            wiringpi.softPwmWrite(RED_PIN, color['red'])
        if 0 <= color['green'] < 100:
            wiringpi.softPwmWrite(GREEN_PIN, color['green'])
        if 0 <= color['blue'] < 100:
            wiringpi.softPwmWrite(BLUE_PIN, color['blue'])
        logger.info('Color: ' + color['red'] + ' ' + color['green'] + ' ' + color['blue'])
    else:
        logger.error('Can not write to GPIO because it is not enabled.')


def set_fade(fade):
    pass


def set_sequence(sequence):
    pass
