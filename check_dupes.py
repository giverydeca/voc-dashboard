import pathlib, csv, io
from collections import Counter

out_dir = pathlib.Path(r"outputs\batch_00001_01000")
csv_files = sorted(out_dir.glob("*.csv"))

multi = []
dupes = []

for f in csv_files:
    text = f.read_text(encoding="utf-8")
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if len(rows) <= 1:
        continue
    data = rows[1:]  # ヘッダー除く

    # 複数行ファイル
    if len(data) > 1:
        multi.append((f.name, len(data), data))

    # 完全重複チェック
    seen = []
    for row in data:
        key = tuple(row)
        if key in seen:
            dupes.append((f.name, row))
        else:
            seen.append(key)

print(f"=== 複数行ファイル: {len(multi)}件 ===")
for name, cnt, rows in multi[:10]:
    print(f"\n{name} ({cnt}行)")
    print(f"  行1 通話ID={rows[0][0]}  意図={rows[0][16][:20] if len(rows[0])>16 else '?'}")
    print(f"  行2 通話ID={rows[1][0]}  意図={rows[1][16][:20] if len(rows[1])>16 else '?'}")
    if cnt > 2:
        print(f"  行3 通話ID={rows[2][0]}  意図={rows[2][16][:20] if len(rows[2])>16 else '?'}")

print(f"\n=== 完全重複行: {len(dupes)}件 ===")
for name, row in dupes[:5]:
    print(f"  {name}: 通話ID={row[0]}  意図={row[16][:20] if len(row)>16 else '?'}")
