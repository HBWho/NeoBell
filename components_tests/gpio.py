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

deactivate_pin(4, 5)
deactivate_pin(4, 9)
deactivate_pin(4, 2)
deactivate_pin(1, 8)
deactivate_pin(1, 13)
deactivate_pin(1, 30)
