import time

from gpio import activate_pin, deactivate_pin

print("Digite um numero par")
num = int(input())

if(num % 2 == 0):
    print("Correto!")
    activate_pin(1, 31)
else:
    print("Errado!")
    deactivate_pin(1, 31)

