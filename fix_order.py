import pathlib, re

path = pathlib.Path(r"pycsv\main.py")
src = path.read_text(encoding="utf-8")

# OP NAME EXTRACTORブロックを切り出す
marker_start = "# ===== OP NAME EXTRACTOR"
marker_end   = "# ===== /OP NAME EXTRACTOR ====="

i_start = src.find(marker_start)
i_end   = src.find(marker_end)
if i_start == -1 or i_end == -1:
    print("ERROR: マーカーが見つかりません")
    print("  marker_start found:", i_start != -1)
    print("  marker_end   found:", i_end   != -1)
    exit(1)

# ブロック全体（末尾改行含む）
block = src[i_start : i_end + len(marker_end)].rstrip()

# 元の位置から削除
without_block = src[:i_start].rstrip() + "\n" + src[i_end + len(marker_end):]

# if __name__ の直前に挿入
target = 'if __name__ == "__main__":'
if target not in without_block:
    print("ERROR: if __name__ が見つかりません")
    exit(1)

new_src = without_block.replace(
    target,
    block + "\n\n" + target,
    1
)

path.write_text(new_src, encoding="utf-8")
print("DONE: OP NAME EXTRACTOR を if __name__ の前に移動しました")
