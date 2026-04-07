import csv, json, os, time
from openai import OpenAI

client = OpenAI()  # OPENAI_API_KEY 環境変数から自動取得

NO_ISSUE = ['確認できず','言及なし','発生していない','課題なし','なし','不明','できず','指摘なし','問題なし']

# バリア要約を収集（課題なし除外）
with open(r'outputs\all_merged.csv', encoding='utf-8') as f:
    rows = list(csv.reader(f))

barriers = []
for row in rows[1:]:
    if len(row) > 20:
        v = row[20].strip()
        if v and not any(k in v for k in NO_ISSUE):
            barriers.append(v)

# ユニーク値のみで集計
from collections import Counter
counter = Counter(barriers)
unique_barriers = list(counter.keys())
print(f"ユニークバリア数: {len(unique_barriers)}")

# バッチ50件ずつAIでカテゴリ分け
BATCH = 50
results = []

for i in range(0, len(unique_barriers), BATCH):
    batch = unique_barriers[i:i+BATCH]
    items = "\n".join([f"{j+1}. {v}" for j, v in enumerate(batch)])
    
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"""以下のコールセンター通話バリア（障壁・課題）を、意味が近いものをグループ化して
カテゴリ名を付けてください。JSONで返してください。
形式: [{{"category": "カテゴリ名", "items": ["バリア1", "バリア2", ...]}}]

バリア一覧:
{items}"""
        }],
        response_format={"type": "json_object"},
        max_tokens=2000
    )
    
    try:
        data = json.loads(resp.choices[0].message.content)
        cats = data.get("categories", data.get("items", [data]))
        if isinstance(cats, list):
            for cat in cats:
                if isinstance(cat, dict):
                    cat_name = cat.get("category", "不明")
                    for item in cat.get("items", []):
                        results.append({"barrier": item, "category": cat_name, "count": counter.get(item, 0)})
    except Exception as e:
        print(f"バッチ {i//BATCH+1} エラー: {e}")
    
    time.sleep(0.5)
    print(f"進捗: {min(i+BATCH, len(unique_barriers))}/{len(unique_barriers)}")

# 結果を保存
with open(r'outputs\barrier_categories.csv', 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['category','barrier','count'])
    writer.writeheader()
    writer.writerows(sorted(results, key=lambda x: (-x['count'], x['category'])))

print("完了: outputs\\barrier_categories.csv に保存しました")
