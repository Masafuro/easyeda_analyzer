import json
import sys
from pathlib import Path

def check_epcb_format(file_path):
    print(f"Checking format mapping for: {file_path}")
    error_count = 0
    parsed_lines = 0
    empty_lines = 0

    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                empty_lines += 1
                continue
            try:
                # 1行ずつJSON配列としてパースできるかテスト
                data = json.loads(line)
                if not isinstance(data, list):
                    print(f"Warning: Line {line_num} is not a JSON list.")
                    error_count += 1
                parsed_lines += 1
            except json.JSONDecodeError as e:
                print(f"Error at line {line_num}: {e}")
                print(f"Content: {line[:100]}...")
                error_count += 1

    if error_count == 0:
        print(f"Success! {parsed_lines} lines parsed successfully. ({empty_lines} empty lines skipped)")
    else:
        print(f"Failed with {error_count} errors out of {parsed_lines + empty_lines} lines.")

if __name__ == '__main__':
    target = Path(r"c:\Users\AI\Documents\LocalDev\easyeda_analysis_system\data\11382505dd454a9f9127fab01f71780a.epcb")
    check_epcb_format(target)
