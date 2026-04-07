import pathlib, csv, io

# 意図ごとに異なる列（;区切りでまとめる）
INTENT_COLS = [12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27]

out_dir  = pathlib.Path(r"outputs\batch_00001_01000")
out_path = pathlib.Path(r"outputs\batch_00001_01000_merged.csv")

csv_files = sorted(out_dir.glob("*.csv"))
all_rows  = []
header    = None

for f in csv_files:
    text = f.read_text(encoding="utf-8")
    rows = list(csv.reader(io.StringIO(text)))
    if len(rows) <= 1:
        continue
    if header is None:
        header = rows[0]

    data = rows[1:]

    if len(data) == 1:
        all_rows.append(data[0])
        continue

    # 複数行 → 1行にまとめる
    merged = list(data[0])  # ベースは1行目
    for col in INTENT_COLS:
        vals = []
        for row in data:
            v = row[col] if col < len(row) else ""
            if v and v not in vals:
                vals.append(v)
        merged[col] = ";".join(vals)

    all_rows.append(merged)

with open(out_path, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f, quoting=csv.QUOTE_ALL)
    writer.writerow(header)
    writer.writerows(all_rows)

print(f"完了: {len(all_rows)}行 → {out_path}")
print(f"（元: 1197行 → 統合後: {len(all_rows)}行）")
