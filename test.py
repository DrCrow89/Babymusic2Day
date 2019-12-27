#!/usr/bin/python
# -*- coding: utf-8 -*-
import threading
import time
import os #getTemperaturCPU()
import RPi.GPIO as GPIO
'''---------------------- Konstanten ----------------------'''
ZYKLUSZEIT_MAIN = 0.1 #Zykluszeit des Programms sind 100ms
ZYKLUSZEIT_ALIVE = 0.9 #Zykluszeit für das senden des Alive Flags
GPIO_PIN_ALIVE = 11
'''--------------------------------------------------------'''
'''------------------ GPIO Einstellungen ------------------'''
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(GPIO_PIN_ALIVE, GPIO.OUT) #Pi Alive Flag für Energie-Kontroller
'''--------------------------------------------------------'''
'''------------------ Support Funktionen ------------------'''

'''--------------------------------------------------------'''
'''------------------- Thread Funktionen ------------------'''
def FlagPiIsAlive(name):
    t = threading.currentThread()
    alive_flag = True
    #print "%s gestartet" % name
    while getattr(t, "do_run", True):
        if alive_flag == True:
            GPIO.output(GPIO_PIN_ALIVE, False)
            alive_flag = False
        else:
            GPIO.output(GPIO_PIN_ALIVE, True)
            alive_flag = True
        #print "Alive: %s" % alive_flag
        time.sleep(ZYKLUSZEIT_ALIVE)
        #GPIO.output(GPIO_PIN_ALIVE, False)

    #print "%s beendet" % name

'''--------------------------------------------------------'''
'''--------------------- Hauptprogramm --------------------'''
def main():
    try:
        t_pi_alive = threading.Thread(target=FlagPiIsAlive, args=("Pi is alive",))
        t_pi_alive.start()
        while True:
            time.sleep(ZYKLUSZEIT_MAIN)

    except KeyboardInterrupt:
        t_pi_alive.do_run = False
        t_pi_alive.join()
        print "Programm beendet"

if __name__ == "__main__":
    main()
