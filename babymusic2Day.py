#!/usr/bin/python
# -*- coding: utf-8 -*-
import threading # Start des Alive-Bits
import time
import os, sys
import glob, random # Playlisten erstellen
import shutil # Kopieren der Log-Datei
import subprocess # Erstellen des neuen Verzeichnisses
import RPi.GPIO as GPIO
sys.path.append('MFRC522-python')
import MFRC522, pygame
import config2Day
'''-------------------- Konfiguration ---------------------'''
'''--------------------------------------------------------'''
INIT_SOUND = False
DEBUG_MODE = True
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

INTRO_SOUND = "./data/intro.mp3"
VERZEICHNIS_DATEN = "./data" # Ablageort der Musikdateien
NAME_LOG_DATEI = "musicfile.log" # Pro Verzeichnis gibt es eine Log Datei um verschiedene Informationen zu speichern
MUSIK_FORMAT = ".mp3" # Musikformat der Musik.
VOLUME_RANGE = 0.05
VOMUME_START = 0.5

NIO_READ_COUNTER_THR = 2 # Ist ein Chip nicht lesbar wird diese Anzahl nochmal gelesen bis es auf einen unglültigen Wert gesetzt wird

'''--------------------------------------------------------'''
'''---------------------- Variablen -----------------------'''
global switch_button_mute # Variable zum einlesen des Schalters um die Lautstärketasten einzulesen
global switch_light_mute  # Variable zum einlesen des Schalters um die Lichtsteuerung ein- oder auszuschalten
nio_read_counter = 0
aktuelle_chip_uid = "LEER"
letzte_gueltige_chip_uid = "LEER"
aktuelles_musik_verzeichnis = "LEER"
aktuelle_playliste = []
aktueller_titel_index = 0
aktueller_titel = "LEER"

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
'''---------------- Musikplayer Funktionen ----------------'''
def init_musikplayer():
    pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=4096)
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
    global switch_button_mute
    if switch_button_mute == True:
        volume = pygame.mixer.music.get_volume() + VOLUME_RANGE
        pygame.mixer.music.set_volume(volume)
        print pygame.mixer.music.get_volume()
    else:
        print "Lautstärketasten sind ausgeschaltet"

def decrease_volume(ue_gpio_nummer):
    global switch_button_mute
    if switch_button_mute == True:
        volume = pygame.mixer.music.get_volume() - VOLUME_RANGE
        pygame.mixer.music.set_volume(volume)
        print pygame.mixer.music.get_volume()
    else:
        print "Lautstärketasten sind ausgeschaltet"

def mute_volume_button(ue_gpio_nummer):
    global switch_button_mute
    if switch_button_mute == True:
        switch_button_mute = False
        print "Schalter für Lautstärketasten aus"
    else:
        switch_button_mute = True
        print "Schalter für Lautstärketasten ein"

'''--------------------------------------------------------'''
'''-------------- Lichtsteuerung Funktionen ---------------'''
def mute_light(ue_gpio_nummer):
    global switch_light_mute
    if switch_light_mute == True:
        switch_light_mute = False
        print "Schalter für Lichtsteuerung war aus"
    else:
        switch_light_mute = True
        print "Schalter für Lichtsteuerung war ein"

'''--------------------------------------------------------'''
'''------------------ Support Funktionen ------------------'''
def read_config_switch():
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
        print "Neues Verzeichnis: " + str(temp_verzeichnis) + " erstellt."
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

    global aktuelles_musik_verzeichnis
    global aktuelle_playliste
    global aktueller_titel
    global aktueller_titel_index
    MIFAREReader = MFRC522.MFRC522() # Create an object of the class MFRC522
    chip_auf_leser = 0
    spielzeit_offset = 0

    read_config_switch()
    GPIO.add_event_detect(GPIO_PIN_LAUTER,GPIO.RISING,callback=increase_volume,bouncetime=800)
    GPIO.add_event_detect(GPIO_PIN_LEISER,GPIO.RISING,callback=decrease_volume,bouncetime=800)
    GPIO.add_event_detect(GPIO_PIN_BUTTON_MUTE,GPIO.BOTH,callback=mute_volume_button,bouncetime=1000)
    GPIO.add_event_detect(GPIO_PIN_LIGHT_MUTE,GPIO.BOTH,callback=mute_light,bouncetime=1000)

    try:
        t_pi_alive = threading.Thread(target=FlagPiIsAlive, args=("Pi is alive",))
        t_pi_alive.start()
        init_musikplayer()
        print "Hauptprogram start"
        while True:
            if GPIO.input(GPIO_PIN_SHUTDOWN) == GPIO.HIGH:
                pass
                #t_pi_alive.do_run = False
                #t_pi_alive.join()
                #GPIO.cleanup()
                #os.system("sudo shutdown -h now")

            neue_uid, chip_uid = read_chip(MIFAREReader) # temp_status is true if a new rfid chip is detected
            if ((neue_uid == True)and(check_verzeichnis(chip_uid)) == True):
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


            time.sleep(ZYKLUSZEIT_MAIN)

    except KeyboardInterrupt:
        t_pi_alive.do_run = False
        t_pi_alive.join()
        GPIO.cleanup()
        print "Programm beendet"

    #except:
    #    GPIO.cleanup()
    #    pygame.mixer.music.stop()
    #    print "Programmfehler: " + str(sys.exc_info()[0])

if __name__ == "__main__":
    main()
