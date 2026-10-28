import os
import sys
import argparse

try:
    import serial
except ImportError:
    serial = None

VALID_MODES = {"NORMAL", "PARTIAL_SHADE", "OPEN_CIRCUIT", "OVER_TEMP"}
TARGET_SAMPLES = 1500

CSV_HEADER = "timestamp_ms,irradiance_wm2,humidity_percent,ambient_temp_c,pv_temp_c,voltage_v,current_a,power_w,fault_mode\n"

def write_header(filepath):
    if not os.path.exists(filepath):
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(CSV_HEADER)

def count_samples(filepath):
    if not os.path.exists(filepath):
        return 0
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    # Skip header
    return max(0, len(lines) - 1)

def main():
    parser = argparse.ArgumentParser(description="Automated PV Dataset Collector (6000 samples)")
    parser.add_argument("--port", type=str, default="COM3", help="Serial port of ESP32 (e.g. COM3)")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate")
    parser.add_argument("--input", type=str, default=None, help="Offline input text file containing Wokwi serial output")
    args = parser.parse_args()

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    data_raw_dir = os.path.join(project_root, 'data', 'raw')
    data_final_dir = os.path.join(project_root, 'data', 'final')
    
    os.makedirs(data_raw_dir, exist_ok=True)
    os.makedirs(data_final_dir, exist_ok=True)

    files = {
        "NORMAL": os.path.join(data_raw_dir, "normal.csv"),
        "PARTIAL_SHADE": os.path.join(data_raw_dir, "partial_shade.csv"),
        "OPEN_CIRCUIT": os.path.join(data_raw_dir, "open_circuit.csv"),
        "OVER_TEMP": os.path.join(data_raw_dir, "over_temp.csv"),
    }

    counts = {}
    for mode, filepath in files.items():
        write_header(filepath)
        counts[mode] = count_samples(filepath)

    def print_status():
        print("\n" + "-" * 25)
        print("PV DATA COLLECTOR")
        print("-" * 25)
        total = 0
        for mode in ["NORMAL", "PARTIAL_SHADE", "OPEN_CIRCUIT", "OVER_TEMP"]:
            c = counts[mode]
            total += c
            status = "COMPLETE" if c >= TARGET_SAMPLES else f"{c} / {TARGET_SAMPLES}"
            print(f"{mode:15s}: {status}")
        print("-" * 25)
        print(f"TOTAL:          {total} / {TARGET_SAMPLES * 4}\n")

    if all(c >= TARGET_SAMPLES for c in counts.values()):
        print("DATASET ALREADY COMPLETE.")
        combine_dataset(files, data_final_dir)
        return

    # Set up the data source (file vs serial)
    if args.input:
        if not os.path.exists(args.input):
            print(f"Error: Input file '{args.input}' not found.")
            sys.exit(1)
        print(f"Reading from offline input file: {args.input}")
        
        def line_generator():
            with open(args.input, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    yield line
        
        source = line_generator()
        ser = None
    else:
        if serial is None:
            print("Error: 'pyserial' package is not installed for live serial capture.")
            print("Run: pip install pyserial (or use --input <file> for offline log ingestion)")
            sys.exit(1)
        print(f"Connecting to {args.port} at {args.baud} baud...")
        try:
            ser = serial.Serial(args.port, args.baud, timeout=1)
        except Exception as e:
            print(f"Failed to open serial port: {e}")
            sys.exit(1)
            
        print("Connected. Listening for DATA,...")
        
        def line_generator():
            while True:
                try:
                    yield ser.readline().decode('utf-8', errors='ignore')
                except KeyboardInterrupt:
                    print("\nCollection interrupted by user.")
                    break
                    
        source = line_generator()
    
    # Process the data
    for raw_line in source:
        if all(c >= TARGET_SAMPLES for c in counts.values()):
            print("DATASET COMPLETE")
            break
            
        line = raw_line.strip()
        if not line:
            continue
            
        if line.startswith("DATA,"):
            # e.g. DATA,12500,742.0,54.2,29.4,32.1,17.2,1.86,31.99,NORMAL
            parts = line[5:].split(',')
            
            if len(parts) != 9:
                print(f"[WARNING] Rejecting malformed row (wrong number of fields): {line}")
                continue
                
            mode = parts[-1].strip()
            if mode not in VALID_MODES:
                print(f"[WARNING] Rejecting row with unknown fault mode '{mode}': {line}")
                continue
                
            try:
                # Numeric checks for all 8 measurement fields
                float(parts[0])  # timestamp_ms
                float(parts[1])  # irradiance_wm2
                float(parts[2])  # humidity_percent
                float(parts[3])  # ambient_temp_c
                float(parts[4])  # pv_temp_c
                float(parts[5])  # voltage_v
                float(parts[6])  # current_a
                float(parts[7])  # power_w
            except ValueError:
                print(f"[WARNING] Rejecting row with non-numeric fields: {line}")
                continue
                
            if counts[mode] < TARGET_SAMPLES:
                counts[mode] += 1
                with open(files[mode], "a", encoding="utf-8") as f:
                    f.write(line[5:] + "\n")
                if counts[mode] % 10 == 0 or counts[mode] == TARGET_SAMPLES:
                    print_status()

    if ser:
        ser.close()
    
    if all(c >= TARGET_SAMPLES for c in counts.values()):
        combine_dataset(files, data_final_dir)
    else:
        if args.input:
            print(f"\n[INFO] End of input file reached.")
            print_status()

def combine_dataset(files, final_dir):
    final_path = os.path.join(final_dir, "pv_dataset_6000.csv")
    print(f"Combining class files into final dataset: {final_path}")
    
    with open(final_path, "w", encoding="utf-8") as outfile:
        outfile.write(CSV_HEADER)
        
        for mode in ["NORMAL", "PARTIAL_SHADE", "OPEN_CIRCUIT", "OVER_TEMP"]:
            with open(files[mode], "r", encoding="utf-8") as infile:
                lines = infile.readlines()
                # Skip header and ensure newline termination
                for l in lines[1:]:
                    if not l.endswith('\n'):
                        l += '\n'
                    outfile.write(l)
    
    print(f"Successfully generated {final_path}")

if __name__ == '__main__':
    main()
