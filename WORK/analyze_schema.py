import json
from collections import defaultdict
from pathlib import Path

def analyze_schema(file_path, out_file):
    # すでに判明しているネット名を基準として、それがどこに現れるかを探す
    known_nets = {"+5V", "GND", "PB5", "PB4", "PA7", "PA6", "PA5", "PC3", "PC2", "PC1", "PC0", "PB3", "PB2", "PB1", "PB0", "PA3", "PA4/XDIR", "PA2", "PA1", "PA0/UPDI", "$1N913", "$1N812", "$1N627"}
    
    # schema_info[element_type] = {
    #     'lengths': set(),
    #     'net_indices': defaultdict(int)  # どのインデックスにknown_netsが出現したかのカウント
    # }
    schema_info = defaultdict(lambda: {'lengths': set(), 'net_indices': defaultdict(int), 'sample': None})
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            if data and isinstance(data, list):
                etype = data[0]
                schema_info[etype]['lengths'].add(len(data))
                
                # サンプルを1つ記憶
                if schema_info[etype]['sample'] is None:
                    schema_info[etype]['sample'] = data
                
                # NET要素の場合は自身がネット名定義なので特別扱い
                if etype == "NET":
                    if len(data) > 1 and isinstance(data[1], str):
                        schema_info[etype]['net_indices'][1] += 1
                else:
                    # 要素内のすべての文字列型アイテムをチェックし、known_netsに含まれていたらそのインデックスを記録
                    for idx, item in enumerate(data):
                        if isinstance(item, str) and item in known_nets:
                            schema_info[etype]['net_indices'][idx] += 1

    with open(out_file, 'w', encoding='utf-8') as fout:
        for etype, info in sorted(schema_info.items(), key=lambda x: max(x[1]['net_indices'].values()) if x[1]['net_indices'] else 0, reverse=True):
            fout.write(f"--- Element: {etype} ---\n")
            fout.write(f"  Array Lengths seen: {sorted(list(info['lengths']))}\n")
            if info['net_indices']:
                for idx, count in sorted(info['net_indices'].items()):
                    fout.write(f"  Net Name found at Index [{idx}] in {count} instances.\n")
            else:
                fout.write("  No known Net Names found in this element.\n")
            fout.write(f"  Sample: {json.dumps(info['sample'], ensure_ascii=False)}\n\n")

if __name__ == '__main__':
    target = Path(r"c:\Users\AI\Documents\LocalDev\easyeda_analysis_system\data\11382505dd454a9f9127fab01f71780a.epcb")
    out = Path(r"c:\Users\AI\Documents\LocalDev\easyeda_analysis_system\WORK\schema_output.txt")
    analyze_schema(target, out)
