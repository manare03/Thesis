"""
============================================================
CLASSIFICATION MONITOR
Reads reg_classification register array every second
and prints any non-zero results in real time.

Run this while tcpreplay is playing to see live classification.

Usage:
    python3 monitor_classification.py
============================================================
"""

import subprocess
import time
import sys

THRIFT_PORT = 9090
POLL_INTERVAL = 1  # seconds between reads
CLASS_NAMES = {
    1: 'VOICE',
    2: 'VIDEO',
    3: 'OTHER',
    4: 'SIGNALLING'
}
def read_register(register_name):
    """Read entire register array via simple_switch_CLI."""
    cmd = f'echo "register_read {register_name}" | simple_switch_CLI --thrift-port {THRIFT_PORT}'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout

def parse_register(output):
    """Parse register array output and return {index: value} for non-zero values."""
    nonzero = {}
    for line in output.split('\n'):
        if register_name := None:
            pass
        if '= ' in line and '[' not in line:
            # Format: reg_name= 0, 0, 0, 123, 0 ...
            try:
                values_str = line.split('= ')[1]
                values = [int(v.strip()) for v in values_str.split(',')]
                for i, v in enumerate(values):
                    if v != 0:
                        nonzero[i] = v
            except:
                pass
    return nonzero

def read_reg_array(reg_name):
    """Read register array and return non-zero entries."""
    cmd = f'echo "register_read {reg_name}" | simple_switch_CLI --thrift-port {THRIFT_PORT} 2>/dev/null'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    nonzero = {}
    for line in result.stdout.split('\n'):
        if f'{reg_name}=' in line:
            try:
                values_str = line.split('= ')[1]
                values = [int(v.strip()) for v in values_str.split(',')]
                for i, v in enumerate(values):
                    if v != 0:
                        nonzero[i] = v
            except:
                pass
    return nonzero


print("=" * 60)
print("LIVE CLASSIFICATION MONITOR")
print("=" * 60)
print(f"Polling every {POLL_INTERVAL} second(s)...")
print("Start tcpreplay now. Press Ctrl+C to stop.\n")

seen_indices = set()

try:
    while True:
        # Read classification register
        classifications = read_reg_array('reg_classification')
        packets = read_reg_array('reg_total_packets')
        total_bytes = read_reg_array('reg_total_bytes')

        if classifications:
            for idx, val in classifications.items():
                label = CLASS_NAMES.get(val, f'UNKNOWN({val})')
                pkts = packets.get(idx, '?')
                tbytes = total_bytes.get(idx, '?')

                if idx not in seen_indices:
                    seen_indices.add(idx)
                    print(f"[NEW FLOW] Index={idx} → {label} | packets={pkts} | total_bytes={tbytes}")
                else:
                    print(f"[LIVE]     Index={idx} → {label} | packets={pkts} | total_bytes={tbytes}")
        else:
            print(f"[WAITING]  No classifications yet...")

        time.sleep(POLL_INTERVAL)

except KeyboardInterrupt:
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    classifications = read_reg_array('reg_classification')
    if classifications:
        for idx, val in classifications.items():
            label = CLASS_NAMES.get(val, f'UNKNOWN({val})')
            pkts = packets.get(idx, '?')
            print(f"  Flow index {idx}: {label} ({pkts} packets processed)")
    else:
        print("  No classifications recorded.")