#include "FastLED.h"

#define NUM_LEDS 4
#define DATA_PIN 3
#define CLOCK_PIN 13

const int MAX_HELLIGKEIT = 128; // 256 = 100% --> 80 = ca. 30% --> 128 = 50%
const int MAX_HELLIGKEIT_TIME = 20; // 256 = 20 --> 80 = 40 --> 128 = 20
const int INIT_LOOPS = 5;

int musik_laeuft = 0;
int do_nothing = 0;
int akt_hell = 0;

// Define the array of leds
CRGB leds[NUM_LEDS];

void set_color(int ue_red, int ue_green, int ue_blue)
{
  for(int i = 0; i < NUM_LEDS; i++)
  {
    leds[i] = CRGB(ue_red, ue_green, ue_blue);
    delay(1);
  }
}

void pulsieren()
{
  for(int j = 4; j < MAX_HELLIGKEIT; j++)
  {
    // Hochdimmen
    FastLED.setBrightness(j);
    FastLED.show();
    delay(MAX_HELLIGKEIT_TIME);
  }
  for(int j = MAX_HELLIGKEIT-1; j > 4; j--)
  {
    // Runterdimmen
    FastLED.setBrightness(j);
    FastLED.show();
    delay(MAX_HELLIGKEIT_TIME);
  }
}

void licht_0_to_max()
{
  for(int j = 1; j < MAX_HELLIGKEIT; j++)
  {
    // Hochdimmen
    FastLED.setBrightness(j);
    FastLED.show();
    delay(MAX_HELLIGKEIT_TIME);
  }
  akt_hell = 1;
}

void licht_max_to_0()
{
  for(int j = MAX_HELLIGKEIT-1; j > 1; j--)
  {
    // Runterdimmen
    FastLED.setBrightness(j);
    FastLED.show();
    delay(MAX_HELLIGKEIT_TIME);
  }
  akt_hell = 0;
}

void licht_off()
{
  set_color(0, 0, 0);
  FastLED.show();
}

void licht_init()
{
  FastLED.setBrightness(MAX_HELLIGKEIT);
  for(int i = 0; i < INIT_LOOPS; i++)
  {
    for(int dot = 0; dot < NUM_LEDS; dot++)
    {
      leds[dot] = CRGB(0, 0, 255);
      FastLED.show();
      leds[dot] = CRGB(0, 0, 0);
      delay(300);
    }
  }
  licht_off();
  set_color(0, 255, 0);
  licht_0_to_max();
}

void setup()
{
  FastLED.addLeds<WS2801, DATA_PIN, CLOCK_PIN, RGB>(leds, NUM_LEDS);
  Serial.begin(9600);
  licht_off();
}

void loop()
{
  if(Serial.available())
  {
    byte empfangen = Serial.read();
    if(empfangen == 49) // Initialisieren
    {
      musik_laeuft = 0;
      Serial.println("1");
      licht_init();
    }
    else if(empfangen == 48) // Licht hart aus
    {
      musik_laeuft = 0;
      licht_off();
      Serial.println("0");
    }
    else if(empfangen == 50) // Musik wird abgespielt
    {
      musik_laeuft = 1;
      Serial.println("2");
      licht_max_to_0();
    }
    else if(empfangen == 51) // Sicht auf runterdimmen
    {
      Serial.println("3");
      musik_laeuft = 0;
      set_color(0, 255, 0);
      licht_max_to_0();
      licht_off();
    }
    else if(empfangen == 52) // Sicht auf hochdimmen
    {
      Serial.println("4");
      musik_laeuft = 0;
      set_color(0, 255, 0);
      licht_0_to_max();
    }
    else
    {
      Serial.println(empfangen);
    }
  }

  if(  (musik_laeuft == 1)
     &&(akt_hell == 0)
    )
  {
    set_color(0, 255, 0);
    licht_0_to_max();
  }
  if(  (musik_laeuft == 1)
     &&(akt_hell == 1)
    )
  {
    set_color(0, 255, 0);
    licht_max_to_0();
  }
  do_nothing = 0;
  delay(10);
}
