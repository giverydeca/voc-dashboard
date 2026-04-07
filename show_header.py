import pathlib, csv, io
f = sorted(pathlib.Path(r"outputs\batch_00001_01000").glob("*.csv"))[0]
rows = list(csv.reader(io.StringIO(f.read_text(encoding="utf-8"))))
for i, h in enumerate(rows[0]):
    print(f"{i:2d}: {h}")
