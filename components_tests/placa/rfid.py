import OPI.GPIO as GPIO
from mfrc522 import MFRC522

RST = 26
BUS = 4
DEVICE = 0

reader = MFRC522(bus=BUS)
