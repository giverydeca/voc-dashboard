import re, pathlib
from collections import Counter

path = pathlib.Path(r"data\calls.tsv")
with open(path, encoding="utf-8-sig", errors="replace") as f:
    lines = f.readlines()

# 改良版: 店名を広く取り、末尾の名前だけ抽出
pattern = re.compile(
    r'(?:'
    r'[^\s　。]{0,8}?'           # 定検装置 などの前置き
    r'(?:ストア|スター|ス[トタ]ア)'   # 店名の始まり
    r'[^\s　、。]{0,12}?'         # エキスプレス等(長めに取る)
    r')'
    r'[、,\s　・]*'
    r'([^\s　、。でございとにはをがもの]{2,8}?)'  # ← ここが名前
    r'(?:でございます|と申します|が受けたまわります|でございます)',
    re.MULTILINE
)

names = Counter()
raw_samples = {}

for line in lines:
    cols = line.split("\t")
    if len(cols) >= 3:
        txt = cols[2][:400]
        for m in pattern.finditer(txt):
            name = m.group(1)
            # 店名カタカナが残っている場合は末尾の漢字/ひらがな部分だけ取る
            cleaned = re.sub(r'^[ァ-ヶー・]+', '', name).strip()
            if cleaned:
                names[cleaned] += 1
                raw_samples[cleaned] = m.group(0)[:40]

print("=== 全件 OP名候補 ===")
for name, cnt in names.most_common():
    print(f"  {cnt:3d}回: [{name}]  例: {raw_samples[name]}")
