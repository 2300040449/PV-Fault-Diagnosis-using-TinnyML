# Prototype Architecture

## PV Digital Model Pipeline

             PV DIGITAL MODEL
                    |
        +-----------+-----------+
        |                       |
   Irradiance              Temperature
   Potentiometer              DHT22
        |                       |
        +-----------+-----------+
                    |
                 ESP32-S3
                    |
             Feature Extraction
                    |
        +-----------+-----------+
        |                       |
     Voltage                 Current
        |                       |
        +-----------+-----------+
                    |
             Fault Classifier
                    |
        +-----------+-----------+
        |           |           |
      OLED        LED        Serial
