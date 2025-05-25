import time
import gpiod
from gpiod.line import Direction, Value

# Configuration (CONFIRMED CORRECT)
CHIP = 'gpiochip0'
LINE_OFFSET = 13  # GPIO0_B5 (Bank 0, Group B(1), Pin 5: 0*32 + 1*8 +5 =13)

# Complete notes
NOTES = { ... }  # Keep your existing note definitions

# Song definition
SONG = [ ... ]  # Keep your song array

def play_tone(line, frequency, duration):
    if frequency <= 0:
        time.sleep(duration)
        return
    
    period = 1.0 / frequency
    half_period = period / 2
    end_time = time.time() + duration
    
    try:
        while time.time() < end_time:
            line.set_value(Value.ACTIVE)
            time.sleep(half_period)
            line.set_value(Value.INACTIVE)
            time.sleep(half_period)
    except Exception as e:
        print(f"Error: {e}")

def main():
    # SINGLE ACQUISITION FOR ENTIRE PROGRAM
    with gpiod.Chip(CHIP) as chip:
        line = chip.get_line(LINE_OFFSET)
        config = gpiod.line_request()
        config.consumer = "buzzer-song"
        config.request_type = Direction.OUTPUT
        line.request(config)
        
        print("Playing Happy Birthday...")
        for note, duration in SONG:
            freq = NOTES[note]
            print(f"Playing {note} ({freq}Hz) for {duration}s")
            play_tone(line, freq, duration)
            
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        print("Cleaning up...")
