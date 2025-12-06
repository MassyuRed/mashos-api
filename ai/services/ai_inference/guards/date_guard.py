import re
from typing import List, Tuple

JA_PATTERNS = [
    r"\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日?",
    r"\d{1,2}\s*月\s*\d{1,2}\s*日",
    r"\d{4}[-/]\d{1,2}[-/]\d{1,2}",
    r"\d{1,2}[:時]\d{2}(?:[:分]\d{2})?",
    r"(昨日|今日|明日|一昨日|明後日|先週|来週|先月|来月|去年|今年|来年)",
    r"(月|火|水|木|金|土|日)曜日",
    r"(何日|何月|何年|いつ)"
]

EN_PATTERNS = [
    r"\b\d{4}-\d{1,2}-\d{1,2}\b",
    r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:,\s*\d{4})?\b",
    r"\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b",
    r"\b(?:yesterday|today|tomorrow|last\s+(?:week|month|year)|next\s+(?:week|month|year))\b",
    r"\b(?:when|what\s+day|what\s+date)\b",
    r"\b\d{1,2}:\d{2}(?::\d{2})?\b"
]

JA_RX = [re.compile(p) for p in JA_PATTERNS]
EN_RX = [re.compile(p, flags=re.IGNORECASE) for p in EN_PATTERNS]

def contains_date_like(text: str, lang: str | None = None) -> Tuple[bool, List[str]]:
    matches = []
    def scan(rx_list):
        local = []
        for rx in rx_list:
            local.extend(m.group(0) for m in rx.finditer(text))
        return local
    if lang == 'ja':
        matches = scan(JA_RX)
    elif lang == 'en':
        matches = scan(EN_RX)
    else:
        matches = scan(JA_RX) + scan(EN_RX)
    return (len(matches) > 0, matches[:5])

def rejection_message(lang: str = 'ja') -> str:
    if lang == 'en':
        return "This query includes date/time specifics, which MyModel does not accept. Please use MyWeb (weekly/monthly) for date-based reflection."
    return "この照会は日付/時系列の特定を含むため、MyModelでは受け付けていません。日付に関する振り返りは MyWeb（週報/月報）をご利用ください。"
