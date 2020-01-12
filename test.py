#!/usr/bin/python
# -*- coding: utf-8 -*-
import threading
import time
import os
import RPi.GPIO as GPIO
'''--------------------------------------------------------'''
'''---------------------- Konstanten ----------------------'''
ZYKLUSZEIT_MAIN = 0.1     # Zykluszeit des Programms sind 100ms
ZYKLUSZEIT_ALIVE = 0.9    # Zykluszeit für das senden des Alive Flags
GPIO_PIN_ALIVE = 7        # Pi Alive Flag für Energie-Kontroller
GPIO_PIN_SHUTDOWN = 11    # Input Pin zum herunterfahren des Pi
GPIO_PIN_BUTTON_MUTE = 13 # Input Pin Lautstärketasten aus- oder einschalten
GPIO_PIN_LIGHT_MUTE = 15  # Input Pin zum ein- und ausschalten der Beleuchtung
GPIO_PIN_LAUTER = 29      # Input Pin für lauter - Button
GPIO_PIN_LEISER = 31      # Input Pin für leiser - Button
'''--------------------------------------------------------'''
'''---------------------- Variablen -----------------------'''
global switch_button_mute # Variable zum einlesen des Schalters um die Lautstärketasten einzulesen
global switch_light_mute  # Variable zum einlesen des Schalters um die Lichtsteuerung ein- oder auszuschalten
'''--------------------------------------------------------'''
'''------------------ GPIO Einstellungen ------------------'''
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(GPIO_PIN_ALIVE, GPIO.OUT)
GPIO.setup(GPIO_PIN_SHUTDOWN, GPIO.IN)
GPIO.setup(GPIO_PIN_BUTTON_MUTE, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(GPIO_PIN_LIGHT_MUTE, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(GPIO_PIN_LAUTER, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(GPIO_PIN_LEISER, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
'''--------------------------------------------------------'''
'''------------------ Support Funktionen ------------------'''
def increase_volume(ue_gpio_nummer):
    global switch_button_mute
    if switch_button_mute == True:
        print "Musik lauter"
    else:
        print "Musik lauter ist ausgeschaltet"

def decrease_volume(ue_gpio_nummer):
    global switch_button_mute
    if switch_button_mute == True:
        print "Musik leiser"
    else:
        print "Musik leiser ist ausgeschaltet"

def mute_volume_button(ue_gpio_nummer):
    global switch_button_mute
    if switch_button_mute == True:
        switch_button_mute = False
        print "Schalter für Lautstärketasten aus"
    else:
        switch_button_mute = True
        print "Schalter für Lautstärketasten ein"

def mute_light(ue_gpio_nummer):
    global switch_light_mute
    if switch_light_mute == True:
        switch_light_mute = False
        print "Schalter für Lichtsteuerung war aus"
    else:
        switch_light_mute = True
        print "Schalter für Lichtsteuerung war ein"

'''--------------------------------------------------------'''
'''------------------- Thread Funktionen ------------------'''
def FlagPiIsAlive(name):
    t = threading.currentThread()
    alive_flag = True
    while getattr(t, "do_run", True):
        if alive_flag == True:
            GPIO.output(GPIO_PIN_ALIVE, True)
            alive_flag = False
        else:
            GPIO.output(GPIO_PIN_ALIVE, False)
            alive_flag = True
        time.sleep(ZYKLUSZEIT_ALIVE)

'''--------------------------------------------------------'''
'''--------------------- Hauptprogramm --------------------'''
def main():
    global switch_button_mute
    global switch_light_mute
    if GPIO.input(GPIO_PIN_BUTTON_MUTE) == True:
        switch_button_mute = True
        print "Schalter für Lautstärketasten war an"
    else:
        switch_button_mute = False
        print "Schalter für Lautstärketasten war aus"
    if GPIO.input(GPIO_PIN_LIGHT_MUTE) == True:
        switch_light_mute = True
        print "Schalter für Lichtsteuerung war an"
    else:
        switch_light_mute = False
        print "Schalter für Lichtsteuerung war aus"

    GPIO.add_event_detect(GPIO_PIN_LAUTER,GPIO.RISING,callback=increase_volume,bouncetime=800)
    GPIO.add_event_detect(GPIO_PIN_LEISER,GPIO.RISING,callback=decrease_volume,bouncetime=800)
    GPIO.add_event_detect(GPIO_PIN_BUTTON_MUTE,GPIO.BOTH,callback=mute_volume_button,bouncetime=1000)
    GPIO.add_event_detect(GPIO_PIN_LIGHT_MUTE,GPIO.BOTH,callback=mute_light,bouncetime=1000)

    try:
        t_pi_alive = threading.Thread(target=FlagPiIsAlive, args=("Pi is alive",))
        t_pi_alive.start()
        while True:
            if GPIO.input(GPIO_PIN_SHUTDOWN) == GPIO.HIGH:
                pass
                #t_pi_alive.do_run = False
                #t_pi_alive.join()
                #GPIO.cleanup()
                #os.system("sudo shutdown -h now")
            time.sleep(ZYKLUSZEIT_MAIN)

    except KeyboardInterrupt:
        t_pi_alive.do_run = False
        t_pi_alive.join()
        GPIO.cleanup()
        print "Programm beendet"

if __name__ == "__main__":
    main()
