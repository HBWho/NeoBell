from hal.gpio import *
import time

class PINService():
    def __init__(self):
        self.led_ext_green = (4, 9)
        self.led_ext_red = (4, 5)
        self.ext_lock = (1, 8)
        self.int_lock = (1, 13)
        self.col_lock = (4, 12)
        self.led_int = (4, 2)

    def activate_green(self):
        activate_pin(self.led_ext_green[0], self.led_ext_green[1])

    def deactivate_green(self):
        deactivate_pin(self.led_ext_green[0], self.led_ext_green[1])

    def activate_red(self):
        activate_pin(self.led_ext_red[0], self.led_ext_red[1])

    def deactivate_red(self):
        deactivate_pin(self.led_ext_red[0], self.led_ext_red[1])

    def activate_external_lock(self):
        activate_pin(self.ext_lock[0], self.ext_lock[1])

    def deactivate_external_lock(self):
        deactivate_pin(self.ext_lock[0], self.ext_lock[1])

    def activate_internal_lock(self):
        activate_pin(self.int_lock[0], self.int_lock[1])

    def deactivate_internal_lock(self):
        deactivate_pin(self.int_lock[0], self.int_lock[1])

    def activate_collect_lock(self):
        activate_pin(self.col_lock[0], self.col_lock[1])

    def deactivate_collect_lock(self):
        deactivate_pin(self.col_lock[0], self.col_lock[1])

    def activate_internal_led(self):
        activate_pin(self.led_int[0], self.led_int[1])

    def deactivate_internal_led(self):
        deactivate_pin(self.led_int[0], self.led_int[1])

