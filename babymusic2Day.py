#!/usr/bin/env python
# -*- coding: utf8 -*-
import RPi.GPIO as GPIO
import os, sys, time, threading
sys.path.append('MFRC522-python')
sys.path.append('pygame')
import MFRC522, pygame

'''---------------------- Konstanten ----------------------'''
'''--------------------------------------------------------'''
ZYKLUSZEIT_MAIN = 0.2 #Zykluszeit des Programms
VERZEICHNIS_DATEN = "./data"
'''---------------------- Variablen -----------------------'''
'''--------------------------------------------------------'''
program_run = True
letzte_uid = "LEER"

def check_verzeichnis(ue_uid):
    if (ue_uid != "LEER"): # Für die erste LOOP bei Programmstart nicht das Verzeichnis prüfen.
        if os.path.isdir(os.path.join(VERZEICHNIS_DATEN, ue_uid)) == True: # Verzeichnis existiert
            print "Verzeichnis: " + str(ue_uid) + " existiert"
        else: # Verzeichnis existiert nicht
            print os.path.join(VERZEICHNIS_DATEN, ue_uid)
            print "Verzeichnis: " + str(ue_uid) + " existiert nicht"


def read_chip(MIFAREReader):
    global letzte_uid
    ret_uid = letzte_uid
    ret_neu = False
    (status,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL) # Scan for card
    (status,uid) = MIFAREReader.MFRC522_Anticoll() # Get the UID of the card
    #print "Status: " + str(status)
    if status == MIFAREReader.MI_OK: # If we have the UID, continue
        gelesene_uid = (str(uid[0]) + str(uid[1]) + str(uid[2]) + str(uid[3]))
        if (gelesene_uid != ret_uid):
            letzte_uid = gelesene_uid
            ret_uid = gelesene_uid
            ret_neu = True
    return ret_neu, ret_uid

def main():
    global letzte_uid
    global program_run
    MIFAREReader = MFRC522.MFRC522() # Create an object of the class MFRC522
    try:
        while program_run:
            temp_status, temp_uid = read_chip(MIFAREReader) # temp_status is true if a new rfid chip is detected
            if temp_status == True:
                check_verzeichnis(temp_uid)
            else:
                # Keine neue Chipkarte erkannt
                pass

            time.sleep(ZYKLUSZEIT_MAIN)
            #print "ENDE"

    except KeyboardInterrupt:
        GPIO.cleanup()
        print "Programm beendet"

    except:
        GPIO.cleanup()
        print "Programmfehler: " + str(sys.exc_info()[0])

if __name__ == "__main__":
    main()
