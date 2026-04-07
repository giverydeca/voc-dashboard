import pathlib, re

path = pathlib.Path(r"pycsv\main.py")
src  = path.read_text(encoding="utf-8")

# 変更A: argparse に --start-id を追加
OLD_A = '    parser.add_argument("--concurrency"'
NEW_A = '''    parser.add_argument("--start-id", type=int, default=1,
                        help="出力CSVの通話IDの開始番号 (default=1)")
    parser.add_argument("--concurrency"'''

# 変更B: run() 内で start_id を受け取り CsvFile に渡す
OLD_B = '    files: list[CsvFile] = []'
NEW_B = '''    start_id: int = args.start_id
    files: list[CsvFile] = []'''

# 変更C: json_to_csv_text 呼び出しに start_id オフセットを渡す
# perInput モードの書き出し部分を特定して採番をオフセット
OLD_C = '            csv_out = json_to_csv_text(json_out, op_name_override=_op)'
NEW_C = '            csv_out = json_to_csv_text(json_out, op_name_override=_op, id_offset=start_id - 1)'

# 変更D: json_to_csv_text の定義に id_offset を追加
OLD_D = 'def json_to_csv_text(json_text: str, op_name_override'
NEW_D = 'def json_to_csv_text(json_text: str, op_name_override'

changes = [
    ("変更A: --start-id 引数追加",  OLD_A, NEW_A),
    ("変更B: start_id 変数宣言",    OLD_B, NEW_B),
    ("変更C: id_offset 渡し",       OLD_C, NEW_C),
]

for label, old, new in changes:
    if old in src:
        src = src.replace(old, new, 1)
        print(f"OK   {label}")
    else:
        print(f"SKIP {label}: 該当箇所なし")

# 変更D: json_to_csv_text の id_offset 対応
OLD_D2 = 'def json_to_csv_text(json_text: str, op_name_override: Optional[str] = None) -> str:'
NEW_D2 = 'def json_to_csv_text(json_text: str, op_name_override: Optional[str] = None, id_offset: int = 0) -> str:'
OLD_E  = '        rec["通話ID"] = str(i)'
NEW_E  = '        rec["通話ID"] = str(i + id_offset)'

for label, old, new in [
    ("変更D: json_to_csv_text シグネチャ", OLD_D2, NEW_D2),
    ("変更E: 通話ID オフセット適用",       OLD_E,  NEW_E),
]:
    if old in src:
        src = src.replace(old, new, 1)
        print(f"OK   {label}")
    else:
        print(f"SKIP {label}: 該当箇所なし")

path.write_text(src, encoding="utf-8")

import py_compile, sys
try:
    py_compile.compile(str(path), doraise=True)
    print("OK   構文チェック通過")
except py_compile.PyCompileError as e:
    print(f"ERROR 構文エラー: {e}")
    sys.exit(1)

print("DONE: main.py 更新完了")
