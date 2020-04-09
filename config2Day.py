# !/usr/bin/env python
# -*- coding:utf-8 -*-
import os, ConfigParser

Config = ConfigParser.ConfigParser()

def check_log_file(ue_pfad_datei):
    #Config = ConfigParser.ConfigParser()
    if not os.path.isfile(ue_pfad_datei):
        cfgfile = open(ue_pfad_datei,'w')
        Config.add_section('Grundeinstellung')
        Config.set('Grundeinstellung', 'Typ', 'Hoerspiel') # Hoerspiel/Musik
        Config.set('Grundeinstellung', 'Name', 'Testhoerspiel')
        Config.add_section('Log')
        Config.set('Log', 'letzter_titel', 'LEER')
        Config.set('Log', 'letzte_stelle', '0')
        Config.set('Log', 'zaehler_abgespielt', '0')
        Config.set('Log', 'gesamt_spielzeit', '0')
        Config.write(cfgfile)
        cfgfile.close()

def check_section(ue_pfad_datei, ue_section):
    if os.path.isfile(ue_pfad_datei):
        #Config = ConfigParser.ConfigParser()
        Config.read(ue_pfad_datei)
        if Config.has_section(ue_section):
            return True
        else:
            return False
    else:
        return False

def get_value_int(ue_pfad_datei, ue_section, ue_option):
    if check_section(ue_pfad_datei, ue_section):
        #Config = ConfigParser.ConfigParser()
        Config.read(ue_pfad_datei)
        try:
            return True, Config.getint(ue_section, ue_option)
        except ValueError:
            #print("Der Wert ist keine Zahl")
            return False, 0
    else:
        return False, 0

def get_value_float(ue_pfad_datei, ue_section, ue_option):
    if check_section(ue_pfad_datei, ue_section):
        #Config = ConfigParser.ConfigParser()
        Config.read(ue_pfad_datei)
        try:
            return True, Config.getfloat(ue_section, ue_option)
        except ValueError:
            #print("Der Wert ist keine Zahl")
            return False, 0
    else:
        return False, 0

# True == [1, yes, true, on] // False == [0, no, false, off]
def get_value_boolean(ue_pfad_datei, ue_section, ue_option):
    if check_section(ue_pfad_datei, ue_section):
        #Config = ConfigParser.ConfigParser()
        Config.read(ue_pfad_datei)
        try:
            return True, Config.getboolean(ue_section, ue_option)
        except ValueError:
            #print("Der Wert ist kein Boolean")
            return False, 0
    else:
        return False, 0

def get_value(ue_pfad_datei, ue_section, ue_option):
    if check_section(ue_pfad_datei, ue_section):
        #Config = ConfigParser.ConfigParser()
        Config.read(ue_pfad_datei)
        try:
            return True, Config.get(ue_section, ue_option)
        except ConfigParser.Error:
            return False, 0
    else:
        return False, 0

def set_value(ue_path, ue_section, ue_option, ue_value):
    try:
        cfgfile = open(ue_path,'w')
        Config.set(ue_section, ue_option, ue_value)
        Config.write(cfgfile)
        cfgfile.close()
    except ValueError:
        pass

def main():
    path = "./data/musicfile.log"
    check_log_file(path)
    #######################################
    if check_section(path, 'Grundeinstellung') == True:
        print "Section Grundeinstellung ist vorhanden"
    else:
        print "Section Grundeinstellung ist nicht vorhanden"
    #######################################
    if check_section(path, 'Log') == True:
        print "Section Log ist vorhanden"
    else:
        print "Section Log ist nicht vorhanden"
    #######################################
    erfolgreich, wert = get_value_int(path, "Log", "letzte_stelle")
    if erfolgreich:
        print "Der int-Wert: " + str(wert) + " vom Typ: " + str(type(wert))
    else:
        print "Kein int-Wert"
    #######################################
    set_value(path, "Log", "letzte_stelle", "987")
    erfolgreich, wert = get_value_int(path, "Log", "letzte_stelle")
    if erfolgreich:
        print "Der int-Wert: " + str(wert) + " vom Typ: " + str(type(wert))
    else:
        print "Kein int-Wert"
    #######################################
    erfolgreich, wert = get_value_float(path, "Log", "letzte_stelle")
    if erfolgreich:
        print "Der float-Wert: " + str(wert) + " vom Typ: " + str(type(wert))
    else:
        print "Kein float-Wert"
    #######################################
    erfolgreich, wert = get_value(path, "Grundeinstellung", "Typ")
    if erfolgreich:
        print "Der Bool-Wert: " + str(wert) + " vom Typ: " + str(type(wert))
    else:
        print "Kein Bool-Wert"
    #######################################
    erfolgreich, wert = get_value(path, "Log", "letzter_titel")
    if erfolgreich:
        print "Der Wert: " + str(wert) + " vom Typ: " + str(type(wert))
    else:
        print "Kein Wert"
    #######################################
    print "Beendet"

if __name__ == '__main__':
    main()
