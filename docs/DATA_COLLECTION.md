# Dataset Collection Pipeline

## Overview
This project uses an automated pipeline to generate exactly 6,000 samples for TinyML training:

`Wokwi Simulator` -> `ESP32` -> `Serial DATA output` -> `Python collector` -> `Class-specific CSV files` -> `Combined 6000-sample dataset` -> `Validation`

## How to use

### Option 1: Offline Log File parsing (Recommended for Wokwi VS Code extension without COM port)
1. Run the Wokwi simulation in VS Code.
2. In the Wokwi Serial Monitor window, you will see output like `DATA,12500,742...`
3. Manually change the potentiometer (Irradiance), DHT22 sensor, and cycle the fault button across all four modes. Let it run for a while.
4. Copy the entire serial monitor output and save it as a text file (e.g. `wokwi_log.txt`) in your project folder.
5. Run the collector with the `--input` flag:
   ```bash
   python collector/dataset_collector.py --input wokwi_log.txt
   ```
6. The collector will parse the log, ignore arbitrary debug lines, tally valid rows into the raw class CSVs, and merge into `pv_dataset_6000.csv` once all classes reach 1500.

### Option 2: Live Serial Collection (For physical ESP32 or virtual COM port bridge)
1. Run the simulation/board and ensure serial is bridged.
2. Run the collector script:
   ```bash
   pip install -r collector/requirements.txt
   python collector/dataset_collector.py --port COM3
   ```

## Validation
Once your dataset is generated, validate it using:
```bash
python collector/validate_dataset.py
```
This script will confirm exactly 1500 samples per class, verify columns, ensure no missing values, and validate physical model constraints (P ≈ V*I).

## Next Stage
Import the `data/final/pv_dataset_6000.csv` dataset into Edge Impulse.
