
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os
from collections import Counter
from datetime import datetime

STRENGTH_SCORE = {'weak':1.0,'medium':2.0,'strong':3.0}

def weight_from_strength(v):
    try:
        # 数値0..1を1..3へ線形変換
        if isinstance(v, (int, float)):
            x = max(0.0, min(1.0, float(v)))
            return 1.0 + 2.0 * x
        if isinstance(v, str):
            return float(STRENGTH_SCORE.get(v.lower(), 1.0))
    except Exception:
        pass
    return 1.0

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_RAW = os.path.join(ROOT, "data", "raw", "logs.jsonl")
DATA_OUT = os.path.join(ROOT, "data", "processed", "features.json")
TEMPLATE = os.path.join(os.path.dirname(__file__), "templates", "summary.txt")
SUMMARY_OUT = os.path.join(ROOT, "data", "processed", "summary.txt")

def time_bucket(ts):
    try:
        dt = datetime.fromisoformat(ts)
    except Exception:
        dt = datetime.fromisoformat(ts.replace(" ", "T"))
    h = dt.hour
    if 0 <= h < 6:   return "night"
    if 6 <= h < 12:  return "morning"
    if 12 <= h < 18: return "afternoon"
    return "evening"

def load_logs(path):
    logs = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            try:
                logs.append(json.loads(line))
            except Exception:
                pass
    return logs

def aggregate(logs):
    emo, tb, kw = Counter(), Counter(), Counter()
    for r in logs:
        if "emotion_details" in r and isinstance(r.get("emotion_details"), list):
            for d in r.get("emotion_details") or []:
                emo[str(d.get("type","Unknown"))] += weight_from_strength(d.get("strength"))
        else:
            w = weight_from_strength(r.get("strength"))
            emo[r.get("emotion","Unknown")] += w
        ts = r.get("ts","1970-01-01T00:00:00")
        try: tb[time_bucket(ts)] += 1
        except: pass
        for w in (r.get("keywords") or []):
            kw[str(w)] += 1
    total = sum(emo.values()) or 1
    ratios = {k: round(v/total, 4) for k,v in emo.items()}
    time_bias = [k for k,_ in tb.most_common(2)]
    hot_words = [k for k,_ in kw.most_common(3)]
    return {"period":"30d","ratios":ratios,"time_bias":time_bias,"hot_words":hot_words}

def render_summary(feat, tmpl_path):
    with open(tmpl_path, "r", encoding="utf-8") as f:
        tmpl = f.read()
    top = max(feat["ratios"].items(), key=lambda kv: kv[1])[0]
    tb = "・".join(feat["time_bias"]) if feat["time_bias"] else "—"
    hw = "・".join(feat["hot_words"]) if feat["hot_words"] else "—"
    return tmpl.format(period=feat["period"], top_emotion=top, time_bias=tb, hot_words=hw)

def main():
    logs = load_logs(DATA_RAW)
    feat = aggregate(logs)
    os.makedirs(os.path.dirname(DATA_OUT), exist_ok=True)
    with open(DATA_OUT, "w", encoding="utf-8") as f:
        json.dump(feat, f, ensure_ascii=False, indent=2)
    if os.path.exists(TEMPLATE):
        s = render_summary(feat, TEMPLATE)
        with open(SUMMARY_OUT, "w", encoding="utf-8") as f:
            f.write(s)
    print("OK")

if __name__ == "__main__":
    main()
