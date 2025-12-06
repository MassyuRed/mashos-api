from dataclasses import dataclass, asdict
from typing import List, Dict, Any
import json, time

@dataclass
class TrainSet:
    instruction: str
    input: Dict[str, Any]
    ideal_output: str
    period: str = "30d"
    lang: str = "ja"
    created_at: float = 0.0

def build_ideal_output(lang: str = 'ja') -> str:
    if lang == 'en':
        return "Observation: ...\nHypothesis: ...\nNote: ..."
    return "観測：...\n仮説：...\n注記：..."

def make_trainset(instruction: str, features: Dict[str, Any], lang: str = 'ja', period: str = '30d') -> TrainSet:
    return TrainSet(
        instruction=instruction,
        input={"period": period, **features},
        ideal_output=build_ideal_output(lang),
        period=period,
        lang=lang,
        created_at=time.time()
    )

def write_jsonl(path: str, rows: List[TrainSet]) -> None:
    with open(path, 'w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")
