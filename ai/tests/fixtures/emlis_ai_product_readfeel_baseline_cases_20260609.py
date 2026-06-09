# -*- coding: utf-8 -*-
from __future__ import annotations

"""P3-1 baseline case matrix for EmlisAI Product Read Feel.

The cases in this module are synthetic local-QA inputs.  They intentionally keep
``current_input.memo`` so the next implementation step can render the current
Emlis output and let reviewers judge read feeling.  They are not public meta,
not scorecard events, and not runtime conditions.

Use ``build_product_readfeel_baseline_public_safe_index_20260609`` when a
body-free, commit/release-safe index is needed.  P3-1 stops at the input matrix;
current-output capture and sanitized output events belong to P3-2/P3-3.
"""

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from copy import deepcopy
import json
import re
from typing import Any, Final

from emlis_ai_product_readfeel_current_output_inventory import (
    FAMILY_DAILY_POSITIVE,
    FAMILY_DAILY_UNPLEASANT,
    FAMILY_INPUT_SELF_REPORT_ONLY_FAILURE,
    FAMILY_LONG_MEANING_ARC,
    FAMILY_LOW_INFORMATION_SHORT,
    FAMILY_MIXED_EMOTION,
    FAMILY_POSITIVE_ONLY,
    FAMILY_RELATIONSHIP_BOUNDARY,
    FAMILY_SELF_DENIAL,
    FAMILY_SELF_UNDERSTANDING_FOLLOW,
    FAMILY_STRUCTURE_QUESTION,
    FAMILY_UNCERTAINTY,
    PRODUCT_READFEEL_REQUIRED_FAMILIES,
)

PRODUCT_READFEEL_BASELINE_CASE_VERSION_20260609: Final = (
    "cocolon.emlis.product_readfeel.baseline_case.v1"
)
PRODUCT_READFEEL_BASELINE_CASE_MATRIX_VERSION_20260609: Final = (
    "cocolon.emlis.product_readfeel.baseline_case_matrix.20260609.v1"
)
PRODUCT_READFEEL_BASELINE_PUBLIC_SAFE_INDEX_VERSION_20260609: Final = (
    "cocolon.emlis.product_readfeel.baseline_public_safe_index.20260609.v1"
)
PRODUCT_READFEEL_BASELINE_CASE_STEP_20260609: Final = "P3-1_Baseline_Case_Matrix"
PRODUCT_READFEEL_BASELINE_CASE_SOURCE_20260609: Final = (
    "Cocolon_EmlisAI_P3_ProductReadFeel_BaselineCases_20260609"
)

SLICE_LIMITED_GROUNDING: Final = "limited_grounding"
SLICE_SOURCE_UNAVAILABLE_HIGH_INFORMATION: Final = "source_unavailable_high_information"
SLICE_HISTORY_LINE_ELIGIBLE: Final = "history_line_eligible"
SLICE_ANGER_OR_BOUNDARY: Final = "anger_or_boundary"
SLICE_STANDARD_STATE_ANSWER: Final = "standard_state_answer"
SLICE_RENDER_DEFAULT_PATH: Final = "render_default_path"
SLICE_COMPLETE_INITIAL_PATH: Final = "complete_initial_path"
SLICE_FREE_TIER: Final = "free_tier"
SLICE_PLUS_TIER: Final = "plus_tier"
SLICE_PREMIUM_TIER: Final = "premium_tier"

PATH_RENDER_DEFAULT: Final = "render_default_path"
PATH_COMPLETE_INITIAL: Final = "complete_initial_path"
PATH_SOURCE_UNAVAILABLE: Final = "source_unavailable_path"
PATH_HISTORY_LINE_CANDIDATE: Final = "history_line_candidate_path"

TIER_FREE: Final = "free"
TIER_PLUS: Final = "plus"
TIER_PREMIUM: Final = "premium"

PRODUCT_READFEEL_BASELINE_REQUIRED_FAMILIES_20260609: Final[tuple[str, ...]] = tuple(
    PRODUCT_READFEEL_REQUIRED_FAMILIES
)
PRODUCT_READFEEL_BASELINE_CASES_PER_FAMILY_20260609: Final = 5
PRODUCT_READFEEL_BASELINE_EXPECTED_CASE_COUNT_20260609: Final = (
    len(PRODUCT_READFEEL_BASELINE_REQUIRED_FAMILIES_20260609)
    * PRODUCT_READFEEL_BASELINE_CASES_PER_FAMILY_20260609
)

VALID_COVERAGE_SLICES_20260609: Final[frozenset[str]] = frozenset(
    {
        SLICE_LIMITED_GROUNDING,
        SLICE_SOURCE_UNAVAILABLE_HIGH_INFORMATION,
        SLICE_HISTORY_LINE_ELIGIBLE,
        SLICE_ANGER_OR_BOUNDARY,
        SLICE_STANDARD_STATE_ANSWER,
        SLICE_RENDER_DEFAULT_PATH,
        SLICE_COMPLETE_INITIAL_PATH,
        SLICE_FREE_TIER,
        SLICE_PLUS_TIER,
        SLICE_PREMIUM_TIER,
    }
)
VALID_PATH_TARGETS_20260609: Final[frozenset[str]] = frozenset(
    {
        PATH_RENDER_DEFAULT,
        PATH_COMPLETE_INITIAL,
        PATH_SOURCE_UNAVAILABLE,
        PATH_HISTORY_LINE_CANDIDATE,
    }
)
VALID_SUBSCRIPTION_TIERS_20260609: Final[frozenset[str]] = frozenset(
    {TIER_FREE, TIER_PLUS, TIER_PREMIUM}
)
REQUIRED_COVERAGE_MINIMUMS_20260609: Final[dict[str, int]] = {
    SLICE_LIMITED_GROUNDING: 5,
    SLICE_SOURCE_UNAVAILABLE_HIGH_INFORMATION: 3,
    SLICE_HISTORY_LINE_ELIGIBLE: 5,
    SLICE_ANGER_OR_BOUNDARY: 5,
    SLICE_STANDARD_STATE_ANSWER: 5,
}

_CASE_ID_RE: Final = re.compile(r"^p3-[a-z0-9_]+-[0-9]{3}$")
_TIER_TO_SLICE: Final[dict[str, str]] = {
    TIER_FREE: SLICE_FREE_TIER,
    TIER_PLUS: SLICE_PLUS_TIER,
    TIER_PREMIUM: SLICE_PREMIUM_TIER,
}
_PATH_TO_SLICE: Final[dict[str, str]] = {
    PATH_RENDER_DEFAULT: SLICE_RENDER_DEFAULT_PATH,
    PATH_COMPLETE_INITIAL: SLICE_COMPLETE_INITIAL_PATH,
}

_LOCAL_CASE_FORBIDDEN_OUTPUT_KEYS: Final[frozenset[str]] = frozenset(
    {
        "comment_text",
        "commentText",
        "comment_text_body",
        "commentTextBody",
        "candidate_body",
        "candidateBody",
        "reply_text",
        "replyText",
        "surface_text",
        "surfaceText",
        "display_text",
        "displayText",
        "expected_comment_text",
        "public_comment_text",
        "accepted_surface_probe",
        "blocked_surface_probe",
    }
)
_PUBLIC_SAFE_FORBIDDEN_TEXT_KEYS: Final[frozenset[str]] = frozenset(
    {
        "raw_input",
        "rawInput",
        "raw_text",
        "rawText",
        "input",
        "input_text",
        "inputText",
        "user_input",
        "userInput",
        "current_input",
        "currentInput",
        "memo",
        "memo_text",
        "memoText",
        "memo_action",
        "memoAction",
        "comment_text",
        "commentText",
        "comment_text_body",
        "commentTextBody",
        "candidate_body",
        "candidateBody",
        "reply_text",
        "replyText",
        "surface_text",
        "surfaceText",
        "display_text",
        "displayText",
        "body",
        "text",
    }
)
_FORBIDDEN_TRUE_FLAGS_20260609: Final[frozenset[str]] = frozenset(
    {
        "exact_comment_text_required",
        "exact_comment_text_locked",
        "case_specific_runtime_branch",
        "case_specific_runtime_branch_allowed",
        "case_specific_runtime_condition_allowed",
        "runtime_branching_uses_fixture_strings",
        "fixture_text_used_for_runtime_branching",
        "gate_relaxation_allowed",
        "gate_relaxed",
        "display_gate_relaxed",
        "grounding_gate_relaxed",
        "reader_gate_relaxed",
        "template_gate_relaxed",
        "public_meta_body_allowed",
        "public_response_key_change",
        "public_response_key_added",
        "response_shape_changed",
        "rn_visible_contract_changed",
        "api_route_changed",
        "db_physical_name_changed",
        "product_gate_ready",
        "public_release_applied",
        "comment_text_body_included",
        "candidate_body_included",
        "raw_input_included",
        "raw_text_included",
    }
)


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    if values is None:
        return []
    raw_values: Iterable[Any]
    if isinstance(values, (str, bytes, bytearray)):
        raw_values = [values]
    else:
        raw_values = values if isinstance(values, Iterable) else [values]
    out: list[str] = []
    seen: set[str] = set()
    for value in raw_values:
        text = str(value).strip()
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _contains_forbidden_key(value: Any, forbidden_keys: frozenset[str]) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in forbidden_keys:
                return True
            if _contains_forbidden_key(child, forbidden_keys):
                return True
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_forbidden_key(child, forbidden_keys) for child in value)
    return False


def _forbidden_true_flag_path(value: Any, *, path: str = "payload") -> str | None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if str(key) in _FORBIDDEN_TRUE_FLAGS_20260609 and child is True:
                return child_path
            nested = _forbidden_true_flag_path(child, path=child_path)
            if nested:
                return nested
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for idx, child in enumerate(value):
            nested = _forbidden_true_flag_path(child, path=f"{path}[{idx}]")
            if nested:
                return nested
    return None


def _slice_for_tier(tier: str) -> str:
    return _TIER_TO_SLICE.get(tier, "")


def _history_context(enabled: bool) -> dict[str, Any]:
    if not enabled:
        return {
            "enabled": False,
            "owned_record_count": 0,
            "evidence_record_count": 0,
            "current_record_included": True,
            "history_records": [],
        }
    return {
        "enabled": True,
        "owned_record_count": 3,
        "evidence_record_count": 2,
        "current_record_included": True,
        "history_records": [
            {
                "record_id": "synthetic-history-01",
                "created_at": "2026-05-20T20:00:00+09:00",
                "emotion_labels": ["不安", "迷い"],
                "category_labels": ["仕事", "自己理解"],
                "raw_text_included": False,
            },
            {
                "record_id": "synthetic-history-02",
                "created_at": "2026-05-29T20:00:00+09:00",
                "emotion_labels": ["重さ", "願い"],
                "category_labels": ["関係", "行動前"],
                "raw_text_included": False,
            },
        ],
    }


def _case(
    *,
    family: str,
    index: int,
    memo: str,
    memo_action: str,
    emotions: Sequence[str],
    category: Sequence[str],
    coverage_slices: Sequence[str] = (),
    subscription_tier: str = TIER_FREE,
    path_targets: Sequence[str] = (PATH_RENDER_DEFAULT,),
    retain_slots: Sequence[str] = (),
    must_not_surface_classes: Sequence[str] = (),
    family_temperature_note: str = "",
) -> dict[str, Any]:
    path_values = _dedupe(path_targets)
    slice_values = _dedupe(
        [
            *coverage_slices,
            _slice_for_tier(subscription_tier),
            *(_PATH_TO_SLICE[path] for path in path_values if path in _PATH_TO_SLICE),
        ]
    )
    case_id = f"p3-{family}-{index:03d}"
    history_enabled = SLICE_HISTORY_LINE_ELIGIBLE in slice_values or PATH_HISTORY_LINE_CANDIDATE in path_values
    item = {
        "schema_version": PRODUCT_READFEEL_BASELINE_CASE_VERSION_20260609,
        "version": PRODUCT_READFEEL_BASELINE_CASE_VERSION_20260609,
        "source": PRODUCT_READFEEL_BASELINE_CASE_SOURCE_20260609,
        "source_step": PRODUCT_READFEEL_BASELINE_CASE_STEP_20260609,
        "case_id": case_id,
        "family": family,
        "product_readfeel_family": family,
        "coverage_slices": slice_values,
        "subscription_tier": subscription_tier,
        "path_targets": path_values,
        "current_input": {
            "id": case_id,
            "created_at": f"2026-06-09T09:{index:02d}:00+09:00",
            "memo": memo,
            "memo_action": memo_action,
            "emotions": list(emotions),
            "category": list(category),
            "is_secret": False,
            "synthetic_case_material": True,
        },
        "history_context": _history_context(history_enabled),
        "expected_contract": {
            "display_expected": True,
            "rn_visible_expected": True,
            "product_surface_validation_required": True,
            "must_retain_slots": list(retain_slots),
            "must_not_surface_classes": list(must_not_surface_classes),
            "family_temperature_note": family_temperature_note,
        },
        "evaluation_controls": {
            "exact_comment_text_required": False,
            "case_specific_runtime_branch_allowed": False,
            "gate_relaxation_allowed": False,
            "public_meta_body_allowed": False,
        },
        "local_qa_only": True,
        "synthetic_case_material": True,
        "runtime_branching_uses_fixture_strings": False,
        "fixture_text_used_for_runtime_branching": False,
        "output_capture_completed": False,
        "sanitized_current_output_event_created": False,
        "product_gate_ready": False,
        "public_release_applied": False,
    }
    return item


_CASE_SPECS: Final[tuple[dict[str, Any], ...]] = (
    # low_information_short
    _case(
        family=FAMILY_LOW_INFORMATION_SHORT,
        index=1,
        memo="疲れた",
        memo_action="今は詳しく書けない",
        emotions=["疲れ"],
        category=["日常"],
        retain_slots=["visible_emotion", "low_information_boundary"],
        must_not_surface_classes=["deep_inference", "history_overread", "generic_advice"],
        family_temperature_note="一語に深読みを足さず、見えている疲れだけを受け取る",
    ),
    _case(
        family=FAMILY_LOW_INFORMATION_SHORT,
        index=2,
        memo="なんか無理",
        memo_action="少しだけ置いておきたい",
        emotions=["重い", "嫌"],
        category=["日常"],
        retain_slots=["visible_refusal", "unspecified_weight"],
        must_not_surface_classes=["cause_claim_without_evidence", "action_instruction"],
        family_temperature_note="理由を決めず、無理さの存在だけを扱う",
    ),
    _case(
        family=FAMILY_LOW_INFORMATION_SHORT,
        index=3,
        memo="ちょっとよかった",
        memo_action="覚えておきたい",
        emotions=["安心"],
        category=["日常", "小さな変化"],
        retain_slots=["small_positive_temperature"],
        must_not_surface_classes=["over_analysis", "future_prediction"],
        family_temperature_note="短いポジティブを冷まさず、重くしない",
    ),
    _case(
        family=FAMILY_LOW_INFORMATION_SHORT,
        index=4,
        memo="もやもやする",
        memo_action="まだ言葉にできない",
        emotions=["もやもや"],
        category=["未整理"],
        subscription_tier=TIER_PLUS,
        retain_slots=["unresolved_feeling"],
        must_not_surface_classes=["period_trend_claim", "history_overread"],
        family_temperature_note="未整理を未整理のまま受け取る",
    ),
    _case(
        family=FAMILY_LOW_INFORMATION_SHORT,
        index=5,
        memo="今日はもう閉じたい",
        memo_action="無理に考えたくない",
        emotions=["疲労", "停止"],
        category=["休息"],
        subscription_tier=TIER_PREMIUM,
        retain_slots=["stop_wish", "low_information_boundary"],
        must_not_surface_classes=["forced_prompt", "deep_inference"],
        family_temperature_note="入力継続を強制せず、閉じたい反応を尊重する",
    ),
    # daily_unpleasant
    _case(
        family=FAMILY_DAILY_UNPLEASANT,
        index=1,
        memo="会議で軽く流された感じが残って、帰ってからもずっと引っかかっている",
        memo_action="距離を少し考えたい",
        emotions=["不快", "怒り"],
        category=["仕事", "関係"],
        coverage_slices=[SLICE_ANGER_OR_BOUNDARY],
        retain_slots=["event", "emotion_direction", "boundary_or_distance"],
        must_not_surface_classes=["target_judgement_agreement", "other_person_intent_claim"],
        family_temperature_note="怒りや不快を消さず、相手断定にしない",
    ),
    _case(
        family=FAMILY_DAILY_UNPLEASANT,
        index=2,
        memo="頼まれごとを断れなくて、いい顔をしたあとに自分だけ疲れている",
        memo_action="次は少し止まりたい",
        emotions=["疲れ", "悔しさ"],
        category=["日常", "境界"],
        coverage_slices=[SLICE_ANGER_OR_BOUNDARY],
        retain_slots=["swallowing", "after_reaction", "boundary_wish"],
        must_not_surface_classes=["self_blame_amplification", "generic_advice"],
        family_temperature_note="飲み込みと疲れをユーザー側の反応として扱う",
    ),
    _case(
        family=FAMILY_DAILY_UNPLEASANT,
        index=3,
        memo="小さな言い方が刺さって、気にしすぎなのかもしれないと思いながらまだ嫌だ",
        memo_action="嫌だったことは消したくない",
        emotions=["嫌", "迷い"],
        category=["関係", "日常"],
        coverage_slices=[SLICE_ANGER_OR_BOUNDARY, SLICE_STANDARD_STATE_ANSWER],
        subscription_tier=TIER_PLUS,
        path_targets=[PATH_RENDER_DEFAULT, PATH_COMPLETE_INITIAL],
        retain_slots=["hurt_reaction", "self_doubt", "discomfort_retention"],
        must_not_surface_classes=["target_intent_claim", "feeling_dismissal"],
        family_temperature_note="気にしすぎ扱いせず、嫌さを残す",
    ),
    _case(
        family=FAMILY_DAILY_UNPLEASANT,
        index=4,
        memo="電車でずっと肩にぶつかられて、何も言えないまま苛立ちだけ残った",
        memo_action="今日は早めに休みたい",
        emotions=["苛立ち", "疲労"],
        category=["日常", "身体"],
        coverage_slices=[SLICE_ANGER_OR_BOUNDARY],
        retain_slots=["body_event", "anger_after_no_action"],
        must_not_surface_classes=["action_instruction", "target_attack_agreement"],
        family_temperature_note="日常の不快を大げさにせず、消さない",
    ),
    _case(
        family=FAMILY_DAILY_UNPLEASANT,
        index=5,
        memo="詳しくは書けないけど、やり取りのあとに大事にされていない感じだけ残っている",
        memo_action="今日は距離を置きたい",
        emotions=["寂しさ", "怒り"],
        category=["関係", "境界"],
        coverage_slices=[SLICE_ANGER_OR_BOUNDARY, SLICE_LIMITED_GROUNDING],
        subscription_tier=TIER_PREMIUM,
        retain_slots=["limited_event", "undervalued_feeling", "distance_wish"],
        must_not_surface_classes=["other_person_intent_claim", "over_specific_inference"],
        family_temperature_note="限定材料でも質問中心に潰さず、受け取りを返す",
    ),
    # daily_positive
    _case(
        family=FAMILY_DAILY_POSITIVE,
        index=1,
        memo="朝に少しだけ早く起きられて、今日は始まり方がいつもより軽かった",
        memo_action="この感じを覚えておきたい",
        emotions=["安心", "嬉しい"],
        category=["日常", "小さな達成"],
        retain_slots=["small_achievement", "relief_temperature"],
        must_not_surface_classes=["heavy_analysis", "future_prediction"],
        family_temperature_note="小さな達成を軽く一緒に喜ぶ",
    ),
    _case(
        family=FAMILY_DAILY_POSITIVE,
        index=2,
        memo="話しかけたら思ったより普通に返ってきて、少し安心した",
        memo_action="次も怖がりすぎずにいたい",
        emotions=["安心", "ほっとした"],
        category=["関係", "回復"],
        retain_slots=["conversation_relief", "fear_eased"],
        must_not_surface_classes=["guarantee_future", "relationship_overclaim"],
        family_temperature_note="安心を保証や未来予測にしない",
    ),
    _case(
        family=FAMILY_DAILY_POSITIVE,
        index=3,
        memo="小さな作業を一つ終えただけなのに、止まっていなかった感じがして嬉しい",
        memo_action="次の一つも小さく進めたい",
        emotions=["嬉しい", "前進"],
        category=["仕事", "回復"],
        coverage_slices=[SLICE_STANDARD_STATE_ANSWER],
        path_targets=[PATH_RENDER_DEFAULT, PATH_COMPLETE_INITIAL],
        retain_slots=["small_progress", "not_stopped_feeling"],
        must_not_surface_classes=["productivity_pressure", "generic_praise"],
        family_temperature_note="前進を圧力に変えず、止まっていなかった感覚を拾う",
    ),
    _case(
        family=FAMILY_DAILY_POSITIVE,
        index=4,
        memo="今日はちゃんとご飯を食べられて、それだけで少し戻れた気がする",
        memo_action="自分を責めすぎないでいたい",
        emotions=["回復", "安心"],
        category=["生活", "身体"],
        retain_slots=["body_care", "small_recovery"],
        must_not_surface_classes=["medical_claim", "over_analysis"],
        family_temperature_note="生活の回復を冷まさず、医療断定にしない",
    ),
    _case(
        family=FAMILY_DAILY_POSITIVE,
        index=5,
        memo="久しぶりに友達と笑えて、まだそういう時間が残っているんだと思えた",
        memo_action="この感覚を残したい",
        emotions=["嬉しい", "安心"],
        category=["関係", "回復"],
        subscription_tier=TIER_PLUS,
        retain_slots=["shared_laughter", "remaining_connection"],
        must_not_surface_classes=["relationship_permanence_claim", "cause_claim_without_evidence"],
        family_temperature_note="嬉しさと残っている感覚を素直に扱う",
    ),
    # self_denial
    _case(
        family=FAMILY_SELF_DENIAL,
        index=1,
        memo="また途中で止まって、自分は本当に続けられない人間なんだと思ってしまった",
        memo_action="責めるだけで終わりたくない",
        emotions=["自己嫌悪", "重い"],
        category=["自己理解", "行動前"],
        coverage_slices=[SLICE_STANDARD_STATE_ANSWER],
        retain_slots=["self_denial_words", "stopped_event", "not_end_in_blame_wish"],
        must_not_surface_classes=["identity_claim_as_fact", "self_blame_amplification"],
        family_temperature_note="自己否定語を本人の事実にしない",
    ),
    _case(
        family=FAMILY_SELF_DENIAL,
        index=2,
        memo="挑戦する前から失敗する感じがして、始める前に自分を下げてしまう",
        memo_action="始める前の重さを見たい",
        emotions=["不安", "自己否定"],
        category=["挑戦", "自己理解"],
        retain_slots=["before_action_weight", "self_lowering_reaction"],
        must_not_surface_classes=["failure_prediction", "diagnosis"],
        family_temperature_note="失敗予測を事実化しない",
    ),
    _case(
        family=FAMILY_SELF_DENIAL,
        index=3,
        memo="周りは進んでいるのに自分だけ何もできていない感じがして、比べるほど苦しくなる",
        memo_action="比較で潰れないようにしたい",
        emotions=["焦り", "苦しい"],
        category=["比較", "自己理解"],
        subscription_tier=TIER_PLUS,
        retain_slots=["comparison", "stuck_feeling", "not_collapse_wish"],
        must_not_surface_classes=["others_are_better_claim", "generic_encouragement"],
        family_temperature_note="比較の苦しさを励ましだけで流さない",
    ),
    _case(
        family=FAMILY_SELF_DENIAL,
        index=4,
        memo="大丈夫なふりをしていたけど、内側では自分が嫌いになりそうなくらい疲れている",
        memo_action="危なくなる前に状態を置きたい",
        emotions=["疲弊", "自己嫌悪"],
        category=["安全隣接", "自己理解"],
        retain_slots=["masking", "exhaustion", "early_state_answer"],
        must_not_surface_classes=["emergency_normalization", "identity_claim_as_fact"],
        family_temperature_note="非緊急安全隣接として、通常観測と安全境界を混ぜない",
    ),
    _case(
        family=FAMILY_SELF_DENIAL,
        index=5,
        memo="できない自分を隠すために笑っていた気がして、あとから空っぽになった",
        memo_action="その場の反応を責めずに見たい",
        emotions=["空っぽ", "恥ずかしさ"],
        category=["自己理解", "関係"],
        coverage_slices=[SLICE_STANDARD_STATE_ANSWER],
        path_targets=[PATH_RENDER_DEFAULT, PATH_COMPLETE_INITIAL],
        retain_slots=["hiding_reaction", "after_empty", "not_blame_reaction"],
        must_not_surface_classes=["personality_claim", "cause_claim_without_evidence"],
        family_temperature_note="隠す反応を人格化せず、あとから残った空虚さを拾う",
    ),
    # uncertainty
    _case(
        family=FAMILY_UNCERTAINTY,
        index=1,
        memo="進みたい気持ちはあるのに、どれを選んでも間違える気がして動けない",
        memo_action="迷いの中身を少し見たい",
        emotions=["迷い", "怖さ"],
        category=["選択", "自己理解"],
        coverage_slices=[SLICE_STANDARD_STATE_ANSWER, SLICE_LIMITED_GROUNDING],
        retain_slots=["wish", "fear", "stuck_before_choice"],
        must_not_surface_classes=["choose_for_user", "future_prediction"],
        family_temperature_note="願いと怖さを片方に潰さない",
    ),
    _case(
        family=FAMILY_UNCERTAINTY,
        index=2,
        memo="このままでいいのか変えた方がいいのか、考えるほど分からなくなる",
        memo_action="急いで答えにしないで整理したい",
        emotions=["不安", "未整理"],
        category=["選択", "行動前"],
        coverage_slices=[SLICE_STANDARD_STATE_ANSWER],
        path_targets=[PATH_RENDER_DEFAULT, PATH_COMPLETE_INITIAL],
        retain_slots=["status_quo_question", "change_question", "not_rush_wish"],
        must_not_surface_classes=["advice", "forced_decision"],
        family_temperature_note="答えを出さず、迷いの構造を返す",
    ),
    _case(
        family=FAMILY_UNCERTAINTY,
        index=3,
        memo="やりたいことなのに近づくと怖くなる。期待しているのか避けたいのか自分でも分からない",
        memo_action="近づきたい気持ちと怖さを分けたい",
        emotions=["期待", "怖さ"],
        category=["挑戦", "自己理解"],
        coverage_slices=[SLICE_STANDARD_STATE_ANSWER],
        subscription_tier=TIER_PLUS,
        retain_slots=["approach", "avoidance", "wish_fear_conflict"],
        must_not_surface_classes=["diagnosis", "cause_claim_without_evidence"],
        family_temperature_note="期待と回避を同時に置く",
    ),
    _case(
        family=FAMILY_UNCERTAINTY,
        index=4,
        memo="詳しく説明できないけど、今の選び方だと何か大事なものを落としそうで怖い",
        memo_action="見えている範囲だけで受け取ってほしい",
        emotions=["怖さ", "迷い"],
        category=["価値", "選択"],
        coverage_slices=[SLICE_LIMITED_GROUNDING, SLICE_STANDARD_STATE_ANSWER],
        subscription_tier=TIER_PREMIUM,
        retain_slots=["limited_reason", "value_loss_fear"],
        must_not_surface_classes=["over_specific_value_claim", "deep_reading"],
        family_temperature_note="限定根拠のまま、怖さの方向だけ拾う",
    ),
    _case(
        family=FAMILY_UNCERTAINTY,
        index=5,
        memo="疲れているだけなのか、本当にやめたいのか、今は区別がつかない",
        memo_action="結論より状態を見たい",
        emotions=["疲れ", "迷い"],
        category=["状態確認", "行動前"],
        coverage_slices=[SLICE_STANDARD_STATE_ANSWER],
        retain_slots=["fatigue", "quit_wish_unclear", "state_before_conclusion"],
        must_not_surface_classes=["conclusion_claim", "advice"],
        family_temperature_note="疲労と本音を勝手に同一視しない",
    ),
    # mixed_emotion
    _case(
        family=FAMILY_MIXED_EMOTION,
        index=1,
        memo="褒められて嬉しかったのに、次も同じようにできるか怖くなった",
        memo_action="嬉しさと怖さを両方残したい",
        emotions=["嬉しい", "不安"],
        category=["仕事", "評価"],
        coverage_slices=[SLICE_STANDARD_STATE_ANSWER],
        retain_slots=["positive_event", "next_pressure", "coexisting_emotions"],
        must_not_surface_classes=["flatten_to_positive", "flatten_to_anxiety"],
        family_temperature_note="嬉しさと怖さの同居を保つ",
    ),
    _case(
        family=FAMILY_MIXED_EMOTION,
        index=2,
        memo="怒っているのに、同時に寂しくて、相手を責めたいのか分かってほしいのか揺れている",
        memo_action="この混ざり方を見たい",
        emotions=["怒り", "寂しさ"],
        category=["関係", "境界"],
        coverage_slices=[SLICE_ANGER_OR_BOUNDARY, SLICE_STANDARD_STATE_ANSWER],
        subscription_tier=TIER_PLUS,
        retain_slots=["anger", "loneliness", "blame_or_be_understood"],
        must_not_surface_classes=["target_attack_agreement", "other_person_intent_claim"],
        family_temperature_note="怒りを消さず、攻撃同意にしない",
    ),
    _case(
        family=FAMILY_MIXED_EMOTION,
        index=3,
        memo="やっと終わって安心したけど、ちゃんとできたのか不安だけ残っている",
        memo_action="安心と不安を分けて残したい",
        emotions=["安心", "不安"],
        category=["仕事", "完了"],
        retain_slots=["completion_relief", "remaining_quality_anxiety"],
        must_not_surface_classes=["performance_judgement", "generic_praise"],
        family_temperature_note="完了の安心と残った不安を両方見る",
    ),
    _case(
        family=FAMILY_MIXED_EMOTION,
        index=4,
        memo="詳しくはまだ言えないけど、楽しみな予定なのに近づくほど身体が固くなる",
        memo_action="楽しみを消さずに怖さも見たい",
        emotions=["楽しみ", "緊張"],
        category=["予定", "身体"],
        coverage_slices=[SLICE_LIMITED_GROUNDING, SLICE_STANDARD_STATE_ANSWER],
        subscription_tier=TIER_PREMIUM,
        retain_slots=["limited_event", "positive_expectation", "body_tension"],
        must_not_surface_classes=["deep_inference", "medical_claim"],
        family_temperature_note="限定情報でも楽しい側と緊張側を両方保持する",
    ),
    _case(
        family=FAMILY_MIXED_EMOTION,
        index=5,
        memo="進めたことは嬉しいのに、前より戻れなくなった感じもあって少し怖い",
        memo_action="変化の嬉しさと怖さを見たい",
        emotions=["嬉しい", "怖い"],
        category=["変化", "自己理解"],
        coverage_slices=[SLICE_STANDARD_STATE_ANSWER],
        retain_slots=["change_progress", "no_return_fear"],
        must_not_surface_classes=["future_prediction", "overclaim"],
        family_temperature_note="変化の明るさと不可逆感の怖さを同居させる",
    ),
    # long_meaning_arc
    _case(
        family=FAMILY_LONG_MEANING_ARC,
        index=1,
        memo="朝からずっと仕事のことを考えていて、やることは見えているのに体が遅れている。進みたい気持ちと、また崩れるかもしれない怖さが一緒にあって、夕方には何もしていないわけではないのに置いていかれた感じになった",
        memo_action="今日の流れを一つの失敗にまとめずに見たい",
        emotions=["焦り", "怖さ", "疲れ"],
        category=["仕事", "自己理解", "行動前"],
        coverage_slices=[SLICE_STANDARD_STATE_ANSWER, SLICE_HISTORY_LINE_ELIGIBLE],
        subscription_tier=TIER_PLUS,
        path_targets=[PATH_RENDER_DEFAULT, PATH_HISTORY_LINE_CANDIDATE],
        retain_slots=["multiple_time_points", "wish", "fear", "not_failure_only"],
        must_not_surface_classes=["single_mood_summary", "failure_identity_claim"],
        family_temperature_note="長文を一つの気分に潰さない",
    ),
    _case(
        family=FAMILY_LONG_MEANING_ARC,
        index=2,
        memo="昨日は人に合わせすぎて疲れて、今日は一人になったら楽になると思っていた。でも静かになるほど、合わせていた時間に自分が何を飲み込んだのかが後から出てきて、休んでいるのに頭だけ戻っている",
        memo_action="後から出てきた反応を見たい",
        emotions=["疲れ", "寂しさ", "怒り"],
        category=["関係", "休息", "境界"],
        coverage_slices=[SLICE_ANGER_OR_BOUNDARY, SLICE_STANDARD_STATE_ANSWER],
        retain_slots=["yesterday_today_shift", "swallowed_reaction", "head_returns"],
        must_not_surface_classes=["target_judgement_agreement", "over_short_summary"],
        family_temperature_note="時間差で出てきた反応を拾う",
    ),
    _case(
        family=FAMILY_LONG_MEANING_ARC,
        index=3,
        memo="やりたいことの準備をしているはずなのに、調べるほど自分には足りないものばかり見えてくる。諦めたいわけではないけど、始める前から減点されている感じがして、手を動かすより先に心が閉じる",
        memo_action="願いと停止を分けたい",
        emotions=["願い", "不安", "停止"],
        category=["挑戦", "自己理解"],
        coverage_slices=[SLICE_STANDARD_STATE_ANSWER],
        retain_slots=["preparation", "lack_focus", "wish_not_quit", "heart_closes"],
        must_not_surface_classes=["ability_claim", "advice"],
        family_temperature_note="願いを残したまま停止を見る",
    ),
    _case(
        family=FAMILY_LONG_MEANING_ARC,
        index=4,
        memo="高情報量の入力として扱う。ここには出来事、感情、願い、止まり方が複数あるが、外部生成が使えない場合でも読めたふりではなく、限定された観測として返せるかを見たい",
        memo_action="source unavailableでも通常観測を偽装しないでほしい",
        emotions=["確認", "慎重"],
        category=["検証", "長文"],
        coverage_slices=[SLICE_STANDARD_STATE_ANSWER, SLICE_SOURCE_UNAVAILABLE_HIGH_INFORMATION],
        path_targets=[PATH_RENDER_DEFAULT, PATH_SOURCE_UNAVAILABLE],
        retain_slots=["high_information", "source_unavailable_boundary", "no_fake_reading"],
        must_not_surface_classes=["normal_rebuild_fake", "source_unavailable_as_success"],
        family_temperature_note="source unavailableを読めたふりにしない",
    ),
    _case(
        family=FAMILY_LONG_MEANING_ARC,
        index=5,
        memo="前にも似たように、始める前に重くなって止まった記録がある。今回は少し準備できたけど、同じ線に戻っているのか、それとも前より少し違うのかを見たい",
        memo_action="履歴線が今の入力を隠さないか確認したい",
        emotions=["重さ", "少し前進"],
        category=["自己理解", "履歴線"],
        coverage_slices=[SLICE_HISTORY_LINE_ELIGIBLE, SLICE_SOURCE_UNAVAILABLE_HIGH_INFORMATION, SLICE_STANDARD_STATE_ANSWER],
        subscription_tier=TIER_PREMIUM,
        path_targets=[PATH_RENDER_DEFAULT, PATH_SOURCE_UNAVAILABLE, PATH_HISTORY_LINE_CANDIDATE],
        retain_slots=["history_line", "current_difference", "not_mask_current_input"],
        must_not_surface_classes=["history_overclaim", "history_masks_current_input_gap"],
        family_temperature_note="履歴線より先に今回入力の核を保持する",
    ),
    # relationship_boundary
    _case(
        family=FAMILY_RELATIONSHIP_BOUNDARY,
        index=1,
        memo="相手に合わせて笑っていたけど、本当は踏み込まれた感じがしてあとから嫌になった",
        memo_action="境界線を見たい",
        emotions=["嫌", "疲れ"],
        category=["関係", "境界"],
        coverage_slices=[SLICE_ANGER_OR_BOUNDARY, SLICE_STANDARD_STATE_ANSWER],
        retain_slots=["surface_smile", "intruded_feeling", "after_discomfort"],
        must_not_surface_classes=["other_person_intent_claim", "target_judgement_agreement"],
        family_temperature_note="相手の意図ではなく、ユーザー側の境界を扱う",
    ),
    _case(
        family=FAMILY_RELATIONSHIP_BOUNDARY,
        index=2,
        memo="頼られるのは嫌じゃないのに、今回は自分の余白まで使われた感じがして苦しい",
        memo_action="どこから無理だったのか見たい",
        emotions=["苦しい", "困惑"],
        category=["関係", "役割"],
        coverage_slices=[SLICE_ANGER_OR_BOUNDARY, SLICE_STANDARD_STATE_ANSWER],
        retain_slots=["not_dislike_help", "personal_margin_used", "where_too_much"],
        must_not_surface_classes=["target_blame", "generic_boundary_advice"],
        family_temperature_note="関係を切る指示ではなく、余白の消耗を返す",
    ),
    _case(
        family=FAMILY_RELATIONSHIP_BOUNDARY,
        index=3,
        memo="大事にしたい相手だからこそ、軽く扱われた感じをなかったことにしたくない",
        memo_action="大事にしたい気持ちと嫌だった気持ちを両方残したい",
        emotions=["怒り", "大切"],
        category=["関係", "境界"],
        coverage_slices=[SLICE_ANGER_OR_BOUNDARY, SLICE_STANDARD_STATE_ANSWER],
        retain_slots=["care_for_person", "felt_lightly_treated", "not_erase_discomfort"],
        must_not_surface_classes=["relationship_judgement", "other_person_intent_claim"],
        family_temperature_note="大事さと怒りを同時に置く",
    ),
    _case(
        family=FAMILY_RELATIONSHIP_BOUNDARY,
        index=4,
        memo="前にも似た場面で黙って飲み込んだ記録がある。今回は黙ったままにしたくないけど、強く言うのも怖い",
        memo_action="履歴と今回の違いを見たい",
        emotions=["怖さ", "怒り"],
        category=["関係", "履歴線"],
        coverage_slices=[SLICE_ANGER_OR_BOUNDARY, SLICE_HISTORY_LINE_ELIGIBLE, SLICE_STANDARD_STATE_ANSWER],
        subscription_tier=TIER_PLUS,
        path_targets=[PATH_RENDER_DEFAULT, PATH_HISTORY_LINE_CANDIDATE],
        retain_slots=["past_swallowing", "current_not_silent_wish", "fear_of_strong_expression"],
        must_not_surface_classes=["history_overclaim", "advice"],
        family_temperature_note="履歴線で今の怖さを隠さない",
    ),
    _case(
        family=FAMILY_RELATIONSHIP_BOUNDARY,
        index=5,
        memo="高情報量だが外部sourceが使えない想定。相手との距離、怒り、寂しさ、言えなかったことがあるので、読めたふりではなく境界だけ安全に見たい",
        memo_action="source unavailable時の関係入力を確認したい",
        emotions=["怒り", "寂しさ"],
        category=["関係", "境界", "検証"],
        coverage_slices=[SLICE_ANGER_OR_BOUNDARY, SLICE_SOURCE_UNAVAILABLE_HIGH_INFORMATION, SLICE_STANDARD_STATE_ANSWER],
        path_targets=[PATH_RENDER_DEFAULT, PATH_SOURCE_UNAVAILABLE],
        retain_slots=["relationship_boundary", "source_unavailable_boundary", "safe_limited_observation"],
        must_not_surface_classes=["other_person_intent_claim", "normal_rebuild_fake"],
        family_temperature_note="source unavailableでも相手断定せず限定観測にする",
    ),
    # structure_question
    _case(
        family=FAMILY_STRUCTURE_QUESTION,
        index=1,
        memo="なぜ毎回、始める前に急に重くなるのかを見たい。やりたい気持ちはあるのに、体だけ止まる感じがある",
        memo_action="自分の反応の構造を知りたい",
        emotions=["重い", "疑問"],
        category=["自己理解", "構造質問"],
        coverage_slices=[SLICE_STANDARD_STATE_ANSWER],
        retain_slots=["why_question", "wish", "body_stops"],
        must_not_surface_classes=["comfort_only", "diagnosis"],
        family_temperature_note="慰めだけで逃げず、問いの構造を返す",
    ),
    _case(
        family=FAMILY_STRUCTURE_QUESTION,
        index=2,
        memo="人から返事が遅いだけで、自分が間違えたのかもしれないと考え始める。この反応は何が起きているんだろう",
        memo_action="反応の始まりを見たい",
        emotions=["不安", "焦り"],
        category=["関係", "構造質問"],
        coverage_slices=[SLICE_STANDARD_STATE_ANSWER],
        path_targets=[PATH_RENDER_DEFAULT, PATH_COMPLETE_INITIAL],
        retain_slots=["reply_delay", "self_error_assumption", "reaction_start"],
        must_not_surface_classes=["other_person_intent_claim", "diagnosis"],
        family_temperature_note="相手理由ではなく、反応開始の構造を見る",
    ),
    _case(
        family=FAMILY_STRUCTURE_QUESTION,
        index=3,
        memo="同じことを繰り返している気がする。やる前に考えすぎて、やった後には責めて、次の前にまた怖くなる",
        memo_action="繰り返しの線を見たい",
        emotions=["怖さ", "自己嫌悪"],
        category=["自己理解", "繰り返し"],
        coverage_slices=[SLICE_STANDARD_STATE_ANSWER],
        retain_slots=["before_overthinking", "after_blame", "repeat_line"],
        must_not_surface_classes=["personality_claim", "fixed_pattern_claim"],
        family_temperature_note="繰り返しを性格断定にしない",
    ),
    _case(
        family=FAMILY_STRUCTURE_QUESTION,
        index=4,
        memo="前にも似た入力があったはず。今回も『自分が悪い』に寄りそうだけど、本当にそこだけなのか見たい",
        memo_action="履歴線と今回の問いを分けたい",
        emotions=["迷い", "自己否定"],
        category=["自己理解", "履歴線"],
        coverage_slices=[SLICE_HISTORY_LINE_ELIGIBLE, SLICE_STANDARD_STATE_ANSWER],
        subscription_tier=TIER_PLUS,
        path_targets=[PATH_RENDER_DEFAULT, PATH_HISTORY_LINE_CANDIDATE],
        retain_slots=["history_line", "current_self_blame_pull", "question_not_answered_as_blame"],
        must_not_surface_classes=["history_overclaim", "self_blame_as_fact"],
        family_temperature_note="履歴線を使っても今回の問いを薄めない",
    ),
    _case(
        family=FAMILY_STRUCTURE_QUESTION,
        index=5,
        memo="詳しくはまだ書けない。でも、反応の形だけでも見たい。怖い、止まる、でも進みたい、という順番がある気がする",
        memo_action="限定された材料で構造を見たい",
        emotions=["怖い", "進みたい"],
        category=["構造質問", "限定"],
        coverage_slices=[SLICE_LIMITED_GROUNDING, SLICE_STANDARD_STATE_ANSWER],
        subscription_tier=TIER_PREMIUM,
        retain_slots=["limited_material", "fear_stop_wish_order"],
        must_not_surface_classes=["over_specific_inference", "question_only_surface"],
        family_temperature_note="限定材料を質問だけで返さず、見える順番だけ扱う",
    ),
    # positive_only
    _case(
        family=FAMILY_POSITIVE_ONLY,
        index=1,
        memo="よかった。今日は本当にそれだけでいい気がする",
        memo_action="このまま残したい",
        emotions=["嬉しい"],
        category=["日常", "ポジティブ"],
        retain_slots=["simple_good", "do_not_overwork"],
        must_not_surface_classes=["heavy_analysis", "problem_search"],
        family_temperature_note="明るさを問題探しに変えない",
    ),
    _case(
        family=FAMILY_POSITIVE_ONLY,
        index=2,
        memo="少し進めた。大きくはないけど、止まってはいなかった",
        memo_action="小さく残しておきたい",
        emotions=["前進", "安心"],
        category=["行動", "回復"],
        path_targets=[PATH_RENDER_DEFAULT, PATH_COMPLETE_INITIAL],
        retain_slots=["small_progress", "not_stopped"],
        must_not_surface_classes=["productivity_pressure", "over_analysis"],
        family_temperature_note="小さな前進を圧力にしない",
    ),
    _case(
        family=FAMILY_POSITIVE_ONLY,
        index=3,
        memo="安心した。思っていたより怖くなかった",
        memo_action="この安心を覚えておきたい",
        emotions=["安心"],
        category=["回復", "挑戦"],
        retain_slots=["relief", "less_fear_than_expected"],
        must_not_surface_classes=["future_guarantee", "challenge_pressure"],
        family_temperature_note="安心を未来保証にしない",
    ),
    _case(
        family=FAMILY_POSITIVE_ONLY,
        index=4,
        memo="助かった、という感覚がちゃんとあった。今日はそれを消したくない",
        memo_action="助かった感覚を残したい",
        emotions=["助かった", "安心"],
        category=["関係", "回復"],
        subscription_tier=TIER_PLUS,
        retain_slots=["felt_helped", "do_not_erase_positive"],
        must_not_surface_classes=["relationship_overclaim", "problem_search"],
        family_temperature_note="助かった感覚をそのまま扱う",
    ),
    _case(
        family=FAMILY_POSITIVE_ONLY,
        index=5,
        memo="今日はいつもより少し自分に優しくできた。それが嬉しい",
        memo_action="自分に向けた良さを覚えたい",
        emotions=["嬉しい", "穏やか"],
        category=["自己理解", "回復"],
        retain_slots=["self_kindness", "quiet_positive"],
        must_not_surface_classes=["identity_overclaim", "heavy_analysis"],
        family_temperature_note="穏やかなポジティブを大げさにしない",
    ),
    # self_understanding_follow
    _case(
        family=FAMILY_SELF_UNDERSTANDING_FOLLOW,
        index=1,
        memo="前にも、何かを始める前に急に重くなって止まった記録がある。今回も似ているけど、少しだけ手前で気づけた",
        memo_action="自分の反応の線として見たい",
        emotions=["重さ", "気づき"],
        category=["自己理解", "履歴線"],
        coverage_slices=[SLICE_HISTORY_LINE_ELIGIBLE, SLICE_STANDARD_STATE_ANSWER],
        subscription_tier=TIER_PLUS,
        path_targets=[PATH_RENDER_DEFAULT, PATH_HISTORY_LINE_CANDIDATE],
        retain_slots=["past_similarity", "current_early_notice", "self_understanding_line"],
        must_not_surface_classes=["history_identity_claim", "always_claim"],
        family_temperature_note="履歴線を断定せず、気づけた差分を拾う",
    ),
    _case(
        family=FAMILY_SELF_UNDERSTANDING_FOLLOW,
        index=2,
        memo="今日は出来事そのものより、自分がすぐに謝りそうになった反応の方が気になっている",
        memo_action="反応を責めずに見たい",
        emotions=["気になる", "不安"],
        category=["自己理解", "関係"],
        coverage_slices=[SLICE_STANDARD_STATE_ANSWER],
        retain_slots=["reaction_focus", "apology_pull", "not_blame"],
        must_not_surface_classes=["personality_claim", "generic_advice"],
        family_temperature_note="出来事より自己観察に焦点を合わせる",
    ),
    _case(
        family=FAMILY_SELF_UNDERSTANDING_FOLLOW,
        index=3,
        memo="行動する前に、頭の中で相手の反応を何度も想像して疲れていることに気づいた",
        memo_action="行動前の反応を見たい",
        emotions=["疲れ", "気づき"],
        category=["行動前", "自己理解"],
        coverage_slices=[SLICE_STANDARD_STATE_ANSWER],
        path_targets=[PATH_RENDER_DEFAULT, PATH_COMPLETE_INITIAL],
        retain_slots=["before_action", "imagined_reactions", "tired_from_simulation"],
        must_not_surface_classes=["other_person_intent_claim", "advice"],
        family_temperature_note="相手ではなく、想像で疲れる工程を見る",
    ),
    _case(
        family=FAMILY_SELF_UNDERSTANDING_FOLLOW,
        index=4,
        memo="自分を分かりたいと思って書いているのに、書くほど分からなさも増える",
        memo_action="分かりたい気持ちを消さずに置きたい",
        emotions=["分からない", "願い"],
        category=["自己理解", "未整理"],
        coverage_slices=[SLICE_STANDARD_STATE_ANSWER],
        retain_slots=["wish_to_understand", "more_unclear_after_writing"],
        must_not_surface_classes=["diagnosis", "forced_clarity"],
        family_temperature_note="分からなさを失敗にしない",
    ),
    _case(
        family=FAMILY_SELF_UNDERSTANDING_FOLLOW,
        index=5,
        memo="前の記録では不安だけを書いていたけど、今回は怖さの奥に進みたい気持ちもあると分かった",
        memo_action="履歴との違いを見たい",
        emotions=["怖さ", "進みたい"],
        category=["自己理解", "履歴線"],
        coverage_slices=[SLICE_HISTORY_LINE_ELIGIBLE, SLICE_STANDARD_STATE_ANSWER],
        subscription_tier=TIER_PREMIUM,
        path_targets=[PATH_RENDER_DEFAULT, PATH_HISTORY_LINE_CANDIDATE],
        retain_slots=["past_anxiety", "current_wish", "difference_from_history"],
        must_not_surface_classes=["history_overclaim", "progress_claim_without_boundary"],
        family_temperature_note="履歴差分を強い成長断定にしない",
    ),
    # input_self_report_only_failure
    _case(
        family=FAMILY_INPUT_SELF_REPORT_ONLY_FAILURE,
        index=1,
        memo="また同じことを言っているだけな気がする。嫌だった、疲れた、でも何が起きているか分からない、で止まる",
        memo_action="復唱だけではなく構造差分が必要か見たい",
        emotions=["疲れ", "嫌"],
        category=["自己理解", "検証"],
        coverage_slices=[SLICE_STANDARD_STATE_ANSWER],
        retain_slots=["repeated_self_report", "unknown_structure", "needs_delta"],
        must_not_surface_classes=["mirror_only", "summary_only"],
        family_temperature_note="言い換えだけでPASSにしない",
    ),
    _case(
        family=FAMILY_INPUT_SELF_REPORT_ONLY_FAILURE,
        index=2,
        memo="私はつらい、私は不安、私は疲れた、と並べているけど、その間のつながりが返らないと浅く感じると思う",
        memo_action="mirror-only検出用に残す",
        emotions=["つらい", "不安", "疲れ"],
        category=["検証", "自己理解"],
        retain_slots=["self_report_list", "relation_missing_expectation"],
        must_not_surface_classes=["self_report_only", "generic_comfort_template"],
        family_temperature_note="自己報告の列挙をそのまま返して終わらない",
    ),
    _case(
        family=FAMILY_INPUT_SELF_REPORT_ONLY_FAILURE,
        index=3,
        memo="やりたい、怖い、止まる、責める。この四つをただ並べ返されると読まれた感じにはならない",
        memo_action="関係が返るかを見たい",
        emotions=["願い", "怖い", "自己責め"],
        category=["検証", "構造質問"],
        coverage_slices=[SLICE_STANDARD_STATE_ANSWER],
        path_targets=[PATH_RENDER_DEFAULT, PATH_COMPLETE_INITIAL],
        retain_slots=["wish_fear_stop_blame_relation"],
        must_not_surface_classes=["list_rephrase_only", "insight_delta_missing"],
        family_temperature_note="材料間の関係がなければ修正対象にする",
    ),
    _case(
        family=FAMILY_INPUT_SELF_REPORT_ONLY_FAILURE,
        index=4,
        memo="今日は不安だった。昨日も不安だった。前も不安だった。という履歴っぽい返しだけだと、今の入力は読まれていない気がする",
        memo_action="履歴線で単発の弱さを隠さないか見たい",
        emotions=["不安", "確認"],
        category=["履歴線", "検証"],
        coverage_slices=[SLICE_HISTORY_LINE_ELIGIBLE, SLICE_STANDARD_STATE_ANSWER],
        subscription_tier=TIER_PLUS,
        path_targets=[PATH_RENDER_DEFAULT, PATH_HISTORY_LINE_CANDIDATE],
        retain_slots=["history_line_risk", "current_input_anchor"],
        must_not_surface_classes=["history_line_masks_current_input_gap", "summary_only"],
        family_temperature_note="履歴線だけで読感不足を隠さない",
    ),
    _case(
        family=FAMILY_INPUT_SELF_REPORT_ONLY_FAILURE,
        index=5,
        memo="詳しくはあるのに、ただ『大変でしたね』で終わると、入力の核が落ちたことを検出したい",
        memo_action="generic surface検出用に残す",
        emotions=["確認", "不安"],
        category=["検証", "長文"],
        coverage_slices=[SLICE_STANDARD_STATE_ANSWER, SLICE_LIMITED_GROUNDING],
        retain_slots=["high_information_but_generic_risk", "input_core_missing"],
        must_not_surface_classes=["generic_reception_surface", "input_core_missing"],
        family_temperature_note="汎用受け取り文だけで終わるケースを検出する",
    ),
)


def build_product_readfeel_baseline_cases_20260609() -> list[dict[str, Any]]:
    """Return the synthetic local-QA baseline matrix for P3-1."""

    cases = [deepcopy(case) for case in _CASE_SPECS]
    assert_product_readfeel_baseline_case_matrix_contract_20260609(cases)
    return cases


def _family_counts(cases: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counter = Counter(str(case.get("family", "")) for case in cases)
    return {family: int(counter.get(family, 0)) for family in PRODUCT_READFEEL_BASELINE_REQUIRED_FAMILIES_20260609}


def _coverage_slice_counts(cases: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for case in cases:
        counter.update(_dedupe(case.get("coverage_slices")))
    return dict(sorted(counter.items()))


def _validate_baseline_cases(cases: Sequence[Mapping[str, Any]]) -> None:
    if len(cases) != PRODUCT_READFEEL_BASELINE_EXPECTED_CASE_COUNT_20260609:
        raise ValueError("P3-1 baseline case matrix must contain exactly 60 cases")
    seen_case_ids: set[str] = set()
    for case in cases:
        if _contains_forbidden_key(case, _LOCAL_CASE_FORBIDDEN_OUTPUT_KEYS):
            raise ValueError("P3-1 baseline cases must not contain output/comment_text payloads")
        flag_path = _forbidden_true_flag_path(case)
        if flag_path:
            raise ValueError(f"P3-1 baseline case violates fixed boundary at {flag_path}")
        case_id = str(case.get("case_id", ""))
        if not _CASE_ID_RE.match(case_id):
            raise ValueError(f"invalid P3-1 baseline case_id: {case_id}")
        if case_id in seen_case_ids:
            raise ValueError(f"duplicate P3-1 baseline case_id: {case_id}")
        seen_case_ids.add(case_id)
        family = str(case.get("family", ""))
        if family not in PRODUCT_READFEEL_BASELINE_REQUIRED_FAMILIES_20260609:
            raise ValueError(f"unsupported P3-1 baseline family: {family}")
        slices = _dedupe(case.get("coverage_slices"))
        if not slices or any(value not in VALID_COVERAGE_SLICES_20260609 for value in slices):
            raise ValueError(f"unsupported P3-1 coverage_slices for {case_id}")
        tier = str(case.get("subscription_tier", ""))
        if tier not in VALID_SUBSCRIPTION_TIERS_20260609:
            raise ValueError(f"unsupported subscription_tier for {case_id}")
        if _slice_for_tier(tier) not in slices:
            raise ValueError(f"tier coverage slice missing for {case_id}")
        path_targets = _dedupe(case.get("path_targets"))
        if not path_targets or any(path not in VALID_PATH_TARGETS_20260609 for path in path_targets):
            raise ValueError(f"unsupported path_targets for {case_id}")
        current = case.get("current_input")
        if not isinstance(current, Mapping):
            raise ValueError(f"current_input missing for {case_id}")
        if not str(current.get("memo", "")).strip():
            raise ValueError(f"current_input.memo missing for {case_id}")
        if not current.get("synthetic_case_material") is True:
            raise ValueError(f"P3-1 baseline case must be synthetic: {case_id}")
        expected = case.get("expected_contract")
        if not isinstance(expected, Mapping):
            raise ValueError(f"expected_contract missing for {case_id}")
        if expected.get("display_expected") is not True:
            raise ValueError(f"display_expected must stay true for P3-1 baseline: {case_id}")
        if expected.get("rn_visible_expected") is not True:
            raise ValueError(f"rn_visible_expected must stay true for P3-1 baseline: {case_id}")
        controls = case.get("evaluation_controls")
        if not isinstance(controls, Mapping):
            raise ValueError(f"evaluation_controls missing for {case_id}")
        for key in (
            "exact_comment_text_required",
            "case_specific_runtime_branch_allowed",
            "gate_relaxation_allowed",
            "public_meta_body_allowed",
        ):
            if controls.get(key) is not False:
                raise ValueError(f"{key} must be false for {case_id}")
    counts = _family_counts(cases)
    if any(count != PRODUCT_READFEEL_BASELINE_CASES_PER_FAMILY_20260609 for count in counts.values()):
        raise ValueError("P3-1 baseline matrix must contain exactly 5 cases for each required family")
    coverage_counts = _coverage_slice_counts(cases)
    for slice_id, minimum in REQUIRED_COVERAGE_MINIMUMS_20260609.items():
        if int(coverage_counts.get(slice_id, 0)) < minimum:
            raise ValueError(f"P3-1 baseline coverage slice {slice_id} is below minimum {minimum}")


def assert_product_readfeel_baseline_case_matrix_contract_20260609(
    cases: Sequence[Mapping[str, Any]] | None,
    *,
    source: str = "product_readfeel_baseline_cases_20260609",
) -> None:
    if not isinstance(cases, Sequence) or isinstance(cases, (str, bytes, bytearray)):
        raise ValueError(f"{source} must be a sequence of mappings")
    _validate_baseline_cases(cases)


def assert_product_readfeel_baseline_public_safe_meta_only_20260609(
    payload: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None,
    *,
    source: str = "product_readfeel_baseline_public_safe_index_20260609",
) -> None:
    if payload is None:
        raise ValueError(f"{source} must not be None")
    if _contains_forbidden_key(payload, _PUBLIC_SAFE_FORBIDDEN_TEXT_KEYS):
        raise ValueError(f"{source} must not include raw input or comment_text payload keys")
    flag_path = _forbidden_true_flag_path(payload)
    if flag_path:
        raise ValueError(f"{source} marks forbidden flag true at {flag_path}")


def build_product_readfeel_baseline_case_matrix_summary_20260609(
    cases: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    local_cases = list(cases or build_product_readfeel_baseline_cases_20260609())
    assert_product_readfeel_baseline_case_matrix_contract_20260609(local_cases)
    family_counts = _family_counts(local_cases)
    coverage_counts = _coverage_slice_counts(local_cases)
    missing_families = [family for family, count in family_counts.items() if count == 0]
    below_minimum_slices = [
        slice_id
        for slice_id, minimum in REQUIRED_COVERAGE_MINIMUMS_20260609.items()
        if int(coverage_counts.get(slice_id, 0)) < minimum
    ]
    summary = {
        "version": PRODUCT_READFEEL_BASELINE_CASE_MATRIX_VERSION_20260609,
        "schema_version": PRODUCT_READFEEL_BASELINE_CASE_MATRIX_VERSION_20260609,
        "source": PRODUCT_READFEEL_BASELINE_CASE_SOURCE_20260609,
        "source_step": PRODUCT_READFEEL_BASELINE_CASE_STEP_20260609,
        "baseline_case_matrix_ready": not missing_families and not below_minimum_slices,
        "p3_0_contract_freeze_respected": True,
        "p3_1_baseline_case_matrix_ready": not missing_families and not below_minimum_slices,
        "local_qa_only": True,
        "contains_synthetic_local_case_material": True,
        "case_count": len(local_cases),
        "required_families": list(PRODUCT_READFEEL_BASELINE_REQUIRED_FAMILIES_20260609),
        "family_counts": family_counts,
        "missing_families": missing_families,
        "cases_per_required_family": PRODUCT_READFEEL_BASELINE_CASES_PER_FAMILY_20260609,
        "coverage_slice_counts": coverage_counts,
        "coverage_requirements": dict(REQUIRED_COVERAGE_MINIMUMS_20260609),
        "below_minimum_slices": below_minimum_slices,
        "output_capture_completed": False,
        "sanitized_current_output_event_created": False,
        "scorecard_event_created": False,
        "exact_comment_text_required": False,
        "case_specific_runtime_branch": False,
        "case_specific_runtime_branch_allowed": False,
        "runtime_branching_uses_fixture_strings": False,
        "fixture_text_used_for_runtime_branching": False,
        "gate_relaxation_allowed": False,
        "public_meta_body_allowed": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "public_response_key_change": False,
        "rn_visible_contract_changed": False,
        "product_gate_ready": False,
        "public_release_applied": False,
    }
    assert_product_readfeel_baseline_public_safe_meta_only_20260609(
        summary,
        source="product_readfeel_baseline_case_matrix_summary_20260609",
    )
    return summary


def build_product_readfeel_baseline_public_safe_index_20260609(
    cases: Sequence[Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Return a body-free index of the P3-1 matrix.

    This index can be committed or passed into meta-only reporting layers.  It
    deliberately drops ``current_input`` and keeps only ids, family/slice/path
    coverage, expected contract booleans, and boundary flags.
    """

    local_cases = list(cases or build_product_readfeel_baseline_cases_20260609())
    assert_product_readfeel_baseline_case_matrix_contract_20260609(local_cases)
    items: list[dict[str, Any]] = []
    for case in local_cases:
        expected = case["expected_contract"]
        controls = case["evaluation_controls"]
        items.append(
            {
                "version": PRODUCT_READFEEL_BASELINE_PUBLIC_SAFE_INDEX_VERSION_20260609,
                "schema_version": PRODUCT_READFEEL_BASELINE_PUBLIC_SAFE_INDEX_VERSION_20260609,
                "source": PRODUCT_READFEEL_BASELINE_CASE_SOURCE_20260609,
                "source_step": PRODUCT_READFEEL_BASELINE_CASE_STEP_20260609,
                "case_id": case["case_id"],
                "family": case["family"],
                "product_readfeel_family": case["product_readfeel_family"],
                "coverage_slices": list(case["coverage_slices"]),
                "subscription_tier": case["subscription_tier"],
                "path_targets": list(case["path_targets"]),
                "display_expected": bool(expected.get("display_expected")),
                "rn_visible_expected": bool(expected.get("rn_visible_expected")),
                "product_surface_validation_required": bool(
                    expected.get("product_surface_validation_required")
                ),
                "must_retain_slot_count": len(expected.get("must_retain_slots") or []),
                "must_not_surface_class_count": len(expected.get("must_not_surface_classes") or []),
                "history_context_enabled": SLICE_HISTORY_LINE_ELIGIBLE in case["coverage_slices"],
                "local_case_material_available": True,
                "local_case_material_is_synthetic": True,
                "local_case_material_retained_here": False,
                "output_capture_completed": False,
                "sanitized_current_output_event_created": False,
                "exact_comment_text_required": bool(controls.get("exact_comment_text_required")),
                "case_specific_runtime_branch_allowed": bool(
                    controls.get("case_specific_runtime_branch_allowed")
                ),
                "gate_relaxation_allowed": bool(controls.get("gate_relaxation_allowed")),
                "public_meta_body_allowed": bool(controls.get("public_meta_body_allowed")),
                "runtime_branching_uses_fixture_strings": False,
                "fixture_text_used_for_runtime_branching": False,
                "raw_input_included": False,
                "comment_text_body_included": False,
                "public_response_key_change": False,
                "rn_visible_contract_changed": False,
                "product_gate_ready": False,
                "public_release_applied": False,
            }
        )
    assert_product_readfeel_baseline_public_safe_meta_only_20260609(
        items,
        source="product_readfeel_baseline_public_safe_index_20260609",
    )
    return items


def dump_product_readfeel_baseline_case_matrix_summary_20260609(
    summary: Mapping[str, Any] | None = None,
) -> str:
    data = dict(summary or build_product_readfeel_baseline_case_matrix_summary_20260609())
    assert_product_readfeel_baseline_public_safe_meta_only_20260609(data)
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


assert_product_readfeel_baseline_case_matrix_contract_20260609(_CASE_SPECS)

__all__ = [
    "PRODUCT_READFEEL_BASELINE_CASE_VERSION_20260609",
    "PRODUCT_READFEEL_BASELINE_CASE_MATRIX_VERSION_20260609",
    "PRODUCT_READFEEL_BASELINE_PUBLIC_SAFE_INDEX_VERSION_20260609",
    "PRODUCT_READFEEL_BASELINE_CASE_STEP_20260609",
    "PRODUCT_READFEEL_BASELINE_REQUIRED_FAMILIES_20260609",
    "PRODUCT_READFEEL_BASELINE_CASES_PER_FAMILY_20260609",
    "PRODUCT_READFEEL_BASELINE_EXPECTED_CASE_COUNT_20260609",
    "REQUIRED_COVERAGE_MINIMUMS_20260609",
    "VALID_COVERAGE_SLICES_20260609",
    "VALID_PATH_TARGETS_20260609",
    "assert_product_readfeel_baseline_case_matrix_contract_20260609",
    "assert_product_readfeel_baseline_public_safe_meta_only_20260609",
    "build_product_readfeel_baseline_cases_20260609",
    "build_product_readfeel_baseline_case_matrix_summary_20260609",
    "build_product_readfeel_baseline_public_safe_index_20260609",
    "dump_product_readfeel_baseline_case_matrix_summary_20260609",
]
