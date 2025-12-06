\
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON/JSONL → logs.jsonl 追記インポート
Usage:
  python tools/import_json_to_logs.py --input data/raw/my_logs.json --uid Mash
  python tools/import_json_to_logs.py --input data/raw/my_logs.jsonl --uid Mash
"""
import json, os, argparse
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

def norm_entry(entry: dict, default_uid: str):
    if "ts" not in entry or "emotion" not in entry:
        return None, "missing ts or emotion"
    ts = entry["ts"]
    emo = entry["emotion"]
    try:
        ts_iso = parse_ts(ts)
    except ValueError as e:
        return None, str(e)
    out = {
        "uid": entry.get("uid") or default_uid or "U1",
        "ts": ts_iso,
        "emotion": emo
    }
    if "strength" in entry:
        try:
            out["strength"] = float(entry["strength"])
        except Exception:
            pass
    kws = entry.get("keywords")
    if isinstance(kws, str):
        # split by common separators
        import re
        parts = re.split(r",|、|\s+", kws)
        kws = [p.strip() for p in parts if p.strip()]
    if isinstance(kws, list) and kws:
        out["keywords"] = kws
    note = entry.get("note")
    if isinstance(note, str) and note.strip():
        out["note"] = note
    return out, None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", default="data/raw/logs.jsonl")
    ap.add_argument("--uid", default=None)
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    appended = 0
    with open(args.out, "a", encoding="utf-8") as w:
        with open(args.input, "r", encoding="utf-8") as f:
            first = f.read(1)
            f.seek(0)
            if first == "[":
                arr = json.load(f)
                for i, e in enumerate(arr, start=1):
                    obj, err = norm_entry(e, args.uid)
                    if obj is None:
                        print(f"[skip] idx {i}: {err}")
                        continue
                    w.write(json.dumps(obj, ensure_ascii=False) + "\n")
                    appended += 1
            else:
                # JSONL
                for i, line in enumerate(f, start=1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        e = json.loads(line)
                    except Exception:
                        print(f"[skip] line {i}: not valid JSON")
                        continue
                    obj, err = norm_entry(e, args.uid)
                    if obj is None:
                        print(f"[skip] line {i}: {err}")
                        continue
                    w.write(json.dumps(obj, ensure_ascii=False) + "\n")
                    appended += 1
    print(f"[done] appended={appended}, out={args.out}")

if __name__ == "__main__":
    main()
