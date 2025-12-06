\
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV → logs.jsonl 追記インポート
Usage:
  python tools/import_csv_to_logs.py --input data/raw/my_logs.csv --uid Mash
Options:
  --out data/raw/logs.jsonl
  --ts-col ts --emotion-col emotion --strength-col strength --keywords-col keywords --note-col note --uid-col uid
  --keywords-sep ","   # 分割文字。複数指定可: ",|、| "
"""
import csv, json, os, argparse, re
from datetime import datetime

def parse_ts(s: str) -> str:
    s = s.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        datetime.fromisoformat(s)
        return s
    except Exception:
        raise ValueError(f"Invalid ISO timestamp: {s}")

def split_keywords(s: str, sep_regex: str):
    s = s.strip()
    if not s:
        return []
    parts = re.split(sep_regex, s)
    return [p.strip() for p in parts if p.strip()]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", default="data/raw/logs.jsonl")
    ap.add_argument("--uid", default=None)
    ap.add_argument("--ts-col", default="ts")
    ap.add_argument("--emotion-col", default="emotion")
    ap.add_argument("--strength-col", default="strength")
    ap.add_argument("--keywords-col", default="keywords")
    ap.add_argument("--note-col", default="note")
    ap.add_argument("--uid-col", default="uid")
    ap.add_argument("--keywords-sep", default=r",|、|\s+")
    args = ap.parse_args()

    rows = 0
    added = 0
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.input, "r", encoding="utf-8-sig") as f, open(args.out, "a", encoding="utf-8") as w:
        reader = csv.DictReader(f)
        for r in reader:
            rows += 1
            ts = r.get(args.ts_col, "").strip()
            emo = r.get(args.emotion_col, "").strip()
            if not ts or not emo:
                print(f"[skip] row {rows}: missing ts or emotion")
                continue
            try:
                ts_iso = parse_ts(ts)
            except ValueError as e:
                print(f"[skip] row {rows}: {e}")
                continue

            uid = (r.get(args.uid_col) or args.uid or "U1").strip()
            strength_raw = r.get(args.strength_col, "").strip()
            strength = None
            if strength_raw:
                try:
                    strength = float(strength_raw)
                except Exception:
                    print(f"[warn] row {rows}: strength not a number -> ignore")
            kw_raw = r.get(args.keywords_col, "")
            keywords = split_keywords(kw_raw, args.keywords_sep) if kw_raw else []
            note = r.get(args.note_col, "")

            obj = {"uid": uid, "ts": ts_iso, "emotion": emo}
            if strength is not None:
                obj["strength"] = strength
            if keywords:
                obj["keywords"] = keywords
            if note:
                obj["note"] = note

            w.write(json.dumps(obj, ensure_ascii=False) + "\n")
            added += 1

    print(f"[done] read={rows}, appended={added}, out={args.out}")

if __name__ == "__main__":
    main()
