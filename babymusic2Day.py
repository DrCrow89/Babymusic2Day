#!/usr/bin/env python
# -*- coding: utf8 -*-
import RPi.GPIO as GPIO
import os, sys, time
import glob, random # Playlisten erstellen
import shutil # Kopieren der Log-Datei
sys.path.append('MFRC522-python')
sys.path.append('pygame')
import MFRC522, pygame
import config2Day

'''---------------------- Konstanten ----------------------'''
'''--------------------------------------------------------'''
ZYKLUSZEIT_MAIN = 0.2 # Zykluszeit des Programms
VERZEICHNIS_DATEN = "./data" # Ablageort der Musikdateien
NAME_LOG_DATEI = "musicfile.log" # Pro Verzeichnis gibt es eine Log Datei um verschiedene Informationen zu speichern
INTRO_SOUND = "./data/intro.mp3"
MUSIK_FORMAT = ".mp3" # Musikformat der Musik
CHIP_AUF_LESER_THR = 5 # Sollte kein Chip mehr auf dem Leser für 5 Mal die Zykluszeit liegen, wird die Musik pausiert
'''---------------------- Variablen -----------------------'''
'''--------------------------------------------------------'''
program_run = True
letzte_uid = "LEER"
aktuelles_musik_verzeichnis = "LEER"
aktuelle_playliste = []

def init_musikplayer():
    pygame.mixer.init()
    #pygame.mixer.music.load(INTRO_SOUND)
    #pygame.mixer.music.play()
    #while pygame.mixer.music.get_busy():
    #    continue

def create_playlist_sortiert(ue_verzeichnis):
    playliste = glob.glob(os.path.join(ue_verzeichnis, '*.mp3')) # TODO: Wildcard ersetzen, damit MUSIK_FORMAT benutzt werden kann.
    playliste.sort()
    return playliste

def create_playlist_random(ue_verzeichnis):
    playliste = glob.glob(os.path.join(ue_verzeichnis, '*.mp3')) # TODO: Wildcard ersetzen, damit MUSIK_FORMAT benutzt werden kann.
    random.shuffle(playliste)
    return playliste


def create_verzeichnis(ue_ordner):
    try:
        os.mkdir(os.path.join(VERZEICHNIS_DATEN, ue_ordner)) # Ordner mit der ID erstellen
        shutil.copy(os.path.join(VERZEICHNIS_DATEN, NAME_LOG_DATEI), os.path.join(VERZEICHNIS_DATEN, ue_ordner)) # Default-Logdatei in neues Verzeichnis kopieren
    except OSError:
        print "Verzeichnis konnte nicht erstellt werden"

def check_verzeichnis(ue_uid):
    ret_musik_vorhanden = False
    if (ue_uid != "LEER"): # Für die erste LOOP bei Programmstart nicht das Verzeichnis prüfen.
        if os.path.isdir(os.path.join(VERZEICHNIS_DATEN, ue_uid)) == True: # Verzeichnis existiert
            print "Verzeichnis: " + str(ue_uid) + " existiert"
            for datei in os.listdir(os.path.join(VERZEICHNIS_DATEN, ue_uid)): # Prüft ob eine Musikdatei vorhanden ist.
                if datei.endswith(MUSIK_FORMAT):
                    ret_musik_vorhanden = True
                    break
        else: # Verzeichnis existiert nicht
            ret_musik_vorhanden = False
            create_verzeichnis(ue_uid)
            print "Verzeichnis: " + str(os.path.join(VERZEICHNIS_DATEN, ue_uid)) + " existiert nicht"

    return ret_musik_vorhanden

def read_chip(MIFAREReader):
    global letzte_uid
    ret_uid = letzte_uid
    ret_neu = False # Die eingelesene ID ist eine neue
    (status,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL) # Scan for card
    (status,uid) = MIFAREReader.MFRC522_Anticoll() # Get the UID of the card
    if (status == MIFAREReader.MI_OK): # If we have the UID, continue
        gelesene_uid = (str(uid[0]) + str(uid[1]) + str(uid[2]) + str(uid[3]))
        if (gelesene_uid != ret_uid):
            letzte_uid = gelesene_uid
            ret_uid = gelesene_uid
            ret_neu = True
    return status, ret_neu, ret_uid

def main():
    global letzte_uid
    global program_run
    global aktuelles_musik_verzeichnis
    global aktuelle_playliste
    MIFAREReader = MFRC522.MFRC522() # Create an object of the class MFRC522
    chip_auf_leser = 0

    init_musikplayer()

    try:
        while program_run:
            # Auswertung des Readers
            temp_status, temp_neue_id, temp_uid = read_chip(MIFAREReader) # temp_status is true if a new rfid chip is detected
            if (temp_neue_id == True)and(check_verzeichnis(temp_uid)) == True: # Neuer Chip wurde erkannt, Verzeichnis und Musik vorhanden
                aktuelles_musik_verzeichnis = os.path.join(VERZEICHNIS_DATEN, temp_uid)
                print "Musikplayer kann neues Verzeichnis abspielen"
                ### Playliste erstellen auf Basis des Musiktyps ###
                erfolgreich_gelesen, wert = config2Day.get_value(os.path.join(VERZEICHNIS_DATEN, temp_uid, NAME_LOG_DATEI), "Grundeinstellung", "Typ")
                if ((erfolgreich_gelesen == True)and(wert == "Hoerspiel")):
                    print "Titel ist ein Hörspiel und wird nicht gemischt"
                    aktuelle_playliste = create_playlist_sortiert(aktuelles_musik_verzeichnis)
                elif ((erfolgreich_gelesen == True)and(wert == "Musik")):
                    print "Titel ist ein Musikalbum und wird gemischt"
                    aktuelle_playliste = create_playlist_random(aktuelles_musik_verzeichnis)
                else:
                    pass
            else: # Kein neuer Chip wurd erkannt, Verzeichnis oder Musik nicht vorhanden
                if (temp_status == 2)and(chip_auf_leser < CHIP_AUF_LESER_THR):
                    chip_auf_leser = chip_auf_leser +1
                elif (temp_status == 2)and(chip_auf_leser == CHIP_AUF_LESER_THR):
                    # Sollte kein Chip mehr auf dem Leser liegen, wird die Musik gestoppt
                    print "Musikplayer stoppen"
                else:
                    chip_auf_leser = 0

            # Steuerung des Musikplayers

            time.sleep(ZYKLUSZEIT_MAIN)

    except KeyboardInterrupt:
        GPIO.cleanup()
        print "Programm beendet"

    except:
        GPIO.cleanup()
        print "Programmfehler: " + str(sys.exc_info()[0])

if __name__ == "__main__":
    main()
