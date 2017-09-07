from typing import List
import wiringpi

wiringpi.wiringPiSetup()

def enable(pins: List[int]):
    for pin in pins:
        wiringpi.softPwmCreate(pin, 0, 100)


def disable(pins: List[int]):
    for pin in pins:
        wiringpi.softPwmWrite(pin, 0)
        wiringpi.softPwmStop(pin)


cpdef set_pwm(int pin, int level):
    wiringpi.softPwmWrite(pin, level)
