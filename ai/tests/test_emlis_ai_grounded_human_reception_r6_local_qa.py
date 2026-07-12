# -*- coding: utf-8 -*-
from __future__ import annotations

"""R6 exact8/same16/unseen batch QA and hash-bound Karen actual read."""

import asyncio
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

import pytest

from helpers.emlis_ai_grounded_human_reception_r6_qa import (
    R6_REVIEW_AXES,
    ReceptionBatchCase,
    evaluate_reception_batch,
    sha256_text,
    validate_karen_review_receipt,
)
from helpers.emlis_ai_grounded_observation_i0_inventory import (
    GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES,
)
from helpers.emlis_ai_grounded_observation_i6_cases import (
    GROUND_OBSERVATION_I6_BLIND_CASES,
    I6_FAMILIES,
)
from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_observation_gate import (
    RECEPTION_GATE_REPORT_FIELDS,
    evaluate_grounded_observation_gate,
)
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_grounded_sentence_surface import (
    build_grounded_sentence_plan,
    realize_grounded_sentence_plan,
    split_two_stage_surface,
)
from emlis_ai_public_feedback_meta import build_public_emlis_input_feedback_meta
from emlis_ai_reply_service import render_emlis_ai_reply


_TEST_ROOT = Path(__file__).resolve().parent
_EXACT8_FIXTURE = (
    _TEST_ROOT / "fixtures" / "grounded_human_reception_exact8_v2_20260712.json"
)
_OBSERVATION_HASHES = (
    _TEST_ROOT / "fixtures" / "grounded_human_reception_section_hashes_20260712.json"
)
_UNSEEN8_FIXTURE = (
    _TEST_ROOT
    / "local_only"
    / "grounded_human_reception_r6_unseen8_20260712.json"
)
_VISIBLE_PACKET = (
    _TEST_ROOT
    / "local_only"
    / "grounded_human_reception_r6_exact8_visible_packet_20260712.json"
)
_KAREN_RECEIPT = (
    _TEST_ROOT
    / "fixtures"
    / "grounded_human_reception_r6_karen_review_receipt_20260712.json"
)
_AUTOMATED_RECEIPT = (
    _TEST_ROOT
    / "fixtures"
    / "grounded_human_reception_r6_local_qa_receipt_20260712.json"
)
_SOURCE_SNAPSHOT_FILES = (
    "ai/services/ai_inference/emlis_ai_grounded_observation_plan.py",
    "ai/services/ai_inference/emlis_ai_grounded_human_reception.py",
    "ai/services/ai_inference/emlis_ai_grounded_sentence_surface.py",
    "ai/services/ai_inference/emlis_ai_grounded_observation_gate.py",
    "ai/services/ai_inference/emlis_ai_reply_service.py",
)
_POLICY_RE = re.compile(
    r"理由を(?:こちらで)?決めつけず|入力から言える範囲で|"
    r"診断はしません|ここでは事実として扱いません|原因は分かりませんが"
)


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _source_snapshot_sha256() -> str:
    backend_root = _TEST_ROOT.parents[1]
    rows = [
        {
            "path": relative_path,
            "sha256": hashlib.sha256(
                (backend_root / relative_path).read_bytes()
            ).hexdigest(),
        }
        for relative_path in _SOURCE_SNAPSHOT_FILES
    ]
    payload = json.dumps(
        rows,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256_text(payload)


_SOURCE_SNAPSHOT_SHA256 = _source_snapshot_sha256()


def _canonical_input_sha256(current_input) -> str:
    payload = json.dumps(
        current_input,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256_text(payload)


def _artifacts(current_input):
    normalized = normalize_emlis_current_input(current_input)
    spans = tuple(build_evidence_ledger(normalized))
    resolver = build_evidence_span_resolver(spans, current_input=normalized)
    plan = build_grounded_observation_plan(normalized, evidence_spans=spans)
    sentence_plan = build_grounded_sentence_plan(plan, resolver)
    surface = realize_grounded_sentence_plan(sentence_plan, plan, resolver)
    report = evaluate_grounded_observation_gate(
        plan=plan,
        sentence_plan=sentence_plan,
        surface_result=surface,
        resolver=resolver,
    )
    observation, reception, issues = split_two_stage_surface(surface.text)
    assert issues == ()
    return plan, sentence_plan, surface, report, observation, reception


def _batch_case(case_id: str, artifacts) -> ReceptionBatchCase:
    _plan, _sentence_plan, surface, report, _observation, reception = artifacts
    return ReceptionBatchCase(
        case_id=case_id,
        reception_text=reception,
        full_surface_sha256=sha256_text(surface.text),
        reception_act=report.reception_act,
        terminal_predicate_kind=report.reception_terminal_predicate_kind,
    )


def _synthetic_batch_case(case_id: str, reception_text: str) -> ReceptionBatchCase:
    return ReceptionBatchCase(
        case_id=case_id,
        reception_text=reception_text,
        full_surface_sha256=sha256_text(f"surface:{case_id}"),
        reception_act="acknowledge_effort",
        terminal_predicate_kind="human_response_acknowledgment",
    )


def _assert_all_reception_gates(report) -> None:
    assert report.passed is True
    assert report.public_observation_status == "passed"
    assert report.semantic_quality_gate == "passed"
    assert report.two_stage_contract_gate == "passed"
    assert report.mechanical_restatement_gate == "passed"
    assert report.repeated_long_anchor_count == 0
    assert all(
        getattr(report, field_name) == "passed"
        for field_name in RECEPTION_GATE_REPORT_FIELDS
    )
    assert report.product_readfeel_status == "not_evaluated"


def _assert_batch_receipt(batch, receipt_row) -> None:
    assert receipt_row["case_count"] == batch.case_count
    assert receipt_row["exact_reception_sentence_duplicate_group_count"] == len(
        batch.duplicate_sentence_groups
    )
    assert receipt_row["self_repeated_sentence_case_count"] == len(
        batch.self_repeated_sentence_cases
    )
    assert receipt_row["maximum_closing_stem_family_count"] == max(
        (family["case_count"] for family in batch.closing_stem_families),
        default=0,
    )
    assert receipt_row["closing_hard_threshold"] == batch.closing_hard_threshold
    assert receipt_row["abstract_ending_union_count"] == (
        batch.abstract_ending_union_count
    )
    assert receipt_row["verdict"] == batch.verdict


def _exact8_results():
    fixture = _load(_EXACT8_FIXTURE)
    manifest = _load(_OBSERVATION_HASHES)
    expected_hashes = {
        case["case_id"]: case["observation_section_sha256"]
        for case in manifest["cases"]
    }
    output = []
    for case in fixture["cases"]:
        artifacts = _artifacts(case["exact_current_input"])
        report = artifacts[3]
        observation = artifacts[4]
        reception = artifacts[5]
        _assert_all_reception_gates(report)
        assert sha256_text(observation) == expected_hashes[case["case_id"]]
        assert _POLICY_RE.search(reception) is None
        output.append((case, artifacts))
    return tuple(output)


def _same16_results():
    cases = (
        *GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES,
        *GROUND_OBSERVATION_I6_BLIND_CASES,
    )
    return tuple(
        (case.case_id, _artifacts(case.as_current_input())) for case in cases
    )


def _unseen8_results():
    fixture = _load(_UNSEEN8_FIXTURE)
    return fixture, tuple(
        (case, _artifacts(case["current_input"])) for case in fixture["cases"]
    )


def test_r6_exact8_technical_acceptance_and_batch_template_qa() -> None:
    results = _exact8_results()
    batch = evaluate_reception_batch(
        "exact8_app_valid",
        tuple(
            _batch_case(case["case_id"], artifacts)
            for case, artifacts in results
        ),
        closing_hard_threshold=4,
    )

    assert len(results) == 8
    assert batch.verdict == "passed"
    assert batch.reason_codes == ()
    assert batch.duplicate_sentence_groups == ()
    assert batch.self_repeated_sentence_cases == ()
    assert all(
        family["case_count"] < 4 for family in batch.closing_stem_families
    )
    assert batch.abstract_ending_union_count <= 4
    assert batch.as_body_free_meta()["surface_body_included"] is False
    _assert_batch_receipt(
        batch,
        _load(_AUTOMATED_RECEIPT)["cohorts"]["exact8"],
    )


def test_r6_batch_qa_rejects_nfkc_and_whitespace_normalized_duplicate() -> None:
    batch = evaluate_reception_batch(
        "duplicate_negative_contract",
        (
            _synthetic_batch_case("one", "同じ　文です。"),
            _synthetic_batch_case("two", "同じ 文です！"),
        ),
        closing_hard_threshold=2,
    )

    assert batch.verdict == "failed"
    assert "r6_exact_reception_sentence_duplicate" in batch.reason_codes
    assert len(batch.duplicate_sentence_groups) == 1


def test_r6_batch_qa_rejects_four_case_common_closing_stem() -> None:
    shared = "違いを保ったまま受け止めています"
    receptions = (
        *(f"入口{i}から、{shared}。" for i in range(4)),
        "別の一件には、その重さをここで認めます。",
        "次の一件には、迷いごと返事を置きます。",
        "さらに一件には、今の歩幅を尊重します。",
        "最後の一件には、選んだ方向を応援します。",
    )
    batch = evaluate_reception_batch(
        "closing_negative_contract",
        tuple(
            _synthetic_batch_case(f"case{i}", reception)
            for i, reception in enumerate(receptions)
        ),
        closing_hard_threshold=4,
    )

    assert batch.verdict == "failed"
    assert "r6_closing_stem_concentration" in batch.reason_codes
    assert any(
        family["case_count"] >= 4
        and family["closing_stem_character_count"] >= 12
        for family in batch.closing_stem_families
    )


def test_r6_batch_qa_rejects_abstract_ending_majority() -> None:
    batch = evaluate_reception_batch(
        "abstract_negative_contract",
        (
            _synthetic_batch_case("one", "その努力を大切に受け取りました。"),
            _synthetic_batch_case("two", "その迷いとして届きました。"),
            _synthetic_batch_case("three", "その選択と受け取りました。"),
            _synthetic_batch_case("four", "その決断を私は応援します。"),
        ),
        closing_hard_threshold=4,
    )

    assert batch.verdict == "failed"
    assert "r6_abstract_ending_concentration" in batch.reason_codes
    assert batch.abstract_ending_union_count == 3


def test_r6_same16_keeps_semantics_and_passes_offline_repetition_qa() -> None:
    results = _same16_results()
    for _case_id, artifacts in results:
        _assert_all_reception_gates(artifacts[3])
    batch = evaluate_reception_batch(
        "same16_current",
        tuple(
            _batch_case(case_id, artifacts)
            for case_id, artifacts in results
        ),
        closing_hard_threshold=8,
    )
    family_counts = Counter(case.family for case in GROUND_OBSERVATION_I6_BLIND_CASES)

    assert len(results) == 16
    assert len({case_id for case_id, _artifacts in results}) == 16
    assert family_counts == Counter({family: 3 for family in I6_FAMILIES})
    assert batch.verdict == "passed"
    assert batch.duplicate_sentence_groups == ()
    assert batch.abstract_ending_union_count <= 8
    _assert_batch_receipt(
        batch,
        _load(_AUTOMATED_RECEIPT)["cohorts"]["same16"],
    )


def test_r6_unseen8_has_all_required_families_and_runtime_boundaries() -> None:
    fixture, results = _unseen8_results()
    required_families = {
        "short_burden",
        "positive_change",
        "retained_intention",
        "action_without_success",
        "long_arc",
        "comparison",
        "self_denial_with_counterevidence",
        "label_limited",
    }
    input_hashes = {
        _canonical_input_sha256(case["current_input"]) for case, _artifacts in results
    }

    assert fixture["local_only"] is True
    assert fixture["synthetic_inputs"] is True
    assert fixture["progression_authority"] == "none"
    assert len(results) == len(input_hashes) == 8
    assert {case["input_family"] for case, _artifacts in results} == required_families
    for case, artifacts in results:
        plan, _sentence_plan, _surface, report, _observation, reception = artifacts
        reception_plan = plan.response_plan.human_reception_plan
        assert reception_plan is not None
        _assert_all_reception_gates(report)
        assert plan.input_profile.material_quality == case[
            "expected_material_quality"
        ]
        assert plan.safety_policy.safety_kind == case["expected_safety_kind"]
        assert reception_plan.primary_reception_act == case[
            "expected_primary_reception_act"
        ]
        assert set(case["required_boundary_codes"]).issubset(
            reception_plan.safety_modifier_codes
        )
        assert _POLICY_RE.search(reception) is None

    batch = evaluate_reception_batch(
        "unseen8_synthetic_local",
        tuple(
            _batch_case(case["case_id"], artifacts)
            for case, artifacts in results
        ),
        closing_hard_threshold=4,
    )
    assert batch.verdict == "passed"
    assert batch.duplicate_sentence_groups == ()
    assert batch.abstract_ending_union_count <= 4
    _assert_batch_receipt(
        batch,
        _load(_AUTOMATED_RECEIPT)["cohorts"]["unseen8"],
    )


def test_r6_public_api_rn_boundary_stays_sanitized_and_shape_compatible() -> None:
    case = _load(_EXACT8_FIXTURE)["cases"][0]
    reply = asyncio.run(
        render_emlis_ai_reply(
            user_id="r6-public-boundary",
            subscription_tier="free",
            current_input=case["exact_current_input"],
        )
    )
    public = build_public_emlis_input_feedback_meta(
        reply.meta,
        comment_text_present=bool(reply.comment_text),
        subscription_tier="free",
    )
    payload = json.dumps(public, ensure_ascii=False, sort_keys=True)

    assert reply.comment_text
    assert reply.meta["public_observation_status"] == "passed"
    assert reply.meta["grounded_observation"][
        "runtime_reception_contract_guard"
    ] == "passed"
    assert public["schema_version"] == "emlis.public_input_feedback_meta.v1"
    assert public["observation_status"] == "passed"
    assert "grounded_observation" not in public
    assert not any(field_name in public for field_name in RECEPTION_GATE_REPORT_FIELDS)
    assert case["exact_current_input"]["memo"] not in payload
    assert reply.comment_text not in payload
    assert reply.meta["public_contract_changed"] is False
    assert reply.meta["api_route_changed"] is False
    assert reply.meta["db_physical_name_changed"] is False
    assert reply.meta["rn_visible_contract_changed"] is False


def test_r6_karen_read_is_visible_body_hash_bound_and_not_auto_inferred() -> None:
    packet = _load(_VISIBLE_PACKET)
    review_receipt = _load(_KAREN_RECEIPT)
    automated_receipt = _load(_AUTOMATED_RECEIPT)
    results = _exact8_results()
    result_by_id = {
        case["case_id"]: (case, artifacts) for case, artifacts in results
    }
    generated_by_id = {
        case_id: artifacts[2].text
        for case_id, (_case, artifacts) in result_by_id.items()
    }
    packet_by_id = {case["case_id"]: case for case in packet["cases"]}

    assert packet["local_only"] is True
    assert packet["review_scope"] == "exact8_visible_surface"
    assert packet["source_fixture_ref"] == (
        "../fixtures/grounded_human_reception_exact8_v2_20260712.json"
    )
    assert packet["source_fixture_sha256"] == hashlib.sha256(
        _EXACT8_FIXTURE.read_bytes()
    ).hexdigest()
    assert packet["source_snapshot_sha256"] == _SOURCE_SNAPSHOT_SHA256
    assert packet["case_order"] == list(result_by_id)
    assert set(packet_by_id) == set(generated_by_id)
    for case_id, generated_surface in generated_by_id.items():
        row = packet_by_id[case_id]
        case, artifacts = result_by_id[case_id]
        assert row["visible_surface"] == generated_surface
        assert row["visible_surface_sha256"] == sha256_text(generated_surface)
        assert row["current_input_sha256"] == _canonical_input_sha256(
            case["exact_current_input"]
        )
        assert row["observation_section_sha256"] == sha256_text(artifacts[4])
        assert row["reception_section_sha256"] == sha256_text(artifacts[5])
        assert row["automated_reception_gates"] == "passed"
        assert row["product_readfeel_status"] == "pending_human_read"

    packet_sha256 = hashlib.sha256(_VISIBLE_PACKET.read_bytes()).hexdigest()
    expected_surface_hashes = {
        case_id: sha256_text(surface)
        for case_id, surface in generated_by_id.items()
    }
    assert validate_karen_review_receipt(
        review_receipt,
        expected_surface_hashes=expected_surface_hashes,
        expected_packet_sha256=packet_sha256,
    ) == ()
    leaked_receipt = dict(review_receipt)
    leaked_receipt["raw_input_copy"] = "secret"
    assert "r6_karen_review_top_level_schema_mismatch" in (
        validate_karen_review_receipt(
            leaked_receipt,
            expected_surface_hashes=expected_surface_hashes,
            expected_packet_sha256=packet_sha256,
        )
    )
    assert review_receipt["review_axes"] == list(R6_REVIEW_AXES)
    assert review_receipt["product_readfeel_status"] == "human_pass"
    assert all(
        review["verdict"] == "human_pass"
        for review in review_receipt["reviews"]
    )
    assert automated_receipt["technical_acceptance"] == "passed"
    assert automated_receipt["source_snapshot_sha256"] == (
        packet["source_snapshot_sha256"]
    )
    assert automated_receipt["exact8_fixture_ref"] == _EXACT8_FIXTURE.name
    assert automated_receipt["exact8_fixture_sha256"] == hashlib.sha256(
        _EXACT8_FIXTURE.read_bytes()
    ).hexdigest()
    assert automated_receipt["unseen8_fixture_ref"] == (
        "../local_only/grounded_human_reception_r6_unseen8_20260712.json"
    )
    assert automated_receipt["unseen8_fixture_sha256"] == hashlib.sha256(
        _UNSEEN8_FIXTURE.read_bytes()
    ).hexdigest()
    assert automated_receipt["automated_qa_order"] == [
        "type_and_unit",
        "plan_contract",
        "sentence_plan_validation",
        "surface",
        "runtime_gate",
        "exact8",
        "same16",
        "unseen8",
        "public_api_rn_boundary",
        "targeted_compile",
        "relevant_backend_regression",
    ]
    assert set(automated_receipt["automated_qa_order_status"].values()) == {
        "passed"
    }
    local_execution = automated_receipt["local_test_execution"]
    assert local_execution["r0_through_r6_contract_test_count"] == 67
    assert local_execution["r0_through_r6_contract_test_file_count"] == 7
    assert local_execution["relevant_backend_regression_test_count"] == 342
    assert local_execution["relevant_backend_regression_test_file_count"] == 22
    assert len(local_execution["relevant_backend_regression_test_files"]) == 22
    assert local_execution["failed_test_count"] == 0
    assert automated_receipt["product_readfeel_status"] == "separate_human_receipt"
    assert automated_receipt["human_review_receipt_ref"] == _KAREN_RECEIPT.name
    assert automated_receipt["human_review_receipt_sha256"] == hashlib.sha256(
        _KAREN_RECEIPT.read_bytes()
    ).hexdigest()
    assert automated_receipt["technical_pass_is_product_readfeel_pass"] is False
    assert all(artifacts[3].product_readfeel_status == "not_evaluated" for _case, artifacts in results)


def test_r6_karen_receipt_rejects_duplicate_review_row() -> None:
    receipt = _load(_KAREN_RECEIPT)
    packet_sha256 = hashlib.sha256(_VISIBLE_PACKET.read_bytes()).hexdigest()
    expected_surface_hashes = {
        row["case_id"]: row["visible_surface_sha256"]
        for row in _load(_VISIBLE_PACKET)["cases"]
    }
    receipt["reviews"].append(deepcopy(receipt["reviews"][0]))

    issues = validate_karen_review_receipt(
        receipt,
        expected_surface_hashes=expected_surface_hashes,
        expected_packet_sha256=packet_sha256,
    )

    assert "r6_karen_review_row_count_mismatch" in issues
    assert "r6_karen_review_case_id_duplicate" in issues


@pytest.mark.parametrize(
    ("field_name", "invalid_value", "expected_issue"),
    [
        (
            "automatic_gate_result_used_as_human_result",
            True,
            "r6_karen_review_automatic_result_boundary_missing",
        ),
        (
            "progression_authority",
            "granted",
            "r6_karen_review_progression_authority_invalid",
        ),
        (
            "valid_for_progression",
            True,
            "r6_karen_review_progression_validity_invalid",
        ),
        (
            "product_readfeel_status",
            "garbage",
            "r6_karen_review_aggregate_pass_invalid",
        ),
        (
            "review_axes",
            [],
            "r6_karen_review_axis_contract_mismatch",
        ),
    ],
)
def test_r6_karen_receipt_rejects_invalid_boundary_values(
    field_name: str,
    invalid_value,
    expected_issue: str,
) -> None:
    receipt = _load(_KAREN_RECEIPT)
    receipt[field_name] = invalid_value
    packet_sha256 = hashlib.sha256(_VISIBLE_PACKET.read_bytes()).hexdigest()
    expected_surface_hashes = {
        row["case_id"]: row["visible_surface_sha256"]
        for row in _load(_VISIBLE_PACKET)["cases"]
    }

    issues = validate_karen_review_receipt(
        receipt,
        expected_surface_hashes=expected_surface_hashes,
        expected_packet_sha256=packet_sha256,
    )

    assert expected_issue in issues
