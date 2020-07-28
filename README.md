# Babymusic2Day
I build my own Jukebox for my daughter. An Arduino is responsible for light (RGB lights) and powering up and down. The Raspberry for playing music. 

## Features
- Own powermanagement, start Pi with button and shut it down again in a controlled manner with the same button
- Light display (Start system --> running lights in blue, online --> permanently green, music plays --> pulsing green)
- If the figure is taken off the field, the music stops.
- Music always starts randomly. Audio books always start from the last finished point.
- Count all played titel and how long the figure stood on the field

# known bugs
* Start des Musikplayers mit ungültiger/nicht möglicher Startzeit

# ToDo
- [ ] MUSIK_FORMAT mit mehr als nur mp3 füllen. Idee wäre das mit "|" erweitern.
- [ ] Erstellen der Playlist die Wildcard ersetzen, dass auch hier MUSIK_FORMAT benmutzt werden kann.
- [ ] Thread erstellen, welcher die Zeit misst und nach 10 Minuten die Pi runterfährt, wenn keine Titel mehr gespielt werden. (Erstmal nicht, da nur die Eltern die Box hoch und runterfahren sollen und für die Tochter die Box die ganze Zeit an bleibt.)
- [ ] Konfigurationen wie z.B. ob der init-sound abgespielt wird in eine allgemeine config Datei auslagern.
- [ ] Handler für Reader und Musikplayer auslagern.
- [ ] Error-Handling erstellen und Fehlerdatei beschreiben.
- [ ] Button-Handling in Modul auslagern.
