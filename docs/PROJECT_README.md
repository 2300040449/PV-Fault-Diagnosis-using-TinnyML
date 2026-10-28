# Project Overview: PV Fault Diagnosis Without Thermal Camera Using TinyML

## Abstract
Photovoltaic (PV) system monitoring typically relies on expensive aerial thermography or infrared inspections. This research project presents an edge-compatible IoT digital twin running on an ESP32-S3 microcontroller that detects and classifies four key PV operating conditions using standard low-cost electrical and environmental sensors:
- Solar Irradiance ($G$)
- Ambient Temperature ($T_a$) and Humidity ($H$)
- Terminal Voltage ($V$)
- Output Current ($I$)

By mathematically coupling environmental measurements with electrical characteristics, faults such as **Partial Shading**, **Open Circuit**, and **Over-Temperature** are identified without requiring thermal imaging.

## Hardware Stack
- **Microcontroller**: Espressif ESP32-S3 DevKitC-1 (240 MHz dual-core, 320 KB SRAM, 8 MB Flash)
- **Display**: SSD1306 128x64 I2C OLED (GPIO 8 SDA, GPIO 9 SCL)
- **Irradiance Simulator**: Rotary Potentiometer (GPIO 1 ADC)
- **Weather Sensor**: DHT22 Digital Temperature & Humidity Sensor (GPIO 4)
- **Fault Injection**: Push Button (GPIO 13 with internal pullup)
- **Indicator**: Red Fault LED (GPIO 2 via 220 $\Omega$ resistor)

## Research Relevance
The generated clean CSV telemetry stream serves as the training benchmark for lightweight TinyML classifiers (Decision Trees, Random Forests, SVMs, and 1D CNNs) designed for ultra-low latency deployment on resource-constrained solar microinverters.
