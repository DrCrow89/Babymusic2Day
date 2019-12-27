const int ZYKLUSZEIT_MAIN = 100;               // Zykluszeit des Arduinoprogramms (nur ein grober Richtwert und natürlich abhängig vom Programm)
const int LED_ALIVE = 13;                      // Arduino und Pi alive Status LED
const int RELAIS_PI_POWER = 12;                // Relais zum einschalten des Pi
const int BUTTON_POWER = 11;                   // Button Power
const int PI_ONLINE = 10;                      // Eingang für Pi Kummunikation

const int BUTTON_PRESS_THR = 5;                // Taster muss ca. 500ms gedrückt werden, dass aktiv etwas erkannt wird.
const int BUTTON_PRESS_HARD_OFF_THR = 40;      // Taster muss ca. 4s gedrückt werden, dass der Hard-Reset erkannt wird.
const int TIMER_STARTING_TO_OFF = 150;         // Ist der Pi Status in STARTING, wird auf das Hochfahren des Pi gewartet.
const int TIMER_ON_TO_OFF = 120;               // Ist der Pi Status in ON und der Befehl kam zum Runterfahren, wird eine Zeit gewartet, bis der Pi tatsächlich heruntergefahren ist.
const int TIMER_STARTING_AFTER_HARDRESET = 30; // Nach einem Hard-Reset muss erst eine Zeit Ablaufen, dass erneut eingeschaltet werden kann.
const int TIMER_ALIVE_PI = 15;                 // Der< Pi sollte mindestens jede Sekunde (plus einen Puffer) den Status wechseln um die Kommunikation zu signalisieren.

enum piStatus
{
  PI_OFF,      // Pi ist aus,  Spannungsversorgung über Relais ist aus
  PI_STARTING, // Relais ist eingeschaltet und Pi ist am Hochfahren
  PI_ON,       // Kommunikation ist mit Pi ist vorhanden
  PI_SHUTDOWN  // Raspberry Pi hat den Befehl zum runterfahren bekommen
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
      }
      else
      {
        digitalWrite(RELAIS_PI_POWER, LOW);
        if(restart_after_hardreset > 0)
        {
          restart_after_hardreset = restart_after_hardreset - 1;
        }
      }
    break;

    case PI_STARTING:
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
        //TODO: Setze GPIO für Pi zum herunterfahren
        release_button_to_con = 0;
        status_pi = PI_SHUTDOWN;
      }
    break;

    case PI_SHUTDOWN:
      if(counter_shutdown_pi < TIMER_ON_TO_OFF)
      {
        counter_shutdown_pi = counter_shutdown_pi + 1;
      }
      else
      {
        Serial.print("PI ausschalten, da er heruntergefahren wurde\n");
        status_pi = PI_OFF;
      }
      if(button_counter_power > BUTTON_PRESS_HARD_OFF_THR)
      {
        Serial.print("PI ausschalten, da Hard-Reset\n");
        restart_after_hardreset = TIMER_STARTING_AFTER_HARDRESET;
        release_button_to_con = 0;
        status_pi = PI_OFF;
      }
    break;
  }
}

void setup()
{
  Serial.begin(9600);
  // initialize the button pins as an input:
  pinMode(BUTTON_POWER, INPUT_PULLUP);
  // initialize the relais pins as an output:
  pinMode(RELAIS_PI_POWER, OUTPUT);
  // initialize pin for communication with PI as an input:
  pinMode(PI_ONLINE, INPUT);
  pinMode(LED_ALIVE, OUTPUT);
  // Wird der Arduino gestartet, ist das Relais immer aus
  status_pi = PI_OFF;
}

void loop()
{
  button_state_power = digitalRead(BUTTON_POWER);
  check_button_power();
  check_status_pi();
  check_commun_pi();
  /*
   * Zykluszeit des Programms muss begrenzt werden.
   * Manuelle Messung hat gepasst. 10s waren 101 Zyklen.
   */
  delay(ZYKLUSZEIT_MAIN);
}
