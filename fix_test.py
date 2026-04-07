def fix_mojibake(s):
    """UTF-8テキストをCP932として誤読した文字列を修復"""
    try:
        return s.encode('cp932').decode('utf-8')
    except Exception as e:
        return f"[修復失敗: {e}]"

with open(r"data\calls_10.tsv", encoding="utf-8-sig", errors="replace") as f:
    lines = f.readlines()

for i, line in enumerate(lines[:3], 1):
    cols = line.split("\t")
    txt = cols[2][:120] if len(cols) >= 3 else ""
    fixed = fix_mojibake(txt)
    print(f"=== 行{i} ===")
    print(f"修復前: {txt[:80]}")
    print(f"修復後: {fixed[:80]}")
    print()
