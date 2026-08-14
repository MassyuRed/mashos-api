from __future__ import annotations

import copy
import ast
from dataclasses import replace
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

import pytest


_AI_ROOT = Path(__file__).resolve().parents[1]
_TOOLS = _AI_ROOT / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import emlis_nls_v3_step11_current_rc_g8_run as runner  # noqa: E402


_KEY = b"k" * 32
_RUN_ID = "g8-evidence-v4-focused"


def _source_snapshot(marker: str = "a") -> dict[str, object]:
    files = [{"path": "ai/tools/focused_source.py", "sha256": marker * 64}]
    return {
        "source_closure_sha256": runner._closure_digest(files),
        "source_closure_file_count": 1,
        "source_closure_files": files,
    }


def _selected_row(index: int) -> dict[str, object]:
    case_id = f"nls3s_b001_{index:04d}"
    return {
        "case_id": case_id,
        "source_case_commitment": f"{index:064x}",
        "source_input": {
            "thought_text": f"private thought {index}",
            "action_text": "",
            "emotions": [{"type": "平穏", "strength": "medium"}],
            "categories": ["生活"],
        },
        "disposition": "selected",
        "candidate_version_id": runner._RECOVERY_CANDIDATE_VERSION,
        "candidate_schema_version": runner._RECOVERY_CANDIDATE_SCHEMA,
        "current_candidate_id": f"current-{index}",
        "candidate_output_utf8": f"private output {index}",
        "machine_checks": {key: True for key in runner._CHECK_KEYS},
        "failure_code": None,
        "exception_captured": False,
    }


def _rows() -> list[dict[str, object]]:
    return [_selected_row(index) for index in range(1, 101)]


def _case_sources() -> tuple[tuple[str, str, bytes], ...]:
    return tuple(
        (
            str(row["case_id"]),
            str(row["source_case_commitment"]),
            runner._canonical_json_bytes(row["source_input"]),
        )
        for row in _rows()
    )


@lru_cache(maxsize=1)
def _real_recovery_structural_case() -> tuple[object, object]:
    from emlis_ai_step10_app_reachable_contract_v3 import (
        project_app_reachable_input,
    )
    from emlis_ai_step11_cycle001_product_recovery_v3 import (
        build_step11_cycle001_product_recovery_candidate,
    )

    samples, _manifest, _commitments = runner._exact100_sources(
        runner._BATCH_PATH, runner._MANIFEST_PATH
    )
    for sample in samples:
        context = runner._build_direct_recovery_context(
            project_app_reachable_input(sample["input"])
        )
        candidate = build_step11_cycle001_product_recovery_candidate(
            plan=context.grounded_plan,
            resolver=context.resolver,
            successor_snapshot=context.successor_snapshot,
            lexical_atom_specs=context.lexical_atom_specs,
            inventory_result=context.inventory_result,
            content_plan=context.content_plan,
            discourse_plans=context.discourse_plans,
            current_input=context.projected_current_input,
        )
        envelope_families = {
            row.semantic_family
            for row in candidate.source_envelope.atom_bindings
        }
        if (
            candidate.construction_atoms
            and candidate.semantic_link_atoms
            and {"construction", "semantic_link"} <= envelope_families
        ):
            return context, candidate
    raise AssertionError("CURRENT_RC_G8_STRUCTURAL_FIXTURE_UNRESOLVED")


def _mutate_visible_line(
    candidate: object,
    context: object,
    *,
    section: str,
    line_index: int,
) -> bytes:
    expected = runner._direct_expected_recovery(context)
    grammar = expected.grammar
    catalog = expected.catalog
    text = candidate.rendered_surface.utf8_bytes.decode("utf-8")
    header = str(grammar["observation_header"])
    separator = str(grammar["section_separator"])
    suffix = str(catalog["clause_morphology"]["sentence_suffix"])
    observation, reception = text[len(header) :].split(separator, 1)
    rows = observation.split("\n") if section == "observation" else reception.split("\n")
    assert rows[line_index].endswith(suffix)
    rows[line_index] = rows[line_index][: -len(suffix)] + "改" + suffix
    if section == "observation":
        observation = "\n".join(rows)
    else:
        reception = "\n".join(rows)
    return (header + observation + separator + reception).encode("utf-8")


def _coordinated_rehash(
    candidate: object,
    context: object,
    *,
    owner_bindings: tuple[object, ...] | None = None,
    root_bindings: tuple[object, ...] | None = None,
    atom_bindings: tuple[object, ...] | None = None,
    reception_bindings: tuple[object, ...] | None = None,
    construction_atoms: tuple[object, ...] | None = None,
    relation_atoms: tuple[object, ...] | None = None,
    semantic_link_atoms: tuple[object, ...] | None = None,
    explicit_unknown_atoms: tuple[object, ...] | None = None,
    plan_units: tuple[object, ...] | None = None,
    body_section: str,
    body_line_index: int,
) -> object:
    from emlis_ai_nls_v3_artifact_contract import artifact_sha256
    from emlis_ai_step11_cycle001_product_recovery_v3 import (
        _plan_material,
        _typed_payload_material,
        step11_cycle001_product_recovery_source_envelope_material,
    )

    constructions = construction_atoms or tuple(candidate.construction_atoms)
    relations = relation_atoms or tuple(candidate.relation_atoms)
    links = semantic_link_atoms or tuple(candidate.semantic_link_atoms)
    unknowns = explicit_unknown_atoms or tuple(candidate.explicit_unknown_atoms)
    receptions = reception_bindings or tuple(candidate.reception_bindings)
    typed_sha256 = artifact_sha256(
        _typed_payload_material(
            owner_registry=candidate.owner_registry,
            constructions=constructions,
            relations=relations,
            links=links,
            unknowns=unknowns,
            receptions=receptions,
        )
    )
    provisional_source = replace(
        candidate.source_envelope,
        source_candidate_id="nls3s11rc0036source_0000000000000000",
        source_envelope_sha256="0" * 64,
        duplicated_typed_payload_sha256=typed_sha256,
        owner_bindings=(
            owner_bindings
            if owner_bindings is not None
            else tuple(candidate.source_envelope.owner_bindings)
        ),
        root_bindings=(
            root_bindings
            if root_bindings is not None
            else tuple(candidate.source_envelope.root_bindings)
        ),
        atom_bindings=(
            atom_bindings
            if atom_bindings is not None
            else tuple(candidate.source_envelope.atom_bindings)
        ),
        reception_bindings=receptions,
    )
    source_sha256 = artifact_sha256(
        step11_cycle001_product_recovery_source_envelope_material(
            provisional_source, include_id=False
        )
    )
    source = replace(
        provisional_source,
        source_candidate_id="nls3s11rc0036source_" + source_sha256[:16],
        source_envelope_sha256=source_sha256,
    )
    provisional_plan = replace(
        candidate.realization_plan,
        source_envelope_sha256=source_sha256,
        duplicated_typed_payload_sha256=typed_sha256,
        realization_plan_id="nls3s11rc0036plan_0000000000000000",
        ast_id="nls3s11rc0036ast_0000000000000000",
        units=(
            plan_units
            if plan_units is not None
            else tuple(candidate.realization_plan.units)
        ),
    )
    plan_sha256 = artifact_sha256(
        _plan_material(provisional_plan, include_identity=False)
    )
    plan = replace(
        provisional_plan,
        realization_plan_id="nls3s11rc0036plan_" + plan_sha256[:16],
        ast_id="nls3s11rc0036ast_" + plan_sha256[16:32],
    )
    body = _mutate_visible_line(
        candidate,
        context,
        section=body_section,
        line_index=body_line_index,
    )
    rendered = replace(
        candidate.rendered_surface,
        source_envelope_sha256=source_sha256,
        source_realization_plan_id=plan.realization_plan_id,
        utf8_bytes=body,
        sha256=hashlib.sha256(body).hexdigest(),
    )
    return replace(
        candidate,
        candidate_id="nls3s11rc0036cand_" + rendered.sha256[:16],
        source_envelope=source,
        realization_plan=plan,
        rendered_surface=rendered,
        construction_atoms=constructions,
        relation_atoms=relations,
        semantic_link_atoms=links,
        explicit_unknown_atoms=unknowns,
        reception_bindings=receptions,
    )


def _payloads(
    rows: list[dict[str, object]] | None = None,
    *,
    source: dict[str, object] | None = None,
) -> tuple[bytes, bytes, dict[str, object], dict[str, object], dict[str, object]]:
    snapshot = source or _source_snapshot()
    private_payload, public_payload, public = runner._result_payloads(
        rows or _rows(),
        key=_KEY,
        run_id=_RUN_ID,
        source_snapshot=snapshot,
        expected_case_sources=_case_sources(),
    )
    private = json.loads(private_payload)
    return private_payload, public_payload, private, public, snapshot


def test_01_cli_help_exposes_exact100_v4_private_pair() -> None:
    help_text = runner._parser().format_help()
    assert "exact-100" in help_text
    assert "--workers" in help_text
    assert "--commitment-key-file" in help_text
    assert "--output-dir" in help_text


def test_02_frozen_batch_preflight_is_exact_ordered_100() -> None:
    samples, manifest, commitments = runner._exact100_sources(
        runner._BATCH_PATH, runner._MANIFEST_PATH
    )
    expected_ids = tuple(
        f"nls3s_b001_{index:04d}" for index in range(1, 101)
    )
    assert tuple(row["case_id"] for row in samples) == expected_ids
    assert tuple(manifest["case_ids"]) == expected_ids
    assert tuple(commitments) == expected_ids


def test_03_v4_pair_is_canonical_body_free_and_hmac_bound() -> None:
    private_payload, public_payload, private, public, source = _payloads()
    assert runner._canonical_json_bytes(private) == private_payload
    assert runner._canonical_json_bytes(public) == public_payload
    assert public["schema_version"] == runner._BODY_FREE_SCHEMA
    assert private["schema_version"] == runner._PRIVATE_SCHEMA
    assert private["candidate_version_id"] == (
        runner._RECOVERY_CANDIDATE_VERSION
    )
    assert public["candidate_schema_version"] == (
        runner._RECOVERY_CANDIDATE_SCHEMA
    )
    assert public["source_closure_sha256"] == source["source_closure_sha256"]
    assert public["disposition_counts"] == {
        "fail_close": 0,
        "no_valid_candidate": 0,
        "selected": 100,
    }
    assert public["exception_count"] == 0
    assert len(public["cases"]) == 100
    assert set(public["cases"][0]) == {
        "ordinal",
        "case_id",
        "source_case_commitment",
        "disposition",
        "candidate_version_id",
        "candidate_schema_version",
        "candidate_present",
        "output_present",
        "exception_present",
        "failure_reason_code",
        "machine_checks",
        "case_hmac",
    }
    assert public["cases"][0]["case_hmac"] == runner._case_commitment(
        _KEY,
        _RUN_ID,
        str(source["source_closure_sha256"]),
        1,
        _rows()[0],
    )
    assert private["pair_integrity"] == public["pair_integrity"]
    assert set(public["pair_integrity"]) == {
        "body_free_core_sha256",
        "run_hmac",
    }
    assert "private_core_sha256" not in public_payload.decode("utf-8")
    assert "private thought" in private_payload.decode("utf-8")
    assert "private output" in private_payload.decode("utf-8")
    assert "private thought" not in public_payload.decode("utf-8")
    assert "private output" not in public_payload.decode("utf-8")
    runner._validate_pair(
        private,
        public,
        key=_KEY,
        expected_source=source,
        expected_case_sources=_case_sources(),
    )

    wrong_input = _rows()
    wrong_input[0]["source_input"] = dict(wrong_input[1]["source_input"])
    wrong_commitment = _rows()
    wrong_commitment[0]["source_case_commitment"] = "f" * 64
    for invalid in (wrong_input, wrong_commitment):
        with pytest.raises(runner.CurrentRcG8RunError) as source_binding:
            runner._result_payloads(
                invalid,
                key=_KEY,
                run_id=_RUN_ID,
                source_snapshot=source,
                expected_case_sources=_case_sources(),
            )
        assert source_binding.value.code == (
            "CURRENT_RC_G8_CASE_SOURCE_BINDING_INVALID"
        )


def test_04_selected_state_rejects_missing_output_or_failed_check() -> None:
    rows = _rows()
    rows[0]["candidate_output_utf8"] = None
    with pytest.raises(runner.CurrentRcG8RunError) as captured:
        runner._result_payloads(
            rows,
            key=_KEY,
            run_id=_RUN_ID,
            source_snapshot=_source_snapshot(),
            expected_case_sources=_case_sources(),
        )
    assert captured.value.code == "CURRENT_RC_G8_PRIVATE_STATE_INVALID"


def test_05_no_valid_state_rejects_candidate_or_private_output() -> None:
    rows = _rows()
    row = rows[0]
    row["disposition"] = "no_valid_candidate"
    row["failure_code"] = None
    row["machine_checks"] = {
        key: key in {"input_projected", "source_context_built"}
        for key in runner._CHECK_KEYS
    }
    with pytest.raises(runner.CurrentRcG8RunError) as captured:
        runner._result_payloads(
            rows,
            key=_KEY,
            run_id=_RUN_ID,
            source_snapshot=_source_snapshot(),
            expected_case_sources=_case_sources(),
        )
    assert captured.value.code == "CURRENT_RC_G8_PRIVATE_STATE_INVALID"


def test_06_fail_close_state_requires_failure_and_a_failed_check() -> None:
    rows = _rows()
    rows[0]["disposition"] = "fail_close"
    with pytest.raises(runner.CurrentRcG8RunError) as captured:
        runner._result_payloads(
            rows,
            key=_KEY,
            run_id=_RUN_ID,
            source_snapshot=_source_snapshot(),
            expected_case_sources=_case_sources(),
        )
    assert captured.value.code == "CURRENT_RC_G8_PRIVATE_STATE_INVALID"

    impossible_rows = []
    builder_without_candidate = _rows()
    row = builder_without_candidate[0]
    row["disposition"] = "fail_close"
    row["current_candidate_id"] = None
    row["candidate_output_utf8"] = None
    row["failure_code"] = "CURRENT_RC_G8_CASE_REJECTED"
    row["machine_checks"] = dict(row["machine_checks"])
    row["machine_checks"]["semantic_atoms_exact"] = False
    impossible_rows.append(builder_without_candidate)

    inverse_without_output = _rows()
    row = inverse_without_output[0]
    row["disposition"] = "fail_close"
    row["candidate_output_utf8"] = None
    row["failure_code"] = "CURRENT_RC_G8_INVERSE_REJECTED"
    row["machine_checks"] = dict(row["machine_checks"])
    row["machine_checks"]["semantic_atoms_exact"] = False
    impossible_rows.append(inverse_without_output)

    builder_without_input = _rows()
    row = builder_without_input[0]
    row["disposition"] = "fail_close"
    row["failure_code"] = "CURRENT_RC_G8_INVERSE_REJECTED"
    row["machine_checks"] = dict(row["machine_checks"])
    row["machine_checks"]["input_projected"] = False
    row["machine_checks"]["semantic_atoms_exact"] = False
    impossible_rows.append(builder_without_input)

    for invalid in impossible_rows:
        with pytest.raises(runner.CurrentRcG8RunError) as impossible:
            runner._result_payloads(
                invalid,
                key=_KEY,
                run_id=_RUN_ID,
                source_snapshot=_source_snapshot(),
                expected_case_sources=_case_sources(),
            )
        assert impossible.value.code == "CURRENT_RC_G8_PRIVATE_STATE_INVALID"


def test_07_unknown_private_failure_is_mapped_to_public_allowlist() -> None:
    rows = _rows()
    row = rows[0]
    row["disposition"] = "fail_close"
    row["current_candidate_id"] = None
    row["candidate_output_utf8"] = None
    row["failure_code"] = "PRIVATE_THOUGHT_SECRET"
    row["machine_checks"] = {
        key: key == "input_projected" for key in runner._CHECK_KEYS
    }
    row["exception_captured"] = True
    private_payload, public_payload, _private, public, _source = _payloads(rows)
    assert "PRIVATE_THOUGHT_SECRET" in private_payload.decode("utf-8")
    assert "PRIVATE_THOUGHT_SECRET" not in public_payload.decode("utf-8")
    assert (
        public["cases"][0]["failure_reason_code"]
        == "CURRENT_RC_G8_CASE_REJECTED"
    )
    assert public["cases"][0]["exception_present"] is True
    assert public["exception_count"] == 1


def test_08_private_row_mutation_is_rejected_by_case_hmac() -> None:
    _private_payload, _public_payload, private, public, source = _payloads()
    private["cases"][0]["result"]["candidate_output_utf8"] = "mutated"
    with pytest.raises(runner.CurrentRcG8RunError) as captured:
        runner._validate_pair(
            private,
            public,
            key=_KEY,
            expected_source=source,
            expected_case_sources=_case_sources(),
        )
    assert captured.value.code == "CURRENT_RC_G8_HMAC_VERIFICATION_FAILED"


def test_09_body_free_projection_mutation_is_rejected() -> None:
    _private_payload, _public_payload, private, public, source = _payloads()
    public["cases"][0]["output_present"] = False
    with pytest.raises(runner.CurrentRcG8RunError) as captured:
        runner._validate_pair(
            private,
            public,
            key=_KEY,
            expected_source=source,
            expected_case_sources=_case_sources(),
        )
    assert captured.value.code == "CURRENT_RC_G8_BODY_FREE_PROJECTION_INVALID"


def test_10_order_replay_or_duplicate_is_rejected() -> None:
    _private_payload, _public_payload, private, public, source = _payloads()
    private["cases"][0], private["cases"][1] = (
        private["cases"][1],
        private["cases"][0],
    )
    with pytest.raises(runner.CurrentRcG8RunError):
        runner._validate_pair(
            private,
            public,
            key=_KEY,
            expected_source=source,
            expected_case_sources=_case_sources(),
        )


def test_11_aggregate_and_run_hmac_mutations_are_rejected() -> None:
    _private_payload, _public_payload, private, public, source = _payloads()
    changed_counts = copy.deepcopy(public)
    changed_counts["disposition_counts"]["selected"] = 99
    changed_counts["disposition_counts"]["fail_close"] = 1
    with pytest.raises(runner.CurrentRcG8RunError) as aggregate:
        runner._validate_pair(
            private,
            changed_counts,
            key=_KEY,
            expected_source=source,
            expected_case_sources=_case_sources(),
        )
    assert aggregate.value.code == "CURRENT_RC_G8_ACCOUNTING_INVALID"
    changed_private = copy.deepcopy(private)
    changed_public = copy.deepcopy(public)
    changed_private["pair_integrity"]["run_hmac"] = "f" * 64
    changed_public["pair_integrity"]["run_hmac"] = "f" * 64
    with pytest.raises(runner.CurrentRcG8RunError) as run_hmac:
        runner._validate_pair(
            changed_private,
            changed_public,
            key=_KEY,
            expected_source=source,
            expected_case_sources=_case_sources(),
        )
    assert run_hmac.value.code == "CURRENT_RC_G8_HMAC_VERIFICATION_FAILED"


def test_12_source_closure_contains_product_runtime_fixture_schema_and_io() -> None:
    source = runner._source_closure_snapshot(
        runner._BATCH_PATH, runner._MANIFEST_PATH
    )
    paths = {row["path"] for row in source["source_closure_files"]}
    assert {
        "ai/services/ai_inference/emlis_ai_step11_natural_surface_v3.py",
        "ai/services/ai_inference/"
        "emlis_ai_step11_rc0030_experiment_surface_catalog_v3.py",
        "ai/services/ai_inference/"
        "emlis_ai_step11_cycle001_product_recovery_v3.py",
        "ai/tools/emlis_nls_v3_step11_current_rc_g8_run.py",
        "ai/tests/fixtures/emlis_nls_v3/generated/batch_001.jsonl",
        "ai/tests/fixtures/emlis_nls_v3/generated/batch_001_manifest.json",
        "ai/tests/fixtures/emlis_nls_v3/generated/batch_001_coverage_matrix.json",
        "ai/tests/fixtures/emlis_nls_v3/generated/batch_001_duplicate_report.json",
        "ai/tests/fixtures/emlis_nls_v3_s2_corpus_registry_20260714.json",
        "ai/tests/schemas/emlis_nls_v3_sample_case_v1.schema.json",
    } <= paths
    assert not any(
        "emlis_nls_v3_rc0029_surface_repair_bounded_experiment" in path
        for path in paths
    )
    assert not any("step11_runtime_adapter" in path for path in paths)
    forbidden_files = {
        "emlis_nls_v3_batch_run.py",
        "emlis_nls_v3_s2_sample_registry.py",
        "emlis_ai_dormant_runtime_adapter_v3.py",
        "emlis_ai_semantic_hard_gate_v3.py",
        "emlis_ai_lexicographic_selector_v3.py",
        "emlis_ai_step11_runtime_adapter_v3.py",
        "emlis_ai_step11_hard_gate_v3.py",
        "emlis_ai_step11_natural_surface_matcher_v3.py",
    }
    assert forbidden_files.isdisjoint({Path(path).name for path in paths})
    assert source["source_closure_file_count"] == len(paths)
    assert runner._validated_source_snapshot(source) == source


def test_13_prewrite_source_drift_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    snapshots = iter((_source_snapshot("a"), _source_snapshot("b")))
    monkeypatch.setattr(
        runner, "_source_closure_snapshot", lambda _batch, _manifest: next(snapshots)
    )
    monkeypatch.setattr(
        runner,
        "_exact100_sources",
        lambda _batch, _manifest: ([], {}, {}),
    )
    with pytest.raises(runner.CurrentRcG8RunError) as preflight:
        runner._bound_exact100_sources(
            runner._BATCH_PATH, runner._MANIFEST_PATH
        )
    assert preflight.value.code == "CURRENT_RC_G8_SOURCE_CHANGED_DURING_PREFLIGHT"

    source = _source_snapshot()
    private_payload, public_payload, _private, _public, _source = _payloads(
        source=source
    )
    output_dir = tmp_path / "drift"
    output_dir.mkdir(mode=0o700)
    os.chmod(output_dir, 0o700)
    monkeypatch.setattr(
        runner,
        "_source_closure_snapshot",
        lambda _batch, _manifest: _source_snapshot("b"),
    )
    with pytest.raises(runner.CurrentRcG8RunError) as captured:
        runner._write_outputs(
            output_dir,
            private_payload,
            public_payload,
            key=_KEY,
            source_snapshot=source,
            expected_case_sources=_case_sources(),
            batch_path=runner._BATCH_PATH,
            manifest_path=runner._MANIFEST_PATH,
        )
    assert captured.value.code == "CURRENT_RC_G8_SOURCE_CHANGED_BEFORE_WRITE"
    assert list(output_dir.iterdir()) == []

    during_write = tmp_path / "during-write-drift"
    during_write.mkdir(mode=0o700)
    os.chmod(during_write, 0o700)
    write_snapshots = iter((copy.deepcopy(source), _source_snapshot("b")))
    monkeypatch.setattr(
        runner,
        "_source_closure_snapshot",
        lambda _batch, _manifest: next(write_snapshots),
    )
    with pytest.raises(runner.CurrentRcG8RunError) as postwrite_drift:
        runner._write_outputs(
            during_write,
            private_payload,
            public_payload,
            key=_KEY,
            source_snapshot=source,
            expected_case_sources=_case_sources(),
            batch_path=runner._BATCH_PATH,
            manifest_path=runner._MANIFEST_PATH,
        )
    assert postwrite_drift.value.code == (
        "CURRENT_RC_G8_SOURCE_CHANGED_DURING_WRITE"
    )
    assert list(during_write.iterdir()) == []


def test_14_secure_disk_round_trip_is_0600_canonical_and_no_overwrite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _source_snapshot()
    private_payload, public_payload, _private, _public, _source = _payloads(
        source=source
    )
    output_dir = tmp_path / "g8-private"
    output_dir.mkdir(mode=0o700)
    os.chmod(output_dir, 0o700)
    monkeypatch.setattr(
        runner,
        "_source_closure_snapshot",
        lambda _batch, _manifest: copy.deepcopy(source),
    )
    private, public = runner._write_outputs(
        output_dir,
        private_payload,
        public_payload,
        key=_KEY,
        source_snapshot=source,
        expected_case_sources=_case_sources(),
        batch_path=runner._BATCH_PATH,
        manifest_path=runner._MANIFEST_PATH,
    )
    private_path = output_dir / runner._PRIVATE_FILENAME
    public_path = output_dir / runner._BODY_FREE_FILENAME
    assert stat.S_IMODE(private_path.stat().st_mode) == 0o600
    assert stat.S_IMODE(public_path.stat().st_mode) == 0o600
    assert private_path.read_bytes() == private_payload
    assert public_path.read_bytes() == public_payload
    assert {path.name for path in output_dir.iterdir()} == {
        runner._PRIVATE_FILENAME,
        runner._BODY_FREE_FILENAME,
    }
    runner._validate_pair(
        private,
        public,
        key=_KEY,
        expected_source=source,
        expected_case_sources=_case_sources(),
    )
    with pytest.raises(runner.CurrentRcG8RunError):
        runner._write_outputs(
            output_dir,
            private_payload,
            public_payload,
            key=_KEY,
            source_snapshot=source,
            expected_case_sources=_case_sources(),
            batch_path=runner._BATCH_PATH,
            manifest_path=runner._MANIFEST_PATH,
        )
    assert private_path.read_bytes() == private_payload
    assert public_path.read_bytes() == public_payload

    nonfresh = tmp_path / "nonfresh-private"
    nonfresh.mkdir(mode=0o700)
    os.chmod(nonfresh, 0o700)
    (nonfresh / "unrelated").write_text("occupied", encoding="utf-8")
    with pytest.raises(runner.CurrentRcG8RunError) as occupied:
        runner._write_outputs(
            nonfresh,
            private_payload,
            public_payload,
            key=_KEY,
            source_snapshot=source,
            expected_case_sources=_case_sources(),
            batch_path=runner._BATCH_PATH,
            manifest_path=runner._MANIFEST_PATH,
        )
    assert occupied.value.code == "CURRENT_RC_G8_PRIVATE_DIRECTORY_NOT_FRESH"
    assert not (nonfresh / runner._PRIVATE_FILENAME).exists()
    assert not (nonfresh / runner._BODY_FREE_FILENAME).exists()

    postverify = tmp_path / "postverify-private"
    postverify.mkdir(mode=0o700)
    os.chmod(postverify, 0o700)
    calls = 0
    original_validate_pair = runner._validate_pair

    def reject_after_write(*args: object, **kwargs: object) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise runner.CurrentRcG8RunError(
                "CURRENT_RC_G8_PRIVATE_OUTPUT_POSTVERIFY_FAILED"
            )
        original_validate_pair(*args, **kwargs)

    monkeypatch.setattr(runner, "_validate_pair", reject_after_write)
    with pytest.raises(runner.CurrentRcG8RunError) as postwrite:
        runner._write_outputs(
            postverify,
            private_payload,
            public_payload,
            key=_KEY,
            source_snapshot=source,
            expected_case_sources=_case_sources(),
            batch_path=runner._BATCH_PATH,
            manifest_path=runner._MANIFEST_PATH,
        )
    assert postwrite.value.code == (
        "CURRENT_RC_G8_PRIVATE_OUTPUT_POSTVERIFY_FAILED"
    )
    assert list(postverify.iterdir()) == []

    mixed = tmp_path / "mixed-private"
    mixed.mkdir(mode=0o700)
    os.chmod(mixed, 0o700)
    source_checks = 0

    def insert_unrelated_after_write(*args: object, **kwargs: object) -> None:
        nonlocal source_checks
        source_checks += 1
        if source_checks == 2:
            (mixed / "unrelated").write_text("occupied", encoding="utf-8")

    monkeypatch.setattr(runner, "_assert_source_unchanged", insert_unrelated_after_write)
    monkeypatch.setattr(runner, "_validate_pair", original_validate_pair)
    with pytest.raises(runner.CurrentRcG8RunError) as mixed_result:
        runner._write_outputs(
            mixed,
            private_payload,
            public_payload,
            key=_KEY,
            source_snapshot=source,
            expected_case_sources=_case_sources(),
            batch_path=runner._BATCH_PATH,
            manifest_path=runner._MANIFEST_PATH,
        )
    assert mixed_result.value.code == (
        "CURRENT_RC_G8_PRIVATE_DIRECTORY_POSTVERIFY_FAILED"
    )
    assert {path.name for path in mixed.iterdir()} == {"unrelated"}


def test_15_runner_imports_no_prior_runtime_gate_or_selector() -> None:
    source = Path(runner.__file__).resolve().read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    } | {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert not any("step11_runtime_adapter" in name for name in imported)
    assert not any("step11_hard_gate" in name for name in imported)
    assert {
        "emlis_nls_v3_batch_run",
        "emlis_nls_v3_s2_sample_registry",
        "emlis_ai_dormant_runtime_adapter_v3",
        "emlis_ai_semantic_hard_gate_v3",
        "emlis_ai_lexicographic_selector_v3",
    }.isdisjoint(imported)
    aliases = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert {
        "execute_step11_offline_v3",
        "evaluate_step11_natural_surface_candidate",
        "select_step11_natural_surface_candidates",
    }.isdisjoint(aliases)


def test_16_template_capture_is_exhaustive_and_typed_ambiguity_rejects() -> None:
    catalog = {
        "construction_predicate_fragments": {},
    }
    grammar = {"referent_scope_cues": {}}
    unique = {
        "ax": ("owner-ax", "", "", ""),
        "b": ("owner-b", "", "", ""),
    }
    assert runner._template_owner_matches(
        "{source}x{target}", "axxb", unique, catalog, grammar
    ) == ((
        ("owner-ax", ()),
        ("owner-b", ()),
    ),)
    ambiguous = {
        **unique,
        "a": ("owner-a", "", "", ""),
        "xb": ("owner-xb", "", "", ""),
    }
    assert len(
        runner._template_owner_matches(
            "{source}x{target}", "axxb", ambiguous, catalog, grammar
        )
    ) == 2


def test_17_leading_unparsed_piece_cannot_hide_behind_valid_tail() -> None:
    catalog = {
        "construction_predicate_fragments": {},
        "relation_predicate_fragments": {
            "linked:source_to_target": "{source}x{target}"
        },
        "semantic_link_predicate_fragments": {},
        "unknown_predicate_fragments": {},
        "clause_morphology": {
            "within_sentence_clause_join": "~",
            "grammatical_sentence_join": ".",
            "unknown_owner_join": "&",
            "construction_standalone_predicate": "!",
        },
    }
    grammar = {
        "clause_join": "|",
        "atom_joiners": ("+",),
        "temporal_scope_cues": {},
        "modality_cues": {},
        "polarity_cues": {},
        "referent_scope_cues": {},
    }
    owners = {
        "ax": ("owner-ax", "", "", ""),
        "b": ("owner-b", "", "", ""),
    }
    parsed = runner._parse_observation(
        ("garbage|axxb",), owners, catalog, grammar
    )
    assert parsed["unparsed"] == 1
    assert parsed["ambiguous"] == 0
    assert sum(parsed["atoms"].values()) == 1


def test_18_machine100_requires_exact_recovery_identity_and_all_checks() -> None:
    rows = _rows()
    runner._assert_machine100(rows)
    invalid_sets = []
    wrong_version = _rows()
    wrong_version[0]["candidate_version_id"] = "nls_v3_rc_0031"
    invalid_sets.append(wrong_version)
    failed_check = _rows()
    failed_check[0]["machine_checks"] = dict(
        failed_check[0]["machine_checks"]
    )
    failed_check[0]["machine_checks"]["source_envelope_exact"] = False
    invalid_sets.append(failed_check)
    missing = _rows()
    missing[0]["candidate_output_utf8"] = None
    invalid_sets.append(missing)
    for invalid in invalid_sets:
        with pytest.raises(runner.CurrentRcG8RunError) as captured:
            runner._assert_machine100(invalid)
        assert captured.value.code == "CURRENT_RC_G8_MACHINE100_REQUIRED"


def test_19_workers_receive_complete_snapshot_and_use_clean_spawn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _source_snapshot()
    captured: dict[str, object] = {}

    class FakeExecutor:
        def __init__(self, *, max_workers: int, mp_context: object) -> None:
            captured["workers"] = max_workers
            captured["start_method"] = mp_context.get_start_method()

        def __enter__(self) -> "FakeExecutor":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def map(
            self,
            function: object,
            jobs: object,
            *,
            chunksize: int,
        ) -> list[object]:
            material = tuple(jobs)
            captured["jobs"] = material
            captured["chunksize"] = chunksize
            return [function(row) for row in material]

    monkeypatch.setattr(runner, "ProcessPoolExecutor", FakeExecutor)
    monkeypatch.setattr(
        runner,
        "_case_row_job",
        lambda row: {
            "case_id": row[0]["case_id"],
            "snapshot": row[2],
        },
    )
    rows = runner._run_cases(
        [{"case_id": "nls3s_b001_0001", "input": {}}],
        {"nls3s_b001_0001": "1" * 64},
        source,
        workers=2,
    )
    assert captured["start_method"] == "spawn"
    assert captured["workers"] == 2
    assert captured["chunksize"] == 1
    jobs = captured["jobs"]
    assert jobs[0][2] == source
    assert set(jobs[0][2]) == {
        "source_closure_sha256",
        "source_closure_file_count",
        "source_closure_files",
    }
    assert rows[0]["snapshot"] == source


def test_20_worker_rejects_stale_before_import_and_change_after_build(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _source_snapshot()
    sample = {
        "case_id": "nls3s_b001_0001",
        "input": _selected_row(1)["source_input"],
    }
    called = False

    def must_not_build(*_args: object, **_kwargs: object) -> object:
        nonlocal called
        called = True
        raise AssertionError("build must not start")

    monkeypatch.setattr(runner, "_current_candidate", must_not_build)
    monkeypatch.setattr(
        runner,
        "_assert_source_unchanged",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            runner.CurrentRcG8RunError("CURRENT_RC_G8_WORKER_SOURCE_STALE")
        ),
    )
    with pytest.raises(runner.CurrentRcG8RunError) as stale:
        runner._case_row(sample, "1" * 64, source)
    assert stale.value.code == "CURRENT_RC_G8_WORKER_SOURCE_STALE"
    assert called is False

    calls = 0

    def change_after(*_args: object, **_kwargs: object) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise runner.CurrentRcG8RunError(
                "CURRENT_RC_G8_WORKER_SOURCE_CHANGED"
            )

    monkeypatch.setattr(runner, "_assert_source_unchanged", change_after)
    monkeypatch.setattr(
        runner,
        "_current_candidate",
        lambda *_args, **_kwargs: (
            "fail_close",
            None,
            runner._empty_checks(),
            "CURRENT_RC_G8_CASE_REJECTED",
        ),
    )
    with pytest.raises(runner.CurrentRcG8RunError) as changed:
        runner._case_row(sample, "1" * 64, source)
    assert changed.value.code == "CURRENT_RC_G8_WORKER_SOURCE_CHANGED"
    assert calls == 2


def test_21_source_derived_inverse_accepts_unmodified_recovery() -> None:
    context, candidate = _real_recovery_structural_case()
    assert runner._recovery_source_envelope_exact(candidate, context=context)
    assert all(
        runner._recovery_inverse_checks(candidate, context=context).values()
    )


def test_22_rehashed_coordinated_mutations_reject_with_replay_stubbed_green(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import emlis_ai_step11_cycle001_product_recovery_v3 as recovery
    from emlis_ai_nls_v3_artifact_contract import artifact_sha256

    context, candidate = _real_recovery_structural_case()
    envelope = candidate.source_envelope
    expected = runner._direct_expected_recovery(context)
    atom_bindings = tuple(envelope.atom_bindings)
    construction_index = next(
        index
        for index, row in enumerate(atom_bindings)
        if row.semantic_family == "construction"
    )
    link_index = next(
        index
        for index, row in enumerate(atom_bindings)
        if row.semantic_family == "semantic_link"
    )
    construction_forward_index = next(
        index
        for index, row in enumerate(candidate.construction_atoms)
        if row.construction_instance_id
        == atom_bindings[construction_index].source_atom_id
    )
    link_forward_index = next(
        index
        for index, row in enumerate(candidate.semantic_link_atoms)
        if row.source_semantic_link_id == atom_bindings[link_index].source_atom_id
    )
    original_replay = recovery.step11_cycle001_product_recovery_visible_inverse(
        candidate
    )
    monkeypatch.setattr(
        recovery,
        "step11_cycle001_product_recovery_visible_inverse",
        lambda _value: original_replay,
    )
    mutations: list[tuple[str, object, str | None]] = []

    def observation_unit_index(atom_id: str) -> int:
        return next(
            index
            for index, unit in enumerate(candidate.realization_plan.units)
            if unit.section_role == "observation"
            and atom_id in unit.source_atom_ids
        )

    link_plan_index = observation_unit_index(
        atom_bindings[link_index].source_atom_id
    )
    construction_plan_index = observation_unit_index(
        atom_bindings[construction_index].source_atom_id
    )

    changed_atoms = list(atom_bindings)
    changed_atoms[link_index] = replace(
        changed_atoms[link_index],
        semantic_key=changed_atoms[link_index].semantic_key + "_mutated",
    )
    changed_links = list(candidate.semantic_link_atoms)
    changed_links[link_forward_index] = replace(
        changed_links[link_forward_index],
        relation_type=(
            changed_links[link_forward_index].relation_type + "_mutated"
        ),
    )
    mutations.append(
        (
            "semantic_key",
            _coordinated_rehash(
                candidate,
                context,
                atom_bindings=tuple(changed_atoms),
                semantic_link_atoms=tuple(changed_links),
                body_section="observation",
                body_line_index=link_plan_index,
            ),
            "semantic_atoms_exact",
        )
    )

    changed_atoms = list(atom_bindings)
    changed_atoms[link_index] = replace(
        changed_atoms[link_index], direction="target_to_source"
    )
    changed_links = list(candidate.semantic_link_atoms)
    changed_links[link_forward_index] = replace(
        changed_links[link_forward_index], direction="target_to_source"
    )
    mutations.append(
        (
            "endpoint_direction",
            _coordinated_rehash(
                candidate,
                context,
                atom_bindings=tuple(changed_atoms),
                semantic_link_atoms=tuple(changed_links),
                body_section="observation",
                body_line_index=link_plan_index,
            ),
            "semantic_atoms_exact",
        )
    )

    changed_atoms = list(atom_bindings)
    role = changed_atoms[construction_index].construction_roles[0]
    changed_atoms[construction_index] = replace(
        changed_atoms[construction_index],
        construction_roles=(
            replace(
                role,
                role_position_surface_token=(
                    role.role_position_surface_token + "改"
                ),
            ),
            *changed_atoms[construction_index].construction_roles[1:],
        ),
    )
    changed_constructions = list(candidate.construction_atoms)
    forward_role = changed_constructions[construction_forward_index].role_atoms[
        0
    ]
    changed_constructions[construction_forward_index] = replace(
        changed_constructions[construction_forward_index],
        role_atoms=(
            replace(
                forward_role,
                role_position_surface_token=(
                    forward_role.role_position_surface_token + "改"
                ),
            ),
            *changed_constructions[0].role_atoms[1:],
        ),
    )
    mutations.append(
        (
            "construction_role",
            _coordinated_rehash(
                candidate,
                context,
                atom_bindings=tuple(changed_atoms),
                construction_atoms=tuple(changed_constructions),
                body_section="observation",
                body_line_index=construction_plan_index,
            ),
            "construction_modifiers_exact",
        )
    )

    changed_atoms = list(atom_bindings)
    changed_atoms[link_index] = replace(
        changed_atoms[link_index],
        dimensions=("mutated", *changed_atoms[link_index].dimensions[1:]),
    )
    changed_units = list(candidate.realization_plan.units)
    plan_index = link_plan_index
    changed_units[plan_index] = replace(
        changed_units[plan_index],
        dimensions=changed_atoms[link_index].dimensions,
    )
    mutations.append(
        (
            "dimension",
            _coordinated_rehash(
                candidate,
                context,
                atom_bindings=tuple(changed_atoms),
                plan_units=tuple(changed_units),
                body_section="observation",
                body_line_index=plan_index,
            ),
            "dimension_loci_exact",
        )
    )

    changed_roots = list(envelope.root_bindings)
    changed_root = replace(
        changed_roots[0],
        source_nucleus_id=changed_roots[0].source_nucleus_id + "_mutated",
        source_root_id=changed_roots[0].source_root_id + "_mutated",
    )
    changed_roots[0] = changed_root
    changed_units = list(candidate.realization_plan.units)
    changed_units[0] = replace(
        changed_units[0], source_unit_id=changed_root.source_root_id
    )
    mutations.append(
        (
            "root_lineage",
            _coordinated_rehash(
                candidate,
                context,
                root_bindings=tuple(changed_roots),
                plan_units=tuple(changed_units),
                body_section="observation",
                body_line_index=0,
            ),
            "inverse_layout_exact",
        )
    )

    changed_receptions = list(envelope.reception_bindings)
    reception = changed_receptions[0]
    alternate_owner = next(
        (
            row
            for row in candidate.owner_registry
            if row not in reception.source_target_owner_ids
        ),
        "nls3s11_mutated_owner",
    )
    new_act = (
        "hold_in_attention"
        if reception.effective_reception_act != "hold_in_attention"
        else "do_not_dismiss"
    )
    changed_receptions[0] = replace(
        reception,
        source_target_owner_ids=(alternate_owner,),
        effective_reception_act=new_act,
    )
    changed_units = list(candidate.realization_plan.units)
    owner_dimensions = {
        row.source_owner_id: row.dimensions for row in expected.owners
    }
    alternate_dimensions = owner_dimensions.get(
        alternate_owner, ("unknown", "unknown", "unknown", "unknown")
    )
    changed_units[-1] = replace(
        changed_units[-1],
        source_owner_ids=(alternate_owner,),
        source_owner_dimensions=(
            (alternate_owner, alternate_dimensions),
        ),
    )
    mutations.append(
        (
            "reception_target_act",
            _coordinated_rehash(
                candidate,
                context,
                reception_bindings=tuple(changed_receptions),
                plan_units=tuple(changed_units),
                body_section="reception",
                body_line_index=0,
            ),
            "reception_bindings_exact",
        )
    )

    changed_owners = list(envelope.owner_bindings)
    changed_referent = changed_owners[0].referent_text + "改"
    changed_owners[0] = replace(
        changed_owners[0],
        referent_text=changed_referent,
        referent_text_sha256=hashlib.sha256(
            changed_referent.encode("utf-8")
        ).hexdigest(),
    )
    mutations.append(
        (
            "owner_referent",
            _coordinated_rehash(
                candidate,
                context,
                owner_bindings=tuple(changed_owners),
                body_section="observation",
                body_line_index=0,
            ),
            None,
        )
    )

    for label, mutated, causal_check in mutations:
        source = mutated.source_envelope
        assert source.source_envelope_sha256 == artifact_sha256(
            recovery.step11_cycle001_product_recovery_source_envelope_material(
                source, include_id=False
            )
        ), label
        assert not runner._recovery_source_envelope_exact(
            mutated, context=context
        ), label
        checks = runner._recovery_inverse_checks(mutated, context=context)
        if causal_check is None:
            assert all(checks.values()), (label, checks)
        else:
            assert checks[causal_check] is False, (label, checks)
            assert not all(checks.values()), label


def test_23_exact100_preflight_fresh_process_loads_no_forbidden_oracle() -> None:
    forbidden_modules = {
        "emlis_nls_v3_batch_run",
        "emlis_nls_v3_s2_sample_registry",
        "emlis_ai_dormant_runtime_adapter_v3",
        "emlis_ai_semantic_hard_gate_v3",
        "emlis_ai_lexicographic_selector_v3",
        "emlis_ai_step11_runtime_adapter_v3",
        "emlis_ai_step11_hard_gate_v3",
        "emlis_ai_step11_natural_surface_matcher_v3",
    }
    program = "\n".join(
        (
            "import sys",
            f"sys.path.insert(0, {str(_TOOLS)!r})",
            "import emlis_nls_v3_step11_current_rc_g8_run as subject",
            "subject._exact100_sources(subject._BATCH_PATH, subject._MANIFEST_PATH)",
            f"forbidden = {forbidden_modules!r}",
            "if forbidden.intersection(sys.modules): raise SystemExit(31)",
            "closure = {path.name for path in subject._source_closure_paths(",
            "    subject._BATCH_PATH, subject._MANIFEST_PATH",
            ")}",
            "if {name + '.py' for name in forbidden}.intersection(closure):",
            "    raise SystemExit(32)",
        )
    )
    completed = subprocess.run(
        [sys.executable, "-B", "-c", program],
        cwd=_AI_ROOT.parent,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=60,
        check=False,
    )
    assert completed.returncode == 0


def test_24_commitment_key_reader_is_local_nofollow_and_0600(
    tmp_path: Path,
) -> None:
    key_path = (tmp_path / "commitment.key").resolve()
    key_path.write_bytes(_KEY)
    os.chmod(key_path, 0o600)
    assert runner._read_commitment_key(key_path) == _KEY

    os.chmod(key_path, 0o640)
    with pytest.raises(runner.CurrentRcG8RunError) as permissive:
        runner._read_commitment_key(key_path)
    assert permissive.value.code == "CURRENT_RC_G8_COMMITMENT_KEY_INVALID"
    os.chmod(key_path, 0o600)

    alias = tmp_path / "commitment-alias.key"
    alias.symlink_to(key_path)
    with pytest.raises(runner.CurrentRcG8RunError) as symlinked:
        runner._read_commitment_key(alias)
    assert symlinked.value.code == "CURRENT_RC_G8_COMMITMENT_KEY_INVALID"
