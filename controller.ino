#include "FastLED.h"

#define NUM_LEDS 4
#define DATA_PIN 2
#define CLOCK_PIN 3

const int ZYKLUSZEIT_MAIN = 100;               // Zykluszeit des Arduinoprogramms (nur ein grober Richtwert und natürlich abhängig vom Programm)
const int LED_ALIVE = 13;                      // Pin Arduino und Pi alive Status LED
const int RELAIS_PI_POWER = 12;                // Pin Relais zum einschalten des Pi
const int BUTTON_POWER = 11;                   // Pin Button Power
const int BUTTON_POWER_LED = 10;               // Pin LED Licht des Button Power
const int PI_ONLINE = 9;                       // Pin Eingang für Pi Kummunikation
const int S_COMMAND_PI_SHUTDOWN = 8;           // Pin zum senden des shutdown-Befehls an den Pi
const int R_MUSIC_PLAY = 5;                    // Pin zum empfangen ob Musik abgespielt wird
const int R_LIGHT_MUTE = 4;                    // Pin zum empfangen ob das Licht angezeigt werden soll oder nicht

const int BUTTON_PRESS_THR = 5;                // Taster muss ca. 500ms gedrückt werden, dass aktiv etwas erkannt wird.
const int BUTTON_PRESS_HARD_OFF_THR = 40;      // Taster muss ca. 4s gedrückt werden, dass der Hard-Reset erkannt wird.
const int TIMER_STARTING_TO_OFF = 150;         // Ist der Pi Status in STARTING, wird auf das Hochfahren des Pi gewartet.
const int TIMER_ON_TO_OFF = 120;               // Ist der Pi Status in ON und der Befehl kam zum Runterfahren, wird eine Zeit gewartet, bis der Pi tatsächlich heruntergefahren ist.
const int TIMER_STARTING_AFTER_HARDRESET = 30; // Nach einem Hard-Reset muss erst eine Zeit Ablaufen, dass erneut eingeschaltet werden kann.
const int TIMER_ALIVE_PI = 15;                 // Der Pi sollte mindestens jede Sekunde (plus einen Puffer) den Status wechseln um die Kommunikation zu signalisieren.

enum piStatus
{
  PI_OFF,      // Pi ist aus,  Spannungsversorgung über Relais ist aus
  PI_STARTING, // Relais ist eingeschaltet und Pi ist am Hochfahren
  PI_ON,       // Kommunikation ist mit Pi ist vorhanden
  PI_SHUTDOWN  // Raspberry Pi hat den Befehl zum runterfahren bekommen
};

enum piLightStatus
{
  LIGHT_OFF,
  LIGHT_INIT,
  LIGHT_ON,
  LIGHT_MUSIC_PLAY,
  LIGHT_SHUTDOWN
};

/* ------------------------------------------------------------------------------------------ */
/* ------------------------------------------------------------------------------------------ */
/* --------------------- Kommunikation von Arduino und dem Raspberry Pi --------------------- */
/* ------------------------------------------------------------------------------------------ */
int input_alive_pi = 0;                   // Input für die Kommunikation mit dem PI
int startup_pi_counter = 0;               // Counter um den Pi hochfahren zu lassen
int counter_lost_comm = 0;                // Counter um den Pi ordentlich herunter zu fahren, nachdem die Kommunikation nicht mehr vorhanden ist
int counter_shutdown_pi = 0;              // Wird der Taster gedrückt, wenn der Pi online ist, wird der Befehl gegeben zum herunterfahren und der Timer zum Ausschalten gestartet
int timer_h = TIMER_ALIVE_PI;             // Ablaufzähler für HIGH-Level from Pi
int timer_l = TIMER_ALIVE_PI;             // Ablaufzähler für LOW-Level from Pi
int communication_pi_activ = 0;           // Am Anfang kann noch keine Kommunikation mit dem PI stattfinden
enum piStatus status_pi;                  // Aktueller Status des Raspberry Pi
enum piLightStatus status_light;          // Aktueller Status der Lichtsteuerung
CRGB leds[NUM_LEDS];
/* ------------------------------------------------------------------------------------------ */
/* ------------------------------------------------------------------------------------------ */
/* ---------------------------------------- Variablen --------------------------------------- */
/* ------------------------------------------------------------------------------------------ */
int button_state_power = 0;               // Temp. Einlese-Variable für Power Button
unsigned long button_counter_power = 0;   // Counter Power Button betätigt Variable
int restart_after_hardreset = 0;          // Nach einem Hard-Reset muss erst eine Zeit Ablaufen, dass erneut eingeschaltet werden kann.
int release_button_to_con = 1;            // Nach einem Hard-Reset muss der Butten zuerst einmal losgelassen werden, dass erneut gestartet werden kann.
/* ------------------------------------------------------------------------------------------ */
/* ------------------------------------------------------------------------------------------ */
/* ------------------------------ Variablen für die Lichtsteuerung--------------------------- */
/* ------------------------------------------------------------------------------------------ */
const int MAX_HELLIGKEIT = 128; // 256 = 100% --> 80 = ca. 30% --> 128 = 50%
const int TIME_BETWEEN_LED = 3;  // 3 Zyklen zwischen dem LED wechsel beim Init-Prozess
int schleifen_zaehler_licht = 0;
int aktuelle_led = 0;
int aktuelle_helligkeit = 0;
int richtung_dimmen_licht = 0; // Soll gerade hochgedimmt werden oder herunter beim Musikabspielen. 0-->runterdimmen, 1-->hochdimmen
int licht_ausschalten = 0;
/* ------------------------------------------------------------------------------------------ */
/* ------------------------------------------------------------------------------------------ */
/* ---------------------------------------- Programm ---------------------------------------- */
/* ------------------------------------------------------------------------------------------ */
void check_button_power()
{
  if(button_state_power == LOW)
  {
    button_counter_power = button_counter_power +1;
  }
  else
  {
    button_counter_power = 0;
    release_button_to_con = 1;
  }
}

void check_commun_pi()
{
  input_alive_pi = digitalRead(PI_ONLINE);
  if(input_alive_pi == HIGH)
  {
    digitalWrite(LED_ALIVE, HIGH);
    if(timer_h < TIMER_ALIVE_PI)
    {
      timer_h ++;
    }
    timer_l = 0;
  }
  else
  {
    digitalWrite(LED_ALIVE, LOW);
    if(timer_l < TIMER_ALIVE_PI)
    {
      timer_l ++;
    }
    timer_h = 0;
  }
  if((timer_l == TIMER_ALIVE_PI)||(timer_h == TIMER_ALIVE_PI))
  {
    communication_pi_activ = 0;
  }
  else
  {
    communication_pi_activ = 1;
  }
  //Serial.print("Timer L: ");Serial.print(timer_l);Serial.print(" und Timer H: ");Serial.print(timer_h);Serial.print(" --> ALIVE: ");Serial.print(communication_pi_activ);Serial.print("\n");
}

void check_status_pi()
{
  switch (status_pi)
  {
    case PI_OFF:
      status_light = LIGHT_OFF;
      startup_pi_counter = 0;
      counter_lost_comm = 0;
      counter_shutdown_pi = 0;

      if(  (button_counter_power > BUTTON_PRESS_THR) // Button lang genug gedrückt zum starten
         &&(restart_after_hardreset == 0) // Kein Einschalten direkt nach einem Hard-Reset
         &&(release_button_to_con == 1)
        )
      {
        Serial.print("Starte PI\n");
        status_pi = PI_STARTING;
        digitalWrite(RELAIS_PI_POWER, HIGH);
        digitalWrite(BUTTON_POWER_LED, HIGH);
      }
      else
      {
        digitalWrite(RELAIS_PI_POWER, LOW);
        digitalWrite(BUTTON_POWER_LED, LOW);
        if(restart_after_hardreset > 0)
        {
          restart_after_hardreset = restart_after_hardreset - 1;
        }
      }
    break;

    case PI_STARTING:
      status_light = LIGHT_INIT;
      // Kommunikation mit dem Pi ist da
      if(communication_pi_activ == 1)
      {
        Serial.print("PI ist online\n");
        release_button_to_con = 0;
        status_pi = PI_ON;
      }
      // Kommunikation noch nicht vorhanden, warten bis Timer abgelaufen ist zum ausschalten
      else if(startup_pi_counter == TIMER_STARTING_TO_OFF)
      {
        Serial.print("PI ausschalten, da Timer abgelaufen\n");
        status_pi = PI_OFF;
      }
      // Hard-Reset erkannt
      else if(  (button_counter_power > BUTTON_PRESS_HARD_OFF_THR)
              &&(release_button_to_con == 1)
             )
      {
        Serial.print("PI ausschalten, da Hard-Reset\n");
        restart_after_hardreset = TIMER_STARTING_AFTER_HARDRESET;
        release_button_to_con = 0;
        status_pi = PI_OFF;
      }
      else
      {
        startup_pi_counter = startup_pi_counter +1;
      }
    break;

    case PI_ON:
      if(digitalRead(R_MUSIC_PLAY) == HIGH)
      {
        status_light = LIGHT_MUSIC_PLAY;
      }
      else
      {
        status_light = LIGHT_ON;
      }
      // Keine Kommunikation mehr vorhanden. Pi wird eventuell heruntergefahren oder hat sich aufgehangen
      if(  (communication_pi_activ == 0)
         &&(counter_lost_comm < TIMER_ON_TO_OFF)
        )
      {
        counter_lost_comm = counter_lost_comm + 1;
      }
      else // Kommunikation weiterhin vorhanden
      {
        counter_lost_comm = 0;
      }
      if(counter_lost_comm == TIMER_ON_TO_OFF) // Timer abgelaufen, Pi ausschalten
      {
        Serial.print("PI ausschalten, da aufgehangen\n");
        status_pi = PI_OFF;
      }

      if(  (button_counter_power > BUTTON_PRESS_THR) // Button lang genug gedrückt um herunter zu fahren
         &&(release_button_to_con == 1)
        )
      {
        Serial.print("PI runterfahren lassen\n");
        release_button_to_con = 0;
        digitalWrite(S_COMMAND_PI_SHUTDOWN, HIGH);
        status_pi = PI_SHUTDOWN;
      }
    break;

    case PI_SHUTDOWN:
      status_light = LIGHT_SHUTDOWN;
      if(counter_shutdown_pi < TIMER_ON_TO_OFF)
      {
        counter_shutdown_pi = counter_shutdown_pi + 1;
      }
      else
      {
        Serial.print("PI ausschalten, da er heruntergefahren wurde\n");
        digitalWrite(S_COMMAND_PI_SHUTDOWN, LOW);
        status_pi = PI_OFF;
      }
      if(button_counter_power > BUTTON_PRESS_HARD_OFF_THR)
      {
        Serial.print("PI ausschalten, da Hard-Reset\n");
        digitalWrite(S_COMMAND_PI_SHUTDOWN, LOW);
        restart_after_hardreset = TIMER_STARTING_AFTER_HARDRESET;
        release_button_to_con = 0;
        status_pi = PI_OFF;
      }
    break;
  }
}

void check_status_light()
{
  switch (status_light)
  {
    case LIGHT_OFF:
      FastLED.setBrightness(0);
      for(int i = 0; i < NUM_LEDS; i++)
      {
        leds[i] = CRGB(0, 0, 0);
      }
      FastLED.show();
    break;
    case LIGHT_INIT:
      FastLED.setBrightness(MAX_HELLIGKEIT);
      if(schleifen_zaehler_licht < TIME_BETWEEN_LED)
      {
        schleifen_zaehler_licht = schleifen_zaehler_licht +1;
      }
      else
      {
        leds[aktuelle_led] = CRGB(0, 0, 255);
        FastLED.show();
        leds[aktuelle_led] = CRGB(0, 0, 0);
        if(aktuelle_led < NUM_LEDS -1)
        {
          aktuelle_led = aktuelle_led +1;
        }
        else
        {
          aktuelle_led = 0;
        }
        schleifen_zaehler_licht = 0;
      }
    break;
    case LIGHT_ON:
      for(int i = 0; i < NUM_LEDS; i++)
      {
        leds[i] = CRGB(0, 255, 0);
      }
      if(aktuelle_helligkeit < MAX_HELLIGKEIT)
      {
        aktuelle_helligkeit = aktuelle_helligkeit +1;
        FastLED.setBrightness(aktuelle_helligkeit);
        FastLED.show();
      }
    break;
    case LIGHT_MUSIC_PLAY:
      if(richtung_dimmen_licht == 0) //runterdimmen
      {
        aktuelle_helligkeit = aktuelle_helligkeit -4;
        if(aktuelle_helligkeit > 4)
        {
          FastLED.setBrightness(aktuelle_helligkeit);
          FastLED.show();
        }
        else
        {
          richtung_dimmen_licht = 1;
        }
      }
      else //hochdimmen
      {
        aktuelle_helligkeit = aktuelle_helligkeit +4;
        if(aktuelle_helligkeit < MAX_HELLIGKEIT)
        {
          FastLED.setBrightness(aktuelle_helligkeit);
          FastLED.show();
        }
        else
        {
          richtung_dimmen_licht = 0;
        }
      }
    break;
    case LIGHT_SHUTDOWN:
      for(int i = 0; i < NUM_LEDS; i++)
      {
        leds[i] = CRGB(255, 0, 0);
      }
      if(aktuelle_helligkeit > 0)
      {
        aktuelle_helligkeit = aktuelle_helligkeit -1;
        FastLED.setBrightness(aktuelle_helligkeit);
        FastLED.show();
      }
    break;
  }
}
void setup()
{
  Serial.begin(9600);
  FastLED.addLeds<WS2801, DATA_PIN, CLOCK_PIN, RGB>(leds, NUM_LEDS);
  pinMode(BUTTON_POWER, INPUT_PULLUP);
  pinMode(BUTTON_POWER_LED, OUTPUT);
  digitalWrite(BUTTON_POWER_LED, LOW);
  pinMode(RELAIS_PI_POWER, OUTPUT);
  digitalWrite(RELAIS_PI_POWER, LOW);
  pinMode(PI_ONLINE, INPUT);
  pinMode(LED_ALIVE, OUTPUT);
  digitalWrite(LED_ALIVE, LOW);
  pinMode(S_COMMAND_PI_SHUTDOWN, OUTPUT);
  digitalWrite(S_COMMAND_PI_SHUTDOWN, LOW);
  pinMode(R_MUSIC_PLAY, INPUT);
  pinMode(R_LIGHT_MUTE, INPUT);
  status_pi = PI_OFF; // Wird der Arduino gestartet, ist das Relais immer aus
  status_light = LIGHT_OFF; // Wird der Arduino gestartet, ist das Licht aus
  Serial.print("Start\n");
}

void loop()
{
  button_state_power = digitalRead(BUTTON_POWER);
  check_button_power();
  check_status_pi();
  check_commun_pi();
  if(digitalRead(R_LIGHT_MUTE) == HIGH)
  {
    check_status_light();
    licht_ausschalten = 1;
  }
  else
  {
    if(licht_ausschalten == 1)
    {
      for(int i = 0; i < NUM_LEDS; i++)
      {
        leds[i] = CRGB(0, 0, 0);
      }
      FastLED.show();
    }
  }

  /*
   * Zykluszeit des Programms muss begrenzt werden.
   * Manuelle Messung hat gepasst. 10s waren 101 Zyklen.
   */
  delay(ZYKLUSZEIT_MAIN);
}
