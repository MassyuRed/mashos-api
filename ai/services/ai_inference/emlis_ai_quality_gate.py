# -*- coding: utf-8 -*-
"""EmlisAI quality gate for the new national core system.

The evaluator itself does not rewrite text, but vNext callers use its result as
a pre-return gate.  A failed immediate reply must be repaired or replaced with a
safe understanding fallback before ``input_feedback.comment_text`` is shown.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Dict, Mapping, Sequence

EMLIS_AI_QUALITY_GATE_SCHEMA_VERSION = "emlis.quality.v2"

_DIAGNOSIS_OR_OVERCLAIM_RE = re.compile(
    r"(うつ病|鬱病|双極性障害|発達障害|ADHD|ASD|診断|病気です|確実に|絶対に|本質的に|あなたは.*タイプ)"
)
_HISTORY_SOURCE_KEYS = {
    "history",
    "input_summary",
    "myweb_home_summary",
    "today_question",
    "derived_user_model",
}
_CROSS_CORE_SOURCE_KEYS = {
    "piece",
    "emotion_report",
    "self_structure_report",
}

_EMOTION_STRENGTH_DISPLAY_RE = re.compile(r"(喜び|悲しみ|怒り|不安|平穏|自己理解|恐れ|焦り)（(?:弱|中|強)）")
_UNNATURAL_REPLY_RE = re.compile(
    r"(になるです|しているです|だったです|したです|ですです|かなぁのあと|というところが残っていた|今回いちばん残っていた言葉|中心としては.*（(?:弱|中|強)）)"
)
_BROKEN_CONNECTION_RE = re.compile(
    r"(それだと|けど|けれど|でも|から|ので|のに|だって)こと"
    r"|ことが、今回(?:大きく|いちばん)残っていたのですね"
    r"|というところが残っていたのですね"
    r"|今回いちばん残っていた言葉"
    r"|かなぁのあと"
)
_BROKEN_NOUN_PHRASE_RE = re.compile(
    r"(だ|だから|けど|けれど|から)(気持ち|思い|願い|状態)"
    r""
)
_ABSTRACT_HISTORY_RE = re.compile(r"(最近の履歴の中でも、近いテーマ|最近の流れも踏まえて|今の気持ちを見ます|近いテーマがまた顔を出して)")
_PRESENCE_RE = re.compile(r"(軽く扱いません|雑に扱いません|小さく扱いません|そのまま置いて大丈夫|きれいにしなくて大丈夫|そばに置いて|大切にします|大切に扱います|一緒に見ていきます|一緒に向き合います|苦しさと、その中に残っている強さ)")
_MIDSTREAM_OPENING_RE = re.compile(r"^(ただ同時に|でも同時に|それでも|だから|だからこそ|そのため|一方で|ただ)[、,]")
_STALE_MEANING_RE = re.compile(r"(?!)")
_MECHANICAL_META_LANGUAGE_RE = re.compile(r"(認識しています|入力として|構造として|分析すると|理解しました|受け取りました|受理しました)")
_INTERNAL_OBSERVATION_LANGUAGE_RE = re.compile(r"(コンフォートゾーン|スペック|精神の問題|皮算用|要求と期待が膨れ上が|本質は|あなたの本質)")
_SECOND_PERSON_PRONOUN_RE = re.compile(r"(あなたは|あなたの|あなたが|あなたに)")
_EMPTY_ACK_LINE_RE = re.compile(r"^(?:今回は、?)?(?:書いてくれた)?(?:内容|入力|言葉|気持ち|感情).{0,18}受け取(?:り|る|ります|りました|っています).{0,4}$")
_RELATION_WORDS = ("一方で", "だけでなく", "からこそ", "重なって", "つながって", "その自分ごと", "切り離さず", "気づいていて", "間で", "同時に", "両方", "良さ", "不便さ")
_UNDERSTANDING_WORDS = ("のですね", "だったのですね", "苦しかった", "重なって", "気づいていて", "気づいています", "見ていた", "見ます", "見ています", "ありました", "あります", "軽く扱いません", "小さく扱いません", "大切にします", "状態として", "圧迫", "弱さではなく", "強さ", "一緒に見ていきます")


@dataclass(frozen=True)
class EmlisAIQualityGateResult:
    passed: bool
    current_input_central: bool
    history_allowed: bool
    cross_core_allowed: bool
    evidence_required_satisfied: bool
    overclaim_suppressed: bool
    diagnosis_blocked: bool
    reply_length_within_limit: bool
    capability_profile: Dict[str, Any]
    understanding_language_ok: bool = True
    receive_repetition_ok: bool = True
    user_word_usage_ok: bool = True
    relationship_line_ok: bool = True
    empty_ack_blocked: bool = True
    mechanical_meta_language_ok: bool = True
    raw_echo_only_blocked: bool = True
    broken_connection_blocked: bool = True
    sentence_ending_variety_ok: bool = True
    presence_line_present: bool = True
    abstract_history_reference_blocked: bool = True
    final_reader_passed: bool = True
    pre_return_blocking_enabled: bool = False
    preflight_passed: bool = True
    repair_attempted: bool = False
    repair_passed: bool = False
    safe_fallback_used: bool = False
    blocked_issue_codes: Sequence[str] = field(default_factory=tuple)
    meaning_coverage_ok: bool = True
    long_input_depth_ok: bool = True
    single_focus_overcompression_blocked: bool = True
    required_role_coverage_ok: bool = True
    clear_long_input_not_underanswered: bool = True
    piece_like_summary_blocked: bool = True
    major_meaning_retention_ok: bool = True
    must_keep_coverage_ok: bool = True
    own_happiness_wish_not_dropped: bool = True
    betrayal_fear_not_dropped: bool = True
    concrete_wishes_not_dropped: bool = True
    present_effort_not_dropped: bool = True
    broken_noun_phrase_blocked: bool = True
    response_composition_ok: bool = True
    opening_thesis_present: bool = True
    first_content_line_not_midstream: bool = True
    transition_coherence_ok: bool = True
    current_input_grounding_ok: bool = True
    stale_meaning_block_leak_blocked: bool = True
    internal_observation_language_blocked: bool = True
    second_person_pronoun_blocked: bool = True

    def as_meta(self) -> Dict[str, Any]:
        return {
            "schema_version": EMLIS_AI_QUALITY_GATE_SCHEMA_VERSION,
            "passed": bool(self.passed),
            "current_input_central": bool(self.current_input_central),
            "history_allowed": bool(self.history_allowed),
            "cross_core_allowed": bool(self.cross_core_allowed),
            "evidence_required_satisfied": bool(self.evidence_required_satisfied),
            "overclaim_suppressed": bool(self.overclaim_suppressed),
            "diagnosis_blocked": bool(self.diagnosis_blocked),
            "reply_length_within_limit": bool(self.reply_length_within_limit),
            "understanding_language_ok": bool(self.understanding_language_ok),
            "receive_repetition_ok": bool(self.receive_repetition_ok),
            "user_word_usage_ok": bool(self.user_word_usage_ok),
            "relationship_line_ok": bool(self.relationship_line_ok),
            "empty_ack_blocked": bool(self.empty_ack_blocked),
            "mechanical_meta_language_ok": bool(self.mechanical_meta_language_ok),
            "raw_echo_only_blocked": bool(self.raw_echo_only_blocked),
            "broken_connection_blocked": bool(self.broken_connection_blocked),
            "sentence_ending_variety_ok": bool(self.sentence_ending_variety_ok),
            "presence_line_present": bool(self.presence_line_present),
            "abstract_history_reference_blocked": bool(self.abstract_history_reference_blocked),
            "final_reader_passed": bool(self.final_reader_passed),
            "pre_return_blocking_enabled": bool(self.pre_return_blocking_enabled),
            "preflight_passed": bool(self.preflight_passed),
            "repair_attempted": bool(self.repair_attempted),
            "repair_passed": bool(self.repair_passed),
            "safe_fallback_used": bool(self.safe_fallback_used),
            "blocked_issue_codes": list(self.blocked_issue_codes or []),
            "meaning_coverage_ok": bool(self.meaning_coverage_ok),
            "long_input_depth_ok": bool(self.long_input_depth_ok),
            "single_focus_overcompression_blocked": bool(self.single_focus_overcompression_blocked),
            "required_role_coverage_ok": bool(self.required_role_coverage_ok),
            "clear_long_input_not_underanswered": bool(self.clear_long_input_not_underanswered),
            "piece_like_summary_blocked": bool(self.piece_like_summary_blocked),
            "major_meaning_retention_ok": bool(self.major_meaning_retention_ok),
            "must_keep_coverage_ok": bool(self.must_keep_coverage_ok),
            "own_happiness_wish_not_dropped": bool(self.own_happiness_wish_not_dropped),
            "betrayal_fear_not_dropped": bool(self.betrayal_fear_not_dropped),
            "concrete_wishes_not_dropped": bool(self.concrete_wishes_not_dropped),
            "present_effort_not_dropped": bool(self.present_effort_not_dropped),
            "broken_noun_phrase_blocked": bool(self.broken_noun_phrase_blocked),
            "response_composition_ok": bool(self.response_composition_ok),
            "opening_thesis_present": bool(self.opening_thesis_present),
            "first_content_line_not_midstream": bool(self.first_content_line_not_midstream),
            "transition_coherence_ok": bool(self.transition_coherence_ok),
            "current_input_grounding_ok": bool(self.current_input_grounding_ok),
            "stale_meaning_block_leak_blocked": bool(self.stale_meaning_block_leak_blocked),
            "internal_observation_language_blocked": bool(self.internal_observation_language_blocked),
            "second_person_pronoun_blocked": bool(self.second_person_pronoun_blocked),
            "capability_profile": dict(self.capability_profile or {}),
        }


def _line_count(text: Any) -> int:
    value = str(text or "").strip()
    if not value:
        return 0
    explicit_lines = [
        line
        for line in value.splitlines()
        if line.strip() and line.strip() != "Emlisです。" and not line.strip().endswith("Emlisです。")
    ]
    if len(explicit_lines) > 1:
        return len(explicit_lines)
    body = "\n".join(explicit_lines) if explicit_lines else ""
    if not body:
        return 0
    return max(1, len([chunk for chunk in re.split(r"[。！？!?]+", body) if chunk.strip()]))


def _used_history_sources(used_sources: Sequence[Any]) -> set[str]:
    return {str(item or "").strip() for item in (used_sources or []) if str(item or "").strip()} & _HISTORY_SOURCE_KEYS


def _used_cross_core_sources(used_sources: Sequence[Any]) -> set[str]:
    return {str(item or "").strip() for item in (used_sources or []) if str(item or "").strip()} & _CROSS_CORE_SOURCE_KEYS


def _compact(value: Any) -> str:
    return re.sub(r"[\s　、,。.!！?？\t\n\r「」『』（）()]", "", str(value or ""))



def _anchor_terms(sample_user_word_anchors: Sequence[Any]) -> list[str]:
    terms: list[str] = []
    for item in sample_user_word_anchors or []:
        if not isinstance(item, Mapping):
            continue
        text = str(item.get("text") or "").strip()
        if not text:
            continue
        # Use short surface fragments from the current input only.  This is a
        # generic grounding check, not an example-specific token list.
        cleaned = re.sub(r"[、,。.!！?？\s　]+", " ", text).strip()
        if 3 <= len(cleaned) <= 22 and cleaned not in terms:
            terms.append(cleaned)
        for chunk in re.split(r"\s+|、|,", cleaned):
            chunk = chunk.strip()
            if 3 <= len(chunk) <= 14 and chunk not in terms:
                terms.append(chunk)
    return terms[:12]


def _user_word_usage_ok(text: str, sample_user_word_anchors: Sequence[Any], user_word_anchor_count: int) -> bool:
    if int(user_word_anchor_count or 0) < 2:
        return True
    compact_text = _compact(text)
    terms = _anchor_terms(sample_user_word_anchors)
    if not terms:
        return True
    used = sum(1 for term in terms if _compact(term) and _compact(term) in compact_text)
    required = 2 if int(user_word_anchor_count or 0) >= 4 else 1
    return used >= min(required, len(terms))


def _relationship_line_ok(text: str, patterns: Sequence[Any]) -> bool:
    pattern_set = {str(item or "") for item in (patterns or [])}
    if not pattern_set:
        return True
    return any(word in text for word in _RELATION_WORDS)


def _raw_echo_only_blocked(text: str) -> bool:
    for line in [line.strip() for line in str(text or "").splitlines() if line.strip()]:
        if "受け取" in line and re.fullmatch(r"「[^」]{1,80}」(?:と書いてくれた)?(?:こと|ところ)?を?.{0,14}受け取(?:ります|りました|りたいです)。?", line):
            return False
    return True


def _ending_group(line: str) -> str:
    if line.endswith("のですね。") or line.endswith("のですね"):
        return "ne_desu"
    if line.endswith("のだと思います。") or line.endswith("と思います。"):
        return "omoimasu"
    if line.endswith("ありました。") or line.endswith("いました。"):
        return "arimashita"
    if line.endswith("ません。"):
        return "masen"
    return "other"


def _sentence_ending_variety_ok(text: str) -> bool:
    lines = [line.strip() for line in str(text or "").splitlines() if line.strip()]
    if sum(line.count("のですね") for line in lines) > 2:
        return False
    groups = [_ending_group(line) for line in lines]
    return not any(a == b == c and a != "other" for a, b, c in zip(groups, groups[1:], groups[2:]))


def _sample_block_summaries(meaning_coverage: Mapping[str, Any] | None) -> list[str]:
    if not isinstance(meaning_coverage, Mapping):
        return []
    blocks = meaning_coverage.get("sample_blocks") if isinstance(meaning_coverage.get("sample_blocks"), list) else []
    out: list[str] = []
    for block in blocks:
        if not isinstance(block, Mapping):
            continue
        summary = str(block.get("summary") or block.get("title") or "").strip()
        if summary:
            out.append(summary)
    return out


def _sample_blocks(meaning_coverage: Mapping[str, Any] | None) -> list[Mapping[str, Any]]:
    if not isinstance(meaning_coverage, Mapping):
        return []
    blocks = meaning_coverage.get("sample_blocks") if isinstance(meaning_coverage.get("sample_blocks"), list) else []
    return [block for block in blocks if isinstance(block, Mapping)]


def _sample_block_covered(text: str, block: Mapping[str, Any]) -> bool:
    summary = str(block.get("summary") or block.get("title") or "").strip()
    if _summary_covered(text, summary):
        return True
    role = str(block.get("role") or "").strip()
    terms = _role_retention_terms(role)
    return bool(terms and any(term in text for term in terms))


def _content_terms(value: str) -> set[str]:
    cleaned = re.sub(r"[\s　、,。.!！?？「」『』（）()]", " ", str(value or ""))
    terms = set()
    for part in cleaned.split():
        part = part.strip()
        if 3 <= len(part) <= 16:
            terms.add(part)
        if len(part) > 16:
            terms.add(part[:16])
    return terms


def _summary_covered(text: str, summary: str) -> bool:
    compact_text = _compact(text)
    if _compact(summary) and _compact(summary)[:18] in compact_text:
        return True
    terms = _content_terms(summary)
    if not terms:
        return True
    return any(_compact(term) and _compact(term) in compact_text for term in terms)



def _observation_frame_coverage_ok(text: str, meaning_coverage: Mapping[str, Any] | None) -> bool:
    if not isinstance(meaning_coverage, Mapping) or not bool(meaning_coverage.get("observation_frame_present")):
        return False
    line_count = _line_count(text)
    required_roles = [str(item or "") for item in list(meaning_coverage.get("observation_required_line_roles") or [])]
    has_state = "状態" in text or "見ています" in text
    has_relation = any(word in text for word in ("間で", "同時", "重なって", "両方", "良さ", "不便さ")) or "tension_relation" not in required_roles
    has_pressure = ("圧迫" in text or "気をつけ" in text) or "pressure_state" not in required_roles
    has_escape = ("逃げ" in text or "弱さではなく" in text) or "escape_signal" not in required_roles
    has_strength = ("強さ" in text or "向き合" in text) or "strength" not in required_roles
    has_close = bool(_PRESENCE_RE.search(text))
    return bool(line_count >= 4 and has_state and has_relation and has_pressure and has_escape and has_strength and has_close)

def _evaluate_meaning_coverage(text: str, meaning_coverage: Mapping[str, Any] | None) -> tuple[bool, bool, bool, bool, bool, bool]:
    if _observation_frame_coverage_ok(text, meaning_coverage):
        return True, True, True, True, True, True
    if not isinstance(meaning_coverage, Mapping) or not bool(meaning_coverage.get("clear_long_input")):
        return True, True, True, True, True, True
    line_count = _line_count(text)
    min_blocks = int(meaning_coverage.get("min_blocks_to_cover") or 0)
    selected_block_count = int(meaning_coverage.get("selected_block_count") or len(meaning_coverage.get("selected_block_keys") or []) or 0)
    blocks = _sample_blocks(meaning_coverage)
    summaries = _sample_block_summaries(meaning_coverage)
    covered = sum(1 for block in blocks if _sample_block_covered(text, block)) if blocks else sum(1 for summary in summaries if _summary_covered(text, summary))
    item_count = len(blocks) if blocks else len(summaries)
    required = min(max(3, min_blocks), max(1, item_count)) if item_count else max(3, min_blocks)
    required_role_coverage_ok = covered >= required if item_count else line_count >= max(5, min_blocks + 1)
    long_input_depth_ok = line_count >= max(5, min_blocks + 1)
    single_focus_overcompression_blocked = not (line_count <= 4 and selected_block_count >= 5)
    clear_long_input_not_underanswered = required_role_coverage_ok and long_input_depth_ok and single_focus_overcompression_blocked
    piece_like_summary_blocked = not (line_count <= 3 and any(token in text for token in ("問い", "答え")))
    meaning_coverage_ok = required_role_coverage_ok and clear_long_input_not_underanswered and piece_like_summary_blocked
    return meaning_coverage_ok, long_input_depth_ok, single_focus_overcompression_blocked, required_role_coverage_ok, clear_long_input_not_underanswered, piece_like_summary_blocked


def _role_retention_terms(role: str) -> tuple[str, ...]:
    return {
        "other_contribution": ("誰かの役に立",),
        "self_dislike_from_halfway": ("中途半端", "好きになれない"),
        "future_not_giving_up": ("諦めたくない",),
        "betrayal_fear": ("諦めている自分", "裏切られたくない", "裏切られるのが怖"),
        "own_happiness_wish": ("幸せになりたい",),
        "concrete_life_wishes": ("好きなこと", "パートナー", "楽しみたい", "たのしみたい"),
        "unreachable_wish": ("手の届かない",),
        "present_effort_toward_wish": ("今頑張れること", "今できること"),
        "burden_avoidance": ("心配", "負担", "我慢", "丸く収"),
        "self_suppression": ("我慢", "正しい"),
        "limit_or_exhaustion": ("一人で抱え込", "余裕がなく", "しんど"),
        "fatigue_or_limit": ("しんど", "疲", "余裕"),
        "support_need": ("話したり頼ったり", "頼る", "話す"),
        "self_protection": ("距離を取", "無理しない選択", "自分を守"),
        "state_awareness": ("自分の状態", "状態を見"),
        "relief_or_benefit_in_constraint": ("リラックス", "自分のことを優先", "家のこと", "嬉しい", "良さ"),
        "reality_gap_or_inconvenience": ("現実", "不便", "ダメージ", "気が抜け"),
        "restriction_pressure": ("気をつけ", "圧迫", "無視"),
        "normal_life_wish": ("普通に生活", "生活したい"),
        "worsening_awareness": ("悪化", "分かって", "わかって"),
        "escape_or_limit": ("逃げ出したく", "逃げたい", "弱さではなく"),
        "balanced_self_awareness": ("両方", "同時", "良さ", "苦しさ"),
    }.get(str(role or ""), ())


def _role_key_covered(text: str, role: str) -> bool:
    terms = _role_retention_terms(role)
    return bool(terms and any(term in text for term in terms))


def _evaluate_major_meaning_retention(text: str, meaning_coverage: Mapping[str, Any] | None) -> tuple[bool, bool, bool, bool, bool, bool]:
    if _observation_frame_coverage_ok(text, meaning_coverage):
        return True, True, True, True, True, True
    if not isinstance(meaning_coverage, Mapping) or not bool(meaning_coverage.get("clear_long_input")):
        return True, True, True, True, True, True
    must_keys = meaning_coverage.get("must_keep_block_keys") if isinstance(meaning_coverage.get("must_keep_block_keys"), list) else []
    summaries = _sample_block_summaries(meaning_coverage)
    if not must_keys and not summaries:
        return True, True, True, True, True, True

    role_keys = [str(key or "") for key in must_keys if _role_retention_terms(str(key or ""))]
    if role_keys:
        covered_roles = sum(1 for role in role_keys if _role_key_covered(text, role))
        ratio = covered_roles / max(1, len(role_keys))
        required_ratio = float(meaning_coverage.get("min_must_keep_coverage_ratio") or 0.60)
        ok = ratio >= required_ratio
        return ok, ok, ok, ok, ok, ok

    blocks = _sample_blocks(meaning_coverage)
    covered = sum(1 for block in blocks if _sample_block_covered(text, block)) if blocks else sum(1 for summary in summaries if _summary_covered(text, summary))
    denominator = max(1, len(blocks) if blocks else len(summaries) if summaries else len(must_keys))
    ratio = covered / denominator
    required_ratio = float(meaning_coverage.get("min_must_keep_coverage_ratio") or 0.60)
    ok = ratio >= required_ratio
    # Legacy booleans remain in the schema, but they now represent generic
    # retention health rather than named sample themes.
    return ok, ok, ok, ok, ok, ok


def _first_content_line(text: str) -> str:
    for line in [line.strip() for line in str(text or "").splitlines() if line.strip()]:
        if line == "Emlisです。" or line.endswith("Emlisです。"): 
            continue
        return line
    return ""


def _evaluate_response_composition(text: str, composition: Mapping[str, Any] | None) -> tuple[bool, bool, bool, bool, bool, bool]:
    first_line = _first_content_line(text)
    first_ok = not bool(_MIDSTREAM_OPENING_RE.search(first_line))
    if isinstance(composition, Mapping) and bool(composition.get("observation_frame_present")):
        primary = str(composition.get("observation_primary_state") or "").strip()
        opening_present = (not primary) or (primary in text) or ("状態" in first_line and "見ています" in first_line)
        ok = first_ok and opening_present
        return ok, opening_present, first_ok, first_ok, True, True
    if not isinstance(composition, Mapping) or not composition.get("composition_key"):
        return first_ok, True, first_ok, first_ok, True, True
    opening_required = bool(composition.get("opening_thesis_present"))
    opening_text = str(composition.get("opening_thesis") or "").strip()
    opening_present = (not opening_required) or bool(opening_text and opening_text in text)
    transition_ok = first_ok
    current_grounding_ok = True
    stale_leak_blocked = True
    response_ok = opening_present and first_ok and transition_ok and current_grounding_ok and stale_leak_blocked
    return response_ok, opening_present, first_ok, transition_ok, current_grounding_ok, stale_leak_blocked

def evaluate_emlis_ai_quality_gate(
    *,
    comment_text: Any,
    capability: Any,
    used_sources: Sequence[Any],
    evidence_by_line: Mapping[str, Any] | None,
    fallback_used: bool,
    allowed_line_count: int | None = None,
    sample_user_word_anchors: Sequence[Any] | None = None,
    user_word_anchor_count: int = 0,
    understanding_patterns: Sequence[Any] | None = None,
    final_reader_passed: bool = True,
    pre_return_blocking_enabled: bool = False,
    repair_attempted: bool = False,
    repair_passed: bool = False,
    safe_fallback_used: bool = False,
    blocked_issue_codes: Sequence[str] | None = None,
    meaning_coverage: Mapping[str, Any] | None = None,
    composition: Mapping[str, Any] | None = None,
) -> EmlisAIQualityGateResult:
    tier = str(getattr(capability, "tier", "free") or "free").strip().lower()
    history_mode = str(getattr(capability, "history_mode", "none") or "none").strip().lower()
    max_reply_lines = int(getattr(capability, "max_reply_lines", 3) or 3)
    strict_evidence_mode = bool(getattr(capability, "strict_evidence_mode", True))
    source_scope = str(getattr(capability, "source_scope", "current_input_only") or "current_input_only")

    sources = [str(item or "").strip() for item in (used_sources or []) if str(item or "").strip()]
    history_sources = _used_history_sources(sources)
    cross_core_sources = _used_cross_core_sources(sources)
    current_input_central = "current_input" in set(sources)
    history_allowed = not history_sources or history_mode != "none"
    if tier == "free" and history_sources:
        history_allowed = False
    cross_core_allowed = not cross_core_sources or (tier == "premium" and bool(getattr(capability, "cross_core_enabled", False)))

    evidence_line_count = len(evidence_by_line or {})
    evidence_required_satisfied = True
    if strict_evidence_mode and not fallback_used:
        evidence_required_satisfied = evidence_line_count > 0

    text = str(comment_text or "")
    has_diagnosis_or_overclaim = bool(_DIAGNOSIS_OR_OVERCLAIM_RE.search(text))
    overclaim_suppressed = not has_diagnosis_or_overclaim
    diagnosis_blocked = not has_diagnosis_or_overclaim
    effective_max_reply_lines = int(allowed_line_count or 0) or (max_reply_lines + 1)
    reply_length_within_limit = _line_count(text) <= effective_max_reply_lines

    receive_repetition_ok = text.count("受け取") <= 1
    empty_ack_blocked = not any(_EMPTY_ACK_LINE_RE.search(line.strip()) for line in text.splitlines() if line.strip())
    mechanical_meta_language_ok = not bool(_MECHANICAL_META_LANGUAGE_RE.search(text))
    internal_observation_language_blocked = not bool(_INTERNAL_OBSERVATION_LANGUAGE_RE.search(text))
    second_person_pronoun_blocked = not bool(_SECOND_PERSON_PRONOUN_RE.search(text))
    raw_echo_only_blocked = _raw_echo_only_blocked(text)
    broken_connection_blocked = not bool(_BROKEN_CONNECTION_RE.search(text))
    broken_noun_phrase_blocked = not bool(_BROKEN_NOUN_PHRASE_RE.search(text))
    sentence_ending_variety_ok = _sentence_ending_variety_ok(text)
    presence_line_present = bool(_PRESENCE_RE.search(text))
    abstract_history_reference_blocked = not bool(_ABSTRACT_HISTORY_RE.search(text))
    observation_frame_ok = _observation_frame_coverage_ok(text, meaning_coverage)
    user_word_usage_ok = True if observation_frame_ok else _user_word_usage_ok(text, sample_user_word_anchors or [], int(user_word_anchor_count or 0))
    relationship_line_ok = _relationship_line_ok(text, understanding_patterns or []) or observation_frame_ok
    understanding_language_ok = any(word in text for word in _UNDERSTANDING_WORDS) and not text.strip().endswith("理解しました。")
    (
        meaning_coverage_ok,
        long_input_depth_ok,
        single_focus_overcompression_blocked,
        required_role_coverage_ok,
        clear_long_input_not_underanswered,
        piece_like_summary_blocked,
    ) = _evaluate_meaning_coverage(text, meaning_coverage)
    (
        major_meaning_retention_ok,
        must_keep_coverage_ok,
        own_happiness_wish_not_dropped,
        betrayal_fear_not_dropped,
        concrete_wishes_not_dropped,
        present_effort_not_dropped,
    ) = _evaluate_major_meaning_retention(text, meaning_coverage)
    (
        response_composition_ok,
        opening_thesis_present,
        first_content_line_not_midstream,
        transition_coherence_ok,
        current_input_grounding_ok,
        stale_meaning_block_leak_blocked,
    ) = _evaluate_response_composition(text, composition)

    capability_profile = {
        "tier": tier,
        "history_mode": history_mode,
        "model_mode": str(getattr(capability, "model_mode", "off") or "off"),
        "interpretation_mode": str(getattr(capability, "interpretation_mode", "current_only") or "current_only"),
        "source_scope": source_scope,
        "cross_core_enabled": bool(getattr(capability, "cross_core_enabled", False)),
        "structure_model_enabled": bool(getattr(capability, "structure_model_enabled", False)),
        "cross_core_sources": sorted(cross_core_sources),
        "max_reply_lines": max_reply_lines,
        "effective_max_reply_lines": effective_max_reply_lines,
    }
    presence_required_ok = presence_line_present or not bool(pre_return_blocking_enabled)
    final_reader_required_ok = bool(final_reader_passed) or not bool(pre_return_blocking_enabled)
    passed = all(
        [
            current_input_central,
            history_allowed,
            cross_core_allowed,
            evidence_required_satisfied,
            overclaim_suppressed,
            diagnosis_blocked,
            reply_length_within_limit,
            understanding_language_ok,
            receive_repetition_ok,
            user_word_usage_ok,
            relationship_line_ok,
            empty_ack_blocked,
            mechanical_meta_language_ok,
            raw_echo_only_blocked,
            broken_connection_blocked,
            sentence_ending_variety_ok,
            presence_required_ok,
            abstract_history_reference_blocked,
            final_reader_required_ok,
            meaning_coverage_ok,
            long_input_depth_ok,
            single_focus_overcompression_blocked,
            required_role_coverage_ok,
            clear_long_input_not_underanswered,
            piece_like_summary_blocked,
            major_meaning_retention_ok,
            must_keep_coverage_ok,
            own_happiness_wish_not_dropped,
            betrayal_fear_not_dropped,
            concrete_wishes_not_dropped,
            present_effort_not_dropped,
            broken_noun_phrase_blocked,
            response_composition_ok,
            opening_thesis_present,
            first_content_line_not_midstream,
            transition_coherence_ok,
            current_input_grounding_ok,
            stale_meaning_block_leak_blocked,
            internal_observation_language_blocked,
            second_person_pronoun_blocked,
        ]
    )
    return EmlisAIQualityGateResult(
        passed=passed,
        current_input_central=current_input_central,
        history_allowed=history_allowed,
        cross_core_allowed=cross_core_allowed,
        evidence_required_satisfied=evidence_required_satisfied,
        overclaim_suppressed=overclaim_suppressed,
        diagnosis_blocked=diagnosis_blocked,
        reply_length_within_limit=reply_length_within_limit,
        capability_profile=capability_profile,
        understanding_language_ok=understanding_language_ok,
        receive_repetition_ok=receive_repetition_ok,
        user_word_usage_ok=user_word_usage_ok,
        relationship_line_ok=relationship_line_ok,
        empty_ack_blocked=empty_ack_blocked,
        mechanical_meta_language_ok=mechanical_meta_language_ok,
        raw_echo_only_blocked=raw_echo_only_blocked,
        broken_connection_blocked=broken_connection_blocked,
        sentence_ending_variety_ok=sentence_ending_variety_ok,
        presence_line_present=presence_line_present,
        abstract_history_reference_blocked=abstract_history_reference_blocked,
        final_reader_passed=bool(final_reader_passed),
        pre_return_blocking_enabled=bool(pre_return_blocking_enabled),
        preflight_passed=passed,
        repair_attempted=bool(repair_attempted),
        repair_passed=bool(repair_passed),
        safe_fallback_used=bool(safe_fallback_used),
        blocked_issue_codes=tuple(str(code or "") for code in (blocked_issue_codes or []) if str(code or "")),
        meaning_coverage_ok=meaning_coverage_ok,
        long_input_depth_ok=long_input_depth_ok,
        single_focus_overcompression_blocked=single_focus_overcompression_blocked,
        required_role_coverage_ok=required_role_coverage_ok,
        clear_long_input_not_underanswered=clear_long_input_not_underanswered,
        piece_like_summary_blocked=piece_like_summary_blocked,
        major_meaning_retention_ok=major_meaning_retention_ok,
        must_keep_coverage_ok=must_keep_coverage_ok,
        own_happiness_wish_not_dropped=own_happiness_wish_not_dropped,
        betrayal_fear_not_dropped=betrayal_fear_not_dropped,
        concrete_wishes_not_dropped=concrete_wishes_not_dropped,
        present_effort_not_dropped=present_effort_not_dropped,
        broken_noun_phrase_blocked=broken_noun_phrase_blocked,
        response_composition_ok=response_composition_ok,
        opening_thesis_present=opening_thesis_present,
        first_content_line_not_midstream=first_content_line_not_midstream,
        transition_coherence_ok=transition_coherence_ok,
        current_input_grounding_ok=current_input_grounding_ok,
        stale_meaning_block_leak_blocked=stale_meaning_block_leak_blocked,
        internal_observation_language_blocked=internal_observation_language_blocked,
        second_person_pronoun_blocked=second_person_pronoun_blocked,
    )


def attach_emlis_ai_quality_gate_meta(
    meta: Mapping[str, Any],
    *,
    comment_text: Any,
    capability: Any,
    fallback_used: bool,
) -> Dict[str, Any]:
    updated = dict(meta or {})
    used_sources = updated.get("used_sources") if isinstance(updated.get("used_sources"), list) else []
    evidence_by_line = updated.get("evidence_by_line") if isinstance(updated.get("evidence_by_line"), dict) else {}
    reply_depth = updated.get("reply_depth") if isinstance(updated.get("reply_depth"), dict) else {}
    anchor_summary = updated.get("anchor_summary") if isinstance(updated.get("anchor_summary"), dict) else {}
    understanding = updated.get("understanding") if isinstance(updated.get("understanding"), dict) else {}
    meaning_coverage = updated.get("meaning_coverage") if isinstance(updated.get("meaning_coverage"), dict) else {}
    composition = updated.get("composition") if isinstance(updated.get("composition"), dict) else {}
    allowed_line_count = int(reply_depth.get("tier_ceiling") or getattr(capability, "max_reply_lines", 3) or 3) + 1
    final_reader_meta = updated.get("final_reader") if isinstance(updated.get("final_reader"), dict) else {}
    pre_return_meta = updated.get("pre_return") if isinstance(updated.get("pre_return"), dict) else {}
    gate = evaluate_emlis_ai_quality_gate(
        comment_text=comment_text,
        capability=capability,
        used_sources=used_sources,
        evidence_by_line=evidence_by_line,
        fallback_used=fallback_used,
        allowed_line_count=allowed_line_count,
        sample_user_word_anchors=anchor_summary.get("sample_user_word_anchors") if isinstance(anchor_summary.get("sample_user_word_anchors"), list) else [],
        user_word_anchor_count=int(anchor_summary.get("user_word_anchor_count") or 0),
        understanding_patterns=understanding.get("patterns") if isinstance(understanding.get("patterns"), list) else [],
        final_reader_passed=bool(final_reader_meta.get("passed", True)),
        pre_return_blocking_enabled=bool(pre_return_meta.get("pre_return_blocking_enabled", True)),
        repair_attempted=bool(pre_return_meta.get("repair_attempted", False)),
        repair_passed=bool(pre_return_meta.get("repair_passed", False)),
        safe_fallback_used=bool(pre_return_meta.get("safe_fallback_used", fallback_used)),
        blocked_issue_codes=pre_return_meta.get("blocked_issue_codes") if isinstance(pre_return_meta.get("blocked_issue_codes"), list) else [],
        meaning_coverage=meaning_coverage,
        composition=composition,
    )
    capability_meta = dict(updated.get("capability") or {}) if isinstance(updated.get("capability"), dict) else {}
    capability_meta.update(gate.capability_profile)
    updated["capability"] = capability_meta

    reply_text = str(comment_text or "")
    strength_display_suppressed = not bool(_EMOTION_STRENGTH_DISPLAY_RE.search(reply_text))
    natural_language_ok = not bool(_UNNATURAL_REPLY_RE.search(reply_text) or _BROKEN_CONNECTION_RE.search(reply_text) or _BROKEN_NOUN_PHRASE_RE.search(reply_text))
    quality_meta = gate.as_meta()
    quality_meta["strength_display_suppressed"] = strength_display_suppressed
    quality_meta["natural_language_ok"] = natural_language_ok
    quality_meta["passed"] = bool(quality_meta.get("passed") and strength_display_suppressed and natural_language_ok)
    updated["quality_gate"] = quality_meta
    return updated


__all__ = [
    "EMLIS_AI_QUALITY_GATE_SCHEMA_VERSION",
    "EmlisAIQualityGateResult",
    "attach_emlis_ai_quality_gate_meta",
    "evaluate_emlis_ai_quality_gate",
]
