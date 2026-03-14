from __future__ import annotations

"""
Self structure engine rule tables and lightweight helper functions.

Intended location:
    analysis_engine/self_structure_engine/rules.py

This file is designed to stay deterministic and side-effect free.
It centralizes:
- target dictionaries
- thinking / action dictionaries
- role template scoring rules
- surface signal detection helpers
- target / tag extraction helpers used by signal_extraction.py
- cluster / world-role rule tables used by fusion.py / builders.py

The implementation is aligned with the shared dataclasses defined in the
latest `models_updated.py` supplied by the user:
- TargetCandidate
- TagScore
- RoleScore
- SurfaceSignals
"""

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

try:  # expected package import
    from ..models import TargetCandidate, TagScore, RoleScore, SurfaceSignals
except Exception:  # local / standalone fallback for design review files
    try:
        from models_updated import TargetCandidate, TagScore, RoleScore, SurfaceSignals  # type: ignore
    except Exception:
        from models import TargetCandidate, TagScore, RoleScore, SurfaceSignals  # type: ignore


# =============================================================================
# Generic constants
# =============================================================================

STANDARD_TOP_K = 3
DEEP_TOP_K = 5
STANDARD_ROLE_MIN_SCORE = 2.5
THINKING_TOP_K = 2
ACTION_TOP_K = 2

TARGET_STRONG_ALIAS_SCORE = 3.0
TARGET_WEAK_ALIAS_SCORE = 1.5
TARGET_DOMAIN_SHARED_BONUS = 0.3
TARGET_CONCEPT_PENALTY = 0.85

MAX_TARGETS_STANDARD = 1
MAX_TARGETS_DEEP = 2
CONCEPT_TARGET_PENALTY = 0.85

TARGET_TYPE_PRIORITY = {
    "person": 5,
    "self": 4,
    "activity": 3,
    "environment": 2,
    "concept": 1,
}

SOURCE_WEIGHT = {
    "emotion_input": 1.0,
    "mymodel_create": 0.9,
    "deep_insight": 1.1,
    "echo": 0.4,
    "discovery": 0.4,
    "today_question": 1.05,
}

RELIABILITY_WEIGHT = {
    "low": 0.25,
    "medium": 0.65,
    "high": 1.0,
}

SOURCE_BIAS = {
    "emotion_input": {
        "primary": {"thinking_weight": 1.0, "action_weight": 0.6},
        "secondary": {"thinking_weight": 0.4, "action_weight": 1.2},
    },
    "mymodel_create": {
        "primary": {"thinking_weight": 1.1, "action_weight": 0.7},
        "secondary": {"thinking_weight": 0.7, "action_weight": 0.5},
    },
    "deep_insight": {
        "primary": {"thinking_weight": 1.2, "action_weight": 0.8},
        "secondary": {"thinking_weight": 0.8, "action_weight": 0.6},
    },
    "echo": {
        "primary": {"thinking_weight": 0.5, "action_weight": 0.4},
        "secondary": {"thinking_weight": 0.4, "action_weight": 0.3},
    },
    "discovery": {
        "primary": {"thinking_weight": 0.5, "action_weight": 0.4},
        "secondary": {"thinking_weight": 0.4, "action_weight": 0.3},
    },
    "today_question": {
        "primary": {"thinking_weight": 1.1, "action_weight": 0.8},
        "secondary": {"thinking_weight": 0.7, "action_weight": 0.5},
    },
}


# =============================================================================
# Role templates
# =============================================================================

ROLE_TEMPLATES: List[str] = [
    "Observer",
    "Mediator",
    "Defender",
    "Challenger",
    "Maintainer",
    "Explorer",
    "Supporter",
    "Analyzer",
    "Organizer",
    "Creator",
]

ROLE_LABELS_JA: Dict[str, str] = {
    "Observer": "観察者",
    "Mediator": "調整者",
    "Defender": "防御者",
    "Challenger": "挑戦者",
    "Maintainer": "維持者",
    "Explorer": "探索者",
    "Supporter": "支援者",
    "Analyzer": "分析者",
    "Organizer": "整理者",
    "Creator": "創造者",
}

ROLE_SUMMARIES_JA: Dict[str, str] = {
    "Observer": "状況を見てから動こうとする役割",
    "Mediator": "摩擦を減らしながら関係を整える役割",
    "Defender": "自分や大切なものを守ろうとする役割",
    "Challenger": "状況を変えるために踏み込む役割",
    "Maintainer": "安定や継続を保とうとする役割",
    "Explorer": "新しい可能性を試しながら探る役割",
    "Supporter": "誰かや何かを支えようとする役割",
    "Analyzer": "理解や把握を優先する役割",
    "Organizer": "構造や段取りを整える役割",
    "Creator": "新しい形や表現を生み出そうとする役割",
}


# =============================================================================
# Surface signal markers
# =============================================================================

NEGATION_MARKERS = [
    "ない", "なく", "なかった", "ず", "ぬ", "ません", "できない", "できなかった",
    "したくない", "言えない", "言えなかった", "向き合えない", "向き合えなかった",
]

INTENT_MARKERS = [
    "したい", "したく", "なりたい", "なりたく", "ありたい", "目指したい",
    "してみたい", "やってみたい", "行きたい", "避けたい", "守りたい", "試したい",
]

EXECUTION_MARKERS = [
    "した", "している", "してた", "やった", "言った", "伝えた", "始めた",
    "動いた", "距離を取った", "離れた", "続けた", "投稿した", "書いた",
]

INABILITY_MARKERS = [
    "できない", "できなかった", "言えない", "言えなかった", "話せない", "話せなかった",
    "向き合えない", "向き合えなかった", "始められない", "始められなかった",
    "発言できない", "発言できなかった",
]

REASON_MARKERS = [
    "から", "ので", "ため", "くて", "怖くて", "不安で", "心配で", "しんどくて",
    "つらくて", "嫌で", "だから",
]


# =============================================================================
# Thinking dictionary
# =============================================================================

THINKING_DICT: Dict[str, Dict[str, Any]] = {
    "th_avoid": {
        "label_ja": "回避",
        "cue_stems": [
            "避け", "逃げ", "先延ばし", "後回し", "関わりたくな",
            "触れたくな", "行きたくな", "見たくな", "スルー", "離れたい",
        ],
        "weak_cues": ["怖", "不安", "面倒", "しんど"],
        "cancel_phrases": ["避けたくない", "逃げたくない", "向き合いたい"],
    },
    "th_protect": {
        "label_ja": "防御",
        "cue_stems": [
            "守りたい", "傷つきたくな", "崩れたくな", "これ以上無理",
            "失いたくな", "防ぎたい", "自分を保ちたい", "安全圏",
        ],
        "weak_cues": ["怖", "危ない", "しんど", "限界"],
        "cancel_phrases": ["傷ついてもいい", "守らなくていい"],
    },
    "th_adjust": {
        "label_ja": "調整",
        "cue_stems": [
            "合わせ", "空気を読", "丸く収め", "角を立てたくな",
            "バランス", "折り合", "妥協", "すり合わせ",
        ],
        "weak_cues": ["周り", "全体", "関係"],
        "cancel_phrases": ["合わせたくない", "妥協したくない"],
    },
    "th_understand": {
        "label_ja": "理解",
        "cue_stems": [
            "理解したい", "知りたい", "理由", "原因", "どうして",
            "背景", "意味", "本質", "仕組み",
        ],
        "weak_cues": ["気になる", "なぜ", "どういう"],
        "cancel_phrases": ["知りたくない", "理解したくない"],
    },
    "th_structure": {
        "label_ja": "整理",
        "cue_stems": [
            "整理したい", "順番", "まとめたい", "構造", "段取り",
            "計画", "明確", "優先順位", "仕分け",
        ],
        "weak_cues": ["整えたい", "見通し", "はっきり"],
        "cancel_phrases": ["整理したくない", "考えたくない"],
    },
    "th_challenge": {
        "label_ja": "挑戦",
        "cue_stems": [
            "向き合", "乗り越え", "挑戦", "突破", "変えたい",
            "やってみたい", "踏み込", "打開", "動かしたい",
        ],
        "weak_cues": ["前に進みたい", "やるしかない"],
        "cancel_phrases": ["向き合いたくない", "挑戦したくない"],
    },
    "th_explore": {
        "label_ja": "探索",
        "cue_stems": [
            "試したい", "探したい", "広げたい", "新しい",
            "可能性", "実験", "見てみたい", "発見", "試行錯誤",
        ],
        "weak_cues": ["気になる", "面白そう"],
        "cancel_phrases": ["試したくない", "探したくない"],
    },
    "th_support": {
        "label_ja": "支援",
        "cue_stems": [
            "助けたい", "支えたい", "役に立ちたい", "力になりたい",
            "フォローしたい", "寄り添いたい", "受け止めたい",
        ],
        "weak_cues": ["誰かのため", "支え", "助け"],
        "cancel_phrases": ["助けたくない", "関わりたくない"],
    },
    "th_create": {
        "label_ja": "生成",
        "cue_stems": [
            "作りたい", "生み出したい", "形にしたい", "表現したい",
            "書きたい", "発信したい", "企画したい", "描きたい",
        ],
        "weak_cues": ["アイデア", "表現", "創りたい"],
        "cancel_phrases": ["作りたくない", "表現したくない"],
    },
    "th_endure": {
        "label_ja": "忍耐",
        "cue_stems": [
            "我慢", "耐え", "こらえ", "飲み込", "やり過ご",
            "持ちこたえ", "無理して", "堪え",
        ],
        "weak_cues": ["しのぐ", "踏ん張る"],
        "cancel_phrases": ["我慢したくない", "耐えたくない"],
    },
}


# =============================================================================
# Action dictionary
# =============================================================================

ACTION_DICT: Dict[str, Dict[str, Any]] = {
    "act_watch": {
        "label_ja": "観察",
        "cue_stems": [
            "見る", "様子を見る", "見守", "観察", "静観", "伺", "見届け", "チェック",
        ],
        "cancel_phrases": ["見たくない", "見ないようにした"],
    },
    "act_silence": {
        "label_ja": "沈黙",
        "cue_stems": [
            "黙", "言えな", "発言できな", "飲み込", "伏せ", "隠", "口を閉ざ", "言わずに",
        ],
        "cancel_phrases": ["黙らない", "ちゃんと言った"],
    },
    "act_distance": {
        "label_ja": "距離化",
        "cue_stems": [
            "距離を取", "離れ", "関わらな", "退", "引", "逃げ", "一人にな", "閉じ", "戻らな",
        ],
        "cancel_phrases": ["距離を取らない", "離れない"],
    },
    "act_support": {
        "label_ja": "支援",
        "cue_stems": [
            "助け", "支え", "フォロー", "寄り添", "手伝", "受け止め", "守", "動いた",
        ],
        "cancel_phrases": ["助けなかった", "支えられなかった"],
    },
    "act_organize": {
        "label_ja": "整理",
        "cue_stems": [
            "整え", "片付け", "調整し", "まとめ", "段取り", "並べ", "決め", "設計し", "組み直",
        ],
        "cancel_phrases": ["整えられなかった", "まとめられなかった"],
    },
    "act_confront": {
        "label_ja": "対峙",
        "cue_stems": [
            "向き合", "話し", "伝え", "言っ", "聞い", "確認し", "断", "交渉", "ぶつか",
        ],
        "cancel_phrases": ["向き合えなかった", "言えなかった"],
    },
    "act_initiate": {
        "label_ja": "着手",
        "cue_stems": [
            "始め", "着手", "提案し", "連絡し", "動き出", "申し出", "申し込", "立ち上げ", "取りかか",
        ],
        "cancel_phrases": ["始められなかった", "着手できなかった"],
    },
    "act_maintain": {
        "label_ja": "維持",
        "cue_stems": [
            "続け", "保", "継続し", "守", "回し", "習慣化", "続行", "キープ",
        ],
        "cancel_phrases": ["続けられなかった", "保てなかった"],
    },
    "act_explore": {
        "label_ja": "試行",
        "cue_stems": [
            "試し", "調べ", "読ん", "比較し", "学ん", "検証し", "実験し", "触ってみ", "探し",
        ],
        "cancel_phrases": ["試さなかった", "調べなかった"],
    },
    "act_express": {
        "label_ja": "表現",
        "cue_stems": [
            "書い", "話し", "投稿し", "発信し", "作っ", "描い", "共有し", "表現し", "出し",
        ],
        "cancel_phrases": ["書けなかった", "話せなかった", "出せなかった"],
    },
}


# =============================================================================
# Target dictionary
# =============================================================================

TARGET_DICT: Dict[str, Dict[str, Any]] = {
    "boss": {
        "label_ja": "上司",
        "target_type": "person",
        "domain": "work",
        "strong_aliases": ["上司", "部長", "課長", "主任", "店長", "マネージャー", "マネージャ"],
        "weak_aliases": ["管理職", "責任者"],
    },
    "coworker": {
        "label_ja": "同僚",
        "target_type": "person",
        "domain": "work",
        "strong_aliases": ["同僚", "同期"],
        "weak_aliases": ["チームメンバー", "メンバー"],
    },
    "subordinate": {
        "label_ja": "部下",
        "target_type": "person",
        "domain": "work",
        "strong_aliases": ["部下", "後輩"],
        "weak_aliases": [],
    },
    "client": {
        "label_ja": "顧客",
        "target_type": "person",
        "domain": "work",
        "strong_aliases": ["顧客", "お客さん", "お客", "クライアント", "取引先"],
        "weak_aliases": [],
    },
    "teacher": {
        "label_ja": "先生",
        "target_type": "person",
        "domain": "school",
        "strong_aliases": ["先生", "教師", "教授", "講師"],
        "weak_aliases": [],
    },
    "classmate": {
        "label_ja": "同級生",
        "target_type": "person",
        "domain": "school",
        "strong_aliases": ["同級生", "クラスメイト", "ゼミ仲間"],
        "weak_aliases": ["友達"],
    },
    "friend": {
        "label_ja": "友人",
        "target_type": "person",
        "domain": "social",
        "strong_aliases": ["友人", "友達", "親友"],
        "weak_aliases": [],
    },
    "partner": {
        "label_ja": "恋人",
        "target_type": "person",
        "domain": "social",
        "strong_aliases": ["恋人", "彼氏", "彼女", "パートナー", "配偶者", "夫", "妻"],
        "weak_aliases": [],
    },
    "family": {
        "label_ja": "家族",
        "target_type": "person",
        "domain": "family",
        "strong_aliases": ["家族"],
        "weak_aliases": ["身内"],
    },
    "parent": {
        "label_ja": "親",
        "target_type": "person",
        "domain": "family",
        "strong_aliases": ["親", "両親", "父", "母", "父親", "母親"],
        "weak_aliases": [],
    },
    "child": {
        "label_ja": "子ども",
        "target_type": "person",
        "domain": "family",
        "strong_aliases": ["子ども", "子供", "息子", "娘"],
        "weak_aliases": [],
    },
    "sibling": {
        "label_ja": "きょうだい",
        "target_type": "person",
        "domain": "family",
        "strong_aliases": ["兄弟", "姉妹", "きょうだい", "兄", "姉", "弟", "妹"],
        "weak_aliases": [],
    },
    "stranger": {
        "label_ja": "他人",
        "target_type": "person",
        "domain": "social",
        "strong_aliases": ["他人", "知らない人", "初対面の人"],
        "weak_aliases": ["周囲の人"],
    },
    "audience": {
        "label_ja": "受け手",
        "target_type": "person",
        "domain": "online",
        "strong_aliases": ["読者", "視聴者", "フォロワー", "受け手"],
        "weak_aliases": ["見る人"],
    },
    "workplace": {
        "label_ja": "職場",
        "target_type": "environment",
        "domain": "work",
        "strong_aliases": ["職場", "会社", "オフィス", "現場"],
        "weak_aliases": ["仕事場"],
    },
    "school": {
        "label_ja": "学校",
        "target_type": "environment",
        "domain": "school",
        "strong_aliases": ["学校", "教室", "研究室", "ゼミ"],
        "weak_aliases": [],
    },
    "home": {
        "label_ja": "家庭",
        "target_type": "environment",
        "domain": "family",
        "strong_aliases": ["家庭", "自宅", "実家", "家の中"],
        "weak_aliases": ["家"],
    },
    "team": {
        "label_ja": "チーム",
        "target_type": "environment",
        "domain": "work",
        "strong_aliases": ["チーム", "グループ", "組織"],
        "weak_aliases": ["所属先"],
    },
    "community": {
        "label_ja": "コミュニティ",
        "target_type": "environment",
        "domain": "social",
        "strong_aliases": ["コミュニティ", "サークル"],
        "weak_aliases": [],
    },
    "online_space": {
        "label_ja": "オンライン空間",
        "target_type": "environment",
        "domain": "online",
        "strong_aliases": ["SNS", "X", "Twitter", "Instagram", "ネット", "オンライン", "タイムライン"],
        "weak_aliases": ["TL"],
    },
    "society": {
        "label_ja": "社会",
        "target_type": "environment",
        "domain": "abstract",
        "strong_aliases": ["社会", "世間", "世の中"],
        "weak_aliases": [],
    },
    "work": {
        "label_ja": "仕事",
        "target_type": "activity",
        "domain": "work",
        "strong_aliases": ["仕事", "業務", "案件", "タスク", "プロジェクト"],
        "weak_aliases": ["作業", "任務"],
    },
    "study": {
        "label_ja": "勉強",
        "target_type": "activity",
        "domain": "school",
        "strong_aliases": ["勉強", "学習", "研究", "課題"],
        "weak_aliases": [],
    },
    "creation": {
        "label_ja": "創作",
        "target_type": "activity",
        "domain": "creative",
        "strong_aliases": ["創作", "制作", "作品", "執筆", "開発", "企画", "表現"],
        "weak_aliases": ["ものづくり"],
    },
    "housework": {
        "label_ja": "家事",
        "target_type": "activity",
        "domain": "family",
        "strong_aliases": ["家事", "掃除", "洗濯", "料理"],
        "weak_aliases": [],
    },
    "caregiving": {
        "label_ja": "育児・介護",
        "target_type": "activity",
        "domain": "family",
        "strong_aliases": ["育児", "子育て", "介護"],
        "weak_aliases": [],
    },
    "communication": {
        "label_ja": "対話",
        "target_type": "activity",
        "domain": "social",
        "strong_aliases": ["会話", "連絡", "相談", "打ち合わせ", "会議", "対話"],
        "weak_aliases": ["返信"],
    },
    "exercise": {
        "label_ja": "運動",
        "target_type": "activity",
        "domain": "daily",
        "strong_aliases": ["運動", "筋トレ", "散歩", "トレーニング"],
        "weak_aliases": [],
    },
    "rest": {
        "label_ja": "休息",
        "target_type": "activity",
        "domain": "daily",
        "strong_aliases": ["休み", "休息", "睡眠", "休養"],
        "weak_aliases": [],
    },
    "evaluation": {
        "label_ja": "評価",
        "target_type": "concept",
        "domain": "work",
        "strong_aliases": ["評価", "査定", "採点", "レビュー", "見られ方"],
        "weak_aliases": [],
    },
    "expectation": {
        "label_ja": "期待",
        "target_type": "concept",
        "domain": "abstract",
        "strong_aliases": ["期待", "期待値", "プレッシャー"],
        "weak_aliases": [],
    },
    "responsibility": {
        "label_ja": "責任",
        "target_type": "concept",
        "domain": "work",
        "strong_aliases": ["責任", "担当", "任務", "役目", "義務"],
        "weak_aliases": [],
    },
    "deadline": {
        "label_ja": "締切",
        "target_type": "concept",
        "domain": "work",
        "strong_aliases": ["締切", "締め切り", "納期", "期限"],
        "weak_aliases": [],
    },
    "time": {
        "label_ja": "時間",
        "target_type": "concept",
        "domain": "daily",
        "strong_aliases": ["時間", "予定", "スケジュール"],
        "weak_aliases": [],
    },
    "money": {
        "label_ja": "お金",
        "target_type": "concept",
        "domain": "daily",
        "strong_aliases": ["お金", "収入", "出費", "生活費", "家計"],
        "weak_aliases": [],
    },
    "future": {
        "label_ja": "将来",
        "target_type": "concept",
        "domain": "abstract",
        "strong_aliases": ["将来", "未来", "今後"],
        "weak_aliases": [],
    },
    "result": {
        "label_ja": "結果",
        "target_type": "concept",
        "domain": "abstract",
        "strong_aliases": ["結果", "成果", "成績", "実績"],
        "weak_aliases": [],
    },
    "failure": {
        "label_ja": "失敗",
        "target_type": "concept",
        "domain": "abstract",
        "strong_aliases": ["失敗", "ミス", "欠点"],
        "weak_aliases": [],
    },
    "success": {
        "label_ja": "成功",
        "target_type": "concept",
        "domain": "abstract",
        "strong_aliases": ["成功", "達成", "合格"],
        "weak_aliases": [],
    },
    "relationship": {
        "label_ja": "人間関係",
        "target_type": "concept",
        "domain": "social",
        "strong_aliases": ["人間関係", "関係", "距離感"],
        "weak_aliases": ["つながり"],
    },
    "health": {
        "label_ja": "体調",
        "target_type": "concept",
        "domain": "internal",
        "strong_aliases": ["体調", "健康", "メンタル", "疲労", "睡眠不足", "ストレス"],
        "weak_aliases": [],
    },
    "self": {
        "label_ja": "自分",
        "target_type": "self",
        "domain": "internal",
        "strong_aliases": ["自分", "自分自身", "私自身"],
        "weak_aliases": ["自分のこと"],
    },
}

BROAD_TARGET_SUPPRESSION = {
    "boss": ["workplace", "work", "team", "evaluation", "responsibility"],
    "coworker": ["workplace", "work", "team", "relationship"],
    "subordinate": ["workplace", "work", "team"],
    "client": ["workplace", "work", "communication"],
    "teacher": ["school", "study", "evaluation"],
    "classmate": ["school", "study", "relationship"],
    "friend": ["relationship", "communication", "community"],
    "partner": ["relationship", "home"],
    "family": ["home", "relationship", "housework", "caregiving"],
    "parent": ["family", "home", "relationship", "caregiving"],
    "child": ["family", "home", "relationship", "caregiving"],
    "sibling": ["family", "home", "relationship"],
}


# =============================================================================
# Role scoring rules
# =============================================================================

THINKING_ROLE_WEIGHTS = {
    "th_avoid": {"Observer": 2.0, "Defender": 2.0, "Maintainer": 0.5},
    "th_protect": {"Defender": 3.0, "Observer": 1.0, "Maintainer": 1.0, "Supporter": 0.5},
    "th_adjust": {"Mediator": 3.0, "Organizer": 1.5, "Supporter": 1.0, "Maintainer": 0.5},
    "th_understand": {"Analyzer": 3.0, "Observer": 1.5, "Explorer": 0.5},
    "th_structure": {"Organizer": 3.0, "Analyzer": 2.0, "Maintainer": 0.5},
    "th_challenge": {"Challenger": 3.0, "Explorer": 0.5, "Creator": 0.5},
    "th_explore": {"Explorer": 3.0, "Analyzer": 1.0, "Creator": 1.0},
    "th_support": {"Supporter": 3.0, "Mediator": 1.0, "Maintainer": 0.5},
    "th_create": {"Creator": 3.0, "Explorer": 1.0, "Challenger": 0.5},
    "th_endure": {"Maintainer": 2.0, "Defender": 2.0, "Observer": 0.5},
}

ACTION_ROLE_WEIGHTS = {
    "act_watch": {"Observer": 3.0, "Analyzer": 1.0},
    "act_silence": {"Observer": 2.0, "Defender": 2.0, "Maintainer": 0.5},
    "act_distance": {"Defender": 2.5, "Observer": 1.5, "Maintainer": 0.5},
    "act_support": {"Supporter": 3.0, "Mediator": 1.0, "Maintainer": 0.5},
    "act_organize": {"Organizer": 3.0, "Mediator": 1.0, "Analyzer": 0.5, "Maintainer": 0.5},
    "act_confront": {"Challenger": 3.0, "Mediator": 1.0},
    "act_initiate": {"Challenger": 2.0, "Explorer": 1.5, "Creator": 1.0},
    "act_maintain": {"Maintainer": 3.0, "Organizer": 1.0, "Supporter": 0.5},
    "act_explore": {"Explorer": 3.0, "Analyzer": 1.0, "Creator": 0.5},
    "act_express": {"Creator": 3.0, "Challenger": 1.0, "Supporter": 0.5},
}

COMBO_ROLE_WEIGHTS = {
    ("th_avoid", "act_silence"): {"Observer": 2.0, "Defender": 2.0},
    ("th_avoid", "act_distance"): {"Defender": 2.5, "Observer": 1.0},
    ("th_protect", "act_silence"): {"Defender": 2.0, "Observer": 1.0},
    ("th_protect", "act_distance"): {"Defender": 2.5, "Maintainer": 1.0},
    ("th_adjust", "act_organize"): {"Mediator": 2.0, "Organizer": 2.0},
    ("th_adjust", "act_support"): {"Mediator": 2.0, "Supporter": 2.0},
    ("th_understand", "act_watch"): {"Analyzer": 2.0, "Observer": 1.0},
    ("th_understand", "act_explore"): {"Analyzer": 2.0, "Explorer": 2.0},
    ("th_structure", "act_organize"): {"Organizer": 3.0, "Analyzer": 1.0},
    ("th_challenge", "act_confront"): {"Challenger": 3.0},
    ("th_challenge", "act_initiate"): {"Challenger": 2.0, "Creator": 1.0},
    ("th_explore", "act_explore"): {"Explorer": 3.0, "Analyzer": 1.0},
    ("th_explore", "act_express"): {"Explorer": 1.0, "Creator": 2.0},
    ("th_support", "act_support"): {"Supporter": 3.0, "Mediator": 1.0},
    ("th_create", "act_express"): {"Creator": 3.0, "Challenger": 1.0},
    ("th_create", "act_initiate"): {"Creator": 2.0, "Explorer": 1.0},
    ("th_endure", "act_maintain"): {"Maintainer": 3.0, "Defender": 1.0},
    ("th_endure", "act_silence"): {"Maintainer": 1.0, "Defender": 2.0, "Observer": 1.0},
}

TARGET_TYPE_ROLE_BIAS = {
    "person": {"Mediator": 0.5, "Supporter": 0.5, "Observer": 0.3, "Defender": 0.3},
    "environment": {"Organizer": 0.5, "Maintainer": 0.5, "Mediator": 0.2},
    "activity": {"Explorer": 0.5, "Creator": 0.5, "Analyzer": 0.3, "Organizer": 0.3},
    "concept": {"Analyzer": 0.6, "Explorer": 0.4, "Creator": 0.2},
    "self": {"Analyzer": 0.6, "Observer": 0.4, "Defender": 0.2},
}

ROLE_DAMPING_RULES = [
    {
        "when_actions_any": ["act_silence", "act_distance"],
        "unless_thinkings_any": ["th_challenge", "th_create"],
        "dampen": {"Challenger": 0.8, "Creator": 0.9},
    },
    {
        "when_actions_any": ["act_confront", "act_initiate"],
        "unless_thinkings_any": ["th_avoid", "th_protect"],
        "dampen": {"Observer": 0.85, "Defender": 0.9},
    },
]


# =============================================================================
# Cluster and world-role rule tables (used by fusion / builders later)
# =============================================================================

CLUSTER_RULES = {
    "Avoidance": {
        "thinkings": {"th_avoid": 2.0, "th_protect": 1.5, "th_endure": 1.0},
        "actions": {"act_silence": 2.0, "act_distance": 2.0, "act_watch": 0.5},
    },
    "Influence": {
        "thinkings": {"th_challenge": 2.0, "th_create": 0.5},
        "actions": {"act_confront": 2.0, "act_initiate": 2.0, "act_express": 0.5},
    },
    "Stability": {
        "thinkings": {"th_adjust": 1.5, "th_structure": 1.5, "th_endure": 1.0},
        "actions": {"act_organize": 2.0, "act_maintain": 2.0, "act_support": 0.5},
    },
    "Exploration": {
        "thinkings": {"th_understand": 1.5, "th_explore": 2.0},
        "actions": {"act_watch": 1.0, "act_explore": 2.0},
    },
    "Expression": {
        "thinkings": {"th_create": 1.5, "th_support": 0.5},
        "actions": {"act_express": 2.0, "act_initiate": 0.5, "act_support": 0.5},
    },
}

SELF_WORLD_MARKERS = ["自分は", "自分が", "私は", "しがち", "な方", "気づくと"]
REAL_WORLD_MARKERS = ["求められる", "任される", "頼られる", "見られる", "扱われる", "期待される"]
DESIRED_MARKERS = ["なりたい", "したい", "こうありたい", "目指したい", "そうなりたい"]

WORLD_ROLE_MIN_SCORE = 2.0
ROLE_GAP_MIN_SCORE = 1.5

THINKING_PURPOSE_PHRASES = {
    "th_avoid": "摩擦や負荷を避けるために",
    "th_protect": "自分を守るために",
    "th_adjust": "関係や全体のバランスを整えるために",
    "th_understand": "状況を理解するために",
    "th_structure": "物事を整理して保つために",
    "th_challenge": "状況を変えるために",
    "th_explore": "新しい可能性を探るために",
    "th_support": "相手や場を支えるために",
    "th_create": "新しい形を生み出すために",
    "th_endure": "崩れずに持ちこたえるために",
}

ACTION_DIRECTION_PHRASES = {
    "act_watch": "観察へ向かう",
    "act_silence": "沈黙へ向かう",
    "act_distance": "距離化へ向かう",
    "act_support": "支援へ向かう",
    "act_organize": "整理へ向かう",
    "act_confront": "対峙へ向かう",
    "act_initiate": "着手へ向かう",
    "act_maintain": "維持へ向かう",
    "act_explore": "試行へ向かう",
    "act_express": "表現へ向かう",
}


# =============================================================================
# Utility helpers
# =============================================================================


def normalize_text(text: Optional[str]) -> str:
    if not text:
        return ""
    return " ".join(str(text).replace("\u3000", " ").replace("\n", " ").split()).strip().lower()


def _dedupe_keep_order(items: Iterable[str]) -> List[str]:
    seen = set()
    out = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _contains_any(text: str, patterns: Sequence[str]) -> bool:
    return any(p for p in patterns if p and p.lower() in text)


def _match_terms(text: str, strong_aliases: Sequence[str], weak_aliases: Sequence[str]) -> Tuple[float, List[str]]:
    score = 0.0
    matched: List[str] = []

    for alias in strong_aliases:
        if alias and alias.lower() in text:
            score += TARGET_STRONG_ALIAS_SCORE
            matched.append(alias)

    for alias in weak_aliases:
        if alias and alias.lower() in text:
            score += TARGET_WEAK_ALIAS_SCORE
            matched.append(alias)

    return score, _dedupe_keep_order(matched)


def get_source_bias(source_type: str, channel: str) -> Dict[str, float]:
    per_source = SOURCE_BIAS.get(source_type, {})
    return per_source.get(channel, {"thinking_weight": 1.0, "action_weight": 1.0})


def detect_surface_signals(text: str) -> SurfaceSignals:
    norm = normalize_text(text)
    return SurfaceSignals(
        has_negation=_contains_any(norm, NEGATION_MARKERS),
        has_intent=_contains_any(norm, INTENT_MARKERS),
        has_execution=_contains_any(norm, EXECUTION_MARKERS),
        has_inability=_contains_any(norm, INABILITY_MARKERS),
        has_reason_marker=_contains_any(norm, REASON_MARKERS),
    )


def estimate_reliability(text: str, source_type: str, surface: Optional[SurfaceSignals] = None) -> str:
    norm = normalize_text(text)
    if not norm:
        return "low"

    surface = surface or detect_surface_signals(norm)

    score = 0
    if len(norm) >= 8:
        score += 1
    if len(norm) >= 20:
        score += 1
    if surface.has_reason_marker:
        score += 1
    if surface.has_execution or surface.has_inability:
        score += 1
    if surface.has_intent:
        score += 1
    if extract_target_candidates(norm):
        score += 1

    if source_type in {"deep_insight", "mymodel_create"} and len(norm) >= 10:
        score += 1

    if score <= 1:
        return "low"
    if score <= 3:
        return "medium"
    return "high"


# =============================================================================
# Target extraction
# =============================================================================


def extract_target_candidates(text: str, source_type: str = "") -> List[TargetCandidate]:
    norm = normalize_text(text)
    if not norm:
        return []

    candidates: List[TargetCandidate] = []

    for key, meta in TARGET_DICT.items():
        score, _ = _match_terms(
            norm,
            meta.get("strong_aliases", []),
            meta.get("weak_aliases", []),
        )
        if score <= 0:
            continue

        if meta["target_type"] == "concept":
            score *= CONCEPT_TARGET_PENALTY

        candidates.append(
            TargetCandidate(
                key=key,
                label_ja=meta["label_ja"],
                target_type=meta["target_type"],
                domain=meta["domain"],
                score=score,
            )
        )

    present_keys = {c.key for c in candidates}
    for c in candidates:
        if c.key not in BROAD_TARGET_SUPPRESSION:
            continue
        for sup_key in BROAD_TARGET_SUPPRESSION[c.key]:
            if sup_key not in present_keys:
                continue
            for x in candidates:
                if x.key == sup_key:
                    x.score *= 0.7

    candidates.sort(
        key=lambda x: (
            x.score,
            TARGET_TYPE_PRIORITY.get(x.target_type, 0),
            len(x.label_ja),
        ),
        reverse=True,
    )
    return candidates


def select_targets(
    candidates: Sequence[TargetCandidate],
    stage: str,
) -> Tuple[Optional[TargetCandidate], List[TargetCandidate]]:
    if not candidates:
        return None, []

    max_targets = MAX_TARGETS_STANDARD if stage == "standard" else MAX_TARGETS_DEEP
    selected = list(candidates[:max_targets])
    return selected[0], selected[1:]


# =============================================================================
# Thinking / action extraction
# =============================================================================


def _score_tag_entry(
    text: str,
    entry: Dict[str, Any],
    *,
    base_strong: float,
    base_weak: float,
) -> Tuple[float, List[str]]:
    if _contains_any(text, entry.get("cancel_phrases", [])):
        return 0.0, []

    score = 0.0
    matched: List[str] = []

    for cue in entry.get("cue_stems", []):
        if cue and cue.lower() in text:
            score += base_strong
            matched.append(cue)

    for cue in entry.get("weak_cues", []):
        if cue and cue.lower() in text:
            score += base_weak
            matched.append(cue)

    return score, _dedupe_keep_order(matched)


def _merge_tag_score(
    bucket: Dict[str, Dict[str, Any]],
    key: str,
    label_ja: str,
    score: float,
    matched_terms: Sequence[str],
) -> None:
    if score <= 0:
        return
    row = bucket.setdefault(
        key,
        {
            "label_ja": label_ja,
            "score": 0.0,
            "matched_terms": [],
        },
    )
    row["score"] += score
    row["matched_terms"].extend(matched_terms)
    row["matched_terms"] = _dedupe_keep_order(row["matched_terms"])


def extract_thinking_tags(
    text_primary: str,
    text_secondary: str,
    source_type: str,
    reliability: str,
    surface: Optional[SurfaceSignals] = None,
) -> List[TagScore]:
    surface = surface or detect_surface_signals(f"{text_primary}\n{text_secondary}")

    bucket: Dict[str, Dict[str, Any]] = {}

    for channel_name, raw_text in (("primary", text_primary), ("secondary", text_secondary)):
        norm = normalize_text(raw_text)
        if not norm:
            continue

        bias = get_source_bias(source_type, channel_name)["thinking_weight"]
        if surface.has_intent:
            bias *= 1.1
        if reliability == "low":
            bias *= 0.8

        for key, entry in THINKING_DICT.items():
            base_score, matched = _score_tag_entry(norm, entry, base_strong=1.0, base_weak=0.45)
            _merge_tag_score(
                bucket,
                key,
                entry["label_ja"],
                base_score * bias,
                matched,
            )

    items = [
        TagScore(
            key=k,
            label_ja=v["label_ja"],
            score=round(v["score"], 4),
            matched_terms=v["matched_terms"],
        )
        for k, v in bucket.items()
        if v["score"] > 0
    ]
    items.sort(key=lambda x: x.score, reverse=True)
    return items[:THINKING_TOP_K]


def extract_action_tags(
    text_primary: str,
    text_secondary: str,
    source_type: str,
    reliability: str,
    surface: Optional[SurfaceSignals] = None,
) -> List[TagScore]:
    surface = surface or detect_surface_signals(f"{text_primary}\n{text_secondary}")

    bucket: Dict[str, Dict[str, Any]] = {}

    for channel_name, raw_text in (("primary", text_primary), ("secondary", text_secondary)):
        norm = normalize_text(raw_text)
        if not norm:
            continue

        bias = get_source_bias(source_type, channel_name)["action_weight"]
        if surface.has_execution or surface.has_inability:
            bias *= 1.1
        if reliability == "low":
            bias *= 0.6

        for key, entry in ACTION_DICT.items():
            base_score, matched = _score_tag_entry(norm, entry, base_strong=1.0, base_weak=0.0)
            _merge_tag_score(
                bucket,
                key,
                entry["label_ja"],
                base_score * bias,
                matched,
            )

    items = [
        TagScore(
            key=k,
            label_ja=v["label_ja"],
            score=round(v["score"], 4),
            matched_terms=v["matched_terms"],
        )
        for k, v in bucket.items()
        if v["score"] > 0
    ]
    items.sort(key=lambda x: x.score, reverse=True)
    return items[:ACTION_TOP_K]


# =============================================================================
# Role scoring
# =============================================================================


def _combo_strength(th_score: float, act_score: float) -> float:
    avg = (th_score + act_score) / 2.0
    return max(0.75, min(avg, 1.5))


def score_role_templates(
    thinking_tags: Sequence[TagScore],
    action_tags: Sequence[TagScore],
    primary_target: Optional[TargetCandidate] = None,
) -> List[RoleScore]:
    score_map: Dict[str, float] = {role: 0.0 for role in ROLE_TEMPLATES}
    reasons_map: Dict[str, List[str]] = {role: [] for role in ROLE_TEMPLATES}

    for tag in thinking_tags:
        for role, weight in THINKING_ROLE_WEIGHTS.get(tag.key, {}).items():
            inc = weight * tag.score
            score_map[role] += inc
            reasons_map[role].append(f"thinking:{tag.key}")

    for tag in action_tags:
        for role, weight in ACTION_ROLE_WEIGHTS.get(tag.key, {}).items():
            inc = weight * tag.score
            score_map[role] += inc
            reasons_map[role].append(f"action:{tag.key}")

    for th in thinking_tags:
        for act in action_tags:
            combo = COMBO_ROLE_WEIGHTS.get((th.key, act.key), {})
            if not combo:
                continue
            strength = _combo_strength(th.score, act.score)
            for role, weight in combo.items():
                inc = weight * strength
                score_map[role] += inc
                reasons_map[role].append(f"combo:{th.key}+{act.key}")

    if primary_target is not None:
        for role, weight in TARGET_TYPE_ROLE_BIAS.get(primary_target.target_type, {}).items():
            score_map[role] += weight
            reasons_map[role].append(f"target_type:{primary_target.target_type}")

    present_actions = {x.key for x in action_tags}
    present_thinkings = {x.key for x in thinking_tags}
    for rule in ROLE_DAMPING_RULES:
        if not present_actions.intersection(rule.get("when_actions_any", [])):
            continue
        unless_any = set(rule.get("unless_thinkings_any", []))
        if present_thinkings.intersection(unless_any):
            continue
        for role, mul in rule.get("dampen", {}).items():
            score_map[role] *= mul
            reasons_map[role].append(f"dampen:{mul}")

    scored = [
        RoleScore(
            role_key=role,
            score=round(score, 4),
            reasons=_dedupe_keep_order(reasons_map[role]),
        )
        for role, score in score_map.items()
        if score > 0
    ]
    scored.sort(key=lambda x: x.score, reverse=True)
    return scored


# =============================================================================
# World-role / builder helpers
# =============================================================================


def detect_world_kind(text: str) -> Optional[str]:
    norm = normalize_text(text)
    if _contains_any(norm, REAL_WORLD_MARKERS):
        return "real"
    if _contains_any(norm, DESIRED_MARKERS):
        return "desired"
    if _contains_any(norm, SELF_WORLD_MARKERS):
        return "self"
    return None


def compute_recency_weight(timestamp: Optional[str], now_ts: Optional[str] = None) -> float:
    if not timestamp:
        return 1.0

    def _parse(ts: str) -> Optional[datetime]:
        try:
            if ts.endswith("Z"):
                return datetime.fromisoformat(ts.replace("Z", "+00:00"))
            dt = datetime.fromisoformat(ts)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return None

    dt = _parse(timestamp)
    now = _parse(now_ts) if now_ts else datetime.now(timezone.utc)
    if dt is None or now is None:
        return 1.0

    days_ago = max((now - dt).days, 0)
    if days_ago <= 30:
        return 1.0
    if days_ago <= 90:
        return 0.7
    if days_ago <= 180:
        return 0.45
    return 0.25


__all__ = [
    "ROLE_TEMPLATES",
    "ROLE_LABELS_JA",
    "ROLE_SUMMARIES_JA",
    "STANDARD_TOP_K",
    "DEEP_TOP_K",
    "STANDARD_ROLE_MIN_SCORE",
    "SOURCE_WEIGHT",
    "RELIABILITY_WEIGHT",
    "SOURCE_BIAS",
    "get_source_bias",
    "NEGATION_MARKERS",
    "INTENT_MARKERS",
    "EXECUTION_MARKERS",
    "INABILITY_MARKERS",
    "REASON_MARKERS",
    "detect_surface_signals",
    "estimate_reliability",
    "THINKING_DICT",
    "ACTION_DICT",
    "TARGET_DICT",
    "BROAD_TARGET_SUPPRESSION",
    "THINKING_TOP_K",
    "ACTION_TOP_K",
    "TARGET_TYPE_PRIORITY",
    "MAX_TARGETS_STANDARD",
    "MAX_TARGETS_DEEP",
    "CONCEPT_TARGET_PENALTY",
    "THINKING_ROLE_WEIGHTS",
    "ACTION_ROLE_WEIGHTS",
    "COMBO_ROLE_WEIGHTS",
    "TARGET_TYPE_ROLE_BIAS",
    "ROLE_DAMPING_RULES",
    "CLUSTER_RULES",
    "SELF_WORLD_MARKERS",
    "REAL_WORLD_MARKERS",
    "DESIRED_MARKERS",
    "WORLD_ROLE_MIN_SCORE",
    "ROLE_GAP_MIN_SCORE",
    "THINKING_PURPOSE_PHRASES",
    "ACTION_DIRECTION_PHRASES",
    "detect_world_kind",
    "normalize_text",
    "extract_target_candidates",
    "select_targets",
    "extract_thinking_tags",
    "extract_action_tags",
    "score_role_templates",
    "compute_recency_weight",
]
