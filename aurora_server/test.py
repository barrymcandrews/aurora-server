import pigpio
import time

if __name__ == '__main__':
    pi = pigpio.pi()

    while True:
        pi.set_PWM_dutycycle(6, 0)
        time.sleep(1)
        pi.set_PWM_dutycycle(6, 255)
        time.sleep(1)
