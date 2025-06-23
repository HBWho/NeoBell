import time
import logging
from periphery import PWM

logger = logging.getLogger(__name__)

class ServoService:
    """
    Provides a high-level API to control a servo motor for mechanisms
    like a trapdoor or hatch. It abstracts the underlying PWM details.
    """
    def __init__(self, pwm_chip: int, pwm_channel: int):
        """
        Initializes the ServoService.
        
        Args:
            pwm_chip: The PWM chip number (e.g., 1 for PWM1).
            pwm_channel: The PWM channel number (e.g., 0 for PWM0).
        """
        self.pwm_chip = pwm_chip
        self.pwm_channel = pwm_channel
        # Define duty cycles for open/closed positions. These may need tuning.
        # Based on your code: 0.025 is open, 0.093 is closed.
        self.open_duty_cycle = 0.025
        self.closed_duty_cycle = 0.093

    def _move_to_position(self, target_duty_cycle: float):
        """Private helper method to move the servo to a target position smoothly."""
        pwm = None # Ensure pwm is defined for the finally block
        try:
            logger.info(f"Moving servo to duty cycle: {target_duty_cycle}")
            pwm = PWM(self.pwm_chip, self.pwm_channel)
            pwm.frequency = 50
            pwm.polarity = "normal"
            pwm.enable()

            # Set a starting position before moving
            pwm.duty_cycle = self.closed_duty_cycle if target_duty_cycle < pwm.duty_cycle else self.open_duty_cycle
            time.sleep(0.5)

            # Move towards the target
            current_duty = pwm.duty_cycle
            direction = 1 if target_duty_cycle > current_duty else -1
            
            while True:
                current_duty += 0.001 * direction
                pwm.duty_cycle = current_duty
                time.sleep(0.02) # Adjust sleep for speed/smoothness

                if direction == 1 and current_duty >= target_duty_cycle:
                    break
                if direction == -1 and current_duty <= target_duty_cycle:
                    break
            
            logger.info("Servo move complete.")
            time.sleep(1) # Hold position briefly

        except Exception as e:
            logger.error("An error occurred while controlling the servo.", exc_info=True)
        finally:
            if pwm:
                pwm.duty_cycle = target_duty_cycle # Ensure it ends at the target
                pwm.disable()
                pwm.close()
                logger.info("PWM resource closed.")

    def open_hatch(self):
        """Opens the hatch to the defined 'open' position."""
        logger.info("Opening hatch...")
        self._move_to_position(self.open_duty_cycle)

    def close_hatch(self):
        """Closes the hatch to the defined 'closed' position."""
        logger.info("Closing hatch...")
        self._move_to_position(self.closed_duty_cycle)