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