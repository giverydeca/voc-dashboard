import csv
from pathlib import Path

d = Path(r".\outputs\per_input_2001_10000")
files = sorted(d.glob("*.csv"))
print("files:", len(files))

bad = []  # (name, header_cols, row1_cols)
for p in files:
    with p.open("r", encoding="utf-8", errors="replace", newline="") as f:
        r = csv.reader(f)
        header = next(r, None)
        row1 = next(r, None)
    hc = len(header) if header else 0
    rc = len(row1) if row1 else 0
    if hc != 44 or rc != 44:
        bad.append((p.name, hc, rc))
        if len(bad) >= 100:
            break

print("bad_first100:", len(bad))
for x in bad:
    print(x)
