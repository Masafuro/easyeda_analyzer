import json
import math
import sys
import argparse
from collections import defaultdict
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(description="EasyEDA .epcb Netlist Analyzer")
    parser.add_argument('filepath', type=str, help="Path to the .epcb file")
    parser.add_argument('--format', choices=['text', 'json'], default='text', help="Output format (text or json)")
    return parser.parse_args()

def analyze_epcb(filepath):
    # Stats structure:
    # stats[net_name] = {
    #     'LINE': { width_in_mil: {"length_mm": 0.0, "count": 0} },
    #     'VIA': { (holesize_mil, diameter_mil): count },
    #     'PAD': count,
    #     'PAD_NET': count,
    #     'POUR': count,
    #     ...
    # }
    stats = defaultdict(lambda: {
        'LINE': defaultdict(lambda: {"length_mm": 0.0, "count": 0}),
        'VIA': defaultdict(int),
        'PAD': 0,
        'PAD_NET': 0,
        'POUR': 0,
        'OTHER': defaultdict(int)
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
                    
                    # Store registered nets
                    if etype == "NET" and len(data) > 1:
                        net_name = data[1]
                        if net_name:
                            known_nets.add(net_name)
                    
                    # Major Elements where index 3 holds Net Name
                    if len(data) >= 4:
                        net_name = str(data[3]).strip()
                        # Allow elements only if they belong to a valid non-empty net name
                        if not net_name or (known_nets and net_name not in known_nets):
                            continue
                            
                        # LINE Element
                        if etype == "LINE" and len(data) >= 10:
                            x1, y1, x2, y2, width = data[5], data[6], data[7], data[8], data[9]
                            # Calc euclidian distance in mil
                            length_mil = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                            length_mm = length_mil * 0.0254
                            
                            stats[net_name]['LINE'][width]["length_mm"] += length_mm
                            stats[net_name]['LINE'][width]["count"] += 1
                            
                        # VIA Element
                        elif etype == "VIA" and len(data) >= 9:
                            hs, dia = data[7], data[8]
                            stats[net_name]['VIA'][(hs, dia)] += 1
                            
                        # PAD Element
                        elif etype == "PAD":
                            stats[net_name]['PAD'] += 1
                            
                        # PAD_NET Component connectivity
                        elif etype == "PAD_NET":
                            stats[net_name]['PAD_NET'] += 1
                            
                        # POUR / Copper Region
                        elif etype == "POUR":
                            stats[net_name]['POUR'] += 1
                            
                        else:
                            # Catch-all for elements with net name at index 3
                            stats[net_name]['OTHER'][etype] += 1
                            
                except json.JSONDecodeError as e:
                    sys.stderr.write(f"Parse error at line {line_num}: {e}\n")
                except Exception as e:
                    sys.stderr.write(f"Unexpected structure at line {line_num}: {e}\n")
    except FileNotFoundError:
        sys.stderr.write(f"Error: File not found -> {filepath}\n")
        sys.exit(1)
        
    return stats, known_nets

def print_text_report(stats):
    # Exclude nets that have completely zero elements (if any)
    for net, s in sorted(stats.items()):
        total_elements = sum(
            c['count'] for c in s['LINE'].values()
        ) + sum(s['VIA'].values()) + s['PAD'] + s['PAD_NET'] + s['POUR'] + sum(s['OTHER'].values())
        
        if total_elements == 0:
            continue
            
        print(f"NET: {net}")
        if s['LINE']:
            for width, line_stat in sorted(s['LINE'].items(), key=lambda x: x[0], reverse=True):
                print(f"  [LINE] Width {width:>7.3f}mil : {line_stat['count']:>4} count | {line_stat['length_mm']:>8.2f} mm (Total)")
        if s['VIA']:
            for (hs, dia), count in sorted(s['VIA'].items()):
                print(f"  [VIA]  Hole {hs:>5.2f}mil / Dia {dia:>5.2f}mil : {count:>4} count")
        if s['PAD'] > 0:
            print(f"  [PAD]      : {s['PAD']:>4} count")
        if s['PAD_NET'] > 0:
            print(f"  [PAD_NET]  : {s['PAD_NET']:>4} count")
        if s['POUR'] > 0:
            print(f"  [POUR]     : {s['POUR']:>4} count")
        
        for otype, ocount in sorted(s['OTHER'].items()):
             print(f"  [{otype:<9}]: {ocount:>4} count")
        print()

def main():
    args = parse_args()
    stats, known_nets = analyze_epcb(args.filepath)
    
    if args.format == 'json':
        # Need to convert VIA tuple keys to string for JSON serialization
        json_friendly = {}
        for net, s in stats.items():
            net_stat = {
                'LINE': {str(k): v for k, v in s['LINE'].items()},
                'VIA': {f"H{k[0]}_D{k[1]}": v for k, v in s['VIA'].items()},
                'PAD': s['PAD'],
                'PAD_NET': s['PAD_NET'],
                'POUR': s['POUR'],
                'OTHER': dict(s['OTHER'])
            }
            json_friendly[net] = net_stat
        print(json.dumps(json_friendly, indent=2))
    else:
        print_text_report(stats)

if __name__ == '__main__':
    main()
