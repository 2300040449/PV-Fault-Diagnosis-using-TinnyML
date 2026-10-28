# System Architecture & Hardware Pinout

## Block Diagram

```text
+-------------------+      +-------------------+
|   Potentiometer   |      |   DHT22 Sensor    |
| (Solar Irradiance)|      | (Ambient Temp/Hum)|
+---------+---------+      +---------+---------+
          | GPIO 1                   | GPIO 4
          +------------+   +---------+
                       |   |
                  +----+---+----+
                  |  ESP32-S3   |
                  |  (Firmware) |
                  +----+---+----+
                       |   |
          +------------+   +---------+
          | GPIO 13                  | GPIO 2
+---------+---------+      +---------+---------+
|    Push Button    |      |  Red Fault LED    |
| (Fault Selection) |      | (Status Output)   |
+-------------------+      +-------------------+
                       |
               +-------+-------+
          I2C  | OLED SSD1306  |
       (SDA:8) | 128x64 Pixels |
       (SCL:9) +---------------+
```

## Microcontroller Pin Mapping Table

| Component | Pin Number | Function / Interface | Mode / Configuration |
| :--- | :--- | :--- | :--- |
| **Potentiometer SIG** | `GPIO 1` | Analog Input (Irradiance) | 12-bit ADC (`0 - 4095`), smoothed with EMA |
| **Fault Indicator LED** | `GPIO 2` | Digital Output | Active `HIGH` through 220 $\Omega$ current limiter |
| **DHT22 DATA** | `GPIO 4` | One-Wire Digital I/O | `DHTesp` timing protocol with NaN fallback |
| **OLED SDA** | `GPIO 8` | I2C Serial Data | Hardware I2C at address `0x3C` |
| **OLED SCL** | `GPIO 9` | I2C Serial Clock | Hardware I2C at 400 kHz |
| **Mode Push Button** | `GPIO 13` | Digital Input | `INPUT_PULLUP` (Active `LOW`, 50 ms debounce) |

## Software Scheduler
The firmware uses a non-blocking `millis()` scheduler:
- **Button Handling**: Polled every cycle with state debounce and falling-edge detection.
- **Sensor Acquisition & PV Model**: Executed every `1000 ms`.
- **Serial Telemetry**: Clean CSV row emitted every `1000 ms`.
- **OLED Dashboard**: Refreshed every `500 ms` to avoid I2C bus congestion and screen flicker.
