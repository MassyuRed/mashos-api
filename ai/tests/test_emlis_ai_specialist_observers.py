from __future__ import annotations

from emlis_ai_evidence_ledger_service import build_evidence_ledger
from emlis_ai_perspective_observers import SPECIALIST_OBSERVER_IDS, phase4_observer_contract_ready, run_perspective_observers
from emlis_ai_types import PerspectiveReport


SAMPLE_MEMO = """
誰かと繋がっていたい気持ちもあるけど、ひとりで静かに過ごしたい気持ちもある。
人と関わると気を使いすぎて疲れるし、でも完全に離れると寂しくなる。
自分でもどうしたいのか分からなくなる。
"""


def _current_input(memo: str = SAMPLE_MEMO):
    return {
        "id": "phase4-test",
        "created_at": "2026-05-10T00:00:00Z",
        "memo": memo,
        "memo_action": "",
        "emotion_details": [{"type": "自己理解", "strength": "medium"}],
        "emotions": ["自己理解"],
        "category": ["人間関係"],
    }


def test_phase4_specialist_observers_return_structured_reports_only():
    evidence = build_evidence_ledger(_current_input())
    reports = run_perspective_observers(evidence)

    assert [report.observer_id for report in reports] == list(SPECIALIST_OBSERVER_IDS)
    assert all(isinstance(report, PerspectiveReport) for report in reports)
    assert phase4_observer_contract_ready(reports, evidence) is True

    banned_surface_fragments = [
        "Emlisです",
        "さんは",
        "見ています",
        "受け取りました",
        "一緒に見ます",
        "小さく扱いません",
        "軽く扱いません",
        "そこには",
    ]
    for report in reports:
        assert hasattr(report, "claims")
        assert hasattr(report, "relations")
        assert hasattr(report, "evidence_span_ids")
        for claim in report.claims:
            # Observer objects may carry raw user words as evidence-linked claim
            # objects, but they must not contain completed Emlis observation text.
            claim_surface = str(claim.object or "")
            for banned in banned_surface_fragments:
                assert banned not in claim_surface


def test_phase4_conflict_observer_builds_relation_edges_from_evidence():
    evidence = build_evidence_ledger(_current_input())
    reports = run_perspective_observers(evidence)
    conflict = next(report for report in reports if report.observer_id == "conflict_coexistence")

    evidence_ids = {span.span_id for span in evidence}
    claim_ids = {claim.claim_id for claim in conflict.claims}

    assert conflict.claims
    assert conflict.relations
    assert any(edge.relation_type in {"tension", "coexistence", "explicit_transition", "limit_tension"} for edge in conflict.relations)
    for edge in conflict.relations:
        assert edge.from_claim_id in claim_ids
        assert edge.to_claim_id in claim_ids
        assert edge.evidence_span_ids
        assert set(edge.evidence_span_ids) <= evidence_ids


def test_phase4_safety_observer_marks_safety_boundary_without_normal_observation_text():
    evidence = build_evidence_ledger(_current_input("消えたい気持ちが強い。もう無理。"))
    reports = run_perspective_observers(evidence)
    safety = next(report for report in reports if report.observer_id == "safety_boundary")

    assert safety.claims
    assert all(claim.claim_type == "safety_boundary" for claim in safety.claims)
    assert all(claim.risk_level == "high" for claim in safety.claims)
    assert phase4_observer_contract_ready(reports, evidence) is True


def test_phase4_empty_viewpoints_still_report_uncertainty_instead_of_text():
    evidence = build_evidence_ledger(_current_input("今日は少し眠い。"))
    reports = run_perspective_observers(evidence)
    safety = next(report for report in reports if report.observer_id == "safety_boundary")

    assert safety.claims == []
    assert safety.relations == []
    assert "no_safety_boundary_evidence" in safety.uncertainty
