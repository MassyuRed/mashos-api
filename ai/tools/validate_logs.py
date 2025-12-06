\
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate logs.jsonl format for CocolonAI pipeline.
"""
import os, json, argparse, datetime, re
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_IN = os.path.join(ROOT, "data", "raw", "logs.jsonl")

EMOTIONS = {"Sadness","Anxiety","Calm","Joy","Anger","Fear","Surprise","Disgust","Unknown"}

def parse_ts(s):
    try:
        datetime.datetime.fromisoformat(s)
        return True
    except Exception:
        return False

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=DEFAULT_IN)
    args = ap.parse_args()

    missing = 0
    invalid_ts = 0
    emo_counts = Counter()
    n = 0

    if not os.path.exists(args.src):
        raise SystemExit(f"not found: {args.src}")

    with open(args.src, "r", encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if not line: 
                continue
            n += 1
            try:
                row = json.loads(line)
            except Exception:
                print("[bad json]", line[:120], "...")
                continue
            ok = True
            for k in ["uid","ts","emotion"]:
                if k not in row:
                    ok = False
            if not ok:
                missing += 1
            if not parse_ts(row.get("ts","")):
                invalid_ts += 1
            emo = row.get("emotion","Unknown")
            if emo not in EMOTIONS:
                emo = "Unknown"
            emo_counts[emo]+=1

    print("Records:", n)
    print("Missing required keys:", missing)
    print("Invalid timestamps:", invalid_ts)
    print("Emotion counts:", dict(emo_counts))

if __name__ == "__main__":
    main()
