import wiringpi
import time
import os

pinR = 17
pinG = 18
pinB = 22

os.system('gpio export ' + str(pinR) + ' out')
os.system('gpio export ' + str(pinG) + ' out')
os.system('gpio export ' + str(pinB) + ' out')

wiringpi.wiringPiSetup()

wiringpi.softPwmCreate(pinR, 0, 127)
wiringpi.softPwmCreate(pinG, 0, 127)
wiringpi.softPwmCreate(pinB, 0, 127)

while True:
    for value in range(0,128):
        wiringpi.softPwmWrite(pinR, value)
        print value
        time.sleep(0.01);
    for value in range(128,0,-1):
        wiringpi.softPwmWrite(pinR, value)
        print value
        time.sleep(0.01);
