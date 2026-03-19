import json
import math
import sys
import argparse
import statistics
from collections import defaultdict
from pathlib import Path

# ==========================================
# Pure Python Lightweight YAML Formatter
# ==========================================
def dump_yaml(data, indent=0):
    lines = []
    prefix = '  ' * indent
    if isinstance(data, dict):
        for k, v in data.items():
            # キー名に不正な文字が含まれる場合はクォート
            k_str = str(k)
            if any(c in k_str for c in ": #[]{}"):
                k_str = f'"{k_str}"'
                
            if isinstance(v, dict):
                if not v: # empty dict
                    lines.append(f"{prefix}{k_str}: {{}}")
                else:
                    lines.append(f"{prefix}{k_str}:")
                    lines.extend(dump_yaml(v, indent + 1))
            elif isinstance(v, list):
                if not v: # empty list
                    lines.append(f"{prefix}{k_str}: []")
                else:
                    lines.append(f"{prefix}{k_str}:")
                    for item in v:
                        lines.append(f"{prefix}  - {item}")
            else:
                lines.append(f"{prefix}{k_str}: {v}")
    return lines

# ==========================================
# Core Analyzer Logic
# ==========================================
def mil_to_mm(mil_value):
    return mil_value * 0.0254

def parse_args():
    parser = argparse.ArgumentParser(description="EasyEDA .epcb Review Analyzer (v2)")
    parser.add_argument('filepath', type=str, help="Path to the .epcb file")
    return parser.parse_args()

def analyze_epcb(filepath):
    # Stats structure to hold raw data
    raw_stats = defaultdict(lambda: {
        'LINE': defaultdict(list), # width_mm -> list of length_mm
        'VIA': defaultdict(int),   # (hole_mm, dia_mm) -> count
        'PAD': 0,
        'POUR': 0,
    })
    
    known_nets = set()

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if not isinstance(data, list):
                        continue
                    
                    etype = data[0]
                    # Register standard nets
                    if etype == "NET" and len(data) > 1 and isinstance(data[1], str):
                        known_nets.add(data[1].strip())
                    
                    # Major Elements
                    if len(data) >= 4:
                        net_name = str(data[3]).strip()
                        # Allow elements only if they belong to a registered net name
                        if not net_name or (known_nets and net_name not in known_nets):
                            continue
                            
                        # LINE Element
                        if etype == "LINE" and len(data) >= 10:
                            x1, y1, x2, y2, width_mil = data[5], data[6], data[7], data[8], data[9]
                            length_mil = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                            
                            width_mm = round(mil_to_mm(width_mil), 3)
                            length_mm = round(mil_to_mm(length_mil), 3)
                            
                            raw_stats[net_name]['LINE'][width_mm].append(length_mm)
                            
                        # VIA Element
                        elif etype == "VIA" and len(data) >= 9:
                            hs_mil, dia_mil = data[7], data[8]
                            hs_mm = round(mil_to_mm(hs_mil), 3)
                            dia_mm = round(mil_to_mm(dia_mil), 3)
                            raw_stats[net_name]['VIA'][(hs_mm, dia_mm)] += 1
                            
                        # PAD Element
                        elif etype == "PAD":
                            raw_stats[net_name]['PAD'] += 1
                            
                        # POUR Element
                        elif etype == "POUR":
                            raw_stats[net_name]['POUR'] += 1
                            
                except json.JSONDecodeError as e:
                    sys.stderr.write(f"Parse error at line {line_num}: {e}\n")
                except Exception as e:
                    sys.stderr.write(f"Unexpected structure at line {line_num}: {e}\n")
    except FileNotFoundError:
        sys.stderr.write(f"Error: File not found -> {filepath}\n")
        sys.exit(1)
        
    return raw_stats

def compile_statistics(raw_stats):
    final_output = {}
    
    for net, raw in sorted(raw_stats.items()):
        # [Filter] Ignore if no LINE components (Rule of Silence / Review focus)
        if not raw['LINE']:
            continue
            
        net_dict = {}
        
        # LINE Stats
        line_dict = {}
        # Sort width roughly desc (widest first)
        for width_mm, lengths in sorted(raw['LINE'].items(), key=lambda x: x[0], reverse=True):
            count = len(lengths)
            total = sum(lengths)
            width_key = f"Width_{width_mm:.3f}mm"
            
            w_stat = {
                "Count": count,
                "TotalLength_mm": round(total, 3)
            }
            if count > 0:
                w_stat["Min_mm"] = round(min(lengths), 3)
                w_stat["Max_mm"] = round(max(lengths), 3)
                w_stat["Mean_mm"] = round(statistics.mean(lengths), 3)
                w_stat["Median_mm"] = round(statistics.median(lengths), 3)
                if count > 1:
                    w_stat["Variance"] = round(statistics.variance(lengths), 3)
                else:
                    w_stat["Variance"] = 0.0
                    
            line_dict[width_key] = w_stat
            
        net_dict["LINE"] = line_dict
        
        # VIA Stats
        if raw['VIA']:
            via_dict = {}
            for (hs, dia), count in sorted(raw['VIA'].items()):
                via_key = f"Hole_{hs:.3f}mm_Dia_{dia:.3f}mm"
                via_dict[via_key] = {"Count": count}
            net_dict["VIA"] = via_dict
            
        # Miscellaneous Counts
        if raw['PAD'] > 0:
            net_dict["PAD"] = {"Count": raw['PAD']}
        if raw['POUR'] > 0:
            net_dict["POUR"] = {"Count": raw['POUR']}
            
        final_output[f"{net}"] = net_dict
        
    return final_output

def main():
    args = parse_args()
    raw_stats = analyze_epcb(args.filepath)
    structured_data = compile_statistics(raw_stats)
    
    # Generate and print YAML
    yaml_lines = dump_yaml(structured_data)
    for line in yaml_lines:
        print(line)

if __name__ == '__main__':
    main()
