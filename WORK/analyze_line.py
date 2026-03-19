import json
import math
from pathlib import Path

def analyze_dimensions(file_path, out_file):
    lines = []
    vias = []
    canvas = None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            if not isinstance(data, list):
                continue
            
            etype = data[0]
            if etype == "CANVAS":
                canvas = data
            elif etype == "LINE" and len(lines) < 15:
                lines.append(data)
            elif etype == "VIA" and len(vias) < 5:
                vias.append(data)

    with open(out_file, 'w', encoding='utf-8') as fout:
        fout.write("--- CANVAS Definition ---\n")
        fout.write(json.dumps(canvas, ensure_ascii=False) + "\n\n")
        
        fout.write("--- LINE Samples & Length Calculation ---\n")
        for l in lines:
            # 推測: [5]=X1, [6]=Y1, [7]=X2, [8]=Y2, [9]=Width
            try:
                x1, y1, x2, y2, width = l[5], l[6], l[7], l[8], l[9]
                length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                fout.write(f"Net: {l[3]:<8} | (X1, Y1)=({x1:>9}, {y1:>9}) to (X2, Y2)=({x2:>9}, {y2:>9}) | Width: {width:>6} | Calculated Length: {length:.4f}\n")
            except Exception as e:
                fout.write(f"Error parsing LINE {l}: {e}\n")
                
        fout.write("\n--- VIA Samples ---\n")
        for v in vias:
            # 推測: [5]=X, [6]=Y, [7]=HoleSize, [8]=Diameter
            try:
                x, y, hs, d = v[5], v[6], v[7], v[8]
                fout.write(f"Net: {v[3]:<8} | (X, Y)=({x:>9}, {y:>9}) | HoleSize: {hs:>7} | Diameter: {d:>7}\n")
            except Exception as e:
                fout.write(f"Error parsing VIA {v}: {e}\n")

if __name__ == '__main__':
    target = Path(r"c:\Users\AI\Documents\LocalDev\easyeda_analysis_system\data\11382505dd454a9f9127fab01f71780a.epcb")
    out = Path(r"c:\Users\AI\Documents\LocalDev\easyeda_analysis_system\WORK\dimension_output.txt")
    analyze_dimensions(target, out)
