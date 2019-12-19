const int LED_ALIVE = 13;                 // Arduino und Pi alive Status LED
const int RELAIS_PI_POWER = 12;           // Relais zum einschalten des Pi
const int BUTTON_POWER = 11;              // Button Power

const int PI_ONLINE = 2;                  // Eingang für Pi Kummunikation
const int TIMER_POWER_ON_THR = 300;       // Nach einem Hard-Reset soll es 3s nicht möglich sein einzuschalten.
const int TIMER_POWER_OFF_THR = 400;      // Der Taster muss 4 Sekunden Gedrückt werden um einen Hard-Reset zu machen.
const int TIMER_ALIVE_PI = 2500;          // Der Pi braucht ca. XX Sekunden um herunterzufahren.
const int STARTUP_PI_THR = 2000;          // Der Pi braucht ca. 14 Sekunden um das Kommunikationsskript zu starten.
const int TIMER_LED_BLINK = 100;          // Die LEDs sollen jeweils im 1 Sekunden Rhythmus blinken.

int button_state_power = 0;               // Temp. Einlese-Variable für Power Button
unsigned long button_counter_power = 0;   // Counter Power Button betätigt Variable
int timer_power_on = 0;                   // Einschalten am Anfang ist möglich
int pi_power_on = 0;                      // Raspberry Pi ist am Anfang aus

/* ------------------------------------------------------------------------------------------ */
/* ------------------------------------------------------------------------------------------ */
/* --------------------- Kommunikation von Arduino und dem Raspberry Pi --------------------- */
/* ------------------------------------------------------------------------------------------ */
int input_alive_pi = 0;                   // Input für die Kommunikation mit dem PI
int startup_pi_counter = 0;               // Counter um den Pi hochfahren zu lassen
int timer_h = 0;                          // Ablaufzähler für HIGH-Level from Pi
int timer_l = 0;                          // Ablaufzähler für LOW-Level from Pi
/* ------------------------------------------------------------------------------------------ */

void check_pi_online()
{
  input_alive_pi = digitalRead(PI_ONLINE);
  if(  (pi_power_on == 1)
     &&(startup_pi_counter < STARTUP_PI_THR)
    )
  {
    //if(var_print_5 != 1){Serial.print("Pi wird hochgefahren\n");var_print_5 = 1;}
    startup_pi_counter ++;
  }
  else if(  (pi_power_on == 1)
          &&(startup_pi_counter == STARTUP_PI_THR)
         )
  {
    //if(var_print_4 != 1){Serial.print("Pi ist hochgefahren\n");var_print_4 = 1;}
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
      digitalWrite(RELAIS_PI_POWER, LOW);
      pi_power_on = 0;
      //if(var_print_3 != 1){Serial.print("Pi herunterfahren\n");var_print_3 = 1;}
    }
  }
  else
  {
    startup_pi_counter = 0;
    timer_l = 0;
    timer_h = 0;
  }
}

void check_button_power()
{
  if(button_state_power == LOW)
  {
    button_counter_power = button_counter_power +1;
    //Serial.print(button_counter_power);
    if(button_counter_power > TIMER_POWER_OFF_THR)
    {
      Serial.print("Hard reset:\n");
      button_counter_power = 0;
      timer_power_on = TIMER_POWER_ON_THR;
      pi_power_on = 0;
      digitalWrite(RELAIS_PI_POWER, LOW);
    }
  }
  else
  {
    if(  (button_counter_power > 0)
       &&(button_counter_power < TIMER_POWER_OFF_THR)
       &&(timer_power_on == 0) //Zeit nach hard-reset ist abgelaufen
       &&(pi_power_on == 0) // Pi ist aus
      )
      {
         Serial.print("Power ON\n");
         //Serial.print(button_counter_power);
         button_counter_power = 0;
         pi_power_on = 1;
         digitalWrite(RELAIS_PI_POWER, HIGH);
      }
      /* Wenn der Button wieder losgelassen wird, soll der Counter zurückgesetzt werden.
       * Sonst kann der Button mehrmals hintereinander gedrückt werden und der Pi wird
       * dann aus gemacht.
       */
      else
      {
         button_counter_power = 0;
      }

     if(timer_power_on > 0)
     {
        timer_power_on = timer_power_on -1;
        button_counter_power = 0;
     }
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
}

void loop()
{
  button_state_power = digitalRead(BUTTON_POWER);
  check_button_power();
  check_pi_online();
  /*
   * Zykluszeit des Programms muss begrenzt werden.
   * Manuelle Messung hat gepasst. 10s waren 101 Zyklen.
   */
  delay(10);
}
