import tkinter as tk
from tkinter import filedialog
import csv
import yaml
import time
import re
from playwright.sync_api import sync_playwright
from tqdm import tqdm

def select_file():
    root = tk.Tk()
    root.withdraw()
    return filedialog.askopenfilename(
        title="BOMファイルを選択してください",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )

def clean_text(text):
    """
    1. 改行や連続スペースを整形
    2. 半角の '~' を 全角の '～' に置換（Markdownの取り消し線対策）
    """
    if not text: return ""
    # 空白の整形
    text = " ".join(text.split()).strip()
    # 波線の置換
    return text.replace('~', '～')

def extract_stock_number(raw_text):
    """在庫数から数値だけを抽出"""
    if not raw_text: return 0
    digits_only = re.sub(r'[^\d]', '', raw_text)
    try:
        return int(digits_only)
    except ValueError:
        return 0

def scrape_lcsc_process(parts_list):
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        for part in tqdm(parts_list, desc="Scraping LCSC", unit="part"):
            url = f"https://www.lcsc.com/product-detail/{part}.html"
            try:
                page.goto(url, wait_until="networkidle", timeout=60000)
                
                # 1. 製品タイトル
                title_loc = page.locator("h1").first
                product_name = clean_text(title_loc.inner_text()) if title_loc.count() > 0 else "N/A"

                # 2. 在庫数
                stock_num = 0
                stock_loc = page.get_by_text("In-Stock", exact=False).first
                if stock_loc.count() > 0:
                    stock_num = extract_stock_number(stock_loc.inner_text())

                # 3. 仕様テーブル
                spec_data = {}
                table_locators = page.locator("table").all()
                for table in table_locators:
                    content = table.inner_text()
                    if "Type" in content and "Description" in content:
                        rows = table.locator("tr").all()
                        for row in rows:
                            cells = row.locator("td, th").all()
                            if len(cells) >= 2:
                                # キーと値の両方に clean_text を適用
                                k = clean_text(cells[0].inner_text())
                                v = clean_text(cells[1].inner_text())
                                if k and k not in ["Type", "Description"]:
                                    spec_data[k] = v
                
                results.append({
                    "supplier_part": part,
                    "product_name": product_name,
                    "in_stock": stock_num,
                    "specifications": spec_data,
                    "url": url
                })

            except Exception as e:
                results.append({"supplier_part": part, "error": str(e)})
            
            time.sleep(1)
            
        browser.close()
    return results

def main():
    file_path = select_file()
    if not file_path: return

    parts_list = []
    with open(file_path, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter='\t')
        parts_list = [row.get("Supplier Part") for row in reader if row.get("Supplier Part")]

    if not parts_list: return

    print(f"全 {len(parts_list)} 件の処理を開始します...")
    scraped_results = scrape_lcsc_process(parts_list)

    output_filename = "lcsc_bom_final.yaml"
    with open(output_filename, 'w', encoding='utf-8') as yf:
        # 整形済みのYAMLとして出力
        yaml.dump(
            scraped_results, 
            yf, 
            allow_unicode=True, 
            sort_keys=False, 
            default_flow_style=False,
            default_style='"' # すべての文字列をダブルクォートで囲む
        )
    
    print(f"\n完了しました！ '{output_filename}' を確認してください。")

if __name__ == "__main__":
    main()
