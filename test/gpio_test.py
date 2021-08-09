import RPi.GPIO as GPIO 
from time import sleep 
GPIO.setwarnings(False)

GPIO_1 = 31
GPIO_2 = 33
GPIO_3 = 35
GPIO_4 = 37
 
GPIO.setmode(GPIO.BOARD) 
GPIO.setup(GPIO_1, GPIO.OUT)
GPIO.setup(GPIO_2, GPIO.OUT)
GPIO.setup(GPIO_3, GPIO.OUT)
GPIO.setup(GPIO_4, GPIO.OUT)

nOn = 0
while True:
    
    print("turning on GPIO{}".format(nOn + 1))
    
    GPIO.output(GPIO_1, nOn == 0) 
    GPIO.output(GPIO_2, nOn == 1)
    GPIO.output(GPIO_3, nOn == 2)
    GPIO.output(GPIO_4, nOn == 3)
    
    nOn += 1 # increment by 1
    nOn = nOn % 4 # limit nOn to be max 3
        
    sleep(0.3) 
