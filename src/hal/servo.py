#!/usr/bin/python3

from periphery import PWM
import time


from hal.gpio import activate_pin, deactivate_pin

#pwm = PWM(1, 0)

class ServoClass():
    def __init__(self):
        pass

    def servopadrao(self):
        try:
            pwm = PWM(1, 0)
            pwm.frequency = 50
            pwm.duty_cycle = 0.0930  # Começa em 0%
            pwm.polarity = "normal"
            pwm.enable()

            posicao_final = 93
            # posicao_target = 18
            posicao_target = 20
            posicao_final = (posicao_final/1000)
            posicao_target = (posicao_target/1000)
            direction = -1  

            while True:
                pwm.duty_cycle += 0.0005 * direction  # passo para suavidade
                pwm.duty_cycle = round(pwm.duty_cycle, 5)

                print("Duty:", pwm.duty_cycle)

                # Limites entre 0% e 10%
                if pwm.duty_cycle >= posicao_final:
                    direction = -1
                elif pwm.duty_cycle <= posicao_target:
                    direction = 1

                if pwm.duty_cycle == posicao_final:
                    break
                if pwm.duty_cycle == posicao_target:
                    activate_pin(1, 13)
                    time.sleep(1)
                    pwm.duty_cycle = 0.093
                    time.sleep(1)
                    deactivate_pin(1, 13)
                if direction == -1:
                    time.sleep(0.01)
                else:
                    time.sleep(0.001)

            pwm.close()
        finally:
            pwm.close()
