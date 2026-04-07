import csv, re
from pathlib import Path

IN_TSV = Path(r'.\data\calls.tsv')
OUT_CSV = Path(r'.\outputs\fulltext_head10.csv')
N = 10

def clean_text(s: str) -> str:
    s = s or ""
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = s.replace("\n", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s

# かなり保守的な話者推定（誤爆を減らす）
OP_CUES = [
    r"お電話ありがとうございます", r"お世話になっております", r"ストアエキスプレス", r"担当", r"でございます",
    r"承ります", r"承っております", r"少々お待ちください", r"確認いたします", r"かしこまりました",
    r"失礼いたします", r"恐れ入ります", r"申し訳ございません",
]
CU_CUES = [
    r"注文", r"キャンセル", r"届", r"到着", r"未着", r"納期", r"在庫", r"請求書", r"納品書", r"領収書",
    r"インボイス", r"ログイン", r"会員登録", r"住所", r"決済", r"クレジット", r"支払",
]

def guess_speaker(seg: str, prev: str) -> str:
    t = seg.strip()
    if not t:
        return prev or "CU"
    # 明確な敬語・定型があるならOP優先
    if any(re.search(p, t) for p in OP_CUES):
        return "OP"
    # 質問・要望っぽさ＋用件語はCU寄り
    if re.search(r"(できますか|でしょうか|したい|したのですが|困って|教えて|お願い)", t):
        return "CU"
    if any(re.search(p, t) for p in CU_CUES):
        return "CU"
    return prev or "CU"

def segment(text: str):
    # 句点/？/！で粗く分割（ASRの改行が潰れている前提）
    # ※分割しすぎ防止で短すぎは前に結合
    raw = re.split(r"(?<=[。！？\?！])\s+", text)
    segs = []
    for r in raw:
        r = r.strip()
        if not r:
            continue
        if segs and len(r) <= 4:
            segs[-1] = segs[-1] + " " + r
        else:
            segs.append(r)
    return segs

def to_dialogue(text: str) -> str:
    text = clean_text(text)
    if not text:
        return "なし"
    segs = segment(text)
    out = []
    prev = ""
    for s in segs:
        sp = guess_speaker(s, prev)
        out.append(f"{sp}: {s}")
        prev = sp
    # OP/CU表記に合わせる
    out = [x.replace("OP:", "OP:").replace("CU:", "CU:") for x in out]
    return " ".join(out)

def main():
    with IN_TSV.open("r", encoding="utf-8", errors="replace", newline="") as f:
        # TSVとして読む（最低3列想定）
        reader = csv.reader(f, delimiter="\t")
        rows = []
        for row in reader:
            if not row:
                continue
            # ヘッダーらしければスキップ（file_path等）
            if row[0].lower().startswith("file") and len(row) >= 3:
                continue
            rows.append(row)
            if len(rows) >= N:
                break

    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["row_id", "file_path", "flag", "会話全文(整形済)"])
        for i, r in enumerate(rows, start=1):
            file_path = r[0] if len(r) >= 1 else ""
            flag = r[1] if len(r) >= 2 else ""
            text = r[2] if len(r) >= 3 else ""
            full = to_dialogue(text)
            w.writerow([i, file_path, flag, full])

    print("WROTE", OUT_CSV)

if __name__ == "__main__":
    main()
