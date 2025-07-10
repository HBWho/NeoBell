import logging
from gpiod.line import Direction, Value, Bias
import gpiod

logger = logging.getLogger(__name__)

class GpioManager:
    """
    Manages the lifecycle of GPIO lines by requesting them upon
    initialization and releasing them when closed. This avoids repeatedly
    opening and closing lines for each operation.
    """
    def __init__(self, output_pins: list[tuple[int, int]], input_pins: list[tuple[int, int]], consumer="app"):
        """
        Initializes the manager and requests all specified GPIO lines.

        Args:
            output_pins: A list of pins to be configured as outputs. Format: [(chip, line), ...].
            input_pins: A list of pins to be configured as inputs. Format: [(chip, line), ...].
            consumer: A string identifying the application using the lines.
        """
        self.config = {}
        
        all_pins = {
            'outputs': output_pins,
            'inputs': input_pins
        }

        for pin_type, pins in all_pins.items():
            for chip_num, line_num in pins:
                chip_path = f"/dev/gpiochip{chip_num}"
                if chip_path not in self.config:
                    self.config[chip_path] = {}
                
                settings = None
                if pin_type == 'outputs':
                    settings = gpiod.LineSettings(direction=Direction.OUTPUT)
                else: 
                    settings = gpiod.LineSettings(
                        direction=Direction.INPUT,
                        # bias=Bias.PULL_UP
                        bias=Bias.PULL_DOWN
                    )

                if settings:
                    self.config[chip_path][line_num] = settings

        self.requests = {
            chip_path: gpiod.request_lines(chip_path, consumer=consumer, config=chip_config)
            for chip_path, chip_config in self.config.items()
        }
        logger.info(f"GPIO Manager initialized for chips: {list(self.requests.keys())}")

    def set_pin_value(self, pin: tuple[int, int], is_active: bool):
        """
        Sets the value of a previously requested output pin.

        Args:
            pin: The (chip, line) tuple of the pin to set.
            is_active: True to set the pin to ACTIVE, False for INACTIVE.
        """
        chip_num, line_num = pin
        chip_path = f"/dev/gpiochip{chip_num}"
        
        request = self.requests.get(chip_path)
        
        if not request:
            raise ValueError(f"No request found for chip {chip_path}. Was it initialized in GpioManager?")

        value = Value.ACTIVE if is_active else Value.INACTIVE
        request.set_value(line_num, value)

    def get_pin_value(self, pin: tuple[int, int]) -> bool:
        """
        Reads the value of a previously requested input pin.

        Args:
            pin: The (chip, line) tuple of the pin to read.

        Returns:
            True if the pin is ACTIVE, False if INACTIVE.
        """
        chip_num, line_num = pin
        chip_path = f"/dev/gpiochip{chip_num}"
        
        request = self.requests.get(chip_path)
        
        if not request:
            raise ValueError(f"No request found for chip {chip_path}. Was it initialized in GpioManager?")

        return request.get_value(line_num) == Value.ACTIVE

    def close(self):
        """Releases all requested GPIO lines."""
        logger.info("Signaling GPIO resources to be released by the system.")
        self.requests.clear()

    def __enter__(self):
        """Enables the use of 'with' statement for resource management."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensures that close() is called when exiting a 'with' block."""
        self.close()
