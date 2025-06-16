from gpiod.line import Direction, Value
import gpiod

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
                
                direction = Direction.OUTPUT if pin_type == 'outputs' else Direction.INPUT
                self.config[chip_path][line_num] = gpiod.LineSettings(direction=direction)

        # Request all configured lines from their respective chips
        self.requests = [
            gpiod.request_lines(chip_path, consumer=consumer, config=chip_config)
            for chip_path, chip_config in self.config.items()
        ]

    def _find_request(self, pin: tuple[int, int]):
        """Finds the gpiod request object corresponding to a given pin."""
        chip_path = f"/dev/gpiochip{pin[0]}"
        for req in self.requests:
            if req.path == chip_path:
                return req
        raise ValueError(f"Pin {pin} was not initialized in this manager.")

    def set_pin_value(self, pin: tuple[int, int], is_active: bool):
        """
        Sets the value of a previously requested output pin.

        Args:
            pin: The (chip, line) tuple of the pin to set.
            is_active: True to set the pin to ACTIVE, False for INACTIVE.
        """
        request = self._find_request(pin)
        value = Value.ACTIVE if is_active else Value.INACTIVE
        request.set_value(pin[1], value)

    def get_pin_value(self, pin: tuple[int, int]) -> bool:
        """
        Reads the value of a previously requested input pin.

        Args:
            pin: The (chip, line) tuple of the pin to read.

        Returns:
            True if the pin is ACTIVE, False if INACTIVE.
        """
        request = self._find_request(pin)
        return request.get_value(pin[1]) == Value.ACTIVE

    def close(self):
        """Releases all requested GPIO lines."""
        for req in self.requests:
            req.close()

    def __enter__(self):
        """Enables the use of 'with' statement for resource management."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensures that close() is called when exiting a 'with' block."""
        self.close()