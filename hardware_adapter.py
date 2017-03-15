import math
import Platform
from log import setup_logger
from time import sleep

PINS = [0, 5, 3]
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
def set_off():
    if is_gpio_enabled:
        wiringpi.softPwmWrite(RED_PIN, 0)
        wiringpi.softPwmWrite(GREEN_PIN, 0)
        wiringpi.softPwmWrite(BLUE_PIN, 0)


def set_pin_level(pin, value):
    if math.isnan(value):
        value = 0.0

    if 0 <= pin <= 2:
        wiringpi.softPwmWrite(PINS[pin], int(value * 100))


def set_rgb(red, green, blue):
    if is_gpio_enabled:
        if 0 <= red < 100:
            wiringpi.softPwmWrite(RED_PIN, red)
        if 0 <= green < 100:
            wiringpi.softPwmWrite(GREEN_PIN, green)
        if 0 <= blue < 100:
            wiringpi.softPwmWrite(BLUE_PIN, blue)
    else:
        logger.error('Can not write to GPIO because it is not enabled.')


def set_color(color):
    if is_gpio_enabled:
        if 'red' in color and 0 <= color['red'] <= 100:
            wiringpi.softPwmWrite(RED_PIN, color['red'])
        if 'green' in color and 0 <= color['green'] <= 100:
            wiringpi.softPwmWrite(GREEN_PIN, color['green'])
        if 'blue' in color and 0 <= color['blue'] <= 100:
            wiringpi.softPwmWrite(BLUE_PIN, color['blue'])
    else:
        logger.error('Can not write to GPIO because it is not enabled.')


def set_fade(fade, continue_func=(lambda: True)):
    if is_gpio_enabled:
        delay = 1 if 'delay' not in fade else fade['delay']
        colors = [] if 'colors' not in fade else fade['colors']

        num_loops = len(colors) - 1
        if num_loops > 0:
            for i in range(0, num_loops, 1):
                nextcolor = i + 1 if i < len(colors) - 1 else 0

                red = colors[i]['red']
                green = colors[i]['green']
                blue = colors[i]['blue']
                delta_r = colors[nextcolor]['red'] - red
                delta_g = colors[nextcolor]['green'] - green
                delta_b = colors[nextcolor]['blue'] - blue
                num_changes = max(abs(delta_r), abs(delta_g), abs(delta_b))

                if num_changes == 0:
                    continue
                pause_time = delay / num_changes

                for j in range(0, num_changes):
                    if not red == colors[nextcolor]['red']:
                        red += int(delta_r / abs(delta_r))
                    if not green == colors[nextcolor]['green']:
                        green += int(delta_g / abs(delta_g))
                    if not blue == colors[nextcolor]['blue']:
                        blue += int(delta_b / abs(delta_b))
                    set_rgb(red, green, blue)
                    sleep(pause_time)
                    if not continue_func():
                        break
    else:
        logger.error('Can not write to GPIO because it is not enabled.')


def set_sequence(sequence, continue_func=(lambda: True)):
    if is_gpio_enabled:
        delay = 1 if 'delay' not in sequence else sequence['delay']
        presets = [] if 'sequence' not in sequence else sequence['sequence']
        for effect in presets:
            cont = continue_func()
            if 'type' not in effect:
                continue
            elif cont and effect['type'] == 'color':
                set_color(effect)
                sleep(delay)
            elif cont and effect['type'] == 'fade':
                set_fade(effect, continue_func)
            elif cont and effect['type'] == 'sequence':
                set_sequence(effect, continue_func)
    else:
        logger.error('Can not write to GPIO because it is not enabled.')
