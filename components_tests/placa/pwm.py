# Python example using GPIO Zero (if supported)
from gpiozero import PWMOutputDevice

pwm = PWMOutputDevice(12)  # Use correct pin number
pwm.value = 0.5  # 50% duty cycle
