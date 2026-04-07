import pathlib

path = pathlib.Path(r"pycsv\main.py")
src  = path.read_text(encoding="utf-8")

# run() 関数内の files: list[CsvFile] = [] の前後10行を表示
lines = src.splitlines()
for i, line in enumerate(lines, 1):
    if "CsvFile" in line or "start_id" in line or "args.start" in line:
        # 前後3行も表示
        start = max(0, i-3)
        end   = min(len(lines), i+3)
        print(f"--- 周辺 (行{start+1}～{end}) ---")
        for j in range(start, end):
            marker = ">>>" if j == i-1 else "   "
            print(f"{marker} {j+1:4d}: {lines[j]}")
        print()
