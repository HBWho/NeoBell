#!/usr/bin/env python3
# -- encoding: utf-8 --

from periphery import PWM 
import time
from gpiod.line import Direction, Value
import gpiod

step = 0.00825

pwm = PWM(1, 0)

def rotate_up():
    pwm.duty_cycle = round(pwm.duty_cycle+step,2)

def rotate_down():
    pwm.duty_cycle = round(pwm.duty_cycle-step,2)

try: 
    pwm.frequency = 50
    pwm.duty_cycle = 0.00
    pwm.enable()
    
    full_up = True

    while True: 
        # pwm.duty_cycle += 0.05
        # if pwm.duty_cycle == 1.00:
        #     pwm.duty_cycle = 0.5
        #     print(f"duty_cycle: {pwm.duty_cycle} | period: {pwm.period}")
        if pwm.duty_cycle == 1.0 or pwm.duty_cycle == 0.0: 
            full_up = not full_up

        if full_up:
            rotate_down()
        else:
            rotate_up()

        time.sleep(0.8) 
except Exception as e: 
    print(f"Error: {e}\n")
finally: 
    pwm.duty_cycle = 1.0 
    pwm.close()
