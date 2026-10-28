"""
Serial Data Collection Script
Captures real-time CSV telemetry from the ESP32-S3 over USB Serial
and appends validated records to data/pv_dataset.csv.
"""

import sys
import os
import time
import argparse

try:
    import serial
except ImportError:
    print("pyserial is not installed. Run: pip install pyserial")
    sys.exit(1)

DEFAULT_PORT = "COM3"
DEFAULT_BAUD = 115200
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "pv_dataset.csv")
CSV_HEADER = "timestamp_ms,irradiance_wm2,humidity_percent,ambient_temp_c,pv_temp_c,voltage_v,current_a,power_w,fault_mode\n"

def validate_row(parts):
    if len(parts) != 9:
        return False
    try:
        int(parts[0])       # timestamp_ms
        float(parts[1])     # irradiance_wm2
        float(parts[2])     # humidity_percent
        float(parts[3])     # ambient_temp_c
        float(parts[4])     # pv_temp_c
        float(parts[5])     # voltage_v
        float(parts[6])     # current_a
        float(parts[7])     # power_w
        str(parts[8].strip()) # fault_mode
        return True
    except ValueError:
        return False

def main():
    parser = argparse.ArgumentParser(description="Capture PV Telemetry from ESP32 Serial")
    parser.add_argument("--port", default=DEFAULT_PORT, help="Serial port (e.g. COM3 or /dev/ttyUSB0)")
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUD, help="Baud rate (default 115200)")
    parser.add_argument("--output", default=OUTPUT_FILE, help="Output CSV path")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    if not os.path.exists(args.output):
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(CSV_HEADER)
        print(f"Created new dataset file: {args.output}")

    print(f"Connecting to {args.port} at {args.baud} baud...")
    try:
        ser = serial.Serial(args.port, args.baud, timeout=2)
        time.sleep(1.5)
        print("Connected. Listening for CSV telemetry stream (Press Ctrl+C to stop)...")

        with open(args.output, "a", encoding="utf-8") as f:
            while True:
                line = ser.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    continue
                if "timestamp_ms" in line or line.startswith("="):
                    continue
                parts = line.split(",")
                if validate_row(parts):
                    f.write(line + "\n")
                    f.flush()
                    print(f"Captured: {line}")
                else:
                    print(f"[DEBUG]: {line}")
    except serial.SerialException as e:
        print(f"Serial communication error: {e}")
    except KeyboardInterrupt:
        print("\nData collection terminated by user.")

if __name__ == "__main__":
    main()
