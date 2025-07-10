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

    def closeHatch(self):
        try:
            pwm = PWM(self.pwm_chip, self.pwm_channel)
            pwm.frequency = 50
            pwm.duty_cycle = 0.0930  
            pwm.polarity = "normal"
            pwm.enable()

            posicao_final = 93
            posicao_target = 31 # TODO
            posicao_final = (posicao_final/1000)
            posicao_target = (posicao_target/1000)
            direction = -1  
            time.sleep(2)
            while True:
                pwm.duty_cycle += 0.0005 * direction  
                pwm.duty_cycle = round(pwm.duty_cycle, 5)

                print("Duty:", pwm.duty_cycle)

                if pwm.duty_cycle >= posicao_final:
                    direction = -1
                elif pwm.duty_cycle <= posicao_target:
                    direction = 1

                if pwm.duty_cycle == posicao_final:
                    break
                if direction == -1:
                    if pwm.duty_cycle > 0.060:
                        time.sleep(0.01)
                    else:
                        time.sleep(0.005)
                else:
                    time.sleep(0.2)
            
            pwm.close()

        finally:
            pwm.close()

    def openHatch(self):
        try:
            pwm = PWM(self.pwm_chip, self.pwm_channel)
            pwm.frequency = 50
            pwm.duty_cycle = 0.0930  
            pwm.polarity = "normal"
            pwm.enable()

            posicao_final = 100
            posicao_target = 93
            posicao_final = (posicao_final/1000)
            posicao_target = (posicao_target/1000)
            direction = 1

            while True:
                pwm.duty_cycle += 0.0005 * direction  
                pwm.duty_cycle = round(pwm.duty_cycle, 5)

                print("Duty:", pwm.duty_cycle)

                if pwm.duty_cycle >= posicao_final:
                    direction = -1
                elif pwm.duty_cycle <= posicao_target:
                    direction = 1

                if pwm.duty_cycle == posicao_final:
                    break
                if pwm.duty_cycle == posicao_target:
                    time.sleep(1)
                if direction == -1:
                    time.sleep(0.01)
                else:
                    time.sleep(0.001)
            time.sleep(3)
            pwm.duty_cycle = 0.0930
            pwm.close()

        finally:
            pwm.close()
