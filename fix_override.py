import pathlib

path = pathlib.Path(r"pycsv\main.py")
src  = path.read_text(encoding="utf-8")

# 変更1: json_to_csv_text の op_name_override 上書きをコメントアウト
OLD1 = '''           if op_name_override and op_name_override != "不明":
               rec["オペレーター名"] = op_name_override'''
NEW1 = '''           # op_name_override による強制上書きを無効化（LLMに委ねる）
           # if op_name_override and op_name_override != "不明":
           #     rec["オペレーター名"] = op_name_override'''

# 変更2: build_call_input_text のヒント埋め込みを改善
OLD2 = 'def build_call_input_text(fp, flag, txt):'
NEW2 = 'def build_call_input_text(fp, flag, txt):  # ヒント付き版'

if OLD1 in src:
    src = src.replace(OLD1, NEW1, 1)
    print("OK: op_name_override 無効化")
else:
    # インデントの違いに対応して再検索
    import re
    pat = re.compile(
        r'( *)if op_name_override and op_name_override != "不明":\s*\n'
        r'\s*rec\["オペレーター名"\] = op_name_override'
    )
    m = pat.search(src)
    if m:
        old = m.group(0)
        indent = m.group(1)
        new = (f'{indent}# op_name_override による強制上書きを無効化（LLMに委ねる）\n'
               f'{indent}# if op_name_override and op_name_override != "不明":\n'
               f'{indent}#     rec["オペレーター名"] = op_name_override')
        src = src.replace(old, new, 1)
        print("OK: op_name_override 無効化（インデント調整版）")
    else:
        print("SKIP: op_name_override 該当箇所なし → 手動確認が必要")
        for i, line in enumerate(src.splitlines(), 1):
            if "op_name_override" in line:
                print(f"  {i:4d}: {line}")

path.write_text(src, encoding="utf-8")

import py_compile, sys
try:
    py_compile.compile(str(path), doraise=True)
    print("OK: 構文チェック通過")
except py_compile.PyCompileError as e:
    print(f"ERROR: {e}")
    sys.exit(1)

print("DONE")
