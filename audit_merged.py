import csv, re, sys
from pathlib import Path
from collections import Counter

if len(sys.argv) < 2:
    print("USAGE: python audit_merged.py <merged_csv_path>")
    raise SystemExit(2)

p = Path(sys.argv[1])
if not p.exists():
    print("NOT FOUND:", p)
    raise SystemExit(2)

with p.open("r", encoding="utf-8", errors="replace", newline="") as f:
    r = csv.reader(f)
    header = next(r, None)
    if not header:
        print("EMPTY FILE")
        raise SystemExit(2)
    exp = len(header)

    ids = []
    bad_id_rows = []     # (lineno, firstcell, colcount)
    bad_cols_rows = []   # (lineno, firstcell, colcount)
    for lineno, row in enumerate(r, start=2):
        if not row:
            continue
        first = row[0] if len(row) >= 1 else ""
        colcount = len(row)

        # column count mismatch
        if colcount != exp and len(bad_cols_rows) < 50:
            bad_cols_rows.append((lineno, first, colcount))

        # numeric id parse
        s = (first or "").strip()
        if re.fullmatch(r"\d+", s):
            ids.append(int(s))
        else:
            if len(bad_id_rows) < 50:
                bad_id_rows.append((lineno, first, colcount))

seen = set(ids)
missing = [x for x in range(1, 10001) if x not in seen]

c = Counter(ids)
dups = [k for k,v in c.items() if v > 1]
dups.sort()

print("FILE:", str(p))
print("HEADER_COLS:", exp)
print("ROWS_WITH_NUMERIC_ID:", len(ids))
print("MISSING_COUNT:", len(missing))
print("DUP_ID_COUNT:", len(dups))

print("MISSING_HEAD_50:", missing[:50])
print("DUP_HEAD_50:", dups[:50])

print("BAD_COLS_FIRST50 (lineno, firstcell, colcount):")
for x in bad_cols_rows:
    print("  ", x)

print("BAD_ID_FIRST50 (lineno, firstcell, colcount):")
for x in bad_id_rows:
    print("  ", x)
