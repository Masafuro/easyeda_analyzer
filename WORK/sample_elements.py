import json
from pathlib import Path

def sample_elements(file_path, out_file):
    targets = {"NET", "PAD", "PAD_NET", "LINE", "VIA"}
    sampled = {k: [] for k in targets}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            if data and isinstance(data, list):
                etype = data[0]
                if etype in targets and len(sampled[etype]) < 3:
                    sampled[etype].append(data)
                    
    with open(out_file, 'w', encoding='utf-8') as fout:
        for etype in targets:
            fout.write(f"--- {etype} ({len(sampled[etype])} samples) ---\n")
            for s in sampled[etype]:
                fout.write(json.dumps(s, ensure_ascii=False) + "\n")

if __name__ == '__main__':
    target = Path(r"c:\Users\AI\Documents\LocalDev\easyeda_analysis_system\data\11382505dd454a9f9127fab01f71780a.epcb")
    out = Path(r"c:\Users\AI\Documents\LocalDev\easyeda_analysis_system\WORK\sample_output.txt")
    sample_elements(target, out)
