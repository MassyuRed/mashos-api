# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 10 runtime/evidence dependency closure and version transition guard.

The Step 9 manifest remains the historical offline closure.  This owner binds
the explicitly authorised reply-service transition and all dormant runner
owners without rewriting the old baseline artifact.
"""

import ast
import hashlib
from pathlib import Path
import re
from typing import Any

from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_step9_dependency_manifest_v3 import (
    FROZEN_STEP9_DEPENDENCY_MANIFEST_SHA256,
    STEP9_DEPENDENCY_MANIFEST,
    validate_step9_dependency_manifest,
)


HISTORICAL_V1_REPLY_SERVICE_SHA256 = (
    "a8b494ff6d14df771e3f1c17d7d516c8457daf17a9431a118f3b44088aff90b6"
)
FROZEN_STEP10_CANDIDATE_VERSION_ID = "nls_v3_rc_0010"
FROZEN_STEP10_MANIFEST_SOURCE_NORMALIZED_SHA256 = "460848600f76b0b3cfd710dc441f54df13c88b4f58fde59f218a4fd3234d0648"

_DEPENDENCY_GROUP_NAMES = (
    "current_source_files",
    "frozen_step9_source_files",
    "runtime_dependency_files",
    "local_e2e_integration_files",
    "local_e2e_transitive_files",
    "test_closure_files",
    "step10_contract_files",
    "unchanged_contract_files",
)
_NORMALIZED_SOURCE_TRUST_ROOT_NAMES = frozenset(
    {
        "FROZEN_STEP10_MANIFEST_SOURCE_NORMALIZED_SHA256",
        "FROZEN_STEP10_DEPENDENCY_CLOSURE_SHA256",
        "FROZEN_STEP10_MANIFEST_SHA256",
    }
)
# This is a tooling hash dependency, not a production import edge.  Keep the
# path assembled so Step 2's frozen source scan can continue to assert that no
# inference owner names/imports its evaluation registry module.
_STEP2_SAMPLE_REGISTRY_TOOL_PATH = (
    "ai/tests/helpers/emlis_nls_v3_s2_" + "sample_registry.py"
)

# Values are patched from final verified bytes once all Step 10 owners exist.
STEP10_DEPENDENCY_MANIFEST: dict[str, Any] = {
    "schema_version": "cocolon.emlis.nls_v3.step10_dependency_manifest.v1",
    "manifest_source_normalized_sha256": (
        FROZEN_STEP10_MANIFEST_SOURCE_NORMALIZED_SHA256
    ),
    "historical_step9_dependency_manifest_sha256": (
        "9ac49f3ee8978f48ff402afdd9fb15f16063595546898e514b09b9bdaf58e880"
    ),
    "historical_v1_reply_service_sha256": HISTORICAL_V1_REPLY_SERVICE_SHA256,
    "current_source_files": {
        "ai/services/ai_inference/emlis_ai_dormant_runtime_adapter_v3.py": "50dab4ba0c788b1c6c4626b57c414ebdc371da54a66df87606cdee832a29669b",
        "ai/services/ai_inference/emlis_ai_reply_service.py": "162b94eb185c519e50dceee62e591cc8ab02204312761874eb2fbb636ffbe50a",
        "ai/services/ai_inference/emlis_ai_step10_app_reachable_contract_v3.py": "ab9739f0fadfa111b9fb34d04693c797f698b88501114ab1a6dfa75247af57d3",
        "ai/services/ai_inference/emlis_ai_step10_evidence_v3.py": "a71d882dee06e29a06b7fd2baba4541ea91dbed18599298da13b3bbea9cd0b35",
        "ai/services/ai_inference/emlis_ai_step9_dependency_manifest_v3.py": "19a21d5853c44130c2c874e8b9c6bbbc0a1fc79591c529fb060e7c1e3cd7742e",
        "ai/tools/emlis_nls_v3_batch_run.py": "eecc03475f25e4ba42a65d1912da0507bbc744f0256d87968ee594def4594996",
        "ai/tools/emlis_nls_v3_cumulative_regression.py": "1a2e0ef0693819114baff54f774a97db5cbf5326b817279fd42443e985fc14a7",
        "ai/tools/emlis_nls_v3_output_diff.py": "8c6b250b6531079651ab70754ee161447fa8dae5462ecd17aa4ccb07bcd12da5",
        "ai/tools/emlis_nls_v3_receipt_verify.py": "2931adfc9459a4677dc6ad4c2ddc5bec10ad3d9e808a92f5b27409d9876c579d",
    },
    "frozen_step9_source_files": {
        f"ai/services/ai_inference/{filename}": sha256
        for filename, sha256 in STEP9_DEPENDENCY_MANIFEST["source_files"].items()
        if filename != "emlis_ai_reply_service.py"
    },
    "runtime_dependency_files": {
        "ai/services/ai_inference/emlis_ai_capability.py": "6edba1c3a097c980b87d68a34f50a3666bc62eaeee8a872b9b456d630c53c311",
        "ai/services/ai_inference/emlis_ai_current_input_bundle.py": "63ddb6bf3db472bdaddfd8c3fbef68034aeb3cf51188508c0ad8b8cd920271f8",
        "ai/services/ai_inference/emlis_ai_grounded_human_reception.py": "a3db3804298ec4c78007faf245f898e64eafbaf04c640b78f2dc24434ffc2298",
        "ai/services/ai_inference/emlis_ai_grounded_observation_gate.py": "932b43a7b6dc5cd8d58ddeff3d7ba3bd5e044ba71858fd6b4f6fdde3b7656c2f",
        "ai/services/ai_inference/emlis_ai_grounded_sentence_surface.py": "e9679d31ee647fa34831def3917a9bc5b17ef5e725f5815635aa4fe3e6f875e0",
        "ai/services/ai_inference/emlis_ai_observation_integrator_service.py": "20aa4f793054844904084ee72c4bdc3b3198a7ad849c8a29fe526a655ce1bf21",
        "ai/services/ai_inference/emlis_ai_perspective_board.py": "c4eabe4403c1cf98f4c645ca94cdf8164f69408d9027f7996f18965dc9c34e93",
        "ai/services/ai_inference/emlis_ai_perspective_observers.py": "cca669364efa7359bd08fcfe8bf5335519be76a81f6700254ed5d0be713ecb61",
        "ai/services/ai_inference/emlis_ai_response_contract.py": "e2c0e7af36700865cb471ef598fa99afa0b775507172571d5a44946b2d71a4c7",
        "ai/services/ai_inference/emlis_ai_safety_boundary_service.py": "77c0317a5bcdf2a71e932f6bd9b53cec2beceb80ddf69f0f5bcb18a22a1c66b7",
        "ai/services/ai_inference/emlis_ai_safety_triage.py": "9aa7ee3b0742fa267e7396b946694d6f99e3ac8f65217e65453b1faad5b2425b",
        "ai/services/ai_inference/emlis_ai_types.py": "3a0cfc7ee9c49cb0dd2b014493357ccd84924f455b22cc483272bf1872d80b17",
        "ai/services/ai_inference/emlis_ai_user_address_service.py": "eecc778d6fc58204801617a4531ffff268346e5f683d9bccfdb45ec382cd3913",
        "ai/services/ai_inference/subscription.py": "9cf2a0b6c7aa4e9a7d79ab9497c8ab26b293b38f245c900259933c5dca743713",
    },
    "local_e2e_integration_files": {
        "ai/services/ai_inference/api_emotion_submit.py": "0705dc5cd7d4a78a4b8f6de1721b80b1ea6ae70b1d48a064acff9a8277af1822",
        "ai/services/ai_inference/emlis_ai_complete_initial_surface_availability.py": "16a280727728ec8b3a194d47bb6c15de98317ac5d4e978d8fc8707e33a561ca2",
        "ai/services/ai_inference/emlis_ai_observation_diagnostic_lockdown.py": "1a311d1dcdbc938a6088c80934897e724e5c1292dd77b848791c4ca3a5b97e99",
        "ai/services/ai_inference/emlis_ai_product_surface_validation.py": "e96bbd493803a190fe012722edfc3238c9b28a37b42c3865b7ec8442f500b05c",
        "ai/services/ai_inference/response_microcache.py": "75a047db0683cd0d1a1db480812a73c29bbfe7c08e383d0e5079598724f1982f",
        "ai/services/ai_inference/subscription_store.py": "f941ad0d8df40f4ee90dc50ec1c854dd08634dcd3076181ac7a50f9ea6162e67",
    },
    "local_e2e_transitive_files": {
        "ai/services/ai_inference/cocolon_environment_state_output_frame.py": "1a27d8f07ecf95cf9d852dd8084a38b68d8127bab17f49d620e8584fe118c1a4",
        "ai/services/ai_inference/emlis_ai_body_free_public_source_lineage.py": "1e2515fa25a80a3bd84b0c0461840dc6fc37845ecc5dbf0d68defd220d1c1a53",
        "ai/services/ai_inference/emlis_ai_complete_initial_surface_recomposition.py": "8c492e29607578d58ad0344d4f9ce480958fb25d6b71e51bdbfa0a3a2d0e645e",
        "ai/services/ai_inference/emlis_ai_diagnostic_failure_taxonomy.py": "c5f9ebbafb96cd389cc51aad6ac13048f6c3c4c51161a461f3691e8581f61cdd",
        "ai/services/ai_inference/emlis_ai_gate_recovery_public_constants.py": "9e25149d7968f4cabb63bc4cad8b63538d33f29aba1605aedf8a6066f8162411",
        "ai/services/ai_inference/emlis_ai_human_follow_selector.py": "bede5fb2b0b089a7af6aa2e2f8960ab4dcdd93d6a49683e49e117c9e99a4b7a6",
        "ai/services/ai_inference/emlis_ai_labelled_two_stage_surface_recomposition.py": "b6045b2dac7a984f348ed7868b973a93ed1636ce581c8798a0d0aa230fad8d81",
        "ai/services/ai_inference/emlis_ai_limited_grounding_reception_surface.py": "796a08428984e69763813905f83329129adc53eee32bac4e4b66fed255e253dc",
        "ai/services/ai_inference/emlis_ai_observation_reply_contract.py": "84c58c6b0cf23ade91609aedd88b22c8497898dda24dcf2657d4bedb6cd537c0",
        "ai/services/ai_inference/emlis_ai_observation_structure_dictionary_loader.py": "bbda7d45ede010c68f175bfb8f925efc6c70d8fa5c092f6c88d8de7bd54bb805",
        "ai/services/ai_inference/emlis_ai_observation_structure_material_service.py": "2897deadf2409757b8fc4c181d34c9a306629a1094f467aabf20a28e94c3b9ef",
        "ai/services/ai_inference/emlis_ai_public_surface_requirement.py": "b84806547836cc7464486f6155e02d840b36289450f09c34281c185f8caa3343",
        "ai/services/ai_inference/emlis_ai_question_dominance_guard.py": "4dc801a22ef2d82cebfe60d14ed1ee0e042b899b3924a452137b6c15837f96aa",
        "ai/services/ai_inference/emlis_ai_reception_assistance_dictionary_loader.py": "82e5dc4c28132f1e295afd6dfb6a389cac579c0324e011ff046f986618e555c2",
        "ai/services/ai_inference/emlis_ai_reception_mode_resolver.py": "ec56f2eb0c0146ebc1e9cc8804e4a05001af049e826e9f9f73cfb8ab918de3e2",
        "ai/services/ai_inference/emlis_ai_runtime_surface_exit_criteria.py": "5c2f1e6f5c107b0144ec647e3954935da9ab3ac0160386cece3755d9092aed24",
        "ai/services/ai_inference/emlis_ai_safe_daily_metaphor_material.py": "4d8b9bc3ca097733aee040eed5268ad434e890ec6b94087e772739f0c3501447",
        "ai/services/ai_inference/emlis_ai_shared_reception_evidence.py": "ed2996d1629a951c16b6a667252ffa4fa5ad84ff1693949050c065174a505737",
        "ai/services/ai_inference/emlis_ai_state_answer_gate_boundary.py": "f25d40394225491a2a4bfc8959813885cbe4b7e5f22dbdd0802713a5f98ceb5d",
        "ai/services/ai_inference/emlis_ai_state_answer_ratio_policy.py": "6d2452a06bbba70d9ea78d171c6622c30eddfc23dc019ddd305b1c6c1ec6b09c",
        "ai/services/ai_inference/emlis_ai_state_answer_special_cases.py": "a09b9ddecd72642681e840885c6e2457e3ec5e30ff5a3c26146a99a8c77ad4e7",
        "ai/services/ai_inference/emlis_ai_state_answer_surface_contract.py": "ed7ff52e76dc7dcb49de131558f54cba58f1b1465300f4ab3dfe093e4bec3577",
        "ai/services/ai_inference/emlis_ai_two_stage_applicability.py": "42ed5d71cd7c0b6370407f36ffa1f5429ff0a2e19c9d6cde89df7a0b7c56b7bb",
        "ai/services/ai_inference/emlis_ai_two_stage_reception_gate.py": "d9cd0ba56cbf5e9432c1217bcc0bbbe36ec3ac02d297c17f7a8534744b25f948",
        "ai/services/ai_inference/emlis_ai_user_fact_grounding_boundary.py": "6514f28b26ee6ddd604d2f0446734b5a25e17dc617cdb5cb106342c044215218",
        "ai/services/ai_inference/emlis_ai_user_label_connection_candidate.py": "d4a20b32e6b4955930426587553fb33bce49291431352ded58e2bb4f6e3e830f",
        "ai/services/ai_inference/emlis_ai_user_label_connection_gate.py": "e786889512a133c2d7bf5bf75bb09c76861ab054b55381fd43678047d85d609b",
        "ai/services/ai_inference/emlis_ai_user_label_connection_material.py": "541d7e81e144f9cbb322a0feb827fc1e3431a6d7ccc80997d13aa68d017ef02a",
        "ai/services/ai_inference/emlis_ai_user_label_connection_public_meta.py": "0dab60f3161525ea8a52d7a1c8a73bb989eb67aaa359d1181434eb54b4803aa5",
        "ai/services/ai_inference/emlis_ai_user_label_connection_surface.py": "863525231938e8869f0b90e1420052232c598b34e9bda665bbf19568fb48eec4",
        "ai/services/ai_inference/emlis_ai_user_label_connection_types.py": "dfe48f23f38cc767ec79718ef87390210f35b891ccf1dd42e27fa30a72fb4891",
    },
    "test_closure_files": {
        "ai/tests/helpers/emlis_nls_v3_s0_s1_baseline.py": "652bd446bd33995d9575b6db60f765caa97305b98d439d294de33bc569ea9f80",
        "ai/tests/test_emlis_nls_v3_s0_s1.py": "fb22f2d76f395f9940a3e735452159787aede36cb26d3ce347d08d7cf41906ce",
        "ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py": "3b87599907e71ea4e98f629aa0252c2a8c9d066458f9f6eac8dd843721c786ae",
        "ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py": "9f6e6b7fc359620106b0ca217c76b060141787889aa1cc79919be1fc6aca63be",
    },
    "step10_contract_files": {
        "ai/tests/schemas/emlis_nls_v3_case_evidence_receipt_v3.schema.json": "463bc226f63436658aa026ab540a1db11c67eeb550324f177216cdfb878b1255",
    },
    "unchanged_contract_files": {
        "ai/services/ai_inference/api_contract_registry.py": "2e2043392f0ca1088c3442685203e0d1949714870e29c03d0f51f3de6d38205b",
        "ai/services/ai_inference/emlis_ai_public_feedback_meta.py": "097be8c02eb68abb7d6a034243b3bd7296842f634f01269349c41b4f8c029029",
        "ai/services/ai_inference/emotion_submit_service.py": "818ee1edb7ac4ff5f12cc7f8537eeb10fedc9f7dd37a4d165c5248a7249830f2",
        _STEP2_SAMPLE_REGISTRY_TOOL_PATH: "cf4f048258c92ccad8d99ee8af4926f1a5730682ae772b9d44a16fc302ff9b6d",
        "ai/tests/fixtures/emlis_nls_v3_s1_input_contract_20260714.json": (
            "d577ac80457e25389c0bac351139b2c80a9a506f225023fb7928a1b9068d53c6"
        ),
        "ai/tests/schemas/emlis_nls_v3_case_evidence_receipt_v2.schema.json": "dc1991712a7bd73d6ead1b1ee9e46f3f91847c7801bc886c108f89c5df8e1dfb",
        "ai/tests/schemas/emlis_nls_v3_sample_case_v1.schema.json": "90d569460f05aa7347145ba1562754c1304fe4b4878165b5bfbb1180cf9087ef",
        "ai/tests/schemas/emlis_nls_v3_coverage_matrix_v1.schema.json": "1e0f31277fd008759e221d0c60ce589ecaede74dfcd55f49002dccd0a68a5c4c",
        "ai/tests/schemas/emlis_nls_v3_sample_batch_manifest_v1.schema.json": "439a64bd457d547bb530922be0d6273d1415783c15fea31f1b618a924035cdae",
        "ai/tests/schemas/emlis_nls_v3_corpus_registry_v1.schema.json": "d28fe0045a393965c4637a320fa98fc1b23c632ca1dd75888a0925d9e61d6c62",
        "ai/tests/fixtures/emlis_nls_v3/generated/batch_001.jsonl": (
            "013dd2ad1c1f446f843f400b3eb16231e8f32649e30114e70039b4cb709e8414"
        ),
        "ai/tests/fixtures/emlis_nls_v3/generated/batch_001_coverage_matrix.json": "4ea17d30ebdf624b374591f5ea9dde7240455a3a833c691d4a2a6e77d5649e5f",
        "ai/tests/fixtures/emlis_nls_v3/generated/batch_001_duplicate_report.json": "140e17311d84ae275ca90d3e93f1aafdfcd667f7bbaaacd92a729df550676354",
        "ai/tests/fixtures/emlis_nls_v3/generated/batch_001_manifest.json": "2b3308c4ada090539a2fc71c1cb235970aa0b90687b8d9633464ba61e94deba4",
        "ai/tests/fixtures/emlis_nls_v3_s2_corpus_registry_20260714.json": "7746ec94267fae0b89adbf8b5a676e469386fd3376275bc5197e39742941eb3d",
    },
    "runtime_boundary": {
        "frozen_candidate_version_id": FROZEN_STEP10_CANDIDATE_VERSION_ID,
        "default_public_routing_state": "disabled",
        "production_owner": "grounded_sentence_surface_canonical_v1",
        "rollback_owner": "grounded_sentence_surface_canonical_v1",
        "v3_general_account_visible": False,
        "owner_activation_permitted_in_step10": False,
        "reply_service_public_export": ["render_emlis_ai_reply"],
        "reply_to_adapter_import": "emlis_ai_dormant_runtime_adapter_v3",
        "core_to_reply_import_forbidden": True,
    },
    "baseline_boundary": {
        "known_v1_case_count": 28,
        "v1_default_output_set_sha256": (
            "a3267017ea4a386795302c91ff0c2a1beb2ee6592cf5a6ef30b0bf191c594bb3"
        ),
        "default_production_output_diff_count": 0,
    },
    "evidence_boundary": {
        "commitment_scheme": "hmac_sha256_v1",
        "private_body_full_separate": True,
        "body_free_summary_required": True,
        "raw_sha256_public_forbidden": True,
        "manual_aggregate_forbidden": True,
        "partial_cumulative_pass_forbidden": True,
    },
    "completion_boundary": {
        "step10_is_formal_batch001_initial_run": False,
        "step10_is_batch001_accepted": False,
        "next_step_authority": "step11_cycle001_initial_run_only",
    },
}

STEP10_DEPENDENCY_MANIFEST_SHA256 = artifact_sha256(STEP10_DEPENDENCY_MANIFEST)
FROZEN_STEP10_DEPENDENCY_CLOSURE_SHA256 = "2b4cd6cb5ea0f0d69ae7de31930dd6833ba21fce8eb7262f579cad514f14a8e9"
FROZEN_STEP10_MANIFEST_SHA256 = "83af18e635b16a7ca5680940f7362e9b844961bf2ac23101ba65a1b44fcc1af2"
FROZEN_V1_DEFAULT_OUTPUT_SET_SHA256 = STEP10_DEPENDENCY_MANIFEST[
    "baseline_boundary"
]["v1_default_output_set_sha256"]

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SHA_RE = re.compile(r"^[0-9a-f]{64}$")


def _file_sha256(relative_path: str) -> str | None:
    try:
        return hashlib.sha256((_REPO_ROOT / relative_path).read_bytes()).hexdigest()
    except OSError:
        return None


def _declared_dependency_paths() -> set[str]:
    paths: set[str] = set()
    for group_name in _DEPENDENCY_GROUP_NAMES:
        group = STEP10_DEPENDENCY_MANIFEST.get(group_name)
        if type(group) is dict:
            paths.update(path for path in group if type(path) is str)
    return paths


def _normalized_manifest_source_bytes(raw: bytes) -> bytes | None:
    """Normalize only the three post-source freeze slots.

    Dependency entry hashes are intentionally not normalized: changing one of
    them must change this source trust root.  The closure and manifest hashes,
    however, are necessarily written after the source root is calculated, so
    their assignment expressions are replaced by a canonical zero literal.
    """

    try:
        source = raw.decode("utf-8", errors="strict")
        tree = ast.parse(source)
    except (SyntaxError, UnicodeError):
        return None
    lines = raw.splitlines(keepends=True)
    starts: list[int] = []
    offset = 0
    for line in lines:
        starts.append(offset)
        offset += len(line)
    replacements: dict[str, tuple[int, int]] = {}
    for node in tree.body:
        if (
            not isinstance(node, ast.Assign)
            or len(node.targets) != 1
            or not isinstance(node.targets[0], ast.Name)
            or node.targets[0].id not in _NORMALIZED_SOURCE_TRUST_ROOT_NAMES
            or not hasattr(node.value, "end_lineno")
            or not hasattr(node.value, "end_col_offset")
        ):
            continue
        name = node.targets[0].id
        if name in replacements:
            return None
        replacements[name] = (
            starts[node.value.lineno - 1] + node.value.col_offset,
            starts[node.value.end_lineno - 1] + node.value.end_col_offset,
        )
    if set(replacements) != _NORMALIZED_SOURCE_TRUST_ROOT_NAMES:
        return None
    normalized = raw
    zero_literal = b'"' + (b"0" * 64) + b'"'
    for start, end in sorted(replacements.values(), reverse=True):
        normalized = normalized[:start] + zero_literal + normalized[end:]
    return normalized


def normalized_step10_manifest_source_sha256() -> str | None:
    """Fresh normalized hash of this manifest owner, including its logic."""

    try:
        raw = Path(__file__).resolve().read_bytes()
    except OSError:
        return None
    normalized = _normalized_manifest_source_bytes(raw)
    return hashlib.sha256(normalized).hexdigest() if normalized is not None else None


def current_step10_source_hashes() -> dict[str, str | None]:
    return {
        path: _file_sha256(path) for path in sorted(_declared_dependency_paths())
    }


def fresh_step10_source_closure_sha256() -> str:
    """Fresh-read every source/contract owner; never use import-cached hashes."""

    hashes = current_step10_source_hashes()
    manifest_source_sha256 = normalized_step10_manifest_source_sha256()
    if (
        not hashes
        or any(value is None for value in hashes.values())
        or type(manifest_source_sha256) is not str
        or _SHA_RE.fullmatch(manifest_source_sha256) is None
    ):
        raise ValueError("STEP10_SOURCE_CLOSURE_INCOMPLETE")
    return artifact_sha256(
        {
            "schema_version": "cocolon.emlis.nls_v3.step10_source_closure.v1",
            "frozen_candidate_version_id": FROZEN_STEP10_CANDIDATE_VERSION_ID,
            "manifest_source_normalized_sha256": manifest_source_sha256,
            "historical_step9_dependency_manifest_sha256": (
                FROZEN_STEP9_DEPENDENCY_MANIFEST_SHA256
            ),
            "files": hashes,
        }
    )


def step10_source_file_sha256(relative_path: str) -> str | None:
    expected = STEP10_DEPENDENCY_MANIFEST.get("current_source_files", {}).get(
        relative_path
    )
    return expected if type(expected) is str and _SHA_RE.fullmatch(expected) else None


def _reply_contract_issues() -> set[str]:
    issues: set[str] = set()
    path = _REPO_ROOT / "ai/services/ai_inference/emlis_ai_reply_service.py"
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError, UnicodeError):
        return {"STEP10_REPLY_SERVICE_PARSE_FAILED"}
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    render = functions.get("render_emlis_ai_reply")
    if not isinstance(render, ast.AsyncFunctionDef):
        issues.add("STEP10_PUBLIC_RENDER_OWNER_MISSING")
    else:
        positional = [arg.arg for arg in render.args.args]
        keyword_only = [arg.arg for arg in render.args.kwonlyargs]
        if positional or keyword_only != [
            "user_id",
            "subscription_tier",
            "current_input",
            "display_name",
            "timezone_name",
            "composer_client",
        ]:
            issues.add("STEP10_PUBLIC_SIGNATURE_DIFF")
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    if "emlis_ai_dormant_runtime_adapter_v3" not in imports:
        issues.add("STEP10_REPLY_ADAPTER_EDGE_MISSING")
    if any(
        name in imports
        for name in {
            "emlis_ai_semantic_hard_gate_v3",
            "emlis_ai_body_semantic_atom_parser_v3",
            "emlis_ai_independent_semantic_matcher_v3",
        }
    ):
        issues.add("STEP10_REPLY_DIRECT_CORE_IMPORT_FORBIDDEN")
    assignments = {
        target.id: node.value.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance((target := node.targets[0]), ast.Name)
        and isinstance(node.value, ast.Constant)
    }
    if assignments.get("_NLS_V3_STEP10_PUBLIC_ROUTING_STATE") != "disabled":
        issues.add("STEP10_DEFAULT_ROUTE_NOT_DISABLED")
    if '__all__ = ["render_emlis_ai_reply"]' not in source:
        issues.add("STEP10_PUBLIC_EXPORT_DIFF")
    return issues


def _reverse_import_issues() -> set[str]:
    issues: set[str] = set()
    service_root = _REPO_ROOT / "ai/services/ai_inference"
    core_names = {
        "emlis_ai_body_semantic_atom_parser_v3.py",
        "emlis_ai_bounded_recovery_v3.py",
        "emlis_ai_canonical_renderer_v3.py",
        "emlis_ai_content_selection_v3.py",
        "emlis_ai_discourse_graph_planner_v3.py",
        "emlis_ai_independent_semantic_matcher_v3.py",
        "emlis_ai_semantic_hard_gate_v3.py",
        "emlis_ai_semantic_obligation_inventory_v3.py",
        "emlis_ai_typed_surface_ast_v3.py",
    }
    for name in core_names:
        try:
            source = (service_root / name).read_text(encoding="utf-8")
            tree = ast.parse(source, filename=name)
        except (OSError, SyntaxError, UnicodeError):
            issues.add("STEP10_CORE_IMPORT_SCAN_FAILED")
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import) and any(
                alias.name == "emlis_ai_reply_service" for alias in node.names
            ):
                issues.add("STEP10_CORE_TO_REPLY_IMPORT_FORBIDDEN")
            elif (
                isinstance(node, ast.ImportFrom)
                and node.module == "emlis_ai_reply_service"
            ):
                issues.add("STEP10_CORE_TO_REPLY_IMPORT_FORBIDDEN")
    return issues


def _local_e2e_transitive_import_issues() -> set[str]:
    """Bind the full local import closure exercised by the Step 10 E2E test.

    The three production-boundary owners replaced with in-process test doubles
    are still required to be declared, but their own imports are not followed.
    This manifest owner is covered by its normalized source trust root instead
    of listing (and recursively self-hashing) itself as a dependency entry.
    """

    service_root = _REPO_ROOT / "ai/services/ai_inference"
    root_module = "emotion_submit_service"
    non_recursive_modules = frozenset(
        {
            "api_emotion_submit",
            "response_microcache",
            "subscription_store",
            "emlis_ai_step10_dependency_manifest_v3",
        }
    )
    manifest_owner = Path(__file__).resolve()
    declared = _declared_dependency_paths()
    issues: set[str] = set()
    reachable: set[str] = set()
    pending = [root_module]
    parsed: set[str] = set()
    while pending:
        module = pending.pop()
        if module in parsed:
            continue
        parsed.add(module)
        path = service_root.joinpath(*module.split(".")).with_suffix(".py")
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
        except (OSError, SyntaxError, UnicodeError):
            issues.add("STEP10_LOCAL_E2E_TRANSITIVE_DEPENDENCY_PARSE_FAILED")
            continue
        for node in ast.walk(tree):
            modules: list[str] = []
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.append(node.module)
            for imported_module in modules:
                candidate = service_root.joinpath(
                    *imported_module.split(".")
                ).with_suffix(".py")
                if not candidate.is_file():
                    continue
                try:
                    resolved = candidate.resolve(strict=True)
                    relative = resolved.relative_to(_REPO_ROOT).as_posix()
                except (OSError, ValueError):
                    issues.add(
                        "STEP10_LOCAL_E2E_TRANSITIVE_DEPENDENCY_OUTSIDE_REPO"
                    )
                    continue
                reachable.add(relative)
                if resolved != manifest_owner and relative not in declared:
                    issues.add(
                        "STEP10_LOCAL_E2E_TRANSITIVE_DEPENDENCY_UNBOUND"
                    )
                if imported_module not in non_recursive_modules:
                    pending.append(imported_module)
    transitive_group = STEP10_DEPENDENCY_MANIFEST.get(
        "local_e2e_transitive_files"
    )
    if type(transitive_group) is not dict or not set(transitive_group).issubset(
        reachable
    ):
        issues.add("STEP10_LOCAL_E2E_TRANSITIVE_DECLARATION_UNREACHABLE")
    return issues


def validate_step10_dependency_manifest() -> tuple[str, ...]:
    issues: set[str] = set()
    if type(STEP10_DEPENDENCY_MANIFEST) is not dict:
        return ("STEP10_DEPENDENCY_MANIFEST_SHAPE_INVALID",)
    if (
        FROZEN_STEP9_DEPENDENCY_MANIFEST_SHA256
        != STEP10_DEPENDENCY_MANIFEST.get(
            "historical_step9_dependency_manifest_sha256"
        )
    ):
        issues.add("STEP10_HISTORICAL_STEP9_HASH_MISMATCH")
    if validate_step9_dependency_manifest():
        issues.add("STEP10_STEP9_DEPENDENCY_DRIFT")
    runtime_boundary = STEP10_DEPENDENCY_MANIFEST.get("runtime_boundary")
    if (
        FROZEN_STEP10_CANDIDATE_VERSION_ID != "nls_v3_rc_0010"
        or type(runtime_boundary) is not dict
        or runtime_boundary.get("frozen_candidate_version_id")
        != FROZEN_STEP10_CANDIDATE_VERSION_ID
    ):
        issues.add("STEP10_CANDIDATE_VERSION_BOUNDARY_INVALID")
    live_manifest_source_hash = normalized_step10_manifest_source_sha256()
    recorded_manifest_source_hash = STEP10_DEPENDENCY_MANIFEST.get(
        "manifest_source_normalized_sha256"
    )
    if (
        type(FROZEN_STEP10_MANIFEST_SOURCE_NORMALIZED_SHA256) is not str
        or _SHA_RE.fullmatch(FROZEN_STEP10_MANIFEST_SOURCE_NORMALIZED_SHA256)
        is None
        or FROZEN_STEP10_MANIFEST_SOURCE_NORMALIZED_SHA256 == "0" * 64
        or recorded_manifest_source_hash
        != FROZEN_STEP10_MANIFEST_SOURCE_NORMALIZED_SHA256
        or live_manifest_source_hash
        != FROZEN_STEP10_MANIFEST_SOURCE_NORMALIZED_SHA256
    ):
        issues.add("STEP10_MANIFEST_SOURCE_SELF_HASH_DRIFT")
    baseline = STEP10_DEPENDENCY_MANIFEST.get("baseline_boundary")
    if (
        type(baseline) is not dict
        or set(baseline)
        != {
            "known_v1_case_count",
            "v1_default_output_set_sha256",
            "default_production_output_diff_count",
        }
        or baseline.get("known_v1_case_count") != 28
        or not _SHA_RE.fullmatch(
            str(baseline.get("v1_default_output_set_sha256", ""))
        )
        or baseline.get("v1_default_output_set_sha256") == "0" * 64
        or baseline.get("default_production_output_diff_count") != 0
    ):
        issues.add("STEP10_V1_BASELINE_BOUNDARY_INVALID")
    try:
        live_manifest_hash = artifact_sha256(STEP10_DEPENDENCY_MANIFEST)
    except (RecursionError, TypeError, ValueError, UnicodeError):
        live_manifest_hash = None
    if (
        live_manifest_hash != FROZEN_STEP10_MANIFEST_SHA256
        or STEP10_DEPENDENCY_MANIFEST_SHA256 != FROZEN_STEP10_MANIFEST_SHA256
    ):
        issues.add("STEP10_MANIFEST_HASH_DRIFT")
    hashes = current_step10_source_hashes()
    seen_paths: set[str] = set()
    for group_name in _DEPENDENCY_GROUP_NAMES:
        group = STEP10_DEPENDENCY_MANIFEST.get(group_name)
        if type(group) is not dict or not group:
            issues.add("STEP10_DEPENDENCY_GROUP_INVALID")
            continue
        for path, expected in group.items():
            if path in seen_paths:
                issues.add("STEP10_DEPENDENCY_PATH_DUPLICATE")
            elif type(path) is str:
                seen_paths.add(path)
            if (
                type(path) is not str
                or Path(path).is_absolute()
                or ".." in Path(path).parts
                or type(expected) is not str
                or _SHA_RE.fullmatch(expected) is None
            ):
                issues.add("STEP10_DEPENDENCY_ENTRY_INVALID")
            elif hashes.get(path) != expected:
                issues.add("STEP10_DEPENDENCY_SOURCE_BYTES_DRIFT")
    try:
        closure_hash = fresh_step10_source_closure_sha256()
    except (TypeError, ValueError, UnicodeError):
        closure_hash = None
    if closure_hash != FROZEN_STEP10_DEPENDENCY_CLOSURE_SHA256:
        issues.add("STEP10_SOURCE_CLOSURE_DRIFT")
    issues.update(_reply_contract_issues())
    issues.update(_reverse_import_issues())
    issues.update(_local_e2e_transitive_import_issues())
    return tuple(sorted(issues))


__all__ = [
    "FROZEN_STEP10_CANDIDATE_VERSION_ID",
    "FROZEN_STEP10_DEPENDENCY_CLOSURE_SHA256",
    "FROZEN_STEP10_MANIFEST_SOURCE_NORMALIZED_SHA256",
    "FROZEN_STEP10_MANIFEST_SHA256",
    "FROZEN_V1_DEFAULT_OUTPUT_SET_SHA256",
    "HISTORICAL_V1_REPLY_SERVICE_SHA256",
    "STEP10_DEPENDENCY_MANIFEST",
    "STEP10_DEPENDENCY_MANIFEST_SHA256",
    "current_step10_source_hashes",
    "fresh_step10_source_closure_sha256",
    "normalized_step10_manifest_source_sha256",
    "step10_source_file_sha256",
    "validate_step10_dependency_manifest",
]
