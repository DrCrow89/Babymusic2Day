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
ZYKLUSZEIT_MAIN = 1.0 #Zykluszeit des Programms sind 100ms
'''---------------------- Variablen -----------------------'''
'''--------------------------------------------------------'''
continue_reading = True
letzte_uid = "LEER"

def MFRC522_Reader(name):
    t = threading.currentThread()
    MIFAREReader = MFRC522.MFRC522() # Create an object of the class MFRC522
    global continue_reading
    global letzte_uid
    while continue_reading:
        (status,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL) # Scan for card
        (status,uid) = MIFAREReader.MFRC522_Anticoll() # Get the UID of the card
        if status == MIFAREReader.MI_OK: # If we have the UID, continue
            var = (str(uid[0]) + str(uid[1]) + str(uid[2]) + str(uid[3]))
#            print "Aktuelle Kartennummer: "+ str(var)
            if ((var == "185100155153")and(letzte_uid != "185100155153")):
                letzte_uid = "185100155153"
                print letzte_uid
            elif ((var == "12157159163")and(letzte_uid != "12157159163")):
                letzte_uid = "12157159163"
                print letzte_uid

def Musikplayer(name):
    t = threading.currentThread()
    pygame.mixer.init()
    pygame.mixer.music.load("numb.mp3")
    pygame.mixer.music.play()
    print "play musik"
    while continue_reading:
        continue
    pygame.mixer.music.stop()

def main():
    try:
        t_reader = threading.Thread(target=MFRC522_Reader, args=("Reader",))
        t_player = threading.Thread(target=Musikplayer, args=("Musikplayer",))
        t_reader.start()
        t_player.start()
        while True:
            time.sleep(ZYKLUSZEIT_MAIN)
#           print "Zeit"

    except KeyboardInterrupt:
        global continue_reading
        continue_reading = False
        GPIO.cleanup()
        t_reader.do_run = False
        t_player.do_run = False
        t_reader.join()
        t_player.join()
        print "Programm beendet"

if __name__ == "__main__":
    main()
