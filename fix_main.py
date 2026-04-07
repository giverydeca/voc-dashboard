f = open('pycsv/main.py', 'r', encoding='utf-8')
content = f.read()
f.close()

old = '    rows = read_tsv_rows(args.input_tsv)\n    if args.max_calls and args.max_calls > 0:\n        rows = rows[: args.max_calls]\n\n    start_id: int = getattr(args, "start_id", 1)'
new = '    rows = read_tsv_rows(args.input_tsv)\n    if args.skip_rows and args.skip_rows > 0:\n        rows = rows[args.skip_rows:]\n    if args.max_calls and args.max_calls > 0:\n        rows = rows[: args.max_calls]\n\n    start_id: int = args.start_id'

if old in content:
    content = content.replace(old, new)
    f = open('pycsv/main.py', 'w', encoding='utf-8')
    f.write(content)
    f.close()
    print('完了')
else:
    print('見つかりませんでした')
