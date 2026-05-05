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
    r"|中途半端だ気持ち|中途半端だから気持ち|好きになれないけど気持ち"
    r"|諦めたくないけれど気持ち|期待して裏切られたくないから気持ち"
)
_ABSTRACT_HISTORY_RE = re.compile(r"(最近の履歴の中でも、近いテーマ|最近の流れも踏まえて|今の気持ちを見ます|近いテーマがまた顔を出して)")
_PRESENCE_RE = re.compile(r"(軽く扱いません|雑に扱いません|小さく扱いません|そのまま置いて大丈夫|きれいにしなくて大丈夫|そばに置いて|大切にします|大切に扱います)")
_MECHANICAL_META_LANGUAGE_RE = re.compile(r"(認識しています|入力として|構造として|分析すると|理解しました|受け取りました|受理しました)")
_EMPTY_ACK_LINE_RE = re.compile(r"^(?:今回は、?)?(?:書いてくれた)?(?:内容|入力|言葉|気持ち|感情).{0,18}受け取(?:り|る|ります|りました|っています).{0,4}$")
_RELATION_WORDS = ("一方で", "だけでなく", "からこそ", "重なって", "つながって", "その自分ごと", "切り離さず", "気づいていて")
_UNDERSTANDING_WORDS = ("のですね", "だったのですね", "苦しかった", "重なって", "気づいていて", "見ていた", "見ます", "軽く扱いません", "大切にします")


@dataclass(frozen=True)
class EmlisAIQualityGateResult:
    passed: bool
    current_input_central: bool
    history_allowed: bool
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

    def as_meta(self) -> Dict[str, Any]:
        return {
            "schema_version": EMLIS_AI_QUALITY_GATE_SCHEMA_VERSION,
            "passed": bool(self.passed),
            "current_input_central": bool(self.current_input_central),
            "history_allowed": bool(self.history_allowed),
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
            "capability_profile": dict(self.capability_profile or {}),
        }


def _line_count(text: Any) -> int:
    value = str(text or "").strip()
    if not value:
        return 0
    explicit_lines = [line for line in value.splitlines() if line.strip()]
    if len(explicit_lines) > 1:
        return len(explicit_lines)
    return max(1, len([chunk for chunk in re.split(r"[。！？!?]+", value) if chunk.strip()]))


def _used_history_sources(used_sources: Sequence[Any]) -> set[str]:
    return {str(item or "").strip() for item in (used_sources or []) if str(item or "").strip()} & _HISTORY_SOURCE_KEYS


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
        for marker in (
            "パーソナルスペース",
            "怒ると知っていながら",
            "自分の非",
            "見たくない",
            "嫌われ",
            "悲しくて不安",
            "連絡の頻度",
            "わかり合え",
            "泣きそう",
            "悔しい",
            "もったいない",
            "むかつく",
            "イライラ",
            "教えて",
            "どう頑張ればいい",
            "チャット",
            "癒",
            "体も心",
            "ボロボロ",
            "ここまで頑張",
            "無理してきた",
            "もう少し頑張りたい",
            "投げ出したい",
            "終わりにしたくない",
            "しんどい",
            "体が重",
            "気持ちがついてこ",
            "崩れ",
            "どっちも",
            "両方",
            "立ち止",
            "整え",
            "弱いわけ",
            "限界",
            "誰かの役に立",
            "中途半端",
            "好きになれない",
            "諦めたくない",
            "諦めて",
            "裏切られたくない",
            "幸せになりたい",
            "好きなこと",
            "パートナー",
            "手の届",
            "今頑張れる",
        ):
            if marker in text and marker not in terms:
                terms.append(marker)
        if len(text) <= 18 and text not in terms:
            terms.append(text)
    return terms


def _user_word_usage_ok(text: str, sample_user_word_anchors: Sequence[Any], user_word_anchor_count: int) -> bool:
    if int(user_word_anchor_count or 0) < 2:
        return True
    compact_text = _compact(text)
    terms = _anchor_terms(sample_user_word_anchors)
    if not terms:
        return True
    used = sum(1 for term in terms if _compact(term) and _compact(term) in compact_text)
    required = 2 if int(user_word_anchor_count or 0) >= 3 else 1
    return used >= required


def _relationship_line_ok(text: str, patterns: Sequence[Any]) -> bool:
    pattern_set = {str(item or "") for item in (patterns or [])}
    if not (pattern_set & {"justification_vs_fault", "rejection_fear_from_self_view", "emotion_from_conflict", "action_and_awareness"}):
        return True
    return any(word in text for word in _RELATION_WORDS)


def _raw_echo_only_blocked(text: str) -> bool:
    for line in [line.strip() for line in str(text or "").splitlines() if line.strip()]:
        if "受け取" in line and re.fullmatch(r"「[^」]{1,60}」(?:と書いてくれた)?(?:こと|ところ)?を?.{0,14}受け取(?:ります|りました|りたいです)。?", line):
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
    for a, b, c in zip(groups, groups[1:], groups[2:]):
        if a == b == c and a != "other":
            return False
    return True


_LONG_ROLE_TERMS = {
    "state_awareness": ("体も心", "ボロボロ", "自分でもちゃんと分か"),
    "effort_history": ("ここまで頑張", "無理してきた時間", "積み重"),
    "continuation_wish": ("もう少し頑張りたい", "投げ出したいわけ", "終わりにしたくない"),
    "not_want_to_quit": ("投げ出したいわけ", "終わりにしたくない"),
    "fatigue_or_limit": ("体が重", "気持ちがついてこ", "しんど"),
    "collapse_anxiety": ("崩れてしまいそう", "崩れそう", "不安"),
    "dual_holding": ("両方", "どちらか", "頑張りたい気持ちもしんどい気持ち"),
    "paced_progress": ("頑張れる日は", "しんどい日は", "立ち止ま", "整え"),
    "self_understanding": ("弱いのではなく", "弱いわけ", "限界に気づ"),
    "other_contribution": ("誰かの役に立", "役に立て", "幸せに笑"),
    "self_dislike_from_halfway": ("中途半端", "好きになれない"),
    "others_happiness_as_own_happiness": ("幸せに笑", "自分の幸せに近"),
    "future_not_giving_up": ("諦めたくない", "今後"),
    "resignation_self": ("諦めている自分", "諦めてる自分"),
    "betrayal_fear": ("裏切られたくない", "裏切られるのが怖", "期待"),
    "own_happiness_wish": ("私も幸せになりたい", "自分も幸せになりたい", "幸せになりたい"),
    "existing_happiness_and_more": ("既に幸せ", "それ以上"),
    "concrete_life_wishes": ("好きなこと", "納得いくまで", "パートナー"),
    "unreachable_wish": ("手の届かない", "手の届"),
    "present_effort_toward_wish": ("今頑張れる", "願いに届", "大切にしたい"),
}


def _long_input_role_hits(text: str, required_roles: Sequence[Any]) -> set[str]:
    compact_text = _compact(text)
    hits: set[str] = set()
    for role in [str(item or "") for item in required_roles or [] if str(item or "")]:
        terms = _LONG_ROLE_TERMS.get(role, ())
        if any(_compact(term) in compact_text for term in terms):
            hits.add(role)
    return hits


def _evaluate_meaning_coverage(text: str, meaning_coverage: Mapping[str, Any] | None) -> tuple[bool, bool, bool, bool, bool, bool]:
    if not isinstance(meaning_coverage, Mapping) or not bool(meaning_coverage.get("clear_long_input")):
        return True, True, True, True, True, True
    required_roles = meaning_coverage.get("required_roles") if isinstance(meaning_coverage.get("required_roles"), list) else []
    selected_block_count = int(meaning_coverage.get("selected_block_count") or len(meaning_coverage.get("selected_block_keys") or []) or 0)
    min_blocks = int(meaning_coverage.get("min_blocks_to_cover") or 0)
    line_count = _line_count(text)
    hits = _long_input_role_hits(text, required_roles)
    required_hits = min(max(4, min_blocks), max(1, len(required_roles))) if required_roles else 0
    required_role_coverage_ok = True if not required_roles else len(hits) >= required_hits
    long_input_depth_ok = line_count >= max(5, min_blocks + 1)
    single_focus_overcompression_blocked = not (line_count <= 4 and selected_block_count >= 5)
    clear_long_input_not_underanswered = required_role_coverage_ok and long_input_depth_ok and single_focus_overcompression_blocked
    piece_like_summary_blocked = not (line_count <= 3 and any(token in text for token in ("問い", "答え", "伸ばしたいのは")))
    meaning_coverage_ok = required_role_coverage_ok and clear_long_input_not_underanswered and piece_like_summary_blocked
    return (
        meaning_coverage_ok,
        long_input_depth_ok,
        single_focus_overcompression_blocked,
        required_role_coverage_ok,
        clear_long_input_not_underanswered,
        piece_like_summary_blocked,
    )


def _evaluate_major_meaning_retention(text: str, meaning_coverage: Mapping[str, Any] | None) -> tuple[bool, bool, bool, bool, bool, bool]:
    if not isinstance(meaning_coverage, Mapping) or not bool(meaning_coverage.get("clear_long_input")):
        return True, True, True, True, True, True
    must_keys = meaning_coverage.get("must_keep_block_keys") if isinstance(meaning_coverage.get("must_keep_block_keys"), list) else []
    if not must_keys:
        return True, True, True, True, True, True
    hits = _long_input_role_hits(text, must_keys)
    required_ratio = float(meaning_coverage.get("min_must_keep_coverage_ratio") or 0.80)
    coverage_ratio = (len(hits) / len(must_keys)) if must_keys else 1.0
    must_keep_coverage_ok = coverage_ratio >= required_ratio
    compact_text = _compact(text)
    own_ok = "own_happiness_wish" not in must_keys or any(_compact(t) in compact_text for t in _LONG_ROLE_TERMS["own_happiness_wish"])
    betrayal_ok = "betrayal_fear" not in must_keys or any(_compact(t) in compact_text for t in _LONG_ROLE_TERMS["betrayal_fear"])
    concrete_ok = "concrete_life_wishes" not in must_keys or sum(1 for t in _LONG_ROLE_TERMS["concrete_life_wishes"] if _compact(t) in compact_text) >= 2
    present_ok = "present_effort_toward_wish" not in must_keys or any(_compact(t) in compact_text for t in _LONG_ROLE_TERMS["present_effort_toward_wish"])
    major_ok = must_keep_coverage_ok and own_ok and betrayal_ok and concrete_ok and present_ok
    return major_ok, must_keep_coverage_ok, own_ok, betrayal_ok, concrete_ok, present_ok


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
) -> EmlisAIQualityGateResult:
    tier = str(getattr(capability, "tier", "free") or "free").strip().lower()
    history_mode = str(getattr(capability, "history_mode", "none") or "none").strip().lower()
    max_reply_lines = int(getattr(capability, "max_reply_lines", 3) or 3)
    strict_evidence_mode = bool(getattr(capability, "strict_evidence_mode", True))
    source_scope = str(getattr(capability, "source_scope", "current_input_only") or "current_input_only")

    sources = [str(item or "").strip() for item in (used_sources or []) if str(item or "").strip()]
    history_sources = _used_history_sources(sources)
    current_input_central = "current_input" in set(sources)
    history_allowed = not history_sources or history_mode != "none"
    if tier == "free" and history_sources:
        history_allowed = False

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
    raw_echo_only_blocked = _raw_echo_only_blocked(text)
    broken_connection_blocked = not bool(_BROKEN_CONNECTION_RE.search(text))
    broken_noun_phrase_blocked = not bool(_BROKEN_NOUN_PHRASE_RE.search(text))
    sentence_ending_variety_ok = _sentence_ending_variety_ok(text)
    presence_line_present = bool(_PRESENCE_RE.search(text))
    abstract_history_reference_blocked = not bool(_ABSTRACT_HISTORY_RE.search(text))
    user_word_usage_ok = _user_word_usage_ok(text, sample_user_word_anchors or [], int(user_word_anchor_count or 0))
    relationship_line_ok = _relationship_line_ok(text, understanding_patterns or [])
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

    capability_profile = {
        "tier": tier,
        "history_mode": history_mode,
        "model_mode": str(getattr(capability, "model_mode", "off") or "off"),
        "interpretation_mode": str(getattr(capability, "interpretation_mode", "current_only") or "current_only"),
        "source_scope": source_scope,
        "cross_core_enabled": bool(getattr(capability, "cross_core_enabled", False)),
        "structure_model_enabled": bool(getattr(capability, "structure_model_enabled", False)),
        "max_reply_lines": max_reply_lines,
        "effective_max_reply_lines": effective_max_reply_lines,
    }
    presence_required_ok = presence_line_present or not bool(pre_return_blocking_enabled)
    final_reader_required_ok = bool(final_reader_passed) or not bool(pre_return_blocking_enabled)
    passed = all(
        [
            current_input_central,
            history_allowed,
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
        ]
    )
    return EmlisAIQualityGateResult(
        passed=passed,
        current_input_central=current_input_central,
        history_allowed=history_allowed,
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
