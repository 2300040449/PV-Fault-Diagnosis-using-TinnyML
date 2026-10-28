import os
import sys
import argparse

def main():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    default_dataset_path = os.path.join(project_root, 'data', 'final', 'pv_dataset_6000.csv')
    
    parser = argparse.ArgumentParser(description="Validate PV Fault Diagnosis Dataset")
    parser.add_argument("--dataset", "--file", "-f", type=str, default=default_dataset_path,
                        help=f"Path to dataset CSV file (default: {default_dataset_path})")
    parser.add_argument("--target", "-t", type=int, default=1500,
                        help="Expected samples per class (default: 1500 for final 6000-sample dataset)")
    args = parser.parse_args()

    dataset_path = args.dataset
    target_samples = args.target
    
    if not os.path.exists(dataset_path):
        print(f"Error: Dataset file not found: {dataset_path}")
        if dataset_path == default_dataset_path:
            fallback_path = os.path.join(project_root, 'data', 'pv_dataset.csv')
            print("\n[NOTE] The target 6,000-sample dataset (data/final/pv_dataset_6000.csv) has not been collected yet.")
            if os.path.exists(fallback_path):
                print("To validate the existing baseline 1,000-sample dataset, run:")
                print("  python collector/validate_dataset.py --dataset data/pv_dataset.csv --target 250")
        sys.exit(1)
        
    counts = {"NORMAL": 0, "PARTIAL_SHADE": 0, "OPEN_CIRCUIT": 0, "OVER_TEMP": 0}
    # Support both snake_case (firmware/collector standard) and space-separated (legacy synthetic) labels
    label_alias = {
        "NORMAL": "NORMAL",
        "PARTIAL SHADE": "PARTIAL_SHADE",
        "PARTIAL_SHADE": "PARTIAL_SHADE",
        "OPEN CIRCUIT": "OPEN_CIRCUIT",
        "OPEN_CIRCUIT": "OPEN_CIRCUIT",
        "OVER TEMP": "OVER_TEMP",
        "OVER_TEMP": "OVER_TEMP"
    }
    malformed = 0
    missing = 0
    inconsistent_power = 0
    
    with open(dataset_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    if not lines:
        print("Error: Dataset file is empty.")
        sys.exit(1)

    header = lines[0].strip().split(',')
    expected_columns = ["timestamp_ms","irradiance_wm2","humidity_percent","ambient_temp_c","pv_temp_c","voltage_v","current_a","power_w","fault_mode"]
    
    if header != expected_columns:
        print("Error: Columns do not match expected format.")
        print(f"Found:    {header}")
        print(f"Expected: {expected_columns}")
        sys.exit(1)
        
    for line in lines[1:]:
        parts = line.strip().split(',')
        if len(parts) != 9:
            malformed += 1
            continue
            
        if any(p.strip() == "" for p in parts):
            missing += 1
            continue
            
        try:
            v = float(parts[5])
            i = float(parts[6])
            p = float(parts[7])
            
            # Allow for small floating point rounding differences
            if abs(v * i - p) > 0.5:
                inconsistent_power += 1
        except ValueError:
            malformed += 1
            continue
            
        raw_mode = parts[8].strip()
        mode = label_alias.get(raw_mode)
        if mode in counts:
            counts[mode] += 1
        else:
            malformed += 1
            
    print("DATASET VALIDATION")
    print("==================")
    print(f"File: {dataset_path}")
    
    total_samples = sum(counts.values())
    expected_total = target_samples * 4
    print(f"Total samples: {total_samples} (Expected: {expected_total})\n")
    
    for mode in ["NORMAL", "PARTIAL_SHADE", "OPEN_CIRCUIT", "OVER_TEMP"]:
        status = "[PASS]" if counts[mode] == target_samples else "[FAIL]"
        print(f"{mode:16s}: {counts[mode]:4d} / {target_samples} {status}")
        
    print(f"\nMissing values:     {missing} {'[PASS]' if missing == 0 else '[FAIL]'}")
    print(f"Malformed rows:     {malformed} {'[PASS]' if malformed == 0 else '[FAIL]'}")
    print(f"Inconsistent Power: {inconsistent_power} {'[PASS]' if inconsistent_power == 0 else '[WARN]'} (Where P != V*I)")
    
    if total_samples == expected_total and all(c == target_samples for c in counts.values()) and missing == 0 and malformed == 0:
        print("\nDataset status: VALID")
        return 0
    else:
        print("\nDataset status: INVALID")
        return 1

if __name__ == '__main__':
    sys.exit(main() or 0)
