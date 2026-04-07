import pathlib, re

path = pathlib.Path(r"pycsv\openai_csv.py")
src = path.read_text(encoding="utf-8")

old = '''        raise RuntimeError(f"{label}: JSON parse failed: {e}\\nHEAD={t[:400]}")'''
new = '''        import sys
        print(f"[WARN] {label}: JSON parse failed (skipped): {e}", file=sys.stderr)
        return []'''

if old in src:
    src = src.replace(old, new)
    path.write_text(src, encoding="utf-8")
    print("OK: エラースキップに変更")
else:
    print("SKIP: 該当行が見つかりません")
