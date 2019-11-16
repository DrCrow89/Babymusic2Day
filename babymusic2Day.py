#!/usr/bin/env python
# -*- coding: utf8 -*-
import RPi.GPIO as GPIO
import sys, time, threading
sys.path.append('MFRC522-python')
sys.path.append('pygame')
import MFRC522, pygame
import signal

'''---------------------- Konstanten ----------------------'''
'''--------------------------------------------------------'''
ZYKLUSZEIT_MAIN = 0.2 #Zykluszeit des Programms
'''---------------------- Variablen -----------------------'''
'''--------------------------------------------------------'''
program_run = True
letzte_uid = "LEER"

def read_chip(MIFAREReader):
    (status,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL) # Scan for card
    (status,uid) = MIFAREReader.MFRC522_Anticoll() # Get the UID of the card
    if status == MIFAREReader.MI_OK: # If we have the UID, continue
        var = (str(uid[0]) + str(uid[1]) + str(uid[2]) + str(uid[3]))
        print var

def main():
    global letzte_uid
    global program_run
    MIFAREReader = MFRC522.MFRC522() # Create an object of the class MFRC522
    try:
        while program_run:
            read_chip(MIFAREReader)
            time.sleep(ZYKLUSZEIT_MAIN)

    except KeyboardInterrupt:
        GPIO.cleanup()
        print "Programm beendet"

    except:
        GPIO.cleanup()
        print "Programmfehler: " + str(sys.exc_info()[0])

if __name__ == "__main__":
    main()
