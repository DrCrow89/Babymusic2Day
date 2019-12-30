#!/usr/bin/python
# -*- coding: utf-8 -*-
import threading
import time
import os
import RPi.GPIO as GPIO
'''---------------------- Konstanten ----------------------'''
ZYKLUSZEIT_MAIN = 0.1 # Zykluszeit des Programms sind 100ms
ZYKLUSZEIT_ALIVE = 0.9 # Zykluszeit für das senden des Alive Flags
GPIO_PIN_ALIVE = 11 # Pi Alive Flag für Energie-Kontroller
GPIO_PIN_SHUTDOWN = 13 # Input Pin zum herunterfahren des Pi
'''--------------------------------------------------------'''
'''------------------ GPIO Einstellungen ------------------'''
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(GPIO_PIN_ALIVE, GPIO.OUT)
GPIO.setup(GPIO_PIN_SHUTDOWN, GPIO.IN)
'''--------------------------------------------------------'''
'''------------------ Support Funktionen ------------------'''

'''--------------------------------------------------------'''
'''------------------- Thread Funktionen ------------------'''
def FlagPiIsAlive(name):
    t = threading.currentThread()
    alive_flag = True
    while getattr(t, "do_run", True):
        if alive_flag == True:
            GPIO.output(GPIO_PIN_ALIVE, False)
            alive_flag = False
        else:
            GPIO.output(GPIO_PIN_ALIVE, True)
            alive_flag = True
        time.sleep(ZYKLUSZEIT_ALIVE)

'''--------------------------------------------------------'''
'''--------------------- Hauptprogramm --------------------'''
def main():
    try:
        t_pi_alive = threading.Thread(target=FlagPiIsAlive, args=("Pi is alive",))
        t_pi_alive.start()
        while True:
            if GPIO.input(GPIO_PIN_SHUTDOWN) == GPIO.HIGH:
                GPIO.cleanup()
                os.system("sudo shutdown -h now")
            time.sleep(ZYKLUSZEIT_MAIN)

    except KeyboardInterrupt:
        t_pi_alive.do_run = False
        t_pi_alive.join()
        GPIO.cleanup()
        print "Programm beendet"

if __name__ == "__main__":
    main()
