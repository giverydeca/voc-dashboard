from pathlib import Path

out = Path(r".\outputs\fill_1_10000_merged_20260227_131928.csv")
per1 = Path(r".\outputs\per_input_1000")
per2 = Path(r".\outputs\per_input_2001_10000")
mid  = Path(r".\outputs\fill_1001_2000.csv")

def first_csv_line(p: Path) -> str:
    with p.open("r", encoding="utf-8", errors="replace") as f:
        return f.readline().rstrip("\n")

def iter_lines_skip1(p: Path):
    with p.open("r", encoding="utf-8", errors="replace") as f:
        _ = f.readline()
        for line in f:
            yield line

def iter_lines_all(p: Path):
    with p.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            yield line

# decide header
header = None
if mid.exists():
    header = first_csv_line(mid)
else:
    for d in (per1, per2):
        if d.exists():
            files = sorted(d.glob("*.csv"))
            if files:
                header = first_csv_line(files[0])
                break

if not header:
    raise SystemExit("No header source found (missing mid and per_input dirs empty).")

out.parent.mkdir(parents=True, exist_ok=True)

with out.open("w", encoding="utf-8", newline="\n") as w:
    w.write(header + "\n")

    # 1001-2000 combined (skip header)
    if mid.exists():
        for line in iter_lines_skip1(mid):
            w.write(line if line.endswith("\n") else line + "\n")

    def add_dir(d: Path):
        if not d.exists():
            return
        files = sorted(d.glob("*.csv"))
        if not files:
            return
        first = first_csv_line(files[0])
        drop = (first == header) or ("通話ID" in first and "通話ID" in header)
        for f in files:
            it = iter_lines_skip1(f) if drop else iter_lines_all(f)
            for line in it:
                w.write(line if line.endswith("\n") else line + "\n")

    add_dir(per1)
    add_dir(per2)

print("WROTE", out)
