#!/usr/bin/env python
# -*- coding: utf8 -*-
import RPi.GPIO as GPIO
import os, sys, time, subprocess
import glob, random # Playlisten erstellen
import shutil # Kopieren der Log-Datei
import serial # Kommunikation mit Arduino
sys.path.append('MFRC522-python')
sys.path.append('pygame')
import MFRC522, pygame
import config2Day

'''-------------------- Konfiguration ---------------------'''
'''--------------------------------------------------------'''
INIT_SOUND = True
DEBUG_MODE = False
'''---------------------- Konstanten ----------------------'''
'''--------------------------------------------------------'''
ZYKLUSZEIT_MAIN = 0.2 # Zykluszeit des Programms
VERZEICHNIS_DATEN = "./data" # Ablageort der Musikdateien
NAME_LOG_DATEI = "musicfile.log" # Pro Verzeichnis gibt es eine Log Datei um verschiedene Informationen zu speichern
INTRO_SOUND = "./data/intro.mp3"
MUSIK_FORMAT = ".mp3" # Musikformat der Musik.
NIO_READ_COUNTER_THR = 2 # Ist ein Chip nicht lesbar wird diese Anzahl nochmal gelesen bis es auf einen unglültigen Wert gesetzt wird
VOLUME_RANGE = 0.05
VOMUME_START = 0.5
TASTER_LAUTER = 31
TASTER_LEISER = 33
GPIO_PIN_ARDUINO = 29
GPIO_PIN_SHUTDOWN = 11 # Wird gebraucht, dass der Port wieder auf BCM gestellt wird und das shutdown Skript von OnOffShim wieder funktioniert.
'''---------------------- Variablen -----------------------'''
'''--------------------------------------------------------'''
program_run = True
nio_read_counter = 0 # Counter zum
aktuelle_chip_uid = "LEER"
letzte_gueltige_chip_uid = "LEER"
aktuelles_musik_verzeichnis = "LEER"
aktuelle_playliste = []
aktueller_titel_index = 0
aktueller_titel = "LEER"
verbindung_arduino = False
status_lichtsteuerung = 0

def set_licht(ue_uid_valid, arduino):
    global status_lichtsteuerung
    try:
        if(status_lichtsteuerung == 0): # Licht wurde initialisiert, geht nach dem Blinken auf dauerhaft grün
            if((ue_uid_valid == True)and(pygame.mixer.music.get_busy() == True)):
                status_lichtsteuerung = 1 # starte blinken
                arduino.write("2")
                response = arduino.readline()
                #print response
            else:
                pass
        elif(status_lichtsteuerung == 1): # Musik läuft und das Licht blinkt
            if(pygame.mixer.music.get_busy() == False):
                status_lichtsteuerung = 0 # Musik wurde gestoppt und das Licht soll zurück auf dauerhaft grün
                arduino.write("4")
                response = arduino.readline()
                #print response
            else:
                pass
        else:
            pass
    except:
        verbindung_arduino = False
        GPIO.output(GPIO_PIN_ARDUINO, False)
        print "Fehler bei der Verbindung zum Arduino nach Start"

def init_musikplayer():
    pygame.mixer.init()
    pygame.mixer.music.set_volume(VOMUME_START)
    if INIT_SOUND == True:
        pygame.mixer.music.load(INTRO_SOUND)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            continue

def start_musikplayer(ue_aktuelle_playliste, ue_aktueller_titel, ue_start):
    pygame.mixer.music.load(ue_aktuelle_playliste[ue_aktuelle_playliste.index(ue_aktueller_titel)])
    # Testen ob es den aktuellen Startpunkt überhaupt gibt.
    pygame.mixer.music.play(start=ue_start)

def set_musikdaten(ue_path, ue_section, ue_option_titel, ue_option_stelle):
    config2Day.set_value(ue_path, "Log", "letzter_titel", str(ue_option_titel))
    config2Day.set_value(ue_path, "Log", "letzte_stelle", str(ue_option_stelle))

def stop_musikplayer_hart():
    if pygame.mixer.music.get_busy() == True:
        pygame.mixer.music.stop()

def stop_musikplayer(ue_path, ue_titel, ue_spielzeit_offset):
    if pygame.mixer.music.get_busy() == True:
        if DEBUG_MODE == True:
            print "Speichern"
        speicherzeit = (((pygame.mixer.music.get_pos())/1000)+ue_spielzeit_offset) # Die aktuelle Spielzeit richtet sich nur nach dem Playerstart. Nicht nach dem Musikstart und muss daher aufaddiert werden.
        set_musikdaten(ue_path, "Log", ue_titel, speicherzeit)
        pygame.mixer.music.stop()

def increase_volume(ue_gpio_nummer):
    volume = pygame.mixer.music.get_volume() + VOLUME_RANGE
    pygame.mixer.music.set_volume(volume)
    print pygame.mixer.music.get_volume()

def decrease_volume(ue_gpio_nummer):
    volume = pygame.mixer.music.get_volume() - VOLUME_RANGE
    pygame.mixer.music.set_volume(volume)
    print pygame.mixer.music.get_volume()

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
        temp_verzeichnis = os.path.join(VERZEICHNIS_DATEN, ue_ordner)
        os.mkdir(temp_verzeichnis) # Ordner mit der ID erstellen
        shutil.copy(os.path.join(VERZEICHNIS_DATEN, NAME_LOG_DATEI), temp_verzeichnis) # Default-Logdatei in neues Verzeichnis kopieren
        subprocess.call(["sudo", "chmod", "-R", "777", temp_verzeichnis])
    except OSError:
        print "Verzeichnis konnte nicht erstellt werden"

def check_verzeichnis(ue_uid):
    ret_musik_vorhanden = False
    if (ue_uid != "LEER"): # Für die erste LOOP bei Programmstart nicht das Verzeichnis prüfen.
        if os.path.isdir(os.path.join(VERZEICHNIS_DATEN, ue_uid)) == True: # Verzeichnis existiert
            #print "Verzeichnis: " + str(ue_uid) + " existiert"
            for datei in os.listdir(os.path.join(VERZEICHNIS_DATEN, ue_uid)): # Prüft ob eine Musikdatei vorhanden ist.
                if datei.endswith(MUSIK_FORMAT):
                    ret_musik_vorhanden = True
                    break
        else: # Verzeichnis existiert nicht
            ret_musik_vorhanden = False
            create_verzeichnis(ue_uid)
    return ret_musik_vorhanden

def read_chip(MIFAREReader):
    # Wirklich nötig die global zu haben?
    global nio_read_counter # Zum zählen der ungültigen Leseversuche
    global aktuelle_chip_uid # Aktuelle Information über den Chip. Ungültig: "LEER" oder gültig mit der uid
    global letzte_gueltige_chip_uid # Letzte gültige chip-uid
    temp_neue_uid = False

    (status,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL) # Scan for card
    (status,uid) = MIFAREReader.MFRC522_Anticoll() # Get the UID of the card
    if (status == MIFAREReader.MI_OK): # If we have the UID, continue
        aktuelle_chip_uid = (str(uid[0]) + str(uid[1]) + str(uid[2]) + str(uid[3]))
        if (aktuelle_chip_uid != letzte_gueltige_chip_uid):
            temp_neue_uid = True
            letzte_gueltige_chip_uid = aktuelle_chip_uid
        else:
            pass
        nio_read_counter = 0
    else:
        if (nio_read_counter < NIO_READ_COUNTER_THR):
            nio_read_counter = nio_read_counter +1
            aktuelle_chip_uid = letzte_gueltige_chip_uid
        elif (nio_read_counter == NIO_READ_COUNTER_THR):
            aktuelle_chip_uid = "LEER"
            letzte_gueltige_chip_uid = "LEER"
        else:
            pass
    return temp_neue_uid, aktuelle_chip_uid # return1: Neue gültige uid / return2: chip uid der aktuellen Karte

def main():
    global program_run
    global aktuelles_musik_verzeichnis
    global aktuelle_playliste
    global aktueller_titel
    global aktueller_titel_index
    global verbindung_arduino
    MIFAREReader = MFRC522.MFRC522() # Create an object of the class MFRC522
    chip_auf_leser = 0
    spielzeit_offset = 0

    '''----------------------- Button -------------------------'''
    '''--------------------------------------------------------'''
    GPIO.setwarnings(False)
    #GPIO.setmode(GPIO.BOARD) Ist schon über MFRC522 importiert
    GPIO.setup(GPIO_PIN_ARDUINO, GPIO.OUT) #Ansteuerung Arduino
    GPIO.output(GPIO_PIN_ARDUINO, False)
    GPIO.setup(TASTER_LAUTER, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(TASTER_LEISER, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(GPIO_PIN_SHUTDOWN, GPIO.IN)
    GPIO.add_event_detect(TASTER_LAUTER, GPIO.FALLING, callback=increase_volume, bouncetime=300)
    GPIO.add_event_detect(TASTER_LEISER, GPIO.FALLING, callback=decrease_volume, bouncetime=300)
    #GPIO.add_event_detect(GPIO_PIN_SHUTDOWN, GPIO.FALLING, callback=count_shutdown, bouncetime=300)

    try:
        GPIO.output(GPIO_PIN_ARDUINO, True)
        arduino = serial.Serial('/dev/ttyUSB0', 9600)
        arduino.isOpen()
        time.sleep(2) # Alternativ 5 Sekunden, der PI versorgt den Arduino schon von Anfang an mit Strom.
        verbindung_arduino = True
        arduino.write("1")
        response = arduino.readline()
        #print response
    except:
        verbindung_arduino = False
        GPIO.output(GPIO_PIN_ARDUINO, False)
        print "Fehler bei der Verbindung zum Arduino"

    init_musikplayer()

    try:
        while program_run:
            # Auswertung des Readers
            neue_uid, chip_uid = read_chip(MIFAREReader) # temp_status is true if a new rfid chip is detected
            if ((neue_uid == True)and(check_verzeichnis(chip_uid)) == True):
                # starte Musikplayer mit neue Playliste
                if DEBUG_MODE == True:
                    print "starte Musikplayer mit neue Playliste"
                if (chip_uid == "LEER"):
                    stop_musikplayer_hart()
                else:
                    stop_musikplayer(os.path.join(aktuelles_musik_verzeichnis, NAME_LOG_DATEI), aktueller_titel, spielzeit_offset)

                aktuelles_musik_verzeichnis = os.path.join(VERZEICHNIS_DATEN, chip_uid)
                erfolgreich_gelesen, musiktyp = config2Day.get_value(os.path.join(VERZEICHNIS_DATEN, chip_uid, NAME_LOG_DATEI), "Grundeinstellung", "Typ")
                if ((erfolgreich_gelesen == True)and(musiktyp == "Hoerspiel")):
                    if DEBUG_MODE == True:
                        print "Titel ist ein Hörspiel und wird nicht gemischt"
                    aktuelle_playliste = create_playlist_sortiert(aktuelles_musik_verzeichnis)
                    erfolgreich_gelesen_1, aktueller_titel = config2Day.get_value(os.path.join(VERZEICHNIS_DATEN, chip_uid, NAME_LOG_DATEI), "Log", "letzter_titel")
                    erfolgreich_gelesen_2, spielzeit_offset = config2Day.get_value_int(os.path.join(VERZEICHNIS_DATEN, chip_uid, NAME_LOG_DATEI), "Log", "letzte_stelle")
                    if aktueller_titel == "LEER":
                        aktueller_titel = aktuelle_playliste[0]
                        aktueller_titel_index = 0
                        spielzeit_offset = 0
                    else:
                        aktueller_titel_index = aktuelle_playliste.index(aktueller_titel)
                elif ((erfolgreich_gelesen == True)and(musiktyp == "Musik")):
                    if DEBUG_MODE == True:
                        print "Titel ist ein Musikalbum und wird gemischt"
                    aktuelle_playliste = create_playlist_random(aktuelles_musik_verzeichnis)
                    aktueller_titel = random.choice(aktuelle_playliste)
                    aktueller_titel_index = aktuelle_playliste.index(aktueller_titel)
                    spielzeit_offset = 0
                else:
                    pass
                start_musikplayer(aktuelle_playliste, aktueller_titel, spielzeit_offset)
            elif ((neue_uid == True)and(check_verzeichnis(chip_uid)) == False):
                # Neuer Chip auf leser aber keine Musik vorhanden. Musikplayer stoppen.
                stop_musikplayer(os.path.join(aktuelles_musik_verzeichnis, NAME_LOG_DATEI), aktueller_titel, spielzeit_offset)

            elif (chip_uid == "LEER"):
                # Kein Chip mehr vorhanden, stoppe Musik
                stop_musikplayer(os.path.join(aktuelles_musik_verzeichnis, NAME_LOG_DATEI), aktueller_titel, spielzeit_offset)
            else:
                # Keine Veränderung und eine gültige Musikwiedergabe
                pass

            # Steuerung Musikplayer
            if ((pygame.mixer.music.get_busy() == False)and(check_verzeichnis(chip_uid) == True)):
                aktueller_titel_index = aktueller_titel_index+1
                spielzeit_offset = 0
                if aktueller_titel_index == len(aktuelle_playliste):
                    aktueller_titel_index = 0
                if DEBUG_MODE == True:
                    print "Nächster Titel"
                aktueller_titel = aktuelle_playliste[aktueller_titel_index]
                start_musikplayer(aktuelle_playliste, aktuelle_playliste[aktueller_titel_index], 0)
            else:
                pass

            # Steuerung Licht
            if(verbindung_arduino == True):
                set_licht(check_verzeichnis(chip_uid), arduino) # Übergebe die Info ob ein gültiges Verzeichnis ausgewählt ist und Musik daraus gespielt werden kann

            time.sleep(ZYKLUSZEIT_MAIN)

    except KeyboardInterrupt:
        GPIO.cleanup()
        pygame.mixer.music.stop()
        if verbindung_arduino == True:
            arduino.close()
        print "Programm beendet"

    except:
        GPIO.cleanup()
        pygame.mixer.music.stop()
        if verbindung_arduino == True:
            arduino.close()
        print "Programmfehler: " + str(sys.exc_info()[0])

if __name__ == "__main__":
    main()
