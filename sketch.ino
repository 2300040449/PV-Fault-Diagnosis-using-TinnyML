/**
 * ============================================================================
 * PROJECT TITLE:
 * PV Fault Diagnosis Without Thermal Camera Using Mathematical PV Modeling
 *
 * PLATFORM:
 * ESP32-S3 DevKitC-1 | Arduino Framework | Wokwi Simulation
 *
 * DESCRIPTION:
 * High-fidelity mathematical digital twin of a Photovoltaic (PV) array.
 * Translates physical inputs (irradiance from potentiometer, ambient temperature
 * and humidity from DHT22) into realistic electrical parameters (V, I, P, Tpv)
 * across four distinct operating modes:
 *   MODE 0: NORMAL
 *   MODE 1: PARTIAL SHADING
 *   MODE 2: OPEN CIRCUIT
 *   MODE 3: OVER TEMPERATURE
 *
 * Features:
 *   - Deterministic single-diode/STC-based mathematical PV model
 *   - Non-blocking millis() scheduler (sample interval: 1000 ms)
 *   - Clean, machine-readable CSV telemetry stream for dataset collection
 *   - Optional human-readable Serial diagnostics (CSV_MODE toggle)
 *   - Hardware-debounced push-button fault mode selector (GPIO 13)
 *   - Fault indicator LED driver (GPIO 2)
 *   - SSD1306 128x64 OLED diagnostic dashboard (GPIO 8 SDA, GPIO 9 SCL)
 * ============================================================================
 */

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <DHTesp.h>

// ============================================================================
// CONFIGURATION FLAGS & SCHEDULER INTERVALS
// ============================================================================
#define CSV_MODE true                          // true = Clean CSV output; false = Diagnostic text
static const unsigned long SAMPLE_INTERVAL = 1000; // Telemetry sampling rate (ms)
static const unsigned long OLED_INTERVAL   = 500;  // OLED refresh period (ms)
static const unsigned long DEBOUNCE_DELAY  = 50;   // Button debounce window (ms)

// ============================================================================
// HARDWARE PIN ASSIGNMENTS (Preserved exact wiring)
// ============================================================================
#define POT_PIN        1   // Potentiometer SIG (Irradiance G: 0 - 1000 W/m2)
#define DHT_PIN        4   // DHT22 DATA (Ambient Temperature & Humidity)
#define OLED_SDA       8   // SSD1306 I2C SDA
#define OLED_SCL       9   // SSD1306 I2C SCL
#define BUTTON_PIN    13   // Fault-mode push button (Active LOW, INPUT_PULLUP)
#define LED_PIN        2   // Red fault indicator LED

// ============================================================================
// OLED DISPLAY CONSTANTS
// ============================================================================
#define SCREEN_WIDTH  128
#define SCREEN_HEIGHT  64
#define OLED_RESET     -1
#define OLED_ADDR    0x3C

// ============================================================================
// MATHEMATICAL PV MODEL REFERENCE CONSTANTS (STC: 1000 W/m2, 25 deg C)
// ============================================================================
static const float Gref                = 1000.0f; // Reference Irradiance (W/m2)
static const float Tref                = 25.0f;   // Reference Temperature (deg C)
static const float Vmp_ref             = 18.0f;   // Maximum Power Point Voltage (V)
static const float Imp_ref             = 2.7f;    // Maximum Power Point Current (A)
static const float Voc_ref             = 21.6f;   // Open Circuit Voltage at STC (V)
static const float beta_V              = -0.004f; // Voltage Temperature Coefficient (1/deg C)
static const float SHADING_FACTOR      = 0.45f;   // Photocurrent ratio under partial shade
static const float TEMP_RISE_OVER_TEMP = 35.0f;   // Temperature rise under thermal fault (deg C)

// ============================================================================
// DATA TYPES & ENUMERATIONS
// ============================================================================
enum FaultMode {
  NORMAL = 0,
  PARTIAL_SHADING = 1,
  OPEN_CIRCUIT = 2,
  OVER_TEMPERATURE = 3
};

struct PVParameters {
  float irradiance;     // G (W/m2)
  float humidity;       // H (%)
  float ambientTemp;    // Ta (deg C)
  float pvTemp;         // Tpv (deg C)
  float voltage;        // V (V)
  float current;        // I (A)
  float power;          // P (W)
  FaultMode mode;       // Operating condition
};

// ============================================================================
// GLOBAL OBJECTS & STATE VARIABLES
// ============================================================================
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
DHTesp dht;

bool oledAvailable = false;
FaultMode currentMode = NORMAL;
PVParameters pvData = {0.0f, 50.0f, 25.0f, 25.0f, 0.0f, 0.0f, 0.0f, NORMAL};

// Sensor smoothing and cached fallbacks
float filteredIrradiance = 0.0f;
float lastValidAmbientTemp = 25.0f;
float lastValidHumidity = 50.0f;

// Button debounce tracking
int lastButtonReading = HIGH;
int buttonState = HIGH;
unsigned long lastDebounceTime = 0;

// Non-blocking timers
unsigned long lastSampleTime = 0;
unsigned long lastOledTime = 0;

// ============================================================================
// FORWARD DECLARATIONS (Modular Architecture)
// ============================================================================
void calculatePVModel(float G, float Ta, float &V, float &I, float &P, float &Tpv);
void applyFaultModel(FaultMode mode, float G, float Ta, float &V, float &I, float &P, float &Tpv);
const char* classifyFault(FaultMode mode);
const char* getOledFaultText(FaultMode mode);
void updateOLED();
void updateFaultLED();
void handleButton();
void logCSV();
void printDiagnosticText();
void readSensors();
float readIrradiance();
void readDHT22();
void displaySplashScreen();

// ============================================================================
// ARDUINO SETUP
// ============================================================================
void setup() {
  Serial.begin(115200);

  // Initialize GPIOs
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW); // LED OFF in NORMAL mode
  pinMode(BUTTON_PIN, INPUT_PULLUP);

  // Initialize DHT22
  dht.setup(DHT_PIN, DHTesp::DHT22);

  // Initialize OLED (I2C SDA=8, SCL=9)
  Wire.begin(OLED_SDA, OLED_SCL);
  if (!display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR)) {
    Serial.println(F("ERROR: OLED initialization failed"));
    oledAvailable = false;
  } else {
    oledAvailable = true;
    displaySplashScreen();
  }

  // Print system header or CSV header
  if (CSV_MODE) {
    Serial.println(F("CSV_DATA_START"));
    Serial.println(F("timestamp_ms,irradiance_wm2,humidity_percent,ambient_temp_c,pv_temp_c,voltage_v,current_a,power_w,fault_mode"));
  } else {
    Serial.println(F("=================================================="));
    Serial.println(F("PV FAULT DIAGNOSIS SYSTEM - ARDUINO ESP32-S3"));
    Serial.println(F("Thermal Camera: NOT USED | Mathematical Digital Twin"));
    Serial.println(F("=================================================="));
  }

  // Prime sensor readings
  filteredIrradiance = ((float)analogRead(POT_PIN) / 4095.0f) * 1000.0f;
  readSensors();
  applyFaultModel(currentMode, pvData.irradiance, pvData.ambientTemp,
                  pvData.voltage, pvData.current, pvData.power, pvData.pvTemp);
  updateFaultLED();

  if (oledAvailable) {
    updateOLED();
  }
}

// ============================================================================
// ARDUINO MAIN LOOP (Non-blocking Millis Scheduler)
// ============================================================================
void loop() {
  // 1. Service button interrupt/debounce continuously
  handleButton();

  unsigned long currentMillis = millis();

  // 2. Periodic sensor acquisition, mathematical modeling, and telemetry (1000 ms)
  if (currentMillis - lastSampleTime >= SAMPLE_INTERVAL) {
    lastSampleTime = currentMillis;

    readSensors();
    applyFaultModel(currentMode, pvData.irradiance, pvData.ambientTemp,
                    pvData.voltage, pvData.current, pvData.power, pvData.pvTemp);
    updateFaultLED();

    if (CSV_MODE) {
      logCSV();
    } else {
      printDiagnosticText();
    }
  }

  // 3. Periodic OLED dashboard refresh (500 ms)
  if (currentMillis - lastOledTime >= OLED_INTERVAL) {
    lastOledTime = currentMillis;
    if (oledAvailable) {
      updateOLED();
    }
  }
}

// ============================================================================
// SENSOR ACQUISITION & FILTERING
// ============================================================================
float readIrradiance() {
  int rawADC = analogRead(POT_PIN);
  float rawIrradiance = ((float)rawADC / 4095.0f) * 1000.0f;
  rawIrradiance = constrain(rawIrradiance, 0.0f, 1000.0f);

  // Exponential moving average filter to reduce ADC jitter
  filteredIrradiance = (0.35f * rawIrradiance) + (0.65f * filteredIrradiance);
  return constrain(filteredIrradiance, 0.0f, 1000.0f);
}

void readDHT22() {
  TempAndHumidity reading = dht.getTempAndHumidity();

  // Robust validation: fall back to last valid reading if error or NaN occurs
  if (dht.getStatus() != DHTesp::ERROR_NONE || isnan(reading.temperature) || isnan(reading.humidity)) {
    // Keep cached values
  } else {
    lastValidAmbientTemp = constrain(reading.temperature, -20.0f, 80.0f);
    lastValidHumidity    = constrain(reading.humidity, 0.0f, 100.0f);
  }
}

void readSensors() {
  pvData.irradiance  = readIrradiance();
  readDHT22();
  pvData.ambientTemp = lastValidAmbientTemp;
  pvData.humidity    = lastValidHumidity;
}

// ============================================================================
// DETERMINISTIC PV MATHEMATICAL MODEL
// ============================================================================
void calculatePVModel(float G, float Ta, float &V, float &I, float &P, float &Tpv) {
  // In normal operation, solar irradiance heats cell slightly above ambient
  float solarHeating = (G / Gref) * 3.0f;
  Tpv = Ta + solarHeating;

  // Current scales linearly with solar irradiance: I = Imp_ref * (G / Gref)
  I = Imp_ref * (G / Gref);

  // Voltage decreases with temperature: V = Vmp_ref * [1 + beta_V * (Tpv - Tref)]
  float vCalc = Vmp_ref * (1.0f + beta_V * (Tpv - Tref));

  // If irradiance is extremely low, voltage drops smoothly
  if (G < 40.0f) {
    vCalc *= (G / 40.0f);
  }

  V = max(0.0f, vCalc);
  I = max(0.0f, I);
  P = V * I;
}

// ============================================================================
// FAULT MODE MODELING
// ============================================================================
void applyFaultModel(FaultMode mode, float G, float Ta, float &V, float &I, float &P, float &Tpv) {
  // Compute healthy baseline first
  calculatePVModel(G, Ta, V, I, P, Tpv);

  switch (mode) {
    case NORMAL:
      // Baseline healthy model unchanged
      break;

    case PARTIAL_SHADING:
      // Partial shading drastically reduces photocurrent
      I = I * SHADING_FACTOR;
      // Voltage slightly reduced due to bypass diode conduction/mismatch
      V = V * 0.95f;
      Tpv = Ta;
      P = V * I;
      break;

    case OPEN_CIRCUIT:
      // Open circuit: terminal current drops to zero
      I = 0.0f;
      // Terminal voltage sits near open-circuit voltage Voc
      V = Voc_ref * (1.0f + beta_V * (Ta - Tref));
      if (G < 40.0f) {
        V *= (G / 40.0f);
      }
      V = max(0.0f, V);
      Tpv = Ta;
      P = 0.0f;
      break;

    case OVER_TEMPERATURE:
      // Simulated module overheating (elevated PV cell temperature)
      Tpv = Ta + TEMP_RISE_OVER_TEMP;
      // Voltage drops significantly due to high thermal coefficient
      V = Vmp_ref * (1.0f + beta_V * (Tpv - Tref));
      if (G < 40.0f) {
        V *= (G / 40.0f);
      }
      V = max(0.0f, V);
      // Current slightly affected by thermal carrier recombination
      I = Imp_ref * (G / Gref) * 0.95f;
      I = max(0.0f, I);
      P = V * I;
      break;
  }

  // Enforce physical bounds
  V = constrain(V, 0.0f, 30.0f);
  I = constrain(I, 0.0f, 10.0f);
  P = constrain(P, 0.0f, 300.0f);
}

// ============================================================================
// FAULT CLASSIFICATION & LABELING
// ============================================================================
const char* classifyFault(FaultMode mode) {
  switch (mode) {
    case NORMAL:           return "NORMAL";
    case PARTIAL_SHADING:  return "PARTIAL_SHADE";
    case OPEN_CIRCUIT:     return "OPEN_CIRCUIT";
    case OVER_TEMPERATURE: return "OVER_TEMP";
    default:               return "UNKNOWN";
  }
}

const char* getOledFaultText(FaultMode mode) {
  switch (mode) {
    case NORMAL:           return "FAULT: NORMAL";
    case PARTIAL_SHADING:  return "FAULT: PARTIAL_SHADE";
    case OPEN_CIRCUIT:     return "FAULT: OPEN_CIRCUIT";
    case OVER_TEMPERATURE: return "FAULT: OVER_TEMP";
    default:               return "FAULT: UNKNOWN";
  }
}

// ============================================================================
// ACTUATOR DRIVERS (LED & OLED)
// ============================================================================
void updateFaultLED() {
  if (currentMode == NORMAL) {
    digitalWrite(LED_PIN, LOW); // Fault LED OFF
  } else {
    digitalWrite(LED_PIN, HIGH); // Fault LED ON
  }
}

void displaySplashScreen() {
  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);
  display.setTextSize(1);

  display.setCursor(18, 8);
  display.println(F("PV FAULT DIAGNOSIS"));
  display.drawLine(10, 20, 118, 20, SSD1306_WHITE);

  display.setCursor(38, 26);
  display.println(F("ESP32-S3"));
  display.setCursor(8, 38);
  display.println(F("NO THERMAL CAMERA"));
  display.setCursor(22, 50);
  display.println(F("MATHEMATICAL TWIN"));

  display.display();
  delay(2000);
}

void updateOLED() {
  if (!oledAvailable) return;

  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);
  display.setTextSize(1);

  // Line 0: Title
  display.setCursor(0, 0);
  display.println(F("PV FAULT DIAGNOSIS"));
  display.drawLine(0, 9, 127, 9, SSD1306_WHITE);

  // Line 1: Irradiance & Humidity
  display.setCursor(0, 12);
  display.printf("G: %4.0f W/m2  H: %2.0f%%\n", pvData.irradiance, pvData.humidity);

  // Line 2: Temperatures (Ambient and PV cell)
  display.setCursor(0, 22);
  display.printf("Ta: %4.1f C  Tpv: %4.1f C\n", pvData.ambientTemp, pvData.pvTemp);

  // Line 3: Voltage & Current
  display.setCursor(0, 32);
  display.printf("V: %5.2f V   I: %4.2f A\n", pvData.voltage, pvData.current);

  // Line 4: Electrical Power
  display.setCursor(0, 42);
  display.printf("P: %5.2f W\n", pvData.power);

  // Line 5: Horizontal separator
  display.drawLine(0, 52, 127, 52, SSD1306_WHITE);

  // Line 6: Fault Status
  display.setCursor(0, 55);
  display.print(getOledFaultText(currentMode));

  display.display();
}

// ============================================================================
// HARDWARE BUTTON HANDLER (Edge Detection & Debounce)
// ============================================================================
void handleButton() {
  int reading = digitalRead(BUTTON_PIN);

  if (reading != lastButtonReading) {
    lastDebounceTime = millis();
  }

  if ((millis() - lastDebounceTime) > DEBOUNCE_DELAY) {
    if (reading != buttonState) {
      buttonState = reading;

      // Active LOW edge detected
      if (buttonState == LOW) {
        currentMode = static_cast<FaultMode>((currentMode + 1) % 4);

        Serial.println();
        Serial.print(F("[MODE] "));
        Serial.println(classifyFault(currentMode));

        // Immediate recalculation for instant UI response
        applyFaultModel(currentMode, pvData.irradiance, pvData.ambientTemp,
                        pvData.voltage, pvData.current, pvData.power, pvData.pvTemp);
        updateFaultLED();
        if (oledAvailable) {
          updateOLED();
        }
      }
    }
  }

  lastButtonReading = reading;
}

// ============================================================================
// TELEMETRY & DATA LOGGING
// ============================================================================
void logCSV() {
  // Format: timestamp_ms,irradiance_wm2,humidity_percent,ambient_temp_c,pv_temp_c,voltage_v,current_a,power_w,fault_mode
  Serial.printf("DATA,%lu,%.0f,%.1f,%.1f,%.1f,%.2f,%.2f,%.2f,%s\n",
                millis(),
                pvData.irradiance,
                pvData.humidity,
                pvData.ambientTemp,
                pvData.pvTemp,
                pvData.voltage,
                pvData.current,
                pvData.power,
                classifyFault(currentMode));
}

void printDiagnosticText() {
  Serial.println(F("------------------"));
  Serial.println(F("PV FAULT DIAGNOSIS"));
  Serial.println(F("------------------"));
  Serial.printf("Irradiance: %.0f W/m2\n", pvData.irradiance);
  Serial.printf("Ambient Temperature: %.1f C\n", pvData.ambientTemp);
  Serial.printf("Humidity: %.1f %%\n", pvData.humidity);
  Serial.printf("PV Temperature: %.1f C\n", pvData.pvTemp);
  Serial.printf("Voltage: %.2f V\n", pvData.voltage);
  Serial.printf("Current: %.2f A\n", pvData.current);
  Serial.printf("Power: %.2f W\n", pvData.power);
  Serial.printf("Fault: %s\n", classifyFault(currentMode));
  Serial.println(F("------------------"));
}
