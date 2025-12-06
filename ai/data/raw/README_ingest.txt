CocolonAI Raw Ingestion Guide
=============================

受け付ける入力
--------------
- CSV: ヘッダーに `ts,emotion,strength,keywords,note,uid` のいずれか（不足可）
- JSONL: 1行1レコード（スキーマは schema.json 参照）
- JSON: 配列として複数レコード

フィールド仕様
--------------
- ts: ISO8601日時 "YYYY-MM-DDTHH:MM:SS"（Z/オフセットもOK）
- emotion: 任意ラベル（例: Sadness, Joy, Anxiety, Calm など）
- strength: 0.0〜1.0（任意）
- keywords: 配列 or 文字列（カンマ/スペース/読点で分割）
- note: 任意のメモ
- uid: ユーザーID（未指定なら引数 --uid の値を利用）

使い方（CSV）
-------------
python tools/import_csv_to_logs.py --input data/raw/my_logs.csv --uid Mash

使い方（JSON/JSONL）
--------------------
python tools/import_json_to_logs.py --input data/raw/my_logs.json  --uid Mash
python tools/import_json_to_logs.py --input data/raw/my_logs.jsonl --uid Mash

検証（バリデーション）
----------------------
python tools/validate_logs.py --input data/raw/logs.jsonl

構造抽出（非GPT）
-----------------
python services/structure_engine/extract.py
→ data/processed/features.json / summary.txt を生成
