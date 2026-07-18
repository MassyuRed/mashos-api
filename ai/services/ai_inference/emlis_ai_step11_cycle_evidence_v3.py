# -*- coding: utf-8 -*-
from __future__ import annotations

"""Closed, body-free evidence owner for NLS v3 Step 11 Cycle 001.

The frozen Step 10 summary remains a Step 10 smoke artifact.  Step 11 may lock
that exact historical result, including machine failures, but never rewrites or
relabels it.  A text-affecting successor uses the independent Step 11 batch and
case-receipt schemas declared here.

All acceptance aggregates are rebuilt from exact parent artifacts.  Raw input,
visible response bytes, review prose, commitment secrets, and permissive free
text are outside this owner.
"""

from collections import Counter
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_step10_dependency_manifest_v3 import (
    FROZEN_STEP10_CANDIDATE_VERSION_ID,
    FROZEN_STEP10_DEPENDENCY_CLOSURE_SHA256,
    FROZEN_STEP10_MANIFEST_SHA256,
)
from emlis_ai_step10_evidence_v3 import (
    COMMITMENT_POLICY_SHA256,
    FAILURE_TAXONOMY_SHA256,
    HARD_GATE_FAILURE_CODES,
    LOCAL_REVIEW_AXES,
    LOCAL_REVIEW_FAILURE_CODES,
    LOCAL_REVIEW_PASS_CODES,
    RUNNER_CASE_FAILURE_CODES,
    assert_body_free,
    validate_historical_batch_run_summary,
)


STEP11_CYCLE_ID = "cycle_001"
STEP11_BATCH_ID = "nls3_batch_001"
STEP11_INITIAL_CANDIDATE_VERSION_ID = FROZEN_STEP10_CANDIDATE_VERSION_ID
STEP11_HISTORICAL_RC0019_CANDIDATE_VERSION_ID = "nls_v3_rc_0019"
# Compatibility name retained for frozen rc0020 evidence only.  Current code
# must use the explicit STEP11_CURRENT_CANDIDATE_VERSION_ID frontier below.
STEP11_SUCCESSOR_CANDIDATE_VERSION_ID = "nls_v3_rc_0020"
STEP11_HISTORICAL_RC0020_CANDIDATE_VERSION_ID = (
    STEP11_SUCCESSOR_CANDIDATE_VERSION_ID
)
STEP11_HISTORICAL_RC0021_CANDIDATE_VERSION_ID = "nls_v3_rc_0021"
STEP11_HISTORICAL_RC0022_CANDIDATE_VERSION_ID = "nls_v3_rc_0022"
STEP11_HISTORICAL_RC0023_CANDIDATE_VERSION_ID = "nls_v3_rc_0023"
STEP11_CURRENT_CANDIDATE_VERSION_ID = "nls_v3_rc_0024"

# Exact body-free rc0020 preflight parents.  They are historical observations,
# never rc0021 defaults and never evidence that rc0020 passed Product Read.
FROZEN_RC0020_PREFLIGHT_MANIFEST_ARTIFACT_SHA256 = (
    "4158d90674478eaa3b5f24c33cb15d35fea65c418cf128eaf8f42123c52e0e4f"
)
FROZEN_RC0020_PREFLIGHT_SOURCE_CLOSURE_SHA256 = (
    "17194929e3a4005aaeb74ca8d01277dd3978023cabb37d099e34d4cfcbaff4d1"
)
FROZEN_RC0020_PREFLIGHT_BATCH_SUMMARY_SHA256 = (
    "719cdacac4492e911502c7b25d46cf50815599825bad6eeaf7208be83e1b3193"
)
FROZEN_RC0020_PREFLIGHT_PRIVATE_VERIFICATION_SHA256 = (
    "bcf12d73d771ece8de5b1175267131aa05fa2f6f62f7efcf9d73b9840c5d5bb6"
)

# Exact body-free rc0021 preflight parents.  The Product Read failure is a
# later observation over these immutable machine-clean artifacts; it never
# relabels their machine outcome and never carries private key material.
FROZEN_RC0021_PREFLIGHT_MANIFEST_ARTIFACT_SHA256 = (
    "b4b2e0b743f3bc5750818bcc352474a303721bb90ee75eebeb13796fe2ce18e4"
)
FROZEN_RC0021_PREFLIGHT_SOURCE_CLOSURE_SHA256 = (
    "612939ef04f90e82e67ae015715d3a5e508aa217effd4a988dee542ba3428cee"
)
FROZEN_RC0021_PREFLIGHT_BATCH_SUMMARY_SHA256 = (
    "e30c1d6adb83a0428a1ebae0e4373edb44ab5122edba77aca4bdadcb11907e4b"
)
FROZEN_RC0021_PREFLIGHT_PRIVATE_VERIFICATION_SHA256 = (
    "111c9212cd67ba191b5f3116d92fcd5c2a3b70c4a28de5eb85e827954b2b96ff"
)

# Exact body-free rc0022 formal-run parents.  This execution completed all
# 100 cases but failed closed: evidence construction rejected 95 selected
# results and the remaining five cases had no valid candidate.  These bytes
# are immutable failure evidence, never an accepted rc0022 result.
FROZEN_RC0022_FORMAL_MANIFEST_ARTIFACT_SHA256 = (
    "a6f691e09b20c31302a30b239b255fa302dd1d94892fedc894d6c45fd36274df"
)
FROZEN_RC0022_FORMAL_SOURCE_CLOSURE_SHA256 = (
    "252b83e41b9f77e3ffb38041471f00a22946443119dff3c26524230ac60b1783"
)
FROZEN_RC0022_FORMAL_BATCH_SUMMARY_SHA256 = (
    "7db9feeb6b7d6a41f54ce0d7a27bb3fbafade2cd60f0c5f89745172d8f5f5c06"
)
FROZEN_RC0022_FORMAL_PRIVATE_VERIFICATION_SHA256 = (
    "ab12f6e1d437f7ab3d04093c08873c5d65141061a45d7836284a90ff79095a87"
)

# Exact body-free rc0023 formal-run parents.  The machine run was clean and
# remains immutable even though the later Known28 regression aborted before a
# durable receipt could be produced.  rc0024 is an immediate source successor;
# it never relabels this formal execution as failed.
FROZEN_RC0023_FORMAL_MANIFEST_ARTIFACT_SHA256 = (
    "c98ffd8fd6da6e74d7811d5ee272bc469321e36f03d3c48b711a15095218b57e"
)
FROZEN_RC0023_FORMAL_SOURCE_CLOSURE_SHA256 = (
    "83c220fa71f4d22549e94b9733918892a3c532367aa4075f268e1bb3eca48e92"
)
FROZEN_RC0023_FORMAL_BATCH_SUMMARY_SHA256 = (
    "d5edd618b53a488de53ad2ffb4ca5f6c4e0b4eff634d7639dc023fc7dbec9c57"
)
FROZEN_RC0023_FORMAL_PRIVATE_VERIFICATION_SHA256 = (
    "26747b6166babceadc23c51ef67f8b53abdb60b7af4a4c565aaa6052d63c051e"
)

FROZEN_BATCH001_MANIFEST_SHA256 = (
    "2b3308c4ada090539a2fc71c1cb235970aa0b90687b8d9633464ba61e94deba4"
)
FROZEN_BATCH001_MATRIX_SHA256 = (
    "4ea17d30ebdf624b374591f5ea9dde7240455a3a833c691d4a2a6e77d5649e5f"
)
FROZEN_BATCH001_DUPLICATE_REPORT_SHA256 = (
    "140e17311d84ae275ca90d3e93f1aafdfcd667f7bbaaacd92a729df550676354"
)
FROZEN_BATCH001_MANIFEST_ARTIFACT_SHA256 = (
    "9d3164d1f62e11d243c205341eef433512b8344edb4cea5ed6bc1824d013341a"
)
FROZEN_BATCH001_MATRIX_ARTIFACT_SHA256 = (
    "014944d64a39c7fc479d3dfd004fe968dcde8d02df0b12c3a9a2272cd468a6f4"
)
FROZEN_BATCH001_DUPLICATE_REPORT_ARTIFACT_SHA256 = (
    "fa5ce696bac955bffdee64f4b829467c68f1485787da3a91396d9a09345f3a34"
)
FROZEN_BATCH001_CORPUS_SHA256 = (
    "013dd2ad1c1f446f843f400b3eb16231e8f32649e30114e70039b4cb709e8414"
)
FROZEN_INVALID16_FILE_SHA256 = (
    "d7cbc344701635d53da21ebb2814a9c8d814cf1c403392b506ece6c00e6e5b77"
)
FROZEN_VALIDATOR_POLICY_SHA256 = (
    "cca85dafcf338637e2338e47306ce4b4c9c7ad18c98ae1bd89935313cc8c7d39"
)

CORPUS_VALIDATION_SCHEMA = "cocolon.emlis.nls_v3.cycle001_corpus_validation.v1"
STEP11_DEPENDENCY_MANIFEST_SCHEMA = (
    "cocolon.emlis.nls_v3.step11_dependency_manifest.v1"
)
STEP11_CASE_RECEIPT_SCHEMA = "cocolon.emlis.nls_v3.case_evidence_receipt.step11.v1"
STEP11_BATCH_RUN_SCHEMA = "cocolon.emlis.nls_v3.batch_run_receipt.step11.v2"
# Historical generic alias used only by the frozen rc0020 validators.
STEP11_SURFACE_DISTRIBUTION_ASSESSMENT_SCHEMA = (
    "cocolon.emlis.nls_v3.surface_distribution_assessment.step11.rc0020.v1"
)
STEP11_PRIVATE_VERIFICATION_RECEIPT_SCHEMA = (
    "cocolon.emlis.nls_v3.private_verification_receipt.step11.v1"
)
INITIAL_RUN_LOCK_SCHEMA = "cocolon.emlis.nls_v3.initial_run_lock.v2"
LOCAL_REVIEW_SET_SCHEMA = "cocolon.emlis.nls_v3.local_review_set.v2"
OUTPUT_DIFF_SCHEMA = "cocolon.emlis.nls_v3.output_diff.step11.v1"
OUTPUT_CHANGE_REVIEW_SCHEMA = "cocolon.emlis.nls_v3.output_change_review.v2"
KNOWN28_RECEIPT_SCHEMA = "cocolon.emlis.nls_v3.known28_receipt.v3"
DEVELOPMENT42_RECEIPT_SCHEMA = (
    "cocolon.emlis.nls_v3.development42_receipt.step11.v1"
)
INVALID16_RECEIPT_SCHEMA = "cocolon.emlis.nls_v3.invalid16_receipt.v2"
WORKAROUND_SCAN_SCHEMA = "cocolon.emlis.nls_v3.case_specific_workaround_scan.v1"
CUMULATIVE100_RECEIPT_SCHEMA = "cocolon.emlis.nls_v3.cumulative100_receipt.v4"
CYCLE_CHANGE_LEDGER_SCHEMA = "cocolon.emlis.nls_v3.cycle_change_ledger.v3"
CYCLE_CHANGE_ROW_SCHEMA = "cocolon.emlis.nls_v3.cycle_change_row.v3"
CYCLE_ACCEPTANCE_SCHEMA = "cocolon.emlis.nls_v3.cycle_acceptance.v6"
RC_CORRECTION_RERUN_LINEAGE_V1_SCHEMA = (
    "cocolon.emlis.nls_v3.rc_correction_rerun_lineage.step11.v1"
)
RC_CORRECTION_RERUN_LINEAGE_EVENT_V1_SCHEMA = (
    "cocolon.emlis.nls_v3.rc_correction_rerun_lineage_event.step11.v1"
)
RC_CORRECTION_RERUN_LINEAGE_SCHEMA = (
    "cocolon.emlis.nls_v3.rc_correction_rerun_lineage.step11.v2"
)
RC_CORRECTION_RERUN_LINEAGE_EVENT_SCHEMA = (
    "cocolon.emlis.nls_v3.rc_correction_rerun_lineage_event.step11.v2"
)
RC_CORRECTION_RERUN_LINEAGE_V3_SCHEMA = (
    "cocolon.emlis.nls_v3.rc_correction_rerun_lineage.step11.v3"
)
RC_CORRECTION_RERUN_LINEAGE_EVENT_V3_SCHEMA = (
    "cocolon.emlis.nls_v3.rc_correction_rerun_lineage_event.step11.v3"
)
RC_CORRECTION_RERUN_LINEAGE_V4_SCHEMA = (
    "cocolon.emlis.nls_v3.rc_correction_rerun_lineage.step11.v4"
)
RC_CORRECTION_RERUN_LINEAGE_EVENT_V4_SCHEMA = (
    "cocolon.emlis.nls_v3.rc_correction_rerun_lineage_event.step11.v4"
)
RC_CORRECTION_RERUN_LINEAGE_V5_SCHEMA = (
    "cocolon.emlis.nls_v3.rc_correction_rerun_lineage.step11.v5"
)
RC_CORRECTION_RERUN_LINEAGE_EVENT_V5_SCHEMA = (
    "cocolon.emlis.nls_v3.rc_correction_rerun_lineage_event.step11.v5"
)
RC_CORRECTION_RERUN_LINEAGE_V6_SCHEMA = (
    "cocolon.emlis.nls_v3.rc_correction_rerun_lineage.step11.v6"
)
RC_CORRECTION_RERUN_LINEAGE_EVENT_V6_SCHEMA = (
    "cocolon.emlis.nls_v3.rc_correction_rerun_lineage_event.step11.v6"
)
STEP11_RC0021_SURFACE_DISTRIBUTION_ASSESSMENT_SCHEMA = (
    "cocolon.emlis.nls_v3.surface_distribution_assessment.step11.rc0021.v1"
)
STEP11_RC0021_AVAILABLE_INPUT_SCOPE_RECEIPT_SCHEMA = (
    "cocolon.emlis.nls_v3.available_input_scope_receipt.step11.rc0021.v1"
)
STEP11_RC0022_SURFACE_DISTRIBUTION_ASSESSMENT_SCHEMA = (
    "cocolon.emlis.nls_v3.surface_distribution_assessment.step11.rc0022.v1"
)
STEP11_RC0022_AVAILABLE_INPUT_SCOPE_RECEIPT_SCHEMA = (
    "cocolon.emlis.nls_v3.available_input_scope_receipt.step11.rc0022.v1"
)
STEP11_RC0023_SURFACE_DISTRIBUTION_ASSESSMENT_SCHEMA = (
    "cocolon.emlis.nls_v3.surface_distribution_assessment.step11.rc0023.v1"
)
STEP11_RC0023_AVAILABLE_INPUT_SCOPE_RECEIPT_SCHEMA = (
    "cocolon.emlis.nls_v3.available_input_scope_receipt.step11.rc0023.v1"
)
STEP11_RC0024_SURFACE_DISTRIBUTION_ASSESSMENT_SCHEMA = (
    "cocolon.emlis.nls_v3.surface_distribution_assessment.step11.rc0024.v1"
)
STEP11_RC0024_AVAILABLE_INPUT_SCOPE_RECEIPT_SCHEMA = (
    "cocolon.emlis.nls_v3.available_input_scope_receipt.step11.rc0024.v1"
)
# Historical generic alias used only by the frozen rc0020 evidence graph.
AVAILABLE_INPUT_SCOPE_RECEIPT_SCHEMA = (
    "cocolon.emlis.nls_v3.available_input_scope_receipt.step11.rc0020.v1"
)
FROZEN_AVAILABLE_INPUT_SCOPE_RECEIPT_SHA256 = (
    "743fbd375184d3e51351492572a5aabdc5233ade710138b6f0f58101c956346f"
)
FROZEN_RC0019_AVAILABLE_INPUT_SCOPE_RECEIPT_SHA256 = (
    "ab8fa72c2ae39a60daef421dc284e0104033ac2a435282fefee8c7f479a89fae"
)
FROZEN_DEVELOPMENT42_SOURCE_FILE_SHA256 = (
    "9e8e81b553b8f3d5d51e66c434350ebbc2fa134a813250dbb5bc5de251e6aa36"
)
FROZEN_DEVELOPMENT42_LOADER_SHA256 = (
    "cf29cbebceea3c4489adc00bb7744aa0c29b43a1376cd9d5ce2809aa0f58f140"
)
FROZEN_DEVELOPMENT42_EXPECTED_APPLICABILITY_SHA256 = (
    "080972e62ff982014e8b4198294d3d5e713fe1621cb3619e2f9f22e70276d407"
)

STEP11_SURFACE_DISTRIBUTION_POLICY = {
    "global_selected_profile_count_required": 100,
    "global_opening_minimum_distinct_variant_count": 3,
    "global_opening_maximum_dominant_share_numerator": 1,
    "global_opening_maximum_dominant_share_denominator": 2,
    "global_ending_minimum_distinct_variant_count": 3,
    "global_ending_maximum_dominant_share_numerator": 1,
    "global_ending_maximum_dominant_share_denominator": 2,
    "global_skeleton_maximum_dominant_share_numerator": 1,
    "global_skeleton_maximum_dominant_share_denominator": 2,
    "semantic_family_evaluation_minimum_case_count": 2,
    "semantic_family_minimum_distinct_variant_count": 2,
    "semantic_family_maximum_dominant_share_numerator": 3,
    "semantic_family_maximum_dominant_share_denominator": 4,
    "singleton_semantic_family_disposition": "recorded_not_failed",
    "exact_output_duplicate_case_count_maximum": 0,
    "literal_replay_case_count_maximum": 0,
    "owned_antecedent_direct_reception_count_maximum": 0,
}
FROZEN_STEP11_SURFACE_DISTRIBUTION_POLICY_SHA256 = (
    "a9beec6ef835917987f118759711006a6b957cc89ca5b8bba73a5e729d2df62c"
)
STEP11_SURFACE_DISTRIBUTION_POLICY_SHA256 = artifact_sha256(
    STEP11_SURFACE_DISTRIBUTION_POLICY
)

STEP11_RUNTIME_ADAPTER_VERSION = (
    "cocolon.emlis.nls_v3.runtime_adapter.step11.rc0024.v1"
)
STEP11_HISTORICAL_RC0023_RUNTIME_ADAPTER_VERSION = (
    "cocolon.emlis.nls_v3.runtime_adapter.step11.rc0023.v1"
)
STEP11_HISTORICAL_RC0022_RUNTIME_ADAPTER_VERSION = (
    "cocolon.emlis.nls_v3.runtime_adapter.step11.rc0022.v1"
)
STEP11_HISTORICAL_RC0021_RUNTIME_ADAPTER_VERSION = (
    "cocolon.emlis.nls_v3.runtime_adapter.step11.rc0021.v1"
)
STEP11_HISTORICAL_RC0020_RUNTIME_ADAPTER_VERSION = (
    "cocolon.emlis.nls_v3.runtime_adapter.step11.rc0020.v1"
)
STEP11_EXECUTION_AUTHORITY = "step11_cycle001_cumulative_rerun"
STEP11_COMMITMENT_POLICY_SHA256 = COMMITMENT_POLICY_SHA256
STEP11_RUNTIME_VALIDATION_PROTOCOL = {
    "schema_version": "cocolon.emlis.nls_v3.runtime_validation_protocol.step11.v1",
    "execution_scope": "offline_batch",
    "production_route_activation": False,
    "source_lineage_recomputed": True,
    "independent_body_parser_matcher": True,
    "hard_gate_required_before_selection": True,
    "verified_renderer_bytes_preserved": True,
    "v1_fallback_counts_as_v3_success": False,
    "private_body_full_and_body_free_separate": True,
    "aggregate_source": "case_rows_only",
}
STEP11_RUNTIME_VALIDATION_PROTOCOL_SHA256 = artifact_sha256(
    STEP11_RUNTIME_VALIDATION_PROTOCOL
)

_SHA_RE = re.compile(r"^[0-9a-f]{64}$")
_RUN_RE = re.compile(r"^nls3run_[0-9a-f]{16,64}$")
_CUM_RE = re.compile(r"^nls3cum_[0-9a-f]{16,64}$")
_LOCK_RE = re.compile(r"^nls3lock_[0-9a-f]{16,64}$")
_RC_RE = re.compile(r"^nls_v3_rc_([0-9]{4})$")
_CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,95}$")
_ISSUE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:\[\]-]{2,127}$")
_LOWER_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
_SAFE_PATH_RE = re.compile(r"^ai/[A-Za-z0-9_./-]{1,240}$")


def _runtime_adapter_version_for_candidate(candidate_version_id: str) -> str:
    match = _RC_RE.fullmatch(candidate_version_id)
    if match is None:
        raise Step11CycleEvidenceError("STEP11_CANDIDATE_VERSION_INVALID")
    return (
        "cocolon.emlis.nls_v3.runtime_adapter.step11."
        f"rc{match.group(1)}.v1"
    )


def _surface_distribution_schema_for_candidate(
    candidate_version_id: str,
) -> str:
    match = _RC_RE.fullmatch(candidate_version_id)
    if match is None:
        raise Step11CycleEvidenceError("STEP11_CANDIDATE_VERSION_INVALID")
    return (
        "cocolon.emlis.nls_v3.surface_distribution_assessment.step11."
        f"rc{match.group(1)}.v1"
    )

_RC0010_RC0019_SEQUENCE = tuple(
    f"nls_v3_rc_{number:04d}" for number in range(10, 20)
)
_RC0010_RC0020_SEQUENCE = tuple(
    f"nls_v3_rc_{number:04d}" for number in range(10, 21)
)
_RC0010_RC0021_SEQUENCE = tuple(
    f"nls_v3_rc_{number:04d}" for number in range(10, 22)
)
_RC0010_RC0022_SEQUENCE = tuple(
    f"nls_v3_rc_{number:04d}" for number in range(10, 23)
)
_RC0010_RC0023_SEQUENCE = tuple(
    f"nls_v3_rc_{number:04d}" for number in range(10, 24)
)
_RC0010_RC0024_SEQUENCE = tuple(
    f"nls_v3_rc_{number:04d}" for number in range(10, 25)
)
_RC0020_FROZEN_HISTORICAL_BATCH_SUMMARY_SHA256 = (
    (
        "nls_v3_rc_0014",
        "d8e06c4247154289cd6cf1b8501435962f8e2077e835802f827cf767e153d7ae",
    ),
    (
        "nls_v3_rc_0015",
        "d1f9ac975cc5b5e79a0b19f2bc19776b30e7260a73dd0fe03e97107e082aed80",
    ),
    (
        "nls_v3_rc_0016",
        "a879aeacee818081921b1d81a52c3b6922b67dd6c9dbf21558e7d4f783104a46",
    ),
    (
        "nls_v3_rc_0018",
        "925d4ec6000f6651b60fcf53266b9777517d88a7235670466263b36deb2dfd20",
    ),
    (
        "nls_v3_rc_0019",
        "265500f48a4eb7fbffa0c24b3f16fdb0f2ed4486505a6085a121daf3ad54ea26",
    ),
)
_LINEAGE_CORRECTION_SOURCE_KINDS = frozenset(
    {
        "dependency_manifest",
        "historical_unfrozen_no_receipt",
        "working_state_unfrozen",
    }
)
_LINEAGE_EXECUTION_SCOPES = frozenset(
    {"formal_cumulative_rerun", "preflight"}
)
_LINEAGE_DISPOSITIONS = frozenset(
    {
        "cycle_final_candidate",
        "current_pending_rerun",
        "historical_unfrozen_no_receipt",
        "superseded_after_observed_result",
        "superseded_unexecuted",
    }
)
_LINEAGE_PRODUCT_READ_OUTCOMES = frozenset({"failed", "passed"})
_LINEAGE_PRODUCT_READ_SEVERITIES = frozenset(
    {"NONE", "MINOR", "MAJOR", "BLOCKER"}
)

_DEVELOPMENT42_CASE_IDS = tuple(
    f"NLS2-F{family:02d}-D{depth:02d}"
    for family in range(1, 15)
    for depth in range(1, 4)
)
_DEVELOPMENT42_NONAPP_ISSUES = {
    **{
        f"NLS2-F02-D{depth:02d}": (
            "input:thought_action_both_empty_after_js_trim",
        )
        for depth in range(1, 4)
    },
    **{
        case_id: ("input.emotions:self_insight_must_be_exclusive",)
        for case_id in (
            "NLS2-F09-D01",
            "NLS2-F09-D02",
            "NLS2-F09-D03",
            "NLS2-F10-D01",
            "NLS2-F10-D03",
            "NLS2-F11-D03",
            "NLS2-F12-D01",
            "NLS2-F12-D02",
            "NLS2-F12-D03",
            "NLS2-F14-D01",
            "NLS2-F14-D02",
            "NLS2-F14-D03",
        )
    },
    "NLS2-F13-D01": ("input:thought_action_both_empty_after_js_trim",),
    "NLS2-F13-D02": ("input:thought_action_both_empty_after_js_trim",),
    "NLS2-F13-D03": (
        "input:thought_action_both_empty_after_js_trim",
        "input.emotions:self_insight_must_be_exclusive",
    ),
}

_CASE_IDS = tuple(f"nls3s_b001_{index:04d}" for index in range(1, 101))
_CASE_ID_SET = frozenset(_CASE_IDS)
_REVIEW_STAGES = frozenset({"initial", "final"})
_SEVERITIES = frozenset({"BLOCKER", "MAJOR", "MINOR", "NOTE"})
_BLOCKING_SEVERITIES = frozenset({"BLOCKER", "MAJOR"})
_BATCH_STATUSES = frozenset({"selected", "v3_no_valid_candidate", "exception"})
_FAILURE_LAYERS = frozenset(
    {
        "source",
        "obligation",
        "content",
        "discourse",
        "ast",
        "renderer",
        "parser",
        "matcher",
        "hard_gate",
        "selector",
        "runtime",
        "evidence",
    }
)
_CHANGE_REGRESSION_RISK_CODES = frozenset(
    {
        "BODY_PARSER_DIVERGENCE",
        "NATURALNESS_REGRESSION",
        "RELATION_DIRECTION_REGRESSION",
        "SELF_DENIAL_SCOPE_REGRESSION",
        "SEMANTIC_COVERAGE_REGRESSION",
        "UNKNOWN_BOUNDARY_REGRESSION",
    }
)
_CHANGE_NEGATIVE_TEST_IDS = frozenset(
    {
        "case_id_override_lookup",
        "forged_candidate_without_ast",
        "noncanonical_body_mutation",
        "relation_scoped_unknown_rejects_partial_antecedent",
        "removing_exact_action_denial_fails_closed",
        "surplus_semantic_atom",
        "typed_unknown_generic_substitution",
        "unbound_denial_injection_is_surplus",
    }
)


def _valid_change_negative_test_ids(value: Any) -> bool:
    return type(value) is list and value == sorted(_CHANGE_NEGATIVE_TEST_IDS)
_STEP11_SECURITY_TEST_PATH = (
    "ai/tests/test_emlis_nls_v3_s11_hard_gate_security.py"
)
_STRUCTURAL_CAUSE_CODES = frozenset(
    {
        "discourse_depth_selection_mismatch",
        "false_understanding_completion_not_prevented",
        "internal_surface_abstraction_leak",
        "reception_not_bound_to_observation",
        "relation_endpoint_direction_mismatch",
        "required_obligation_not_realised",
        "runtime_execution_failed",
        "runtime_response_missing",
        "section_semantic_distinctness_lost",
        "selector_no_valid_candidate",
        "self_denial_boundary_not_preserved",
        "source_nucleus_not_surface_bound",
        "surface_family_selection_collapse",
        "unknown_boundary_not_preserved",
        "unsupported_inference_not_filtered",
    }
)
_CORRECTION_STRATEGY_CODES = frozenset(
    {
        "bind_reception_to_source_nucleus",
        "prevent_false_understanding_completion",
        "preserve_self_denial_source_scope",
        "preserve_relation_endpoints_direction",
        "preserve_unknown_boundary_scope",
        "realise_required_obligations",
        "rebalance_surface_family_selection",
        "reject_unsupported_semantic_atom",
        "render_exact_source_nuclei_naturally",
        "restore_candidate_selection_path",
        "restore_runtime_response_delivery",
        "retain_source_nucleus_observation",
        "select_proportional_discourse_depth",
        "separate_section_semantic_contributions",
        "stabilize_runtime_execution",
    }
)
_STEP11_RUNNER_FAILURE_CODES = frozenset(
    set(RUNNER_CASE_FAILURE_CODES)
    | {
        "STEP11_CASE_EXECUTION_REJECTED",
        "STEP11_EVIDENCE_BUILD_REJECTED",
    }
)
_STEP11_HARD_GATE_FAILURE_CODES = frozenset(
    {
        "S11_GATE01_ARTIFACT_SCHEMA_PARENT_HASH",
        "S11_GATE02_VERSION_DEPENDENCY",
        "S11_GATE03_CANONICAL_RENDER_EQUALITY",
        "S11_GATE04_BODY_PARSEABILITY",
        "S11_GATE05_EVIDENCE_RESOLUTION",
        "S11_GATE06_REQUIRED_OBLIGATION_COVERAGE",
        "S11_GATE07_BOUND_RECEPTION",
        "S11_GATE08_POLARITY_MODALITY_TIME",
        "S11_GATE09_RELATION_TYPE_DIRECTION",
        "S11_GATE10_REFERENT_TOPIC",
        "S11_GATE11_UNKNOWN_BOUNDARY",
        "S11_GATE12_SELF_DENIAL",
        "S11_GATE13_UNSUPPORTED_CLAIM",
        "S11_GATE14_SECTION_DISTINCTNESS",
        "S11_GATE15_INPUT_ENUMERATION",
        "S11_GATE16_CONTRIBUTION_DISTINCTNESS",
        "S11_GATE17_DEPTH",
        "S11_GATE18_SURFACE_INTEGRITY",
        "S11_GATE19_NAMING_ADDRESS",
        "S11_GATE20_BODY_FREE_PUBLIC_CONTRACT",
    }
)
_STEP11_REVIEW_FAILURE_CODES = frozenset(
    set(LOCAL_REVIEW_FAILURE_CODES)
    | {"EXECUTION_EXCEPTION", "NO_VALID_CANDIDATE", "NO_RESPONSE"}
)

_FORBIDDEN_KEYS = frozenset(
    {
        "raw_input",
        "input",
        "normalized_input",
        "thought_text",
        "action_text",
        "memo",
        "memo_action",
        "question_answer",
        "supplemental_answer",
        "comment_text",
        "candidate_text",
        "final_text",
        "visible_body",
        "response_text",
        "v1_body",
        "v3_body",
        "free_text",
        "local_review_note",
        "note",
        "description",
        "message",
        "hmac_key_hex",
        "commitment_key",
        "nonce",
        "username",
        "honorific",
    }
)

_KNOWN28_CASE_REFS = tuple(
    sorted(
        (
            "A",
            "B",
            "C",
            "D",
            "I6-S03",
            "I6-L03",
            "I6-C01",
            "I6-D02",
            "RR8-U01",
            "RR8-U02",
            "RR8-U03",
            "RR8-U04",
            "RR8-U05",
            "RR8-U06",
            "RR8-U07",
            "RR8-U08",
            "RR8-U09",
            "RR8-U10",
            "RR8-U11",
            "RR8-U12",
            "I6-S01",
            "I6-S02",
            "I6-L01",
            "I6-L02",
            "I6-C02",
            "I6-C03",
            "I6-D01",
            "I6-D03",
        )
    )
)
FROZEN_KNOWN28_INVENTORY_SHA256 = (
    "f31c35d7e72cbbf4b2f04ad1092041443e42f932731afa33668871f406f76866"
)

# This policy is a frozen, generic projection of the three historical Known28
# source cohorts into the Step 1 app-reachable shape.  It classifies regression
# applicability only.  It is never passed to candidate generation and has no
# case-specific override surface.
KNOWN28_GENERIC_PROJECTION_POLICY = {
    "schema_version": (
        "cocolon.emlis.nls_v3.known28_generic_projection_policy.v1"
    ),
    "authority": "frozen_regression_input_contract_classification_only",
    "source_exact_keys": ["category", "emotions", "memo", "memo_action"],
    "target_exact_keys": [
        "action_text",
        "categories",
        "emotions",
        "thought_text",
    ],
    "field_projection": [
        {
            "source_field": "memo",
            "target_field": "thought_text",
            "operation": "copy_scalar_text",
        },
        {
            "source_field": "memo_action",
            "target_field": "action_text",
            "operation": "copy_scalar_text",
        },
        {
            "source_field": "emotions",
            "target_field": "emotions",
            "operation": "legacy_label_to_typed_emotion",
        },
        {
            "source_field": "category",
            "target_field": "categories",
            "operation": "copy_scalar_text_array",
        },
    ],
    "typed_emotion_projection": {
        "source_item_type": "string",
        "target_exact_keys": ["strength", "type"],
        "type_value": "source_item",
        "strength_value": "medium",
    },
    "validator_contract_version": "cocolon.input_contract.20260714",
    "case_specific_overrides_allowed": False,
    "candidate_generation_control_allowed": False,
    "body_free": True,
}
FROZEN_KNOWN28_GENERIC_PROJECTION_POLICY_SHA256 = (
    "06ddb82832ae74a207ba4d2eca28eb58a54444aa25030d5fd0681fc02421f8ad"
)
KNOWN28_GENERIC_PROJECTION_POLICY_SHA256 = artifact_sha256(
    KNOWN28_GENERIC_PROJECTION_POLICY
)

_KNOWN28_EXPECTED_NON_APPLICABLE_ISSUES = {
    "I6-C02": [
        "input.emotions[0].type:unknown_emotion_type",
        "input.categories[0]:unknown_category",
    ],
    "I6-C03": [
        "input.emotions[0].type:unknown_emotion_type",
        "input.categories[0]:unknown_category",
    ],
    "I6-D01": [
        "input.emotions[0].type:unknown_emotion_type",
        "input.categories[0]:unknown_category",
    ],
    "I6-D03": [
        "input.emotions[0].type:unknown_emotion_type",
        "input.categories[0]:unknown_category",
    ],
    "I6-L01": ["input.emotions[0].type:unknown_emotion_type"],
    "I6-L02": [
        "input.emotions[0].type:unknown_emotion_type",
        "input.categories[0]:unknown_category",
    ],
    "I6-S01": [
        "input.emotions[0].type:unknown_emotion_type",
        "input.categories[0]:unknown_category",
    ],
    "I6-S02": [
        "input.emotions[0].type:unknown_emotion_type",
        "input.categories[0]:unknown_category",
    ],
    "RR8-U12": ["input:thought_action_both_empty_after_js_trim"],
}
KNOWN28_EXPECTED_APPLICABILITY = {
    "schema_version": (
        "cocolon.emlis.nls_v3.known28_expected_applicability_inventory.v1"
    ),
    "projection_policy_sha256": (
        FROZEN_KNOWN28_GENERIC_PROJECTION_POLICY_SHA256
    ),
    "classification_source": "frozen_regression_input_contract_only",
    "cases": [
        {
            "case_ref": case_ref,
            "applicability_status": (
                "expected_non_applicable"
                if case_ref in _KNOWN28_EXPECTED_NON_APPLICABLE_ISSUES
                else "app_reachable"
            ),
            "expected_issue_codes": list(
                _KNOWN28_EXPECTED_NON_APPLICABLE_ISSUES.get(case_ref, ())
            ),
        }
        for case_ref in _KNOWN28_CASE_REFS
    ],
    "counts": {"app_reachable": 19, "expected_non_applicable": 9},
    "candidate_generation_control_allowed": False,
    "body_free": True,
}
FROZEN_KNOWN28_EXPECTED_APPLICABILITY_SHA256 = (
    "3e705e4870184402a9626e6a0c3f38204113367c6accb32f8ac7b7cff99503d4"
)
KNOWN28_EXPECTED_APPLICABILITY_SHA256 = artifact_sha256(
    KNOWN28_EXPECTED_APPLICABILITY
)

INVALID16_EXPECTED_INVENTORY = (
    {
        "fixture_id": "both_empty",
        "expected_issue": "input:thought_action_both_empty_after_js_trim",
    },
    {
        "fixture_id": "both_whitespace",
        "expected_issue": "input:thought_action_both_empty_after_js_trim",
    },
    {
        "fixture_id": "emotion_empty",
        "expected_issue": "input.emotions:minimum_one_required",
    },
    {
        "fixture_id": "category_empty",
        "expected_issue": "input.categories:minimum_one_required",
    },
    {
        "fixture_id": "emotion_unknown",
        "expected_issue": "input.emotions[0].type:unknown_emotion_type",
    },
    {
        "fixture_id": "emotion_type_empty",
        "expected_issue": "input.emotions[0].type:unknown_emotion_type",
    },
    {
        "fixture_id": "category_unknown",
        "expected_issue": "input.categories[0]:unknown_category",
    },
    {
        "fixture_id": "category_value_empty",
        "expected_issue": "input.categories[0]:unknown_category",
    },
    {
        "fixture_id": "strength_unknown",
        "expected_issue": "input.emotions[0].strength:unknown_strength",
    },
    {
        "fixture_id": "emotion_duplicate",
        "expected_issue": "input.emotions:duplicate_emotion_type",
    },
    {
        "fixture_id": "category_duplicate",
        "expected_issue": "input.categories:duplicate_category",
    },
    {
        "fixture_id": "self_insight_mixed",
        "expected_issue": "input.emotions:self_insight_must_be_exclusive",
    },
    {
        "fixture_id": "self_insight_wrong_strength",
        "expected_issue": (
            "input.emotions[0].strength:self_insight_requires_medium"
        ),
    },
    {
        "fixture_id": "emotion_not_array",
        "expected_issue": "input.emotions:array_required",
    },
    {
        "fixture_id": "category_not_array",
        "expected_issue": "input.categories:array_required",
    },
    {
        "fixture_id": "unknown_input_field",
        "expected_issue": "input:keyset_mismatch",
    },
)
_INVALID16_EXPECTED = {
    row["fixture_id"]: row["expected_issue"]
    for row in INVALID16_EXPECTED_INVENTORY
}
_INVALID16_IDS = tuple(sorted(_INVALID16_EXPECTED))
FROZEN_INVALID16_INVENTORY_SHA256 = (
    "a383abec2e19f66d83322500fd93e844553facfbf198ae113dc9789d95c66bd1"
)


def validate_invalid16_inventory_contract() -> tuple[str, ...]:
    issues: list[str] = []
    if type(INVALID16_EXPECTED_INVENTORY) is not tuple or len(
        INVALID16_EXPECTED_INVENTORY
    ) != 16:
        return ("INVALID16_INVENTORY_SHAPE_INVALID",)
    seen: set[str] = set()
    for row in INVALID16_EXPECTED_INVENTORY:
        if type(row) is not dict or set(row) != {
            "fixture_id",
            "expected_issue",
        }:
            issues.append("INVALID16_INVENTORY_ROW_INVALID")
            continue
        fixture_id = row["fixture_id"]
        expected_issue = row["expected_issue"]
        if (
            type(fixture_id) is not str
            or fixture_id in seen
            or type(expected_issue) is not str
            or _ISSUE_RE.fullmatch(expected_issue) is None
        ):
            issues.append("INVALID16_INVENTORY_ROW_INVALID")
        else:
            seen.add(fixture_id)
    if artifact_sha256(list(INVALID16_EXPECTED_INVENTORY)) != (
        FROZEN_INVALID16_INVENTORY_SHA256
    ):
        issues.append("INVALID16_INVENTORY_HASH_DRIFT")
    return tuple(dict.fromkeys(issues))

_WORKAROUND_DIMENSIONS = (
    "case_id_branch",
    "coverage_family_branch",
    "expected_output_literal",
    "fixed_sentence_literal",
    "input_specific_literal",
)
_WORKAROUND_SCANNER_PATH = "ai/tools/emlis_nls_v3_step11_cycle_finalize.py"
_WORKAROUND_SCANNED_PATHS = (
    "ai/services/ai_inference/emlis_ai_step11_surface_catalog_v3.py",
    "ai/services/ai_inference/emlis_ai_step11_semantic_overlay_v3.py",
    "ai/services/ai_inference/emlis_ai_step11_natural_surface_v3.py",
    "ai/services/ai_inference/emlis_ai_step11_natural_surface_matcher_v3.py",
    "ai/services/ai_inference/emlis_ai_step11_hard_gate_v3.py",
    "ai/services/ai_inference/emlis_ai_step11_runtime_adapter_v3.py",
)
_WORKAROUND_NEGATIVE_POLICY = {
    "schema_version": "cocolon.emlis.nls_v3.workaround_scan_negative.v2",
    "attacks": [
        "case_id_control_branch",
        "case_id_override_lookup",
        "case_id_split_control_branch",
        "coverage_family_control_branch",
        "coverage_family_subscript_branch",
        "expected_output_identifier",
        "fixed_body_split_literal",
        "input_hash_override_lookup",
        "input_literal_direct",
        "input_literal_split_concatenation",
    ],
    "dimensions": list(_WORKAROUND_DIMENSIONS),
    "all_attacks_must_be_detected": True,
}
WORKAROUND_NEGATIVE_POLICY_SHA256 = artifact_sha256(
    _WORKAROUND_NEGATIVE_POLICY
)


class Step11CycleEvidenceError(ValueError):
    """Fail-closed error carrying a body-free machine code only."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _valid_sha(value: Any) -> bool:
    return type(value) is str and _SHA_RE.fullmatch(value) is not None


def _valid_nonzero_sha(value: Any) -> bool:
    return _valid_sha(value) and value != "0" * 64


def _rc_number(value: Any) -> int | None:
    if type(value) is not str:
        return None
    match = _RC_RE.fullmatch(value)
    return int(match.group(1)) if match is not None else None


def _valid_rc(value: Any) -> bool:
    return _rc_number(value) is not None


def _is_successor(value: Any, before: str = STEP11_INITIAL_CANDIDATE_VERSION_ID) -> bool:
    current = _rc_number(value)
    prior = _rc_number(before)
    return current is not None and prior is not None and current > prior


def _require_exact_keys(value: Any, keys: set[str] | frozenset[str], code: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != set(keys):
        raise Step11CycleEvidenceError(code)
    return dict(value)


def _scan_forbidden_keys(value: Any, path: str = "$") -> tuple[str, ...]:
    issues: list[str] = []
    if type(value) is dict:
        for key, child in value.items():
            if type(key) is not str:
                issues.append(f"NON_STRING_KEY:{path}")
                continue
            if key in _FORBIDDEN_KEYS:
                issues.append(f"FORBIDDEN_BODY_KEY:{path}.{key}")
            issues.extend(_scan_forbidden_keys(child, f"{path}.{key}"))
    elif type(value) is list:
        for index, child in enumerate(value):
            issues.extend(_scan_forbidden_keys(child, f"{path}[{index}]"))
    return tuple(issues)


def _require_body_free(value: Any) -> None:
    if _scan_forbidden_keys(value):
        raise Step11CycleEvidenceError("STEP11_BODY_FREE_VIOLATION")
    try:
        assert_body_free(value)
    except ValueError as exc:
        raise Step11CycleEvidenceError("STEP11_BODY_FREE_VIOLATION") from exc


def validate_known28_applicability_contract() -> tuple[str, ...]:
    """Validate the frozen generic projection and applicability inventory."""

    issues: set[str] = set()
    if (
        KNOWN28_GENERIC_PROJECTION_POLICY_SHA256
        != FROZEN_KNOWN28_GENERIC_PROJECTION_POLICY_SHA256
        or FROZEN_KNOWN28_GENERIC_PROJECTION_POLICY_SHA256 == "0" * 64
    ):
        issues.add("KNOWN28_GENERIC_PROJECTION_POLICY_HASH_DRIFT")
    if (
        KNOWN28_EXPECTED_APPLICABILITY_SHA256
        != FROZEN_KNOWN28_EXPECTED_APPLICABILITY_SHA256
        or FROZEN_KNOWN28_EXPECTED_APPLICABILITY_SHA256 == "0" * 64
    ):
        issues.add("KNOWN28_EXPECTED_APPLICABILITY_HASH_DRIFT")
    try:
        _require_body_free(KNOWN28_GENERIC_PROJECTION_POLICY)
        _require_body_free(KNOWN28_EXPECTED_APPLICABILITY)
        rows = KNOWN28_EXPECTED_APPLICABILITY["cases"]
        if (
            KNOWN28_EXPECTED_APPLICABILITY.get("projection_policy_sha256")
            != FROZEN_KNOWN28_GENERIC_PROJECTION_POLICY_SHA256
            or type(rows) is not list
            or tuple(row.get("case_ref") for row in rows)
            != _KNOWN28_CASE_REFS
            or KNOWN28_EXPECTED_APPLICABILITY.get("counts")
            != {"app_reachable": 19, "expected_non_applicable": 9}
            or KNOWN28_EXPECTED_APPLICABILITY.get(
                "candidate_generation_control_allowed"
            )
            is not False
        ):
            issues.add("KNOWN28_EXPECTED_APPLICABILITY_CONTRACT_INVALID")
        app_count = 0
        nonapp_count = 0
        for row in rows:
            if type(row) is not dict or set(row) != {
                "case_ref",
                "applicability_status",
                "expected_issue_codes",
            }:
                issues.add("KNOWN28_EXPECTED_APPLICABILITY_CONTRACT_INVALID")
                continue
            status = row.get("applicability_status")
            codes = row.get("expected_issue_codes")
            if (
                type(codes) is not list
                or len(codes) != len(set(codes))
                or any(
                    type(code) is not str or _ISSUE_RE.fullmatch(code) is None
                    for code in codes
                )
            ):
                issues.add("KNOWN28_EXPECTED_APPLICABILITY_CONTRACT_INVALID")
            if status == "app_reachable" and codes == []:
                app_count += 1
            elif status == "expected_non_applicable" and codes:
                nonapp_count += 1
            else:
                issues.add("KNOWN28_EXPECTED_APPLICABILITY_CONTRACT_INVALID")
        if (app_count, nonapp_count) != (19, 9):
            issues.add("KNOWN28_EXPECTED_APPLICABILITY_CONTRACT_INVALID")
    except (KeyError, TypeError, ValueError, Step11CycleEvidenceError):
        issues.add("KNOWN28_EXPECTED_APPLICABILITY_CONTRACT_INVALID")
    return tuple(sorted(issues))


def _count(values: Sequence[str]) -> dict[str, int]:
    return dict(sorted(Counter(values).items()))


def _safe_file_rows(value: Any, *, required: bool = True) -> list[dict[str, str]]:
    if type(value) not in {list, tuple} or (required and not value):
        raise Step11CycleEvidenceError("FILE_HASH_ROWS_INVALID")
    rows: list[dict[str, str]] = []
    for raw in value:
        row = _require_exact_keys(raw, {"path", "sha256"}, "FILE_HASH_ROW_INVALID")
        path = row["path"]
        if (
            type(path) is not str
            or _SAFE_PATH_RE.fullmatch(path) is None
            or Path(path).is_absolute()
            or ".." in Path(path).parts
            or not _valid_nonzero_sha(row["sha256"])
        ):
            raise Step11CycleEvidenceError("FILE_HASH_ROW_INVALID")
        rows.append({"path": path, "sha256": row["sha256"]})
    rows.sort(key=lambda row: row["path"])
    if len({row["path"] for row in rows}) != len(rows):
        raise Step11CycleEvidenceError("FILE_HASH_PATH_DUPLICATE")
    return rows


def build_cycle001_corpus_validation(
    manifest: Mapping[str, Any],
    coverage_matrix: Mapping[str, Any],
    duplicate_report: Mapping[str, Any],
) -> dict[str, Any]:
    """Revalidate the exact Step 2 frozen parents without reopening bodies."""

    for value in (manifest, coverage_matrix, duplicate_report):
        if type(value) is not dict:
            raise Step11CycleEvidenceError("CORPUS_PARENT_MAPPING_REQUIRED")
        _require_body_free(value)
    if (
        artifact_sha256(manifest) != FROZEN_BATCH001_MANIFEST_ARTIFACT_SHA256
        or artifact_sha256(coverage_matrix)
        != FROZEN_BATCH001_MATRIX_ARTIFACT_SHA256
        or artifact_sha256(duplicate_report)
        != FROZEN_BATCH001_DUPLICATE_REPORT_ARTIFACT_SHA256
    ):
        raise Step11CycleEvidenceError("CORPUS_FROZEN_PARENT_MISMATCH")
    if (
        manifest.get("schema_version")
        != "cocolon.emlis.nls_v3.sample_batch_manifest.v1"
        or manifest.get("batch_id") != STEP11_BATCH_ID
        or manifest.get("state") != "VALIDATED"
        or manifest.get("frozen") is not True
        or manifest.get("case_count") != 100
        or manifest.get("valid_case_count") != 100
        or manifest.get("invalid_case_count") != 0
        or tuple(manifest.get("case_ids", ())) != _CASE_IDS
        or manifest.get("source_partition") != "karen_generated"
        or manifest.get("duplicate_counts")
        != {"exact": 0, "near": 0, "normalized": 0}
        or manifest.get("corpus_file_sha256") != FROZEN_BATCH001_CORPUS_SHA256
        or manifest.get("coverage_matrix_sha256") != FROZEN_BATCH001_MATRIX_SHA256
        or manifest.get("duplicate_report_sha256")
        != FROZEN_BATCH001_DUPLICATE_REPORT_SHA256
        or manifest.get("validator_policy_sha256")
        != FROZEN_VALIDATOR_POLICY_SHA256
        or manifest.get("body_free") is not True
    ):
        raise Step11CycleEvidenceError("CORPUS_MANIFEST_CONTRACT_INVALID")
    privacy = manifest.get("privacy_review")
    if (
        type(privacy) is not dict
        or privacy.get("status") != "passed"
        or privacy.get("pii_absent") is not True
        or privacy.get("expected_response_absent") is not True
        or privacy.get("real_user_text_copy_absent") is not True
    ):
        raise Step11CycleEvidenceError("CORPUS_PRIVACY_REVIEW_INVALID")
    if (
        coverage_matrix.get("schema_version")
        != "cocolon.emlis.nls_v3.coverage_matrix.v1"
        or coverage_matrix.get("batch_id") != STEP11_BATCH_ID
        or coverage_matrix.get("case_count") != 100
        or coverage_matrix.get("source_case_set_commitment")
        != manifest.get("corpus_set_commitment")
        or coverage_matrix.get("sample_schema_sha256")
        != manifest.get("sample_schema_sha256")
        or coverage_matrix.get("body_free") is not True
        or type(coverage_matrix.get("axis_counts")) is not list
    ):
        raise Step11CycleEvidenceError("CORPUS_MATRIX_CONTRACT_INVALID")
    if (
        duplicate_report.get("schema_version")
        != "cocolon.emlis.nls_v3.duplicate_report.v1"
        or duplicate_report.get("query_case_count") != 100
        or duplicate_report.get("query_corpus_set_commitment")
        != manifest.get("corpus_set_commitment")
        or duplicate_report.get("counts")
        != {"exact": 0, "near": 0, "normalized": 0}
        or duplicate_report.get("pairs") != []
        or duplicate_report.get("body_free") is not True
    ):
        raise Step11CycleEvidenceError("CORPUS_DUPLICATE_CONTRACT_INVALID")
    result = {
        "schema_version": CORPUS_VALIDATION_SCHEMA,
        "cycle_id": STEP11_CYCLE_ID,
        "batch_id": STEP11_BATCH_ID,
        "state": "VALIDATED",
        "manifest_file_sha256": FROZEN_BATCH001_MANIFEST_SHA256,
        "manifest_artifact_sha256": FROZEN_BATCH001_MANIFEST_ARTIFACT_SHA256,
        "coverage_matrix_file_sha256": FROZEN_BATCH001_MATRIX_SHA256,
        "coverage_matrix_artifact_sha256": FROZEN_BATCH001_MATRIX_ARTIFACT_SHA256,
        "duplicate_report_file_sha256": FROZEN_BATCH001_DUPLICATE_REPORT_SHA256,
        "duplicate_report_artifact_sha256": (
            FROZEN_BATCH001_DUPLICATE_REPORT_ARTIFACT_SHA256
        ),
        "corpus_file_sha256": FROZEN_BATCH001_CORPUS_SHA256,
        "validator_policy_sha256": FROZEN_VALIDATOR_POLICY_SHA256,
        "case_set_commitment": manifest["corpus_set_commitment"],
        "valid_case_count": 100,
        "app_reachable_count": 100,
        "exact_duplicate_count": 0,
        "normalized_duplicate_count": 0,
        "near_duplicate_count": 0,
        "privacy_review_status": "passed",
        "body_free": True,
    }
    _require_body_free(result)
    return result


def validate_cycle001_corpus_validation(
    value: Any,
    *,
    manifest: Mapping[str, Any],
    coverage_matrix: Mapping[str, Any],
    duplicate_report: Mapping[str, Any],
) -> tuple[str, ...]:
    try:
        expected = build_cycle001_corpus_validation(
            manifest,
            coverage_matrix,
            duplicate_report,
        )
    except (KeyError, TypeError, ValueError, Step11CycleEvidenceError):
        return ("CORPUS_VALIDATION_PARENT_INVALID",)
    return () if value == expected else ("CORPUS_VALIDATION_RECOMPUTATION_MISMATCH",)


def _validated_corpus(value: Any) -> dict[str, Any]:
    keys = {
        "schema_version",
        "cycle_id",
        "batch_id",
        "state",
        "manifest_file_sha256",
        "manifest_artifact_sha256",
        "coverage_matrix_file_sha256",
        "coverage_matrix_artifact_sha256",
        "duplicate_report_file_sha256",
        "duplicate_report_artifact_sha256",
        "corpus_file_sha256",
        "validator_policy_sha256",
        "case_set_commitment",
        "valid_case_count",
        "app_reachable_count",
        "exact_duplicate_count",
        "normalized_duplicate_count",
        "near_duplicate_count",
        "privacy_review_status",
        "body_free",
    }
    row = _require_exact_keys(value, keys, "CORPUS_VALIDATION_INVALID")
    if (
        row["schema_version"] != CORPUS_VALIDATION_SCHEMA
        or row["cycle_id"] != STEP11_CYCLE_ID
        or row["batch_id"] != STEP11_BATCH_ID
        or row["state"] != "VALIDATED"
        or row["manifest_file_sha256"] != FROZEN_BATCH001_MANIFEST_SHA256
        or row["manifest_artifact_sha256"]
        != FROZEN_BATCH001_MANIFEST_ARTIFACT_SHA256
        or row["coverage_matrix_file_sha256"] != FROZEN_BATCH001_MATRIX_SHA256
        or row["coverage_matrix_artifact_sha256"]
        != FROZEN_BATCH001_MATRIX_ARTIFACT_SHA256
        or row["duplicate_report_file_sha256"]
        != FROZEN_BATCH001_DUPLICATE_REPORT_SHA256
        or row["duplicate_report_artifact_sha256"]
        != FROZEN_BATCH001_DUPLICATE_REPORT_ARTIFACT_SHA256
        or row["corpus_file_sha256"] != FROZEN_BATCH001_CORPUS_SHA256
        or row["validator_policy_sha256"] != FROZEN_VALIDATOR_POLICY_SHA256
        or not _valid_nonzero_sha(row["case_set_commitment"])
        or row["valid_case_count"] != 100
        or row["app_reachable_count"] != 100
        or row["exact_duplicate_count"] != 0
        or row["normalized_duplicate_count"] != 0
        or row["near_duplicate_count"] != 0
        or row["privacy_review_status"] != "passed"
        or row["body_free"] is not True
    ):
        raise Step11CycleEvidenceError("CORPUS_VALIDATION_INVALID")
    _require_body_free(row)
    return row


def build_step11_dependency_manifest(
    *,
    before_candidate_version_id: str,
    before_source_closure_sha256: str,
    candidate_version_id: str,
    file_hashes: Sequence[Mapping[str, str]],
    changed_file_hashes: Sequence[Mapping[str, str]],
) -> dict[str, Any]:
    """Build a historical, recomputable source-closure manifest."""

    if (
        not _valid_rc(before_candidate_version_id)
        or not _valid_nonzero_sha(before_source_closure_sha256)
        or not _is_successor(candidate_version_id, before_candidate_version_id)
    ):
        raise Step11CycleEvidenceError("DEPENDENCY_VERSION_LINEAGE_INVALID")
    files = _safe_file_rows(file_hashes)
    changed = _safe_file_rows(changed_file_hashes)
    by_path = {row["path"]: row["sha256"] for row in files}
    if any(by_path.get(row["path"]) != row["sha256"] for row in changed):
        raise Step11CycleEvidenceError("DEPENDENCY_CHANGED_FILE_NOT_IN_CLOSURE")
    material = {
        "schema_version": STEP11_DEPENDENCY_MANIFEST_SCHEMA,
        "cycle_id": STEP11_CYCLE_ID,
        "before_candidate_version_id": before_candidate_version_id,
        "before_source_closure_sha256": before_source_closure_sha256,
        "candidate_version_id": candidate_version_id,
        "file_hashes": files,
        "changed_file_hashes": changed,
    }
    closure = artifact_sha256(material)
    value = {
        **material,
        "source_dependency_closure_sha256": closure,
        "body_free": True,
    }
    _require_body_free(value)
    return value


def validate_step11_dependency_manifest(value: Any) -> tuple[str, ...]:
    if type(value) is not dict:
        return ("DEPENDENCY_MANIFEST_MAPPING_REQUIRED",)
    try:
        expected = build_step11_dependency_manifest(
            before_candidate_version_id=value.get("before_candidate_version_id"),
            before_source_closure_sha256=value.get(
                "before_source_closure_sha256"
            ),
            candidate_version_id=value.get("candidate_version_id"),
            file_hashes=value.get("file_hashes"),
            changed_file_hashes=value.get("changed_file_hashes"),
        )
    except (TypeError, ValueError, Step11CycleEvidenceError):
        return ("DEPENDENCY_MANIFEST_CONTRACT_INVALID",)
    return () if value == expected else ("DEPENDENCY_MANIFEST_RECOMPUTATION_MISMATCH",)


def _validated_dependency_manifest(value: Any) -> dict[str, Any]:
    if validate_step11_dependency_manifest(value):
        raise Step11CycleEvidenceError("DEPENDENCY_MANIFEST_INVALID")
    return dict(value)


_STEP11_RECEIPT_KEYS = {
    "schema_version",
    "candidate_version_id",
    "run_id",
    "batch_id",
    "case_id",
    "sample_source",
    "case_identity_commitment",
    "commitment_policy_sha256",
    "app_reachable_validation",
    "source_dependency_closure_sha256",
    "observation_stage_context_commitment",
    "source_observation_plan_commitment",
    "obligation_ledger_commitment",
    "content_plan_commitment",
    "candidate_set_commitment",
    "selected_discourse_plan_commitment",
    "selected_surface_ast_commitment",
    "selected_candidate_body_commitment",
    "parsed_witness_binding_commitment",
    "hard_gate",
    "selector_decision",
    "v1_baseline_body_commitment",
    "runtime_summary_commitment",
    "environment_sha256",
    "runner_sha256",
    "body_free",
}


def _normalize_codes(value: Any, allowed: frozenset[str], code: str) -> list[str]:
    if type(value) not in {list, tuple}:
        raise Step11CycleEvidenceError(code)
    result = sorted(set(value))
    if len(result) != len(value) or any(
        type(item) is not str or item not in allowed for item in result
    ):
        raise Step11CycleEvidenceError(code)
    return result


def _step11_receipt(
    value: Any,
    *,
    candidate_version_id: str,
    run_id: str,
    case_id: str,
    source_closure: str,
    commitment_policy_sha256: str,
    environment_sha256: str,
    runner_sha256: str,
    row_status: str,
) -> dict[str, Any]:
    row = _require_exact_keys(value, _STEP11_RECEIPT_KEYS, "STEP11_RECEIPT_KEYSET_INVALID")
    if (
        row["schema_version"] != STEP11_CASE_RECEIPT_SCHEMA
        or row["candidate_version_id"] != candidate_version_id
        or row["run_id"] != run_id
        or row["batch_id"] != STEP11_BATCH_ID
        or row["case_id"] != case_id
        or row["sample_source"] != "karen_generated"
        or not _valid_nonzero_sha(row["case_identity_commitment"])
        or row["commitment_policy_sha256"] != commitment_policy_sha256
        or row["source_dependency_closure_sha256"] != source_closure
        or row["environment_sha256"] != environment_sha256
        or row["runner_sha256"] != runner_sha256
        or row["body_free"] is not True
    ):
        raise Step11CycleEvidenceError("STEP11_RECEIPT_PARENT_INVALID")
    app = _require_exact_keys(
        row["app_reachable_validation"],
        {"status", "contract_version"},
        "STEP11_RECEIPT_APP_VALIDATION_INVALID",
    )
    if app != {
        "status": "passed",
        "contract_version": "cocolon.input_contract.20260714",
    }:
        raise Step11CycleEvidenceError("STEP11_RECEIPT_APP_VALIDATION_INVALID")
    always_hashes = (
        "observation_stage_context_commitment",
        "source_observation_plan_commitment",
        "obligation_ledger_commitment",
        "content_plan_commitment",
        "candidate_set_commitment",
        "v1_baseline_body_commitment",
        "runtime_summary_commitment",
    )
    if any(not _valid_nonzero_sha(row[field]) for field in always_hashes):
        raise Step11CycleEvidenceError("STEP11_RECEIPT_LINEAGE_HASH_INVALID")
    gate = _require_exact_keys(
        row["hard_gate"], {"status", "failed_codes"}, "STEP11_RECEIPT_GATE_INVALID"
    )
    selector = _require_exact_keys(
        row["selector_decision"],
        {"status", "selection_attributes_commitment"},
        "STEP11_RECEIPT_SELECTOR_INVALID",
    )
    if not _valid_nonzero_sha(selector["selection_attributes_commitment"]):
        raise Step11CycleEvidenceError("STEP11_RECEIPT_SELECTOR_INVALID")
    failed_codes = _normalize_codes(
        gate["failed_codes"],
        frozenset(HARD_GATE_FAILURE_CODES) | _STEP11_HARD_GATE_FAILURE_CODES,
        "STEP11_RECEIPT_GATE_INVALID",
    )
    selected_hashes = (
        "selected_discourse_plan_commitment",
        "selected_surface_ast_commitment",
        "selected_candidate_body_commitment",
        "parsed_witness_binding_commitment",
    )
    if row_status == "selected":
        if (
            gate["status"] != "passed"
            or failed_codes
            or selector["status"] != "selected"
            or any(not _valid_nonzero_sha(row[field]) for field in selected_hashes)
        ):
            raise Step11CycleEvidenceError("STEP11_RECEIPT_SELECTED_STATE_INVALID")
    elif row_status == "v3_no_valid_candidate":
        if (
            gate["status"] != "failed"
            or not failed_codes
            or selector["status"] != "no_valid_candidate"
            or any(row[field] is not None for field in selected_hashes)
        ):
            raise Step11CycleEvidenceError("STEP11_RECEIPT_NO_VALID_STATE_INVALID")
    else:
        raise Step11CycleEvidenceError("STEP11_RECEIPT_STATUS_INVALID")
    row["hard_gate"] = {"status": gate["status"], "failed_codes": failed_codes}
    row["selector_decision"] = selector
    _require_body_free(row)
    return row


_SURFACE_PROFILE_KEYS = {
    "opening_family",
    "opening_semantic_family",
    "opening_variant_id",
    "ending_family",
    "predicate_families",
    "reception_act_families",
    "reception_content_kind",
    "observation_literal_count",
    "unique_literal_owner_count",
    "literal_replay_count",
    "reception_literal_count",
    "near_duplicate_skeleton_commitment",
}

_RECEPTION_CONTENT_KINDS = frozenset(
    {
        "none",
        "anaphoric",
        "direct_owned_antecedent",
        "direct_unowned_antecedent",
        "mixed_owned_antecedent",
        "mixed_unowned_antecedent",
    }
)


def _surface_profile(value: Any) -> dict[str, Any]:
    row = _require_exact_keys(value, _SURFACE_PROFILE_KEYS, "SURFACE_PROFILE_INVALID")
    if (
        type(row["opening_family"]) is not str
        or _LOWER_CODE_RE.fullmatch(row["opening_family"]) is None
        or type(row["opening_semantic_family"]) is not str
        or _LOWER_CODE_RE.fullmatch(row["opening_semantic_family"]) is None
        or type(row["opening_variant_id"]) is not str
        or _LOWER_CODE_RE.fullmatch(row["opening_variant_id"]) is None
        or row["opening_variant_id"] != row["opening_family"]
        or type(row["ending_family"]) is not str
        or _LOWER_CODE_RE.fullmatch(row["ending_family"]) is None
        or row["reception_content_kind"] not in _RECEPTION_CONTENT_KINDS
        or not _valid_nonzero_sha(row["near_duplicate_skeleton_commitment"])
    ):
        raise Step11CycleEvidenceError("SURFACE_PROFILE_INVALID")
    for field in (
        "observation_literal_count",
        "unique_literal_owner_count",
        "literal_replay_count",
        "reception_literal_count",
    ):
        if (
            type(row[field]) is not int
            or type(row[field]) is bool
            or row[field] < 0
        ):
            raise Step11CycleEvidenceError("SURFACE_PROFILE_INVALID")
    if (
        row["unique_literal_owner_count"] > row["observation_literal_count"]
        or row["literal_replay_count"]
        != row["observation_literal_count"] - row["unique_literal_owner_count"]
        or (
            row["reception_content_kind"] in {"none", "anaphoric"}
            and row["reception_literal_count"] != 0
        )
        or (
            row["reception_content_kind"]
            in {
                "direct_owned_antecedent",
                "direct_unowned_antecedent",
                "mixed_owned_antecedent",
                "mixed_unowned_antecedent",
            }
            and row["reception_literal_count"] < 1
        )
    ):
        raise Step11CycleEvidenceError("SURFACE_PROFILE_INVALID")
    for field in ("predicate_families", "reception_act_families"):
        values = row[field]
        if (
            type(values) is not list
            or values != sorted(set(values))
            or any(type(item) is not str or _LOWER_CODE_RE.fullmatch(item) is None for item in values)
        ):
            raise Step11CycleEvidenceError("SURFACE_PROFILE_INVALID")
    return row


_STEP11_CASE_ROW_KEYS = {
    "case_id",
    "sample_case_commitment",
    "case_identity_commitment",
    "v1_baseline_body_commitment",
    "status",
    "failure_code",
    "private_failure_code_commitment",
    "runtime_summary",
    "runtime_summary_commitment",
    "surface_profile",
    "receipt",
    "v1_fallback_used",
}


_RUNTIME_SUMMARY_KEYS = {
    "schema_version",
    "adapter_version",
    "candidate_version_id",
    "execution_scope",
    "status",
    "source_dependency_closure_sha256",
    "selected_candidate_present",
    "evaluated_candidate_count",
    "rejected_candidate_count",
    "hard_gate_pass_count",
    "hard_gate_failure_code_counts",
    "recovery_attempt_count",
    "latency_ns",
    "semantic_metrics",
    "v3_success",
    "v1_fallback_used",
    "v1_fallback_counts_as_v3_success",
    "body_free",
}
_RUNTIME_SEMANTIC_METRIC_KEYS = {
    "required_obligation_count",
    "bound_obligation_count",
    "semantic_atom_count",
    "integrated_relation_count",
    "integrated_unknown_count",
    "source_fragment_count",
    "section_count",
    "sentence_count",
    "depth",
}


def _runtime_summary(
    value: Any,
    *,
    candidate_version_id: str,
    source_closure: str,
    row_status: str,
) -> dict[str, Any]:
    row = _require_exact_keys(
        value, _RUNTIME_SUMMARY_KEYS, "STEP11_RUNTIME_SUMMARY_INVALID"
    )
    counts = (
        "evaluated_candidate_count",
        "rejected_candidate_count",
        "hard_gate_pass_count",
        "recovery_attempt_count",
        "latency_ns",
    )
    if (
        row["schema_version"]
        != "cocolon.emlis.nls_v3.step11_runtime_execution_summary.v2"
        or row["adapter_version"]
        != _runtime_adapter_version_for_candidate(candidate_version_id)
        or row["candidate_version_id"] != candidate_version_id
        or row["execution_scope"] != "offline_batch"
        or row["status"] != row_status
        or row["source_dependency_closure_sha256"] != source_closure
        or any(
            type(row[field]) is not int
            or type(row[field]) is bool
            or row[field] < 0
            for field in counts
        )
        or not 1 <= row["evaluated_candidate_count"] <= 12
        or row["rejected_candidate_count"] > row["evaluated_candidate_count"]
        or row["hard_gate_pass_count"] > row["evaluated_candidate_count"]
        or row["recovery_attempt_count"] != 0
        or row["v1_fallback_used"] is not False
        or row["v1_fallback_counts_as_v3_success"] is not False
        or row["body_free"] is not True
    ):
        raise Step11CycleEvidenceError("STEP11_RUNTIME_SUMMARY_INVALID")
    failures = row["hard_gate_failure_code_counts"]
    if (
        type(failures) is not dict
        or list(failures) != sorted(failures)
        or any(
            type(code) is not str
            or code
            not in frozenset(HARD_GATE_FAILURE_CODES)
            | _STEP11_HARD_GATE_FAILURE_CODES
            or type(count) is not int
            or type(count) is bool
            or count < 1
            for code, count in failures.items()
        )
    ):
        raise Step11CycleEvidenceError("STEP11_RUNTIME_SUMMARY_GATE_COUNTS_INVALID")
    metrics = _require_exact_keys(
        row["semantic_metrics"],
        _RUNTIME_SEMANTIC_METRIC_KEYS,
        "STEP11_RUNTIME_SUMMARY_METRICS_INVALID",
    )
    for field in _RUNTIME_SEMANTIC_METRIC_KEYS - {"depth"}:
        if (
            type(metrics[field]) is not int
            or type(metrics[field]) is bool
            or metrics[field] < 0
        ):
            raise Step11CycleEvidenceError(
                "STEP11_RUNTIME_SUMMARY_METRICS_INVALID"
            )
    if metrics["depth"] not in {"minimal", "focused", "layered"}:
        raise Step11CycleEvidenceError("STEP11_RUNTIME_SUMMARY_METRICS_INVALID")
    if row_status == "selected":
        if (
            row["selected_candidate_present"] is not True
            or row["hard_gate_pass_count"] < 1
            or row["v3_success"] is not True
            or metrics["required_obligation_count"] < 1
            or metrics["bound_obligation_count"]
            < metrics["required_obligation_count"]
            or metrics["section_count"] != 2
            or metrics["sentence_count"] < 2
        ):
            raise Step11CycleEvidenceError("STEP11_RUNTIME_SUMMARY_SELECTED_INVALID")
    elif row_status == "v3_no_valid_candidate":
        if (
            row["selected_candidate_present"] is not False
            or row["hard_gate_pass_count"] != 0
            or row["v3_success"] is not False
        ):
            raise Step11CycleEvidenceError("STEP11_RUNTIME_SUMMARY_FAILED_INVALID")
    else:
        raise Step11CycleEvidenceError("STEP11_RUNTIME_SUMMARY_STATUS_INVALID")
    row["semantic_metrics"] = metrics
    _require_body_free(row)
    return row


def _step11_case_row(
    value: Any,
    *,
    candidate_version_id: str,
    run_id: str,
    source_closure: str,
    commitment_policy_sha256: str,
    environment_sha256: str,
    runner_sha256: str,
) -> dict[str, Any]:
    row = _require_exact_keys(value, _STEP11_CASE_ROW_KEYS, "STEP11_CASE_ROW_KEYSET_INVALID")
    status = row["status"]
    if (
        row["case_id"] not in _CASE_ID_SET
        or status not in _BATCH_STATUSES
        or not _valid_nonzero_sha(row["sample_case_commitment"])
        or not _valid_nonzero_sha(row["case_identity_commitment"])
        or type(row["v1_fallback_used"]) is not bool
    ):
        raise Step11CycleEvidenceError("STEP11_CASE_ROW_INVALID")
    if status == "exception":
        if (
            row["failure_code"] not in _STEP11_RUNNER_FAILURE_CODES
            or not _valid_nonzero_sha(row["private_failure_code_commitment"])
            or row["receipt"] is not None
            or row["surface_profile"] is not None
            or row["runtime_summary"] is not None
            or row["runtime_summary_commitment"] is not None
            or (
                row["v1_baseline_body_commitment"] is not None
                and not _valid_nonzero_sha(row["v1_baseline_body_commitment"])
            )
        ):
            raise Step11CycleEvidenceError("STEP11_EXCEPTION_ROW_INVALID")
    else:
        if (
            row["failure_code"] is not None
            or row["private_failure_code_commitment"] is not None
            or not _valid_nonzero_sha(row["runtime_summary_commitment"])
            or not _valid_nonzero_sha(row["v1_baseline_body_commitment"])
        ):
            raise Step11CycleEvidenceError("STEP11_COMPLETED_ROW_INVALID")
        row["runtime_summary"] = _runtime_summary(
            row["runtime_summary"],
            candidate_version_id=candidate_version_id,
            source_closure=source_closure,
            row_status=status,
        )
        receipt = _step11_receipt(
            row["receipt"],
            candidate_version_id=candidate_version_id,
            run_id=run_id,
            case_id=row["case_id"],
            source_closure=source_closure,
            commitment_policy_sha256=commitment_policy_sha256,
            environment_sha256=environment_sha256,
            runner_sha256=runner_sha256,
            row_status=status,
        )
        if (
            receipt["case_identity_commitment"] != row["case_identity_commitment"]
            or receipt["v1_baseline_body_commitment"]
            != row["v1_baseline_body_commitment"]
            or receipt["runtime_summary_commitment"]
            != row["runtime_summary_commitment"]
        ):
            raise Step11CycleEvidenceError("STEP11_CASE_RECEIPT_BINDING_INVALID")
        row["receipt"] = receipt
        if status == "selected":
            row["surface_profile"] = _surface_profile(row["surface_profile"])
        elif row["surface_profile"] is not None:
            raise Step11CycleEvidenceError("STEP11_FAILED_SURFACE_PROFILE_FORBIDDEN")
    _require_body_free(row)
    return row


def _batch_aggregate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    selected = [row for row in rows if row["status"] == "selected"]
    completed = [row for row in rows if row["runtime_summary"] is not None]
    latencies = [row["runtime_summary"]["latency_ns"] for row in completed]
    exact_counts = Counter(
        row["receipt"]["selected_candidate_body_commitment"] for row in selected
    )
    skeleton_counts = Counter(
        row["surface_profile"]["near_duplicate_skeleton_commitment"]
        for row in selected
    )
    metric_fields = tuple(
        sorted(_RUNTIME_SEMANTIC_METRIC_KEYS - {"depth"})
    )
    value: dict[str, Any] = {
        "case_count": len(rows),
        "selected_count": len(selected),
        "no_valid_candidate_count": sum(
            row["status"] == "v3_no_valid_candidate" for row in rows
        ),
        "exception_count": sum(row["status"] == "exception" for row in rows),
        "v1_fallback_count": sum(row["v1_fallback_used"] for row in rows),
        "hard_gate_pass_count": len(selected),
        "app_reachable_pass_count": sum(
            row["status"] != "exception"
            and row["receipt"]["app_reachable_validation"]["status"] == "passed"
            for row in rows
        ),
        "output_duplicate_cluster_count": sum(
            count > 1 for count in exact_counts.values()
        ),
        "output_duplicate_case_count": sum(
            count for count in exact_counts.values() if count > 1
        ),
        "output_near_duplicate_cluster_count": sum(
            count > 1 for count in skeleton_counts.values()
        ),
        "output_near_duplicate_case_count": sum(
            count for count in skeleton_counts.values() if count > 1
        ),
        "latency_sample_count": len(latencies),
        "latency_total_ns": sum(latencies),
        "latency_min_ns": min(latencies) if latencies else None,
        "latency_max_ns": max(latencies) if latencies else None,
        "semantic_metric_totals": {
            field: sum(
                row["runtime_summary"]["semantic_metrics"][field]
                for row in completed
            )
            for field in metric_fields
        },
        "depth_counts": _count(
            [row["runtime_summary"]["semantic_metrics"]["depth"] for row in completed]
        ),
        "opening_family_counts": _count(
            [row["surface_profile"]["opening_family"] for row in selected]
        ),
        "opening_semantic_family_counts": _count(
            [
                row["surface_profile"]["opening_semantic_family"]
                for row in selected
            ]
        ),
        "opening_variant_counts": _count(
            [row["surface_profile"]["opening_variant_id"] for row in selected]
        ),
        "ending_family_counts": _count(
            [row["surface_profile"]["ending_family"] for row in selected]
        ),
        "predicate_family_counts": _count(
            [
                family
                for row in selected
                for family in row["surface_profile"]["predicate_families"]
            ]
        ),
        "reception_act_family_counts": _count(
            [
                family
                for row in selected
                for family in row["surface_profile"]["reception_act_families"]
            ]
        ),
        "reception_content_kind_counts": _count(
            [
                row["surface_profile"]["reception_content_kind"]
                for row in selected
            ]
        ),
        "observation_literal_count_total": sum(
            row["surface_profile"]["observation_literal_count"]
            for row in selected
        ),
        "unique_literal_owner_count_total": sum(
            row["surface_profile"]["unique_literal_owner_count"]
            for row in selected
        ),
        "literal_replay_count_total": sum(
            row["surface_profile"]["literal_replay_count"] for row in selected
        ),
        "reception_literal_count_total": sum(
            row["surface_profile"]["reception_literal_count"] for row in selected
        ),
    }
    return value


def _surface_distribution_assessment(
    case_rows: Sequence[Mapping[str, Any]],
    *,
    candidate_version_id: str,
) -> dict[str, Any]:
    """Recompute the current distribution gate from body-free profiles only."""

    if (
        type(case_rows) not in {list, tuple}
        or not _valid_rc(candidate_version_id)
        or STEP11_SURFACE_DISTRIBUTION_POLICY_SHA256
        != FROZEN_STEP11_SURFACE_DISTRIBUTION_POLICY_SHA256
    ):
        raise Step11CycleEvidenceError("SURFACE_DISTRIBUTION_PARENT_INVALID")
    rows: list[dict[str, Any]] = []
    for value in case_rows:
        if type(value) is not dict:
            raise Step11CycleEvidenceError("SURFACE_DISTRIBUTION_ROW_INVALID")
        case_id = value.get("case_id")
        status = value.get("status")
        profile = value.get("surface_profile")
        if case_id not in _CASE_ID_SET or status not in _BATCH_STATUSES:
            raise Step11CycleEvidenceError("SURFACE_DISTRIBUTION_ROW_INVALID")
        if status == "selected":
            profile = _surface_profile(profile)
            receipt = value.get("receipt")
            body_commitment = (
                receipt.get("selected_candidate_body_commitment")
                if type(receipt) is dict
                else None
            )
            if not _valid_nonzero_sha(body_commitment):
                body_commitment = None
        elif profile is not None:
            raise Step11CycleEvidenceError("SURFACE_DISTRIBUTION_ROW_INVALID")
        else:
            body_commitment = None
        rows.append(
            {
                "case_id": case_id,
                "status": status,
                "surface_profile": profile,
                "selected_candidate_body_commitment": body_commitment,
            }
        )
    rows.sort(key=lambda row: row["case_id"])
    if len({row["case_id"] for row in rows}) != len(rows):
        raise Step11CycleEvidenceError("SURFACE_DISTRIBUTION_CASE_DUPLICATE")

    selected = [row for row in rows if row["status"] == "selected"]
    full_100_scope = tuple(row["case_id"] for row in rows) == _CASE_IDS
    variants_by_family: dict[str, Counter[str]] = {}
    for row in selected:
        profile = row["surface_profile"]
        family = profile["opening_semantic_family"]
        variants_by_family.setdefault(family, Counter()).update(
            [profile["opening_variant_id"]]
        )

    # Preserve the predecessor-compatible family view for old evidence readers.  The
    # acceptance authority below does not depend on this sparse >=20 view; it
    # independently evaluates every non-singleton semantic family.
    family_rows: list[dict[str, Any]] = []
    for family in sorted(variants_by_family):
        variant_counts = variants_by_family[family]
        family_count = sum(variant_counts.values())
        dominant_variant_count = max(variant_counts.values())
        distinct_variant_count = len(variant_counts)
        evaluated = family_count >= 20
        passed = (
            distinct_variant_count >= 3
            and dominant_variant_count * 2 <= family_count
            if evaluated
            else None
        )
        family_rows.append(
            {
                "opening_semantic_family": family,
                "case_count": family_count,
                "distinct_variant_count": distinct_variant_count,
                "dominant_variant_count": dominant_variant_count,
                "dominant_variant_share_ppm": (
                    dominant_variant_count * 1_000_000 // family_count
                ),
                "policy_evaluated": evaluated,
                "policy_passed": passed,
            }
        )

    policy = STEP11_SURFACE_DISTRIBUTION_POLICY
    semantic_family_rows: list[dict[str, Any]] = []
    for family in sorted(variants_by_family):
        variant_counts = variants_by_family[family]
        family_count = sum(variant_counts.values())
        dominant_variant_count = max(variant_counts.values())
        distinct_variant_count = len(variant_counts)
        evaluated = family_count >= policy[
            "semantic_family_evaluation_minimum_case_count"
        ]
        passed = (
            distinct_variant_count
            >= policy["semantic_family_minimum_distinct_variant_count"]
            and dominant_variant_count
            * policy["semantic_family_maximum_dominant_share_denominator"]
            <= family_count
            * policy["semantic_family_maximum_dominant_share_numerator"]
            if evaluated
            else None
        )
        semantic_family_rows.append(
            {
                "opening_semantic_family": family,
                "case_count": family_count,
                "distinct_variant_count": distinct_variant_count,
                "dominant_variant_count": dominant_variant_count,
                "dominant_variant_share_ppm": (
                    dominant_variant_count * 1_000_000 // family_count
                ),
                "policy_evaluated": evaluated,
                "policy_passed": passed,
                "singleton_disposition": (
                    None
                    if evaluated
                    else policy["singleton_semantic_family_disposition"]
                ),
            }
        )

    def global_row(
        dimension: str,
        counts: Counter[str],
        *,
        minimum_distinct: int | None,
        maximum_numerator: int,
        maximum_denominator: int,
    ) -> dict[str, Any]:
        total = sum(counts.values())
        dominant = max(counts.values(), default=0)
        distinct = len(counts)
        coverage_complete = total == len(selected) == policy[
            "global_selected_profile_count_required"
        ]
        passed = bool(
            coverage_complete
            and (minimum_distinct is None or distinct >= minimum_distinct)
            and dominant * maximum_denominator <= total * maximum_numerator
        )
        return {
            "dimension": dimension,
            "evaluated_case_count": total,
            "distinct_variant_count": distinct,
            "dominant_variant_count": dominant,
            "dominant_variant_share_ppm": (
                dominant * 1_000_000 // total if total else None
            ),
            "coverage_complete": coverage_complete,
            "policy_evaluated": coverage_complete,
            "policy_passed": passed,
        }

    opening_counts = Counter(
        row["surface_profile"]["opening_variant_id"] for row in selected
    )
    ending_counts = Counter(
        row["surface_profile"]["ending_family"] for row in selected
    )
    skeleton_counts = Counter(
        row["surface_profile"]["near_duplicate_skeleton_commitment"]
        for row in selected
    )
    global_rows = [
        global_row(
            "opening_variant",
            opening_counts,
            minimum_distinct=policy[
                "global_opening_minimum_distinct_variant_count"
            ],
            maximum_numerator=policy[
                "global_opening_maximum_dominant_share_numerator"
            ],
            maximum_denominator=policy[
                "global_opening_maximum_dominant_share_denominator"
            ],
        ),
        global_row(
            "ending_variant",
            ending_counts,
            minimum_distinct=policy[
                "global_ending_minimum_distinct_variant_count"
            ],
            maximum_numerator=policy[
                "global_ending_maximum_dominant_share_numerator"
            ],
            maximum_denominator=policy[
                "global_ending_maximum_dominant_share_denominator"
            ],
        ),
        global_row(
            "surface_skeleton",
            skeleton_counts,
            minimum_distinct=None,
            maximum_numerator=policy[
                "global_skeleton_maximum_dominant_share_numerator"
            ],
            maximum_denominator=policy[
                "global_skeleton_maximum_dominant_share_denominator"
            ],
        ),
    ]

    exact_output_commitments = [
        row["selected_candidate_body_commitment"]
        for row in selected
        if row["selected_candidate_body_commitment"] is not None
    ]
    exact_output_counts = Counter(exact_output_commitments)
    exact_output_duplicate_cluster_count = sum(
        count > 1 for count in exact_output_counts.values()
    )
    exact_output_duplicate_case_count = sum(
        count for count in exact_output_counts.values() if count > 1
    )
    exact_output_coverage_complete = (
        len(exact_output_commitments)
        == len(selected)
        == policy["global_selected_profile_count_required"]
    )
    literal_replay_case_count = sum(
        row["surface_profile"]["literal_replay_count"] > 0 for row in selected
    )
    owned_antecedent_direct_reception_count = sum(
        row["surface_profile"]["reception_content_kind"]
        in {"direct_owned_antecedent", "mixed_owned_antecedent"}
        for row in selected
    )
    family_policy_passed = all(
        row["policy_passed"] is not False for row in family_rows
    )
    semantic_family_policy_passed = all(
        row["policy_passed"] is not False for row in semantic_family_rows
    )
    semantic_family_accounted_case_count = sum(
        row["case_count"] for row in semantic_family_rows
    )
    semantic_family_coverage_complete = bool(
        semantic_family_accounted_case_count
        == len(selected)
        == policy["global_selected_profile_count_required"]
        and all(
            row["policy_evaluated"] is True
            or (
                row["case_count"] == 1
                and row["singleton_disposition"]
                == policy["singleton_semantic_family_disposition"]
            )
            for row in semantic_family_rows
        )
    )
    global_policy_passed = all(
        row["policy_passed"] is True for row in global_rows
    )
    acceptance_passed = bool(
        full_100_scope
        and len(selected) == 100
        and semantic_family_policy_passed
        and semantic_family_coverage_complete
        and global_policy_passed
        and exact_output_coverage_complete
        and exact_output_duplicate_case_count
        <= policy["exact_output_duplicate_case_count_maximum"]
        and literal_replay_case_count == 0
        and owned_antecedent_direct_reception_count == 0
    )
    value = {
        "schema_version": _surface_distribution_schema_for_candidate(
            candidate_version_id
        ),
        "candidate_version_id": candidate_version_id,
        "evaluation_scope": "full_100_only",
        "status": "evaluated" if full_100_scope else "not_applicable",
        "input_authority": "parsed_surface_profile_only",
        "case_count": len(rows),
        "selected_profile_count": len(selected),
        "policy": {
            "opening_family_minimum_case_count": 20,
            "opening_family_minimum_distinct_variant_count": 3,
            "opening_family_maximum_dominant_share_numerator": 1,
            "opening_family_maximum_dominant_share_denominator": 2,
            "literal_replay_case_count_maximum": 0,
            "owned_antecedent_direct_reception_count_maximum": 0,
        },
        "legacy_sparse_family_view_acceptance_authority": False,
        "frozen_acceptance_policy": dict(policy),
        "frozen_acceptance_policy_sha256": (
            STEP11_SURFACE_DISTRIBUTION_POLICY_SHA256
        ),
        "global_rows": global_rows,
        "family_rows": family_rows,
        "evaluated_family_count": sum(
            row["policy_evaluated"] for row in family_rows
        ),
        "failed_family_count": sum(
            row["policy_passed"] is False for row in family_rows
        ),
        "semantic_family_rows": semantic_family_rows,
        "semantic_evaluated_family_count": sum(
            row["policy_evaluated"] for row in semantic_family_rows
        ),
        "semantic_singleton_family_count": sum(
            row["singleton_disposition"] is not None
            for row in semantic_family_rows
        ),
        "semantic_failed_family_count": sum(
            row["policy_passed"] is False for row in semantic_family_rows
        ),
        "semantic_family_accounted_case_count": (
            semantic_family_accounted_case_count
        ),
        "semantic_family_coverage_complete": semantic_family_coverage_complete,
        "global_evaluated_dimension_count": sum(
            row["policy_evaluated"] for row in global_rows
        ),
        "global_failed_dimension_count": sum(
            row["policy_passed"] is False for row in global_rows
        ),
        "exact_output_evaluated_case_count": len(exact_output_commitments),
        "exact_output_coverage_complete": exact_output_coverage_complete,
        "exact_output_duplicate_cluster_count": (
            exact_output_duplicate_cluster_count
        ),
        "exact_output_duplicate_case_count": exact_output_duplicate_case_count,
        "literal_replay_case_count": literal_replay_case_count,
        "owned_antecedent_direct_reception_count": (
            owned_antecedent_direct_reception_count
        ),
        "semantic_contract_consulted": False,
        "case_specific_branching": False,
        "legacy_family_policy_passed": family_policy_passed,
        "global_policy_passed": global_policy_passed,
        "semantic_family_policy_passed": semantic_family_policy_passed,
        "acceptance_passed": acceptance_passed,
        "body_free": True,
    }
    _require_body_free(value)
    return value


def build_step11_batch_run_summary(
    case_rows: Sequence[Mapping[str, Any]],
    *,
    dependency_manifest: Mapping[str, Any],
    run_id: str,
    commitment_key_id: str,
    environment_sha256: str,
    runner_sha256: str,
    runtime_validation_protocol_sha256: str,
    local_review_rubric_sha256: str,
) -> dict[str, Any]:
    dependency = _validated_dependency_manifest(dependency_manifest)
    candidate = dependency["candidate_version_id"]
    closure = dependency["source_dependency_closure_sha256"]
    hashes = (
        commitment_key_id,
        environment_sha256,
        runner_sha256,
        runtime_validation_protocol_sha256,
        local_review_rubric_sha256,
    )
    if (
        type(run_id) is not str
        or _RUN_RE.fullmatch(run_id) is None
        or any(not _valid_nonzero_sha(item) for item in hashes)
        or runtime_validation_protocol_sha256
        != STEP11_RUNTIME_VALIDATION_PROTOCOL_SHA256
        or local_review_rubric_sha256 != STEP11_REVIEW_RUBRIC_SHA256
        or type(case_rows) not in {list, tuple}
    ):
        raise Step11CycleEvidenceError("STEP11_BATCH_PARENT_INVALID")
    rows = [
        _step11_case_row(
            row,
            candidate_version_id=candidate,
            run_id=run_id,
            source_closure=closure,
            commitment_policy_sha256=STEP11_COMMITMENT_POLICY_SHA256,
            environment_sha256=environment_sha256,
            runner_sha256=runner_sha256,
        )
        for row in case_rows
    ]
    rows.sort(key=lambda row: row["case_id"])
    if len({row["case_id"] for row in rows}) != len(rows):
        raise Step11CycleEvidenceError("STEP11_BATCH_CASE_DUPLICATE")
    aggregate = _batch_aggregate(rows)
    surface_distribution_assessment = _surface_distribution_assessment(
        rows, candidate_version_id=candidate
    )
    complete = tuple(row["case_id"] for row in rows) == _CASE_IDS
    clean = bool(
        complete
        and aggregate["selected_count"] == 100
        and aggregate["exception_count"] == 0
        and aggregate["no_valid_candidate_count"] == 0
        and aggregate["v1_fallback_count"] == 0
        and aggregate["hard_gate_pass_count"] == 100
        and aggregate["app_reachable_pass_count"] == 100
        and surface_distribution_assessment["acceptance_passed"] is True
    )
    value = {
        "schema_version": STEP11_BATCH_RUN_SCHEMA,
        "candidate_version_id": candidate,
        "run_id": run_id,
        "batch_id": STEP11_BATCH_ID,
        "batch_manifest_sha256": FROZEN_BATCH001_MANIFEST_SHA256,
        "dependency_manifest_sha256": artifact_sha256(dependency),
        "source_dependency_closure_sha256": closure,
        "source_closure_start_sha256": closure,
        "source_closure_end_sha256": closure,
        "source_closure_stable": True,
        "commitment_policy_sha256": STEP11_COMMITMENT_POLICY_SHA256,
        "commitment_key_id": commitment_key_id,
        "runtime_adapter_version": _runtime_adapter_version_for_candidate(
            candidate
        ),
        "runtime_validation_protocol_sha256": runtime_validation_protocol_sha256,
        "local_review_rubric_sha256": local_review_rubric_sha256,
        "environment_sha256": environment_sha256,
        "runner_sha256": runner_sha256,
        "expected_case_count": 100,
        "executed_case_count": len(rows),
        "all_expected_cases_executed": complete,
        "case_rows": rows,
        "aggregate": aggregate,
        "surface_distribution_assessment": surface_distribution_assessment,
        "aggregate_recomputed_from_case_rows": True,
        "machine_status": "clean" if clean else "failed" if complete else "incomplete",
        "execution_authority": STEP11_EXECUTION_AUTHORITY,
        "body_free": True,
    }
    _require_body_free(value)
    return value


def validate_step11_batch_run_summary(
    value: Any,
    *,
    dependency_manifest: Mapping[str, Any],
) -> tuple[str, ...]:
    if type(value) is not dict or type(value.get("case_rows")) is not list:
        return ("STEP11_BATCH_SUMMARY_MAPPING_REQUIRED",)
    try:
        expected = build_step11_batch_run_summary(
            value["case_rows"],
            dependency_manifest=dependency_manifest,
            run_id=value.get("run_id"),
            commitment_key_id=value.get("commitment_key_id"),
            environment_sha256=value.get("environment_sha256"),
            runner_sha256=value.get("runner_sha256"),
            runtime_validation_protocol_sha256=value.get(
                "runtime_validation_protocol_sha256"
            ),
            local_review_rubric_sha256=value.get("local_review_rubric_sha256"),
        )
    except (KeyError, TypeError, ValueError, Step11CycleEvidenceError):
        return ("STEP11_BATCH_SUMMARY_CONTRACT_INVALID",)
    return () if value == expected else ("STEP11_BATCH_SUMMARY_RECOMPUTATION_MISMATCH",)


def build_step11_private_verification_receipt(
    final_batch_summary: Mapping[str, Any],
    *,
    final_dependency_manifest: Mapping[str, Any],
    private_packet_commitment: str,
    initial_private_packet_commitment: str,
    initial_batch_summary_sha256: str,
    verifier_sha256: str,
    verified_case_count: int,
    initial_verified_case_count: int,
) -> dict[str, Any]:
    """Bind the successful private HMAC recomputation to public evidence."""

    dependency = _validated_dependency_manifest(final_dependency_manifest)
    if validate_step11_batch_run_summary(
        final_batch_summary, dependency_manifest=dependency
    ):
        raise Step11CycleEvidenceError(
            "STEP11_PRIVATE_VERIFICATION_SUMMARY_INVALID"
        )
    by_path = {row["path"]: row["sha256"] for row in dependency["file_hashes"]}
    aggregate = final_batch_summary["aggregate"]
    if (
        any(
            not _valid_nonzero_sha(value)
            for value in (
                private_packet_commitment,
                initial_private_packet_commitment,
                initial_batch_summary_sha256,
                verifier_sha256,
            )
        )
        or verifier_sha256
        != by_path.get("ai/tools/emlis_nls_v3_step11_batch_run.py")
        or type(verified_case_count) is not int
        or type(verified_case_count) is bool
        or verified_case_count != final_batch_summary["executed_case_count"]
        or verified_case_count != 100
        or type(initial_verified_case_count) is not int
        or type(initial_verified_case_count) is bool
        or initial_verified_case_count != 100
    ):
        raise Step11CycleEvidenceError(
            "STEP11_PRIVATE_VERIFICATION_PARENT_INVALID"
        )
    value = {
        "schema_version": STEP11_PRIVATE_VERIFICATION_RECEIPT_SCHEMA,
        "cycle_id": STEP11_CYCLE_ID,
        "candidate_version_id": final_batch_summary["candidate_version_id"],
        "run_id": final_batch_summary["run_id"],
        "source_dependency_closure_sha256": final_batch_summary[
            "source_dependency_closure_sha256"
        ],
        "dependency_manifest_sha256": artifact_sha256(dependency),
        "final_batch_summary_sha256": artifact_sha256(final_batch_summary),
        "initial_batch_summary_sha256": initial_batch_summary_sha256,
        "commitment_policy_sha256": final_batch_summary[
            "commitment_policy_sha256"
        ],
        "commitment_key_id": final_batch_summary["commitment_key_id"],
        "private_packet_commitment": private_packet_commitment,
        "initial_private_packet_commitment": initial_private_packet_commitment,
        "verifier_sha256": verifier_sha256,
        "verified_case_count": verified_case_count,
        "verified_selected_count": aggregate["selected_count"],
        "verified_no_valid_candidate_count": aggregate[
            "no_valid_candidate_count"
        ],
        "verified_exception_count": aggregate["exception_count"],
        "initial_verified_case_count": initial_verified_case_count,
        "private_packet_validation_status": "clean",
        "initial_evidence_validation_status": "clean",
        "body_free": True,
    }
    _require_body_free(value)
    return value


def validate_step11_private_verification_receipt(
    value: Any,
    *,
    final_batch_summary: Mapping[str, Any],
    final_dependency_manifest: Mapping[str, Any],
) -> tuple[str, ...]:
    if type(value) is not dict:
        return ("STEP11_PRIVATE_VERIFICATION_RECEIPT_MAPPING_REQUIRED",)
    try:
        expected = build_step11_private_verification_receipt(
            final_batch_summary,
            final_dependency_manifest=final_dependency_manifest,
            private_packet_commitment=value.get("private_packet_commitment"),
            initial_private_packet_commitment=value.get(
                "initial_private_packet_commitment"
            ),
            initial_batch_summary_sha256=value.get(
                "initial_batch_summary_sha256"
            ),
            verifier_sha256=value.get("verifier_sha256"),
            verified_case_count=value.get("verified_case_count"),
            initial_verified_case_count=value.get("initial_verified_case_count"),
        )
    except (KeyError, TypeError, ValueError, Step11CycleEvidenceError):
        return ("STEP11_PRIVATE_VERIFICATION_RECEIPT_CONTRACT_INVALID",)
    return () if value == expected else (
        "STEP11_PRIVATE_VERIFICATION_RECEIPT_RECOMPUTATION_MISMATCH",
    )


def _project_historical_initial(summary: Any) -> dict[str, Any]:
    if type(summary) is not dict or validate_historical_batch_run_summary(summary):
        raise Step11CycleEvidenceError("INITIAL_BATCH_SUMMARY_CONTRACT_INVALID")
    if (
        summary.get("candidate_version_id") != STEP11_INITIAL_CANDIDATE_VERSION_ID
        or summary.get("batch_id") != STEP11_BATCH_ID
        or summary.get("batch_manifest_sha256")
        != FROZEN_BATCH001_MANIFEST_SHA256
        or summary.get("source_dependency_closure_sha256")
        != FROZEN_STEP10_DEPENDENCY_CLOSURE_SHA256
        or summary.get("expected_case_count") != 100
        or summary.get("executed_case_count") != 100
        or summary.get("all_expected_cases_executed") is not True
        or type(summary.get("case_rows")) is not list
    ):
        raise Step11CycleEvidenceError("INITIAL_BATCH_PARENT_INVALID")
    rows: list[dict[str, Any]] = []
    for raw in summary["case_rows"]:
        receipt = raw.get("receipt") if type(raw) is dict else None
        status = raw.get("status") if type(raw) is dict else None
        if status not in _BATCH_STATUSES:
            raise Step11CycleEvidenceError("INITIAL_BATCH_CASE_STATUS_INVALID")
        body = (
            receipt.get("selected_candidate_body_commitment")
            if status == "selected" and type(receipt) is dict
            else None
        )
        gate = (
            receipt.get("hard_gate", {}).get("status")
            if type(receipt) is dict
            else "not_evaluated"
        )
        rows.append(
            {
                "case_id": raw["case_id"],
                "case_identity_commitment": raw["case_identity_commitment"],
                "v1_baseline_body_commitment": raw[
                    "v1_baseline_body_commitment"
                ],
                "selected_candidate_body_commitment": body,
                "status": status,
                "failure_code": raw.get("failure_code"),
                "hard_gate_status": gate,
                "v1_fallback_used": bool(
                    type(raw.get("runtime_summary")) is dict
                    and raw["runtime_summary"].get("v1_fallback_used") is True
                ),
                "case_row_sha256": artifact_sha256(raw),
            }
        )
    rows.sort(key=lambda row: row["case_id"])
    if tuple(row["case_id"] for row in rows) != _CASE_IDS:
        raise Step11CycleEvidenceError("INITIAL_BATCH_CASE_SET_INVALID")
    projection = {
        "summary_schema_version": summary["schema_version"],
        "candidate_version_id": summary["candidate_version_id"],
        "run_id": summary["run_id"],
        "batch_id": summary["batch_id"],
        "batch_manifest_sha256": summary["batch_manifest_sha256"],
        "source_dependency_closure_sha256": summary[
            "source_dependency_closure_sha256"
        ],
        "commitment_policy_sha256": summary["commitment_policy_sha256"],
        "commitment_key_id": summary["commitment_key_id"],
        "executed_case_count": 100,
        "all_expected_cases_executed": True,
        "machine_status": summary["machine_status"],
        "case_rows": rows,
        "summary_sha256": artifact_sha256(summary),
    }
    _require_body_free(projection)
    return projection


def _project_step11_final(
    summary: Any,
    dependency_manifest: Mapping[str, Any],
) -> dict[str, Any]:
    candidate_version_id = (
        summary.get("candidate_version_id")
        if type(summary) is dict
        else None
    )
    if (
        type(summary) is not dict
        or candidate_version_id
        not in {
            STEP11_SUCCESSOR_CANDIDATE_VERSION_ID,
            STEP11_HISTORICAL_RC0021_CANDIDATE_VERSION_ID,
            STEP11_HISTORICAL_RC0022_CANDIDATE_VERSION_ID,
            STEP11_HISTORICAL_RC0023_CANDIDATE_VERSION_ID,
            STEP11_CURRENT_CANDIDATE_VERSION_ID,
        }
        or dependency_manifest.get("candidate_version_id")
        != candidate_version_id
        or validate_step11_batch_run_summary(
        summary, dependency_manifest=dependency_manifest
        )
    ):
        raise Step11CycleEvidenceError("FINAL_BATCH_SUMMARY_CONTRACT_INVALID")
    rows = []
    for raw in summary["case_rows"]:
        receipt = raw.get("receipt")
        status = raw["status"]
        rows.append(
            {
                "case_id": raw["case_id"],
                "case_identity_commitment": raw["case_identity_commitment"],
                "v1_baseline_body_commitment": raw[
                    "v1_baseline_body_commitment"
                ],
                "selected_candidate_body_commitment": (
                    receipt["selected_candidate_body_commitment"]
                    if status == "selected"
                    else None
                ),
                "status": status,
                "failure_code": raw["failure_code"],
                "hard_gate_status": (
                    receipt["hard_gate"]["status"]
                    if type(receipt) is dict
                    else "not_evaluated"
                ),
                "v1_fallback_used": raw["v1_fallback_used"],
                "case_row_sha256": artifact_sha256(raw),
            }
        )
    projection = {
        "summary_schema_version": STEP11_BATCH_RUN_SCHEMA,
        "candidate_version_id": summary["candidate_version_id"],
        "run_id": summary["run_id"],
        "batch_id": summary["batch_id"],
        "batch_manifest_sha256": summary["batch_manifest_sha256"],
        "source_dependency_closure_sha256": summary[
            "source_dependency_closure_sha256"
        ],
        "commitment_policy_sha256": summary["commitment_policy_sha256"],
        "commitment_key_id": summary["commitment_key_id"],
        "executed_case_count": summary["executed_case_count"],
        "all_expected_cases_executed": summary["all_expected_cases_executed"],
        "machine_status": summary["machine_status"],
        "case_rows": rows,
        "summary_sha256": artifact_sha256(summary),
    }
    _require_body_free(projection)
    return projection


def _project_final(
    summary: Any,
    dependency_manifest: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if type(summary) is not dict:
        raise Step11CycleEvidenceError("FINAL_BATCH_SUMMARY_MAPPING_REQUIRED")
    if summary.get("schema_version") == STEP11_BATCH_RUN_SCHEMA:
        if dependency_manifest is None:
            raise Step11CycleEvidenceError("FINAL_DEPENDENCY_MANIFEST_REQUIRED")
        projection = _project_step11_final(summary, dependency_manifest)
    else:
        if dependency_manifest is not None:
            raise Step11CycleEvidenceError("INITIAL_RC_DEPENDENCY_MANIFEST_FORBIDDEN")
        projection = _project_historical_initial(summary)
    rows = projection["case_rows"]
    if (
        projection["machine_status"] != "clean"
        or projection["executed_case_count"] != 100
        or projection["all_expected_cases_executed"] is not True
        or any(
            row["status"] != "selected"
            or row["hard_gate_status"] != "passed"
            or not _valid_nonzero_sha(row["v1_baseline_body_commitment"])
            or not _valid_nonzero_sha(row["selected_candidate_body_commitment"])
            or row["v1_fallback_used"] is not False
            for row in rows
        )
    ):
        raise Step11CycleEvidenceError("FINAL_BATCH_NOT_COMPLETE_CLEAN_100")
    return projection


def _case_bindings(projection: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "case_id": row["case_id"],
            "case_identity_commitment": row["case_identity_commitment"],
            "v1_baseline_body_commitment": row[
                "v1_baseline_body_commitment"
            ],
            "selected_candidate_body_commitment": row[
                "selected_candidate_body_commitment"
            ],
            "status": row["status"],
            "failure_code": row["failure_code"],
            "hard_gate_status": row["hard_gate_status"],
            "case_row_sha256": row["case_row_sha256"],
        }
        for row in projection["case_rows"]
    ]


def build_initial_run_lock(
    batch_summary: Mapping[str, Any],
    corpus_validation: Mapping[str, Any],
    *,
    lock_id: str,
) -> dict[str, Any]:
    if type(lock_id) is not str or _LOCK_RE.fullmatch(lock_id) is None:
        raise Step11CycleEvidenceError("INITIAL_LOCK_ID_INVALID")
    corpus = _validated_corpus(corpus_validation)
    projection = _project_historical_initial(batch_summary)
    rows = projection["case_rows"]
    aggregate = {
        "expected_case_count": 100,
        "executed_case_count": 100,
        "selected_count": sum(row["status"] == "selected" for row in rows),
        "exception_count": sum(row["status"] == "exception" for row in rows),
        "no_valid_candidate_count": sum(
            row["status"] == "v3_no_valid_candidate" for row in rows
        ),
        "v1_fallback_count": sum(row["v1_fallback_used"] for row in rows),
    }
    value = {
        "schema_version": INITIAL_RUN_LOCK_SCHEMA,
        "cycle_id": STEP11_CYCLE_ID,
        "lock_id": lock_id,
        "state": "INITIAL_RUN_LOCKED",
        "batch_id": STEP11_BATCH_ID,
        "candidate_version_id": STEP11_INITIAL_CANDIDATE_VERSION_ID,
        "run_id": projection["run_id"],
        "parent_summary_schema_version": projection["summary_schema_version"],
        "batch_manifest_sha256": FROZEN_BATCH001_MANIFEST_SHA256,
        "step10_manifest_sha256": FROZEN_STEP10_MANIFEST_SHA256,
        "source_dependency_closure_sha256": FROZEN_STEP10_DEPENDENCY_CLOSURE_SHA256,
        "commitment_policy_sha256": projection["commitment_policy_sha256"],
        "commitment_key_id": projection["commitment_key_id"],
        "corpus_validation_sha256": artifact_sha256(corpus),
        "initial_batch_summary_sha256": projection["summary_sha256"],
        "case_bindings": _case_bindings(projection),
        "aggregate": aggregate,
        "parent_step10_smoke_artifact_unchanged": True,
        "append_only": True,
        "body_free": True,
    }
    _require_body_free(value)
    return value


def validate_initial_run_lock(
    value: Any,
    *,
    batch_summary: Mapping[str, Any],
    corpus_validation: Mapping[str, Any],
) -> tuple[str, ...]:
    if type(value) is not dict:
        return ("INITIAL_LOCK_MAPPING_REQUIRED",)
    try:
        expected = build_initial_run_lock(
            batch_summary,
            corpus_validation,
            lock_id=value.get("lock_id"),
        )
    except (KeyError, TypeError, ValueError, Step11CycleEvidenceError):
        return ("INITIAL_LOCK_PARENT_OR_CONTRACT_INVALID",)
    return () if value == expected else ("INITIAL_LOCK_RECOMPUTATION_MISMATCH",)


def _validated_initial_lock(
    value: Any,
    *,
    batch_summary: Mapping[str, Any],
    corpus_validation: Mapping[str, Any],
) -> dict[str, Any]:
    if validate_initial_run_lock(
        value,
        batch_summary=batch_summary,
        corpus_validation=corpus_validation,
    ):
        raise Step11CycleEvidenceError("INITIAL_LOCK_INVALID")
    return dict(value)


_STEP11_REVIEW_RUBRIC = {
    "schema_version": "cocolon.emlis.nls_v3.local_review_rubric.step11.v1",
    "axes": list(LOCAL_REVIEW_AXES),
    "pass_codes": sorted(LOCAL_REVIEW_PASS_CODES),
    "failure_codes": sorted(_STEP11_REVIEW_FAILURE_CODES),
    "severities": sorted(_SEVERITIES),
    "failure_taxonomy_parent_sha256": FAILURE_TAXONOMY_SHA256,
    "free_text_forbidden": True,
}
STEP11_REVIEW_RUBRIC_SHA256 = artifact_sha256(_STEP11_REVIEW_RUBRIC)


def _review_decision(value: Any) -> dict[str, Any]:
    return _require_exact_keys(
        value,
        {"case_id", "status", "axis_results", "reason_codes", "severity"},
        "LOCAL_REVIEW_DECISION_SHAPE_INVALID",
    )


def _build_review_row(
    decision: Mapping[str, Any],
    binding: Mapping[str, Any],
    *,
    run_id: str,
) -> dict[str, Any]:
    status = decision["status"]
    axes = decision["axis_results"]
    codes = decision["reason_codes"]
    severity = decision["severity"]
    if (
        status not in {"passed", "failed"}
        or type(axes) is not dict
        or set(axes) != set(LOCAL_REVIEW_AXES)
        or any(value not in {"passed", "failed"} for value in axes.values())
        or type(codes) not in {list, tuple}
        or type(run_id) is not str
        or _RUN_RE.fullmatch(run_id) is None
    ):
        raise Step11CycleEvidenceError("LOCAL_REVIEW_RUBRIC_INVALID")
    normalized_codes = sorted(set(codes))
    if len(normalized_codes) != len(codes):
        raise Step11CycleEvidenceError("LOCAL_REVIEW_RUBRIC_INVALID")
    if status == "passed":
        if (
            set(axes.values()) != {"passed"}
            or not normalized_codes
            or any(code not in LOCAL_REVIEW_PASS_CODES for code in normalized_codes)
            or severity is not None
            or binding["status"] != "selected"
        ):
            raise Step11CycleEvidenceError("LOCAL_REVIEW_PASSED_STATE_INVALID")
    else:
        if (
            "failed" not in set(axes.values())
            or not normalized_codes
            or any(code not in _STEP11_REVIEW_FAILURE_CODES for code in normalized_codes)
            or severity not in _SEVERITIES
        ):
            raise Step11CycleEvidenceError("LOCAL_REVIEW_FAILED_STATE_INVALID")
        required_machine_code = {
            "exception": "EXECUTION_EXCEPTION",
            "v3_no_valid_candidate": "NO_VALID_CANDIDATE",
        }.get(binding["status"])
        if required_machine_code is not None and (
            required_machine_code not in normalized_codes
            or severity != "BLOCKER"
        ):
            raise Step11CycleEvidenceError("LOCAL_REVIEW_MACHINE_FAILURE_NOT_RECORDED")
    value = {
        "schema_version": "cocolon.emlis.nls_v3.local_product_review.step11.v1",
        "case_identity_commitment": binding["case_identity_commitment"],
        "case_outcome_commitment": binding["case_row_sha256"],
        "run_id": run_id,
        "selected_candidate_body_commitment": binding[
            "selected_candidate_body_commitment"
        ],
        "status": status,
        "axis_results": {axis: axes[axis] for axis in LOCAL_REVIEW_AXES},
        "severity": severity,
        "reason_codes": normalized_codes,
        "rubric_sha256": STEP11_REVIEW_RUBRIC_SHA256,
        "body_free": True,
    }
    _require_body_free(value)
    return value


def _review_aggregate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    reviews = [row["review"] for row in rows]
    severities = [review["severity"] for review in reviews if review["severity"] is not None]
    return {
        "case_count": len(rows),
        "reviewed_count": len(rows),
        "passed_count": sum(review["status"] == "passed" for review in reviews),
        "failed_count": sum(review["status"] == "failed" for review in reviews),
        "severity_counts": _count(severities),
        "reason_code_counts": _count(
            [code for review in reviews for code in review["reason_codes"]]
        ),
        "axis_failure_counts": _count(
            [
                axis
                for review in reviews
                for axis, status in review["axis_results"].items()
                if status == "failed"
            ]
        ),
        "unresolved_blocker_major_count": sum(
            review["severity"] in _BLOCKING_SEVERITIES for review in reviews
        ),
    }


def _assert_projection_continuity(
    lock: Mapping[str, Any],
    projection: Mapping[str, Any],
) -> None:
    if (
        projection["batch_id"] != STEP11_BATCH_ID
        or projection["batch_manifest_sha256"] != lock["batch_manifest_sha256"]
        or projection["commitment_policy_sha256"]
        != lock["commitment_policy_sha256"]
        or projection["commitment_key_id"] != lock["commitment_key_id"]
    ):
        raise Step11CycleEvidenceError("CYCLE_SUMMARY_CONTINUITY_INVALID")
    initial_by_case = {row["case_id"]: row for row in lock["case_bindings"]}
    if any(
        row["case_id"] not in initial_by_case
        or row["case_identity_commitment"]
        != initial_by_case[row["case_id"]]["case_identity_commitment"]
        or row["v1_baseline_body_commitment"]
        != initial_by_case[row["case_id"]]["v1_baseline_body_commitment"]
        for row in projection["case_rows"]
    ):
        raise Step11CycleEvidenceError("CYCLE_CASE_IDENTITY_CONTINUITY_INVALID")


def build_local_review_set(
    initial_lock: Mapping[str, Any],
    initial_batch_summary: Mapping[str, Any],
    corpus_validation: Mapping[str, Any],
    batch_summary: Mapping[str, Any],
    decisions: Sequence[Mapping[str, Any]],
    *,
    review_stage: str,
    dependency_manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    lock = _validated_initial_lock(
        initial_lock,
        batch_summary=initial_batch_summary,
        corpus_validation=corpus_validation,
    )
    if review_stage not in _REVIEW_STAGES:
        raise Step11CycleEvidenceError("LOCAL_REVIEW_STAGE_INVALID")
    projection = (
        _project_historical_initial(batch_summary)
        if review_stage == "initial"
        else _project_final(batch_summary, dependency_manifest)
    )
    if review_stage == "initial" and projection["summary_sha256"] != lock[
        "initial_batch_summary_sha256"
    ]:
        raise Step11CycleEvidenceError("INITIAL_REVIEW_PARENT_MISMATCH")
    _assert_projection_continuity(lock, projection)
    if type(decisions) not in {list, tuple} or len(decisions) != 100:
        raise Step11CycleEvidenceError("LOCAL_REVIEW_EXACT_100_REQUIRED")
    by_case: dict[str, dict[str, Any]] = {}
    for raw in decisions:
        decision = _review_decision(raw)
        case_id = decision["case_id"]
        if type(case_id) is not str or case_id not in _CASE_ID_SET or case_id in by_case:
            raise Step11CycleEvidenceError("LOCAL_REVIEW_CASE_SET_INVALID")
        by_case[case_id] = decision
    if set(by_case) != _CASE_ID_SET:
        raise Step11CycleEvidenceError("LOCAL_REVIEW_CASE_SET_INVALID")
    binding_by_case = {row["case_id"]: row for row in projection["case_rows"]}
    rows = [
        {
            "case_id": case_id,
            "review_stage": review_stage,
            "review": _build_review_row(
                by_case[case_id], binding_by_case[case_id], run_id=projection["run_id"]
            ),
        }
        for case_id in _CASE_IDS
    ]
    value = {
        "schema_version": LOCAL_REVIEW_SET_SCHEMA,
        "cycle_id": STEP11_CYCLE_ID,
        "review_stage": review_stage,
        "state": "REVIEWED",
        "batch_id": STEP11_BATCH_ID,
        "candidate_version_id": projection["candidate_version_id"],
        "run_id": projection["run_id"],
        "summary_schema_version": projection["summary_schema_version"],
        "initial_lock_sha256": artifact_sha256(lock),
        "batch_summary_sha256": projection["summary_sha256"],
        "rows": rows,
        "aggregate": _review_aggregate(rows),
        "aggregate_recomputed_from_rows": True,
        "body_free": True,
    }
    _require_body_free(value)
    return value


def validate_local_review_set(
    value: Any,
    *,
    initial_lock: Mapping[str, Any],
    initial_batch_summary: Mapping[str, Any],
    corpus_validation: Mapping[str, Any],
    batch_summary: Mapping[str, Any],
    dependency_manifest: Mapping[str, Any] | None = None,
) -> tuple[str, ...]:
    if type(value) is not dict or type(value.get("rows")) is not list:
        return ("LOCAL_REVIEW_SET_MAPPING_REQUIRED",)
    decisions: list[dict[str, Any]] = []
    try:
        for row in value["rows"]:
            row = _require_exact_keys(
                row,
                {"case_id", "review_stage", "review"},
                "LOCAL_REVIEW_ROW_INVALID",
            )
            review = row["review"]
            if type(review) is not dict:
                raise Step11CycleEvidenceError("LOCAL_REVIEW_ROW_INVALID")
            decisions.append(
                {
                    "case_id": row["case_id"],
                    "status": review.get("status"),
                    "axis_results": review.get("axis_results"),
                    "reason_codes": review.get("reason_codes"),
                    "severity": review.get("severity"),
                }
            )
        expected = build_local_review_set(
            initial_lock,
            initial_batch_summary,
            corpus_validation,
            batch_summary,
            decisions,
            review_stage=value.get("review_stage"),
            dependency_manifest=dependency_manifest,
        )
    except (KeyError, TypeError, ValueError, Step11CycleEvidenceError):
        return ("LOCAL_REVIEW_SET_PARENT_OR_CONTRACT_INVALID",)
    return () if value == expected else ("LOCAL_REVIEW_SET_RECOMPUTATION_MISMATCH",)


def _validated_review_set(
    value: Any,
    *,
    initial_lock: Mapping[str, Any],
    initial_batch_summary: Mapping[str, Any],
    corpus_validation: Mapping[str, Any],
    batch_summary: Mapping[str, Any],
    expected_stage: str,
    dependency_manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if (
        type(value) is not dict
        or value.get("review_stage") != expected_stage
        or validate_local_review_set(
            value,
            initial_lock=initial_lock,
            initial_batch_summary=initial_batch_summary,
            corpus_validation=corpus_validation,
            batch_summary=batch_summary,
            dependency_manifest=dependency_manifest,
        )
    ):
        raise Step11CycleEvidenceError("LOCAL_REVIEW_SET_INVALID")
    return dict(value)


def build_output_diff(
    initial_lock: Mapping[str, Any],
    initial_batch_summary: Mapping[str, Any],
    corpus_validation: Mapping[str, Any],
    final_batch_summary: Mapping[str, Any],
    *,
    final_dependency_manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    lock = _validated_initial_lock(
        initial_lock,
        batch_summary=initial_batch_summary,
        corpus_validation=corpus_validation,
    )
    before = _project_historical_initial(initial_batch_summary)
    after = _project_final(final_batch_summary, final_dependency_manifest)
    _assert_projection_continuity(lock, after)
    left = {row["case_id"]: row for row in before["case_rows"]}
    right = {row["case_id"]: row for row in after["case_rows"]}
    rows = []
    for case_id in _CASE_IDS:
        previous = left[case_id]
        current = right[case_id]
        changed = previous["selected_candidate_body_commitment"] != current[
            "selected_candidate_body_commitment"
        ]
        rows.append(
            {
                "case_id": case_id,
                "case_identity_commitment": previous["case_identity_commitment"],
                "previous_body_commitment": previous[
                    "selected_candidate_body_commitment"
                ],
                "current_body_commitment": current[
                    "selected_candidate_body_commitment"
                ],
                "previous_status": previous["status"],
                "current_status": current["status"],
                "changed": changed,
            }
        )
    value = {
        "schema_version": OUTPUT_DIFF_SCHEMA,
        "cycle_id": STEP11_CYCLE_ID,
        "batch_id": STEP11_BATCH_ID,
        "batch_manifest_sha256": FROZEN_BATCH001_MANIFEST_SHA256,
        "previous_candidate_version_id": before["candidate_version_id"],
        "current_candidate_version_id": after["candidate_version_id"],
        "previous_run_id": before["run_id"],
        "current_run_id": after["run_id"],
        "previous_batch_summary_sha256": before["summary_sha256"],
        "current_batch_summary_sha256": after["summary_sha256"],
        "previous_source_dependency_closure_sha256": before[
            "source_dependency_closure_sha256"
        ],
        "current_source_dependency_closure_sha256": after[
            "source_dependency_closure_sha256"
        ],
        "commitment_policy_sha256": lock["commitment_policy_sha256"],
        "commitment_key_id": lock["commitment_key_id"],
        "case_rows": rows,
        "aggregate": {
            "case_count": 100,
            "changed_count": sum(row["changed"] for row in rows),
            "unchanged_count": sum(not row["changed"] for row in rows),
        },
        "body_free": True,
    }
    _require_body_free(value)
    return value


def validate_output_diff(
    value: Any,
    *,
    initial_lock: Mapping[str, Any],
    initial_batch_summary: Mapping[str, Any],
    corpus_validation: Mapping[str, Any],
    final_batch_summary: Mapping[str, Any],
    final_dependency_manifest: Mapping[str, Any] | None = None,
) -> tuple[str, ...]:
    try:
        expected = build_output_diff(
            initial_lock,
            initial_batch_summary,
            corpus_validation,
            final_batch_summary,
            final_dependency_manifest=final_dependency_manifest,
        )
    except (KeyError, TypeError, ValueError, Step11CycleEvidenceError):
        return ("OUTPUT_DIFF_PARENT_OR_CONTRACT_INVALID",)
    return () if value == expected else ("OUTPUT_DIFF_RECOMPUTATION_MISMATCH",)


def build_output_change_review(
    initial_lock: Mapping[str, Any],
    initial_batch_summary: Mapping[str, Any],
    corpus_validation: Mapping[str, Any],
    initial_review_set: Mapping[str, Any],
    final_batch_summary: Mapping[str, Any],
    final_review_set: Mapping[str, Any],
    output_diff: Mapping[str, Any],
    *,
    final_dependency_manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    lock = _validated_initial_lock(
        initial_lock,
        batch_summary=initial_batch_summary,
        corpus_validation=corpus_validation,
    )
    initial = _validated_review_set(
        initial_review_set,
        initial_lock=lock,
        initial_batch_summary=initial_batch_summary,
        corpus_validation=corpus_validation,
        batch_summary=initial_batch_summary,
        expected_stage="initial",
    )
    final = _validated_review_set(
        final_review_set,
        initial_lock=lock,
        initial_batch_summary=initial_batch_summary,
        corpus_validation=corpus_validation,
        batch_summary=final_batch_summary,
        expected_stage="final",
        dependency_manifest=final_dependency_manifest,
    )
    expected_diff = build_output_diff(
        lock,
        initial_batch_summary,
        corpus_validation,
        final_batch_summary,
        final_dependency_manifest=final_dependency_manifest,
    )
    if output_diff != expected_diff:
        raise Step11CycleEvidenceError("OUTPUT_DIFF_PARENT_MISMATCH")
    initial_blocking = {
        row["case_id"]
        for row in initial["rows"]
        if row["review"]["severity"] in _BLOCKING_SEVERITIES
    }
    changed = {row["case_id"] for row in output_diff["case_rows"] if row["changed"]}
    required = changed | initial_blocking
    final_by_case = {row["case_id"]: row for row in final["rows"]}
    rows = [
        {
            "case_id": case_id,
            "changed_output": case_id in changed,
            "initial_blocking_failure": case_id in initial_blocking,
            "final_review_row_sha256": artifact_sha256(final_by_case[case_id]),
            "final_review_status": final_by_case[case_id]["review"]["status"],
            "final_review_severity": final_by_case[case_id]["review"]["severity"],
        }
        for case_id in sorted(required)
    ]
    value = {
        "schema_version": OUTPUT_CHANGE_REVIEW_SCHEMA,
        "cycle_id": STEP11_CYCLE_ID,
        "initial_lock_sha256": artifact_sha256(lock),
        "initial_review_set_sha256": artifact_sha256(initial),
        "final_batch_summary_sha256": artifact_sha256(final_batch_summary),
        "final_dependency_manifest_sha256": artifact_sha256(
            final_dependency_manifest
        ),
        "final_review_set_sha256": artifact_sha256(final),
        "output_diff_sha256": artifact_sha256(output_diff),
        "previous_batch_summary_sha256": lock["initial_batch_summary_sha256"],
        "current_batch_summary_sha256": final["batch_summary_sha256"],
        "rows": rows,
        "aggregate": {
            "changed_case_count": len(changed),
            "initial_blocking_case_count": len(initial_blocking),
            "required_review_case_count": len(required),
            "completed_review_case_count": len(rows),
        },
        "status": "complete",
        "body_free": True,
    }
    _require_body_free(value)
    return value


def validate_output_change_review(
    value: Any,
    **parents: Any,
) -> tuple[str, ...]:
    try:
        expected = build_output_change_review(**parents)
    except (KeyError, TypeError, ValueError, Step11CycleEvidenceError):
        return ("OUTPUT_CHANGE_REVIEW_PARENT_OR_CONTRACT_INVALID",)
    return () if value == expected else ("OUTPUT_CHANGE_REVIEW_RECOMPUTATION_MISMATCH",)


_KNOWN28_ROW_KEYS = {
    "case_ref",
    "legacy_input_commitment",
    "projected_input_commitment",
    "applicability_binding_commitment",
    "applicability_status",
    "applicability_issue_codes",
    "v1_baseline_body_commitment",
    "selected_candidate_body_commitment",
    "status",
    "hard_gate_status",
    "failure_codes",
    "exception",
    "v1_fallback_used",
}


def _known28_row(value: Any) -> dict[str, Any]:
    row = _require_exact_keys(value, _KNOWN28_ROW_KEYS, "KNOWN28_ROW_SHAPE_INVALID")
    applicability_codes = row["applicability_issue_codes"]
    failure_codes = row["failure_codes"]
    if (
        row["case_ref"] not in set(_KNOWN28_CASE_REFS)
        or not _valid_nonzero_sha(row["legacy_input_commitment"])
        or not _valid_nonzero_sha(row["applicability_binding_commitment"])
        or not _valid_nonzero_sha(row["v1_baseline_body_commitment"])
        or row["applicability_status"]
        not in {"app_reachable", "expected_non_applicable"}
        or type(applicability_codes) is not list
        or len(applicability_codes) != len(set(applicability_codes))
        or any(
            type(code) is not str or _ISSUE_RE.fullmatch(code) is None
            for code in applicability_codes
        )
        or row["status"] not in {"selected", "expected_non_applicable"}
        or row["hard_gate_status"] not in {"passed", "not_applicable"}
        or type(failure_codes) is not list
        or failure_codes != sorted(set(failure_codes))
        or any(
            type(code) is not str or _CODE_RE.fullmatch(code) is None
            for code in failure_codes
        )
        or type(row["exception"]) is not bool
        or type(row["v1_fallback_used"]) is not bool
        or row["exception"] is not False
        or row["v1_fallback_used"] is not False
        or failure_codes
    ):
        raise Step11CycleEvidenceError("KNOWN28_ROW_INVALID")
    if row["applicability_status"] == "app_reachable":
        if (
            applicability_codes
            or not _valid_nonzero_sha(row["projected_input_commitment"])
            or row["status"] != "selected"
            or row["hard_gate_status"] != "passed"
            or not _valid_nonzero_sha(row["selected_candidate_body_commitment"])
        ):
            raise Step11CycleEvidenceError("KNOWN28_SELECTED_ROW_INVALID")
    elif (
        not applicability_codes
        or row["projected_input_commitment"] is not None
        or row["status"] != "expected_non_applicable"
        or row["hard_gate_status"] != "not_applicable"
        or row["selected_candidate_body_commitment"] is not None
    ):
        raise Step11CycleEvidenceError("KNOWN28_NON_APPLICABLE_ROW_INVALID")
    _require_body_free(row)
    return row


def _known28_aggregate(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    expected_by_ref = {
        row["case_ref"]: row
        for row in KNOWN28_EXPECTED_APPLICABILITY["cases"]
    }
    app_matches = []
    nonapp_matches = []
    for row in rows:
        expected = expected_by_ref[row["case_ref"]]
        app_matches.append(
            expected["applicability_status"] == "app_reachable"
            and expected["expected_issue_codes"] == []
            and row["applicability_status"] == "app_reachable"
            and row["applicability_issue_codes"] == []
            and row["status"] == "selected"
            and row["hard_gate_status"] == "passed"
        )
        nonapp_matches.append(
            expected["applicability_status"] == "expected_non_applicable"
            and row["applicability_status"] == "expected_non_applicable"
            and row["applicability_issue_codes"]
            == expected["expected_issue_codes"]
            and row["status"] == "expected_non_applicable"
            and row["hard_gate_status"] == "not_applicable"
        )
    contract_pass_count = sum(app_matches) + sum(nonapp_matches)
    return {
        "case_count": len(rows),
        "app_reachable_count": 19,
        "expected_non_applicable_count": 9,
        "selected_count": sum(row["status"] == "selected" for row in rows),
        "hard_gate_pass_count": sum(row["hard_gate_status"] == "passed" for row in rows),
        "expected_non_applicable_match_count": sum(nonapp_matches),
        "contract_pass_count": contract_pass_count,
        "exception_count": sum(row["exception"] for row in rows),
        "v1_fallback_count": sum(row["v1_fallback_used"] for row in rows),
        "failure_case_count": len(rows) - contract_pass_count,
    }


def build_known28_receipt(
    rows: Sequence[Mapping[str, Any]],
    *,
    final_batch_summary: Mapping[str, Any],
    final_dependency_manifest: Mapping[str, Any] | None,
    run_id: str,
    private_packet_commitment: str,
    verifier_sha256: str,
    verified_case_count: int,
) -> dict[str, Any]:
    applicability_issues = validate_known28_applicability_contract()
    if applicability_issues:
        raise Step11CycleEvidenceError(applicability_issues[0])
    final = _project_final(final_batch_summary, final_dependency_manifest)
    if final_dependency_manifest is None:
        raise Step11CycleEvidenceError("KNOWN28_DEPENDENCY_MANIFEST_REQUIRED")
    dependency = _validated_dependency_manifest(final_dependency_manifest)
    by_path = {row["path"]: row["sha256"] for row in dependency["file_hashes"]}
    if (
        type(run_id) is not str
        or _RUN_RE.fullmatch(run_id) is None
        or not _valid_nonzero_sha(private_packet_commitment)
        or verifier_sha256
        != by_path.get("ai/tools/emlis_nls_v3_step11_regression.py")
        or type(verified_case_count) is not int
        or type(verified_case_count) is bool
        or verified_case_count != 28
    ):
        raise Step11CycleEvidenceError("KNOWN28_RUN_ID_INVALID")
    if type(rows) not in {list, tuple} or len(rows) != 28:
        raise Step11CycleEvidenceError("KNOWN28_COUNT_INVALID")
    normalized = sorted((_known28_row(row) for row in rows), key=lambda row: row["case_ref"])
    if tuple(row["case_ref"] for row in normalized) != _KNOWN28_CASE_REFS:
        raise Step11CycleEvidenceError("KNOWN28_CASE_SET_INVALID")
    aggregate = _known28_aggregate(normalized)
    value = {
        "schema_version": KNOWN28_RECEIPT_SCHEMA,
        "cycle_id": STEP11_CYCLE_ID,
        "candidate_version_id": final["candidate_version_id"],
        "run_id": run_id,
        "source_dependency_closure_sha256": final[
            "source_dependency_closure_sha256"
        ],
        "commitment_policy_sha256": final["commitment_policy_sha256"],
        "commitment_key_id": final["commitment_key_id"],
        "final_batch_summary_sha256": final["summary_sha256"],
        "known_inventory_sha256": FROZEN_KNOWN28_INVENTORY_SHA256,
        "generic_projection_policy_sha256": (
            FROZEN_KNOWN28_GENERIC_PROJECTION_POLICY_SHA256
        ),
        "expected_applicability_inventory_sha256": (
            FROZEN_KNOWN28_EXPECTED_APPLICABILITY_SHA256
        ),
        "private_packet_commitment": private_packet_commitment,
        "verifier_sha256": verifier_sha256,
        "verified_case_count": verified_case_count,
        "private_packet_validation_status": "clean",
        "regression_set": "V1_KNOWN_COMPARISON_28",
        "rows": normalized,
        "aggregate": aggregate,
        "aggregate_recomputed_from_rows": True,
        "formal_status": (
            "clean" if aggregate["contract_pass_count"] == 28 else "failed"
        ),
        "counts_toward_karen_minimum": False,
        "body_free": True,
    }
    _require_body_free(value)
    return value


def validate_known28_receipt(
    value: Any,
    *,
    final_batch_summary: Mapping[str, Any],
    final_dependency_manifest: Mapping[str, Any] | None,
) -> tuple[str, ...]:
    if type(value) is not dict or type(value.get("rows")) is not list:
        return ("KNOWN28_RECEIPT_MAPPING_REQUIRED",)
    try:
        expected = build_known28_receipt(
            value["rows"],
            final_batch_summary=final_batch_summary,
            final_dependency_manifest=final_dependency_manifest,
            run_id=value.get("run_id"),
            private_packet_commitment=value.get("private_packet_commitment"),
            verifier_sha256=value.get("verifier_sha256"),
            verified_case_count=value.get("verified_case_count"),
        )
    except (KeyError, TypeError, ValueError, Step11CycleEvidenceError):
        return ("KNOWN28_RECEIPT_CONTRACT_INVALID",)
    return () if value == expected else ("KNOWN28_RECEIPT_RECOMPUTATION_MISMATCH",)


def build_invalid16_receipt(
    rows: Sequence[Mapping[str, Any]],
    *,
    final_batch_summary: Mapping[str, Any],
    final_dependency_manifest: Mapping[str, Any] | None,
    run_id: str,
    verifier_sha256: str,
    verified_case_count: int,
) -> dict[str, Any]:
    inventory_issues = validate_invalid16_inventory_contract()
    if inventory_issues:
        raise Step11CycleEvidenceError(inventory_issues[0])
    final = _project_final(final_batch_summary, final_dependency_manifest)
    if final_dependency_manifest is None:
        raise Step11CycleEvidenceError("INVALID16_DEPENDENCY_MANIFEST_REQUIRED")
    dependency = _validated_dependency_manifest(final_dependency_manifest)
    by_path = {row["path"]: row["sha256"] for row in dependency["file_hashes"]}
    if (
        type(run_id) is not str
        or _RUN_RE.fullmatch(run_id) is None
        or type(rows) not in {list, tuple}
        or len(rows) != 16
        or verifier_sha256
        != by_path.get("ai/tools/emlis_nls_v3_step11_regression.py")
        or type(verified_case_count) is not int
        or type(verified_case_count) is bool
        or verified_case_count != 16
    ):
        raise Step11CycleEvidenceError("INVALID16_PARENT_OR_COUNT_INVALID")
    by_id: dict[str, list[str]] = {}
    for raw in rows:
        row = _require_exact_keys(
            raw, {"fixture_id", "actual_issue_codes"}, "INVALID16_INPUT_ROW_INVALID"
        )
        fixture_id = row["fixture_id"]
        actual = row["actual_issue_codes"]
        if (
            fixture_id not in _INVALID16_EXPECTED
            or fixture_id in by_id
            or type(actual) is not list
            or actual != sorted(set(actual))
            or any(type(code) is not str or _ISSUE_RE.fullmatch(code) is None for code in actual)
        ):
            raise Step11CycleEvidenceError("INVALID16_INPUT_ROW_INVALID")
        by_id[fixture_id] = actual
    if set(by_id) != set(_INVALID16_IDS):
        raise Step11CycleEvidenceError("INVALID16_CASE_SET_INVALID")
    normalized = []
    for fixture_id in _INVALID16_IDS:
        expected = _INVALID16_EXPECTED[fixture_id]
        actual = by_id[fixture_id]
        status = (
            "rejected"
            if actual == [expected]
            else "wrong_rejection"
            if actual
            else "unexpectedly_accepted"
        )
        normalized.append(
            {
                "fixture_id": fixture_id,
                "expected_issue_code": expected,
                "actual_issue_codes": actual,
                "status": status,
            }
        )
    matches = sum(row["status"] == "rejected" for row in normalized)
    aggregate = {
        "case_count": 16,
        "rejected_count": sum(bool(row["actual_issue_codes"]) for row in normalized),
        "expected_rejection_match_count": matches,
        "under_rejected_count": 16 - matches,
    }
    value = {
        "schema_version": INVALID16_RECEIPT_SCHEMA,
        "cycle_id": STEP11_CYCLE_ID,
        "candidate_version_id": final["candidate_version_id"],
        "run_id": run_id,
        "source_dependency_closure_sha256": final[
            "source_dependency_closure_sha256"
        ],
        "commitment_policy_sha256": final["commitment_policy_sha256"],
        "commitment_key_id": final["commitment_key_id"],
        "final_batch_summary_sha256": final["summary_sha256"],
        "validator_policy_sha256": FROZEN_VALIDATOR_POLICY_SHA256,
        "invalid_fixture_file_sha256": FROZEN_INVALID16_FILE_SHA256,
        "invalid_inventory_sha256": FROZEN_INVALID16_INVENTORY_SHA256,
        "validator_owner_sha256": by_path[
            "ai/services/ai_inference/emlis_ai_step10_app_reachable_contract_v3.py"
        ],
        "verifier_sha256": verifier_sha256,
        "verified_case_count": verified_case_count,
        "regression_set": "INVALID_CONTRACT_16",
        "rows": normalized,
        "aggregate": aggregate,
        "aggregate_recomputed_from_rows": True,
        "formal_status": "clean" if matches == 16 else "failed",
        "counts_toward_karen_minimum": False,
        "body_free": True,
    }
    _require_body_free(value)
    return value


def validate_invalid16_receipt(
    value: Any,
    *,
    final_batch_summary: Mapping[str, Any],
    final_dependency_manifest: Mapping[str, Any] | None,
) -> tuple[str, ...]:
    if type(value) is not dict or type(value.get("rows")) is not list:
        return ("INVALID16_RECEIPT_MAPPING_REQUIRED",)
    try:
        inputs = [
            {
                "fixture_id": row["fixture_id"],
                "actual_issue_codes": row["actual_issue_codes"],
            }
            for row in value["rows"]
        ]
        expected = build_invalid16_receipt(
            inputs,
            final_batch_summary=final_batch_summary,
            final_dependency_manifest=final_dependency_manifest,
            run_id=value.get("run_id"),
            verifier_sha256=value.get("verifier_sha256"),
            verified_case_count=value.get("verified_case_count"),
        )
    except (KeyError, TypeError, ValueError, Step11CycleEvidenceError):
        return ("INVALID16_RECEIPT_CONTRACT_INVALID",)
    return () if value == expected else ("INVALID16_RECEIPT_RECOMPUTATION_MISMATCH",)


def build_case_specific_workaround_scan_receipt(
    dependency_manifest: Mapping[str, Any],
    *,
    scanner_sha256: str,
    negative_test_receipt_sha256: str,
    forbidden_reference_counts: Mapping[str, Any],
    negative_test_results: Mapping[str, Any],
) -> dict[str, Any]:
    dependency = _validated_dependency_manifest(dependency_manifest)
    by_path = {row["path"]: row["sha256"] for row in dependency["file_hashes"]}
    if (
        scanner_sha256 != by_path.get(_WORKAROUND_SCANNER_PATH)
        or negative_test_receipt_sha256 != WORKAROUND_NEGATIVE_POLICY_SHA256
        or any(path not in by_path for path in _WORKAROUND_SCANNED_PATHS)
    ):
        raise Step11CycleEvidenceError("WORKAROUND_SCAN_PARENT_INVALID")
    scanned = [
        {"path": path, "sha256": by_path[path]}
        for path in sorted(_WORKAROUND_SCANNED_PATHS)
    ]
    if (
        type(forbidden_reference_counts) is not dict
        or set(forbidden_reference_counts) != set(_WORKAROUND_DIMENSIONS)
        or any(
            type(forbidden_reference_counts[dimension]) is not int
            or type(forbidden_reference_counts[dimension]) is bool
            or forbidden_reference_counts[dimension] < 0
            for dimension in _WORKAROUND_DIMENSIONS
        )
        or type(negative_test_results) is not dict
        or set(negative_test_results) != set(_WORKAROUND_NEGATIVE_POLICY["attacks"])
        or any(value is not True for value in negative_test_results.values())
    ):
        raise Step11CycleEvidenceError("WORKAROUND_SCAN_RESULT_INVALID")
    counts = {
        dimension: forbidden_reference_counts[dimension]
        for dimension in _WORKAROUND_DIMENSIONS
    }
    negative_rows = [
        {"attack_id": attack_id, "detected": negative_test_results[attack_id]}
        for attack_id in sorted(negative_test_results)
    ]
    finding_count = sum(counts.values())
    if finding_count != 0:
        raise Step11CycleEvidenceError("WORKAROUND_SCAN_FINDING_PRESENT")
    value = {
        "schema_version": WORKAROUND_SCAN_SCHEMA,
        "cycle_id": STEP11_CYCLE_ID,
        "candidate_version_id": dependency["candidate_version_id"],
        "source_dependency_closure_sha256": dependency[
            "source_dependency_closure_sha256"
        ],
        "dependency_manifest_sha256": artifact_sha256(dependency),
        "scanner_sha256": scanner_sha256,
        "negative_test_receipt_sha256": negative_test_receipt_sha256,
        "scanned_file_hashes": scanned,
        "forbidden_reference_counts": counts,
        "negative_test_results": negative_rows,
        "finding_count": finding_count,
        "status": "passed",
        "body_free": True,
    }
    _require_body_free(value)
    return value


def validate_case_specific_workaround_scan_receipt(
    value: Any,
    *,
    dependency_manifest: Mapping[str, Any],
) -> tuple[str, ...]:
    if type(value) is not dict:
        return ("WORKAROUND_SCAN_MAPPING_REQUIRED",)
    try:
        expected = build_case_specific_workaround_scan_receipt(
            dependency_manifest,
            scanner_sha256=value.get("scanner_sha256"),
            negative_test_receipt_sha256=value.get("negative_test_receipt_sha256"),
            forbidden_reference_counts=value.get("forbidden_reference_counts"),
            negative_test_results={
                row.get("attack_id"): row.get("detected")
                for row in value.get("negative_test_results", [])
                if type(row) is dict
            },
        )
    except (TypeError, ValueError, Step11CycleEvidenceError):
        return ("WORKAROUND_SCAN_CONTRACT_INVALID",)
    return () if value == expected else ("WORKAROUND_SCAN_RECOMPUTATION_MISMATCH",)


def _clean_known28(
    value: Any,
    *,
    final_batch_summary: Mapping[str, Any],
    final_dependency_manifest: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if (
        validate_known28_receipt(
            value,
            final_batch_summary=final_batch_summary,
            final_dependency_manifest=final_dependency_manifest,
        )
        or value.get("formal_status") != "clean"
    ):
        raise Step11CycleEvidenceError("KNOWN28_NOT_CLEAN")
    return dict(value)


def _clean_development42(
    value: Any,
    *,
    final_batch_summary: Mapping[str, Any],
    final_dependency_manifest: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Validate the complete Development42 receipt without importing tools.

    The tool-side validator additionally replays the frozen loader.  This
    evidence owner independently freezes the resulting applicability ledger,
    receipt keyset, row state machine, aggregate, and final-closure bindings so
    a caller cannot turn an excluded legacy input into a false green result.
    """

    if final_dependency_manifest is None or type(value) is not dict:
        raise Step11CycleEvidenceError("DEVELOPMENT42_NOT_CLEAN")
    final = _project_final(final_batch_summary, final_dependency_manifest)
    dependency = _validated_dependency_manifest(final_dependency_manifest)
    by_path = {row["path"]: row["sha256"] for row in dependency["file_hashes"]}
    row = _require_exact_keys(
        value,
        {
            "schema_version",
            "cycle_id",
            "candidate_version_id",
            "run_id",
            "source_dependency_closure_sha256",
            "commitment_policy_sha256",
            "commitment_key_id",
            "final_batch_summary_sha256",
            "regression_set",
            "development_fixture_file_sha256",
            "development_fixture_loader_sha256",
            "generic_projection_policy_sha256",
            "expected_applicability_inventory_sha256",
            "validator_owner_sha256",
            "private_packet_commitment",
            "verifier_sha256",
            "verified_case_count",
            "private_packet_validation_status",
            "rows",
            "aggregate",
            "aggregate_recomputed_from_rows",
            "formal_status",
            "counts_toward_karen_minimum",
            "body_free",
        },
        "DEVELOPMENT42_RECEIPT_KEYSET_INVALID",
    )
    if (
        row["schema_version"] != DEVELOPMENT42_RECEIPT_SCHEMA
        or row["cycle_id"] != STEP11_CYCLE_ID
        or row["candidate_version_id"] != final["candidate_version_id"]
        or type(row["run_id"]) is not str
        or _RUN_RE.fullmatch(row["run_id"]) is None
        or row["source_dependency_closure_sha256"]
        != final["source_dependency_closure_sha256"]
        or row["commitment_policy_sha256"] != final["commitment_policy_sha256"]
        or row["commitment_key_id"] != final["commitment_key_id"]
        or row["final_batch_summary_sha256"] != final["summary_sha256"]
        or row["regression_set"] != "V2_DEVELOPMENT_42"
        or row["development_fixture_file_sha256"]
        != FROZEN_DEVELOPMENT42_SOURCE_FILE_SHA256
        or row["development_fixture_loader_sha256"]
        != FROZEN_DEVELOPMENT42_LOADER_SHA256
        or row["generic_projection_policy_sha256"]
        != FROZEN_KNOWN28_GENERIC_PROJECTION_POLICY_SHA256
        or row["expected_applicability_inventory_sha256"]
        != FROZEN_DEVELOPMENT42_EXPECTED_APPLICABILITY_SHA256
        or row["validator_owner_sha256"]
        != by_path.get(
            "ai/services/ai_inference/"
            "emlis_ai_step10_app_reachable_contract_v3.py"
        )
        or row["verifier_sha256"]
        != by_path.get("ai/tools/emlis_nls_v3_step11_regression.py")
        or not _valid_nonzero_sha(row["private_packet_commitment"])
        or row["verified_case_count"] != 42
        or type(row["verified_case_count"]) is bool
        or row["private_packet_validation_status"] != "clean"
        or row["aggregate_recomputed_from_rows"] is not True
        or row["formal_status"] != "clean"
        or row["counts_toward_karen_minimum"] is not False
        or row["body_free"] is not True
        or type(row["rows"]) is not list
        or len(row["rows"]) != 42
    ):
        raise Step11CycleEvidenceError("DEVELOPMENT42_PARENT_INVALID")

    normalized_rows: list[dict[str, Any]] = []
    for expected_case_id, raw_case in zip(
        _DEVELOPMENT42_CASE_IDS, row["rows"], strict=True
    ):
        case = _require_exact_keys(
            raw_case,
            {
                "case_ref",
                "family",
                "legacy_input_commitment",
                "projected_input_commitment",
                "applicability_binding_commitment",
                "applicability_status",
                "applicability_issue_codes",
                "v1_baseline_body_commitment",
                "selected_candidate_body_commitment",
                "status",
                "hard_gate_status",
                "failure_codes",
                "exception",
                "v1_fallback_used",
            },
            "DEVELOPMENT42_ROW_KEYSET_INVALID",
        )
        expected_issues = list(
            _DEVELOPMENT42_NONAPP_ISSUES.get(expected_case_id, ())
        )
        applicable = not expected_issues
        if (
            case["case_ref"] != expected_case_id
            or type(case["family"]) is not str
            or not case["family"]
            or not _valid_nonzero_sha(case["legacy_input_commitment"])
            or not _valid_nonzero_sha(case["applicability_binding_commitment"])
            or not _valid_nonzero_sha(case["v1_baseline_body_commitment"])
            or case["applicability_status"]
            != ("app_reachable" if applicable else "expected_non_applicable")
            or case["applicability_issue_codes"] != expected_issues
            or case["status"]
            != ("selected" if applicable else "expected_non_applicable")
            or case["hard_gate_status"]
            != ("passed" if applicable else "not_applicable")
            or case["failure_codes"] != []
            or case["exception"] is not False
            or case["v1_fallback_used"] is not False
            or (
                applicable
                and (
                    not _valid_nonzero_sha(case["projected_input_commitment"])
                    or not _valid_nonzero_sha(
                        case["selected_candidate_body_commitment"]
                    )
                )
            )
            or (
                not applicable
                and (
                    case["projected_input_commitment"] is not None
                    or case["selected_candidate_body_commitment"] is not None
                )
            )
        ):
            raise Step11CycleEvidenceError("DEVELOPMENT42_ROW_INVALID")
        normalized_rows.append(case)

    expected_aggregate = {
        "case_count": 42,
        "pass_count": 42,
        "app_reachable_count": 24,
        "selected_count": 24,
        "expected_non_applicable_count": 18,
        "expected_non_applicable_match_count": 18,
        "hard_gate_pass_count": 24,
        "failure_count": 0,
        "exception_count": 0,
        "v1_fallback_count": 0,
    }
    if row["aggregate"] != expected_aggregate:
        raise Step11CycleEvidenceError("DEVELOPMENT42_AGGREGATE_INVALID")
    _require_body_free(row)
    return row


def _clean_available_input_scope(value: Any) -> dict[str, Any]:
    candidate = value.get("candidate_version_id") if type(value) is dict else None
    historical_rc0020 = candidate == STEP11_SUCCESSOR_CANDIDATE_VERSION_ID
    historical_rc0021 = (
        candidate == STEP11_HISTORICAL_RC0021_CANDIDATE_VERSION_ID
    )
    historical_rc0022 = (
        candidate == STEP11_HISTORICAL_RC0022_CANDIDATE_VERSION_ID
    )
    historical_rc0023 = (
        candidate == STEP11_HISTORICAL_RC0023_CANDIDATE_VERSION_ID
    )
    current_rc0024 = candidate == STEP11_CURRENT_CANDIDATE_VERSION_ID
    if (
        type(value) is not dict
        or not (
            historical_rc0020
            or historical_rc0021
            or historical_rc0022
            or historical_rc0023
            or current_rc0024
        )
        or (
            historical_rc0020
            and (
                artifact_sha256(value)
                != FROZEN_AVAILABLE_INPUT_SCOPE_RECEIPT_SHA256
                or value.get("schema_version")
                != AVAILABLE_INPUT_SCOPE_RECEIPT_SCHEMA
            )
        )
        or (
            historical_rc0021
            and value.get("schema_version")
            != STEP11_RC0021_AVAILABLE_INPUT_SCOPE_RECEIPT_SCHEMA
        )
        or (
            historical_rc0022
            and value.get("schema_version")
            != STEP11_RC0022_AVAILABLE_INPUT_SCOPE_RECEIPT_SCHEMA
        )
        or (
            historical_rc0023
            and value.get("schema_version")
            != STEP11_RC0023_AVAILABLE_INPUT_SCOPE_RECEIPT_SCHEMA
        )
        or (
            current_rc0024
            and value.get("schema_version")
            != STEP11_RC0024_AVAILABLE_INPUT_SCOPE_RECEIPT_SCHEMA
        )
        or value.get("formal_status") != "scope_frozen"
        or value.get("body_free") is not True
        or value.get("scope_aggregate")
        != {
            "known_inventory_entry_count": 11,
            "known_machine_execution_cohort_count": 2,
            "known_machine_execution_case_count": 70,
            "legacy_registered_case_count": 3,
            "legacy_app_reachable_to_execute_count": 0,
            "legacy_expected_non_applicable_count": 3,
            "legacy_contract_negative_expected_rejection_count": 0,
            "available_real_user_current_valid_count": 0,
            "registered_auxiliary_case_count": 73,
        }
    ):
        raise Step11CycleEvidenceError("AVAILABLE_INPUT_SCOPE_NOT_FROZEN")
    _require_body_free(value)
    return dict(value)


def _clean_correction_rerun_lineage(
    value: Any,
    *,
    dependency_manifests: Sequence[Mapping[str, Any]],
    batch_run_summaries: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    current_candidate = (
        value.get("current_candidate_version_id")
        if type(value) is dict
        else None
    )
    if current_candidate == STEP11_CURRENT_CANDIDATE_VERSION_ID:
        lineage_issues = validate_rc0010_rc0024_correction_rerun_lineage(
            value,
            dependency_manifests=dependency_manifests,
            batch_run_summaries=batch_run_summaries,
        )
    elif (
        current_candidate
        == STEP11_HISTORICAL_RC0023_CANDIDATE_VERSION_ID
    ):
        lineage_issues = validate_rc0010_rc0023_correction_rerun_lineage(
            value,
            dependency_manifests=dependency_manifests,
            batch_run_summaries=batch_run_summaries,
        )
    elif (
        current_candidate
        == STEP11_HISTORICAL_RC0022_CANDIDATE_VERSION_ID
    ):
        lineage_issues = validate_rc0010_rc0022_correction_rerun_lineage(
            value,
            dependency_manifests=dependency_manifests,
            batch_run_summaries=batch_run_summaries,
        )
    elif (
        current_candidate
        == STEP11_HISTORICAL_RC0021_CANDIDATE_VERSION_ID
    ):
        lineage_issues = validate_rc0010_rc0021_correction_rerun_lineage(
            value,
            dependency_manifests=dependency_manifests,
            batch_run_summaries=batch_run_summaries,
        )
    else:
        lineage_issues = validate_rc0010_rc0020_correction_rerun_lineage(
            value,
            dependency_manifests=dependency_manifests,
            batch_run_summaries=batch_run_summaries,
        )
    if (
        lineage_issues
        or value.get("acceptance_lineage_ready") is not True
        or current_candidate
        not in {
            STEP11_SUCCESSOR_CANDIDATE_VERSION_ID,
            STEP11_HISTORICAL_RC0021_CANDIDATE_VERSION_ID,
            STEP11_HISTORICAL_RC0022_CANDIDATE_VERSION_ID,
            STEP11_HISTORICAL_RC0023_CANDIDATE_VERSION_ID,
            STEP11_CURRENT_CANDIDATE_VERSION_ID,
        }
        or value.get("historical_sequence_complete") is not True
        or value.get("append_only_hash_chain") is not True
        or value.get("aggregate", {}).get("unreceipted_execution_claim_count")
        != 0
    ):
        raise Step11CycleEvidenceError("CORRECTION_RERUN_LINEAGE_NOT_READY")
    return dict(value)


def _require_lineage_final_parent_binding(
    lineage: Mapping[str, Any],
    *,
    final_batch_summary: Mapping[str, Any],
    final_dependency_manifest: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Bind the final lineage event to the exact acceptance parents."""

    if final_dependency_manifest is None:
        raise Step11CycleEvidenceError("LINEAGE_FINAL_PARENT_REQUIRED")
    final = _project_final(final_batch_summary, final_dependency_manifest)
    dependency = _validated_dependency_manifest(final_dependency_manifest)
    summary_sha = artifact_sha256(final_batch_summary)
    manifest_sha = artifact_sha256(dependency)
    events = lineage.get("events")
    if type(events) is not list:
        raise Step11CycleEvidenceError("LINEAGE_FINAL_PARENT_BINDING_INVALID")
    current_candidate = lineage.get(
        "current_candidate_version_id",
        final["candidate_version_id"],
    )
    if current_candidate not in {
        STEP11_SUCCESSOR_CANDIDATE_VERSION_ID,
        STEP11_HISTORICAL_RC0021_CANDIDATE_VERSION_ID,
        STEP11_HISTORICAL_RC0022_CANDIDATE_VERSION_ID,
        STEP11_HISTORICAL_RC0023_CANDIDATE_VERSION_ID,
        STEP11_CURRENT_CANDIDATE_VERSION_ID,
    }:
        raise Step11CycleEvidenceError("LINEAGE_FINAL_PARENT_BINDING_INVALID")
    corrections = [
        event
        for event in events
        if type(event) is dict
        and event.get("event_type") == "correction_recorded"
        and event.get("candidate_version_id")
        == current_candidate
    ]
    formal_executions = [
        event
        for event in events
        if type(event) is dict
        and event.get("event_type") == "execution_observed"
        and event.get("candidate_version_id")
        == current_candidate
        and event.get("execution_scope") == "formal_cumulative_rerun"
    ]
    final_dispositions = [
        event
        for event in events
        if type(event) is dict
        and event.get("event_type") == "revision_disposition"
        and event.get("candidate_version_id")
        == current_candidate
        and event.get("disposition") == "cycle_final_candidate"
    ]
    if (
        len(corrections) != 1
        or corrections[0].get("source_state_kind") != "dependency_manifest"
        or corrections[0].get("dependency_manifest_sha256") != manifest_sha
        or corrections[0].get("source_state_artifact_sha256") != manifest_sha
        or corrections[0].get("source_dependency_closure_sha256")
        != final["source_dependency_closure_sha256"]
        or len(formal_executions) != 1
        or formal_executions[0].get("batch_summary_sha256") != summary_sha
        or formal_executions[0].get("outcome_receipt_commitment") != summary_sha
        or formal_executions[0].get("run_id") != final["run_id"]
        or formal_executions[0].get("source_dependency_closure_sha256")
        != final["source_dependency_closure_sha256"]
        or formal_executions[0].get("machine_status") != "clean"
        or formal_executions[0].get("counts_as_clean_formal_rerun") is not True
        or len(final_dispositions) != 1
        or final_dispositions[0].get("counts_as_passed_rerun") is not True
        or lineage.get("lineage_head_commitment")
        != final_dispositions[0].get("event_commitment")
    ):
        raise Step11CycleEvidenceError("LINEAGE_FINAL_PARENT_BINDING_INVALID")
    return {
        "candidate_version_id": final["candidate_version_id"],
        "run_id": final["run_id"],
        "source_dependency_closure_sha256": final[
            "source_dependency_closure_sha256"
        ],
        "final_batch_summary_sha256": summary_sha,
        "final_dependency_manifest_sha256": manifest_sha,
        "lineage_event_commitment": final_dispositions[0][
            "event_commitment"
        ],
    }


def _auxiliary_acceptance_conditions(
    *,
    final_run_id: str,
    known: Mapping[str, Any],
    development: Mapping[str, Any],
    available_scope: Mapping[str, Any],
    invalid: Mapping[str, Any],
    correction_lineage: Mapping[str, Any],
    lineage_final_binding: Mapping[str, Any],
) -> dict[str, bool]:
    known_aggregate = known["aggregate"]
    development_aggregate = development["aggregate"]
    scope_aggregate = available_scope["scope_aggregate"]
    invalid_aggregate = invalid["aggregate"]
    run_ids = (
        final_run_id,
        known["run_id"],
        development["run_id"],
        invalid["run_id"],
    )
    lineage_candidate = correction_lineage.get(
        "current_candidate_version_id",
        lineage_final_binding.get("candidate_version_id"),
    )
    return {
        "known_regression_registered_case_count_70": (
            scope_aggregate["known_machine_execution_case_count"] == 70
        ),
        "known28_receipt_case_count_28": known_aggregate["case_count"] == 28,
        "development42_receipt_case_count_42": (
            development_aggregate["case_count"] == 42
        ),
        "development42_app_reachable_selected_24": (
            development_aggregate["app_reachable_count"] == 24
            and development_aggregate["selected_count"] == 24
            and development_aggregate["hard_gate_pass_count"] == 24
        ),
        "development42_expected_non_applicable_matched_18": (
            development_aggregate["expected_non_applicable_count"] == 18
            and development_aggregate[
                "expected_non_applicable_match_count"
            ]
            == 18
        ),
        "known_regression_all_70_passed": (
            known_aggregate["contract_pass_count"]
            + development_aggregate["pass_count"]
            == 70
        ),
        "legacy_registered_case_count_3": (
            scope_aggregate["legacy_registered_case_count"] == 3
        ),
        "legacy_app_reachable_to_execute_count_0": (
            scope_aggregate["legacy_app_reachable_to_execute_count"] == 0
        ),
        "legacy_expected_non_applicable_count_3": (
            scope_aggregate["legacy_expected_non_applicable_count"] == 3
        ),
        "available_real_user_current_valid_count_0": (
            scope_aggregate["available_real_user_current_valid_count"] == 0
        ),
        "invalid16_expected_rejection_match_count_16": (
            invalid_aggregate["case_count"] == 16
            and invalid_aggregate["expected_rejection_match_count"] == 16
            and invalid_aggregate["under_rejected_count"] == 0
        ),
        "final_known_development_invalid_run_ids_pairwise_distinct": (
            len(set(run_ids)) == 4
        ),
        "correction_lineage_complete_and_ready": (
            correction_lineage["historical_sequence_complete"] is True
            and correction_lineage["acceptance_lineage_ready"] is True
            and correction_lineage["aggregate"][
                "unreceipted_execution_claim_count"
            ]
            == 0
        ),
        **{
            (
                "lineage_final_rc0020_parents_exact"
                if lineage_candidate
                == STEP11_SUCCESSOR_CANDIDATE_VERSION_ID
                else "lineage_final_rc0024_parents_exact"
                if lineage_candidate == STEP11_CURRENT_CANDIDATE_VERSION_ID
                else "lineage_final_rc0023_parents_exact"
                if lineage_candidate
                == STEP11_HISTORICAL_RC0023_CANDIDATE_VERSION_ID
                else "lineage_final_rc0022_parents_exact"
                if lineage_candidate
                == STEP11_HISTORICAL_RC0022_CANDIDATE_VERSION_ID
                else "lineage_final_rc0021_parents_exact"
            ): (
                lineage_final_binding["run_id"] == final_run_id
                and lineage_final_binding["candidate_version_id"]
                == lineage_candidate
            )
        },
    }


def _clean_invalid16(
    value: Any,
    *,
    final_batch_summary: Mapping[str, Any],
    final_dependency_manifest: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if (
        validate_invalid16_receipt(
            value,
            final_batch_summary=final_batch_summary,
            final_dependency_manifest=final_dependency_manifest,
        )
        or value.get("formal_status") != "clean"
    ):
        raise Step11CycleEvidenceError("INVALID16_NOT_CLEAN")
    return dict(value)


def build_cumulative100_receipt(
    initial_lock: Mapping[str, Any],
    initial_batch_summary: Mapping[str, Any],
    corpus_validation: Mapping[str, Any],
    initial_review_set: Mapping[str, Any],
    final_batch_summary: Mapping[str, Any],
    final_review_set: Mapping[str, Any],
    private_verification_receipt: Mapping[str, Any],
    known28_receipt: Mapping[str, Any],
    invalid16_receipt: Mapping[str, Any],
    output_diff: Mapping[str, Any],
    output_change_review: Mapping[str, Any],
    *,
    development42_receipt: Mapping[str, Any],
    available_input_scope_receipt: Mapping[str, Any],
    correction_rerun_lineage: Mapping[str, Any],
    lineage_dependency_manifests: Sequence[Mapping[str, Any]],
    lineage_batch_run_summaries: Sequence[Mapping[str, Any]],
    final_dependency_manifest: Mapping[str, Any] | None,
    cumulative_run_id: str,
) -> dict[str, Any]:
    lock = _validated_initial_lock(
        initial_lock,
        batch_summary=initial_batch_summary,
        corpus_validation=corpus_validation,
    )
    final_projection = _project_final(final_batch_summary, final_dependency_manifest)
    _assert_projection_continuity(lock, final_projection)
    initial_review = _validated_review_set(
        initial_review_set,
        initial_lock=lock,
        initial_batch_summary=initial_batch_summary,
        corpus_validation=corpus_validation,
        batch_summary=initial_batch_summary,
        expected_stage="initial",
    )
    final_review = _validated_review_set(
        final_review_set,
        initial_lock=lock,
        initial_batch_summary=initial_batch_summary,
        corpus_validation=corpus_validation,
        batch_summary=final_batch_summary,
        expected_stage="final",
        dependency_manifest=final_dependency_manifest,
    )
    if (
        final_dependency_manifest is None
        or validate_step11_private_verification_receipt(
            private_verification_receipt,
            final_batch_summary=final_batch_summary,
            final_dependency_manifest=final_dependency_manifest,
        )
        or private_verification_receipt.get("initial_batch_summary_sha256")
        != lock["initial_batch_summary_sha256"]
        or private_verification_receipt.get("verified_case_count") != 100
        or private_verification_receipt.get("initial_verified_case_count") != 100
        or private_verification_receipt.get(
            "private_packet_validation_status"
        )
        != "clean"
        or private_verification_receipt.get(
            "initial_evidence_validation_status"
        )
        != "clean"
    ):
        raise Step11CycleEvidenceError(
            "CUMULATIVE_PRIVATE_VERIFICATION_INVALID"
        )
    expected_diff = build_output_diff(
        lock,
        initial_batch_summary,
        corpus_validation,
        final_batch_summary,
        final_dependency_manifest=final_dependency_manifest,
    )
    if output_diff != expected_diff:
        raise Step11CycleEvidenceError("CUMULATIVE_OUTPUT_DIFF_INVALID")
    expected_output_review = build_output_change_review(
        lock,
        initial_batch_summary,
        corpus_validation,
        initial_review,
        final_batch_summary,
        final_review,
        expected_diff,
        final_dependency_manifest=final_dependency_manifest,
    )
    if output_change_review != expected_output_review:
        raise Step11CycleEvidenceError("CUMULATIVE_OUTPUT_REVIEW_INVALID")
    known = _clean_known28(
        known28_receipt,
        final_batch_summary=final_batch_summary,
        final_dependency_manifest=final_dependency_manifest,
    )
    development = _clean_development42(
        development42_receipt,
        final_batch_summary=final_batch_summary,
        final_dependency_manifest=final_dependency_manifest,
    )
    available_scope = _clean_available_input_scope(
        available_input_scope_receipt
    )
    correction_lineage = _clean_correction_rerun_lineage(
        correction_rerun_lineage,
        dependency_manifests=lineage_dependency_manifests,
        batch_run_summaries=lineage_batch_run_summaries,
    )
    invalid = _clean_invalid16(
        invalid16_receipt,
        final_batch_summary=final_batch_summary,
        final_dependency_manifest=final_dependency_manifest,
    )
    lineage_final_binding = _require_lineage_final_parent_binding(
        correction_lineage,
        final_batch_summary=final_batch_summary,
        final_dependency_manifest=final_dependency_manifest,
    )
    auxiliary_conditions = _auxiliary_acceptance_conditions(
        final_run_id=final_projection["run_id"],
        known=known,
        development=development,
        available_scope=available_scope,
        invalid=invalid,
        correction_lineage=correction_lineage,
        lineage_final_binding=lineage_final_binding,
    )
    if (
        type(cumulative_run_id) is not str
        or _CUM_RE.fullmatch(cumulative_run_id) is None
        or final_review["aggregate"]["unresolved_blocker_major_count"] != 0
        or not all(auxiliary_conditions.values())
    ):
        raise Step11CycleEvidenceError("CUMULATIVE100_PARENT_MISMATCH")
    corrected = final_projection["candidate_version_id"] != STEP11_INITIAL_CANDIDATE_VERSION_ID
    if corrected and (
        final_projection["run_id"] == lock["run_id"]
        or final_projection["source_dependency_closure_sha256"]
        == lock["source_dependency_closure_sha256"]
        or not _is_successor(final_projection["candidate_version_id"])
        or final_dependency_manifest is None
    ):
        raise Step11CycleEvidenceError("CUMULATIVE_CORRECTED_LINEAGE_INVALID")
    if not corrected and (
        final_projection["summary_sha256"] != lock["initial_batch_summary_sha256"]
        or final_dependency_manifest is not None
    ):
        raise Step11CycleEvidenceError("CUMULATIVE_NO_CHANGE_LINEAGE_INVALID")
    rows = final_projection["case_rows"]
    value = {
        "schema_version": CUMULATIVE100_RECEIPT_SCHEMA,
        "cycle_id": STEP11_CYCLE_ID,
        "cumulative_run_id": cumulative_run_id,
        "state": "CUMULATIVE_RERUN_COMPLETE" if corrected else "INITIAL_RESULT_REUSED",
        "candidate_version_id": final_projection["candidate_version_id"],
        "source_dependency_closure_sha256": final_projection[
            "source_dependency_closure_sha256"
        ],
        "dependency_manifest_sha256": (
            artifact_sha256(final_dependency_manifest)
            if final_dependency_manifest is not None
            else None
        ),
        "initial_lock_sha256": artifact_sha256(lock),
        "initial_review_set_sha256": artifact_sha256(initial_review),
        "final_batch_summary_sha256": final_projection["summary_sha256"],
        "final_review_set_sha256": artifact_sha256(final_review),
        "private_verification_receipt_sha256": artifact_sha256(
            private_verification_receipt
        ),
        "known28_receipt_sha256": artifact_sha256(known),
        "development42_receipt_sha256": artifact_sha256(development),
        "available_input_scope_receipt_sha256": artifact_sha256(
            available_scope
        ),
        "correction_rerun_lineage_sha256": artifact_sha256(
            correction_lineage
        ),
        "lineage_final_parent_binding": lineage_final_binding,
        "invalid16_receipt_sha256": artifact_sha256(invalid),
        "output_diff_sha256": artifact_sha256(expected_diff),
        "output_change_review_sha256": artifact_sha256(expected_output_review),
        "aggregate": {
            "expected_case_count": 100,
            "executed_case_count": 100,
            "selected_count": sum(row["status"] == "selected" for row in rows),
            "exception_count": sum(row["status"] == "exception" for row in rows),
            "no_valid_candidate_count": sum(
                row["status"] == "v3_no_valid_candidate" for row in rows
            ),
            "v1_fallback_count": sum(row["v1_fallback_used"] for row in rows),
            "local_reviewed_count": final_review["aggregate"]["reviewed_count"],
            "private_verified_case_count": private_verification_receipt[
                "verified_case_count"
            ],
            "unresolved_blocker_major_count": 0,
            "known28_pass_count": known["aggregate"]["contract_pass_count"],
            "known28_selected_count": known["aggregate"]["selected_count"],
            "known28_expected_non_applicable_match_count": known["aggregate"][
                "expected_non_applicable_match_count"
            ],
            "development42_pass_count": development["aggregate"][
                "pass_count"
            ],
            "development42_selected_count": development["aggregate"][
                "selected_count"
            ],
            "development42_expected_non_applicable_match_count": development[
                "aggregate"
            ]["expected_non_applicable_match_count"],
            "known_regression_registered_case_count": available_scope[
                "scope_aggregate"
            ]["known_machine_execution_case_count"],
            "known_regression_pass_count": (
                known["aggregate"]["contract_pass_count"]
                + development["aggregate"]["pass_count"]
            ),
            "legacy_registered_case_count": available_scope[
                "scope_aggregate"
            ]["legacy_registered_case_count"],
            "legacy_app_reachable_to_execute_count": available_scope[
                "scope_aggregate"
            ]["legacy_app_reachable_to_execute_count"],
            "legacy_expected_non_applicable_count": available_scope[
                "scope_aggregate"
            ]["legacy_expected_non_applicable_count"],
            "available_real_user_current_valid_count": available_scope[
                "scope_aggregate"
            ]["available_real_user_current_valid_count"],
            "lineage_receipt_bound_execution_count": correction_lineage[
                "aggregate"
            ]["receipt_bound_execution_count"],
            "lineage_clean_formal_rerun_count": correction_lineage[
                "aggregate"
            ]["receipt_bound_clean_formal_rerun_count"],
            "invalid16_expected_rejection_match_count": invalid["aggregate"][
                "expected_rejection_match_count"
            ],
        },
        "execution_run_ids": {
            "final_batch": final_projection["run_id"],
            "known28": known["run_id"],
            "development42": development["run_id"],
            "invalid16": invalid["run_id"],
        },
        "auxiliary_acceptance_conditions": auxiliary_conditions,
        "machine_status": "clean",
        "local_review_status": "clean",
        "known_regression_status": "clean",
        "available_input_scope_status": "scope_frozen",
        "correction_rerun_lineage_status": "clean",
        "invalid_contract_status": "clean",
        "aggregate_recomputed_from_parents": True,
        "batch_acceptance_claimed": False,
        "body_free": True,
    }
    _require_body_free(value)
    return value


def validate_cumulative100_receipt(
    value: Any,
    **parents: Any,
) -> tuple[str, ...]:
    if type(value) is not dict:
        return ("CUMULATIVE100_RECEIPT_MAPPING_REQUIRED",)
    try:
        expected = build_cumulative100_receipt(
            **parents,
            cumulative_run_id=value.get("cumulative_run_id"),
        )
    except (KeyError, TypeError, ValueError, Step11CycleEvidenceError):
        return ("CUMULATIVE100_PARENT_OR_CONTRACT_INVALID",)
    return () if value == expected else ("CUMULATIVE100_RECOMPUTATION_MISMATCH",)


def _final_correction_delta(
    dependency: Mapping[str, Any],
    *,
    final_candidate_version_id: str,
    final_source_closure_sha256: str,
) -> dict[str, Any]:
    """Project the final immediate RC delta without relabelling Cycle history."""

    before_candidate = dependency["before_candidate_version_id"]
    after_candidate = dependency["candidate_version_id"]
    before_number = _rc_number(before_candidate)
    after_number = _rc_number(after_candidate)
    if (
        after_candidate != final_candidate_version_id
        or dependency["source_dependency_closure_sha256"]
        != final_source_closure_sha256
        or before_number is None
        or after_number is None
        or after_number != before_number + 1
    ):
        raise Step11CycleEvidenceError(
            "FINAL_CORRECTION_DEPENDENCY_BOUNDARY_INVALID"
        )
    value = {
        "schema_version": (
            "cocolon.emlis.nls_v3.final_correction_delta.step11.v1"
        ),
        "before_candidate_version_id": before_candidate,
        "after_candidate_version_id": after_candidate,
        "before_source_closure_sha256": dependency[
            "before_source_closure_sha256"
        ],
        "after_source_closure_sha256": dependency[
            "source_dependency_closure_sha256"
        ],
        "dependency_manifest_sha256": artifact_sha256(dependency),
        "changed_file_hashes": dependency["changed_file_hashes"],
        "append_only": True,
        "body_free": True,
    }
    _require_body_free(value)
    return value


def build_cycle_change_ledger(
    initial_lock: Mapping[str, Any],
    initial_batch_summary: Mapping[str, Any],
    corpus_validation: Mapping[str, Any],
    initial_review_set: Mapping[str, Any],
    final_batch_summary: Mapping[str, Any],
    cumulative100_receipt: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
    *,
    final_dependency_manifest: Mapping[str, Any] | None,
    workaround_scan_receipt: Mapping[str, Any] | None,
) -> dict[str, Any]:
    lock = _validated_initial_lock(
        initial_lock,
        batch_summary=initial_batch_summary,
        corpus_validation=corpus_validation,
    )
    initial = _validated_review_set(
        initial_review_set,
        initial_lock=lock,
        initial_batch_summary=initial_batch_summary,
        corpus_validation=corpus_validation,
        batch_summary=initial_batch_summary,
        expected_stage="initial",
    )
    final = _project_final(final_batch_summary, final_dependency_manifest)
    blocking_by_commitment = {
        row["review"]["case_identity_commitment"]: {
            "severity": row["review"]["severity"],
            "reason_codes": set(row["review"]["reason_codes"]),
        }
        for row in initial["rows"]
        if row["review"]["severity"] in _BLOCKING_SEVERITIES
    }
    corrected = final["candidate_version_id"] != STEP11_INITIAL_CANDIDATE_VERSION_ID
    cumulative_sha = artifact_sha256(cumulative100_receipt)
    if (
        type(cumulative100_receipt) is not dict
        or cumulative100_receipt.get("schema_version")
        != CUMULATIVE100_RECEIPT_SCHEMA
        or cumulative100_receipt.get("candidate_version_id")
        != final["candidate_version_id"]
        or cumulative100_receipt.get("source_dependency_closure_sha256")
        != final["source_dependency_closure_sha256"]
        or cumulative100_receipt.get("final_batch_summary_sha256")
        != final["summary_sha256"]
        or cumulative100_receipt.get("initial_lock_sha256")
        != artifact_sha256(lock)
        or cumulative100_receipt.get("body_free") is not True
    ):
        raise Step11CycleEvidenceError("CYCLE_LEDGER_CUMULATIVE_PARENT_INVALID")
    if corrected:
        if final_dependency_manifest is None or workaround_scan_receipt is None:
            raise Step11CycleEvidenceError("CORRECTED_LEDGER_PARENT_REQUIRED")
        dependency = _validated_dependency_manifest(final_dependency_manifest)
        if validate_case_specific_workaround_scan_receipt(
            workaround_scan_receipt, dependency_manifest=dependency
        ):
            raise Step11CycleEvidenceError("WORKAROUND_SCAN_INVALID")
        if (
            final["candidate_version_id"]
            not in {
                STEP11_SUCCESSOR_CANDIDATE_VERSION_ID,
                STEP11_HISTORICAL_RC0021_CANDIDATE_VERSION_ID,
                STEP11_HISTORICAL_RC0022_CANDIDATE_VERSION_ID,
                STEP11_HISTORICAL_RC0023_CANDIDATE_VERSION_ID,
                STEP11_CURRENT_CANDIDATE_VERSION_ID,
            }
            or dependency["candidate_version_id"]
            != final["candidate_version_id"]
            or type(rows) not in {list, tuple}
            or not rows
            or not blocking_by_commitment
        ):
            raise Step11CycleEvidenceError("CORRECTED_LEDGER_STATE_INVALID")
        final_delta = _final_correction_delta(
            dependency,
            final_candidate_version_id=final["candidate_version_id"],
            final_source_closure_sha256=final[
                "source_dependency_closure_sha256"
            ],
        )
        final_delta_sha = artifact_sha256(final_delta)
        dependency_by_path = {
            item["path"]: item["sha256"] for item in dependency["file_hashes"]
        }
        security_test_sha256 = dependency_by_path.get(_STEP11_SECURITY_TEST_PATH)
        workaround_test_sha256 = dependency_by_path.get(_WORKAROUND_SCANNER_PATH)
        if (
            not _valid_nonzero_sha(security_test_sha256)
            or not _valid_nonzero_sha(workaround_test_sha256)
        ):
            raise Step11CycleEvidenceError(
                "CHANGE_LEDGER_NEGATIVE_TEST_OWNER_MISSING"
            )
        normalized_rows = []
        covered: set[str] = set()
        for raw in rows:
            row = _require_exact_keys(
                raw,
                {
                    "failure_case_commitments",
                    "failure_layer",
                    "severity",
                    "failure_codes",
                    "shared_structural_hypothesis",
                    "shared_structural_hypothesis_commitment",
                    "correction_owner_paths",
                    "regression_risk_codes",
                    "negative_test_ids",
                },
                "CHANGE_LEDGER_INPUT_ROW_INVALID",
            )
            commitments = row["failure_case_commitments"]
            codes = row["failure_codes"]
            owners = row["correction_owner_paths"]
            risks = row["regression_risk_codes"]
            negative_tests = row["negative_test_ids"]
            hypothesis = row["shared_structural_hypothesis"]
            hypothesis_row = (
                _require_exact_keys(
                    hypothesis,
                    {
                        "schema_version",
                        "owner_scope",
                        "failure_layer",
                        "severity",
                        "failure_codes",
                        "common_cause_codes",
                        "correction_strategy_codes",
                        "affected_owner_paths",
                        "applies_to_case_count",
                    },
                    "CHANGE_LEDGER_HYPOTHESIS_INVALID",
                )
                if type(hypothesis) is dict
                else None
            )
            if (
                type(commitments) is not list
                or not commitments
                or commitments != sorted(set(commitments))
                or any(item not in blocking_by_commitment for item in commitments)
                or row["failure_layer"] not in _FAILURE_LAYERS
                or row["severity"] not in _BLOCKING_SEVERITIES
                or type(codes) is not list
                or not codes
                or codes != sorted(set(codes))
                or any(code not in _STEP11_REVIEW_FAILURE_CODES for code in codes)
                or hypothesis_row is None
                or hypothesis_row["schema_version"]
                != "cocolon.emlis.nls_v3.shared_failure_hypothesis.v2"
                or hypothesis_row["owner_scope"]
                != "step11_common_structural_owner"
                or hypothesis_row["failure_layer"] != row["failure_layer"]
                or hypothesis_row["severity"] != row["severity"]
                or hypothesis_row["failure_codes"] != codes
                or type(hypothesis_row["common_cause_codes"]) is not list
                or not hypothesis_row["common_cause_codes"]
                or hypothesis_row["common_cause_codes"]
                != sorted(set(hypothesis_row["common_cause_codes"]))
                or any(
                    code not in _STRUCTURAL_CAUSE_CODES
                    for code in hypothesis_row["common_cause_codes"]
                )
                or type(hypothesis_row["correction_strategy_codes"]) is not list
                or not hypothesis_row["correction_strategy_codes"]
                or hypothesis_row["correction_strategy_codes"]
                != sorted(set(hypothesis_row["correction_strategy_codes"]))
                or any(
                    code not in _CORRECTION_STRATEGY_CODES
                    for code in hypothesis_row["correction_strategy_codes"]
                )
                or hypothesis_row["affected_owner_paths"] != owners
                or hypothesis_row["applies_to_case_count"] != len(commitments)
                or artifact_sha256(hypothesis_row)
                != row["shared_structural_hypothesis_commitment"]
                or not _valid_nonzero_sha(row["shared_structural_hypothesis_commitment"])
                or type(owners) is not list
                or not owners
                or owners != sorted(set(owners))
                or any(
                    type(path) is not str
                    or _SAFE_PATH_RE.fullmatch(path) is None
                    or path not in dependency_by_path
                    for path in owners
                )
                or type(risks) is not list
                or not risks
                or risks != sorted(set(risks))
                or any(code not in _CHANGE_REGRESSION_RISK_CODES for code in risks)
                or not _valid_change_negative_test_ids(negative_tests)
            ):
                raise Step11CycleEvidenceError("CHANGE_LEDGER_INPUT_ROW_INVALID")
            for commitment in commitments:
                source = blocking_by_commitment[commitment]
                if row["severity"] != source["severity"] or not set(codes) <= source[
                    "reason_codes"
                ]:
                    raise Step11CycleEvidenceError("CHANGE_LEDGER_REVIEW_BINDING_INVALID")
            covered.update(commitments)
            normalized_rows.append(
                {
                    "schema_version": CYCLE_CHANGE_ROW_SCHEMA,
                    "cycle_initial_candidate_version_id": (
                        STEP11_INITIAL_CANDIDATE_VERSION_ID
                    ),
                    "cycle_final_candidate_version_id": final[
                        "candidate_version_id"
                    ],
                    "cycle_initial_source_closure_sha256": lock[
                        "source_dependency_closure_sha256"
                    ],
                    "cycle_final_source_closure_sha256": final[
                        "source_dependency_closure_sha256"
                    ],
                    "failure_evidence_origin": "cycle_initial_review",
                    "failure_evidence_initial_review_set_sha256": (
                        artifact_sha256(initial)
                    ),
                    "final_correction_delta_sha256": final_delta_sha,
                    "failure_case_commitments": commitments,
                    "failure_layer": row["failure_layer"],
                    "severity": row["severity"],
                    "failure_codes": codes,
                    "shared_structural_hypothesis": hypothesis_row,
                    "shared_structural_hypothesis_commitment": row[
                        "shared_structural_hypothesis_commitment"
                    ],
                    "correction_owner_paths": owners,
                    "regression_risk_codes": risks,
                    "negative_test_ids": negative_tests,
                    "negative_test_file_hashes": [
                        {
                            "path": _STEP11_SECURITY_TEST_PATH,
                            "sha256": security_test_sha256,
                        },
                        {
                            "path": _WORKAROUND_SCANNER_PATH,
                            "sha256": workaround_test_sha256,
                        },
                    ],
                    "case_specific_workaround_scan_receipt_sha256": artifact_sha256(
                        workaround_scan_receipt
                    ),
                    "cumulative_rerun_receipt_sha256": cumulative_sha,
                    "new_batch_first_run_receipt_sha256": lock[
                        "initial_batch_summary_sha256"
                    ],
                    "decision": "accepted",
                    "body_free": True,
                }
            )
        if covered != set(blocking_by_commitment):
            raise Step11CycleEvidenceError("CHANGE_LEDGER_BLOCKING_COVERAGE_INCOMPLETE")
        normalized_rows.sort(
            key=lambda row: (
                row["failure_case_commitments"],
                row["failure_layer"],
                row["shared_structural_hypothesis_commitment"],
            )
        )
        mode = "corrected"
        dependency_sha: str | None = artifact_sha256(dependency)
        scan_sha: str | None = artifact_sha256(workaround_scan_receipt)
    else:
        if (
            final_dependency_manifest is not None
            or workaround_scan_receipt is not None
            or rows
            or blocking_by_commitment
            or final["summary_sha256"] != lock["initial_batch_summary_sha256"]
        ):
            raise Step11CycleEvidenceError("NO_CHANGE_LEDGER_STATE_INVALID")
        normalized_rows = []
        mode = "accepted_without_source_change"
        dependency_sha = None
        scan_sha = None
        final_delta = None
    value = {
        "schema_version": CYCLE_CHANGE_LEDGER_SCHEMA,
        "cycle_id": STEP11_CYCLE_ID,
        "mode": mode,
        "initial_lock_sha256": artifact_sha256(lock),
        "initial_review_set_sha256": artifact_sha256(initial),
        "cycle_initial_candidate_version_id": (
            STEP11_INITIAL_CANDIDATE_VERSION_ID
        ),
        "cycle_final_candidate_version_id": final["candidate_version_id"],
        "cycle_initial_source_closure_sha256": lock[
            "source_dependency_closure_sha256"
        ],
        "cycle_final_source_closure_sha256": final[
            "source_dependency_closure_sha256"
        ],
        "final_dependency_manifest_sha256": dependency_sha,
        "final_correction_delta": final_delta,
        "cumulative100_receipt_sha256": cumulative_sha,
        "case_specific_workaround_scan_receipt_sha256": scan_sha,
        "rows": normalized_rows,
        "aggregate": {
            "initial_blocking_case_count": len(blocking_by_commitment),
            "covered_blocking_case_count": len(blocking_by_commitment),
            "accepted_change_row_count": len(normalized_rows),
        },
        "append_only": True,
        "body_free": True,
    }
    _require_body_free(value)
    return value


def validate_cycle_change_ledger(
    value: Any,
    **parents: Any,
) -> tuple[str, ...]:
    if type(value) is not dict:
        return ("CYCLE_CHANGE_LEDGER_MAPPING_REQUIRED",)
    try:
        input_rows = [
            {
                "failure_case_commitments": row["failure_case_commitments"],
                "failure_layer": row["failure_layer"],
                "severity": row["severity"],
                "failure_codes": row["failure_codes"],
                "shared_structural_hypothesis": row[
                    "shared_structural_hypothesis"
                ],
                "shared_structural_hypothesis_commitment": row[
                    "shared_structural_hypothesis_commitment"
                ],
                "correction_owner_paths": row["correction_owner_paths"],
                "regression_risk_codes": row["regression_risk_codes"],
                "negative_test_ids": row["negative_test_ids"],
            }
            for row in value.get("rows", [])
        ]
        expected = build_cycle_change_ledger(**parents, rows=input_rows)
    except (KeyError, TypeError, ValueError, Step11CycleEvidenceError):
        return ("CYCLE_CHANGE_LEDGER_CONTRACT_INVALID",)
    return () if value == expected else ("CYCLE_CHANGE_LEDGER_RECOMPUTATION_MISMATCH",)


def _lineage_artifact_map(
    artifacts: Sequence[Mapping[str, Any]],
    *,
    code: str,
) -> dict[str, dict[str, Any]]:
    if type(artifacts) not in {list, tuple}:
        raise Step11CycleEvidenceError(code)
    indexed: dict[str, dict[str, Any]] = {}
    for artifact in artifacts:
        if type(artifact) is not dict:
            raise Step11CycleEvidenceError(code)
        commitment = artifact_sha256(artifact)
        if commitment in indexed:
            raise Step11CycleEvidenceError(code)
        indexed[commitment] = dict(artifact)
    return indexed


def _lineage_batch_summary_projection(
    summary: Mapping[str, Any],
    *,
    candidate_sequence: Sequence[str],
) -> dict[str, Any]:
    """Project only receipt-backed, body-free execution facts.

    Historical Step 11 revisions used older summary schema revisions.  They
    must remain immutable and are therefore checked by their common closed
    row/count contract rather than reinterpreted as the current rc0020
    schema.  rc0010 additionally retains its original full validator.
    """

    if type(summary) is not dict:
        raise Step11CycleEvidenceError("RC_LINEAGE_BATCH_SUMMARY_INVALID")
    _require_body_free(summary)
    candidate_version_id = summary.get("candidate_version_id")
    run_id = summary.get("run_id")
    source_closure = summary.get("source_dependency_closure_sha256")
    rows = summary.get("case_rows")
    aggregate = summary.get("aggregate")
    expected_count = summary.get("expected_case_count")
    executed_count = summary.get("executed_case_count")
    if (
        summary.get("schema_version")
        not in {
            "cocolon.emlis.nls_v3.batch_run_receipt.v1",
            "cocolon.emlis.nls_v3.batch_run_receipt.step11.v1",
            STEP11_BATCH_RUN_SCHEMA,
        }
        or candidate_version_id not in candidate_sequence
        or type(run_id) is not str
        or _RUN_RE.fullmatch(run_id) is None
        or summary.get("batch_id") != STEP11_BATCH_ID
        or summary.get("batch_manifest_sha256")
        != FROZEN_BATCH001_MANIFEST_SHA256
        or not _valid_nonzero_sha(source_closure)
        or type(expected_count) is not int
        or type(expected_count) is bool
        or expected_count != 100
        or type(executed_count) is not int
        or type(executed_count) is bool
        or type(rows) is not list
        or executed_count != len(rows)
        or type(aggregate) is not dict
        or summary.get("body_free") is not True
    ):
        raise Step11CycleEvidenceError("RC_LINEAGE_BATCH_SUMMARY_INVALID")

    case_ids: list[str] = []
    status_counts: Counter[str] = Counter()
    for row in rows:
        if type(row) is not dict:
            raise Step11CycleEvidenceError("RC_LINEAGE_BATCH_SUMMARY_INVALID")
        case_id = row.get("case_id")
        status = row.get("status")
        if type(case_id) is not str or status not in _BATCH_STATUSES:
            raise Step11CycleEvidenceError("RC_LINEAGE_BATCH_SUMMARY_INVALID")
        case_ids.append(case_id)
        status_counts[status] += 1
    if tuple(case_ids) != _CASE_IDS:
        raise Step11CycleEvidenceError("RC_LINEAGE_BATCH_SUMMARY_INVALID")

    selected_count = aggregate.get("selected_count")
    no_valid_count = aggregate.get("no_valid_candidate_count")
    exception_count = aggregate.get("exception_count")
    fallback_count = aggregate.get("v1_fallback_count")
    if (
        selected_count != status_counts["selected"]
        or no_valid_count != status_counts["v3_no_valid_candidate"]
        or exception_count != status_counts["exception"]
        or type(fallback_count) is not int
        or type(fallback_count) is bool
        or fallback_count < 0
        or selected_count + no_valid_count + exception_count != executed_count
    ):
        raise Step11CycleEvidenceError("RC_LINEAGE_BATCH_SUMMARY_INVALID")
    complete = executed_count == expected_count
    if summary.get("all_expected_cases_executed") is not complete:
        raise Step11CycleEvidenceError("RC_LINEAGE_BATCH_SUMMARY_INVALID")
    clean = bool(
        complete
        and selected_count == expected_count
        and no_valid_count == 0
        and exception_count == 0
        and fallback_count == 0
    )
    expected_machine_status = (
        "clean" if clean else "failed" if complete else "incomplete"
    )
    if summary.get("machine_status") != expected_machine_status:
        raise Step11CycleEvidenceError("RC_LINEAGE_BATCH_SUMMARY_INVALID")
    if (
        candidate_version_id == STEP11_INITIAL_CANDIDATE_VERSION_ID
        and validate_historical_batch_run_summary(summary)
    ):
        raise Step11CycleEvidenceError("RC_LINEAGE_INITIAL_SUMMARY_INVALID")
    return {
        "summary_schema_version": summary["schema_version"],
        "batch_summary_sha256": artifact_sha256(summary),
        "candidate_version_id": candidate_version_id,
        "run_id": run_id,
        "source_dependency_closure_sha256": source_closure,
        "executed_case_count": executed_count,
        "selected_count": selected_count,
        "no_valid_candidate_count": no_valid_count,
        "exception_count": exception_count,
        "v1_fallback_count": fallback_count,
        "all_expected_cases_executed": complete,
        "machine_status": expected_machine_status,
        "receipt_bound": True,
    }


def _require_frozen_rc0020_historical_batch_summaries(
    summaries: Sequence[Mapping[str, Any]],
) -> None:
    """Bind v2 history to the exact retained historical run receipts."""

    expected = dict(_RC0020_FROZEN_HISTORICAL_BATCH_SUMMARY_SHA256)
    observed: dict[str, str] = {}
    for summary in summaries:
        if type(summary) is not dict:
            raise Step11CycleEvidenceError(
                "RC_LINEAGE_SUMMARY_PARENT_INVALID"
            )
        candidate = summary.get("candidate_version_id")
        if candidate not in expected:
            continue
        commitment = artifact_sha256(summary)
        if candidate in observed or commitment != expected[candidate]:
            raise Step11CycleEvidenceError(
                "RC_LINEAGE_HISTORICAL_SUMMARY_COMMITMENT_MISMATCH"
            )
        observed[candidate] = commitment
    if observed != expected:
        raise Step11CycleEvidenceError(
            "RC_LINEAGE_HISTORICAL_SUMMARY_COMMITMENT_MISMATCH"
        )


def _require_frozen_rc0021_historical_parents(
    dependency_manifests: Sequence[Mapping[str, Any]],
    summaries: Sequence[Mapping[str, Any]],
) -> None:
    """Bind v3 history to the exact machine-clean rc0020 preflight parents."""

    _require_frozen_rc0020_historical_batch_summaries(summaries)
    rc0020_manifests = [
        value
        for value in dependency_manifests
        if type(value) is dict
        and value.get("candidate_version_id")
        == STEP11_HISTORICAL_RC0020_CANDIDATE_VERSION_ID
    ]
    if (
        len(rc0020_manifests) != 1
        or validate_step11_dependency_manifest(rc0020_manifests[0])
        or artifact_sha256(rc0020_manifests[0])
        != FROZEN_RC0020_PREFLIGHT_MANIFEST_ARTIFACT_SHA256
        or rc0020_manifests[0].get("source_dependency_closure_sha256")
        != FROZEN_RC0020_PREFLIGHT_SOURCE_CLOSURE_SHA256
    ):
        raise Step11CycleEvidenceError(
            "RC_LINEAGE_RC0020_PREFLIGHT_MANIFEST_MISMATCH"
        )
    rc0020_summaries = [
        value
        for value in summaries
        if type(value) is dict
        and value.get("candidate_version_id")
        == STEP11_HISTORICAL_RC0020_CANDIDATE_VERSION_ID
    ]
    if (
        len(rc0020_summaries) != 1
        or artifact_sha256(rc0020_summaries[0])
        != FROZEN_RC0020_PREFLIGHT_BATCH_SUMMARY_SHA256
        or rc0020_summaries[0].get("source_dependency_closure_sha256")
        != FROZEN_RC0020_PREFLIGHT_SOURCE_CLOSURE_SHA256
        or rc0020_summaries[0].get("machine_status") != "clean"
        or rc0020_summaries[0].get("all_expected_cases_executed") is not True
        or rc0020_summaries[0].get("executed_case_count") != 100
        or rc0020_summaries[0].get("aggregate", {}).get("selected_count")
        != 100
        or rc0020_summaries[0].get("aggregate", {}).get(
            "no_valid_candidate_count"
        )
        != 0
        or rc0020_summaries[0].get("aggregate", {}).get("exception_count")
        != 0
        or rc0020_summaries[0].get("aggregate", {}).get("v1_fallback_count")
        != 0
    ):
        raise Step11CycleEvidenceError(
            "RC_LINEAGE_RC0020_PREFLIGHT_SUMMARY_MISMATCH"
        )


def _require_frozen_rc0022_historical_parents(
    dependency_manifests: Sequence[Mapping[str, Any]],
    summaries: Sequence[Mapping[str, Any]],
) -> None:
    """Bind v4 history to the exact rc0020 and rc0021 preflight chain."""

    _require_frozen_rc0021_historical_parents(
        dependency_manifests,
        summaries,
    )
    rc0021_manifests = [
        value
        for value in dependency_manifests
        if type(value) is dict
        and value.get("candidate_version_id")
        == STEP11_HISTORICAL_RC0021_CANDIDATE_VERSION_ID
    ]
    if (
        len(rc0021_manifests) != 1
        or validate_step11_dependency_manifest(rc0021_manifests[0])
        or artifact_sha256(rc0021_manifests[0])
        != FROZEN_RC0021_PREFLIGHT_MANIFEST_ARTIFACT_SHA256
        or rc0021_manifests[0].get("source_dependency_closure_sha256")
        != FROZEN_RC0021_PREFLIGHT_SOURCE_CLOSURE_SHA256
        or rc0021_manifests[0].get("before_candidate_version_id")
        != STEP11_HISTORICAL_RC0020_CANDIDATE_VERSION_ID
        or rc0021_manifests[0].get("before_source_closure_sha256")
        != FROZEN_RC0020_PREFLIGHT_SOURCE_CLOSURE_SHA256
    ):
        raise Step11CycleEvidenceError(
            "RC_LINEAGE_RC0021_PREFLIGHT_MANIFEST_MISMATCH"
        )
    rc0021_summaries = [
        value
        for value in summaries
        if type(value) is dict
        and value.get("candidate_version_id")
        == STEP11_HISTORICAL_RC0021_CANDIDATE_VERSION_ID
    ]
    if (
        len(rc0021_summaries) != 1
        or artifact_sha256(rc0021_summaries[0])
        != FROZEN_RC0021_PREFLIGHT_BATCH_SUMMARY_SHA256
        or rc0021_summaries[0].get("source_dependency_closure_sha256")
        != FROZEN_RC0021_PREFLIGHT_SOURCE_CLOSURE_SHA256
        or rc0021_summaries[0].get("machine_status") != "clean"
        or rc0021_summaries[0].get("all_expected_cases_executed") is not True
        or rc0021_summaries[0].get("executed_case_count") != 100
        or rc0021_summaries[0].get("aggregate", {}).get("selected_count")
        != 100
        or rc0021_summaries[0].get("aggregate", {}).get(
            "no_valid_candidate_count"
        )
        != 0
        or rc0021_summaries[0].get("aggregate", {}).get("exception_count")
        != 0
        or rc0021_summaries[0].get("aggregate", {}).get("v1_fallback_count")
        != 0
    ):
        raise Step11CycleEvidenceError(
            "RC_LINEAGE_RC0021_PREFLIGHT_SUMMARY_MISMATCH"
        )


def _require_frozen_rc0023_historical_parents(
    dependency_manifests: Sequence[Mapping[str, Any]],
    summaries: Sequence[Mapping[str, Any]],
) -> None:
    """Bind v5 history to the exact failed rc0022 formal execution.

    rc0022 is a completed, receipt-backed machine failure.  It must remain in
    the append-only history as failed and superseded; it cannot be omitted,
    relabelled clean, or treated as an unexecuted revision.
    """

    _require_frozen_rc0022_historical_parents(
        dependency_manifests,
        summaries,
    )
    rc0022_manifests = [
        value
        for value in dependency_manifests
        if type(value) is dict
        and value.get("candidate_version_id")
        == STEP11_HISTORICAL_RC0022_CANDIDATE_VERSION_ID
    ]
    if (
        len(rc0022_manifests) != 1
        or validate_step11_dependency_manifest(rc0022_manifests[0])
        or artifact_sha256(rc0022_manifests[0])
        != FROZEN_RC0022_FORMAL_MANIFEST_ARTIFACT_SHA256
        or rc0022_manifests[0].get("source_dependency_closure_sha256")
        != FROZEN_RC0022_FORMAL_SOURCE_CLOSURE_SHA256
        or rc0022_manifests[0].get("before_candidate_version_id")
        != STEP11_HISTORICAL_RC0021_CANDIDATE_VERSION_ID
        or rc0022_manifests[0].get("before_source_closure_sha256")
        != FROZEN_RC0021_PREFLIGHT_SOURCE_CLOSURE_SHA256
        or type(rc0022_manifests[0].get("file_hashes")) is not list
        or len(rc0022_manifests[0]["file_hashes"]) != 141
    ):
        raise Step11CycleEvidenceError(
            "RC_LINEAGE_RC0022_FORMAL_MANIFEST_MISMATCH"
        )

    rc0022_summaries = [
        value
        for value in summaries
        if type(value) is dict
        and value.get("candidate_version_id")
        == STEP11_HISTORICAL_RC0022_CANDIDATE_VERSION_ID
    ]
    if len(rc0022_summaries) != 1:
        raise Step11CycleEvidenceError(
            "RC_LINEAGE_RC0022_FORMAL_SUMMARY_MISMATCH"
        )


def _require_frozen_rc0024_historical_parents(
    dependency_manifests: Sequence[Mapping[str, Any]],
    summaries: Sequence[Mapping[str, Any]],
) -> None:
    """Bind v6 history to the exact machine-clean rc0023 formal run."""

    _require_frozen_rc0023_historical_parents(
        dependency_manifests,
        summaries,
    )
    rc0023_manifests = [
        value
        for value in dependency_manifests
        if type(value) is dict
        and value.get("candidate_version_id")
        == STEP11_HISTORICAL_RC0023_CANDIDATE_VERSION_ID
    ]
    if (
        len(rc0023_manifests) != 1
        or validate_step11_dependency_manifest(rc0023_manifests[0])
        or artifact_sha256(rc0023_manifests[0])
        != FROZEN_RC0023_FORMAL_MANIFEST_ARTIFACT_SHA256
        or rc0023_manifests[0].get("source_dependency_closure_sha256")
        != FROZEN_RC0023_FORMAL_SOURCE_CLOSURE_SHA256
        or rc0023_manifests[0].get("before_candidate_version_id")
        != STEP11_HISTORICAL_RC0022_CANDIDATE_VERSION_ID
        or rc0023_manifests[0].get("before_source_closure_sha256")
        != FROZEN_RC0022_FORMAL_SOURCE_CLOSURE_SHA256
        or type(rc0023_manifests[0].get("file_hashes")) is not list
        or len(rc0023_manifests[0]["file_hashes"]) != 145
    ):
        raise Step11CycleEvidenceError(
            "RC_LINEAGE_RC0023_FORMAL_MANIFEST_MISMATCH"
        )

    rc0023_summaries = [
        value
        for value in summaries
        if type(value) is dict
        and value.get("candidate_version_id")
        == STEP11_HISTORICAL_RC0023_CANDIDATE_VERSION_ID
    ]
    if len(rc0023_summaries) != 1:
        raise Step11CycleEvidenceError(
            "RC_LINEAGE_RC0023_FORMAL_SUMMARY_MISMATCH"
        )
    summary = rc0023_summaries[0]
    aggregate = summary.get("aggregate", {})
    if (
        artifact_sha256(summary)
        != FROZEN_RC0023_FORMAL_BATCH_SUMMARY_SHA256
        or summary.get("dependency_manifest_sha256")
        != FROZEN_RC0023_FORMAL_MANIFEST_ARTIFACT_SHA256
        or summary.get("source_dependency_closure_sha256")
        != FROZEN_RC0023_FORMAL_SOURCE_CLOSURE_SHA256
        or summary.get("source_closure_start_sha256")
        != FROZEN_RC0023_FORMAL_SOURCE_CLOSURE_SHA256
        or summary.get("source_closure_end_sha256")
        != FROZEN_RC0023_FORMAL_SOURCE_CLOSURE_SHA256
        or summary.get("source_closure_stable") is not True
        or summary.get("machine_status") != "clean"
        or summary.get("all_expected_cases_executed") is not True
        or summary.get("executed_case_count") != 100
        or aggregate.get("selected_count") != 100
        or aggregate.get("no_valid_candidate_count") != 0
        or aggregate.get("exception_count") != 0
        or aggregate.get("v1_fallback_count") != 0
    ):
        raise Step11CycleEvidenceError(
            "RC_LINEAGE_RC0023_FORMAL_SUMMARY_MISMATCH"
        )
def _lineage_event(
    *,
    event_index: int,
    previous_event_commitment: str | None,
    payload: Mapping[str, Any],
    event_schema: str,
) -> dict[str, Any]:
    material = {
        "schema_version": event_schema,
        "event_index": event_index,
        "previous_event_commitment": previous_event_commitment,
        **dict(payload),
        "body_free": True,
    }
    _require_body_free(material)
    return {**material, "event_commitment": artifact_sha256(material)}


def _build_rc_correction_rerun_lineage(
    events: Sequence[Mapping[str, Any]],
    *,
    dependency_manifests: Sequence[Mapping[str, Any]],
    batch_run_summaries: Sequence[Mapping[str, Any]],
    candidate_sequence: Sequence[str],
    final_candidate_version_id: str,
    lineage_schema: str,
    event_schema: str,
    require_immediate_final_dependency_base: bool,
    required_failed_product_read_candidate_version_id: str | None = None,
    required_failed_product_read_candidate_version_ids: Sequence[str]
    | None = None,
    required_product_read_failure_case_ids: Mapping[
        str, Sequence[str]
    ]
    | None = None,
    required_failed_execution_candidate_version_ids: Sequence[str]
    | None = None,
) -> dict[str, Any]:
    """Build one closed append-only correction/rerun history.

    An execution event cannot be constructed from a run ID or claimed outcome
    alone.  It must point to one of ``batch_run_summaries`` and all execution
    facts are independently projected from that immutable receipt.  Revisions
    for which no durable receipt exists are represented explicitly, with no
    run fields and no ability to contribute to the passed-rerun aggregate.
    """

    if type(events) not in {list, tuple} or not events:
        raise Step11CycleEvidenceError("RC_LINEAGE_EVENT_SEQUENCE_INVALID")
    if (
        required_failed_product_read_candidate_version_id is not None
        and required_failed_product_read_candidate_version_ids is not None
    ):
        raise Step11CycleEvidenceError(
            "RC_LINEAGE_PRODUCT_READ_REQUIREMENT_INVALID"
        )
    required_product_read_candidates = tuple(
        required_failed_product_read_candidate_version_ids
        if required_failed_product_read_candidate_version_ids is not None
        else (
            (required_failed_product_read_candidate_version_id,)
            if required_failed_product_read_candidate_version_id is not None
            else ()
        )
    )
    required_failed_execution_candidates = tuple(
        required_failed_execution_candidate_version_ids or ()
    )
    candidate_order = {candidate: index for index, candidate in enumerate(candidate_sequence)}
    if (
        len(required_product_read_candidates)
        != len(set(required_product_read_candidates))
        or any(
            candidate not in candidate_order
            or candidate == final_candidate_version_id
            for candidate in required_product_read_candidates
        )
        or list(required_product_read_candidates)
        != sorted(
            required_product_read_candidates,
            key=candidate_order.__getitem__,
        )
    ):
        raise Step11CycleEvidenceError(
            "RC_LINEAGE_PRODUCT_READ_REQUIREMENT_INVALID"
        )
    if (
        len(required_failed_execution_candidates)
        != len(set(required_failed_execution_candidates))
        or any(
            candidate not in candidate_order
            or candidate == final_candidate_version_id
            for candidate in required_failed_execution_candidates
        )
        or list(required_failed_execution_candidates)
        != sorted(
            required_failed_execution_candidates,
            key=candidate_order.__getitem__,
        )
    ):
        raise Step11CycleEvidenceError(
            "RC_LINEAGE_FAILED_EXECUTION_REQUIREMENT_INVALID"
        )
    required_case_ids_by_candidate = {
        candidate: tuple(case_ids)
        for candidate, case_ids in (
            required_product_read_failure_case_ids or {}
        ).items()
    }
    if (
        not set(required_case_ids_by_candidate)
        <= set(required_product_read_candidates)
        or any(
            not case_ids
            or len(case_ids) != len(set(case_ids))
            or tuple(sorted(case_ids)) != case_ids
            or any(case_id not in _CASE_ID_SET for case_id in case_ids)
            for case_ids in required_case_ids_by_candidate.values()
        )
    ):
        raise Step11CycleEvidenceError(
            "RC_LINEAGE_PRODUCT_READ_REQUIREMENT_INVALID"
        )
    manifest_by_sha = _lineage_artifact_map(
        dependency_manifests,
        code="RC_LINEAGE_DEPENDENCY_PARENT_INVALID",
    )
    summary_by_sha = _lineage_artifact_map(
        batch_run_summaries,
        code="RC_LINEAGE_SUMMARY_PARENT_INVALID",
    )
    summary_projection_by_sha = {
        commitment: _lineage_batch_summary_projection(
            summary,
            candidate_sequence=candidate_sequence,
        )
        for commitment, summary in summary_by_sha.items()
    }

    normalized: list[dict[str, Any]] = []
    used_manifests: set[str] = set()
    used_summaries: set[str] = set()
    candidate_states: dict[str, dict[str, Any]] = {}
    correction_sequence: list[str] = []
    previous_event_commitment: str | None = None
    active_candidate: str | None = None
    next_correction_number = 11

    def append_event(payload: Mapping[str, Any]) -> None:
        nonlocal previous_event_commitment
        event = _lineage_event(
            event_index=len(normalized),
            previous_event_commitment=previous_event_commitment,
            payload=payload,
            event_schema=event_schema,
        )
        normalized.append(event)
        previous_event_commitment = event["event_commitment"]

    for raw_event in events:
        if type(raw_event) is not dict:
            raise Step11CycleEvidenceError("RC_LINEAGE_EVENT_INVALID")
        event_type = raw_event.get("event_type")

        if event_type == "initial_run_observed":
            row = _require_exact_keys(
                raw_event,
                {
                    "event_type",
                    "candidate_version_id",
                    "batch_summary_sha256",
                },
                "RC_LINEAGE_INITIAL_EVENT_INVALID",
            )
            summary_sha = row["batch_summary_sha256"]
            projection = summary_projection_by_sha.get(summary_sha)
            if (
                normalized
                or row["candidate_version_id"]
                != STEP11_INITIAL_CANDIDATE_VERSION_ID
                or projection is None
                or projection["candidate_version_id"]
                != STEP11_INITIAL_CANDIDATE_VERSION_ID
            ):
                raise Step11CycleEvidenceError(
                    "RC_LINEAGE_INITIAL_EVENT_INVALID"
                )
            used_summaries.add(summary_sha)
            active_candidate = STEP11_INITIAL_CANDIDATE_VERSION_ID
            candidate_states[active_candidate] = {
                "source_kind": "initial_run_receipt",
                "source_dependency_closure_sha256": projection[
                    "source_dependency_closure_sha256"
                ],
                "executions": [
                    {**projection, "execution_scope": "formal_initial_run"}
                ],
                "terminal_disposition": None,
                "pending_recorded": False,
                "product_reads": [],
            }
            append_event(
                {
                    "event_type": event_type,
                    "candidate_version_id": active_candidate,
                    "execution_scope": "formal_initial_run",
                    **projection,
                    "outcome_receipt_commitment": summary_sha,
                    "counts_as_clean_formal_rerun": False,
                }
            )
            continue

        if active_candidate is None:
            raise Step11CycleEvidenceError("RC_LINEAGE_INITIAL_EVENT_REQUIRED")

        if event_type == "correction_recorded":
            row = _require_exact_keys(
                raw_event,
                {
                    "event_type",
                    "candidate_version_id",
                    "source_state_kind",
                    "source_state_artifact_sha256",
                    "failure_evidence_commitment",
                    "structural_hypothesis_commitment",
                    "changed_file_set_commitment",
                    "negative_suite_commitment",
                    "correction_decision_commitment",
                },
                "RC_LINEAGE_CORRECTION_EVENT_INVALID",
            )
            candidate = row["candidate_version_id"]
            expected_candidate = f"nls_v3_rc_{next_correction_number:04d}"
            previous_state = candidate_states[active_candidate]
            source_kind = row["source_state_kind"]
            commitment_fields = (
                "source_state_artifact_sha256",
                "failure_evidence_commitment",
                "structural_hypothesis_commitment",
                "changed_file_set_commitment",
                "negative_suite_commitment",
                "correction_decision_commitment",
            )
            if (
                candidate != expected_candidate
                or previous_state["terminal_disposition"]
                not in {
                    "historical_unfrozen_no_receipt",
                    "superseded_after_observed_result",
                    "superseded_unexecuted",
                }
                or source_kind not in _LINEAGE_CORRECTION_SOURCE_KINDS
                or any(not _valid_nonzero_sha(row[key]) for key in commitment_fields)
            ):
                raise Step11CycleEvidenceError(
                    "RC_LINEAGE_CORRECTION_EVENT_INVALID"
                )

            source_artifact_sha = row["source_state_artifact_sha256"]
            manifest_sha: str | None = None
            source_closure: str | None = None
            diff_base_candidate: str | None = None
            diff_base_closure: str | None = None
            if source_kind == "dependency_manifest":
                manifest = manifest_by_sha.get(source_artifact_sha)
                if (
                    manifest is None
                    or validate_step11_dependency_manifest(manifest)
                    or manifest.get("candidate_version_id") != candidate
                    or artifact_sha256(manifest.get("changed_file_hashes"))
                    != row["changed_file_set_commitment"]
                ):
                    raise Step11CycleEvidenceError(
                        "RC_LINEAGE_DEPENDENCY_BINDING_INVALID"
                    )
                if (
                    require_immediate_final_dependency_base
                    and candidate == final_candidate_version_id
                    and (
                        manifest.get("before_candidate_version_id")
                        != active_candidate
                        or manifest.get("before_source_closure_sha256")
                        != previous_state[
                            "source_dependency_closure_sha256"
                        ]
                    )
                ):
                    raise Step11CycleEvidenceError(
                        "RC_LINEAGE_FINAL_DEPENDENCY_BASE_INVALID"
                    )
                manifest_sha = source_artifact_sha
                used_manifests.add(manifest_sha)
                source_closure = manifest["source_dependency_closure_sha256"]
                diff_base_candidate = manifest["before_candidate_version_id"]
                diff_base_closure = manifest["before_source_closure_sha256"]
            elif (
                source_kind == "historical_unfrozen_no_receipt"
                and candidate == final_candidate_version_id
            ) or (
                source_kind == "working_state_unfrozen"
                and candidate != final_candidate_version_id
            ):
                raise Step11CycleEvidenceError(
                    "RC_LINEAGE_CORRECTION_SOURCE_KIND_INVALID"
                )

            correction_sequence.append(candidate)
            candidate_states[candidate] = {
                "source_kind": source_kind,
                "source_dependency_closure_sha256": source_closure,
                "executions": [],
                "terminal_disposition": None,
                "pending_recorded": False,
                "product_reads": [],
            }
            append_event(
                {
                    "event_type": event_type,
                    "candidate_version_id": candidate,
                    "lineage_predecessor_candidate_version_id": active_candidate,
                    "lineage_predecessor_source_closure_sha256": previous_state[
                        "source_dependency_closure_sha256"
                    ],
                    "source_state_kind": source_kind,
                    "source_state_artifact_sha256": source_artifact_sha,
                    "dependency_manifest_sha256": manifest_sha,
                    "dependency_diff_base_candidate_version_id": (
                        diff_base_candidate
                    ),
                    "dependency_diff_base_source_closure_sha256": (
                        diff_base_closure
                    ),
                    "source_dependency_closure_sha256": source_closure,
                    "failure_evidence_commitment": row[
                        "failure_evidence_commitment"
                    ],
                    "structural_hypothesis_commitment": row[
                        "structural_hypothesis_commitment"
                    ],
                    "changed_file_set_commitment": row[
                        "changed_file_set_commitment"
                    ],
                    "negative_suite_commitment": row[
                        "negative_suite_commitment"
                    ],
                    "correction_decision_commitment": row[
                        "correction_decision_commitment"
                    ],
                    "execution_claimed": False,
                }
            )
            active_candidate = candidate
            next_correction_number += 1
            continue

        if event_type == "execution_observed":
            row = _require_exact_keys(
                raw_event,
                {
                    "event_type",
                    "candidate_version_id",
                    "execution_scope",
                    "batch_summary_sha256",
                },
                "RC_LINEAGE_EXECUTION_EVENT_INVALID",
            )
            summary_sha = row["batch_summary_sha256"]
            projection = summary_projection_by_sha.get(summary_sha)
            state = candidate_states[active_candidate]
            if (
                row["candidate_version_id"] != active_candidate
                or active_candidate == STEP11_INITIAL_CANDIDATE_VERSION_ID
                or row["execution_scope"] not in _LINEAGE_EXECUTION_SCOPES
                or state["terminal_disposition"] is not None
                or state["source_kind"] != "dependency_manifest"
                or projection is None
                or projection["candidate_version_id"] != active_candidate
                or projection["source_dependency_closure_sha256"]
                != state["source_dependency_closure_sha256"]
                or any(
                    execution["batch_summary_sha256"] == summary_sha
                    for execution in state["executions"]
                )
            ):
                raise Step11CycleEvidenceError(
                    "RC_LINEAGE_EXECUTION_EVENT_INVALID"
                )
            state["executions"].append(
                {**projection, "execution_scope": row["execution_scope"]}
            )
            used_summaries.add(summary_sha)
            clean_formal = bool(
                row["execution_scope"] == "formal_cumulative_rerun"
                and projection["machine_status"] == "clean"
                and projection["all_expected_cases_executed"] is True
                and projection["executed_case_count"] == 100
            )
            append_event(
                {
                    "event_type": event_type,
                    "candidate_version_id": active_candidate,
                    "execution_scope": row["execution_scope"],
                    **projection,
                    "outcome_receipt_commitment": summary_sha,
                    "counts_as_clean_formal_rerun": clean_formal,
                }
            )
            continue

        if event_type == "product_read_observed":
            if not required_product_read_candidates:
                raise Step11CycleEvidenceError(
                    "RC_LINEAGE_PRODUCT_READ_EVENT_INVALID"
                )
            expected_failure_case_ids = required_case_ids_by_candidate.get(
                str(active_candidate)
            )
            product_read_keys = {
                "event_type",
                "candidate_version_id",
                "batch_summary_sha256",
                "review_outcome",
                "maximum_severity",
                "failure_axis_codes",
                "failure_reason_codes",
                "review_receipt_commitment",
            }
            if expected_failure_case_ids is not None:
                product_read_keys.add("failure_case_ids")
            row = _require_exact_keys(
                raw_event,
                product_read_keys,
                "RC_LINEAGE_PRODUCT_READ_EVENT_INVALID",
            )
            state = candidate_states[active_candidate]
            summary_sha = row["batch_summary_sha256"]
            matching_execution = next(
                (
                    execution
                    for execution in state["executions"]
                    if execution["batch_summary_sha256"] == summary_sha
                ),
                None,
            )
            failure_axes = row["failure_axis_codes"]
            failure_reasons = row["failure_reason_codes"]
            failure_case_ids = row.get("failure_case_ids")
            if (
                active_candidate not in required_product_read_candidates
                or row["candidate_version_id"] != active_candidate
                or state["terminal_disposition"] is not None
                or state["product_reads"]
                or matching_execution is None
                or matching_execution["execution_scope"] != "preflight"
                or matching_execution["machine_status"] != "clean"
                or matching_execution["all_expected_cases_executed"] is not True
                or matching_execution["executed_case_count"] != 100
                or row["review_outcome"] != "failed"
                or row["review_outcome"] not in _LINEAGE_PRODUCT_READ_OUTCOMES
                or row["maximum_severity"] != "MAJOR"
                or row["maximum_severity"]
                not in _LINEAGE_PRODUCT_READ_SEVERITIES
                or type(failure_axes) is not list
                or not failure_axes
                or failure_axes != sorted(set(failure_axes))
                or any(
                    type(code) is not str or _CODE_RE.fullmatch(code) is None
                    for code in failure_axes
                )
                or type(failure_reasons) is not list
                or not failure_reasons
                or failure_reasons != sorted(set(failure_reasons))
                or any(
                    type(code) is not str or _CODE_RE.fullmatch(code) is None
                    for code in failure_reasons
                )
                or (
                    expected_failure_case_ids is not None
                    and failure_case_ids
                    != list(expected_failure_case_ids)
                )
                or not _valid_nonzero_sha(row["review_receipt_commitment"])
            ):
                raise Step11CycleEvidenceError(
                    "RC_LINEAGE_PRODUCT_READ_EVENT_INVALID"
                )
            product_read = {
                "batch_summary_sha256": summary_sha,
                "review_outcome": row["review_outcome"],
                "maximum_severity": row["maximum_severity"],
                "failure_axis_codes": list(failure_axes),
                "failure_reason_codes": list(failure_reasons),
                **(
                    {"failure_case_ids": list(expected_failure_case_ids)}
                    if expected_failure_case_ids is not None
                    else {}
                ),
                "review_receipt_commitment": row[
                    "review_receipt_commitment"
                ],
                "acceptance_eligible": False,
            }
            state["product_reads"].append(product_read)
            append_event(
                {
                    "event_type": event_type,
                    "candidate_version_id": active_candidate,
                    **product_read,
                    "counts_as_passed_rerun": False,
                }
            )
            continue

        if event_type == "revision_disposition":
            row = _require_exact_keys(
                raw_event,
                {
                    "event_type",
                    "candidate_version_id",
                    "disposition",
                    "decision_receipt_commitment",
                },
                "RC_LINEAGE_DISPOSITION_EVENT_INVALID",
            )
            state = candidate_states[active_candidate]
            disposition = row["disposition"]
            executions = state["executions"]
            formal_clean = any(
                execution["execution_scope"] == "formal_cumulative_rerun"
                and execution["machine_status"] == "clean"
                and execution["all_expected_cases_executed"] is True
                and execution["executed_case_count"] == 100
                for execution in executions
            )
            failed_product_read = any(
                review["review_outcome"] == "failed"
                for review in state["product_reads"]
            )
            failed_machine_execution = any(
                execution["execution_scope"] == "formal_cumulative_rerun"
                and execution["machine_status"] == "failed"
                and execution["all_expected_cases_executed"] is True
                and execution["executed_case_count"] == 100
                for execution in executions
            )
            if (
                row["candidate_version_id"] != active_candidate
                or disposition not in _LINEAGE_DISPOSITIONS
                or not _valid_nonzero_sha(row["decision_receipt_commitment"])
                or state["terminal_disposition"] is not None
            ):
                raise Step11CycleEvidenceError(
                    "RC_LINEAGE_DISPOSITION_EVENT_INVALID"
                )
            if disposition == "historical_unfrozen_no_receipt" and (
                state["source_kind"] != "historical_unfrozen_no_receipt"
                or executions
            ):
                raise Step11CycleEvidenceError(
                    "RC_LINEAGE_DISPOSITION_EVENT_INVALID"
                )
            if disposition == "superseded_unexecuted" and executions:
                raise Step11CycleEvidenceError(
                    "RC_LINEAGE_DISPOSITION_EVENT_INVALID"
                )
            if (
                disposition == "superseded_after_observed_result"
                and not executions
            ):
                raise Step11CycleEvidenceError(
                    "RC_LINEAGE_DISPOSITION_EVENT_INVALID"
                )
            if disposition == "current_pending_rerun":
                if (
                    active_candidate != final_candidate_version_id
                    or formal_clean
                    or state["pending_recorded"] is True
                ):
                    raise Step11CycleEvidenceError(
                        "RC_LINEAGE_DISPOSITION_EVENT_INVALID"
                    )
                state["pending_recorded"] = True
            elif disposition == "cycle_final_candidate":
                if (
                    active_candidate != final_candidate_version_id
                    or state["source_kind"] != "dependency_manifest"
                    or not formal_clean
                    or failed_product_read
                ):
                    raise Step11CycleEvidenceError(
                        "RC_LINEAGE_FINAL_DISPOSITION_INVALID"
                    )
                state["terminal_disposition"] = disposition
            else:
                if active_candidate == final_candidate_version_id:
                    raise Step11CycleEvidenceError(
                        "RC_LINEAGE_DISPOSITION_EVENT_INVALID"
                    )
                state["terminal_disposition"] = disposition
            append_event(
                {
                    "event_type": event_type,
                    "candidate_version_id": active_candidate,
                    "disposition": disposition,
                    "decision_receipt_commitment": row[
                        "decision_receipt_commitment"
                    ],
                    "observed_execution_count": len(executions),
                    "receipt_bound_clean_execution_observed": formal_clean,
                    **(
                        {
                            "failed_product_read_observed": (
                                failed_product_read
                            )
                        }
                        if required_product_read_candidates
                        else {}
                    ),
                    **(
                        {
                            "failed_machine_execution_observed": (
                                failed_machine_execution
                            )
                        }
                        if active_candidate
                        in required_failed_execution_candidates
                        else {}
                    ),
                    "counts_as_passed_rerun": bool(
                        disposition == "cycle_final_candidate"
                        and formal_clean
                        and not failed_product_read
                    ),
                }
            )
            continue

        raise Step11CycleEvidenceError("RC_LINEAGE_EVENT_TYPE_INVALID")

    if correction_sequence != list(candidate_sequence[1:]):
        raise Step11CycleEvidenceError("RC_LINEAGE_CANDIDATE_SEQUENCE_INCOMPLETE")
    for candidate in candidate_sequence[:-1]:
        if candidate_states[candidate]["terminal_disposition"] not in {
            "historical_unfrozen_no_receipt",
            "superseded_after_observed_result",
            "superseded_unexecuted",
        }:
            raise Step11CycleEvidenceError(
                "RC_LINEAGE_HISTORICAL_DISPOSITION_INCOMPLETE"
            )
    final_state = candidate_states[final_candidate_version_id]
    final_ready = final_state["terminal_disposition"] == "cycle_final_candidate"
    if not final_ready and final_state["pending_recorded"] is not True:
        raise Step11CycleEvidenceError("RC_LINEAGE_CURRENT_DISPOSITION_MISSING")
    for product_candidate in required_product_read_candidates:
        product_state = candidate_states.get(product_candidate)
        expected_failure_case_ids = required_case_ids_by_candidate.get(
            product_candidate
        )
        if (
            product_state is None
            or len(product_state["product_reads"]) != 1
            or product_state["product_reads"][0]["review_outcome"]
            != "failed"
            or product_state["product_reads"][0]["maximum_severity"]
            != "MAJOR"
            or (
                expected_failure_case_ids is not None
                and product_state["product_reads"][0].get(
                    "failure_case_ids"
                )
                != list(expected_failure_case_ids)
            )
            or product_state["terminal_disposition"]
            != "superseded_after_observed_result"
        ):
            raise Step11CycleEvidenceError(
                "RC_LINEAGE_REQUIRED_PRODUCT_READ_FAILURE_MISSING"
            )
    for failed_candidate in required_failed_execution_candidates:
        failed_state = candidate_states.get(failed_candidate)
        failed_executions = (
            failed_state["executions"] if failed_state is not None else []
        )
        if (
            failed_state is None
            or len(failed_executions) != 1
            or failed_executions[0]["execution_scope"]
            != "formal_cumulative_rerun"
            or failed_executions[0]["machine_status"] != "failed"
            or failed_executions[0]["all_expected_cases_executed"] is not True
            or failed_executions[0]["executed_case_count"] != 100
            or failed_state["terminal_disposition"]
            != "superseded_after_observed_result"
        ):
            raise Step11CycleEvidenceError(
                "RC_LINEAGE_REQUIRED_FAILED_EXECUTION_MISSING"
            )
    if used_manifests != set(manifest_by_sha):
        raise Step11CycleEvidenceError("RC_LINEAGE_UNUSED_DEPENDENCY_PARENT")
    if used_summaries != set(summary_by_sha):
        raise Step11CycleEvidenceError("RC_LINEAGE_UNUSED_SUMMARY_PARENT")

    execution_events = [
        event
        for event in normalized
        if event["event_type"]
        in {"initial_run_observed", "execution_observed"}
    ]
    no_receipt_revisions = [
        candidate
        for candidate, state in candidate_states.items()
        if state["source_kind"] == "historical_unfrozen_no_receipt"
    ]
    value = {
        "schema_version": lineage_schema,
        "cycle_id": STEP11_CYCLE_ID,
        "expected_candidate_sequence": list(candidate_sequence),
        "initial_candidate_version_id": STEP11_INITIAL_CANDIDATE_VERSION_ID,
        "current_candidate_version_id": final_candidate_version_id,
        "events": normalized,
        "lineage_head_commitment": previous_event_commitment,
        "aggregate": {
            "candidate_revision_count": len(candidate_states),
            "correction_event_count": len(correction_sequence),
            "receipt_bound_execution_count": len(execution_events),
            "receipt_bound_clean_formal_rerun_count": sum(
                event.get("counts_as_clean_formal_rerun") is True
                for event in execution_events
            ),
            "historical_no_receipt_revision_count": len(
                no_receipt_revisions
            ),
            "unreceipted_execution_claim_count": 0,
            **(
                {
                    "product_read_observation_count": sum(
                        len(state["product_reads"])
                        for state in candidate_states.values()
                    ),
                    "failed_product_read_count": sum(
                        review["review_outcome"] == "failed"
                        for state in candidate_states.values()
                        for review in state["product_reads"]
                    ),
                }
                if required_product_read_candidates
                else {}
            ),
            **(
                {
                    "failed_machine_execution_count": len(
                        required_failed_execution_candidates
                    )
                }
                if required_failed_execution_candidates
                else {}
            ),
        },
        **(
            {
                "failed_product_read_candidate_sequence": list(
                    required_product_read_candidates
                )
            }
            if len(required_product_read_candidates) > 1
            else {}
        ),
        **(
            {
                "failed_machine_execution_candidate_sequence": list(
                    required_failed_execution_candidates
                )
            }
            if required_failed_execution_candidates
            else {}
        ),
        "historical_sequence_complete": True,
        "outcome_and_receipt_commitments_explicit": True,
        "acceptance_lineage_ready": final_ready,
        "append_only_hash_chain": True,
        "body_free": True,
    }
    _require_body_free(value)
    return value


def build_rc0010_rc0019_correction_rerun_lineage(
    events: Sequence[Mapping[str, Any]],
    *,
    dependency_manifests: Sequence[Mapping[str, Any]],
    batch_run_summaries: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Rebuild the frozen v1 rc0010--rc0019 history without reinterpretation."""

    return _build_rc_correction_rerun_lineage(
        events,
        dependency_manifests=dependency_manifests,
        batch_run_summaries=batch_run_summaries,
        candidate_sequence=_RC0010_RC0019_SEQUENCE,
        final_candidate_version_id=(
            STEP11_HISTORICAL_RC0019_CANDIDATE_VERSION_ID
        ),
        lineage_schema=RC_CORRECTION_RERUN_LINEAGE_V1_SCHEMA,
        event_schema=RC_CORRECTION_RERUN_LINEAGE_EVENT_V1_SCHEMA,
        require_immediate_final_dependency_base=False,
    )


def build_rc0010_rc0020_correction_rerun_lineage(
    events: Sequence[Mapping[str, Any]],
    *,
    dependency_manifests: Sequence[Mapping[str, Any]],
    batch_run_summaries: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build v2 history with rc0019 observed as an immutable predecessor.

    The final rc0020 dependency manifest must be based on the exact rc0019
    closure already carried by the preceding lineage state.  This prevents a
    new final receipt from silently jumping back to rc0010 while presenting
    its changed-file set as the rc0019-to-rc0020 correction.
    """

    _require_frozen_rc0020_historical_batch_summaries(batch_run_summaries)

    return _build_rc_correction_rerun_lineage(
        events,
        dependency_manifests=dependency_manifests,
        batch_run_summaries=batch_run_summaries,
        candidate_sequence=_RC0010_RC0020_SEQUENCE,
        final_candidate_version_id=STEP11_SUCCESSOR_CANDIDATE_VERSION_ID,
        lineage_schema=RC_CORRECTION_RERUN_LINEAGE_SCHEMA,
        event_schema=RC_CORRECTION_RERUN_LINEAGE_EVENT_SCHEMA,
        require_immediate_final_dependency_base=True,
    )


def build_rc0010_rc0021_correction_rerun_lineage(
    events: Sequence[Mapping[str, Any]],
    *,
    dependency_manifests: Sequence[Mapping[str, Any]],
    batch_run_summaries: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Append rc0021 without accepting the failed rc0020 Product Read.

    rc0020 is bound to the exact frozen preflight manifest and batch summary.
    Its machine-clean result is retained, while a separate receipt-bound
    Product Read MAJOR event makes it acceptance-ineligible and requires a
    superseded disposition.  The rc0021 manifest must then be an immediate
    diff from that exact rc0020 closure.
    """

    _require_frozen_rc0021_historical_parents(
        dependency_manifests,
        batch_run_summaries,
    )
    return _build_rc_correction_rerun_lineage(
        events,
        dependency_manifests=dependency_manifests,
        batch_run_summaries=batch_run_summaries,
        candidate_sequence=_RC0010_RC0021_SEQUENCE,
        final_candidate_version_id=(
            STEP11_HISTORICAL_RC0021_CANDIDATE_VERSION_ID
        ),
        lineage_schema=RC_CORRECTION_RERUN_LINEAGE_V3_SCHEMA,
        event_schema=RC_CORRECTION_RERUN_LINEAGE_EVENT_V3_SCHEMA,
        require_immediate_final_dependency_base=True,
        required_failed_product_read_candidate_version_id=(
            STEP11_HISTORICAL_RC0020_CANDIDATE_VERSION_ID
        ),
    )


def build_rc0010_rc0022_correction_rerun_lineage(
    events: Sequence[Mapping[str, Any]],
    *,
    dependency_manifests: Sequence[Mapping[str, Any]],
    batch_run_summaries: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Append rc0022 after ordered rc0020 and rc0021 Product Read failures.

    Both predecessors remain machine-clean immutable preflight observations.
    rc0020 retains its original Product Read MAJOR boundary; rc0021 adds the
    exact case-0035 MAJOR observation before the immediate rc0022 diff.
    """

    _require_frozen_rc0022_historical_parents(
        dependency_manifests,
        batch_run_summaries,
    )
    return _build_rc_correction_rerun_lineage(
        events,
        dependency_manifests=dependency_manifests,
        batch_run_summaries=batch_run_summaries,
        candidate_sequence=_RC0010_RC0022_SEQUENCE,
        final_candidate_version_id=(
            STEP11_HISTORICAL_RC0022_CANDIDATE_VERSION_ID
        ),
        lineage_schema=RC_CORRECTION_RERUN_LINEAGE_V4_SCHEMA,
        event_schema=RC_CORRECTION_RERUN_LINEAGE_EVENT_V4_SCHEMA,
        require_immediate_final_dependency_base=True,
        required_failed_product_read_candidate_version_ids=(
            STEP11_HISTORICAL_RC0020_CANDIDATE_VERSION_ID,
            STEP11_HISTORICAL_RC0021_CANDIDATE_VERSION_ID,
        ),
        required_product_read_failure_case_ids={
            STEP11_HISTORICAL_RC0021_CANDIDATE_VERSION_ID: (
                "nls3s_b001_0035",
            )
        },
    )


def build_rc0010_rc0023_correction_rerun_lineage(
    events: Sequence[Mapping[str, Any]],
    *,
    dependency_manifests: Sequence[Mapping[str, Any]],
    batch_run_summaries: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Append rc0023 after the exact failed rc0022 formal execution.

    The rc0020 and rc0021 Product Read failures remain unchanged.  rc0022 is
    separately retained as a complete machine-failed execution, followed by
    a superseded-after-observed-result disposition and an immediate rc0023
    dependency diff.
    """

    _require_frozen_rc0023_historical_parents(
        dependency_manifests,
        batch_run_summaries,
    )
    return _build_rc_correction_rerun_lineage(
        events,
        dependency_manifests=dependency_manifests,
        batch_run_summaries=batch_run_summaries,
        candidate_sequence=_RC0010_RC0023_SEQUENCE,
        final_candidate_version_id=(
            STEP11_HISTORICAL_RC0023_CANDIDATE_VERSION_ID
        ),
        lineage_schema=RC_CORRECTION_RERUN_LINEAGE_V5_SCHEMA,
        event_schema=RC_CORRECTION_RERUN_LINEAGE_EVENT_V5_SCHEMA,
        require_immediate_final_dependency_base=True,
        required_failed_product_read_candidate_version_ids=(
            STEP11_HISTORICAL_RC0020_CANDIDATE_VERSION_ID,
            STEP11_HISTORICAL_RC0021_CANDIDATE_VERSION_ID,
        ),
        required_product_read_failure_case_ids={
            STEP11_HISTORICAL_RC0021_CANDIDATE_VERSION_ID: (
                "nls3s_b001_0035",
            )
        },
        required_failed_execution_candidate_version_ids=(
            STEP11_HISTORICAL_RC0022_CANDIDATE_VERSION_ID,
        ),
    )


def build_rc0010_rc0024_correction_rerun_lineage(
    events: Sequence[Mapping[str, Any]],
    *,
    dependency_manifests: Sequence[Mapping[str, Any]],
    batch_run_summaries: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Append rc0024 after the exact machine-clean rc0023 formal run.

    rc0023 remains a clean receipt-backed execution.  The later Known28 abort
    produced no durable regression receipt, so the append-only chain records
    only the source correction and superseding decision before the immediate
    rc0024 dependency diff; it never fabricates or relabels execution facts.
    """

    _require_frozen_rc0024_historical_parents(
        dependency_manifests,
        batch_run_summaries,
    )
    return _build_rc_correction_rerun_lineage(
        events,
        dependency_manifests=dependency_manifests,
        batch_run_summaries=batch_run_summaries,
        candidate_sequence=_RC0010_RC0024_SEQUENCE,
        final_candidate_version_id=STEP11_CURRENT_CANDIDATE_VERSION_ID,
        lineage_schema=RC_CORRECTION_RERUN_LINEAGE_V6_SCHEMA,
        event_schema=RC_CORRECTION_RERUN_LINEAGE_EVENT_V6_SCHEMA,
        require_immediate_final_dependency_base=True,
        required_failed_product_read_candidate_version_ids=(
            STEP11_HISTORICAL_RC0020_CANDIDATE_VERSION_ID,
            STEP11_HISTORICAL_RC0021_CANDIDATE_VERSION_ID,
        ),
        required_product_read_failure_case_ids={
            STEP11_HISTORICAL_RC0021_CANDIDATE_VERSION_ID: (
                "nls3s_b001_0035",
            )
        },
        required_failed_execution_candidate_version_ids=(
            STEP11_HISTORICAL_RC0022_CANDIDATE_VERSION_ID,
        ),
    )


def _rc_lineage_input_events(
    value: Mapping[str, Any],
    *,
    allow_product_read: bool = False,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for event in value.get("events", []):
        if type(event) is not dict:
            raise Step11CycleEvidenceError("RC_LINEAGE_EVENT_INVALID")
        event_type = event.get("event_type")
        if event_type == "initial_run_observed":
            keys = {
                "event_type",
                "candidate_version_id",
                "batch_summary_sha256",
            }
        elif event_type == "correction_recorded":
            keys = {
                "event_type",
                "candidate_version_id",
                "source_state_kind",
                "source_state_artifact_sha256",
                "failure_evidence_commitment",
                "structural_hypothesis_commitment",
                "changed_file_set_commitment",
                "negative_suite_commitment",
                "correction_decision_commitment",
            }
        elif event_type == "execution_observed":
            keys = {
                "event_type",
                "candidate_version_id",
                "execution_scope",
                "batch_summary_sha256",
            }
        elif event_type == "product_read_observed" and allow_product_read:
            keys = {
                "event_type",
                "candidate_version_id",
                "batch_summary_sha256",
                "review_outcome",
                "maximum_severity",
                "failure_axis_codes",
                "failure_reason_codes",
                "review_receipt_commitment",
            }
            if "failure_case_ids" in event:
                keys.add("failure_case_ids")
        elif event_type == "revision_disposition":
            keys = {
                "event_type",
                "candidate_version_id",
                "disposition",
                "decision_receipt_commitment",
            }
        else:
            raise Step11CycleEvidenceError("RC_LINEAGE_EVENT_TYPE_INVALID")
        try:
            events.append({key: event[key] for key in keys})
        except KeyError as exc:
            raise Step11CycleEvidenceError("RC_LINEAGE_EVENT_INVALID") from exc
    return events


def validate_rc0010_rc0019_correction_rerun_lineage(
    value: Any,
    *,
    dependency_manifests: Sequence[Mapping[str, Any]],
    batch_run_summaries: Sequence[Mapping[str, Any]],
) -> tuple[str, ...]:
    if type(value) is not dict:
        return ("RC_CORRECTION_RERUN_LINEAGE_MAPPING_REQUIRED",)
    try:
        expected = build_rc0010_rc0019_correction_rerun_lineage(
            _rc_lineage_input_events(value),
            dependency_manifests=dependency_manifests,
            batch_run_summaries=batch_run_summaries,
        )
    except (KeyError, TypeError, ValueError, Step11CycleEvidenceError):
        return ("RC_CORRECTION_RERUN_LINEAGE_CONTRACT_INVALID",)
    return () if value == expected else (
        "RC_CORRECTION_RERUN_LINEAGE_RECOMPUTATION_MISMATCH",
    )


def validate_rc0010_rc0020_correction_rerun_lineage(
    value: Any,
    *,
    dependency_manifests: Sequence[Mapping[str, Any]],
    batch_run_summaries: Sequence[Mapping[str, Any]],
) -> tuple[str, ...]:
    if type(value) is not dict:
        return ("RC_CORRECTION_RERUN_LINEAGE_MAPPING_REQUIRED",)
    try:
        expected = build_rc0010_rc0020_correction_rerun_lineage(
            _rc_lineage_input_events(value),
            dependency_manifests=dependency_manifests,
            batch_run_summaries=batch_run_summaries,
        )
    except (KeyError, TypeError, ValueError, Step11CycleEvidenceError):
        return ("RC_CORRECTION_RERUN_LINEAGE_CONTRACT_INVALID",)
    return () if value == expected else (
        "RC_CORRECTION_RERUN_LINEAGE_RECOMPUTATION_MISMATCH",
    )


def validate_rc0010_rc0021_correction_rerun_lineage(
    value: Any,
    *,
    dependency_manifests: Sequence[Mapping[str, Any]],
    batch_run_summaries: Sequence[Mapping[str, Any]],
) -> tuple[str, ...]:
    if type(value) is not dict:
        return ("RC_CORRECTION_RERUN_LINEAGE_MAPPING_REQUIRED",)
    try:
        expected = build_rc0010_rc0021_correction_rerun_lineage(
            _rc_lineage_input_events(value, allow_product_read=True),
            dependency_manifests=dependency_manifests,
            batch_run_summaries=batch_run_summaries,
        )
    except (KeyError, TypeError, ValueError, Step11CycleEvidenceError):
        return ("RC_CORRECTION_RERUN_LINEAGE_CONTRACT_INVALID",)
    return () if value == expected else (
        "RC_CORRECTION_RERUN_LINEAGE_RECOMPUTATION_MISMATCH",
    )


def validate_rc0010_rc0022_correction_rerun_lineage(
    value: Any,
    *,
    dependency_manifests: Sequence[Mapping[str, Any]],
    batch_run_summaries: Sequence[Mapping[str, Any]],
) -> tuple[str, ...]:
    if type(value) is not dict:
        return ("RC_CORRECTION_RERUN_LINEAGE_MAPPING_REQUIRED",)
    try:
        expected = build_rc0010_rc0022_correction_rerun_lineage(
            _rc_lineage_input_events(value, allow_product_read=True),
            dependency_manifests=dependency_manifests,
            batch_run_summaries=batch_run_summaries,
        )
    except (KeyError, TypeError, ValueError, Step11CycleEvidenceError):
        return ("RC_CORRECTION_RERUN_LINEAGE_CONTRACT_INVALID",)
    return () if value == expected else (
        "RC_CORRECTION_RERUN_LINEAGE_RECOMPUTATION_MISMATCH",
    )


def validate_rc0010_rc0023_correction_rerun_lineage(
    value: Any,
    *,
    dependency_manifests: Sequence[Mapping[str, Any]],
    batch_run_summaries: Sequence[Mapping[str, Any]],
) -> tuple[str, ...]:
    if type(value) is not dict:
        return ("RC_CORRECTION_RERUN_LINEAGE_MAPPING_REQUIRED",)
    try:
        expected = build_rc0010_rc0023_correction_rerun_lineage(
            _rc_lineage_input_events(value, allow_product_read=True),
            dependency_manifests=dependency_manifests,
            batch_run_summaries=batch_run_summaries,
        )
    except (KeyError, TypeError, ValueError, Step11CycleEvidenceError):
        return ("RC_CORRECTION_RERUN_LINEAGE_CONTRACT_INVALID",)
    return () if value == expected else (
        "RC_CORRECTION_RERUN_LINEAGE_RECOMPUTATION_MISMATCH",
    )


def validate_rc0010_rc0024_correction_rerun_lineage(
    value: Any,
    *,
    dependency_manifests: Sequence[Mapping[str, Any]],
    batch_run_summaries: Sequence[Mapping[str, Any]],
) -> tuple[str, ...]:
    if type(value) is not dict:
        return ("RC_CORRECTION_RERUN_LINEAGE_MAPPING_REQUIRED",)
    try:
        expected = build_rc0010_rc0024_correction_rerun_lineage(
            _rc_lineage_input_events(value, allow_product_read=True),
            dependency_manifests=dependency_manifests,
            batch_run_summaries=batch_run_summaries,
        )
    except (KeyError, TypeError, ValueError, Step11CycleEvidenceError):
        return ("RC_CORRECTION_RERUN_LINEAGE_CONTRACT_INVALID",)
    return () if value == expected else (
        "RC_CORRECTION_RERUN_LINEAGE_RECOMPUTATION_MISMATCH",
    )


def build_cycle001_acceptance(
    initial_lock: Mapping[str, Any],
    initial_batch_summary: Mapping[str, Any],
    corpus_validation: Mapping[str, Any],
    initial_review_set: Mapping[str, Any],
    final_batch_summary: Mapping[str, Any],
    final_review_set: Mapping[str, Any],
    private_verification_receipt: Mapping[str, Any],
    known28_receipt: Mapping[str, Any],
    invalid16_receipt: Mapping[str, Any],
    output_diff: Mapping[str, Any],
    output_change_review: Mapping[str, Any],
    cumulative100_receipt: Mapping[str, Any],
    change_ledger: Mapping[str, Any],
    *,
    manifest: Mapping[str, Any],
    coverage_matrix: Mapping[str, Any],
    duplicate_report: Mapping[str, Any],
    development42_receipt: Mapping[str, Any],
    available_input_scope_receipt: Mapping[str, Any],
    correction_rerun_lineage: Mapping[str, Any],
    lineage_dependency_manifests: Sequence[Mapping[str, Any]],
    lineage_batch_run_summaries: Sequence[Mapping[str, Any]],
    final_dependency_manifest: Mapping[str, Any] | None,
    workaround_scan_receipt: Mapping[str, Any] | None,
) -> dict[str, Any]:
    expected_corpus = build_cycle001_corpus_validation(
        manifest, coverage_matrix, duplicate_report
    )
    if corpus_validation != expected_corpus:
        raise Step11CycleEvidenceError("CYCLE_CORPUS_PARENT_INVALID")
    lock = _validated_initial_lock(
        initial_lock,
        batch_summary=initial_batch_summary,
        corpus_validation=corpus_validation,
    )
    initial = _validated_review_set(
        initial_review_set,
        initial_lock=lock,
        initial_batch_summary=initial_batch_summary,
        corpus_validation=corpus_validation,
        batch_summary=initial_batch_summary,
        expected_stage="initial",
    )
    final = _validated_review_set(
        final_review_set,
        initial_lock=lock,
        initial_batch_summary=initial_batch_summary,
        corpus_validation=corpus_validation,
        batch_summary=final_batch_summary,
        expected_stage="final",
        dependency_manifest=final_dependency_manifest,
    )
    expected_diff = build_output_diff(
        lock,
        initial_batch_summary,
        corpus_validation,
        final_batch_summary,
        final_dependency_manifest=final_dependency_manifest,
    )
    if output_diff != expected_diff:
        raise Step11CycleEvidenceError("CYCLE_OUTPUT_DIFF_INVALID")
    expected_output_review = build_output_change_review(
        lock,
        initial_batch_summary,
        corpus_validation,
        initial,
        final_batch_summary,
        final,
        expected_diff,
        final_dependency_manifest=final_dependency_manifest,
    )
    if output_change_review != expected_output_review:
        raise Step11CycleEvidenceError("CYCLE_OUTPUT_REVIEW_INVALID")
    expected_cumulative = build_cumulative100_receipt(
        lock,
        initial_batch_summary,
        corpus_validation,
        initial,
        final_batch_summary,
        final,
        private_verification_receipt,
        known28_receipt,
        invalid16_receipt,
        expected_diff,
        expected_output_review,
        development42_receipt=development42_receipt,
        available_input_scope_receipt=available_input_scope_receipt,
        correction_rerun_lineage=correction_rerun_lineage,
        lineage_dependency_manifests=lineage_dependency_manifests,
        lineage_batch_run_summaries=lineage_batch_run_summaries,
        final_dependency_manifest=final_dependency_manifest,
        cumulative_run_id=cumulative100_receipt.get("cumulative_run_id"),
    )
    if cumulative100_receipt != expected_cumulative:
        raise Step11CycleEvidenceError("CYCLE_CUMULATIVE_INVALID")
    expected_ledger = build_cycle_change_ledger(
        lock,
        initial_batch_summary,
        corpus_validation,
        initial,
        final_batch_summary,
        expected_cumulative,
        [
            {
                "failure_case_commitments": row["failure_case_commitments"],
                "failure_layer": row["failure_layer"],
                "severity": row["severity"],
                "failure_codes": row["failure_codes"],
                "shared_structural_hypothesis": row[
                    "shared_structural_hypothesis"
                ],
                "shared_structural_hypothesis_commitment": row[
                    "shared_structural_hypothesis_commitment"
                ],
                "correction_owner_paths": row["correction_owner_paths"],
                "regression_risk_codes": row["regression_risk_codes"],
                "negative_test_ids": row["negative_test_ids"],
            }
            for row in change_ledger.get("rows", [])
        ],
        final_dependency_manifest=final_dependency_manifest,
        workaround_scan_receipt=workaround_scan_receipt,
    )
    if change_ledger != expected_ledger:
        raise Step11CycleEvidenceError("CYCLE_CHANGE_LEDGER_INVALID")
    known = _clean_known28(
        known28_receipt,
        final_batch_summary=final_batch_summary,
        final_dependency_manifest=final_dependency_manifest,
    )
    development = _clean_development42(
        development42_receipt,
        final_batch_summary=final_batch_summary,
        final_dependency_manifest=final_dependency_manifest,
    )
    available_scope = _clean_available_input_scope(
        available_input_scope_receipt
    )
    correction_lineage = _clean_correction_rerun_lineage(
        correction_rerun_lineage,
        dependency_manifests=lineage_dependency_manifests,
        batch_run_summaries=lineage_batch_run_summaries,
    )
    invalid = _clean_invalid16(
        invalid16_receipt,
        final_batch_summary=final_batch_summary,
        final_dependency_manifest=final_dependency_manifest,
    )
    final_projection = _project_final(
        final_batch_summary, final_dependency_manifest
    )
    lineage_final_binding = _require_lineage_final_parent_binding(
        correction_lineage,
        final_batch_summary=final_batch_summary,
        final_dependency_manifest=final_dependency_manifest,
    )
    auxiliary_conditions = _auxiliary_acceptance_conditions(
        final_run_id=final_projection["run_id"],
        known=known,
        development=development,
        available_scope=available_scope,
        invalid=invalid,
        correction_lineage=correction_lineage,
        lineage_final_binding=lineage_final_binding,
    )
    surface_distribution = final_batch_summary.get(
        "surface_distribution_assessment"
    )
    aggregate = expected_cumulative["aggregate"]
    if (
        type(surface_distribution) is not dict
        or surface_distribution.get("schema_version")
        != _surface_distribution_schema_for_candidate(
            final_projection["candidate_version_id"]
        )
        or surface_distribution.get("status") != "evaluated"
        or surface_distribution.get("acceptance_passed") is not True
        or surface_distribution.get("frozen_acceptance_policy_sha256")
        != FROZEN_STEP11_SURFACE_DISTRIBUTION_POLICY_SHA256
        or surface_distribution.get("global_evaluated_dimension_count") != 3
        or surface_distribution.get("global_failed_dimension_count") != 0
        or surface_distribution.get("semantic_failed_family_count") != 0
        or surface_distribution.get("semantic_family_coverage_complete")
        is not True
        or surface_distribution.get("global_policy_passed") is not True
        or surface_distribution.get("semantic_family_policy_passed") is not True
        or surface_distribution.get("exact_output_evaluated_case_count") != 100
        or surface_distribution.get("exact_output_coverage_complete") is not True
        or surface_distribution.get("exact_output_duplicate_case_count") != 0
        or final_batch_summary.get("aggregate", {}).get(
            "output_duplicate_case_count"
        )
        != 0
        or aggregate["executed_case_count"] != 100
        or aggregate["selected_count"] != 100
        or aggregate["exception_count"] != 0
        or aggregate["no_valid_candidate_count"] != 0
        or aggregate["v1_fallback_count"] != 0
        or aggregate["private_verified_case_count"] != 100
        or aggregate["known28_pass_count"] != 28
        or aggregate["known28_selected_count"] != 19
        or aggregate["known28_expected_non_applicable_match_count"] != 9
        or aggregate["development42_pass_count"] != 42
        or aggregate["development42_selected_count"] != 24
        or aggregate[
            "development42_expected_non_applicable_match_count"
        ]
        != 18
        or aggregate["known_regression_registered_case_count"] != 70
        or aggregate["known_regression_pass_count"] != 70
        or aggregate["legacy_registered_case_count"] != 3
        or aggregate["legacy_app_reachable_to_execute_count"] != 0
        or aggregate["legacy_expected_non_applicable_count"] != 3
        or aggregate["available_real_user_current_valid_count"] != 0
        or aggregate["invalid16_expected_rejection_match_count"] != 16
        or aggregate["unresolved_blocker_major_count"] != 0
        or final["aggregate"]["reviewed_count"] != 100
        or expected_output_review["status"] != "complete"
        or known["aggregate"]["contract_pass_count"] != 28
        or known["aggregate"]["selected_count"] != 19
        or known["aggregate"]["expected_non_applicable_match_count"] != 9
        or known["aggregate"]["failure_case_count"] != 0
        or development["aggregate"]["pass_count"] != 42
        or development["aggregate"]["selected_count"] != 24
        or development["aggregate"]["expected_non_applicable_match_count"]
        != 18
        or available_scope["scope_aggregate"][
            "known_machine_execution_case_count"
        ]
        != 70
        or invalid["aggregate"]["under_rejected_count"] != 0
        or not all(auxiliary_conditions.values())
    ):
        raise Step11CycleEvidenceError("CYCLE_ACCEPTANCE_CONDITION_FAILED")
    corrected = expected_ledger["mode"] == "corrected"
    lifecycle = ["DRAFT", "VALIDATED", "INITIAL_RUN_LOCKED", "REVIEWED"]
    if corrected:
        lifecycle.extend(["CORRECTION_IN_PROGRESS", "CUMULATIVE_RERUN_COMPLETE"])
    else:
        lifecycle.append("ACCEPTED_WITHOUT_SOURCE_CHANGE")
    lifecycle.append("ACCEPTED")
    value = {
        "schema_version": CYCLE_ACCEPTANCE_SCHEMA,
        "cycle_id": STEP11_CYCLE_ID,
        "batch_id": STEP11_BATCH_ID,
        "state": "ACCEPTED",
        "candidate_version_id": expected_cumulative["candidate_version_id"],
        "lifecycle": lifecycle,
        "corpus_validation_sha256": artifact_sha256(expected_corpus),
        "initial_lock_sha256": artifact_sha256(lock),
        "initial_review_set_sha256": artifact_sha256(initial),
        "final_review_set_sha256": artifact_sha256(final),
        "private_verification_receipt_sha256": artifact_sha256(
            private_verification_receipt
        ),
        "known28_receipt_sha256": artifact_sha256(known),
        "development42_receipt_sha256": artifact_sha256(development),
        "available_input_scope_receipt_sha256": artifact_sha256(
            available_scope
        ),
        "correction_rerun_lineage_sha256": artifact_sha256(
            correction_lineage
        ),
        "lineage_final_parent_binding": lineage_final_binding,
        "invalid16_receipt_sha256": artifact_sha256(invalid),
        "output_diff_sha256": artifact_sha256(expected_diff),
        "output_change_review_sha256": artifact_sha256(expected_output_review),
        "cumulative100_receipt_sha256": artifact_sha256(expected_cumulative),
        "change_ledger_sha256": artifact_sha256(expected_ledger),
        "acceptance_conditions": {
            "valid_sample_count_100": expected_corpus["valid_case_count"] == 100,
            "app_reachable_100_of_100": (
                expected_corpus["app_reachable_count"] == 100
            ),
            "exact_duplicate_count_0": (
                expected_corpus["exact_duplicate_count"] == 0
            ),
            "manifest_and_initial_result_locked": True,
            "cumulative_exception_count_0": aggregate["exception_count"] == 0,
            "cumulative_no_valid_candidate_count_0": (
                aggregate["no_valid_candidate_count"] == 0
            ),
            "cumulative_v1_fallback_count_0": aggregate["v1_fallback_count"] == 0,
            "private_evidence_100_verified": (
                aggregate["private_verified_case_count"] == 100
            ),
            "known28_all_passed": aggregate["known28_pass_count"] == 28,
            "known28_app_reachable_selected_19": (
                aggregate["known28_selected_count"] == 19
            ),
            "known28_expected_non_applicable_matched_9": (
                aggregate["known28_expected_non_applicable_match_count"] == 9
            ),
            "invalid16_all_rejected_as_expected": (
                aggregate["invalid16_expected_rejection_match_count"] == 16
            ),
            "surface_distribution_full100_passed": (
                surface_distribution["acceptance_passed"] is True
            ),
            "surface_distribution_global_3_dimensions_passed": (
                surface_distribution["global_evaluated_dimension_count"] == 3
                and surface_distribution["global_failed_dimension_count"] == 0
            ),
            "surface_distribution_all_non_singleton_families_passed": (
                surface_distribution["semantic_failed_family_count"] == 0
                and surface_distribution["semantic_family_policy_passed"]
                is True
                and surface_distribution["semantic_family_coverage_complete"]
                is True
            ),
            "surface_distribution_exact_output_duplicate_count_0": (
                surface_distribution["exact_output_duplicate_case_count"] == 0
                and surface_distribution["exact_output_coverage_complete"]
                is True
            ),
            "unresolved_blocker_count_0": (
                final["aggregate"]["severity_counts"].get("BLOCKER", 0) == 0
            ),
            "unresolved_major_count_0": (
                final["aggregate"]["severity_counts"].get("MAJOR", 0) == 0
            ),
            "case_specific_workaround_count_0": (
                not corrected
                or workaround_scan_receipt.get("finding_count") == 0
            ),
            "output_change_review_complete": True,
            "change_ledger_recomputable": True,
            **auxiliary_conditions,
        },
        "execution_run_ids": {
            "final_batch": final_projection["run_id"],
            "known28": known["run_id"],
            "development42": development["run_id"],
            "invalid16": invalid["run_id"],
        },
        "counts_toward_karen_minimum": 100,
        "next_authority": "step11_cycle002_only",
        "append_only": True,
        "body_free": True,
    }
    if not all(value["acceptance_conditions"].values()):
        raise Step11CycleEvidenceError("CYCLE_ACCEPTANCE_BOOLEAN_FALSE")
    _require_body_free(value)
    return value


def validate_cycle001_acceptance(
    value: Any,
    **parents: Any,
) -> tuple[str, ...]:
    try:
        expected = build_cycle001_acceptance(**parents)
    except (KeyError, TypeError, ValueError, Step11CycleEvidenceError):
        return ("CYCLE001_ACCEPTANCE_PARENT_OR_CONTRACT_INVALID",)
    return () if value == expected else ("CYCLE001_ACCEPTANCE_RECOMPUTATION_MISMATCH",)


__all__ = [
    "AVAILABLE_INPUT_SCOPE_RECEIPT_SCHEMA",
    "CORPUS_VALIDATION_SCHEMA",
    "CUMULATIVE100_RECEIPT_SCHEMA",
    "CYCLE_ACCEPTANCE_SCHEMA",
    "CYCLE_CHANGE_LEDGER_SCHEMA",
    "CYCLE_CHANGE_ROW_SCHEMA",
    "DEVELOPMENT42_RECEIPT_SCHEMA",
    "FROZEN_AVAILABLE_INPUT_SCOPE_RECEIPT_SHA256",
    "FROZEN_RC0019_AVAILABLE_INPUT_SCOPE_RECEIPT_SHA256",
    "FROZEN_RC0020_PREFLIGHT_BATCH_SUMMARY_SHA256",
    "FROZEN_RC0020_PREFLIGHT_MANIFEST_ARTIFACT_SHA256",
    "FROZEN_RC0020_PREFLIGHT_PRIVATE_VERIFICATION_SHA256",
    "FROZEN_RC0020_PREFLIGHT_SOURCE_CLOSURE_SHA256",
    "FROZEN_RC0021_PREFLIGHT_BATCH_SUMMARY_SHA256",
    "FROZEN_RC0021_PREFLIGHT_MANIFEST_ARTIFACT_SHA256",
    "FROZEN_RC0021_PREFLIGHT_PRIVATE_VERIFICATION_SHA256",
    "FROZEN_RC0021_PREFLIGHT_SOURCE_CLOSURE_SHA256",
    "FROZEN_RC0022_FORMAL_BATCH_SUMMARY_SHA256",
    "FROZEN_RC0022_FORMAL_MANIFEST_ARTIFACT_SHA256",
    "FROZEN_RC0022_FORMAL_PRIVATE_VERIFICATION_SHA256",
    "FROZEN_RC0022_FORMAL_SOURCE_CLOSURE_SHA256",
    "FROZEN_RC0023_FORMAL_BATCH_SUMMARY_SHA256",
    "FROZEN_RC0023_FORMAL_MANIFEST_ARTIFACT_SHA256",
    "FROZEN_RC0023_FORMAL_PRIVATE_VERIFICATION_SHA256",
    "FROZEN_RC0023_FORMAL_SOURCE_CLOSURE_SHA256",
    "FROZEN_BATCH001_DUPLICATE_REPORT_SHA256",
    "FROZEN_BATCH001_MANIFEST_SHA256",
    "FROZEN_BATCH001_MATRIX_SHA256",
    "FROZEN_INVALID16_FILE_SHA256",
    "FROZEN_INVALID16_INVENTORY_SHA256",
    "INVALID16_EXPECTED_INVENTORY",
    "FROZEN_KNOWN28_EXPECTED_APPLICABILITY_SHA256",
    "FROZEN_KNOWN28_GENERIC_PROJECTION_POLICY_SHA256",
    "FROZEN_KNOWN28_INVENTORY_SHA256",
    "FROZEN_STEP11_SURFACE_DISTRIBUTION_POLICY_SHA256",
    "INITIAL_RUN_LOCK_SCHEMA",
    "INVALID16_RECEIPT_SCHEMA",
    "KNOWN28_EXPECTED_APPLICABILITY",
    "KNOWN28_EXPECTED_APPLICABILITY_SHA256",
    "KNOWN28_GENERIC_PROJECTION_POLICY",
    "KNOWN28_GENERIC_PROJECTION_POLICY_SHA256",
    "KNOWN28_RECEIPT_SCHEMA",
    "LOCAL_REVIEW_SET_SCHEMA",
    "OUTPUT_CHANGE_REVIEW_SCHEMA",
    "OUTPUT_DIFF_SCHEMA",
    "RC_CORRECTION_RERUN_LINEAGE_EVENT_SCHEMA",
    "RC_CORRECTION_RERUN_LINEAGE_EVENT_V3_SCHEMA",
    "RC_CORRECTION_RERUN_LINEAGE_EVENT_V4_SCHEMA",
    "RC_CORRECTION_RERUN_LINEAGE_EVENT_V5_SCHEMA",
    "RC_CORRECTION_RERUN_LINEAGE_EVENT_V6_SCHEMA",
    "RC_CORRECTION_RERUN_LINEAGE_EVENT_V1_SCHEMA",
    "RC_CORRECTION_RERUN_LINEAGE_SCHEMA",
    "RC_CORRECTION_RERUN_LINEAGE_V3_SCHEMA",
    "RC_CORRECTION_RERUN_LINEAGE_V4_SCHEMA",
    "RC_CORRECTION_RERUN_LINEAGE_V5_SCHEMA",
    "RC_CORRECTION_RERUN_LINEAGE_V6_SCHEMA",
    "RC_CORRECTION_RERUN_LINEAGE_V1_SCHEMA",
    "STEP11_BATCH_ID",
    "STEP11_BATCH_RUN_SCHEMA",
    "STEP11_CASE_RECEIPT_SCHEMA",
    "STEP11_COMMITMENT_POLICY_SHA256",
    "STEP11_CYCLE_ID",
    "STEP11_DEPENDENCY_MANIFEST_SCHEMA",
    "STEP11_INITIAL_CANDIDATE_VERSION_ID",
    "STEP11_HISTORICAL_RC0019_CANDIDATE_VERSION_ID",
    "STEP11_HISTORICAL_RC0020_CANDIDATE_VERSION_ID",
    "STEP11_HISTORICAL_RC0021_CANDIDATE_VERSION_ID",
    "STEP11_HISTORICAL_RC0021_RUNTIME_ADAPTER_VERSION",
    "STEP11_HISTORICAL_RC0022_CANDIDATE_VERSION_ID",
    "STEP11_HISTORICAL_RC0022_RUNTIME_ADAPTER_VERSION",
    "STEP11_HISTORICAL_RC0023_CANDIDATE_VERSION_ID",
    "STEP11_HISTORICAL_RC0023_RUNTIME_ADAPTER_VERSION",
    "STEP11_PRIVATE_VERIFICATION_RECEIPT_SCHEMA",
    "STEP11_CURRENT_CANDIDATE_VERSION_ID",
    "STEP11_RC0021_AVAILABLE_INPUT_SCOPE_RECEIPT_SCHEMA",
    "STEP11_RC0021_SURFACE_DISTRIBUTION_ASSESSMENT_SCHEMA",
    "STEP11_RC0022_AVAILABLE_INPUT_SCOPE_RECEIPT_SCHEMA",
    "STEP11_RC0022_SURFACE_DISTRIBUTION_ASSESSMENT_SCHEMA",
    "STEP11_RC0023_AVAILABLE_INPUT_SCOPE_RECEIPT_SCHEMA",
    "STEP11_RC0023_SURFACE_DISTRIBUTION_ASSESSMENT_SCHEMA",
    "STEP11_RC0024_AVAILABLE_INPUT_SCOPE_RECEIPT_SCHEMA",
    "STEP11_RC0024_SURFACE_DISTRIBUTION_ASSESSMENT_SCHEMA",
    "STEP11_REVIEW_RUBRIC_SHA256",
    "STEP11_SURFACE_DISTRIBUTION_ASSESSMENT_SCHEMA",
    "STEP11_SURFACE_DISTRIBUTION_POLICY",
    "STEP11_SURFACE_DISTRIBUTION_POLICY_SHA256",
    "STEP11_RUNTIME_VALIDATION_PROTOCOL_SHA256",
    "STEP11_SUCCESSOR_CANDIDATE_VERSION_ID",
    "Step11CycleEvidenceError",
    "WORKAROUND_SCAN_SCHEMA",
    "build_case_specific_workaround_scan_receipt",
    "build_cumulative100_receipt",
    "build_cycle001_acceptance",
    "build_cycle001_corpus_validation",
    "build_cycle_change_ledger",
    "build_initial_run_lock",
    "build_invalid16_receipt",
    "build_known28_receipt",
    "build_local_review_set",
    "build_output_change_review",
    "build_output_diff",
    "build_rc0010_rc0019_correction_rerun_lineage",
    "build_rc0010_rc0020_correction_rerun_lineage",
    "build_rc0010_rc0021_correction_rerun_lineage",
    "build_rc0010_rc0022_correction_rerun_lineage",
    "build_rc0010_rc0023_correction_rerun_lineage",
    "build_rc0010_rc0024_correction_rerun_lineage",
    "build_step11_batch_run_summary",
    "build_step11_private_verification_receipt",
    "build_step11_dependency_manifest",
    "validate_case_specific_workaround_scan_receipt",
    "validate_cumulative100_receipt",
    "validate_cycle001_acceptance",
    "validate_cycle001_corpus_validation",
    "validate_cycle_change_ledger",
    "validate_initial_run_lock",
    "validate_invalid16_receipt",
    "validate_invalid16_inventory_contract",
    "validate_known28_applicability_contract",
    "validate_known28_receipt",
    "validate_local_review_set",
    "validate_output_change_review",
    "validate_output_diff",
    "validate_rc0010_rc0019_correction_rerun_lineage",
    "validate_rc0010_rc0020_correction_rerun_lineage",
    "validate_rc0010_rc0021_correction_rerun_lineage",
    "validate_rc0010_rc0022_correction_rerun_lineage",
    "validate_rc0010_rc0023_correction_rerun_lineage",
    "validate_rc0010_rc0024_correction_rerun_lineage",
    "validate_step11_batch_run_summary",
    "validate_step11_dependency_manifest",
    "validate_step11_private_verification_receipt",
]
