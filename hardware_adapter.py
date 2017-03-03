import tkinter
import Platform
import logging

RED_PIN = 5
GREEN_PIN = 0
BLUE_PIN = 3

is_a_raspberryPI = Platform.platform_detect() == 1
is_gpio_enabled = False

if is_a_raspberryPI:
    import wiringpi
else:
    # if this is not a RPi you can't run wiringpi so lets load
    # something in its place
    import wiring_pi as wiringpi
    logging.debug("Detected: Not running on a Raspberry Pi")

wiringpi.wiringPiSetup()


def enable_gpio():
    """Attempts to take hold of the gpio from wiring pi."""

    wiringpi.softPwmCreate(RED_PIN, 0, 100)
    wiringpi.softPwmCreate(GREEN_PIN, 0, 100)
    wiringpi.softPwmCreate(BLUE_PIN, 0, 100)
    is_gpio_enabled = True


def disable_gpio():
    """Releases hold on gpio, so other programs can use it"""

    wiringpi.softPwmStop(RED_PIN)
    wiringpi.softPwmStop(GREEN_PIN)
    wiringpi.softPwmStop(BLUE_PIN)
    is_gpio_enabled = False


# High Level GPIO Functions


def set_color(color):
    pass


def set_fade(fade):
    pass


def set_sequence(sequence):
    pass
