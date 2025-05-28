import time
from gpio import activate_pin, deactivate_pin

chip = 4
line = 2

while(True):
    print("Ativado")
    activate_pin(chip, line)
    time.sleep(5)
    print("Desativado")
    deactivate_pin(chip, line)
    time.sleep(5)
