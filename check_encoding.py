import re

def is_mojibake(s):
    return (s.count("縺") + s.count("繧") + s.count("繝") + s.count("竏")) >= 3

with open(r"data\calls_10.tsv", encoding="utf-8-sig", errors="replace") as f:
    lines = f.readlines()

ok = 0
ng = 0
for i, line in enumerate(lines, 1):
    cols = line.split("\t")
    txt = cols[2][:80] if len(cols) >= 3 else ""
    if is_mojibake(txt):
        ng += 1
        print(f"NG 行{i:3d}: {txt[:60]}")
    else:
        ok += 1
        print(f"OK 行{i:3d}: {txt[:60]}")

print(f"\n正常: {ok}件 / 文字化け: {ng}件 / 合計: {ok+ng}件")
