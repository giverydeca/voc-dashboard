import pathlib, re

base = pathlib.Path(".")
targets = []
for ext in ["*.py", "*.sh", "*.bat", "*.ps1"]:
    targets.extend(base.rglob(ext))

for p in sorted(targets):
    if "node_modules" in str(p):
        continue
    try:
        src = p.read_text(encoding="utf-8", errors="replace")
        if "calls.tsv" in src or ".tsv" in src:
            lines = [(i+1, l) for i, l in enumerate(src.splitlines())
                     if ".tsv" in l or "encoding" in l.lower() or "whisper" in l.lower()]
            if lines:
                print(f"\n=== {p} ===")
                for no, l in lines[:15]:
                    print(f"  {no:4d}: {l}")
    except:
        pass
