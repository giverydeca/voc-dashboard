import pathlib

path = pathlib.Path(r"pycsv\main.py")
lines = path.read_text(encoding="utf-8").splitlines(keepends=True)

# 123行目 (0-indexed: 122) の直前に挿入
insert_line = 122  # 0-indexed
new_line = '    start_id: int = getattr(args, "start_id", 1)\n'

if 'start_id' in lines[insert_line - 1] or 'start_id' in lines[insert_line]:
    print("SKIP: すでに start_id が存在します")
else:
    lines.insert(insert_line, new_line)
    path.write_text("".join(lines), encoding="utf-8")
    print(f"OK: {insert_line+1}行目に start_id 宣言を挿入")

import py_compile, sys
try:
    py_compile.compile(str(path), doraise=True)
    print("OK: 構文チェック通過")
except py_compile.PyCompileError as e:
    print(f"ERROR: {e}")
    sys.exit(1)

print("DONE")
