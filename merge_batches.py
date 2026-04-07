import csv
from pathlib import Path

def merge_all_batches(batch_dirs, output_file):
    all_rows = []
    
    # 各バッチフォルダから全CSVを読み込み
    for batch_dir in batch_dirs:
        batch_path = Path(batch_dir)
        if not batch_path.exists():
            print(f"スキップ: {batch_dir} が見つかりません")
            continue
            
        csv_files = sorted(batch_path.glob("*.csv"))
        print(f"{batch_dir}: {len(csv_files)} ファイル")
        
        for csv_file in csv_files:
            with open(csv_file, 'r', encoding='utf-8-sig', errors='replace') as f:
                reader = csv.reader(f)
                rows = list(reader)
                if len(rows) > 1:  # ヘッダー + データ行がある場合
                    all_rows.extend(rows[1:])  # ヘッダーを除いてデータ行のみ追加
    
    # 問い合わせIDで昇順ソート
    all_rows.sort(key=lambda x: int(x[0]) if x[0].isdigit() else 0)
    
    # 1つのファイルに出力
    with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        
        # ヘッダーを書き込み（batch1の最初のファイルから取得）
        first_file = sorted(Path(batch_dirs[0]).glob("*.csv"))[0]
        with open(first_file, 'r', encoding='utf-8-sig') as hf:
            header = list(csv.reader(hf))[0]
            writer.writerow(header)
        
        # 全データ行を書き込み
        writer.writerows(all_rows)
    
    print(f"\n✅ 完了: {len(all_rows)} 行を {output_file} に出力しました")

if __name__ == "__main__":
    batch_dirs = ["output/batch1", "output/batch2", "output/batch3", "output/batch4"]
    merge_all_batches(batch_dirs, "form_merged.csv")
