from hal.gpio import GpioManager
import time

# --- Hardware Pinout Definition ---
EXTERNAL_GREEN_LED_PIN = (4, 9)
EXTERNAL_RED_LED_PIN = (4, 5)
CAMERA_LED_PIN = (4, 8)
INTERNAL_LED_PIN = (4, 2)
EXTERNAL_LOCK_PIN = (1, 8)
INTERNAL_LOCK_PIN = (1, 13)
COLLECT_LOCK_PIN = (4, 12)

class GpioService:
    """
    Provides a high-level API to control hardware components like LEDs and locks,
    abstracting away the underlying pin details.
    """
    def __init__(self, gpio_manager: GpioManager):
        self.manager = gpio_manager

    # --- LED Control Methods ---
    
    def set_external_green_led(self, is_on: bool):
        """Controls the external green LED."""
        self.manager.set_pin_value(EXTERNAL_GREEN_LED_PIN, is_on)

    def set_external_red_led(self, is_on: bool):
        """Controls the external red LED."""
        self.manager.set_pin_value(EXTERNAL_RED_LED_PIN, is_on)
        
    def set_internal_led(self, is_on: bool):
        """Controls the internal LED."""
        self.manager.set_pin_value(INTERNAL_LED_PIN, is_on)

    def set_camera_led(self, is_on: bool):
        self.manager.set_pin_value(CAMERA_LED_PIN, is_on)

    # --- Solenoid Lock Control Methods ---

    def set_external_lock(self, is_locked: bool):
        # COMPARTIMENTO DE COLOCAR PACOTE
        """Controls the external lock solenoid."""
        self.manager.set_pin_value(EXTERNAL_LOCK_PIN, is_locked)

    def set_internal_lock(self, is_locked: bool):
        pass
        # NAO EXISTE MAIS
        # """Controls the internal lock solenoid."""
        # self.manager.set_pin_value(INTERNAL_LOCK_PIN, is_locked)

    def set_collect_lock(self, is_locked: bool):
        # COMPARTIMENTO DE RETIRAR PACOTE
        """Controls the collection lock solenoid."""
        self.manager.set_pin_value(COLLECT_LOCK_PIN, is_locked)

