import os, csv, re, argparse, time
from datetime import datetime
from openai import OpenAI

LABEL_NAME = {
  '01':'ログイン時','02':'注文前商品選定中','03':'注文手続き中',
  '04':'注文後出荷前','05':'出荷後到着前','06':'到着後','07':'不明'
}

def clean(v: str) -> str:
    v = (v or '').replace('\r', ' ').replace('\n', ' ')
    v = re.sub(r'\s+', ' ', v).strip()
    return v

def label(code: str) -> str:
    code = code if code in LABEL_NAME else '07'
    return f"{code} {LABEL_NAME[code]}"

def heuristic_code(timing_text: str) -> str:
    t = clean(timing_text)

    if (not t) or t in ('不明','不詳','記載なし'):
        return '07'

    # 固定ルール（確定）
    if 'カタログ送付の停止・変更依頼時' in t:
        return '02'
    if '請求書未着' in t:
        return '04'
    if ('注文後' in t) and ('FAX' in t):
        return '04'
    if re.search(r'購入後|ご購入後', t):
        return '06'

    # 強い語優先：06 > 05 > 03 > 04 > 02 > 01
    if re.search(r'到着後|商品到着後|受領後|受取後|届いた後|開梱|開封|組立|設置|使用|利用開始|不良|初期不良|破損|不足|返品|交換|不具合', t):
        return '06'
    if re.search(r'出荷後|出荷完了後|発送後|発送済|出荷済|配送|配送中|配達|配達当日|到着前|受取前|未着|届かない|到着予定|到着予定日|到着予定時刻超過|遅延|追跡|伝票|配送予定', t):
        return '05'
    if re.search(r'注文確定前|確認ページ|最終確定|注文手続き|注文中|注文時|カート|決済|支払い方法|クレジット|配送先選択|お届け先選択|指定日選択|入力|FAX送信前|FAX送信直後|FAX送信後|FAX注文書記入|FAX', t):
        return '03'
    if re.search(r'注文後|ご注文後|注文完了|注文完了直後|注文完了後|注文確定後|出荷前|発送前|出荷前〜出荷当日|請求書|納品書|領収書|インボイス|帳票|請求|入金|請求メール|入金予定日変更', t):
        return '04'
    if re.search(r'注文前|購入前|検討|購入検討|商品検討|商品選定|見積|仕様確認|在庫|納期確認|発注前|カタログ請求|カタログ閲覧|カタログ受取後', t):
        return '02'
    if re.search(r'ログイン|認証|パスワード|ID|サインイン', t):
        return '01'

    return '07'

def make_item(row: dict, col_timing: str, ctx_cols: list[str]) -> str:
    # AIには多列コンテキストを渡す（精度用）
    parts = [f"{col_timing}={clean(row.get(col_timing))}"]
    for c in ctx_cols:
        v = clean(row.get(c))
        if v:
            parts.append(f"{c}={v}")
    return ' / '.join(parts)

def ai_classify_codes(client: OpenAI, model: str, items: list[str]) -> list[str]:
    # AIにはコード(01-07)だけ返させる
    prompt = (
        "あなたは分類器。各入力を発生タイミングコード(01-07)に分類せよ。\n"
        "出力は必ずN行。i行目が入力iのコード。各行は 01,02,03,04,05,06,07 のいずれか2桁のみ。余計な文字禁止。\n\n"
        "定義(最優先語):\n"
        "- 06: 到着後/受領後/開梱/組立/設置/使用/不良/破損/不足/返品/交換\n"
        "- 05: 出荷後/発送後/配送中/配達当日/未着/届かない/到着予定/追跡/伝票\n"
        "- 03: 注文確定前/確認ページ/注文手続き/決済/支払い方法/配送先選択/指定日選択/FAX送信\n"
        "- 04: 注文後/注文完了/出荷前/請求書/納品書/領収書/インボイス/帳票/入金\n"
        "- 02: 注文前/購入前/検討/見積/商品選定/カタログ\n"
        "- 01: ログイン/認証/パスワード\n"
        "- 根拠なし: 07\n\n"
        "固定ルール:\n"
        "- 「カタログ送付の停止・変更依頼時」=> 02\n"
        "- 「請求書未着」=> 04\n"
        "- 「注文後」かつ「FAX」=> 04\n"
        "- 「購入後」=> 06\n\n"
        "入力:\n" + "\n".join([f"{i+1}. {it}" for i, it in enumerate(items)])
    )

    resp = client.responses.create(
        model=model,
        input=[{'role':'user','content':prompt}],
        temperature=0
    )
    lines = [x.strip() for x in (resp.output_text or '').splitlines() if x.strip()]

    out = []
    for ln in lines:
        m = re.search(r'0[1-7]', ln)
        out.append(m.group(0) if m else '07')
    return out

def write_chunk(out_path: str, header: list[str], rows: list[list[str]]):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default=r'.\outputs\all_merged.csv')
    ap.add_argument('--outdir', default=r'.\outputs\timing_chunks')
    ap.add_argument('--n', type=int, default=10000)
    ap.add_argument('--chunk', type=int, default=1000)      # 1000件ごと保存
    ap.add_argument('--ai_batch', type=int, default=80)     # 1 APIコール当たりの件数
    ap.add_argument('--sleep', type=float, default=0.15)
    ap.add_argument('--model', default=os.getenv('OPENAI_MODEL', 'gpt-5.2'))
    ap.add_argument('--col_timing', default='発生タイミング')
    ap.add_argument('--id_col', default='通話ID')
    ap.add_argument('--ctx_cols', default='大区分名,小区分名,意図要約(短),対象機能(Target Function),バリア要約(短),推定発生ページ,重要キーワード,緊急度,解決ステータス')
    args = ap.parse_args()

    ctx_cols = [c.strip() for c in args.ctx_cols.split(',') if c.strip()]
    client = OpenAI()

    t0 = time.time()
    total_read = 0
    chunk_index = 0
    ai_total = 0

    def log(msg: str):
        dt = datetime.now().strftime('%H:%M:%S')
        print(f"[{dt}] {msg}", flush=True)

    with open(args.src, 'r', encoding='utf-8', errors='replace', newline='') as f:
        r = csv.DictReader(f)
        fns = r.fieldnames or []
        if args.col_timing not in fns:
            raise SystemExit(f"列が見つかりません: {args.col_timing}")

        while total_read < args.n:
            # --- 1) 1000件分読み込む（または残り）
            buf = []
            for _ in range(args.chunk):
                if total_read >= args.n:
                    break
                try:
                    row = next(r)
                except StopIteration:
                    break
                buf.append(row)
                total_read += 1

            if not buf:
                break

            chunk_index += 1
            start_id = total_read - len(buf) + 1
            end_id = total_read
            log(f"chunk {chunk_index} read rows {start_id}-{end_id} (total {total_read})")

            # --- 2) ヒューリスティック確定 + AI対象抽出
            timings = [clean(x.get(args.col_timing)) for x in buf]
            codes = [''] * len(buf)
            need_idx, need_items = [], []

            for i, t in enumerate(timings):
                c = heuristic_code(t)
                if c != '07':
                    codes[i] = c
                else:
                    # AIに回す価値があるものだけ
                    if len(t) >= 4 and not re.fullmatch(r'[0-9\-\s;；/]+', t):
                        need_idx.append(i)
                        need_items.append(make_item(buf[i], args.col_timing, ctx_cols))
                    else:
                        codes[i] = '07'

            # --- 3) AIで残り判定（ai_batchずつ）
            if need_items:
                log(f"chunk {chunk_index} AI rows {len(need_items)} (heuristic fixed {len(buf)-len(need_items)})")
                ai_total += len(need_items)

                out_codes = []
                for j in range(0, len(need_items), args.ai_batch):
                    batch = need_items[j:j+args.ai_batch]
                    got = ai_classify_codes(client, args.model, batch)
                    if len(got) != len(batch):
                        got = (got + ['07'] * len(batch))[:len(batch)]
                    out_codes.extend(got)
                    time.sleep(args.sleep)

                for i, c in zip(need_idx, out_codes):
                    fixed = heuristic_code(timings[i])
                    codes[i] = fixed if fixed != '07' else c
            else:
                log(f"chunk {chunk_index} AI rows 0 (all heuristic)")

            # --- 4) chunk結果を書き出し（1000件ごと）
            out_rows = []
            for local_i, (row, code) in enumerate(zip(buf, codes), start=0):
                rid = clean(row.get(args.id_col)) or str(start_id + local_i)
                out_rows.append([rid, clean(row.get(args.col_timing)), label(code)])

            out_path = os.path.join(args.outdir, f"timing_{start_id:05d}_{end_id:05d}.csv")
            write_chunk(out_path, [args.id_col, args.col_timing, '発生タイミング_正規化'], out_rows)

            elapsed = time.time() - t0
            rate = total_read / elapsed if elapsed > 0 else 0
            eta = (args.n - total_read) / rate if rate > 0 else 0
            log(f"chunk {chunk_index} wrote {out_path} | elapsed {elapsed/60:.1f}m | rate {rate:.2f} rows/s | ETA {eta/60:.1f}m")

    log(f"DONE total_read={total_read} ai_total={ai_total} outdir={args.outdir}")

if __name__ == '__main__':
    main()
