#!/usr/bin/env python
# -*- coding: utf8 -*-
import RPi.GPIO as GPIO
import os, sys, time, threading, subprocess
sys.path.append('MFRC522-python')
import MFRC522
'''---------------------- Konstanten ----------------------'''
'''--------------------------------------------------------'''
ZYKLUSZEIT_MAIN = 0.1 #Zykluszeit des Programms sind 100ms
'''---------------------- Variablen -----------------------'''
'''--------------------------------------------------------'''
continue_reading = True
letzte_uid = "LEER"

def main():
    global continue_reading
    global letzte_uid
    MIFAREReader = MFRC522.MFRC522() # Create an object of the class MFRC522
    #musicplayer = subprocess.Popen(['mpg321', '-K', '-v', 'numb.mp3'], stdout=subprocess.PIPE)
    musicplayer = subprocess.Popen(['mpg321', '-K', 'numb.mp3'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    try:
        while continue_reading:
            (status,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL) # Scan for card
            (status,uid) = MIFAREReader.MFRC522_Anticoll() # Get the UID of the card
            if status == MIFAREReader.MI_OK: # If we have the UID, continue
                var = (str(uid[0]) + str(uid[1]) + str(uid[2]) + str(uid[3]))
                if ((var == "185100155153")and(letzte_uid != "185100155153")):
                    letzte_uid = "185100155153"
                    print letzte_uid
                elif ((var == "12157159163")and(letzte_uid != "12157159163")):
                    letzte_uid = "12157159163"
                    musicplayer.stdin.write('\0x03')
                    musicplayer.stdin.flush()
                    print letzte_uid
            #print "Startausgabe"
            musicplayer.stdin.write('/')
            musicplayer.stdin.flush()
            #print "Endausgabe\n"
            time.sleep(ZYKLUSZEIT_MAIN)

    except KeyboardInterrupt:
        musicplayer.stdin.close()
        musicplayer.terminate()
        #print musicplayer.stdout.readline()
        continue_reading = False
        GPIO.cleanup()
        print "Programm beendet"
    except:
        musicplayer.stdin.close()
        musicplayer.terminate()
        #print musicplayer.stdout.readline()
        continue_reading = False
        GPIO.cleanup()
        print "Programmfehler: " + str(sys.exc_info()[0])

if __name__ == "__main__":
    main()
