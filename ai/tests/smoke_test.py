import sys, os
# Make ai_inference importable
base = os.path.dirname(os.path.dirname(__file__))  # mashos/ai
sys.path.append(os.path.join(base, "services", "ai_inference"))
from guards.date_guard import contains_date_like, rejection_message

print('JA date-like:', contains_date_like("10月3日に何があった？", lang='ja'))
print('EN date-like:', contains_date_like("What happened on 2025-11-04?", lang='en'))
print('Non date-like:', contains_date_like("夜に不安が出やすいのはなぜ？", lang='ja'))
print('Reject message (ja):', rejection_message('ja'))
