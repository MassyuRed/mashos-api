\
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CocolonAI Data Importer
-----------------------
実データ（CSV/JSON/JSONL）を、標準スキーマ logs.jsonl に変換して保存します。

Usage examples:
  python tools/import_logs.py --src data/raw/mylogs.csv --mapping tools/import_mapping.yaml
  python tools/import_logs.py --src data/raw/mylogs.jsonl
  python tools/import_logs.py --src data/raw/mylogs.json --out data/raw/logs.jsonl

標準スキーマ（1行1レコード/JSON Lines）:
  {
    "uid": "U1",                    # 任意（なければ "U1" を付与）
    "ts": "2025-10-20T22:15:00",    # ISO8601 (yyyy-MM-ddTHH:mm:ss)
    "emotion": "Sadness",           # 英語ラベル（emotion_mapで正規化）
    "strength": 0.7,                # 0.0〜1.0
    "keywords": ["孤独","疲労"],     # リスト（区切りを正規化）
    "note": "帰宅してから急に沈んだ" # 任意
  }
"""
import os, sys, json, csv, argparse, re, datetime

try:
    import yaml
except Exception:
    yaml = None  # mapping未使用なら不要

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_OUT = os.path.join(ROOT, "data", "raw", "logs.jsonl")
ERROR_LOG = os.path.join(ROOT, "data", "raw", "import_errors.log")

def load_yaml(path):
    if path is None:
        return {}
    if yaml is None:
        raise SystemExit("PyYAML が必要です。`pip install pyyaml` してから実行してください。")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def detect_format(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in [".csv"]:
        return "csv"
    if ext in [".jsonl", ".jsonl.txt"]:
        return "jsonl"
    if ext in [".json"]:
        return "json"
    raise SystemExit(f"未対応の拡張子です: {ext}")

def parse_keywords(raw, delim_pattern):
    if raw is None:
        return []
    parts = re.split(delim_pattern, str(raw))
    out = [p.strip() for p in parts if p and p.strip()]
    # 重複除去
    seen = set()
    uniq = []
    for w in out:
        if w not in seen:
            seen.add(w)
            uniq.append(w)
    return uniq

def norm_strength(raw, scale):
    if raw is None or str(raw).strip() == "":
        return None
    try:
        v = float(raw)
    except Exception:
        return None
    if scale == "0-100":
        return max(0.0, min(1.0, v/100.0))
    # default "0-1"
    return max(0.0, min(1.0, v))

def norm_emotion(raw, emo_map):
    if raw is None:
        return None
    s = str(raw).strip()
    if s in emo_map:
        return emo_map[s]
    # 小文字比較も試みる
    if s.lower() in emo_map:
        return emo_map[s.lower()]
    return s  # そのまま返す（後で検証で拾う）

def parse_ts(raw):
    if raw is None or str(raw).strip() == "":
        return None
    s = str(raw).strip()
    # 簡易バリデーション（厳密なtzは要求しない）
    try:
        # 2025-10-20T22:15:00
        datetime.datetime.fromisoformat(s)
        return s
    except Exception:
        # 許容: "2025/10/20 22:15" など → 可能なら置換
        s2 = s.replace("/", "-").replace(" ", "T")
        try:
            datetime.datetime.fromisoformat(s2)
            return s2
        except Exception:
            return None

def write_error(msg):
    os.makedirs(os.path.dirname(ERROR_LOG), exist_ok=True)
    with open(ERROR_LOG, "a", encoding="utf-8") as f:
        f.write(msg.rstrip() + "\n")

def import_csv(src, out_path, cfg):
    mapping = (cfg.get("mapping") or {})
    kw_delim = cfg.get("keywords_delimiter", r"[,;、／/|]")
    scale = cfg.get("strength_scale", "0-1")
    emo_map = (cfg.get("emotion_map") or {})
    defaults = (cfg.get("defaults") or {})
    cnt_in, cnt_ok, cnt_ng = 0, 0, 0

    with open(src, "r", encoding="utf-8") as f, open(out_path, "a", encoding="utf-8") as w:
        reader = csv.DictReader(f)
        for row in reader:
            cnt_in += 1
            ts = parse_ts(row.get(mapping.get("timestamp", "ts")))
            emo = norm_emotion(row.get(mapping.get("emotion", "emotion")), emo_map) or defaults.get("emotion", "Unknown")
            strength = norm_strength(row.get(mapping.get("strength", "strength")), scale)
            keywords = parse_keywords(row.get(mapping.get("keywords", "keywords")), kw_delim)
            note = row.get(mapping.get("note", "note"), "")
            uid = row.get(mapping.get("uid", "uid"), "U1")

            if ts is None:
                write_error(f"[{cnt_in}] invalid timestamp: {row}")
                cnt_ng += 1
                continue
            r = {
                "uid": uid,
                "ts": ts,
                "emotion": emo,
                "strength": strength if strength is not None else 0.0,
                "keywords": keywords,
                "note": note
            }
            w.write(json.dumps(r, ensure_ascii=False) + "\n")
            cnt_ok += 1
    return cnt_in, cnt_ok, cnt_ng

def import_json(src, out_path):
    cnt_in, cnt_ok, cnt_ng = 0, 0, 0
    with open(src, "r", encoding="utf-8") as f, open(out_path, "a", encoding="utf-8") as w:
        data = json.load(f)
        if isinstance(data, dict):
            data = [data]
        for row in data:
            cnt_in += 1
            ts = parse_ts(row.get("ts"))
            if ts is None:
                write_error(f"[{cnt_in}] invalid timestamp: {row}")
                cnt_ng += 1
                continue
            emo = row.get("emotion", "Unknown")
            strength = row.get("strength", 0.0)
            keywords = row.get("keywords") or []
            note = row.get("note", "")
            uid = row.get("uid", "U1")
            r = {"uid": uid, "ts": ts, "emotion": emo, "strength": strength, "keywords": keywords, "note": note}
            w.write(json.dumps(r, ensure_ascii=False) + "\n")
            cnt_ok += 1
    return cnt_in, cnt_ok, cnt_ng

def import_jsonl(src, out_path):
    cnt_in, cnt_ok, cnt_ng = 0, 0, 0
    with open(src, "r", encoding="utf-8") as f, open(out_path, "a", encoding="utf-8") as w:
        for line in f:
            line = line.strip()
            if not line:
                continue
            cnt_in += 1
            try:
                row = json.loads(line)
            except Exception:
                write_error(f"[{cnt_in}] invalid json line: {line[:120]} ...")
                cnt_ng += 1
                continue
            ts = parse_ts(row.get("ts"))
            if ts is None:
                write_error(f"[{cnt_in}] invalid timestamp: {row}")
                cnt_ng += 1
                continue
            emo = row.get("emotion", "Unknown")
            strength = row.get("strength", 0.0)
            keywords = row.get("keywords") or []
            note = row.get("note", "")
            uid = row.get("uid", "U1")
            r = {"uid": uid, "ts": ts, "emotion": emo, "strength": strength, "keywords": keywords, "note": note}
            w.write(json.dumps(r, ensure_ascii=False) + "\n")
            cnt_ok += 1
    return cnt_in, cnt_ok, cnt_ng

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="入力ファイル（csv/json/jsonl）")
    ap.add_argument("--mapping", default=None, help="CSV用の列名マッピングYAML")
    ap.add_argument("--out", default=DEFAULT_OUT, help="出力先 logs.jsonl （既定: data/raw/logs.jsonl）")
    ap.add_argument("--backup", action="store_true", help="既存logs.jsonlをバックアップしてから追記")
    args = ap.parse_args()

    fmt = detect_format(args.src)
    if args.backup and os.path.exists(args.out):
        base, ext = os.path.splitext(args.out)
        bak = f"{base}.backup.{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}{ext}"
        os.rename(args.out, bak)
        print("Backup:", bak)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    cfg = load_yaml(args.mapping) if (fmt == "csv") else {}

    if fmt == "csv":
        i, ok, ng = import_csv(args.src, args.out, cfg)
    elif fmt == "json":
        i, ok, ng = import_json(args.src, args.out)
    else:
        i, ok, ng = import_jsonl(args.src, args.out)

    print(f"Imported: {ok}/{i}  (skipped: {ng})")
    if os.path.exists(ERROR_LOG):
        print("Errors logged to:", ERROR_LOG)

if __name__ == "__main__":
    main()
