import csv, re, sys, time
from pathlib import Path

old_dir = Path(sys.argv[1])
out_path = Path(sys.argv[2])

files = sorted(old_dir.glob("*.csv"))
print("files:", len(files), flush=True)

bad_ids = []
seen = set()

def read_two_rows(p: Path):
    with p.open("r", encoding="utf-8", errors="replace", newline="") as f:
        r = csv.reader(f)
        header = next(r, None)
        row1 = next(r, None)
    return header, row1

t0 = time.time()
for i, p in enumerate(files, start=1):
    if i % 500 == 0:
        print(f"progress: {i}/{len(files)} bad={len(bad_ids)} elapsed={time.time()-t0:.1f}s", flush=True)
    try:
        header, row1 = read_two_rows(p)
        hc = len(header) if header else 0
        rc = len(row1) if row1 else 0
        cid = (row1[0].strip() if row1 and len(row1)>0 else "")
        ok = (hc == 44 and rc == 44 and re.fullmatch(r"\d+", cid or "") is not None)
        if not ok:
            if cid and cid not in seen:
                bad_ids.append(cid)
                seen.add(cid)
            elif not cid:
                bad_ids.append(f"NO_ID::{p.name}")
    except Exception as e:
        bad_ids.append(f"UNREADABLE::{p.name}")

# split numeric vs misc
bad_num = sorted({int(x) for x in bad_ids if isinstance(x,str) and x.isdigit()})
bad_misc = [x for x in bad_ids if not (isinstance(x,str) and x.isdigit())]

out_path.parent.mkdir(parents=True, exist_ok=True)
with out_path.open("w", encoding="utf-8", newline="\n") as w:
    for x in bad_num:
        w.write(str(x) + "\n")
    for x in bad_misc:
        w.write(str(x) + "\n")

print("bad_numeric_ids:", len(bad_num))
print("bad_misc:", len(bad_misc))
print("wrote:", out_path)
print("head20_numeric:", bad_num[:20])
if bad_misc:
    print("head20_misc:", bad_misc[:20])
