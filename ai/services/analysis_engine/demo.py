
from analysis_engine import EmotionEntry, build_weekly_features, narrate_weekly, build_baseline, assemble_monthly, narrate_monthly
from datetime import datetime

# sample normalized entries (ordered)
entries = [
    EmotionEntry(id="1", timestamp="2025-10-01T09:12:00+09:00", date="2025-10-01", label="sadness", intensity=2, memo="寝不足"),
    EmotionEntry(id="2", timestamp="2025-10-01T22:40:00+09:00", date="2025-10-01", label="peace", intensity=2),
    EmotionEntry(id="3", timestamp="2025-10-02T08:10:00+09:00", date="2025-10-02", label="joy", intensity=3),
    EmotionEntry(id="4", timestamp="2025-10-03T19:05:00+09:00", date="2025-10-03", label="anxiety", intensity=2),
    EmotionEntry(id="5", timestamp="2025-10-04T21:33:00+09:00", date="2025-10-04", label="peace", intensity=1),
    EmotionEntry(id="6", timestamp="2025-10-05T07:21:00+09:00", date="2025-10-05", label="joy", intensity=2),
]

wk = build_weekly_features(entries, period="2025-10-01..2025-10-07")
baseline = build_baseline(user_id="demo", weeks=[wk], window_weeks=3, window_months=2)  # minimal baseline
nar_wk = narrate_weekly(wk, baseline)

# monthly: duplicate weeks to make 4-week sequence (for demo)
weeks = [wk, wk, wk, wk]
monthly = assemble_monthly(weeks, period="2025-10-01..2025-10-28")
nar_m = narrate_monthly(monthly)

print("=== Weekly Narrative ===")
print(nar_wk.to_dict())
print("\n=== Monthly Narrative ===")
print(nar_m.to_dict())
