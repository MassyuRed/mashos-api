# -*- coding: utf-8 -*-
from __future__ import annotations

"""Mechanical Japanese coherence guard for Phase8 Limited Composer output."""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Sequence

_EMOTION_LABELS = {"喜び", "悲しみ", "怒り", "不安", "平穏", "自己理解", "恐れ", "焦り"}
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？!?])\s*|\n+")
_GREETING_RE = re.compile(r"^(?:[^。！？!?\n]{1,36}さん、)?(?:おはようございます|こんにちは|こんばんは|Emlisです|.+Emlisです)[。.!！]?$")
_BROKEN_SURFACE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("phase8_generic_relation_suffix", re.compile(r"がつながっています[。.!！]?$")),
    ("phase8_generic_relation_suffix", re.compile(r"同じ中にあります[。.!！]?$")),
    ("phase8_unfinished_phrase", re.compile(r"なんであ(?:が|$)")),
    ("phase8_unfinished_phrase", re.compile(r"考え始めが|考え始め[。.!！]?$")),
    ("phase8_unfinished_phrase", re.compile(r"悪化するが(?:同じ中にあります|$)")),
    ("phase8_orphan_particle_fragment", re.compile(r"(?:けど|でも|のに|から|なら|すると|したい|怖い|嬉しい)が(?:同じ中|つながって)")),
)
_TRAILING_UNFINISHED_RE = re.compile(r"(なんであ|考え始め|現実と|普通に|けど|でも|のに|から|なら|すると)$")
_GENERIC_CLOSING_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("phase8_generic_closing", re.compile(r"(?:今の言葉として|ここに置いてくれた言葉|急いで片づけず|一つの結論へ急がず)[^。！？!?]{0,40}(?:一緒に見ます|小さく扱いません|軽く扱いません)[。.!！]?$")),
    ("phase8_generic_closing", re.compile(r"(?:一緒に見ます|一緒に見ていきます|軽く扱いません|小さく扱いません)[。.!！]?$")),
)
_LIMITED_TAIL_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("surface_visible", re.compile(r"表に出ています[。.!！]?$")),
    ("front", re.compile(r"前面にあります[。.!！]?$")),
    ("written", re.compile(r"(?:が|も)書かれています[。.!！]?$")),
    ("remain", re.compile(r"(?:が|も|同時に)残っています[。.!！]?$")),
    ("strong_remain", re.compile(r"強く残っています[。.!！]?$")),
    ("return", re.compile(r"戻ってきています[。.!！]?$")),
    ("mixed", re.compile(r"混ざっています[。.!！]?$")),
    ("stack", re.compile(r"重なっています[。.!！]?$")),
    ("continue", re.compile(r"続いています[。.!！]?$")),
    ("impact", re.compile(r"大きく響いています[。.!！]?$")),
    ("center", re.compile(r"中心にあります[。.!！]?$")),
    ("arrived", re.compile(r"来ています[。.!！]?$")),
    ("visible", re.compile(r"見えています[。.!！]?$")),
    ("progress_shape", re.compile(r"形になっています[。.!！]?$")),
    ("worded", re.compile(r"言葉になっています[。.!！]?$")),
    ("tension", re.compile(r"ぶつかっています[。.!！]?$")),
    ("parallel", re.compile(r"並んでいます[。.!！]?$")),
    ("exists", re.compile(r"あります[。.!！]?$")),
)
_COMPACT_TRIM_RE = re.compile(r"[\s\n\r\t 　、,。.!！?？『』\"'「」（）()\[\]【】]+")

_TEXT_SOURCE_FIELDS = {"memo", "memo_action", "text", "free_text"}

_KNOWN_PHASE8_PROFILES = {
    "mixed_positive_anxiety",
    "anger_hurt_boundary",
    "self_understanding_loop",
    "positive_progress",
    "relationship_approach_avoidance",
    "reality_escape_tension",
    "energy_fatigue",
    "anxiety_anticipation",
    "value_wish",
    "long_meaning_arc",
}
_SHALLOW_PROFILE_KEYS = {"", "unknown", "current_input_core", "short_ambiguous_low_evidence"}

_PROFILE_REQUIRED_ROLES: Dict[str, tuple[str, ...]] = {
    "mixed_positive_anxiety": ("positive_state", "anxiety_return"),
    "anger_hurt_boundary": ("anger_surface", "hurt_core"),
    "self_understanding_loop": ("anticipation_loop", "perfection_fear"),
    "positive_progress": ("small_action", "achievement"),
    "relationship_approach_avoidance": ("wish_to_rely", "burden_fear", "rejection_fear", "limit"),
    "reality_escape_tension": ("safe_home", "reality_damage", "ordinary_life_wish", "worsening_risk"),
    "energy_fatigue": ("fatigue_accumulation", "loss_of_control"),
    "anxiety_anticipation": ("anticipation_loop", "anxiety_return"),
    "value_wish": ("value_wish", "loss_of_control"),
    "long_meaning_arc": ("fatigue_accumulation", "value_wish"),
}

_ROLE_REFLECTION_CUES: Dict[str, tuple[str, ...]] = {
    "positive_state": ("友達", "楽しか", "楽しさ", "笑え", "元気", "ほっと", "落ち着", "安心", "散歩"),
    "anxiety_return": ("不安", "心配", "落ちる", "落差"),
    "anger_surface": ("怒り", "腹が立", "むっと", "ムッと", "言い方", "返し方", "雑"),
    "hurt_core": ("しんど", "大事に扱", "軽く扱", "傷つ"),
    "anticipation_loop": ("考えすぎ", "止ま", "動け", "進めない", "手が止ま", "先のこと"),
    "perfection_fear": ("完璧", "適当", "失敗", "ちゃんとできない", "怖さ"),
    "small_action": ("片付け", "洗い物", "机", "台所", "整", "進め", "終え"),
    "achievement": ("できた", "嬉し", "ほっと", "進められ", "形にな"),
    "wish_to_rely": ("頼り", "相談", "助け", "話したい", "支えて"),
    "burden_fear": ("迷惑", "負担", "時間を奪", "困らせ", "言い出せない", "邪魔"),
    "rejection_fear": ("嫌われ", "重い", "離れ", "困らせ", "面倒だと思", "怖さ"),
    "limit": ("限界", "抱える", "一人で考え", "つら", "逃げ出", "投げ出", "何もしたくない", "来て"),
    "safe_home": ("家", "お家", "おうち", "リラックス", "安心", "ペース", "優先", "整え"),
    "reality_damage": ("現実", "不便", "ダメージ", "移動", "準備", "重く"),
    "ordinary_life_wish": ("生活したい", "いつも通り", "過ごしたい", "普通に生活"),
    "worsening_risk": ("悪化", "体調", "崩れ", "リスク", "怖さ"),
    "fatigue_accumulation": ("疲れ", "疲労", "消耗", "体力", "へとへと", "ぐったり", "だる", "眠", "抜けない"),
    "loss_of_control": ("集中", "手が止ま", "手につか", "追いつ", "余裕", "予定", "動け", "頭が回", "多すぎ"),
    "small_repair": ("整え", "片付け", "お茶", "散歩", "休め", "深呼吸", "洗い物", "落ち着"),
    "avoidance_wish": ("逃げ", "休みたい", "横になりたい", "寝たい", "距離", "離れたい", "投げ出", "やめたい", "全部無視"),
    "value_wish": ("大事", "大切", "守りたい", "選びたい", "優先", "欲しい", "ほしい", "願"),
}

_DEEP_OVERCLAIM_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("本当の願い", re.compile(r"本当の願い|心の奥|無意識|本心")),
    ("人格", re.compile(r"人格|性格|本質|怠け|甘え")),
    ("診断", re.compile(r"診断|治療|病気|症状|トラウマ|障害|うつ|ADHD|自律神経")),
    ("原因断定", re.compile(r"(?:原因|理由)は[^。！？!?]{0,24}(?:です|あります)")),
    ("助言断定", re.compile(r"必要があります|すべきです|するべきです")),
    ("あなた断定", re.compile(r"あなた(?:は|の本質|の性格|が)")),
)

# Step14 A-plan readiness guard surfaces. These are rejection signatures,
# not user-facing text templates.
_STEP14_DIAGNOSIS_LIKE_RE = re.compile(r"診断|治療|病気|症状|トラウマ|障害|発達障害|ADHD|うつ|鬱|自律神経|依存症|PTSD|医療|心理療法|心理学的")
_STEP14_PERSONALITY_LABEL_RE = re.compile(r"(?:あなた|その人|本人)(?:は|の)(?:[^。！？!?]{0,28})?(?:性格|人格|本質|タイプ|こういう人|弱い人|強い人|怠け|甘え)")
_STEP14_GENERAL_KNOWLEDGE_RE = re.compile(r"(?:一般的に|普通は|多くの人|誰でも|人はみんな|よくあること|心理学的には|科学的には|医学的には)(?:[^。！？!?]{0,48})(?:です|あります|なります|と言われています)")
_STEP14_CAUSAL_ADVICE_RE = re.compile(r"(?:原因は[^。！？!?]{0,40}(?:です|あります)|必要があります|すべきです|するべきです|しなければなりません|正解です|間違いです)")

_INTERNAL_TEMPLATE_MARKER_RE = re.compile(
    r"role_template|static_observation_text|fallback_observation|input_feedback_text_templates|"
    r"primary_state|core_tension|pressure_sources|limit_signal|value_or_strength|ObservationProfile|PhraseUnit"
)
_TEMPLATE_META_FLAGS = {
    "fixed_string_renderer_used": "phase8_fixed_template_renderer_used",
    "role_template_used": "phase8_role_template_renderer_used",
    "example_phrase_replacement_used": "phase8_example_phrase_replacement_used",
    "fixed_observation_template_used": "phase8_fixed_observation_template_used",
    "fallback_observation_used": "phase8_fallback_observation_used",
}

_PHASE8_ROLE_META: Dict[str, tuple[str, bool]] = {
    "positive_state": ("positive", True),
    "shift_trigger": ("neutral", False),
    "anxiety_return": ("negative", True),
    "fall_contrast": ("mixed", False),
    "anger_surface": ("negative", True),
    "unfairness": ("negative", True),
    "hurt_core": ("negative", True),
    "withdrawal": ("negative", False),
    "known_action": ("neutral", True),
    "anticipation_loop": ("negative", True),
    "perfection_fear": ("negative", True),
    "small_action": ("positive", True),
    "relieved_weight": ("positive", True),
    "achievement": ("positive", True),
    "wish_to_rely": ("mixed", True),
    "burden_fear": ("negative", True),
    "rejection_fear": ("negative", True),
    "limit": ("negative", True),
    "safe_home": ("positive", True),
    "reality_damage": ("negative", True),
    "ordinary_life_wish": ("mixed", True),
    "worsening_risk": ("negative", True),
    "low_energy": ("negative", True),
    "pressure_or_limit": ("negative", False),
    "fatigue_accumulation": ("negative", True),
    "loss_of_control": ("negative", True),
    "small_repair": ("positive", True),
    "avoidance_wish": ("negative", True),
    "value_wish": ("mixed", True),
}

_PRIMARY_ROLE_PRIORITY: tuple[str, ...] = (
    "avoidance_wish",
    "value_wish",
    "loss_of_control",
    "fatigue_accumulation",
    "small_repair",
    "anticipation_loop",
    "perfection_fear",
    "known_action",
    "wish_to_rely",
    "rejection_fear",
    "burden_fear",
    "limit",
    "anger_surface",
    "hurt_core",
    "unfairness",
    "withdrawal",
    "small_action",
    "relieved_weight",
    "achievement",
    "safe_home",
    "reality_damage",
    "ordinary_life_wish",
    "worsening_risk",
    "positive_state",
    "anxiety_return",
    "fall_contrast",
    "low_energy",
    "pressure_or_limit",
)

_PROFILE_ROLE_REQUIREMENTS: tuple[tuple[str, tuple[set[str], ...]], ...] = (
    ("relationship_approach_avoidance", ({"wish_to_rely"}, {"burden_fear", "rejection_fear"}, {"limit", "rejection_fear"})),
    ("reality_escape_tension", ({"safe_home"}, {"reality_damage"}, {"ordinary_life_wish"}, {"worsening_risk", "limit"})),
    ("anger_hurt_boundary", ({"anger_surface"}, {"hurt_core", "unfairness"})),
    ("self_understanding_loop", ({"anticipation_loop"}, {"perfection_fear"})),
    ("positive_progress", ({"small_action"}, {"relieved_weight", "achievement"})),
    ("mixed_positive_anxiety", ({"positive_state"}, {"anxiety_return"})),
    ("energy_fatigue", ({"fatigue_accumulation"}, {"loss_of_control"})),
    ("anxiety_anticipation", ({"anticipation_loop"}, {"anxiety_return", "loss_of_control"})),
    ("value_wish", ({"value_wish"}, {"loss_of_control", "wish_to_rely"})),
)


def _compact(value: Any) -> str:
    return _COMPACT_TRIM_RE.sub("", str(value or ""))


def _span_detected_type(span: Any) -> str:
    if isinstance(span, Mapping):
        return str(span.get("detected_type") or "")
    return str(getattr(span, "detected_type", "") or "")


def _has_any(text: str, terms: Iterable[str]) -> bool:
    return any(term and term in text for term in terms)


def _add_role(roles: List[str], role: str) -> None:
    if role and role not in roles:
        roles.append(role)


def phase8_roles_for_text(text: Any, detected_type: str = "") -> tuple[str, ...]:
    """Return semantic PhraseUnit roles found in one evidence span.

    Profile detection uses the aggregated roles, not direct raw-text profile
    keyword matches.  The checks below are role extractors: they map source
    phrases to Phase8's intermediate roles before any profile is selected.
    """

    c = _compact(text)
    detected = str(detected_type or "").strip()
    if not c or c in _EMOTION_LABELS:
        return tuple()

    roles: List[str] = []

    # Step11 PhraseUnit/role expansion roles
    if _has_any(c, ("仕事で疲れ", "疲れた", "疲れて", "疲れが溜", "疲れがたま", "疲れが抜け", "疲労", "消耗", "体力", "へとへと", "ぐったり", "くたくた", "眠気", "寝ても", "休んでも")):
        _add_role(roles, "fatigue_accumulation")
    if _has_any(c, ("頭が回", "集中が切", "手につか", "手が止ま", "予定が詰", "やることが多", "余裕がな", "追いつ", "動けな")):
        _add_role(roles, "loss_of_control")
    if _has_any(c, ("机を整", "少し整", "片付け", "お茶", "深呼吸", "散歩", "手帳", "少し休め", "休めた", "整えたら", "落ち着いた")):
        _add_role(roles, "small_repair")
    if _has_any(c, ("休みたい", "横になりたい", "寝たい", "逃げたい", "逃げ出", "投げ出", "距離を置", "離れたい", "やめたい", "全部無視")):
        _add_role(roles, "avoidance_wish")
    if _has_any(c, ("大事にしたい", "大切にしたい", "守りたい", "選びたい", "優先したい", "願", "欲しい", "ほしい")):
        _add_role(roles, "value_wish")

    # relationship_approach_avoidance roles
    if _has_any(c, ("頼りたい", "頼ったら", "相談したい", "話したい", "助けを借りたい", "支えてほしい")):
        _add_role(roles, "wish_to_rely")
    if _has_any(c, ("迷惑", "負担", "時間を奪う", "困らせ", "邪魔になる", "言い出せない")):
        _add_role(roles, "burden_fear")
    if _has_any(c, ("嫌われ", "重いと思われ", "離れられ", "面倒だと思われ", "困らせそう", "怖い")) and _has_any(c, ("相手", "嫌われ", "重い", "困らせ", "頼", "相談", "助け")):
        _add_role(roles, "rejection_fear")
    if _has_any(c, ("限界", "抱える", "抱え", "一人で考え続け", "一人で考える", "一人ではきつ", "つらい")):
        _add_role(roles, "limit")

    # anger_hurt_boundary roles
    if _has_any(c, ("腹が立", "怒って", "むっと", "ムッと", "言い方がきつ", "返し方が雑", "雑で")):
        _add_role(roles, "anger_surface")
    if _has_any(c, ("ちゃんと考えて話", "丁寧に伝え", "されなきゃ", "軽く扱われ", "雑に扱われ")):
        _add_role(roles, "unfairness")
    if _has_any(c, ("大事に扱われ", "しんど", "軽く扱われ", "傷つ")):
        _add_role(roles, "hurt_core")
    if _has_any(c, ("面倒", "説明する気力", "気力がなく", "距離を置")):
        _add_role(roles, "withdrawal")

    # self_understanding_loop roles
    if _has_any(c, ("分かってる", "分かっている", "やることは分か", "やることは見えて", "見えている")):
        _add_role(roles, "known_action")
    if _has_any(c, ("考えすぎ", "先のこと", "止まら", "手が止ま", "動けなく", "動けない", "進めない", "考え始め")):
        _add_role(roles, "anticipation_loop")
    if _has_any(c, ("完璧", "適当にやる", "適当", "失敗が怖", "失敗しそう", "失敗が不安", "ちゃんとできない")):
        _add_role(roles, "perfection_fear")

    # positive_progress roles
    if _has_any(c, ("片付け", "洗い物", "少し終えた", "終えた", "少し進められ", "台所が整", "場所が整")):
        _add_role(roles, "small_action")
    if _has_any(c, ("気になってた", "気になっていた", "気持ちが軽", "軽い", "気持ちが落ち着", "落ち着いた", "ほっとした", "整って")):
        _add_role(roles, "relieved_weight")
    if _has_any(c, ("ちゃんとできた", "嬉しい", "進められた", "少し進められ", "ほっとした")) and not _has_any(c, ("ちゃんとできない", "嬉しくない")):
        _add_role(roles, "achievement")

    # reality_escape_tension roles
    if _has_any(c, ("家にいて", "家にいる", "お家", "おうち", "リラックス", "自分のペース", "ペースで過ご", "優先", "整え", "安心でき")):
        _add_role(roles, "safe_home")
    if _has_any(c, ("現実", "ダメージ", "不便", "外に出る準備", "移動", "重くなる")):
        _add_role(roles, "reality_damage")
    if _has_any(c, ("普通に生活したい", "生活したい", "いつも通りに過ごしたい", "いつも通り過ごしたい")):
        _add_role(roles, "ordinary_life_wish")
    if _has_any(c, ("悪化", "体調が崩れ", "崩れそう", "また崩れ")):
        _add_role(roles, "worsening_risk")
    if _has_any(c, ("逃げ出", "投げ出したく", "全部投げ出", "何もしたくない")):
        _add_role(roles, "limit")

    # mixed_positive_anxiety roles
    if _has_any(c, ("友達と話せ", "楽しかった", "笑えた", "元気", "ほっと", "落ち着いた", "安心した")) and "ちゃんとできない" not in c:
        if not _has_any(c, ("家にいる", "家にいて", "自分のペース", "お家", "おうち")):
            _add_role(roles, "positive_state")
    if _has_any(c, ("一人にな", "夜にな", "静かにな", "急に不安", "不安にな", "不安が強", "心配", "落ちる")):
        _add_role(roles, "anxiety_return")
    if _has_any(c, ("落差", "楽しかったはず")):
        _add_role(roles, "fall_contrast")

    if _has_any(c, ("だるい", "何もしたくない")):
        _add_role(roles, "low_energy")
    if detected in {"fear", "constraint", "limit_signal"} and not any(role in roles for role in ("anxiety_return", "limit", "worsening_risk", "perfection_fear", "burden_fear", "rejection_fear")):
        _add_role(roles, "pressure_or_limit")
    if detected in {"wish", "value"} and not roles:
        _add_role(roles, "positive_state")

    return tuple(roles)


def phase8_primary_role_for_text(text: Any, detected_type: str = "") -> tuple[str, str, bool]:
    roles = phase8_roles_for_text(text, detected_type)
    for role in _PRIMARY_ROLE_PRIORITY:
        if role in roles:
            polarity, must_keep = _PHASE8_ROLE_META.get(role, ("neutral", False))
            return role, polarity, must_keep
    return "other", "neutral", False


def phase8_role_meta(role: str) -> tuple[str, bool]:
    return _PHASE8_ROLE_META.get(str(role or ""), ("neutral", False))


def _span_phase8_roles(span: Any) -> tuple[str, ...]:
    return phase8_roles_for_text(_span_raw(span), _span_detected_type(span))


def _roles_match(role_set: set[str], requirements: tuple[set[str], ...]) -> bool:
    return all(role_set.intersection(group) for group in requirements)


@dataclass(frozen=True)
class LimitedSentenceQualityReport:
    passed: bool
    rejection_reasons: List[str] = field(default_factory=list)
    matched_patterns: List[str] = field(default_factory=list)
    emotion_label_lines: List[str] = field(default_factory=list)
    unfinished_fragments: List[str] = field(default_factory=list)
    missing_must_keep_roles: List[str] = field(default_factory=list)


def _sentences(text: Any) -> List[str]:
    return [s.strip() for s in _SENTENCE_SPLIT_RE.split(str(text or "")) if s.strip()]


def _body_sentences(text: Any) -> List[str]:
    return [s for s in _sentences(text) if not _GREETING_RE.match(s)]


def _limited_tail_signatures(sentences: Sequence[str]) -> List[str]:
    signatures: List[str] = []
    for sentence in sentences:
        for key, pattern in _LIMITED_TAIL_PATTERNS:
            if pattern.search(sentence):
                signatures.append(key)
                break
    return signatures


def _repeated_values(values: Sequence[str], *, min_count: int = 2) -> List[str]:
    out: List[str] = []
    for value in values:
        if values.count(value) >= min_count and value not in out:
            out.append(value)
    return out


def _span_raw(span: Any) -> str:
    if isinstance(span, Mapping):
        return str(span.get("raw_text") or "")
    return str(getattr(span, "raw_text", "") or "")


def _span_source(span: Any) -> str:
    if isinstance(span, Mapping):
        return str(span.get("source_field") or "")
    return str(getattr(span, "source_field", "") or "")


def _span_id(span: Any) -> str:
    if isinstance(span, Mapping):
        return str(span.get("span_id") or "")
    return str(getattr(span, "span_id", "") or "")


def _as_id_set(values: Sequence[str] | None) -> set[str]:
    if values is None:
        return set()
    return {str(value or "").strip() for value in values if str(value or "").strip()}


def _text_list(value: Any) -> List[str]:
    if isinstance(value, (list, tuple, set)):
        return [str(item or "").strip() for item in value if str(item or "").strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _candidate_text_spans(evidence_spans: Sequence[Any], used_evidence_span_ids: Sequence[str] | None) -> List[Any]:
    spans = [span for span in list(evidence_spans or []) if _span_source(span) in _TEXT_SOURCE_FIELDS]
    if used_evidence_span_ids is None:
        return spans
    used_ids = _as_id_set(used_evidence_span_ids)
    if not used_ids:
        return []
    return [span for span in spans if _span_id(span).strip() in used_ids]


def _effective_profile_key(*, profile_key: str, evidence_spans: Sequence[Any], composer_meta: Mapping[str, Any] | None) -> str:
    meta = composer_meta if isinstance(composer_meta, Mapping) else {}
    for value in (profile_key, meta.get("profile_key"), meta.get("phase8_profile_key")):
        item = str(value or "").strip()
        if item:
            return item
    return detect_phase8_profile(evidence_spans)


def _required_roles_for_profile(profile_key: str, composer_meta: Mapping[str, Any] | None) -> List[str]:
    meta = composer_meta if isinstance(composer_meta, Mapping) else {}
    configured = _text_list(meta.get("required_roles"))
    if configured:
        return configured
    if not (meta.get("covered_roles") or meta.get("phase8_quality_enforce_required_roles")):
        return []
    return list(_PROFILE_REQUIRED_ROLES.get(str(profile_key or "").strip(), ()))


def _role_reflected_in_text(role: str, text: Any) -> bool:
    compact = _compact(text)
    if not compact or not role:
        return False
    cues = _ROLE_REFLECTION_CUES.get(str(role or ""), tuple())
    if _has_any(compact, cues):
        return True
    if role == "rejection_fear" and "怖" in compact and _has_any(compact, ("相手", "助け", "相談", "頼")):
        return True
    if role == "perfection_fear" and "怖" in compact and _has_any(compact, ("完璧", "適当", "失敗", "ちゃんとできない")):
        return True
    return False


def _missing_required_roles(*, text: str, profile_key: str, composer_meta: Mapping[str, Any] | None) -> List[str]:
    if profile_key not in _KNOWN_PHASE8_PROFILES:
        return []
    meta = composer_meta if isinstance(composer_meta, Mapping) else {}
    covered_roles = set(_text_list(meta.get("covered_roles")))
    missing: List[str] = []
    for role in _required_roles_for_profile(profile_key, meta):
        if role not in covered_roles and not _role_reflected_in_text(role, text):
            missing.append(role)
    return list(dict.fromkeys(missing))


def _raw_source_copy_fragments(*, body_sentences: Sequence[str], evidence_spans: Sequence[Any], used_evidence_span_ids: Sequence[str] | None) -> List[str]:
    source_fragments = [
        _compact(_span_raw(span))
        for span in _candidate_text_spans(evidence_spans, used_evidence_span_ids)
        if len(_compact(_span_raw(span))) >= 8
    ]
    fragments: List[str] = []
    for sentence in body_sentences:
        sentence_norm = _compact(sentence)
        if len(sentence_norm) < 8:
            continue
        for fragment in source_fragments:
            direct_copy = sentence_norm == fragment
            embedded_raw = fragment in sentence_norm and len(fragment) / max(1, len(sentence_norm)) >= 0.74
            embedded_sentence = sentence_norm in fragment and len(sentence_norm) / max(1, len(fragment)) >= 0.86
            if direct_copy or embedded_raw or embedded_sentence:
                fragments.append(sentence)
                break
    return list(dict.fromkeys(fragments))


def _source_terms(compact_raw: str) -> List[str]:
    terms: List[str] = []
    for length in (6, 5, 4, 3):
        for index in range(0, max(0, len(compact_raw) - length + 1)):
            term = compact_raw[index : index + length]
            if term and term not in terms:
                terms.append(term)
        if terms:
            return terms[:12]
    return [compact_raw] if compact_raw else []


def _body_has_text_evidence_overlap(*, body_sentences: Sequence[str], evidence_spans: Sequence[Any], used_evidence_span_ids: Sequence[str] | None) -> bool:
    body_compact = _compact("\n".join(body_sentences))
    if not body_compact:
        return False
    for span in _candidate_text_spans(evidence_spans, used_evidence_span_ids):
        raw = _compact(_span_raw(span))
        if len(raw) < 3:
            continue
        if any(term and term in body_compact for term in _source_terms(raw)):
            return True
    return False


def _matched_deep_overclaims(text: str) -> List[str]:
    matches: List[str] = []
    for label, pattern in _DEEP_OVERCLAIM_PATTERNS:
        if pattern.search(text) and label not in matches:
            matches.append(label)
    return matches


def _matched_step14_overclaims(text: str) -> List[str]:
    matches: List[str] = []
    checks = (
        ("diagnosis_like", _STEP14_DIAGNOSIS_LIKE_RE),
        ("personality_label", _STEP14_PERSONALITY_LABEL_RE),
        ("general_knowledge_completion", _STEP14_GENERAL_KNOWLEDGE_RE),
        ("causal_or_advice_assertion", _STEP14_CAUSAL_ADVICE_RE),
    )
    for label, pattern in checks:
        if pattern.search(text) and label not in matches:
            matches.append(label)
    return matches


def _sentence_shapes_for_step14(sentences: Sequence[str]) -> List[str]:
    # Structural repetition only: do not collapse every Japanese sentence to
    # ``x``.  Step14 must not reduce passed rate by treating ordinary varied
    # sentences as repeated just because they share Japanese characters.
    suffix_patterns = (
        ("表に出ています", re.compile(r"表に出ています[。.!！]?$")),
        ("重なっています", re.compile(r"重なっています[。.!！]?$")),
        ("混ざっています", re.compile(r"混ざっています[。.!！]?$")),
        ("残っています", re.compile(r"残っています[。.!！]?$")),
        ("続いています", re.compile(r"続いています[。.!！]?$")),
        ("同じ中にあります", re.compile(r"同じ中にあります[。.!！]?$")),
    )
    shapes: List[str] = []
    for sentence in sentences:
        for key, pattern in suffix_patterns:
            if pattern.search(sentence):
                shapes.append(key)
                break
    return shapes


def _is_shallow_path(profile_key: str, composer_meta: Mapping[str, Any] | None) -> bool:
    meta = composer_meta if isinstance(composer_meta, Mapping) else {}
    return profile_key == "current_input_core" or bool(meta.get("shallow_observation_path")) or str(meta.get("coverage_scope") or "") == "current_input_core"


def _template_meta_reasons(composer_meta: Mapping[str, Any] | None) -> List[str]:
    meta = composer_meta if isinstance(composer_meta, Mapping) else {}
    return [reason for key, reason in _TEMPLATE_META_FLAGS.items() if bool(meta.get(key))]


def detect_phase8_profile(evidence_spans: Sequence[Any] | None = None) -> str:
    text_spans = [span for span in list(evidence_spans or []) if _span_source(span) in _TEXT_SOURCE_FIELDS]
    roles: List[str] = []
    for span in text_spans:
        roles.extend(_span_phase8_roles(span))

    role_set = set(roles)
    compact_text = _compact("\n".join(_span_raw(span) for span in text_spans))
    if "low_energy" in role_set and role_set.issubset({"low_energy", "limit"}) and len(compact_text) < 40:
        return "short_ambiguous_low_evidence"

    # Step12: long arcs are selected by role composition and source span count,
    # not by direct example sentence matching.
    if (
        len(text_spans) >= 4
        and role_set.intersection({"fatigue_accumulation", "loss_of_control"})
        and role_set.intersection({"value_wish", "avoidance_wish"})
        and role_set.intersection({"small_repair", "limit", "perfection_fear"})
    ):
        return "long_meaning_arc"

    for profile_key, requirements in _PROFILE_ROLE_REQUIREMENTS:
        if _roles_match(role_set, requirements):
            return profile_key
    return "unknown"




# Step4 PhraseUnit material quality guard.
# This is a material-stage filter, not a completed-sentence template.
_STEP4_PHRASE_UNIT_MATERIAL_VERSION = "emlis.phrase_unit_material_quality.v1"
_STEP4_PHRASE_UNIT_MATERIAL_TARGET_STEP = "4_PhraseUnit_material_improvement"
_STEP4_MATERIAL_TRIM = " \t\r\n　、,。.!！?？『』\"'「」（）()[]【】"
_STEP4_CONNECTOR_ONLY_COMPACT = {"けど", "けどさ", "けれど", "だけど", "だけどさ", "でも", "でもさ", "のに", "から", "ので", "なら", "すると", "したら", "それだと", "だと", "ただ", "それで", "普通に"}
_STEP4_SAFE_NOMINAL_SUFFIXES = ("こと", "気持ち", "感覚", "怖さ", "しんどさ", "つらさ", "不安", "願い", "限界", "流れ", "状態")
_STEP4_RESIDUAL_NOMINAL_COMPACT = {"普通こと", "普通にこと", "現実こと", "なんであこと", "考え始めこと", "それだとこと", "自分のことをこと", "けどこと", "けどさこと", "だけどこと", "だけどさこと", "でもこと", "でもさこと", "のにこと", "からこと"}
_STEP4_UNFINISHED_SUFFIX_RE = re.compile(r"(?:なんであ|考え始め|現実と|自分のことを|普通に|それだと|だと|けどさ|だけどさ|でもさ|けど|けれど|だけど|でも|のに|から|ので|なら|すると|したら)$")
_STEP4_ORPHAN_PARTICLE_RE = re.compile(r"[をがにはへでも]$")
_STEP4_BROKEN_NOMINAL_RE = re.compile(r"(?:なんであこと|考え始めこと|現実こと|普通こと|普通にこと|それだとこと|自分のことをこと|けどこと|けどさこと|だけどこと|だけどさこと|でもこと|でもさこと|のにこと|からこと)$")
_STEP4_MALFORMED_NOMINALIZATION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("malformed_nominalization_temporal_fragment", re.compile(r"(?:今まで|これまで|さっき|先ほど|さきほど|このまま|まだ)こと(?:$|[もがはに])")),
    ("malformed_nominalization_adjective_fragment", re.compile(r"(?:大丈夫|平気|普通|不安定|曖昧|中途半端|好き|嫌い|上手|下手)こと(?:$|[もがはに])")),
    ("malformed_nominalization_question_fragment", re.compile(r"(?:ないか|どれ|どこ|なに|何|なんで|どうして)こと(?:$|[もがはに])")),
    ("malformed_nominalization_auxiliary_fragment", re.compile(r"(?:(?<!かも)しれない(?:どれ|どこ|なに|何)?|なっ|し|見え|残っ|重なっ)こと(?:$|[もがはに])")),
    ("malformed_nominalization_te_form_fragment", re.compile(r"(?:なくて|ないで|なれなくて|できなくて|ならなくて|なせなくて|しきれなくて)こと(?:$|[もがはに])")),
    ("malformed_nominalization_tari_fragment", re.compile(r"たりこと(?:$|[もがはにをでへ])")),
    (
        "malformed_nominalization_conditional_fragment",
        re.compile(
            r"(?:なければ|なきゃ|ないと|しないと|しなくては|せねば|しなければ|"
            r"行かなければ|出なければ|やらなければ|取らなければ)こと(?:$|[もがはにをでへ])"
        ),
    ),
    (
        "malformed_nominalization_prediction_noun_fragment",
        re.compile(r"(?:予感|気配|予定|必要|つもり|はず|可能性|見込み|感じ)こと(?:$|[もがはにをでへ])"),
    ),
    (
        "residual_koto_splice_fragment",
        re.compile(r"(?:ことこと|(?:なければ|なきゃ|ないと|しないと|しなくては|せねば|しなければ|行かなければ|出なければ|やらなければ|取らなければ)こと|予感こと|気配こと|予定こと|必要こと|つもりこと|はずこと|可能性こと|見込みこと|感じこと)(?:$|[もがはにをでへ])"),
    ),
    (
        "long_clause_koto_attachment_risk",
        re.compile(
            r".{18,}(?:(?:なければ|なきゃ|ないと|しないと|しなくては|せねば)こと|"
            r"(?:予感|気配|予定|必要|可能性|見込み)こと)(?:$|[もがはにをでへ])"
        ),
    ),
    ("malformed_nominalization_unknown_fragment", re.compile(r"しれない(?:どれ|どこ|なに|何)こと(?:$|[もがはに])")),
)
_STEP4_MALFORMED_NOMINALIZATION_FLAGS = {code for code, _pattern in _STEP4_MALFORMED_NOMINALIZATION_PATTERNS}
_STEP4_BLOCKING_MATERIAL_FLAGS = {"empty_phrase_unit_material", "emotion_label_only", "connector_only_material", "residual_nominal_material", "unfinished_phrase", "orphan_particle", "broken_nominalized_fragment", "too_long_quote", "too_short_phrase_unit_material", "non_text_material_source", *_STEP4_MALFORMED_NOMINALIZATION_FLAGS}


def _step4_material_norm(value: Any) -> str:
    return str(value or "").replace("\u3000", " ").strip(_STEP4_MATERIAL_TRIM)


def _step4_label_compacts() -> set[str]:
    return {_compact(label) for label in _EMOTION_LABELS}


def _step4_add_material_reason(reasons: List[str], matched: List[str], reason: str, fragment: Any) -> None:
    if reason and reason not in reasons:
        reasons.append(reason)
    item = _step4_material_norm(fragment)
    if item and item not in matched:
        matched.append(item)


def phrase_unit_material_flags(
    text: Any,
    *,
    raw_text: Any = "",
    role: str = "",
    detected_type: str = "",
    source_field: str = "",
    max_quote_chars: int = 64,
) -> tuple[str, ...]:
    """Return Step4 material-quality flags before SentencePlan."""
    phrase = _step4_material_norm(text)
    raw = _step4_material_norm(raw_text)
    compact = _compact(phrase)
    raw_compact = _compact(raw)
    labels = _step4_label_compacts()
    reasons: List[str] = []
    matched: List[str] = []

    if not compact:
        _step4_add_material_reason(reasons, matched, "empty_phrase_unit_material", phrase or raw)
    if compact in labels:
        _step4_add_material_reason(reasons, matched, "emotion_label_only", phrase)
    if compact and len(compact) < 3 and compact not in labels:
        _step4_add_material_reason(reasons, matched, "too_short_phrase_unit_material", phrase)

    # Judge the material that will actually be handed to SentencePlan.
    # Raw source text can end with a connector because the evidence splitter cut it there;
    # that must not block a safe compressed PhraseUnit such as "家で落ち着けること".
    safe_suffix = compact.endswith(_STEP4_SAFE_NOMINAL_SUFFIXES)
    if compact in _STEP4_CONNECTOR_ONLY_COMPACT:
        _step4_add_material_reason(reasons, matched, "connector_only_material", phrase)
        _step4_add_material_reason(reasons, matched, "unfinished_phrase", phrase)
    if compact in _STEP4_RESIDUAL_NOMINAL_COMPACT:
        _step4_add_material_reason(reasons, matched, "residual_nominal_material", phrase)
        _step4_add_material_reason(reasons, matched, "unfinished_phrase", phrase)
    if _STEP4_BROKEN_NOMINAL_RE.search(compact):
        _step4_add_material_reason(reasons, matched, "broken_nominalized_fragment", phrase)
        _step4_add_material_reason(reasons, matched, "unfinished_phrase", phrase)
    for code, pattern in _STEP4_MALFORMED_NOMINALIZATION_PATTERNS:
        if pattern.search(compact):
            _step4_add_material_reason(reasons, matched, code, phrase)
            _step4_add_material_reason(reasons, matched, "broken_nominalized_fragment", phrase)
            if code in {
                "malformed_nominalization_question_fragment",
                "malformed_nominalization_te_form_fragment",
                "malformed_nominalization_tari_fragment",
                "malformed_nominalization_conditional_fragment",
                "malformed_nominalization_prediction_noun_fragment",
                "residual_koto_splice_fragment",
                "long_clause_koto_attachment_risk",
                "malformed_nominalization_unknown_fragment",
            }:
                _step4_add_material_reason(reasons, matched, "unfinished_phrase", phrase)
    if not safe_suffix and _STEP4_UNFINISHED_SUFFIX_RE.search(compact):
        _step4_add_material_reason(reasons, matched, "unfinished_phrase", phrase)
    if not safe_suffix and _STEP4_ORPHAN_PARTICLE_RE.search(compact):
        _step4_add_material_reason(reasons, matched, "orphan_particle", phrase)

    if compact and len(compact) > int(max_quote_chars or 64):
        _step4_add_material_reason(reasons, matched, "too_long_quote", phrase)
    if raw_compact and compact == raw_compact and len(compact) > 44:
        _step4_add_material_reason(reasons, matched, "too_long_quote", phrase)
    if str(detected_type or "").strip() in {"emotion"} or str(source_field or "").strip() in {"emotion_details", "emotions", "category"}:
        _step4_add_material_reason(reasons, matched, "non_text_material_source", phrase or raw)

    return tuple(dict.fromkeys(reasons))


def phrase_unit_material_rejection_flags(flags: Iterable[Any]) -> tuple[str, ...]:
    out: List[str] = []
    for flag in flags or []:
        item = str(flag or "").strip()
        if item and item in _STEP4_BLOCKING_MATERIAL_FLAGS and item not in out:
            out.append(item)
    return tuple(out)


def judge_phrase_unit_material_quality(
    text: Any,
    *,
    raw_text: Any = "",
    role: str = "",
    detected_type: str = "",
    source_field: str = "",
    max_quote_chars: int = 64,
) -> Dict[str, Any]:
    flags = phrase_unit_material_flags(
        text,
        raw_text=raw_text,
        role=role,
        detected_type=detected_type,
        source_field=source_field,
        max_quote_chars=max_quote_chars,
    )
    rejection_reasons = phrase_unit_material_rejection_flags(flags)
    return {
        "version": _STEP4_PHRASE_UNIT_MATERIAL_VERSION,
        "target_step": _STEP4_PHRASE_UNIT_MATERIAL_TARGET_STEP,
        "step": _STEP4_PHRASE_UNIT_MATERIAL_TARGET_STEP,
        "passed": not rejection_reasons,
        "usable_material": not rejection_reasons,
        "material_quality_passed": not rejection_reasons,
        "material_stage_filter_enabled": True,
        "material_stage_filtering_enabled": True,
        "quality_flags": list(flags),
        "rejection_reasons": list(rejection_reasons),
        "unsafe_reasons": list(rejection_reasons),
        "blocking_flags": list(rejection_reasons),
        "matched_fragments": [],
        "emotion_label_only": "emotion_label_only" in flags,
        "emotion_label_only_blocked": "emotion_label_only" in rejection_reasons,
        "unfinished_fragment": "unfinished_phrase" in flags,
        "unfinished_fragment_blocked": "unfinished_phrase" in rejection_reasons,
        "orphan_particle": "orphan_particle" in flags,
        "orphan_particle_blocked": "orphan_particle" in rejection_reasons,
        "too_long_quote": "too_long_quote" in flags,
        "too_long_quote_blocked": "too_long_quote" in rejection_reasons,
        "connector_only_material_blocked": "connector_only_material" in rejection_reasons,
        "residual_nominal_material_blocked": "residual_nominal_material" in rejection_reasons,
        "broken_nominalized_fragment_blocked": "broken_nominalized_fragment" in rejection_reasons,
        "malformed_nominalization_guard_enabled": True,
        "malformed_phrase_unit_guard_enabled": True,
        "malformed_nominalization_blocked": any(str(reason).startswith("malformed_nominalization_") or str(reason) in {"residual_koto_splice_fragment", "long_clause_koto_attachment_risk"} for reason in rejection_reasons),
        "malformed_nominalization_rejection_reasons": [reason for reason in rejection_reasons if str(reason).startswith("malformed_nominalization_") or str(reason) in {"residual_koto_splice_fragment", "long_clause_koto_attachment_risk"}],
        "malformed_nominalization_temporal_fragment_blocked": "malformed_nominalization_temporal_fragment" in rejection_reasons,
        "malformed_nominalization_adjective_fragment_blocked": "malformed_nominalization_adjective_fragment" in rejection_reasons,
        "malformed_nominalization_question_fragment_blocked": "malformed_nominalization_question_fragment" in rejection_reasons,
        "malformed_nominalization_auxiliary_fragment_blocked": "malformed_nominalization_auxiliary_fragment" in rejection_reasons,
        "malformed_nominalization_te_form_fragment_blocked": "malformed_nominalization_te_form_fragment" in rejection_reasons,
        "malformed_nominalization_tari_fragment_blocked": "malformed_nominalization_tari_fragment" in rejection_reasons,
        "malformed_nominalization_conditional_fragment_blocked": "malformed_nominalization_conditional_fragment" in rejection_reasons,
        "malformed_nominalization_prediction_noun_fragment_blocked": "malformed_nominalization_prediction_noun_fragment" in rejection_reasons,
        "residual_koto_splice_fragment_blocked": "residual_koto_splice_fragment" in rejection_reasons,
        "long_clause_koto_attachment_risk_blocked": "long_clause_koto_attachment_risk" in rejection_reasons,
        "malformed_nominalization_unknown_fragment_blocked": "malformed_nominalization_unknown_fragment" in rejection_reasons,
        "role": str(role or "").strip(),
        "detected_type": str(detected_type or "").strip(),
        "source_field": str(source_field or "").strip(),
        "raw_text_included": False,
        "raw_input_required_for_debug": False,
        "input_specific_template_used": False,
        "completion_sentence_templates_added": False,
    }


def evaluate_phrase_unit_material_quality(text: Any, **kwargs: Any) -> Dict[str, Any]:
    return judge_phrase_unit_material_quality(text, **kwargs)


def phase8_phrase_unit_material_quality_flags(text: Any, **kwargs: Any) -> tuple[str, ...]:
    return phrase_unit_material_flags(text, **kwargs)


def is_safe_phrase_unit_material(text: Any, **kwargs: Any) -> bool:
    return bool(judge_phrase_unit_material_quality(text, **kwargs).get("passed"))


def phrase_unit_material_quality_policy_meta() -> Dict[str, Any]:
    return {
        "version": _STEP4_PHRASE_UNIT_MATERIAL_VERSION,
        "target_step": _STEP4_PHRASE_UNIT_MATERIAL_TARGET_STEP,
        "step": _STEP4_PHRASE_UNIT_MATERIAL_TARGET_STEP,
        "material_stage_filter_enabled": True,
        "material_stage_filtering_enabled": True,
        "unfinished_fragment_guarded": True,
        "orphan_particle_guarded": True,
        "emotion_label_single_guarded": True,
        "too_long_quote_guarded": True,
        "malformed_nominalization_guard_enabled": True,
        "malformed_phrase_unit_guard_enabled": True,
        "malformed_nominalization_temporal_fragment_guarded": True,
        "malformed_nominalization_adjective_fragment_guarded": True,
        "malformed_nominalization_question_fragment_guarded": True,
        "malformed_nominalization_auxiliary_fragment_guarded": True,
        "malformed_nominalization_te_form_fragment_guarded": True,
        "malformed_nominalization_tari_fragment_guarded": True,
        "malformed_nominalization_conditional_fragment_guarded": True,
        "malformed_nominalization_prediction_noun_fragment_guarded": True,
        "residual_koto_splice_fragment_guarded": True,
        "long_clause_koto_attachment_risk_guarded": True,
        "malformed_nominalization_unknown_fragment_guarded": True,
        "input_specific_template_used": False,
        "completion_sentence_templates_added": False,
    }

def judge_limited_sentence_quality(
    *,
    comment_text: Any,
    evidence_spans: Sequence[Any] = (),
    profile_key: str = "",
    used_evidence_span_ids: Sequence[str] | None = None,
    composer_meta: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    text = str(comment_text or "").strip()
    meta = composer_meta if isinstance(composer_meta, Mapping) else {}
    reasons: List[str] = []
    matched: List[str] = []
    label_lines: List[str] = []
    unfinished: List[str] = []
    body = _body_sentences(text)

    if not text:
        reasons.append("empty_text")

    for sentence in body:
        normalized = sentence.strip(" 　、,。.!！?？")
        if normalized in _EMOTION_LABELS:
            label_lines.append(normalized)
        if _TRAILING_UNFINISHED_RE.search(normalized):
            unfinished.append(sentence)
        for key, pattern in _BROKEN_SURFACE_PATTERNS:
            if pattern.search(sentence):
                reasons.append(key)
                matched.append(sentence)
        for key, pattern in _GENERIC_CLOSING_PATTERNS:
            if pattern.search(sentence):
                reasons.append(key)
                matched.append(sentence)

    if label_lines:
        reasons.append("phase8_emotion_label_body_line")
        matched.extend(label_lines)
    if unfinished:
        reasons.append("phase8_unfinished_phrase")
        matched.extend(unfinished)

    effective_profile = _effective_profile_key(profile_key=profile_key, evidence_spans=evidence_spans, composer_meta=meta)
    if effective_profile not in _SHALLOW_PROFILE_KEYS and len(body) < 2:
        reasons.append("phase8_body_too_short")

    missing_roles = _missing_required_roles(text=text, profile_key=effective_profile, composer_meta=meta)
    if missing_roles:
        reasons.append("phase8_missing_required_role")
        reasons.append("phase8_missing_must_keep_roles")
        matched.extend(missing_roles)

    raw_copy_fragments = _raw_source_copy_fragments(
        body_sentences=body,
        evidence_spans=evidence_spans,
        used_evidence_span_ids=used_evidence_span_ids,
    )
    if raw_copy_fragments:
        reasons.append("phase8_raw_evidence_sentence_copy")
        matched.extend(raw_copy_fragments)

    deep_overclaims = _matched_deep_overclaims(text)
    if deep_overclaims:
        reasons.append("phase8_deep_overclaim")
        if "本当の願い" in deep_overclaims:
            reasons.append("phase8_ungrounded_deep_wish")
        if "人格" in deep_overclaims:
            reasons.append("phase8_personality_overclaim")
            reasons.append("personality_label")
        if "診断" in deep_overclaims:
            reasons.append("phase8_diagnosis_overclaim")
            reasons.append("diagnosis_like")
        if "原因断定" in deep_overclaims:
            reasons.append("phase8_causal_overclaim")
        if "助言断定" in deep_overclaims:
            reasons.append("phase8_advice_overclaim")
        matched.extend(deep_overclaims)

    step14_overclaims = _matched_step14_overclaims(text)
    if step14_overclaims:
        reasons.append("phase14_overclaim_guard")
        for label in step14_overclaims:
            reasons.append(label)
            if label == "diagnosis_like":
                reasons.append("phase14_diagnosis_like")
            elif label == "personality_label":
                reasons.append("phase14_personality_label")
            elif label == "general_knowledge_completion":
                reasons.append("phase14_general_knowledge_completion")
            elif label == "causal_or_advice_assertion":
                reasons.append("phase14_causal_or_advice_assertion")
        matched.extend(step14_overclaims)

    if _is_shallow_path(effective_profile, meta):
        used_text_spans = _candidate_text_spans(evidence_spans, used_evidence_span_ids)
        if not used_text_spans:
            reasons.append("phase8_missing_used_text_evidence")
            reasons.append("phase8_current_input_core_missing_text_evidence")
        if not _body_has_text_evidence_overlap(
            body_sentences=body,
            evidence_spans=evidence_spans,
            used_evidence_span_ids=used_evidence_span_ids,
        ):
            reasons.append("phase8_shallow_unbacked_text")
        if deep_overclaims:
            reasons.append("phase8_shallow_overclaim")

    template_reasons = _template_meta_reasons(meta)
    if template_reasons:
        reasons.extend(template_reasons)
    if _INTERNAL_TEMPLATE_MARKER_RE.search(text):
        reasons.append("phase8_internal_template_marker_visible")
        matched.append("internal_template_marker")

    repeated_tails = _repeated_values(_limited_tail_signatures(body), min_count=2)
    if repeated_tails:
        reasons.append("phase8_repeated_sentence_tail")
        reasons.append("repeated_surface")
        matched.extend(repeated_tails)

    repeated_shapes = _repeated_values(_sentence_shapes_for_step14(body), min_count=3)
    if repeated_shapes and len(body) >= 4:
        reasons.append("repeated_surface")
        reasons.append("phase14_repeated_surface")
        matched.extend(repeated_shapes)

    reasons = list(dict.fromkeys(reasons))
    matched = list(dict.fromkeys(matched))
    return {
        "passed": not reasons,
        "rejection_reasons": reasons,
        "matched_surfaces": matched,
        "matched_patterns": matched,
        "matched_fragments": matched,
        "emotion_label_lines": label_lines,
        "unfinished_fragments": unfinished,
        "missing_must_keep_roles": missing_roles,
        "missing_required_roles": missing_roles,
        "raw_copy_fragments": raw_copy_fragments,
        "deep_overclaim_matches": deep_overclaims,
        "step14_overclaim_matches": step14_overclaims,
        "step14_repeated_surface_shapes": repeated_shapes,
        "step14_guard_strengthening": {
            "version": "emlis.guard_strengthening.v1",
            "target_step": "Step14_guard_strengthening",
            "diagnosis_like_guarded": "diagnosis_like" in reasons,
            "personality_label_guarded": "personality_label" in reasons,
            "general_knowledge_completion_guarded": "general_knowledge_completion" in reasons,
            "repeated_surface_guarded": "repeated_surface" in reasons,
            "guard_threshold_relaxed": False,
        },
        "template_meta_rejection_reasons": template_reasons,
        "profile_key": effective_profile,
        "body_sentence_count": len(body),
        "shallow_text_evidence_count": len(_candidate_text_spans(evidence_spans, used_evidence_span_ids)),
    }


def evaluate_limited_sentence_quality(*args: Any, **kwargs: Any) -> Dict[str, Any]:
    comment_text = kwargs.pop("comment_text", None)
    if args:
        comment_text = args[0]
    # Ignore compatibility-only kwargs that this mechanical guard does not need.
    kwargs.pop("composer_model", None)
    return judge_limited_sentence_quality(comment_text=comment_text, **kwargs)


__all__ = [
    "LimitedSentenceQualityReport",
    "detect_phase8_profile",
    "phase8_roles_for_text",
    "phase8_primary_role_for_text",
    "phase8_role_meta",
    "judge_limited_sentence_quality",
    "evaluate_limited_sentence_quality",
    "phrase_unit_material_flags",
    "phase8_phrase_unit_material_quality_flags",
    "phrase_unit_material_rejection_flags",
    "judge_phrase_unit_material_quality",
    "evaluate_phrase_unit_material_quality",
    "is_safe_phrase_unit_material",
    "phrase_unit_material_quality_policy_meta",
]
