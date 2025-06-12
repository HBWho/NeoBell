import time

from gpiod.line import Direction, Value
import gpiod

def activate_pin(chip_num, line_num):
    LINE = line_num

    with gpiod.request_lines(
        f"/dev/gpiochip{chip_num}",
        consumer="blink-example",
        config={
            LINE: gpiod.LineSettings(
                direction=Direction.OUTPUT, output_value=Value.ACTIVE
            )
        },
    ) as request:
        request.set_value(LINE, Value.ACTIVE)

def deactivate_pin(chip_num, line_num):
    LINE = line_num

    with gpiod.request_lines(
        f"/dev/gpiochip{chip_num}",
        consumer="blink-example",
        config={
            LINE: gpiod.LineSettings(
                direction=Direction.OUTPUT, output_value=Value.ACTIVE
            )
        },
    ) as request:
        request.set_value(LINE, Value.INACTIVE)

def read_pin_state(chip_num, line_num):
    """
    Reads the current state of a GPIO pin.
    Returns Value.ACTIVE (high) or Value.INACTIVE (low)
    """
    LINE = line_num
    
    with gpiod.request_lines(
        f"/dev/gpiochip{chip_num}",
        consumer="read-example",
        config={
            LINE: gpiod.LineSettings(
                direction=Direction.INPUT  # Set as input to read
            )
        },
    ) as request:
        return request.get_value(LINE)
