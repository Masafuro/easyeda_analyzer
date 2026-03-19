import json
from collections import defaultdict
from pathlib import Path

def analyze_elements(file_path):
    print(f"Analyzing element types in: {file_path}")
    element_counts = defaultdict(int)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            if data and isinstance(data, list):
                element_type = data[0]
                element_counts[element_type] += 1
                
    # 出現回数順にソートして出力
    for etype, count in sorted(element_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"[{etype}]: {count}")

if __name__ == '__main__':
    target = Path(r"c:\Users\AI\Documents\LocalDev\easyeda_analysis_system\data\11382505dd454a9f9127fab01f71780a.epcb")
    analyze_elements(target)
