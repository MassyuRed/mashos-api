#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Generate the disabled CMEE V1-A private Product-Read packet.

Stdout is body-free. Full synthetic input and generated text are written only
to an explicitly selected private output.  The Step-3 early actual path
publishes its exact3 output as one atomically committed run directory, so a
process interruption cannot expose a partially committed result set.
"""

import argparse
import base64
import binascii
import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from typing import Any, Mapping


AI_ROOT = Path(__file__).resolve().parents[1]
AI_INFERENCE = AI_ROOT / "services" / "ai_inference"
if str(AI_INFERENCE) not in sys.path:
    sys.path.insert(0, str(AI_INFERENCE))

from emlis_ai_current_input_bundle import build_emlis_current_input_bundle  # noqa: E402
from emlis_ai_grounded_observation_plan import (  # noqa: E402
    build_final_stage1_grounded_observation_plan,
)
from cocolon_meaning_experience_engine import GenerationRequest, MeaningExperienceEngine  # noqa: E402
import cocolon_meaning_experience_engine.emlis_stage1_composition as stage1_composition  # noqa: E402
import cocolon_meaning_experience_engine.emlis_stage1_response as stage1_response  # noqa: E402
from cocolon_meaning_experience_engine.contracts import (  # noqa: E402
    AttachmentAdmission,
    CMEE_COMMON_GUARD_PROOF_VERSION,
    CMEE_STAGE1_TRACE_EXTENSION_SCHEMA_VERSION,
    CMEE_TERMINAL_GENERATED_DISABLED,
    CommonGuardProof,
    CommonGuardResultProof,
    EmlisStage1PositiveTraceExtension,
    EmlisTraceClaimDomain,
    EpistemicState,
    ExperiencePlan,
    GenerationArtifactBundle,
    GroundedMeaningGraph,
    MeaningNode,
    OwnerClass,
    ResolverResolution,
    SourceOwnerDisposition,
    VisibleAuthority,
    VisibleUnitTrace,
    VisibleUnknownUnit,
)
from cocolon_meaning_experience_engine.emlis_v1a import (  # noqa: E402
    COMMON_GUARD_STABILIZATION_CORE_ID,
    COMMON_GUARD_STABILIZATION_PHASE,
    COMMON_GUARD_STABILIZATION_REPORT_NAME,
    EXPECTED_COMMON_GUARD_IDS,
    REALIZER_CONTRACT_IDS,
    TRUST_POLICY_IDS,
    _build_experience_plan,
    _build_graph,
    _common_guard_proof_id,
    _ordered,
    _planned_visible_source_ids,
)
from cocolon_meaning_experience_engine.source_kernel import freeze_text_source  # noqa: E402


EXACT8: tuple[tuple[str, str, str, str, str], ...] = (
    ("SX-01", "疲れているけれど、少し整えたい気持ちもある。", "生活", "自己理解", "medium"),
    ("SX-02", "続けたいのに限界が近い感じがある。", "仕事", "不安", "medium"),
    (
        "SX-03",
        "今日は仕事の話を受けたあと、納得したい気持ちと引っかかりが残っている。",
        "仕事",
        "自己理解",
        "medium",
    ),
    (
        "SX-04",
        "だるいし何もしたくない。相談したいけど迷惑かもしれない。",
        "健康",
        "不安",
        "strong",
    ),
    ("SX-05", "環境を変えたいけど変えられなくて疲れた。", "生活", "不安", "medium"),
    (
        "SX-06",
        "変えたいのに動けなくて疲れた。ずっとこのままなのが不安で、どうしたらいいのか考えている。",
        "生活",
        "不安",
        "strong",
    ),
    (
        "SX-07",
        "この職場でやっていけるか不安。でも、続けられる形は探したい。",
        "仕事",
        "不安",
        "medium",
    ),
    (
        "SX-08",
        "今日は仕事で疲れたけど、帰ってから少し散歩したら落ち着いた。",
        "生活",
        "平穏",
        "medium",
    ),
)

# Public-safe early inputs are review material, not expected-output fixtures.
# Their family labels remain outside every production request and selector.
EARLY_KNOWN_EXACT4: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "tension",
        "続けたい気持ちはある。でも、もうかなり無理をしている気もする。",
        "生活",
        "不安",
        "medium",
    ),
    (
        "temporal_change",
        "散歩に出たら、少し落ち着いた。ただ、いつもそうなるとは思っていない。",
        "生活",
        "不安",
        "medium",
    ),
    (
        "help_seeking",
        "相談したい。でも、迷惑かもしれないと思うと切り出せない。",
        "生活",
        "不安",
        "medium",
    ),
    (
        "unfinished",
        "仕事の話はした。でも、まだ気持ちが残っていて、どうしたいかは分からない。",
        "生活",
        "不安",
        "medium",
    ),
)
EARLY_STRUCTURAL_FAMILIES = tuple(row[0] for row in EARLY_KNOWN_EXACT4)
EARLY_WITHHELD_INPUT_SCHEMA_VERSION = (
    "cocolon.cmee.stage1.withheld_early_input.v1"
)
EARLY_FROZEN_WITHHELD_INPUT_RAW_SHA256 = (
    "af718e82a6d9ed4e476f6d6b85f297272eef4790e1809cb6566d427e1f588a57"
)
EARLY_FROZEN_WITHHELD_SET_DIGEST = (
    "489dcf8763ff95893fd67030422e5af24f391d5f9594b899486749da3dbcc6a7"
)
EARLY_KNOWN_VISIBLE_SCHEMA_VERSION = (
    "cocolon.cmee.stage1.known_early_actual_visible.v1"
)
EARLY_WITHHELD_BODY_FREE_SCHEMA_VERSION = (
    "cocolon.cmee.stage1.withheld_early_machine_body_free.v2"
)
EARLY_BODY_FREE_PACKET_SCHEMA_VERSION = (
    "cocolon.cmee.stage1.early_actual_body_free.v4"
)
EARLY_HUMAN_READ_RESULT_SCHEMA_VERSION = (
    "cocolon.cmee.stage1.early_human_read_result.v4"
)
EARLY_ULTRA_KNOWN_TECHNICAL_RESULT_SCHEMA_VERSION = (
    "cocolon.cmee.stage1.early_ultra_known_technical_result.v5"
)
EARLY_ACTUAL_FINAL_BODY_FREE_SCHEMA_VERSION = (
    "cocolon.cmee.stage1.early_actual_final_body_free.v6"
)
EARLY_PRIVATE_PACKET_SCHEMA_VERSION = (
    "cocolon.cmee.stage1.withheld_early_private_packet.v2"
)
EARLY_PRIVATE_PACKET_BINDING_SCHEMA_VERSION = (
    "cocolon.cmee.stage1.withheld_early_binding.v2"
)
EARLY_RUN_EXACT3_SCHEMA_VERSION = (
    "cocolon.cmee.stage1.early_actual_run_exact3.v1"
)
EARLY_PRIVATE_REVIEW_MASTER_SCHEMA_VERSION = (
    "cocolon.cmee.stage1.private_review_output_master.v1"
)
EARLY_PRIVATE_REVIEW_MASTER_RECEIPT_SCHEMA_VERSION = (
    "cocolon.cmee.stage1.private_review_output_master_receipt.v1"
)
EARLY_RUN_BODY_FREE_MACHINE_FILENAME = "body_free_machine.json"
EARLY_RUN_KNOWN_VISIBLE_FILENAME = "known_visible.json"
EARLY_RUN_PRIVATE_PACKET_FILENAME = "private_packet.json"
EARLY_RUN_EXACT3_FILENAMES = (
    EARLY_RUN_KNOWN_VISIBLE_FILENAME,
    EARLY_RUN_PRIVATE_PACKET_FILENAME,
    EARLY_RUN_BODY_FREE_MACHINE_FILENAME,
)
EARLY_BOUNDED_UNIT_ID = (
    "cocolon.cmee.stage1.route_a.typed_japanese.case_frame_realizer."
    "clear_alignment.20260827.v1"
)
WITHHELD_EARLY_PACKET_ID = (
    "SUCCESSOR_EARLY_LANGUAGE_CLEAR_ALIGNMENT_SET_EXACT8"
)
WITHHELD_EARLY_PRIVATE_SLOT_ID = (
    "PRIVATE_SLOT_SUCCESSOR_EARLY_LANGUAGE_CLEAR_ALIGNMENT_SET_EXACT8"
)
EARLY_ACTUAL_ATTEMPT_ID = (
    "SUCCESSOR_EARLY_LANGUAGE_CLEAR_ALIGNMENT_ATTEMPT_01"
)
EARLY_PRO_COMBINED_READ_ATTEMPT_ID = (
    "SUCCESSOR_EARLY_LANGUAGE_CLEAR_ALIGNMENT_PRO_COMBINED_READ_ATTEMPT_01"
)
EARLY_ULTRA_KNOWN_READ_ATTEMPT_ID = (
    "SUCCESSOR_EARLY_LANGUAGE_CLEAR_ALIGNMENT_ULTRA_KNOWN_READ_ATTEMPT_01"
)
EARLY_ACTUAL_RUN_DIRECTORY_NAME = EARLY_ACTUAL_ATTEMPT_ID
EARLY_ACTUAL_STAGING_DIRECTORY_NAME = (
    f".{EARLY_ACTUAL_RUN_DIRECTORY_NAME}.staging"
)
EARLY_PRIVATE_REVIEW_MASTER_ALIAS = (
    "Cocolon_CMEE_Stage1_EarlyReviewMaster_"
    f"{EARLY_ACTUAL_ATTEMPT_ID}.json"
)
EARLY_PRIVATE_REVIEW_MASTER_KIND = "EARLY_ACTUAL_EXACT3"
EARLY_PRIVATE_REVIEW_MASTER_MEMBER_MEDIA_TYPE = "application/json"
EARLY_PRIVATE_REVIEW_MASTER_READER = "PRO_ONLY"
EARLY_PRIVATE_REVIEW_MASTER_LIFECYCLE = (
    "DELETE_AFTER_I08_DECISION_DUAL_REMOTE_POSTVERIFY"
)
EARLY_KNOWN_REVIEW_AUXILIARY_SCHEMA_VERSION = (
    "cocolon.cmee.stage1.early_known_review_auxiliary.v1"
)
EARLY_KNOWN_REVIEW_AUXILIARY_RECEIPT_SCHEMA_VERSION = (
    "cocolon.cmee.stage1.early_known_review_auxiliary_receipt.v1"
)
EARLY_KNOWN_REVIEW_AUXILIARY_KIND = "EARLY_KNOWN_VISIBLE_EXACT4"
EARLY_KNOWN_REVIEW_AUXILIARY_ALIAS = (
    "Cocolon_CMEE_Stage1_EarlyKnownReviewAuxiliary_"
    f"{EARLY_ACTUAL_ATTEMPT_ID}.json"
)
EARLY_KNOWN_REVIEW_AUXILIARY_READER = "ULTRA_ONLY"
EARLY_KNOWN_REVIEW_AUXILIARY_LIFECYCLE = (
    "DELETE_AFTER_I08_DECISION_DUAL_REMOTE_POSTVERIFY"
)
EARLY_MACHINE_ACTUAL_COMPLETED_STATUS = (
    "EARLY_ACTUAL_MACHINE_COMPLETED_PENDING_REVIEW"
)
EARLY_MACHINE_ACTUAL_NONCLEAR_STATUS = "EARLY_ACTUAL_MACHINE_NONCLEAR_STOP"
EARLY_ACTUAL_REVIEWED_NONCLEAR_STATUS = (
    "EARLY_ACTUAL_REVIEWED_NONCLEAR_PENDING_TRANSITION"
)
N3_LANGUAGE_CORE_IDENTITY = (
    "fc337cc7712d461d594dd8ec45ec46da10939a8d18dedc3fc4cf9246fe6a5f3d"
)
N3_RUNTIME_INTEGRATION_IDENTITY = (
    "8f9eb006847beb24446cacb64228c70ef7852a2e7cc364913e6876a99a9f8e3d"
)
# Compatibility names remain public to the existing body-free serializers;
# they resolve only to the current N3 snapshot and never to predecessor bytes.
STEP2_FROZEN_LANGUAGE_CORE_IDENTITY = N3_LANGUAGE_CORE_IDENTITY
STEP3_FROZEN_STAGE1_RUNTIME_INTEGRATION_IDENTITY = (
    N3_RUNTIME_INTEGRATION_IDENTITY
)
PREDECESSOR_EARLY_NONREUSE_RECORD = (
    ("schema_version", "cocolon.cmee.stage1.predecessor_nonreuse.v1"),
    (
        "bounded_unit_id",
        "cocolon.cmee.stage1.additional_correction.route_a.20260824.v1",
    ),
    ("packet_id", "CMEE_STAGE1_WITHHELD_EARLY_DURABLE_20260826_V2"),
    ("private_slot_id", "PRIVATE_SLOT_WITHHELD_EARLY_DURABLE_20260826_V2"),
    ("attempt_id", "CMEE_STAGE1_STEP3_3_ATTEMPT_01"),
    ("pro_read_attempt_id", "EARLY_PRO_COMBINED_READ_ATTEMPT_01"),
    ("ultra_read_attempt_id", "EARLY_ULTRA_KNOWN_READ_ATTEMPT_01"),
    ("runtime_activation_head", "3d6f3499190f1465e57cdb102e1937d095cdd457"),
    ("design_activation_head", "f46159ec204e3bf4b204896d1e39947d58d872c2"),
    (
        "language_core_identity",
        "ab4a6b5612a3912e9789ef1cc0983ce4f37a0e0657b76f49b430b1baea8755a2",
    ),
    (
        "runtime_integration_identity",
        "49da471397d19828b4a2e8326f76d4309e7d36a716221a1a91e1959f4b44a91d",
    ),
    ("run_retry_rerun", (1, 0, 0)),
    ("machine_known_withheld", ("CLEAR", "CLEAR")),
    ("ultra_result", "NOT_CLEAR"),
    ("pro_result", "COMMON_DEFECT"),
    ("terminal", "COMMON_DEFECT_RETURN_BUDGET_EXHAUSTED_STOP"),
    ("correction_counter", "2_OF_2_IMMUTABLE"),
    ("attempt_output_read_reuse_allowed", False),
)
N3_LANGUAGE_PAYLOAD_NAME_SHA256_BYTE_COUNT_EXACT16 = (
    ("language_core_source_owner_ast:ai/services/ai_inference/cocolon_meaning_experience_engine/emlis_stage1_composition.py", "94830072dd48f9cda3ca4b80838dd04138890a23acc0f348973ff5cffe95c6d2", 1133688),
    ("language_core_source_owner_ast:ai/services/ai_inference/cocolon_meaning_experience_engine/contracts.py", "48a312c9019aaa4d8ffb150163c57f8bf6c28028f16afd190eca1b55aa31cb01", 767466),
    ("language_core_source_owner_ast:ai/services/ai_inference/cocolon_meaning_experience_engine/emlis_stage1_response.py", "0224e2578b2544e2f4f0b4a87a446927a5d64c7d14a5e0a10738b8c55fa3c7d3", 442538),
    ("language_core_source_owner_ast:ai/services/ai_inference/cocolon_meaning_experience_engine/emlis_v1a.py", "8c6ed267db55cc87751d3f75fc39eb7678224266595c175b5d216518d004e8ca", 712544),
    ("language_core_source_owner_ast:ai/services/ai_inference/emlis_ai_grounded_observation_plan.py", "2fd50144fb65e9ff7d3dfd163c71f6ac6691e04d608ae70d6082d93ef577da07", 900661),
    ("language_core_source_owner_ast:ai/services/ai_inference/cocolon_text_generation_core/composer.py", "8b6c361506f5efe3d508a8ea0685524baa2c092fb149fa04718242afaf524e43", 21822),
    ("language_core_source_owner_ast:ai/services/ai_inference/cocolon_text_generation_core/adapters/emlis_observation_composer.py", "19ec812e35ecbb70661c66156cd6609e2dc813016b7358f290db04cab09de64f", 90077),
    ("language_core_contract_manifest", "01a0727258de897242262ef5d05851a040bc8b4c4694c7126d744e85c0de66e0", 183448),
    ("case_frame_and_particle_manifest", "838767e83ab7f34e955bab4ed5e9efd07e238a6a74c5024ea644e70af1cd3cf1", 14076),
    ("predicate_sense_and_atomic_head_manifest", "7db3d6c83e24a364e701af35c84ec68b7f36ff24acbe5c6f2b9020dfbbc96774", 8097),
    ("source_complement_reference_manifest", "b60f13b6f253cfb94d759d8b0ade9d3ea6c7fd6786a964886cf02037ab2d4d40", 25759),
    ("morphology_link_functional_manifest", "9a0b927f1a8239024a2d97351277412fed65e1975408de1328411ac2e1ae2ea9", 7408),
    ("participant_structural_manifest", "cee6c2989896f8e3f3642f98a354ea294d34b05eff81a2322fcb94ce9fc9abba", 774),
    ("policy_and_closed_enum_manifest", "ed64aa5ca1e92121f4098bfc7c855646c904ff6d4d599d31edb1522fdaf7f973", 20889),
    ("normal_form_and_profile_manifest", "3c14b8eb9e5cd8ff5410ffc7c1a0d3558784a75f8c355c272904dc650dd50ff7", 4055),
    ("product_causal_owner_and_registry_digests_manifest", "805deae2406958a3ea3a3d9aaaeecd4a186489c50c2b8edd82101943f3789e04", 5956),
)
N3_RUNTIME_PAYLOAD_NAME_SHA256_BYTE_COUNT_EXACT16 = (
    ("ai/services/ai_inference/cocolon_meaning_experience_engine/emlis_stage1_composition.py", "a0d243595ad95d434bac88d6a08ddfc356f4ec6e19799dd3c5c58ec3a1ec3ada", 523147),
    ("ai/services/ai_inference/cocolon_meaning_experience_engine/contracts.py", "239533f7514fb516185aebc61ebfb076c3fe24aaffca8d78cca734e8dc203777", 284967),
    ("ai/services/ai_inference/cocolon_meaning_experience_engine/emlis_stage1_response.py", "b6d64dc15fc93d4a3e99d608778fa32cc462af3efb24e52f9d703aafa40f7a75", 325262),
    ("ai/services/ai_inference/cocolon_meaning_experience_engine/emlis_v1a.py", "c907af7a059f802120b3e494a88651015a14d45c5e272ab1f9d3f1e9bfa8d06f", 293740),
    ("ai/services/ai_inference/emlis_ai_grounded_observation_plan.py", "efb08a5f49d6c3452a8f2332c9d45cebcb5e91ed2c8e8c41fa5a06b3faa4fadd", 352379),
    ("ai/services/ai_inference/cocolon_text_generation_core/composer.py", "e524111597d75599b0550b271a3df464df4d468aec28e608ab4586b7840da1f0", 8179),
    ("ai/services/ai_inference/cocolon_text_generation_core/adapters/emlis_observation_composer.py", "3ca31fbcf0ad9c93bdd4d267a3ef2000ce79b8d702bd7188f020eb11d5bd593c", 25495),
    *N3_LANGUAGE_PAYLOAD_NAME_SHA256_BYTE_COUNT_EXACT16[7:],
)
N3_LANGUAGE_PAYLOAD_TUPLE_SHA256 = (
    "f29ab019e5bb1d36617157a5f141c9c11adf8f52109e16665364573fe613e565"
)
N3_RUNTIME_PAYLOAD_TUPLE_SHA256 = (
    "fdf5f722513485b9f8e9718512915eb12d76f03b05ec94bc9180826cdacfb726"
)
N3_SOURCE_OWNER_PAYLOAD_EXACT7_TUPLE_SHA256 = (
    "4c959b6ba61ff5135417e91d296d0291e4e246183040c3f639afab9d8694dbfe"
)
N3_SOURCE_OWNER_SYMBOL_SET_SHA256 = (
    "c3baf89b8810fc71c4468aa0f00262fc2626febccb12f9bece049cdd6ba85e58"
)
N3_SOURCE_OWNER_DECLARATION_COUNTS_EXACT7 = (260, 238, 97, 180, 251, 5, 39)
N3_SOURCE_OWNER_IMPORT_COUNTS_EXACT7 = (99, 14, 91, 70, 36, 25, 19)
N3_PRODUCT_CAUSAL_OWNER_MANIFEST_SHA256 = (
    "c499a7b048dac5afc6e81fc7b44564c25d110b1c4d1e86b8507015133e81de3c"
)
N3_BEHAVIOR_ROOT_EXACT28_SHA256 = (
    "e2484757b2e834ea27febec130cacff36deb2df9ddc15a66f25f38708aec0606"
)
N3_IDENTITY_INFRASTRUCTURE_EXACT5_SHA256 = (
    "1df267709164af1ce8e3ee443eddad14c83efa132bb1cf87492ab8cccf9f9c27"
)
IM03_WORKING_LANGUAGE_CORE_IDENTITY = (
    "a9d045889bd860c4aca8bf51c7a461ff5cb8baec3e216ef68842e5e43a5d990c"
)
IM03_WORKING_RUNTIME_INTEGRATION_IDENTITY = (
    "7a566130463f63e0906af70e18914206e61d15eff25f46d30b268f79cd03f20b"
)
IM03_WORKING_LANGUAGE_PAYLOAD_NAME_SHA256_BYTE_COUNT_EXACT17 = (
    ("language_core_source_owner_ast:ai/services/ai_inference/cocolon_meaning_experience_engine/emlis_stage1_composition.py", "3c84ec5489c7a42238991c3327b85e91bccd2784f45eba986b6e4682b4e3d214", 1158935),
    ("language_core_source_owner_ast:ai/services/ai_inference/cocolon_meaning_experience_engine/contracts.py", "23f88c8ea5bdf7731b085cb129b265aad5a91cf9a127ad883352c12b195027ce", 1805832),
    ("language_core_source_owner_ast:ai/services/ai_inference/cocolon_meaning_experience_engine/emlis_stage1_response.py", "88056e3c96337f3aab7eeb9ab47a1a9354aed11cbe7cd663ec276a4d0f9c9a66", 527687),
    ("language_core_source_owner_ast:ai/services/ai_inference/cocolon_meaning_experience_engine/emlis_v1a.py", "8c6ed267db55cc87751d3f75fc39eb7678224266595c175b5d216518d004e8ca", 712544),
    ("language_core_source_owner_ast:ai/services/ai_inference/emlis_ai_grounded_observation_plan.py", "2fd50144fb65e9ff7d3dfd163c71f6ac6691e04d608ae70d6082d93ef577da07", 900661),
    ("language_core_source_owner_ast:ai/services/ai_inference/cocolon_text_generation_core/composer.py", "8b6c361506f5efe3d508a8ea0685524baa2c092fb149fa04718242afaf524e43", 21822),
    ("language_core_source_owner_ast:ai/services/ai_inference/cocolon_text_generation_core/adapters/emlis_observation_composer.py", "19ec812e35ecbb70661c66156cd6609e2dc813016b7358f290db04cab09de64f", 90077),
    ("language_core_source_owner_ast:ai/services/ai_inference/cocolon_meaning_experience_engine/emlis_input_specific_meaning.py", "b603514b0788bad34db52da7339c59d08bc85eec2c78b776625d02531ff375d7", 478409),
    ("language_core_contract_manifest", "5ff427fc41fd31ad508ae7d1315b71dbd084c9b58bf47c58470f1070363f36ff", 199530),
    ("case_frame_and_particle_manifest", "838767e83ab7f34e955bab4ed5e9efd07e238a6a74c5024ea644e70af1cd3cf1", 14076),
    ("predicate_sense_and_atomic_head_manifest", "7db3d6c83e24a364e701af35c84ec68b7f36ff24acbe5c6f2b9020dfbbc96774", 8097),
    ("source_complement_reference_manifest", "b60f13b6f253cfb94d759d8b0ade9d3ea6c7fd6786a964886cf02037ab2d4d40", 25759),
    ("morphology_link_functional_manifest", "9a0b927f1a8239024a2d97351277412fed65e1975408de1328411ac2e1ae2ea9", 7408),
    ("participant_structural_manifest", "cee6c2989896f8e3f3642f98a354ea294d34b05eff81a2322fcb94ce9fc9abba", 774),
    ("policy_and_closed_enum_manifest", "9a6c96d121fa0b3e4b41b6431d12ccaac57ad558de78836669dd1ad94e22b56e", 21233),
    ("normal_form_and_profile_manifest", "3c14b8eb9e5cd8ff5410ffc7c1a0d3558784a75f8c355c272904dc650dd50ff7", 4055),
    ("product_causal_owner_and_registry_digests_manifest", "c776dbc37aa2452d74bddba2b2c02a36daed6aa7a077bf72055be5ad8bc5e839", 6646),
)
IM03_WORKING_RUNTIME_PAYLOAD_NAME_SHA256_BYTE_COUNT_EXACT17 = (
    ("ai/services/ai_inference/cocolon_meaning_experience_engine/emlis_stage1_composition.py", "529ee5df05c8c1eace34bae265236e279440628766eb93a1f87dcdaef7917c04", 538801),
    ("ai/services/ai_inference/cocolon_meaning_experience_engine/contracts.py", "ea9aaa705ef79522b158041d6eaee4f82fc33a60c67f478c0c1462e809e4c22b", 715016),
    ("ai/services/ai_inference/cocolon_meaning_experience_engine/emlis_stage1_response.py", "f5e8f742307c7ddfcda4268b8034fbbb1b435c7e1b721e484165850c46e5da94", 361023),
    ("ai/services/ai_inference/cocolon_meaning_experience_engine/emlis_v1a.py", "c907af7a059f802120b3e494a88651015a14d45c5e272ab1f9d3f1e9bfa8d06f", 293740),
    ("ai/services/ai_inference/emlis_ai_grounded_observation_plan.py", "efb08a5f49d6c3452a8f2332c9d45cebcb5e91ed2c8e8c41fa5a06b3faa4fadd", 352379),
    ("ai/services/ai_inference/cocolon_text_generation_core/composer.py", "e524111597d75599b0550b271a3df464df4d468aec28e608ab4586b7840da1f0", 8179),
    ("ai/services/ai_inference/cocolon_text_generation_core/adapters/emlis_observation_composer.py", "3ca31fbcf0ad9c93bdd4d267a3ef2000ce79b8d702bd7188f020eb11d5bd593c", 25495),
    ("ai/services/ai_inference/cocolon_meaning_experience_engine/emlis_input_specific_meaning.py", "4f8e56c9f7f04d54d54ad908c81f40a85d5cb6215dbdfcea8c13652f95b4042b", 193615),
    ("language_core_contract_manifest", "5ff427fc41fd31ad508ae7d1315b71dbd084c9b58bf47c58470f1070363f36ff", 199530),
    ("case_frame_and_particle_manifest", "838767e83ab7f34e955bab4ed5e9efd07e238a6a74c5024ea644e70af1cd3cf1", 14076),
    ("predicate_sense_and_atomic_head_manifest", "7db3d6c83e24a364e701af35c84ec68b7f36ff24acbe5c6f2b9020dfbbc96774", 8097),
    ("source_complement_reference_manifest", "b60f13b6f253cfb94d759d8b0ade9d3ea6c7fd6786a964886cf02037ab2d4d40", 25759),
    ("morphology_link_functional_manifest", "9a0b927f1a8239024a2d97351277412fed65e1975408de1328411ac2e1ae2ea9", 7408),
    ("participant_structural_manifest", "cee6c2989896f8e3f3642f98a354ea294d34b05eff81a2322fcb94ce9fc9abba", 774),
    ("policy_and_closed_enum_manifest", "9a6c96d121fa0b3e4b41b6431d12ccaac57ad558de78836669dd1ad94e22b56e", 21233),
    ("normal_form_and_profile_manifest", "3c14b8eb9e5cd8ff5410ffc7c1a0d3558784a75f8c355c272904dc650dd50ff7", 4055),
    ("product_causal_owner_and_registry_digests_manifest", "c776dbc37aa2452d74bddba2b2c02a36daed6aa7a077bf72055be5ad8bc5e839", 6646),
)
IM03_WORKING_LANGUAGE_PAYLOAD_TUPLE_SHA256 = (
    "70007aec0a1613e841ec5ec202b77621c8198d47e38b649e04cd4a32cbf3ddb5"
)
IM03_WORKING_RUNTIME_PAYLOAD_TUPLE_SHA256 = (
    "55d90e4485802027fc4db63c0545fac805bf053279424ebd1eecab089a5bf523"
)
IM03_WORKING_SOURCE_OWNER_PAYLOAD_EXACT8_TUPLE_SHA256 = (
    "620b0d67685d13891b99fcc5e1a0f577bd6cdd58172237da1943d9bf699646a1"
)
IM03_WORKING_SOURCE_OWNER_SYMBOL_SET_SHA256 = (
    "e7c4a1fb7289bd171b8ab3802f3da94411dea2c366ab689157e33205dd1eb727"
)
IM03_WORKING_SOURCE_OWNER_DECLARATION_COUNTS_EXACT8 = (
    260, 462, 109, 180, 251, 5, 39, 89,
)
IM03_WORKING_SOURCE_OWNER_IMPORT_COUNTS_EXACT8 = (
    119, 17, 132, 70, 36, 25, 19, 94,
)
IM03_WORKING_PRODUCT_CAUSAL_OWNER_MANIFEST_SHA256 = (
    "cc3017e9cef7e5e679a23a81bd78a6fcf2810a4a374db97062c76572ad6a6e9d"
)
IM03_WORKING_BEHAVIOR_ROOT_EXACT35_SHA256 = (
    "53945aaccaf175b7adf9482ee38e4dfce754e6d7651ed4d65a131b54d8b6c297"
)
IM03_WORKING_IDENTITY_INFRASTRUCTURE_EXACT5_SHA256 = (
    "1df267709164af1ce8e3ee443eddad14c83efa132bb1cf87492ab8cccf9f9c27"
)
N4_ACTIVATION_OWNER_SYMBOL_SET_EXACT2 = (
    (
        "ai/services/ai_inference/cocolon_meaning_experience_engine/emlis_stage1_response.py",
        "compile_stage1_response",
    ),
    (
        "ai/services/ai_inference/cocolon_meaning_experience_engine/emlis_v1a.py",
        "build_text_grounded_limited_artifact",
    ),
)
N4_ACTIVATION_OWNER_SYMBOL_SET_EXACT2_SHA256 = (
    "1eb7baf3fcc2673f0d73ecf1663f140baa955967a4e3066e54913b978f9d9e79"
)
EARLY_HUMAN_READ_RESULTS = (
    "CLEAR",
    "COMMON_DEFECT",
    "ROUTE_LEVEL_CEILING",
)
EARLY_ULTRA_KNOWN_TECHNICAL_RESULTS = (
    "CLEAR",
    "NOT_CLEAR",
)
EARLY_COMMON_DEFECT_CAUSE_COMPONENTS = (
    "SUBJECTIVE_MEANING_PLANNER",
    "DISCOURSE_PLANNER",
    "RESPONSE_OBJECT_EXPRESSION",
    "GROUNDED_JAPANESE_COMPOSER",
    "WHOLE_ARTIFACT_NORMALIZER",
)
EARLY_COMMON_DEFECT_CLASSES = (
    "SURFACE_SEAM",
    "SAME_FAMILY_CONCENTRATION",
    "GENERIC_SUBJECTIVE_CONTENT",
    "NON_IDIOMATIC_SURFACE",
)
EARLY_ROUTE_LEVEL_CEILING_REASONS = (
    "CASE_OR_PHRASE_FAMILY_RULE_REQUIRED",
    "FINISHED_SENTENCE_REQUIRED",
    "NEW_ENUM_OR_AXIS_REQUIRED",
    "NEW_ASSET_FAMILY_REQUIRED",
    "LISTED_OUTSIDE_PATH_OR_EXTERNAL_DEPENDENCY_REQUIRED",
    "TYPED_PROFILE_CANNOT_RESOLVE_IDIOMATICITY",
)

STAGE1_KAREN_DERIVED_MUTATION_SET_ID = (
    "STAGE1_KAREN_DERIVED_MUTATION_SET_V1"
)
STAGE1_KAREN_DERIVED_AFTER_PACKET_ID = (
    "CMEE_STAGE1_KAREN_DERIVED_AFTER_EXACT8_20260823_V2"
)
STAGE1_KAREN_DERIVED_AFTER_PRIVATE_SLOT_ID = (
    "PRIVATE_SLOT_AFTER_EXACT8_20260823_V2"
)
STAGE1_KAREN_DERIVED_MUTATION_SET_V1: tuple[
    tuple[str, str, str], ...
] = (
    ("KDM-SE-01", "SEMANTIC_EQUIVALENCE_MUTATION", "REGISTER_INFLECTION"),
    ("KDM-SE-02", "SEMANTIC_EQUIVALENCE_MUTATION", "LEXICAL_PARAPHRASE"),
    ("KDM-SE-03", "SEMANTIC_EQUIVALENCE_MUTATION", "CLAUSE_ORDER"),
    ("KDM-RC-01", "RELATION_CONTRAST_MUTATION", "TEMPORAL_ORDER"),
    ("KDM-RC-02", "RELATION_CONTRAST_MUTATION", "COEXISTENCE_TENSION"),
    ("KDM-RC-03", "RELATION_CONTRAST_MUTATION", "SEQUENCE_CAUSE"),
    ("KDM-CB-01", "CLAIM_BOUNDARY_MUTATION", "NEGATION"),
    ("KDM-CB-02", "CLAIM_BOUNDARY_MUTATION", "MODALITY"),
    ("KDM-CB-03", "CLAIM_BOUNDARY_MUTATION", "EXPERIENCER"),
    ("KDM-CB-04", "CLAIM_BOUNDARY_MUTATION", "MATERIAL_UNRELATED"),
    ("KDM-SU-01", "SUBJECTIVITY_MUTATION", "SOURCE_STRENGTH"),
    ("KDM-SU-02", "SUBJECTIVITY_MUTATION", "DISCOMFORT_PERSON_TARGET"),
)

PRODUCT_READ_AXES = (
    "PRIMARY_MEANING_RETAINED",
    "RELATION_DIRECTION_CORRECT",
    "NO_CAUSE_PERSONALITY_DIAGNOSIS_PROMOTION",
    "UNKNOWN_BOUNDARY_PRESERVED",
    "SELF_DENIAL_NOT_ADOPTED_OR_AMPLIFIED",
    "BOUND_EMLIS_RECEPTION",
    "SECTION_SEMANTIC_DISTINCTNESS",
    "NATURAL_NON_REPETITIVE_SURFACE",
    "DISTRIBUTION_NOT_OVERCONCENTRATED",
    "DEPTH_PROPORTIONAL",
    "NO_FALSE_UNDERSTANDING_COMPLETION",
    "IMMEDIATE_OBSERVATION_FEELS_READ",
)
PRIVATE_OUTPUT_ROOT = Path(
    os.environ.get("CMEE_PRIVATE_OUTPUT_ROOT", "/tmp/cocolon-cmee-v1a-private")
).resolve()
CHECKOUT_ROOT = AI_ROOT.parent.resolve()


def _body_free_mutation_registry() -> dict[str, Any]:
    expected_classes = (
        ("SEMANTIC_EQUIVALENCE_MUTATION", 3),
        ("RELATION_CONTRAST_MUTATION", 3),
        ("CLAIM_BOUNDARY_MUTATION", 4),
        ("SUBJECTIVITY_MUTATION", 2),
    )
    case_ids = tuple(row[0] for row in STAGE1_KAREN_DERIVED_MUTATION_SET_V1)
    if (
        len(STAGE1_KAREN_DERIVED_MUTATION_SET_V1) != 12
        or len(case_ids) != len(set(case_ids))
        or any(
            sum(row[1] == class_name for row in STAGE1_KAREN_DERIVED_MUTATION_SET_V1)
            != expected_count
            for class_name, expected_count in expected_classes
        )
    ):
        raise RuntimeError("stage1_mutation_registry_invalid")
    return {
        "set_id": STAGE1_KAREN_DERIVED_MUTATION_SET_ID,
        "case_count": len(STAGE1_KAREN_DERIVED_MUTATION_SET_V1),
        "body_payload_present": False,
        "runner_executes_source_bodies": False,
        "execution_owner": "current_and_new_tests",
        "class_counts": {
            class_name: expected_count
            for class_name, expected_count in expected_classes
        },
        "cases": [
            {
                "case_id": case_id,
                "mutation_class": mutation_class,
                "mutation_operator": mutation_operator,
            }
            for case_id, mutation_class, mutation_operator
            in STAGE1_KAREN_DERIVED_MUTATION_SET_V1
        ],
    }


def _raw(case_id: str, memo: str, category: str, emotion: str, strength: str) -> dict[str, Any]:
    return {
        "id": f"cmee-i1sx-{case_id.lower()}",
        "created_at": "2026-08-15T00:00:00Z",
        "memo": memo,
        "memo_action": "",
        "category": [category],
        "emotion_details": [{"type": emotion, "strength": strength}],
        "emotions": [emotion],
        "is_secret": False,
    }


def _valid_ref_tuple(value: object, *, allow_empty: bool = False) -> bool:
    return (
        type(value) is tuple
        and (allow_empty or bool(value))
        and all(type(ref) is str and bool(ref) for ref in value)
        and len(value) == len(set(value))
    )


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_sha256(value: object) -> str:
    return _sha256_text(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )


def _pretty_json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")


def _canonical_json_line_bytes(value: object) -> bytes:
    """Serialize one closed artifact deterministically with a final newline."""

    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )


def _canonical_whitespace_text(value: str) -> str:
    return " ".join(value.split())


def _validate_early_repo_heads(
    *,
    runtime_repo_head: str,
    design_repo_head: str,
) -> None:
    # The runtime head is additionally verified against this clean checkout
    # by the CLI preflight.  The design head belongs to the separate design
    # repository and remains an externally postverified preflight attestation.
    if any(
        re.fullmatch(r"[0-9a-f]{40}", head) is None
        for head in (runtime_repo_head, design_repo_head)
    ):
        raise ValueError("early private packet repo head binding invalid")


def _validate_early_runtime_checkout(runtime_repo_head: str) -> None:
    """Bind the runtime activation head to a clean local tracked tree."""

    if re.fullmatch(r"[0-9a-f]{40}", runtime_repo_head) is None:
        raise ValueError("early runtime checkout preflight invalid")
    try:
        head = subprocess.run(
            ("git", "rev-parse", "--verify", "HEAD"),
            cwd=CHECKOUT_ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        tracked_status = subprocess.run(
            (
                "git",
                "status",
                "--porcelain=v1",
                "--untracked-files=no",
            ),
            cwd=CHECKOUT_ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        raise ValueError("early runtime checkout preflight invalid") from None
    if (
        head.returncode != 0
        or head.stderr
        or head.stdout.strip() != runtime_repo_head
        or tracked_status.returncode != 0
        or tracked_status.stderr
        or tracked_status.stdout != ""
    ):
        raise ValueError("early runtime checkout preflight invalid")


def _validate_withheld_early_payload(
    payload: object,
) -> tuple[dict[str, str], ...]:
    """Validate the private exact4 without retaining any caller identity field."""

    expected_root_keys = {
        "schema_version",
        "selection_frozen_before_first_after",
        "synthetic_non_identifying",
        "cases",
    }
    if type(payload) is not dict or set(payload) != expected_root_keys:
        raise ValueError("withheld early private input invalid")
    if (
        payload["schema_version"] != EARLY_WITHHELD_INPUT_SCHEMA_VERSION
        or payload["selection_frozen_before_first_after"] is not True
        or payload["synthetic_non_identifying"] is not True
        or type(payload["cases"]) is not list
        or len(payload["cases"]) != len(EARLY_STRUCTURAL_FAMILIES)
    ):
        raise ValueError("withheld early private input invalid")

    expected_case_keys = {
        "structural_family",
        "memo",
        "category",
        "emotion",
        "strength",
    }
    rows: list[dict[str, str]] = []
    for row in payload["cases"]:
        if type(row) is not dict or set(row) != expected_case_keys:
            raise ValueError("withheld early private input invalid")
        if any(type(row[key]) is not str or not row[key] for key in expected_case_keys):
            raise ValueError("withheld early private input invalid")
        if row["strength"] not in {"weak", "medium", "strong"}:
            raise ValueError("withheld early private input invalid")
        rows.append({key: row[key] for key in expected_case_keys})

    if tuple(row["structural_family"] for row in rows) != EARLY_STRUCTURAL_FAMILIES:
        raise ValueError("withheld early private input invalid")
    memos = tuple(row["memo"] for row in rows)
    canonical_memos = tuple(_canonical_whitespace_text(memo) for memo in memos)
    canonical_known_memos = {
        _canonical_whitespace_text(row[1]) for row in EARLY_KNOWN_EXACT4
    }
    if (
        any(not memo for memo in canonical_memos)
        or len(canonical_memos) != len(set(canonical_memos))
        or set(canonical_memos).intersection(canonical_known_memos)
    ):
        raise ValueError("withheld early private input invalid")
    return tuple(rows)


def _validate_frozen_withheld_early_payload(
    payload: object,
    *,
    raw_sha256: str,
) -> tuple[dict[str, str], ...]:
    """Bind the same opened bytes to both frozen V2 aggregate digests."""

    rows = _validate_withheld_early_payload(payload)
    canonical_payload = {
        "schema_version": EARLY_WITHHELD_INPUT_SCHEMA_VERSION,
        "selection_frozen_before_first_after": True,
        "synthetic_non_identifying": True,
        "cases": rows,
    }
    if (
        raw_sha256 != EARLY_FROZEN_WITHHELD_INPUT_RAW_SHA256
        or _canonical_sha256(canonical_payload)
        != EARLY_FROZEN_WITHHELD_SET_DIGEST
    ):
        raise ValueError("frozen withheld early input binding invalid")
    return rows


def _early_case_failure_summary(error: Exception) -> dict[str, Any]:
    return {
        "actual_japanese_reached": False,
        "phase_a_and_b_validated": False,
        "subjective_claim_count": 0,
        "internal_candidate_count": 0,
        "ranked_candidate_count": 0,
        "material_alternate_present": False,
        "normal_form_phase_exact6": False,
        "normal_form_defect_free": False,
        "normalization_idempotent": False,
        "required_duty_coverage_exact": False,
        "language_core_identity_match": False,
        "machine_invariant_clear": False,
        "failure_class": type(error).__name__,
    }


def _materialize_early_case(
    *,
    request_token: str,
    structural_family: str,
    memo: str,
    category: str,
    emotion: str,
    strength: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Run one case through the final Step 2 production call graph only."""

    raw = _raw(request_token, memo, category, emotion, strength)
    public_source = {
        "memo": memo,
        "category": category,
        "emotion": emotion,
        "strength": strength,
    }
    try:
        request = GenerationRequest(
            request_id=f"req-{request_token}",
            current_input_bundle=build_emlis_current_input_bundle(raw),
            expected_source_record_id=str(raw["id"]),
        )
        source = freeze_text_source(request)
        grounded_plan = build_final_stage1_grounded_observation_plan(
            source.normalized_current_input,
            evidence_spans=source.evidence_spans,
        )
        required_nuclei, required_relations, reception_targets = (
            _planned_visible_source_ids(grounded_plan)
        )
        graph = _build_graph(
            source,
            grounded_plan,
            _ordered((*required_nuclei, *reception_targets)),
            required_relations,
        )
        parent_plan = _build_experience_plan(
            source,
            graph,
            grounded_plan,
            required_nuclei,
            required_relations,
            reception_targets,
        )
        phase_a = stage1_response.build_subjective_planning_inputs(
            source=source,
            grounded_graph=graph,
            parent_plan=parent_plan,
            grounded_plan=grounded_plan,
        )
        subjective_plan = stage1_composition.project_subjective_meaning_plan(
            phase_a
        )
        projection = stage1_response.seal_stage1_projection(
            phase_a,
            subjective_plan,
        )
        phase_b = stage1_response.build_surface_composition_inputs(
            phase_a,
            projection,
        )
        result = stage1_composition.compose_stage1_from_projection(phase_b)
        ranked = result.ranked_candidates
        selected = result.selected_candidate
        units = selected.sentence_units
        selected_normalized = selected.normalized_artifact
        renormalized_ranked = tuple(
            stage1_composition.normalize_to_normal_form(
                candidate.normalized_artifact,
                candidate.normalized_artifact.layout_preference_seed,
                phase_b,
            )
            for candidate in ranked
        )
        idempotent = all(
            stage1_composition.canonical_normalized_bytes(
                candidate.normalized_artifact
            )
            == stage1_composition.canonical_normalized_bytes(repeated)
            for candidate, repeated in zip(ranked, renormalized_ranked)
        )
        realized_duties = tuple(ref for unit in units for ref in unit.duty_refs)
        required_coverage = (
            len(realized_duties) == len(set(realized_duties))
            and set(realized_duties) == set(selected_normalized.required_duty_refs)
        )
        exact6 = all(
            candidate.normalized_artifact.normalization_phase_trace
            == tuple(stage1_composition.NormalFormPhase)
            for candidate in ranked
        )
        defect_free = all(
            candidate.normalized_artifact.correctable_defect_rows == ()
            for candidate in ranked
        )
        japanese_reached = bool(units) and all(
            unit.text.endswith("。")
            and re.search(r"[ぁ-んァ-ヶ一-龯]", unit.text) is not None
            for unit in units
        )
        identity_match = (
            result.language_core_identity
            == stage1_composition.LANGUAGE_CORE_IDENTITY
            == N3_LANGUAGE_CORE_IDENTITY
        )
        ranked_count = len(ranked)
        summary = {
            "actual_japanese_reached": japanese_reached,
            "phase_a_and_b_validated": True,
            "subjective_claim_count": len(subjective_plan.subjective_claim_rows),
            "internal_candidate_count": result.internal_candidate_count,
            "ranked_candidate_count": ranked_count,
            "material_alternate_present": (
                result.internal_candidate_count >= 2 and ranked_count >= 2
            ),
            "normal_form_phase_exact6": exact6,
            "normal_form_defect_free": defect_free,
            "normalization_idempotent": idempotent,
            "required_duty_coverage_exact": required_coverage,
            "language_core_identity_match": identity_match,
            "machine_invariant_clear": all(
                (
                    japanese_reached,
                    bool(subjective_plan.subjective_claim_rows),
                    result.internal_candidate_count >= ranked_count,
                    1 <= ranked_count <= 2,
                    tuple(row.rank for row in ranked)
                    == tuple(range(1, ranked_count + 1)),
                    selected.rank == 1,
                    exact6,
                    defect_free,
                    idempotent,
                    required_coverage,
                    identity_match,
                )
            ),
            "failure_class": None,
        }
        actual_japanese = "\n".join(unit.text for unit in units)
    except Exception as error:  # The body-free surface never serializes repr(error).
        summary = _early_case_failure_summary(error)
        actual_japanese = ""

    public_case = {
        "structural_family": structural_family,
        "synthetic_input": public_source,
        "actual_japanese": actual_japanese,
        "machine_invariant": summary,
    }
    private_case = {
        "structural_family": structural_family,
        "synthetic_input_private": raw,
        "candidate_private": actual_japanese,
        "machine_invariant_body_free": summary,
    }
    return public_case, private_case


def _early_private_packet_binding(
    *,
    early_attempt_id: str,
    runtime_repo_head: str,
    design_repo_head: str,
    withheld_input_raw_sha256: str,
    withheld_set_digest: str,
    language_core_identity: str,
    stage1_runtime_integration_identity: str,
) -> dict[str, Any]:
    _validate_early_repo_heads(
        runtime_repo_head=runtime_repo_head,
        design_repo_head=design_repo_head,
    )
    material = {
        "binding_version": EARLY_PRIVATE_PACKET_BINDING_SCHEMA_VERSION,
        "packet_id": WITHHELD_EARLY_PACKET_ID,
        "bounded_unit_id": EARLY_BOUNDED_UNIT_ID,
        "early_attempt_id": early_attempt_id,
        "runtime_repo_head": runtime_repo_head,
        "design_repo_head": design_repo_head,
        "language_core_identity": language_core_identity,
        "stage1_runtime_integration_identity": (
            stage1_runtime_integration_identity
        ),
        "known_structural_families": EARLY_STRUCTURAL_FAMILIES,
        "withheld_input_raw_sha256": withheld_input_raw_sha256,
        "withheld_set_digest": withheld_set_digest,
        "runner_identity": {
            "repo_relative_path": str(
                Path(__file__).resolve().relative_to(CHECKOUT_ROOT)
            ),
            "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    return {**material, "packet_binding_sha256": _canonical_sha256(material)}


def _identity_payload_proof_rows(
    payloads: tuple[tuple[str, bytes], ...],
) -> tuple[tuple[str, str, int], ...]:
    return tuple(
        (name, hashlib.sha256(payload).hexdigest(), len(payload))
        for name, payload in payloads
    )


def _source_owner_symbol_proof(
    language_payloads: tuple[tuple[str, bytes], ...],
    *,
    source_owner_count: int = 7,
) -> tuple[tuple[int, ...], tuple[int, ...], str]:
    symbol_rows = []
    declaration_counts = []
    import_counts = []
    for _name, payload in language_payloads[:source_owner_count]:
        try:
            projected = dict(json.loads(payload))
            relative_path = projected["relative_path"]
            declaration_names = tuple(
                bound_name
                for row in projected["selected_declarations"]
                for bound_name in dict(row)["bound_names"]
            )
            import_names = tuple(
                dict(row)["bound_name"]
                for row in projected["selected_import_bindings"]
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            raise RuntimeError("early frozen owner symbol proof mismatch") from None
        symbol_rows.append(
            (relative_path, declaration_names, import_names)
        )
        declaration_counts.append(len(declaration_names))
        import_counts.append(len(import_names))
    return (
        tuple(declaration_counts),
        tuple(import_counts),
        _canonical_sha256(tuple(symbol_rows)),
    )


def _current_frozen_early_identity_pair() -> tuple[str, str]:
    """Return the exact N3 pair only after the full I05 proof matches."""

    language_payloads = stage1_composition.language_core_identity_payloads()
    runtime_payloads = (
        stage1_composition.stage1_runtime_integration_identity_payloads()
    )
    language_payload_rows = _identity_payload_proof_rows(language_payloads)
    runtime_payload_rows = _identity_payload_proof_rows(runtime_payloads)
    (
        declaration_counts,
        import_counts,
        source_owner_symbol_set_sha256,
    ) = _source_owner_symbol_proof(language_payloads)
    language_core_identity = stage1_composition.compute_language_core_identity()
    stage1_runtime_integration_identity = (
        stage1_composition.compute_stage1_runtime_integration_identity()
    )
    if (
        language_payload_rows
        != N3_LANGUAGE_PAYLOAD_NAME_SHA256_BYTE_COUNT_EXACT16
        or runtime_payload_rows
        != N3_RUNTIME_PAYLOAD_NAME_SHA256_BYTE_COUNT_EXACT16
        or _canonical_sha256(language_payload_rows)
        != N3_LANGUAGE_PAYLOAD_TUPLE_SHA256
        or _canonical_sha256(runtime_payload_rows)
        != N3_RUNTIME_PAYLOAD_TUPLE_SHA256
        or _canonical_sha256(language_payload_rows[:7])
        != N3_SOURCE_OWNER_PAYLOAD_EXACT7_TUPLE_SHA256
        or declaration_counts
        != N3_SOURCE_OWNER_DECLARATION_COUNTS_EXACT7
        or import_counts != N3_SOURCE_OWNER_IMPORT_COUNTS_EXACT7
        or source_owner_symbol_set_sha256
        != N3_SOURCE_OWNER_SYMBOL_SET_SHA256
        or _canonical_sha256(
            stage1_composition.LANGUAGE_CORE_PRODUCT_CAUSAL_OWNER_MANIFEST
        )
        != N3_PRODUCT_CAUSAL_OWNER_MANIFEST_SHA256
        or _canonical_sha256(
            stage1_composition.N2_BEHAVIOR_ROOT_SYMBOL_SET_EXACT28
        )
        != N3_BEHAVIOR_ROOT_EXACT28_SHA256
        or _canonical_sha256(
            stage1_composition.N2_IDENTITY_INFRASTRUCTURE_CHANGED_SYMBOL_SET_EXACT5
        )
        != N3_IDENTITY_INFRASTRUCTURE_EXACT5_SHA256
        or _canonical_sha256(N4_ACTIVATION_OWNER_SYMBOL_SET_EXACT2)
        != N4_ACTIVATION_OWNER_SYMBOL_SET_EXACT2_SHA256
        or language_core_identity != stage1_composition.LANGUAGE_CORE_IDENTITY
        or language_core_identity != N3_LANGUAGE_CORE_IDENTITY
        or stage1_runtime_integration_identity
        != stage1_composition.STAGE1_RUNTIME_INTEGRATION_IDENTITY
        or stage1_runtime_integration_identity
        != N3_RUNTIME_INTEGRATION_IDENTITY
    ):
        raise RuntimeError("early frozen runtime identity mismatch")
    return language_core_identity, stage1_runtime_integration_identity


def _current_im03_working_identity_pair() -> tuple[str, str]:
    """Return the IM03 pair only after the exact17 proof matches."""

    language_payloads = stage1_composition.language_core_identity_payloads()
    runtime_payloads = (
        stage1_composition.stage1_runtime_integration_identity_payloads()
    )
    language_payload_rows = _identity_payload_proof_rows(language_payloads)
    runtime_payload_rows = _identity_payload_proof_rows(runtime_payloads)
    (
        declaration_counts,
        import_counts,
        source_owner_symbol_set_sha256,
    ) = _source_owner_symbol_proof(
        language_payloads,
        source_owner_count=8,
    )
    language_core_identity = stage1_composition.compute_language_core_identity()
    stage1_runtime_integration_identity = (
        stage1_composition.compute_stage1_runtime_integration_identity()
    )
    if (
        language_payload_rows
        != IM03_WORKING_LANGUAGE_PAYLOAD_NAME_SHA256_BYTE_COUNT_EXACT17
        or runtime_payload_rows
        != IM03_WORKING_RUNTIME_PAYLOAD_NAME_SHA256_BYTE_COUNT_EXACT17
        or _canonical_sha256(language_payload_rows)
        != IM03_WORKING_LANGUAGE_PAYLOAD_TUPLE_SHA256
        or _canonical_sha256(runtime_payload_rows)
        != IM03_WORKING_RUNTIME_PAYLOAD_TUPLE_SHA256
        or _canonical_sha256(language_payload_rows[:8])
        != IM03_WORKING_SOURCE_OWNER_PAYLOAD_EXACT8_TUPLE_SHA256
        or declaration_counts
        != IM03_WORKING_SOURCE_OWNER_DECLARATION_COUNTS_EXACT8
        or import_counts != IM03_WORKING_SOURCE_OWNER_IMPORT_COUNTS_EXACT8
        or source_owner_symbol_set_sha256
        != IM03_WORKING_SOURCE_OWNER_SYMBOL_SET_SHA256
        or _canonical_sha256(
            stage1_composition.LANGUAGE_CORE_PRODUCT_CAUSAL_OWNER_MANIFEST
        )
        != IM03_WORKING_PRODUCT_CAUSAL_OWNER_MANIFEST_SHA256
        or _canonical_sha256(
            stage1_composition.IM03_BEHAVIOR_ROOT_SYMBOL_SET_EXACT35
        )
        != IM03_WORKING_BEHAVIOR_ROOT_EXACT35_SHA256
        or _canonical_sha256(
            stage1_composition.N2_IDENTITY_INFRASTRUCTURE_CHANGED_SYMBOL_SET_EXACT5
        )
        != IM03_WORKING_IDENTITY_INFRASTRUCTURE_EXACT5_SHA256
        or _canonical_sha256(N4_ACTIVATION_OWNER_SYMBOL_SET_EXACT2)
        != N4_ACTIVATION_OWNER_SYMBOL_SET_EXACT2_SHA256
        or language_core_identity
        != stage1_composition.LANGUAGE_CORE_IDENTITY
        or language_core_identity != IM03_WORKING_LANGUAGE_CORE_IDENTITY
        or stage1_runtime_integration_identity
        != stage1_composition.STAGE1_RUNTIME_INTEGRATION_IDENTITY
        or stage1_runtime_integration_identity
        != IM03_WORKING_RUNTIME_INTEGRATION_IDENTITY
    ):
        raise RuntimeError("im03 working runtime identity mismatch")
    return language_core_identity, stage1_runtime_integration_identity


def _early_exact8_machine_is_clear(
    known: Mapping[str, Any],
    withheld: Mapping[str, Any],
) -> bool:
    """Apply the sole exact8 machine CLEAR predicate.

    Material alternate counts remain bounded diagnostics.  They do not
    participate in CLEAR and no alternate is generated merely to satisfy
    this aggregate gate.
    """

    known_exact4_fields = (
        "case_count",
        "actual_japanese_reached_count",
        "machine_invariant_clear_count",
    )
    withheld_exact4_fields = (
        "withheld_set_count",
        "actual_japanese_reached_count",
        "machine_invariant_clear_count",
        "normal_form_phase_exact6_count",
        "normal_form_defect_free_count",
        "normalization_idempotent_count",
        "required_duty_coverage_exact_count",
    )
    return (
        all(
            type(known.get(field)) is int and known[field] == 4
            for field in known_exact4_fields
        )
        and known.get("machine_invariant_result") == "CLEAR"
        and all(
            type(withheld.get(field)) is int and withheld[field] == 4
            for field in withheld_exact4_fields
        )
        and withheld.get("machine_failure_classes") == []
        and withheld.get("machine_invariant_result") == "CLEAR"
    )


def run_early_actual(
    *,
    withheld_private_payload: object,
    withheld_input_raw_sha256: str,
    early_attempt_id: str,
    runtime_repo_head: str,
    design_repo_head: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Materialize known exact4 plus private withheld exact4 through one core."""

    _validate_early_repo_heads(
        runtime_repo_head=runtime_repo_head,
        design_repo_head=design_repo_head,
    )
    if early_attempt_id != EARLY_ACTUAL_ATTEMPT_ID:
        raise ValueError("early actual attempt binding invalid")
    withheld_rows = _validate_frozen_withheld_early_payload(
        withheld_private_payload,
        raw_sha256=withheld_input_raw_sha256,
    )
    (
        fresh_identity,
        fresh_runtime_integration_identity,
    ) = _current_frozen_early_identity_pair()

    known_public_cases: list[dict[str, Any]] = []
    known_private_cases: list[dict[str, Any]] = []
    for index, (family, memo, category, emotion, strength) in enumerate(
        EARLY_KNOWN_EXACT4,
        start=1,
    ):
        public_case, private_case = _materialize_early_case(
            request_token=f"early-known-{index:02d}",
            structural_family=family,
            memo=memo,
            category=category,
            emotion=emotion,
            strength=strength,
        )
        known_public_cases.append(public_case)
        known_private_cases.append(private_case)

    withheld_set_digest = _canonical_sha256(
        {
            "schema_version": EARLY_WITHHELD_INPUT_SCHEMA_VERSION,
            "selection_frozen_before_first_after": True,
            "synthetic_non_identifying": True,
            "cases": withheld_rows,
        }
    )
    if withheld_set_digest != EARLY_FROZEN_WITHHELD_SET_DIGEST:
        raise RuntimeError("frozen withheld early input binding invalid")
    withheld_private_cases: list[dict[str, Any]] = []
    withheld_summaries: list[dict[str, Any]] = []
    for index, row in enumerate(withheld_rows, start=1):
        _public_case, private_case = _materialize_early_case(
            request_token=f"early-withheld-{index:02d}",
            structural_family=row["structural_family"],
            memo=row["memo"],
            category=row["category"],
            emotion=row["emotion"],
            strength=row["strength"],
        )
        withheld_private_cases.append(private_case)
        withheld_summaries.append(private_case["machine_invariant_body_free"])

    known_summaries = [row["machine_invariant"] for row in known_public_cases]
    known_clear_count = sum(row["machine_invariant_clear"] for row in known_summaries)
    withheld_clear_count = sum(
        row["machine_invariant_clear"] for row in withheld_summaries
    )
    family_counts = {
        family: sum(row["structural_family"] == family for row in withheld_rows)
        for family in EARLY_STRUCTURAL_FAMILIES
    }
    withheld_body_free = {
        "schema_version": EARLY_WITHHELD_BODY_FREE_SCHEMA_VERSION,
        "packet_id": WITHHELD_EARLY_PACKET_ID,
        "bounded_unit_id": EARLY_BOUNDED_UNIT_ID,
        "early_attempt_id": early_attempt_id,
        "language_core_identity": fresh_identity,
        "stage1_runtime_integration_identity": (
            fresh_runtime_integration_identity
        ),
        "withheld_input_raw_sha256": withheld_input_raw_sha256,
        "withheld_set_count": len(withheld_rows),
        "structural_family_counts": family_counts,
        "withheld_set_digest": withheld_set_digest,
        "selection_frozen_before_first_after": True,
        "synthetic_non_identifying_attested": True,
        "actual_japanese_reached_count": sum(
            row["actual_japanese_reached"] for row in withheld_summaries
        ),
        "machine_invariant_clear_count": withheld_clear_count,
        "normal_form_phase_exact6_count": sum(
            row["normal_form_phase_exact6"] for row in withheld_summaries
        ),
        "normal_form_defect_free_count": sum(
            row["normal_form_defect_free"] for row in withheld_summaries
        ),
        "normalization_idempotent_count": sum(
            row["normalization_idempotent"] for row in withheld_summaries
        ),
        "required_duty_coverage_exact_count": sum(
            row["required_duty_coverage_exact"] for row in withheld_summaries
        ),
        "material_alternate_case_count": sum(
            row["material_alternate_present"] for row in withheld_summaries
        ),
        "machine_failure_classes": sorted(
            {
                row["failure_class"]
                for row in withheld_summaries
                if row["failure_class"] is not None
            }
        ),
        "machine_invariant_result": (
            "CLEAR"
            if withheld_clear_count == len(withheld_rows)
            else "FAIL"
        ),
        "body_payload_present": False,
        "private_text_published": False,
        "body_full_readers": "PRO_ONLY",
        "ultra_withheld_body_access": 0,
        "mash_withheld_body_access": 0,
        "formal_exact8_denominator_effect": 0,
        "product_acceptance_denominator_effect": 0,
        "numeric_score_or_pass_rate": 0,
        "product_credit": 0,
        "candidate_ready": False,
        "production_effect": 0,
        "automatic_progression": False,
    }
    known_visible = {
        "schema_version": EARLY_KNOWN_VISIBLE_SCHEMA_VERSION,
        "case_count": len(known_public_cases),
        "structural_family_counts": {
            family: sum(
                row["structural_family"] == family for row in known_public_cases
            )
            for family in EARLY_STRUCTURAL_FAMILIES
        },
        "machine_invariant_clear_count": known_clear_count,
        "machine_invariant_result": (
            "CLEAR"
            if known_clear_count == len(known_public_cases)
            else "FAIL"
        ),
        "material_alternate_case_count": sum(
            row["material_alternate_present"] for row in known_summaries
        ),
        "cases": known_public_cases,
    }
    known_body_free = {
        "case_count": len(known_public_cases),
        "structural_family_counts": known_visible["structural_family_counts"],
        "actual_japanese_reached_count": sum(
            row["actual_japanese_reached"] for row in known_summaries
        ),
        "machine_invariant_clear_count": known_clear_count,
        "machine_invariant_result": known_visible["machine_invariant_result"],
        "material_alternate_case_count": known_visible[
            "material_alternate_case_count"
        ],
        "known_visible_packet_sha256": _canonical_sha256(known_visible),
        "body_payload_present": False,
    }
    private_packet = {
        "schema_version": EARLY_PRIVATE_PACKET_SCHEMA_VERSION,
        "packet_id": WITHHELD_EARLY_PACKET_ID,
        "private_slot_id": WITHHELD_EARLY_PRIVATE_SLOT_ID,
        "early_attempt_id": early_attempt_id,
        "withheld_input_raw_sha256": withheld_input_raw_sha256,
        "withheld_set_digest": withheld_set_digest,
        "private_body_full": True,
        "private_packet_binding": _early_private_packet_binding(
            early_attempt_id=early_attempt_id,
            runtime_repo_head=runtime_repo_head,
            design_repo_head=design_repo_head,
            withheld_input_raw_sha256=withheld_input_raw_sha256,
            withheld_set_digest=withheld_set_digest,
            language_core_identity=fresh_identity,
            stage1_runtime_integration_identity=(
                fresh_runtime_integration_identity
            ),
        ),
        "language_core_identity": fresh_identity,
        "stage1_runtime_integration_identity": (
            fresh_runtime_integration_identity
        ),
        "selection_frozen_before_first_after": True,
        "known_cases": known_private_cases,
        "withheld_cases": withheld_private_cases,
        "human_language_viability_read": {
            "body_full_readers": "PRO_ONLY",
            "early_human_read_result": None,
            "defect_class": None,
            "cause_component": None,
            "ceiling_reason": None,
        },
    }
    _validate_early_private_packet(
        private_packet,
        early_attempt_id=early_attempt_id,
        runtime_repo_head=runtime_repo_head,
        design_repo_head=design_repo_head,
        withheld_input_raw_sha256=withheld_input_raw_sha256,
        withheld_set_digest=withheld_set_digest,
        language_core_identity=fresh_identity,
        stage1_runtime_integration_identity=(
            fresh_runtime_integration_identity
        ),
        known_visible_packet=known_visible,
    )
    body_free_packet = {
        "schema_version": EARLY_BODY_FREE_PACKET_SCHEMA_VERSION,
        "exact3_schema_version": EARLY_RUN_EXACT3_SCHEMA_VERSION,
        "packet_id": WITHHELD_EARLY_PACKET_ID,
        "bounded_unit_id": EARLY_BOUNDED_UNIT_ID,
        "early_attempt_id": early_attempt_id,
        "runtime_repo_head": runtime_repo_head,
        "design_repo_head": design_repo_head,
        "language_core_identity": fresh_identity,
        "stage1_runtime_integration_identity": (
            fresh_runtime_integration_identity
        ),
        "withheld_input_raw_sha256": withheld_input_raw_sha256,
        "withheld_set_digest": withheld_set_digest,
        "known_exact4_body_free": known_body_free,
        "withheld_exact4_body_free": withheld_body_free,
        "private_packet_sha256": _canonical_sha256(private_packet),
        "early_human_read_result": "NOT_RUN",
        "early_actual_status": (
            EARLY_MACHINE_ACTUAL_COMPLETED_STATUS
            if _early_exact8_machine_is_clear(
                known_body_free,
                withheld_body_free,
            )
            else EARLY_MACHINE_ACTUAL_NONCLEAR_STATUS
        ),
        "body_payload_present": False,
        "private_text_published": False,
    }
    return body_free_packet, known_visible, private_packet


def _validate_early_private_case_summary(
    summary: object,
    *,
    candidate: object,
) -> dict[str, Any]:
    """Validate one private case's complete body-free machine summary."""

    invariant_keys = {
        "actual_japanese_reached",
        "phase_a_and_b_validated",
        "subjective_claim_count",
        "internal_candidate_count",
        "ranked_candidate_count",
        "material_alternate_present",
        "normal_form_phase_exact6",
        "normal_form_defect_free",
        "normalization_idempotent",
        "required_duty_coverage_exact",
        "language_core_identity_match",
        "machine_invariant_clear",
        "failure_class",
    }
    bool_fields = (
        "actual_japanese_reached",
        "phase_a_and_b_validated",
        "material_alternate_present",
        "normal_form_phase_exact6",
        "normal_form_defect_free",
        "normalization_idempotent",
        "required_duty_coverage_exact",
        "language_core_identity_match",
        "machine_invariant_clear",
    )
    count_fields = (
        "subjective_claim_count",
        "internal_candidate_count",
        "ranked_candidate_count",
    )
    if (
        type(candidate) is not str
        or len(candidate.encode("utf-8")) > 64 * 1024
        or type(summary) is not dict
        or set(summary) != invariant_keys
        or any(type(summary[field]) is not bool for field in bool_fields)
        or any(
            type(summary[field]) is not int or not 0 <= summary[field] <= 64
            for field in count_fields
        )
        or (
            summary["failure_class"] is not None
            and (
                type(summary["failure_class"]) is not str
                or re.fullmatch(
                    r"[A-Za-z_][A-Za-z0-9_]{0,127}",
                    summary["failure_class"],
                )
                is None
            )
        )
    ):
        raise ValueError("early private packet nested body invalid")
    expected_alternate = (
        summary["internal_candidate_count"] >= 2
        and summary["ranked_candidate_count"] >= 2
    )
    available_clear = all(
        (
            summary["actual_japanese_reached"],
            summary["phase_a_and_b_validated"],
            summary["subjective_claim_count"] > 0,
            summary["internal_candidate_count"]
            >= summary["ranked_candidate_count"],
            1 <= summary["ranked_candidate_count"] <= 2,
            summary["normal_form_phase_exact6"],
            summary["normal_form_defect_free"],
            summary["normalization_idempotent"],
            summary["required_duty_coverage_exact"],
            summary["language_core_identity_match"],
            summary["failure_class"] is None,
        )
    )
    failure_shape = (
        summary["phase_a_and_b_validated"] is False
        and candidate == ""
        and all(summary[field] == 0 for field in count_fields)
        and all(summary[field] is False for field in bool_fields)
        and summary["failure_class"] is not None
    )
    if (
        summary["material_alternate_present"] != expected_alternate
        or (summary["machine_invariant_clear"] and not available_clear)
        or (
            summary["actual_japanese_reached"]
            and (
                not candidate
                or any(
                    not sentence.endswith("。")
                    or re.search(r"[ぁ-んァ-ヶ一-龯]", sentence) is None
                    for sentence in candidate.splitlines()
                )
            )
        )
        or (
            summary["phase_a_and_b_validated"] is False
            and not failure_shape
        )
        or (
            summary["phase_a_and_b_validated"]
            and summary["failure_class"] is not None
        )
    ):
        raise ValueError("early private packet nested body invalid")
    return summary


def _validate_early_private_packet(
    payload: object,
    *,
    early_attempt_id: str,
    runtime_repo_head: str,
    design_repo_head: str,
    withheld_input_raw_sha256: str,
    withheld_set_digest: str,
    language_core_identity: str,
    stage1_runtime_integration_identity: str,
    known_visible_packet: Mapping[str, Any] | None = None,
    body_free_withheld_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Fail closed on the private packet envelope and complete nested body."""

    top_keys = {
        "schema_version",
        "packet_id",
        "private_slot_id",
        "early_attempt_id",
        "withheld_input_raw_sha256",
        "withheld_set_digest",
        "private_body_full",
        "private_packet_binding",
        "language_core_identity",
        "stage1_runtime_integration_identity",
        "selection_frozen_before_first_after",
        "known_cases",
        "withheld_cases",
        "human_language_viability_read",
    }
    binding_keys = {
        "binding_version",
        "packet_id",
        "bounded_unit_id",
        "early_attempt_id",
        "runtime_repo_head",
        "design_repo_head",
        "language_core_identity",
        "stage1_runtime_integration_identity",
        "known_structural_families",
        "withheld_input_raw_sha256",
        "withheld_set_digest",
        "runner_identity",
        "packet_binding_sha256",
    }
    runner_keys = {"repo_relative_path", "runner_sha256"}
    human_keys = {
        "body_full_readers",
        "early_human_read_result",
        "defect_class",
        "cause_component",
        "ceiling_reason",
    }
    case_keys = {
        "structural_family",
        "synthetic_input_private",
        "candidate_private",
        "machine_invariant_body_free",
    }
    if type(payload) is not dict or set(payload) != top_keys:
        raise ValueError("early private packet binding invalid")
    binding = payload["private_packet_binding"]
    if type(binding) is not dict or set(binding) != binding_keys:
        raise ValueError("early private packet binding invalid")
    runner = binding["runner_identity"]
    if type(runner) is not dict or set(runner) != runner_keys:
        raise ValueError("early private packet binding invalid")
    binding_material = {
        key: binding[key]
        for key in binding
        if key != "packet_binding_sha256"
    }
    if (
        payload["schema_version"] != EARLY_PRIVATE_PACKET_SCHEMA_VERSION
        or payload["packet_id"] != WITHHELD_EARLY_PACKET_ID
        or payload["private_slot_id"] != WITHHELD_EARLY_PRIVATE_SLOT_ID
        or payload["early_attempt_id"] != early_attempt_id
        or early_attempt_id != EARLY_ACTUAL_ATTEMPT_ID
        or payload["withheld_input_raw_sha256"]
        != withheld_input_raw_sha256
        or withheld_input_raw_sha256
        != EARLY_FROZEN_WITHHELD_INPUT_RAW_SHA256
        or payload["withheld_set_digest"] != withheld_set_digest
        or withheld_set_digest != EARLY_FROZEN_WITHHELD_SET_DIGEST
        or payload["private_body_full"] is not True
        or payload["language_core_identity"] != language_core_identity
        or payload["stage1_runtime_integration_identity"]
        != stage1_runtime_integration_identity
        or payload["selection_frozen_before_first_after"] is not True
        or type(payload["known_cases"]) is not list
        or len(payload["known_cases"]) != 4
        or type(payload["withheld_cases"]) is not list
        or len(payload["withheld_cases"]) != 4
        or type(payload["human_language_viability_read"]) is not dict
        or set(payload["human_language_viability_read"]) != human_keys
        or payload["human_language_viability_read"]
        != {
            "body_full_readers": "PRO_ONLY",
            "early_human_read_result": None,
            "defect_class": None,
            "cause_component": None,
            "ceiling_reason": None,
        }
        or binding["binding_version"]
        != EARLY_PRIVATE_PACKET_BINDING_SCHEMA_VERSION
        or binding["packet_id"] != WITHHELD_EARLY_PACKET_ID
        or binding["bounded_unit_id"] != EARLY_BOUNDED_UNIT_ID
        or binding["early_attempt_id"] != early_attempt_id
        or binding["runtime_repo_head"] != runtime_repo_head
        or binding["design_repo_head"] != design_repo_head
        or binding["language_core_identity"] != language_core_identity
        or binding["stage1_runtime_integration_identity"]
        != stage1_runtime_integration_identity
        or type(binding["known_structural_families"]) not in {list, tuple}
        or tuple(binding["known_structural_families"])
        != EARLY_STRUCTURAL_FAMILIES
        or binding["withheld_input_raw_sha256"]
        != withheld_input_raw_sha256
        or binding["withheld_set_digest"] != withheld_set_digest
        or runner["repo_relative_path"]
        != str(Path(__file__).resolve().relative_to(CHECKOUT_ROOT))
        or runner["runner_sha256"]
        != hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        or binding["packet_binding_sha256"]
        != _canonical_sha256(binding_material)
    ):
        raise ValueError("early private packet binding invalid")

    known_visible_cases: object = None
    if known_visible_packet is not None:
        if (
            type(known_visible_packet) is not dict
            or type(known_visible_packet.get("cases")) is not list
            or len(known_visible_packet["cases"]) != 4
        ):
            raise ValueError("early private packet nested body invalid")
        known_visible_cases = known_visible_packet["cases"]

    for index, (case, frozen) in enumerate(
        zip(payload["known_cases"], EARLY_KNOWN_EXACT4, strict=True),
        start=1,
    ):
        family, memo, category, emotion, strength = frozen
        expected_raw = _raw(
            f"early-known-{index:02d}",
            memo,
            category,
            emotion,
            strength,
        )
        if (
            type(case) is not dict
            or set(case) != case_keys
            or case["structural_family"] != family
            or case["synthetic_input_private"] != expected_raw
        ):
            raise ValueError("early private packet nested body invalid")
        _validate_early_private_case_summary(
            case["machine_invariant_body_free"],
            candidate=case["candidate_private"],
        )
        if known_visible_cases is not None:
            visible = known_visible_cases[index - 1]
            if (
                type(visible) is not dict
                or case["structural_family"]
                != visible.get("structural_family")
                or case["candidate_private"] != visible.get("actual_japanese")
                or case["machine_invariant_body_free"]
                != visible.get("machine_invariant")
                or {
                    "memo": expected_raw["memo"],
                    "category": expected_raw["category"][0],
                    "emotion": expected_raw["emotions"][0],
                    "strength": expected_raw["emotion_details"][0][
                        "strength"
                    ],
                }
                != visible.get("synthetic_input")
            ):
                raise ValueError("early private packet nested body invalid")

    withheld_rows: list[dict[str, str]] = []
    withheld_summaries: list[dict[str, Any]] = []
    for index, case in enumerate(payload["withheld_cases"], start=1):
        if type(case) is not dict or set(case) != case_keys:
            raise ValueError("early private packet nested body invalid")
        raw = case["synthetic_input_private"]
        if (
            type(raw) is not dict
            or set(raw)
            != {
                "id",
                "created_at",
                "memo",
                "memo_action",
                "category",
                "emotion_details",
                "emotions",
                "is_secret",
            }
            or type(raw["memo"]) is not str
            or type(raw["category"]) is not list
            or len(raw["category"]) != 1
            or type(raw["category"][0]) is not str
            or type(raw["emotions"]) is not list
            or len(raw["emotions"]) != 1
            or type(raw["emotions"][0]) is not str
            or type(raw["emotion_details"]) is not list
            or len(raw["emotion_details"]) != 1
            or type(raw["emotion_details"][0]) is not dict
            or set(raw["emotion_details"][0]) != {"type", "strength"}
            or type(raw["emotion_details"][0]["type"]) is not str
            or type(raw["emotion_details"][0]["strength"]) is not str
            or raw["emotions"][0] != raw["emotion_details"][0]["type"]
            or type(case["structural_family"]) is not str
        ):
            raise ValueError("early private packet nested body invalid")
        row = {
            "structural_family": case["structural_family"],
            "memo": raw["memo"],
            "category": raw["category"][0],
            "emotion": raw["emotions"][0],
            "strength": raw["emotion_details"][0]["strength"],
        }
        expected_raw = _raw(
            f"early-withheld-{index:02d}",
            row["memo"],
            row["category"],
            row["emotion"],
            row["strength"],
        )
        if raw != expected_raw:
            raise ValueError("early private packet nested body invalid")
        summary = _validate_early_private_case_summary(
            case["machine_invariant_body_free"],
            candidate=case["candidate_private"],
        )
        withheld_rows.append(row)
        withheld_summaries.append(summary)

    reconstructed_withheld = {
        "schema_version": EARLY_WITHHELD_INPUT_SCHEMA_VERSION,
        "selection_frozen_before_first_after": True,
        "synthetic_non_identifying": True,
        "cases": withheld_rows,
    }
    _validate_withheld_early_payload(reconstructed_withheld)
    if (
        _canonical_sha256(reconstructed_withheld) != withheld_set_digest
        or withheld_set_digest != EARLY_FROZEN_WITHHELD_SET_DIGEST
    ):
        raise ValueError("early private packet nested body invalid")

    if body_free_withheld_summary is not None:
        family_counts = {
            family: sum(
                row["structural_family"] == family for row in withheld_rows
            )
            for family in EARLY_STRUCTURAL_FAMILIES
        }
        clear_count = sum(
            summary["machine_invariant_clear"]
            for summary in withheld_summaries
        )
        expected_summary_bindings = {
            "withheld_set_count": 4,
            "structural_family_counts": family_counts,
            "withheld_set_digest": withheld_set_digest,
            "actual_japanese_reached_count": sum(
                summary["actual_japanese_reached"]
                for summary in withheld_summaries
            ),
            "machine_invariant_clear_count": clear_count,
            "normal_form_phase_exact6_count": sum(
                summary["normal_form_phase_exact6"]
                for summary in withheld_summaries
            ),
            "normal_form_defect_free_count": sum(
                summary["normal_form_defect_free"]
                for summary in withheld_summaries
            ),
            "normalization_idempotent_count": sum(
                summary["normalization_idempotent"]
                for summary in withheld_summaries
            ),
            "required_duty_coverage_exact_count": sum(
                summary["required_duty_coverage_exact"]
                for summary in withheld_summaries
            ),
            "material_alternate_case_count": sum(
                summary["material_alternate_present"]
                for summary in withheld_summaries
            ),
            "machine_failure_classes": sorted(
                {
                    summary["failure_class"]
                    for summary in withheld_summaries
                    if summary["failure_class"] is not None
                }
            ),
            "machine_invariant_result": (
                "CLEAR" if clear_count == 4 else "FAIL"
            ),
        }
        if (
            type(body_free_withheld_summary) is not dict
            or any(
                body_free_withheld_summary.get(key) != value
                for key, value in expected_summary_bindings.items()
            )
        ):
            raise ValueError("early private packet nested body invalid")
    return payload


def _validate_early_known_visible_packet(
    payload: object,
    *,
    body_free_known_summary: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate the complete public known-exact4 body and its aggregates."""

    top_keys = {
        "schema_version",
        "case_count",
        "structural_family_counts",
        "machine_invariant_clear_count",
        "machine_invariant_result",
        "material_alternate_case_count",
        "cases",
    }
    case_keys = {
        "structural_family",
        "synthetic_input",
        "actual_japanese",
        "machine_invariant",
    }
    input_keys = {"memo", "category", "emotion", "strength"}
    invariant_keys = {
        "actual_japanese_reached",
        "phase_a_and_b_validated",
        "subjective_claim_count",
        "internal_candidate_count",
        "ranked_candidate_count",
        "material_alternate_present",
        "normal_form_phase_exact6",
        "normal_form_defect_free",
        "normalization_idempotent",
        "required_duty_coverage_exact",
        "language_core_identity_match",
        "machine_invariant_clear",
        "failure_class",
    }
    summary_keys = {
        "case_count",
        "structural_family_counts",
        "actual_japanese_reached_count",
        "machine_invariant_clear_count",
        "machine_invariant_result",
        "material_alternate_case_count",
        "known_visible_packet_sha256",
        "body_payload_present",
    }
    if (
        type(payload) is not dict
        or set(payload) != top_keys
        or type(body_free_known_summary) is not dict
        or set(body_free_known_summary) != summary_keys
        or payload["schema_version"] != EARLY_KNOWN_VISIBLE_SCHEMA_VERSION
        or type(payload["cases"]) is not list
        or len(payload["cases"]) != 4
        or type(payload["case_count"]) is not int
        or payload["case_count"] != 4
    ):
        raise ValueError("early known visible packet invalid")

    bool_fields = (
        "actual_japanese_reached",
        "phase_a_and_b_validated",
        "material_alternate_present",
        "normal_form_phase_exact6",
        "normal_form_defect_free",
        "normalization_idempotent",
        "required_duty_coverage_exact",
        "language_core_identity_match",
        "machine_invariant_clear",
    )
    validated_cases: list[dict[str, Any]] = []
    for case, frozen in zip(payload["cases"], EARLY_KNOWN_EXACT4, strict=True):
        family, memo, category, emotion, strength = frozen
        if type(case) is not dict or set(case) != case_keys:
            raise ValueError("early known visible packet invalid")
        source = case["synthetic_input"]
        invariant = case["machine_invariant"]
        actual_japanese = case["actual_japanese"]
        if (
            case["structural_family"] != family
            or type(source) is not dict
            or set(source) != input_keys
            or source
            != {
                "memo": memo,
                "category": category,
                "emotion": emotion,
                "strength": strength,
            }
            or type(actual_japanese) is not str
            or len(actual_japanese.encode("utf-8")) > 64 * 1024
            or type(invariant) is not dict
            or set(invariant) != invariant_keys
            or any(type(invariant[field]) is not bool for field in bool_fields)
            or any(
                type(invariant[field]) is not int
                or not 0 <= invariant[field] <= 64
                for field in (
                    "subjective_claim_count",
                    "internal_candidate_count",
                    "ranked_candidate_count",
                )
            )
            or (
                invariant["failure_class"] is not None
                and (
                    type(invariant["failure_class"]) is not str
                    or re.fullmatch(
                        r"[A-Za-z_][A-Za-z0-9_]{0,127}",
                        invariant["failure_class"],
                    )
                    is None
                )
            )
        ):
            raise ValueError("early known visible packet invalid")

        expected_alternate = (
            invariant["internal_candidate_count"] >= 2
            and invariant["ranked_candidate_count"] >= 2
        )
        available_clear = all(
            (
                invariant["actual_japanese_reached"],
                invariant["phase_a_and_b_validated"],
                invariant["subjective_claim_count"] > 0,
                invariant["internal_candidate_count"]
                >= invariant["ranked_candidate_count"],
                1 <= invariant["ranked_candidate_count"] <= 2,
                invariant["normal_form_phase_exact6"],
                invariant["normal_form_defect_free"],
                invariant["normalization_idempotent"],
                invariant["required_duty_coverage_exact"],
                invariant["language_core_identity_match"],
                invariant["failure_class"] is None,
            )
        )
        failure_shape = (
            invariant["phase_a_and_b_validated"] is False
            and actual_japanese == ""
            and all(
                invariant[field] == 0
                for field in (
                    "subjective_claim_count",
                    "internal_candidate_count",
                    "ranked_candidate_count",
                )
            )
            and all(invariant[field] is False for field in bool_fields)
            and invariant["failure_class"] is not None
        )
        if (
            invariant["material_alternate_present"] != expected_alternate
            or (
                invariant["machine_invariant_clear"]
                and not available_clear
            )
            or (
                invariant["actual_japanese_reached"]
                and (
                    not actual_japanese
                    or any(
                        not sentence.endswith("。")
                        or re.search(r"[ぁ-んァ-ヶ一-龯]", sentence) is None
                        for sentence in actual_japanese.splitlines()
                    )
                )
            )
            or (
                invariant["phase_a_and_b_validated"] is False
                and not failure_shape
            )
            or (
                invariant["phase_a_and_b_validated"]
                and invariant["failure_class"] is not None
            )
        ):
            raise ValueError("early known visible packet invalid")
        validated_cases.append(case)

    family_counts = {
        family: sum(
            case["structural_family"] == family for case in validated_cases
        )
        for family in EARLY_STRUCTURAL_FAMILIES
    }
    clear_count = sum(
        case["machine_invariant"]["machine_invariant_clear"]
        for case in validated_cases
    )
    japanese_count = sum(
        case["machine_invariant"]["actual_japanese_reached"]
        for case in validated_cases
    )
    alternate_count = sum(
        case["machine_invariant"]["material_alternate_present"]
        for case in validated_cases
    )
    result = "CLEAR" if clear_count == 4 else "FAIL"
    aggregate_bindings = {
        "case_count": 4,
        "structural_family_counts": family_counts,
        "machine_invariant_clear_count": clear_count,
        "machine_invariant_result": result,
        "material_alternate_case_count": alternate_count,
    }
    body_free_bindings = {
        **aggregate_bindings,
        "actual_japanese_reached_count": japanese_count,
        "known_visible_packet_sha256": _canonical_sha256(payload),
        "body_payload_present": False,
    }
    if (
        any(payload[key] != value for key, value in aggregate_bindings.items())
        or any(
            body_free_known_summary[key] != value
            for key, value in body_free_bindings.items()
        )
    ):
        raise ValueError("early known visible packet invalid")
    return payload


def _validate_early_body_free_machine_packet(
    payload: object,
    *,
    require_clear: bool = True,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate packet integrity, optionally applying the human-entry gate."""

    top_keys = {
        "schema_version",
        "exact3_schema_version",
        "packet_id",
        "bounded_unit_id",
        "early_attempt_id",
        "runtime_repo_head",
        "design_repo_head",
        "language_core_identity",
        "stage1_runtime_integration_identity",
        "withheld_input_raw_sha256",
        "withheld_set_digest",
        "known_exact4_body_free",
        "withheld_exact4_body_free",
        "private_packet_sha256",
        "early_human_read_result",
        "early_actual_status",
        "body_payload_present",
        "private_text_published",
    }
    known_keys = {
        "case_count",
        "structural_family_counts",
        "actual_japanese_reached_count",
        "machine_invariant_clear_count",
        "machine_invariant_result",
        "material_alternate_case_count",
        "known_visible_packet_sha256",
        "body_payload_present",
    }
    withheld_keys = {
        "schema_version",
        "packet_id",
        "bounded_unit_id",
        "early_attempt_id",
        "language_core_identity",
        "stage1_runtime_integration_identity",
        "withheld_input_raw_sha256",
        "withheld_set_count",
        "structural_family_counts",
        "withheld_set_digest",
        "selection_frozen_before_first_after",
        "synthetic_non_identifying_attested",
        "actual_japanese_reached_count",
        "machine_invariant_clear_count",
        "normal_form_phase_exact6_count",
        "normal_form_defect_free_count",
        "normalization_idempotent_count",
        "required_duty_coverage_exact_count",
        "material_alternate_case_count",
        "machine_failure_classes",
        "machine_invariant_result",
        "body_payload_present",
        "private_text_published",
        "body_full_readers",
        "ultra_withheld_body_access",
        "mash_withheld_body_access",
        "formal_exact8_denominator_effect",
        "product_acceptance_denominator_effect",
        "numeric_score_or_pass_rate",
        "product_credit",
        "candidate_ready",
        "production_effect",
        "automatic_progression",
    }
    if type(payload) is not dict or set(payload) != top_keys:
        raise ValueError("early human read machine binding invalid")
    known = payload["known_exact4_body_free"]
    withheld = payload["withheld_exact4_body_free"]
    if (
        type(known) is not dict
        or set(known) != known_keys
        or type(withheld) is not dict
        or set(withheld) != withheld_keys
    ):
        raise ValueError("early human read machine binding invalid")

    try:
        (
            fresh_identity,
            fresh_runtime_integration_identity,
        ) = _current_frozen_early_identity_pair()
    except Exception:
        raise ValueError("early human read machine binding invalid") from None
    family_counts = {family: 1 for family in EARLY_STRUCTURAL_FAMILIES}

    def exact_int(value: object, expected: int) -> bool:
        return type(value) is int and value == expected

    def bounded_count(value: object) -> bool:
        return type(value) is int and 0 <= value <= 4

    def exact_family_counts(value: object) -> bool:
        return (
            type(value) is dict
            and set(value) == set(family_counts)
            and all(exact_int(value[family], 1) for family in family_counts)
        )

    known_bounded_fields = (
        "actual_japanese_reached_count",
        "machine_invariant_clear_count",
    )
    withheld_bounded_fields = (
        "actual_japanese_reached_count",
        "machine_invariant_clear_count",
        "normal_form_phase_exact6_count",
        "normal_form_defect_free_count",
        "normalization_idempotent_count",
        "required_duty_coverage_exact_count",
    )
    if (
        payload["schema_version"] != EARLY_BODY_FREE_PACKET_SCHEMA_VERSION
        or payload["exact3_schema_version"] != EARLY_RUN_EXACT3_SCHEMA_VERSION
        or payload["packet_id"] != WITHHELD_EARLY_PACKET_ID
        or payload["bounded_unit_id"] != EARLY_BOUNDED_UNIT_ID
        or payload["early_attempt_id"] != EARLY_ACTUAL_ATTEMPT_ID
        or type(payload["runtime_repo_head"]) is not str
        or re.fullmatch(r"[0-9a-f]{40}", payload["runtime_repo_head"])
        is None
        or type(payload["design_repo_head"]) is not str
        or re.fullmatch(r"[0-9a-f]{40}", payload["design_repo_head"])
        is None
        or payload["language_core_identity"]
        != fresh_identity
        or payload["stage1_runtime_integration_identity"]
        != fresh_runtime_integration_identity
        or payload["withheld_input_raw_sha256"]
        != EARLY_FROZEN_WITHHELD_INPUT_RAW_SHA256
        or payload["withheld_set_digest"]
        != EARLY_FROZEN_WITHHELD_SET_DIGEST
        or type(payload["private_packet_sha256"]) is not str
        or re.fullmatch(r"[0-9a-f]{64}", payload["private_packet_sha256"])
        is None
        or payload["early_human_read_result"] != "NOT_RUN"
        or payload["early_actual_status"]
        != (
            EARLY_MACHINE_ACTUAL_COMPLETED_STATUS
            if _early_exact8_machine_is_clear(known, withheld)
            else EARLY_MACHINE_ACTUAL_NONCLEAR_STATUS
        )
        or payload["body_payload_present"] is not False
        or payload["private_text_published"] is not False
        or not exact_family_counts(known["structural_family_counts"])
        or not exact_int(known["case_count"], 4)
        or any(
            not bounded_count(known[field])
            for field in known_bounded_fields
        )
        or known["machine_invariant_clear_count"]
        > known["actual_japanese_reached_count"]
        or known["machine_invariant_result"]
        != (
            "CLEAR"
            if known["machine_invariant_clear_count"] == 4
            else "FAIL"
        )
        or not bounded_count(known["material_alternate_case_count"])
        or type(known["known_visible_packet_sha256"]) is not str
        or re.fullmatch(
            r"[0-9a-f]{64}", known["known_visible_packet_sha256"]
        )
        is None
        or known["body_payload_present"] is not False
        or withheld["schema_version"]
        != EARLY_WITHHELD_BODY_FREE_SCHEMA_VERSION
        or withheld["packet_id"] != WITHHELD_EARLY_PACKET_ID
        or withheld["bounded_unit_id"] != EARLY_BOUNDED_UNIT_ID
        or withheld["early_attempt_id"] != EARLY_ACTUAL_ATTEMPT_ID
        or withheld["language_core_identity"] != fresh_identity
        or withheld["stage1_runtime_integration_identity"]
        != fresh_runtime_integration_identity
        or withheld["withheld_input_raw_sha256"]
        != EARLY_FROZEN_WITHHELD_INPUT_RAW_SHA256
        or not exact_family_counts(withheld["structural_family_counts"])
        or not exact_int(withheld["withheld_set_count"], 4)
        or any(
            not bounded_count(withheld[field])
            for field in withheld_bounded_fields
        )
        or withheld["machine_invariant_clear_count"]
        > withheld["actual_japanese_reached_count"]
        or type(withheld["withheld_set_digest"]) is not str
        or withheld["withheld_set_digest"]
        != EARLY_FROZEN_WITHHELD_SET_DIGEST
        or withheld["withheld_set_digest"] != payload["withheld_set_digest"]
        or withheld["selection_frozen_before_first_after"] is not True
        or withheld["synthetic_non_identifying_attested"] is not True
        or not bounded_count(withheld["material_alternate_case_count"])
        or type(withheld["machine_failure_classes"]) is not list
        or withheld["machine_failure_classes"]
        != sorted(set(withheld["machine_failure_classes"]))
        or len(withheld["machine_failure_classes"]) > 4
        or any(
            type(failure) is not str
            or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,127}", failure) is None
            for failure in withheld["machine_failure_classes"]
        )
        or withheld["machine_invariant_result"]
        != (
            "CLEAR"
            if withheld["machine_invariant_clear_count"] == 4
            else "FAIL"
        )
        or withheld["body_payload_present"] is not False
        or withheld["private_text_published"] is not False
        or withheld["body_full_readers"] != "PRO_ONLY"
        or any(
            not exact_int(withheld[field], 0)
            for field in (
                "ultra_withheld_body_access",
                "mash_withheld_body_access",
                "formal_exact8_denominator_effect",
                "product_acceptance_denominator_effect",
                "numeric_score_or_pass_rate",
                "product_credit",
                "production_effect",
            )
        )
        or withheld["candidate_ready"] is not False
        or withheld["automatic_progression"] is not False
    ):
        raise ValueError("early human read machine binding invalid")
    if require_clear and not _early_exact8_machine_is_clear(known, withheld):
        raise ValueError("early human read machine binding invalid")
    return known, withheld


def validate_early_human_read_result(
    payload: object,
    *,
    body_free_machine_packet: Mapping[str, Any],
    private_review_master_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate Pro's sole body-free human transition input exact1."""

    expected_keys = (
        "schema_version",
        "packet_id",
        "bounded_unit_id",
        "early_attempt_id",
        "review_attempt_id",
        "read_count",
        "reread_count",
        "runtime_repo_head",
        "design_repo_head",
        "language_core_identity",
        "stage1_runtime_integration_identity",
        "withheld_input_raw_sha256",
        "withheld_set_digest",
        "private_packet_sha256",
        "body_free_machine_packet_sha256",
        "private_review_master_sha256",
        "reviewed_known_count",
        "reviewed_withheld_count",
        "body_payload_present",
        "early_human_read_result",
        "defect_class",
        "cause_component",
        "ceiling_reason",
    )
    known, withheld = _validate_early_body_free_machine_packet(
        body_free_machine_packet
    )
    try:
        master_receipt = validate_early_private_review_master_receipt(
            private_review_master_receipt,
            body_free_machine_packet=body_free_machine_packet,
        )
    except ValueError:
        raise ValueError("early human read result invalid") from None
    if master_receipt["operation"] != "VALIDATED_FRESH_MATERIALIZATION":
        raise ValueError("early human read result invalid")
    if type(payload) is not dict or set(payload) != set(expected_keys):
        raise ValueError("early human read result invalid")
    machine_bindings = {
        "packet_id": body_free_machine_packet.get("packet_id"),
        "bounded_unit_id": body_free_machine_packet.get("bounded_unit_id"),
        "early_attempt_id": body_free_machine_packet.get("early_attempt_id"),
        "runtime_repo_head": body_free_machine_packet.get("runtime_repo_head"),
        "design_repo_head": body_free_machine_packet.get("design_repo_head"),
        "language_core_identity": body_free_machine_packet.get(
            "language_core_identity"
        ),
        "stage1_runtime_integration_identity": body_free_machine_packet.get(
            "stage1_runtime_integration_identity"
        ),
        "withheld_input_raw_sha256": body_free_machine_packet.get(
            "withheld_input_raw_sha256"
        ),
        "withheld_set_digest": withheld.get("withheld_set_digest"),
        "private_packet_sha256": body_free_machine_packet.get(
            "private_packet_sha256"
        ),
        "body_free_machine_packet_sha256": _canonical_sha256(
            body_free_machine_packet
        ),
        "private_review_master_sha256": master_receipt[
            "private_review_master_sha256"
        ],
    }
    if (
        any(payload[key] != value for key, value in machine_bindings.items())
        or payload["schema_version"] != EARLY_HUMAN_READ_RESULT_SCHEMA_VERSION
        or payload["review_attempt_id"]
        != EARLY_PRO_COMBINED_READ_ATTEMPT_ID
        or type(payload["read_count"]) is not int
        or payload["read_count"] != 1
        or type(payload["reread_count"]) is not int
        or payload["reread_count"] != 0
        or payload["reviewed_known_count"] != 4
        or payload["reviewed_withheld_count"] != 4
        or payload["body_payload_present"] is not False
        or payload["early_human_read_result"] not in EARLY_HUMAN_READ_RESULTS
    ):
        raise ValueError("early human read result invalid")

    result = payload["early_human_read_result"]
    defect_class = payload["defect_class"]
    cause = payload["cause_component"]
    ceiling = payload["ceiling_reason"]
    if result == "CLEAR":
        conditional_valid = (
            defect_class is None and cause is None and ceiling is None
        )
    elif result == "COMMON_DEFECT":
        conditional_valid = (
            defect_class in EARLY_COMMON_DEFECT_CLASSES
            and cause in EARLY_COMMON_DEFECT_CAUSE_COMPONENTS
            and ceiling is None
        )
    else:
        conditional_valid = (
            defect_class is None
            and cause is None
            and ceiling in EARLY_ROUTE_LEVEL_CEILING_REASONS
        )
    if not conditional_valid:
        raise ValueError("early human read result invalid")
    return {key: payload[key] for key in expected_keys}


def validate_ultra_known_technical_result(
    payload: object,
    *,
    body_free_machine_packet: Mapping[str, Any],
    private_review_master_receipt: Mapping[str, Any],
    early_known_review_auxiliary_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate Ultra's body-free technical result for known exact4."""

    expected_keys = (
        "schema_version",
        "packet_id",
        "bounded_unit_id",
        "early_attempt_id",
        "review_attempt_id",
        "read_count",
        "reread_count",
        "runtime_repo_head",
        "design_repo_head",
        "language_core_identity",
        "stage1_runtime_integration_identity",
        "withheld_input_raw_sha256",
        "withheld_set_digest",
        "known_visible_packet_sha256",
        "body_free_machine_packet_sha256",
        "private_review_master_sha256",
        "early_known_review_auxiliary_sha256",
        "reviewed_known_count",
        "body_payload_present",
        "ultra_known_technical_invariant",
    )
    _validate_early_body_free_machine_packet(body_free_machine_packet)
    try:
        master_receipt = validate_early_private_review_master_receipt(
            private_review_master_receipt,
            body_free_machine_packet=body_free_machine_packet,
        )
    except ValueError:
        raise ValueError(
            "early Ultra known technical result invalid"
        ) from None
    if master_receipt["operation"] != "VALIDATED_FRESH_MATERIALIZATION":
        raise ValueError("early Ultra known technical result invalid")
    try:
        auxiliary_receipt = validate_early_known_review_auxiliary_receipt(
            early_known_review_auxiliary_receipt,
            body_free_machine_packet=body_free_machine_packet,
            private_review_master_receipt=master_receipt,
        )
    except ValueError:
        raise ValueError(
            "early Ultra known technical result invalid"
        ) from None
    if (
        auxiliary_receipt["operation"]
        != "VALIDATED_FRESH_MATERIALIZATION"
    ):
        raise ValueError("early Ultra known technical result invalid")
    if type(payload) is not dict or set(payload) != set(expected_keys):
        raise ValueError("early Ultra known technical result invalid")
    machine_bindings = {
        "packet_id": body_free_machine_packet.get("packet_id"),
        "bounded_unit_id": body_free_machine_packet.get("bounded_unit_id"),
        "early_attempt_id": body_free_machine_packet.get("early_attempt_id"),
        "runtime_repo_head": body_free_machine_packet.get("runtime_repo_head"),
        "design_repo_head": body_free_machine_packet.get("design_repo_head"),
        "language_core_identity": body_free_machine_packet.get(
            "language_core_identity"
        ),
        "stage1_runtime_integration_identity": body_free_machine_packet.get(
            "stage1_runtime_integration_identity"
        ),
        "withheld_input_raw_sha256": body_free_machine_packet.get(
            "withheld_input_raw_sha256"
        ),
        "withheld_set_digest": body_free_machine_packet.get(
            "withheld_set_digest"
        ),
        "known_visible_packet_sha256": body_free_machine_packet.get(
            "known_exact4_body_free", {}
        ).get("known_visible_packet_sha256"),
        "body_free_machine_packet_sha256": _canonical_sha256(
            body_free_machine_packet
        ),
        "private_review_master_sha256": master_receipt[
            "private_review_master_sha256"
        ],
        "early_known_review_auxiliary_sha256": auxiliary_receipt[
            "early_known_review_auxiliary_sha256"
        ],
    }
    if (
        any(payload[key] != value for key, value in machine_bindings.items())
        or payload["schema_version"]
        != EARLY_ULTRA_KNOWN_TECHNICAL_RESULT_SCHEMA_VERSION
        or payload["review_attempt_id"]
        != EARLY_ULTRA_KNOWN_READ_ATTEMPT_ID
        or type(payload["read_count"]) is not int
        or payload["read_count"] != 1
        or type(payload["reread_count"]) is not int
        or payload["reread_count"] != 0
        or payload["reviewed_known_count"] != 4
        or payload["body_payload_present"] is not False
        or payload["ultra_known_technical_invariant"]
        not in EARLY_ULTRA_KNOWN_TECHNICAL_RESULTS
    ):
        raise ValueError("early Ultra known technical result invalid")
    return {key: payload[key] for key in expected_keys}


def finalize_early_actual_body_free(
    *,
    body_free_machine_packet: Mapping[str, Any],
    private_review_master_receipt: Mapping[str, Any],
    early_known_review_auxiliary_receipt: Mapping[str, Any],
    pro_human_read_result: object,
    ultra_known_technical_result: object,
) -> dict[str, Any]:
    """Create a separate body-free receipt from the Step 3 exact3 results."""

    _known, withheld = _validate_early_body_free_machine_packet(
        body_free_machine_packet
    )
    master_receipt = validate_early_private_review_master_receipt(
        private_review_master_receipt,
        body_free_machine_packet=body_free_machine_packet,
    )
    if master_receipt["operation"] != "VALIDATED_FRESH_MATERIALIZATION":
        raise ValueError("early final result generation binding invalid")
    auxiliary_receipt = validate_early_known_review_auxiliary_receipt(
        early_known_review_auxiliary_receipt,
        body_free_machine_packet=body_free_machine_packet,
        private_review_master_receipt=master_receipt,
    )
    if (
        auxiliary_receipt["operation"]
        != "VALIDATED_FRESH_MATERIALIZATION"
    ):
        raise ValueError("early final result generation binding invalid")
    pro = validate_early_human_read_result(
        pro_human_read_result,
        body_free_machine_packet=body_free_machine_packet,
        private_review_master_receipt=master_receipt,
    )
    ultra = validate_ultra_known_technical_result(
        ultra_known_technical_result,
        body_free_machine_packet=body_free_machine_packet,
        private_review_master_receipt=master_receipt,
        early_known_review_auxiliary_receipt=auxiliary_receipt,
    )
    pro_result = pro["early_human_read_result"]
    ultra_result = ultra["ultra_known_technical_invariant"]
    withheld_result = withheld["machine_invariant_result"]
    if (
        pro["body_free_machine_packet_sha256"]
        != ultra["body_free_machine_packet_sha256"]
        or pro["private_review_master_sha256"]
        != ultra["private_review_master_sha256"]
        or pro["private_review_master_sha256"]
        != master_receipt["private_review_master_sha256"]
        or ultra["early_known_review_auxiliary_sha256"]
        != auxiliary_receipt["early_known_review_auxiliary_sha256"]
        or pro["private_packet_sha256"]
        != body_free_machine_packet["private_packet_sha256"]
        or pro["review_attempt_id"]
        != EARLY_PRO_COMBINED_READ_ATTEMPT_ID
        or pro["read_count"] != 1
        or pro["reread_count"] != 0
        or ultra["review_attempt_id"]
        != EARLY_ULTRA_KNOWN_READ_ATTEMPT_ID
        or ultra["read_count"] != 1
        or ultra["reread_count"] != 0
    ):
        raise ValueError("early final result generation binding invalid")
    all_three_clear = (
        pro_result == ultra_result == withheld_result == "CLEAR"
    )
    return {
        "schema_version": EARLY_ACTUAL_FINAL_BODY_FREE_SCHEMA_VERSION,
        "packet_id": body_free_machine_packet["packet_id"],
        "bounded_unit_id": body_free_machine_packet["bounded_unit_id"],
        "early_attempt_id": body_free_machine_packet["early_attempt_id"],
        "runtime_repo_head": body_free_machine_packet["runtime_repo_head"],
        "design_repo_head": body_free_machine_packet["design_repo_head"],
        "language_core_identity": body_free_machine_packet[
            "language_core_identity"
        ],
        "stage1_runtime_integration_identity": body_free_machine_packet[
            "stage1_runtime_integration_identity"
        ],
        "withheld_input_raw_sha256": body_free_machine_packet[
            "withheld_input_raw_sha256"
        ],
        "withheld_set_digest": withheld["withheld_set_digest"],
        "known_visible_packet_sha256": ultra[
            "known_visible_packet_sha256"
        ],
        "private_packet_sha256": body_free_machine_packet[
            "private_packet_sha256"
        ],
        "body_free_machine_packet_sha256": ultra[
            "body_free_machine_packet_sha256"
        ],
        "private_review_master_sha256": master_receipt[
            "private_review_master_sha256"
        ],
        "private_review_master_receipt_sha256": _canonical_sha256(
            master_receipt
        ),
        "early_known_review_auxiliary_sha256": auxiliary_receipt[
            "early_known_review_auxiliary_sha256"
        ],
        "early_known_review_auxiliary_receipt_sha256": _canonical_sha256(
            auxiliary_receipt
        ),
        "source_actual_run_count": 1,
        "source_actual_retry_count": 0,
        "source_actual_rerun_count": 0,
        "pro_review_attempt_id": pro["review_attempt_id"],
        "pro_read_count": pro["read_count"],
        "pro_reread_count": pro["reread_count"],
        "ultra_review_attempt_id": ultra["review_attempt_id"],
        "ultra_read_count": ultra["read_count"],
        "ultra_reread_count": ultra["reread_count"],
        "pro_human_read_result_sha256": _canonical_sha256(pro),
        "ultra_known_technical_result_sha256": _canonical_sha256(ultra),
        "pro_body_free_early_human_read_result": pro_result,
        "ultra_known_technical_invariant": ultra_result,
        "withheld_body_free_machine_invariant": withheld_result,
        "all_three_clear": all_three_clear,
        "early_actual_status": (
            "LANGUAGE_VIABILITY_OBSERVED"
            if all_three_clear
            else EARLY_ACTUAL_REVIEWED_NONCLEAR_STATUS
        ),
        "body_payload_present": False,
        "private_text_published": False,
        "formal_exact8": "NOT_RUN",
        "product_read_evaluated": False,
        "product_credit": 0,
        "candidate_ready": False,
        "production_effect": 0,
        "automatic_progression": False,
    }


def _private_packet_binding(
    *,
    runtime_repo_head: str,
    design_repo_head: str,
) -> dict[str, Any]:
    """Bind one private materialization to both repos, fixture and runner."""

    heads = (runtime_repo_head, design_repo_head)
    if any(re.fullmatch(r"[0-9a-f]{40}", head) is None for head in heads):
        raise ValueError("private packet repo head binding invalid")
    fixture_identity = {
        "fixture_order": [row[0] for row in EXACT8],
        "fixture_and_axes_sha256": _canonical_sha256(
            {
                "exact8": EXACT8,
                "product_read_axes": PRODUCT_READ_AXES,
            }
        ),
    }
    runner_identity = {
        "repo_relative_path": str(Path(__file__).resolve().relative_to(CHECKOUT_ROOT)),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    material = {
        "binding_version": "cocolon.cmee.stage1.private_packet_binding.v1",
        "packet_id": STAGE1_KAREN_DERIVED_AFTER_PACKET_ID,
        "runtime_repo_head": runtime_repo_head,
        "design_repo_head": design_repo_head,
        "fixture_identity": fixture_identity,
        "runner_identity": runner_identity,
    }
    return {
        **material,
        "packet_binding_sha256": _canonical_sha256(material),
    }


_STRICT_DIRECTIONAL_TRACE_RELATIONS = frozenset(
    {
        "temporal_before_after",
        "shift_from_to",
        "user_stated_cause",
        "user_stated_result",
        "attempt_and_block",
        "action_supports_change",
        "evaluation_about_event",
        "self_evaluation_about_state",
    }
)


def _source_owner_dispositions_valid(graph: GroundedMeaningGraph) -> bool:
    """Validate the exact disabled source-owner rows used by the packet."""

    nodes = {row.node_id: row for row in graph.nodes}
    edges = {row.edge_id: row for row in graph.edges}
    claims = {**nodes, **edges}
    positive = {
        SourceOwnerDisposition.SOURCE_EXPLICIT_VISIBLE,
        SourceOwnerDisposition.SUPPLEMENTAL_USER_VISIBLE,
    }
    for row in graph.owner_dispositions:
        refs = tuple(row.visible_claim_refs)
        if not row.evidence_ids or len(row.evidence_ids) != len(set(row.evidence_ids)):
            return False
        if row.disposition in positive:
            expected_fields = (
                (
                    ResolverResolution.MISSING_OR_INVALID,
                    AttachmentAdmission.UNAVAILABLE,
                    VisibleAuthority.SOURCE_EXPLICIT,
                )
                if row.disposition
                is SourceOwnerDisposition.SOURCE_EXPLICIT_VISIBLE
                else (
                    ResolverResolution.UNIQUE,
                    AttachmentAdmission.PROVISIONAL_ONLY,
                    VisibleAuthority.SUPPLEMENTAL_USER,
                )
            )
            if (
                (
                    row.resolver_resolution,
                    row.attachment_admission,
                    row.visible_authority,
                )
                != expected_fields
                or not refs
                or len(refs) != len(set(refs))
                or row.target_unknown_ref is not None
                or row.reason_codes
            ):
                return False
            for claim_ref in refs:
                claim = claims.get(claim_ref)
                if (
                    claim is None
                    or claim.owner_id != row.owner_id
                    or claim.epistemic_state is not EpistemicState.SOURCE_EXPLICIT
                    or not claim.evidence_ids
                    or not set(claim.evidence_ids).issubset(set(row.evidence_ids))
                ):
                    return False
        elif (
            row.disposition
            is SourceOwnerDisposition.UNKNOWN_PRESERVED_LIMITED
        ):
            target = nodes.get(row.target_unknown_ref or "")
            if (
                row.resolver_resolution is not ResolverResolution.UNRESOLVED
                or row.attachment_admission is not AttachmentAdmission.UNRESOLVED
                or row.visible_authority is not VisibleAuthority.NONE
                or row.target_unknown_ref is None
                or refs != (row.target_unknown_ref,)
                or type(target) is not MeaningNode
                or target.owner_id != row.owner_id
                or target.epistemic_state is not EpistemicState.UNKNOWN
                or target.evidence_ids != row.evidence_ids
                or row.reason_codes != ("ATTACHMENT_UNRESOLVED",)
            ):
                return False
        elif (
            row.disposition
            is SourceOwnerDisposition.NOT_VISIBLE_UNRESOLVED
        ):
            if (
                row.resolver_resolution
                is not ResolverResolution.MISSING_OR_INVALID
                or row.attachment_admission is not AttachmentAdmission.UNAVAILABLE
                or row.visible_authority is not VisibleAuthority.NONE
                or refs
                or row.target_unknown_ref is not None
                or row.reason_codes != ("ATTACHMENT_UNRESOLVED",)
            ):
                return False
        else:
            return False
    return True


def _structural_trace_valid(outcome: object) -> bool:
    artifact = getattr(outcome, "artifact", None)
    graph = getattr(outcome, "meaning_graph", None)
    status = getattr(getattr(outcome, "status", None), "value", "")
    if status not in {"GENERATED", "LIMITED"}:
        return False
    if (
        type(artifact) is not GenerationArtifactBundle
        or type(graph) is not GroundedMeaningGraph
        or type(artifact.plan) is not ExperiencePlan
        or type(artifact.trace) is not tuple
        or any(type(row) is not VisibleUnitTrace for row in artifact.trace)
        or type(artifact.visible_unknowns) is not tuple
        or any(
            type(row) is not VisibleUnknownUnit for row in artifact.visible_unknowns
        )
        or getattr(outcome, "terminal_state", "")
        != CMEE_TERMINAL_GENERATED_DISABLED
        or getattr(outcome, "automatic_progression", True)
    ):
        return False
    expected_lineage = (
        graph.source_envelope_id,
        graph.source_version,
        graph.obligation_version,
        graph.owner_universe_digest,
    )
    if (
        type(artifact.observation) is not str
        or not artifact.observation
        or type(artifact.reception) is not str
        or not artifact.reception
        or type(artifact.artifact_id) is not str
        or re.fullmatch(r"artifact-[0-9a-f]{24}", artifact.artifact_id) is None
        or artifact.realizer_contract_ids != REALIZER_CONTRACT_IDS
        or artifact.trust_policy_ids != TRUST_POLICY_IDS
        or (
            artifact.plan.source_envelope_id,
            artifact.plan.source_version,
            artifact.plan.obligation_version,
            artifact.plan.owner_universe_digest,
        )
        != expected_lineage
        or any(
            (
                row.source_envelope_id,
                row.source_version,
                row.obligation_version,
                row.owner_universe_digest,
            )
            != expected_lineage
            for row in artifact.trace
        )
    ):
        return False
    owner_ids = tuple(row.owner_id for row in graph.owner_dispositions)
    if owner_ids != graph.required_owner_refs + graph.active_optional_owner_refs:
        return False
    if len(owner_ids) != len(set(owner_ids)):
        return False
    roles = tuple(row.role for row in artifact.trace)
    observation_count = roles.count("OBSERVATION")
    unknown_traces = tuple(row for row in artifact.trace if row.role == "UNKNOWN")
    reception_traces = tuple(
        row for row in artifact.trace if row.role == "RECEPTION"
    )
    visible_unknowns = tuple(getattr(artifact, "visible_unknowns", ()))
    expected_status = "LIMITED" if unknown_traces else "GENERATED"
    if (
        status != expected_status
        or not 1 <= observation_count <= 5
        or not 0 <= len(unknown_traces) <= 1
        or not 1 <= len(reception_traces) <= 4
        or roles
        != (
            *("OBSERVATION" for _ in range(observation_count)),
            *("UNKNOWN" for _ in range(len(unknown_traces))),
            *("RECEPTION" for _ in range(len(reception_traces))),
        )
    ):
        return False
    visible_unit_ids = tuple(row.visible_unit_id for row in artifact.trace)
    source_sentence_ids = tuple(row.source_sentence_id for row in artifact.trace)
    if (
        visible_unit_ids != tuple(
            f"visible:{index}" for index in range(1, len(artifact.trace) + 1)
        )
        or len(visible_unit_ids) != len(set(visible_unit_ids))
        or len(source_sentence_ids) != len(set(source_sentence_ids))
    ):
        return False
    expected_source_sentence_ids = (
        *(f"cmee:observation:{index}" for index in range(1, observation_count + 1)),
        *(f"cmee:unknown:{index}" for index in range(1, len(unknown_traces) + 1)),
        *(f"cmee:reception:{index}" for index in range(1, len(reception_traces) + 1)),
    )
    if source_sentence_ids != expected_source_sentence_ids:
        return False
    if len(visible_unknowns) != len(unknown_traces):
        return False
    if (
        tuple(
            owner_id
            for trace in unknown_traces
            for owner_id in trace.constrained_by_owner_ids
        )
        != artifact.plan.visible_unknown_owner_ids
        or not set(artifact.plan.required_unknown_owner_ids).issubset(
            artifact.plan.visible_unknown_owner_ids
        )
    ):
        return False
    if any(
        unknown_trace.visible_unit_id != visible_unknown.unknown_unit_id
        or unknown_trace.source_sentence_id != visible_unknown.source_sentence_id
        or unknown_trace.source_envelope_id != visible_unknown.source_envelope_id
        or unknown_trace.source_version != visible_unknown.source_version
        or unknown_trace.obligation_version != visible_unknown.obligation_version
        or unknown_trace.owner_universe_digest
        != visible_unknown.owner_universe_digest
        or unknown_trace.duty_id != visible_unknown.duty_id
        or unknown_trace.constrained_by_owner_ids != visible_unknown.owner_ids
        or unknown_trace.evidence_ids != visible_unknown.evidence_ids
        for unknown_trace, visible_unknown in zip(
            unknown_traces, visible_unknowns, strict=True
        )
    ):
        return False
    if not all(
        _valid_ref_tuple(row.evidence_ids)
        and _valid_ref_tuple(row.meaning_node_ids, allow_empty=True)
        and _valid_ref_tuple(row.meaning_edge_ids, allow_empty=True)
        and _valid_ref_tuple(row.constrained_by_owner_ids, allow_empty=True)
        for row in artifact.trace
    ):
        return False
    nodes = {row.node_id: row for row in graph.nodes}
    edges = {row.edge_id: row for row in graph.edges}
    disposition = {row.owner_id: row for row in graph.owner_dispositions}
    if not _source_owner_dispositions_valid(graph):
        return False
    disposition_evidence_ids = {
        evidence_id
        for row in graph.owner_dispositions
        for evidence_id in row.evidence_ids
    }
    positive_dispositions = {
        SourceOwnerDisposition.SOURCE_EXPLICIT_VISIBLE,
        SourceOwnerDisposition.SUPPLEMENTAL_USER_VISIBLE,
    }
    for row in graph.owner_dispositions:
        refs = tuple(row.visible_claim_refs)
        if (
            (row.disposition in positive_dispositions and not refs)
            or len(refs) != len(set(refs))
            or any(
                (
                    ref not in nodes
                    or nodes[ref].owner_id != row.owner_id
                    or (
                        row.disposition in positive_dispositions
                        and nodes[ref].epistemic_state
                        is not EpistemicState.SOURCE_EXPLICIT
                    )
                )
                and (
                    ref not in edges
                    or edges[ref].owner_id != row.owner_id
                    or (
                        row.disposition in positive_dispositions
                        and edges[ref].epistemic_state
                        is not EpistemicState.SOURCE_EXPLICIT
                    )
                )
                for ref in refs
            )
        ):
            return False
    expected_visible_owner_ids = tuple(
        row.owner_id
        for row in graph.owner_dispositions
        if row.disposition in positive_dispositions
    )
    expected_unresolved_owner_ids = tuple(
        row.owner_id
        for row in graph.owner_dispositions
        if row.disposition not in positive_dispositions
    )
    if (
        artifact.plan.visible_owner_ids != expected_visible_owner_ids
        or artifact.plan.unresolved_owner_ids != expected_unresolved_owner_ids
    ):
        return False
    for unknown in unknown_traces:
        constrained_evidence_ids = {
            evidence_id
            for owner_id in unknown.constrained_by_owner_ids
            if owner_id in disposition
            for evidence_id in disposition[owner_id].evidence_ids
        }
        allowed_unknown_evidence_owner_ids = set(
            unknown.constrained_by_owner_ids
        ) | set(artifact.plan.required_observation_owner_ids)
        allowed_unknown_evidence_ids = {
            evidence_id
            for owner_id in allowed_unknown_evidence_owner_ids
            if owner_id in disposition
            for evidence_id in disposition[owner_id].evidence_ids
        }
        if (
            unknown.duty_id != "PRESERVE_EVIDENCE_BOUND_UNKNOWN"
            or unknown.operation != "EVIDENCE_BOUND_UNKNOWN_PRESERVATION"
            or unknown.meaning_node_ids
            or unknown.meaning_edge_ids
            or not unknown.constrained_by_owner_ids
            or unknown.emlis_stage1_extension is not None
            or any(
                owner_id not in disposition
                for owner_id in unknown.constrained_by_owner_ids
            )
            or any(
                disposition[owner_id].disposition
                is not SourceOwnerDisposition.UNKNOWN_PRESERVED_LIMITED
                and (
                    disposition[owner_id].owner_class is not OwnerClass.REQUIRED
                    or disposition[owner_id].disposition in positive_dispositions
                )
                for owner_id in unknown.constrained_by_owner_ids
            )
            or not constrained_evidence_ids.issubset(unknown.evidence_ids)
            or not set(unknown.evidence_ids).issubset(
                allowed_unknown_evidence_ids & disposition_evidence_ids
            )
        ):
            return False
    trace_position = {
        row.visible_unit_id: index for index, row in enumerate(artifact.trace)
    }
    observation_trace_ids = {
        row.visible_unit_id for row in artifact.trace if row.role == "OBSERVATION"
    }
    observation_contributions_by_trace: dict[str, tuple[str, ...]] = {}
    positive_variants: set[str] = set()
    observation_contribution_refs: list[str] = []
    reception_claim_refs: list[str] = []
    for trace in artifact.trace:
        extension = trace.emlis_stage1_extension
        semantic_evidence_ids: set[str] = set()
        if trace.role in {"OBSERVATION", "RECEPTION"}:
            if (
                type(extension) is not EmlisStage1PositiveTraceExtension
                or not (trace.meaning_node_ids or trace.meaning_edge_ids)
                or trace.constrained_by_owner_ids
            ):
                return False
            if (
                extension.schema_version
                != CMEE_STAGE1_TRACE_EXTENSION_SCHEMA_VERSION
                or type(extension.owner_ref) is not str
                or extension.owner_ref
                != "owner:emlis@cocolon.cmee.v1a.emlis_stage1_response.v1"
                or type(extension.user_fact_effect) is not int
                or extension.user_fact_effect != 0
                or type(extension.composition_variant_id) is not str
                or not extension.composition_variant_id
                or not _valid_ref_tuple(extension.contribution_refs, allow_empty=True)
                or not _valid_ref_tuple(extension.basis_trace_refs, allow_empty=True)
                or not _valid_ref_tuple(
                    extension.interpretation_candidate_refs, allow_empty=True
                )
                or not _valid_ref_tuple(
                    extension.basis_observation_contribution_refs,
                    allow_empty=True,
                )
                or not _valid_ref_tuple(extension.value_principle_refs, allow_empty=True)
            ):
                return False
            positive_variants.add(extension.composition_variant_id)
            if trace.role == "OBSERVATION":
                if (
                    trace.duty_id != artifact.plan.observation_duty_id
                    or trace.operation != "SOURCE_EXPLICIT_GROUNDED_OBSERVATION"
                    or extension.claim_domain
                    is not EmlisTraceClaimDomain.INTERPRETIVE_OBSERVATION
                    or len(extension.contribution_refs) != 1
                    or not extension.interpretation_candidate_refs
                    or extension.subjective_claim_ref is not None
                    or extension.basis_trace_refs
                    or extension.basis_observation_contribution_refs
                    or extension.value_principle_refs
                    or extension.speaker_owner is not None
                ):
                    return False
                observation_contributions_by_trace[trace.visible_unit_id] = (
                    extension.contribution_refs
                )
                observation_contribution_refs.extend(extension.contribution_refs)
            elif (
                trace.duty_id != artifact.plan.reception_duty_id
                or trace.operation != "BOUND_HUMAN_RECEPTION"
                or extension.claim_domain
                is not EmlisTraceClaimDomain.SUBJECTIVE_RESPONSE
                or extension.contribution_refs
                or extension.interpretation_candidate_refs
                or type(extension.subjective_claim_ref) is not str
                or not extension.subjective_claim_ref
                or not extension.basis_observation_contribution_refs
                or not extension.basis_trace_refs
                or extension.speaker_owner != "EMLIS"
                or any(
                    basis_ref not in observation_trace_ids
                    or trace_position[basis_ref] >= trace_position[trace.visible_unit_id]
                    for basis_ref in extension.basis_trace_refs
                )
            ):
                return False
            else:
                reception_claim_refs.append(extension.subjective_claim_ref)
                reachable_basis_contributions = tuple(
                    contribution_ref
                    for basis_ref in extension.basis_trace_refs
                    for contribution_ref in observation_contributions_by_trace.get(
                        basis_ref, ()
                    )
                )
                if (
                    extension.basis_observation_contribution_refs
                    != reachable_basis_contributions
                ):
                    return False
        for node_id in trace.meaning_node_ids:
            node = nodes.get(node_id)
            owner_disposition = disposition.get(node.owner_id) if node else None
            if (
                node is None
                or owner_disposition is None
                or owner_disposition.disposition not in positive_dispositions
                or node.owner_id not in set(artifact.plan.visible_owner_ids)
                or node.node_id not in set(owner_disposition.visible_claim_refs)
                or node.epistemic_state is not EpistemicState.SOURCE_EXPLICIT
                or node.grounding_kind not in {"explicit", "user_stated_relation"}
                or not node.evidence_ids
            ):
                return False
            semantic_evidence_ids.update(node.evidence_ids)
        for edge_id in trace.meaning_edge_ids:
            edge = edges.get(edge_id)
            owner_disposition = disposition.get(edge.owner_id) if edge else None
            if (
                edge is None
                or owner_disposition is None
                or owner_disposition.disposition not in positive_dispositions
                or edge.owner_id not in set(artifact.plan.visible_owner_ids)
                or edge.edge_id not in set(owner_disposition.visible_claim_refs)
                or edge.epistemic_state is not EpistemicState.SOURCE_EXPLICIT
                or edge.grounding_kind != "user_stated_relation"
                or not edge.evidence_ids
            ):
                return False
            semantic_evidence_ids.update(edge.evidence_ids)
            if edge.relation in _STRICT_DIRECTIONAL_TRACE_RELATIONS:
                try:
                    source_position = trace.meaning_node_ids.index(
                        edge.source_node_id
                    )
                    target_position = trace.meaning_node_ids.index(
                        edge.target_node_id
                    )
                except ValueError:
                    return False
                if source_position >= target_position:
                    return False
        if trace.role in {"OBSERVATION", "RECEPTION"} and set(
            trace.evidence_ids
        ) != semantic_evidence_ids:
            return False
    if len(positive_variants) != 1:
        return False
    if (
        len(observation_contribution_refs)
        != len(set(observation_contribution_refs))
        or len(reception_claim_refs) != len(set(reception_claim_refs))
    ):
        return False
    guarded_ids = tuple(
        row.source_sentence_id
        for row in artifact.trace
        if row.role == "OBSERVATION"
    )
    proof = artifact.common_guard_proof
    if (
        type(proof) is not CommonGuardProof
        or type(proof.guarded_observation_units) is not tuple
        or any(
            type(row) is not tuple
            or len(row) != 2
            or any(type(value) is not str or not value for value in row)
            for row in proof.guarded_observation_units
        )
    ):
        return False
    if tuple(
        row[0] for row in proof.guarded_observation_units
    ) != guarded_ids:
        return False
    if "\r" in artifact.observation or "\r" in artifact.reception:
        return False
    observation_lines = tuple(artifact.observation.split("\n"))
    reception_lines = tuple(artifact.reception.split("\n"))
    if (
        any(not line for line in (*observation_lines, *reception_lines))
        or artifact.observation != "\n".join(observation_lines)
        or artifact.reception != "\n".join(reception_lines)
        or len(observation_lines) != observation_count
        or len(reception_lines) != len(reception_traces)
    ):
        return False
    visible_text = (
        *observation_lines,
        *(row.text for row in visible_unknowns),
        *reception_lines,
    )
    if any(
        trace.text_sha256 != _sha256_text(text)
        for trace, text in zip(artifact.trace, visible_text, strict=True)
    ):
        return False
    expected_guarded_observation_units = tuple(
        (source_sentence_id, _sha256_text(text))
        for source_sentence_id, text in zip(
            guarded_ids,
            observation_lines,
            strict=True,
        )
    )
    if (
        proof.schema_version != CMEE_COMMON_GUARD_PROOF_VERSION
        or type(proof.proof_id) is not str
        or not proof.proof_id
        or proof.source_envelope_id != graph.source_envelope_id
        or proof.graph_id != graph.graph_id
        or proof.plan_id != artifact.plan.plan_id
        or any(
            row.artifact_common_guard_proof_ref != proof.proof_id
            for row in artifact.trace
        )
        or type(proof.guarded_observation_units) is not tuple
        or proof.guarded_observation_units != expected_guarded_observation_units
        or type(proof.guard_results) is not tuple
        or len(proof.guard_results) != len(EXPECTED_COMMON_GUARD_IDS)
        or any(
            type(row) is not CommonGuardResultProof
            or row.guard_id != expected_guard_id
            or type(row.passed) is not bool
            or row.passed is not True
            for expected_guard_id, row in zip(
                EXPECTED_COMMON_GUARD_IDS,
                proof.guard_results,
                strict=True,
            )
        )
        or proof.stabilization_report_name
        != COMMON_GUARD_STABILIZATION_REPORT_NAME
        or proof.stabilization_phase != COMMON_GUARD_STABILIZATION_PHASE
        or proof.stabilization_core_id != COMMON_GUARD_STABILIZATION_CORE_ID
        or type(proof.stabilization_passed) is not bool
        or proof.stabilization_passed is not True
        or type(proof.common_shapes_ready) is not bool
        or proof.common_shapes_ready is not True
        or type(proof.stabilization_guard_names) is not tuple
        or proof.stabilization_guard_names != EXPECTED_COMMON_GUARD_IDS
        or type(proof.issue_codes) is not tuple
        or proof.issue_codes != ()
    ):
        return False
    if proof.proof_id != _common_guard_proof_id(
        source_envelope_id=proof.source_envelope_id,
        graph_id=proof.graph_id,
        plan_id=proof.plan_id,
        guarded_observation_units=proof.guarded_observation_units,
        guard_results=proof.guard_results,
        stabilization_report_name=proof.stabilization_report_name,
        stabilization_phase=proof.stabilization_phase,
        stabilization_core_id=proof.stabilization_core_id,
        stabilization_passed=proof.stabilization_passed,
        common_shapes_ready=proof.common_shapes_ready,
        stabilization_guard_names=proof.stabilization_guard_names,
        issue_codes=proof.issue_codes,
    ):
        return False
    return True


def run(
    *,
    runtime_repo_head: str | None = None,
    design_repo_head: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if (runtime_repo_head is None) != (design_repo_head is None):
        raise ValueError("private packet repo head binding incomplete")
    engine = MeaningExperienceEngine()
    mutation_registry = _body_free_mutation_registry()
    private_cases: list[dict[str, Any]] = []
    body_free_cases: list[dict[str, Any]] = []
    for case_id, memo, category, emotion, strength in EXACT8:
        raw = _raw(case_id, memo, category, emotion, strength)
        outcome = engine.generate(
            GenerationRequest(
                request_id=f"req-{case_id}",
                current_input_bundle=build_emlis_current_input_bundle(raw),
                expected_source_record_id=str(raw["id"]),
            )
        )
        structural_valid = _structural_trace_valid(outcome)
        private_cases.append(
            {
                "case_id": case_id,
                "synthetic_input_private": raw,
                "candidate_private": outcome.artifact.text if outcome.artifact else "",
                "structural_trace_valid": structural_valid,
                "review_axes": list(PRODUCT_READ_AXES),
                "human_product_read": {
                    "axis_results": None,
                    "common_severity": None,
                    "accepted": None,
                },
            }
        )
        body_free_cases.append(
            {
                "case_id": case_id,
                "status": outcome.status.value,
                "reason_codes": list(outcome.reason_codes),
                "structural_trace_valid": structural_valid,
                "artifact_present": outcome.artifact is not None,
                "visible_unit_trace_count": len(outcome.artifact.trace) if outcome.artifact else 0,
            }
        )

    artifact_count = sum(item["artifact_present"] for item in body_free_cases)
    structural_count = sum(item["structural_trace_valid"] for item in body_free_cases)
    candidate_state = (
        "GENERATED_FOR_PRODUCT_READ_DISABLED"
        if structural_count == len(EXACT8)
        else "EXACT8_GENERATION_INCOMPLETE_DISABLED"
    )
    full = {
        "packet_id": STAGE1_KAREN_DERIVED_AFTER_PACKET_ID,
        "private_slot_id": STAGE1_KAREN_DERIVED_AFTER_PRIVATE_SLOT_ID,
        "private_body_full": True,
        "private_packet_binding": (
            _private_packet_binding(
                runtime_repo_head=runtime_repo_head,
                design_repo_head=design_repo_head,
            )
            if runtime_repo_head is not None and design_repo_head is not None
            else {"binding_state": "UNMATERIALIZED"}
        ),
        "candidate_state": candidate_state,
        "finite_mutation_set_body_free": mutation_registry,
        "cases": private_cases,
        "candidate_evaluation_not_yet_accepted": {
            "structural_trace_valid_is_observation_only": False,
            "human_axes_required": list(PRODUCT_READ_AXES),
            "common_blocker_or_major_required": 0,
            "set_level_reread_required": True,
        },
    }
    body_free: dict[str, Any] = {
        "packet_id": full["packet_id"],
        "case_count": len(body_free_cases),
        "generated_count": sum(item["status"] == "GENERATED" for item in body_free_cases),
        "limited_count": sum(item["status"] == "LIMITED" for item in body_free_cases),
        "material_unknown_case_count": sum(
            item["status"] == "LIMITED" for item in body_free_cases
        ),
        "structural_trace_valid_count": sum(item["structural_trace_valid"] for item in body_free_cases),
        "artifact_count": artifact_count,
        "observation_plus_bound_reception_trace_count": sum(
            item["structural_trace_valid"] for item in body_free_cases
        ),
        "cases": body_free_cases,
        "candidate_state": candidate_state,
        "finite_mutation_set_body_free": mutation_registry,
        "implementation_state": "DRAFT_WIP_DISABLED",
        "source_owner_contract_complete": False,
        "candidate_ready": False,
        "product_read_eligible": False,
        "exact8_acceptance_complete": False,
        "product_read_evaluated": False,
        "private_text_published": False,
        "p0_credit": 0,
        "l3i_credit": 0,
        "full_i1_credit": 0,
        "cycle001_credit": 0,
        "production_effect": 0,
        "automatic_progression": False,
    }
    return body_free, full


def _paths_overlap(left: Path, right: Path) -> bool:
    return left == right or left in right.parents or right in left.parents


def _private_output_target(
    parser: argparse.ArgumentParser,
    requested: Path,
) -> Path:
    """Resolve a private target that is disjoint from this checkout."""

    root = PRIVATE_OUTPUT_ROOT.resolve()
    checkout = CHECKOUT_ROOT.resolve()
    target = requested.resolve()
    if _paths_overlap(root, checkout):
        parser.error("private output root is not isolated from the checkout")
    if (
        target == root
        or root not in target.parents
        or _paths_overlap(target, checkout)
    ):
        parser.error("private output target is not isolated")
    return target


def _private_input_target(
    parser: argparse.ArgumentParser,
    requested: Path,
) -> Path:
    """Lexically bind an input below the root without following any path."""

    root = Path(os.path.abspath(os.fspath(PRIVATE_OUTPUT_ROOT)))
    checkout = CHECKOUT_ROOT.resolve()
    target = Path(os.path.abspath(os.fspath(requested)))
    if (
        _paths_overlap(root, checkout)
        or target == root
        or root not in target.parents
        or _paths_overlap(target, checkout)
    ):
        parser.error("private input target is not isolated")
    return target


def _require_new_private_output_targets(
    parser: argparse.ArgumentParser,
    targets: tuple[Path, ...],
) -> None:
    """Reject an already materialized early output before any body is read."""

    for target in targets:
        try:
            target.lstat()
        except FileNotFoundError:
            continue
        except OSError:
            parser.error("early actual private output target is unavailable")
        parser.error("early actual private output target already exists")


def _require_unconsumed_early_attempt(
    parser: argparse.ArgumentParser,
    target: Path,
) -> None:
    """Reject a stale fixed attempt marker before private input is opened."""

    marker = target.parent / EARLY_ACTUAL_STAGING_DIRECTORY_NAME
    try:
        marker.lstat()
    except FileNotFoundError:
        return
    except OSError:
        parser.error("early actual attempt state unavailable")
    parser.error("early actual RUN_RESULT_UNKNOWN_TERMINAL; retry prohibited")


def _open_directory_path_without_symlinks(target: Path) -> int:
    """Open one absolute directory path component-by-component."""

    no_follow = getattr(os, "O_NOFOLLOW", 0)
    directory = getattr(os, "O_DIRECTORY", 0)
    flags = os.O_RDONLY | directory | no_follow
    directory_fd = os.open(target.anchor, flags)
    try:
        for part in target.parts[1:]:
            next_directory_fd = os.open(
                part,
                flags,
                dir_fd=directory_fd,
            )
            os.close(directory_fd)
            directory_fd = next_directory_fd
        return directory_fd
    except BaseException:
        os.close(directory_fd)
        raise


def _read_private_json_and_raw_sha256(target: Path) -> tuple[object, str]:
    """Read and hash the exact bytes through one validated final inode fd."""

    root = Path(os.path.abspath(os.fspath(PRIVATE_OUTPUT_ROOT)))
    target = Path(os.path.abspath(os.fspath(target)))
    try:
        relative_parts = target.relative_to(root).parts
    except ValueError:
        raise ValueError("withheld early private input invalid") from None
    no_follow = getattr(os, "O_NOFOLLOW", 0)
    directory = getattr(os, "O_DIRECTORY", 0)
    directory_flags = os.O_RDONLY | directory | no_follow
    owner_uid = os.geteuid()
    directory_fd = -1
    file_fd = -1
    try:
        directory_fd = _open_directory_path_without_symlinks(root)
        root_stat = os.fstat(directory_fd)
        if (
            not stat.S_ISDIR(root_stat.st_mode)
            or stat.S_IMODE(root_stat.st_mode) != 0o700
            or root_stat.st_uid != owner_uid
        ):
            raise ValueError("withheld early private input invalid")

        for part in relative_parts[:-1]:
            next_directory_fd = os.open(
                part,
                directory_flags,
                dir_fd=directory_fd,
            )
            next_stat = os.fstat(next_directory_fd)
            if (
                not stat.S_ISDIR(next_stat.st_mode)
                or stat.S_IMODE(next_stat.st_mode) != 0o700
                or next_stat.st_uid != owner_uid
            ):
                os.close(next_directory_fd)
                raise ValueError("withheld early private input invalid")
            os.close(directory_fd)
            directory_fd = next_directory_fd

        file_fd = os.open(
            relative_parts[-1],
            os.O_RDONLY | no_follow,
            dir_fd=directory_fd,
        )
        file_stat = os.fstat(file_fd)
        if (
            not stat.S_ISREG(file_stat.st_mode)
            or stat.S_IMODE(file_stat.st_mode) != 0o600
            or file_stat.st_uid != owner_uid
            or file_stat.st_nlink != 1
            or not 0 < file_stat.st_size <= 64 * 1024
        ):
            raise ValueError("withheld early private input invalid")
        with os.fdopen(file_fd, "rb") as handle:
            file_fd = -1
            raw = handle.read()
        return json.loads(raw.decode("utf-8")), hashlib.sha256(raw).hexdigest()
    except OSError:
        raise ValueError("withheld early private input invalid") from None
    finally:
        if file_fd >= 0:
            os.close(file_fd)
        if directory_fd >= 0:
            os.close(directory_fd)


def _read_private_json(target: Path) -> object:
    """Compatibility reader retaining the same single-fd security checks."""

    payload, _raw_sha256 = _read_private_json_and_raw_sha256(target)
    return payload


def _write_private_json_exclusive(
    parser: argparse.ArgumentParser,
    target: Path,
    payload: Mapping[str, Any],
) -> None:
    root = PRIVATE_OUTPUT_ROOT.resolve()
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    if _paths_overlap(root, CHECKOUT_ROOT.resolve()):
        parser.error("private output target is not isolated")
    os.chmod(root, 0o700)
    no_follow = getattr(os, "O_NOFOLLOW", 0)
    directory = getattr(os, "O_DIRECTORY", 0)
    relative_parts = target.relative_to(root).parts
    directory_fd = os.open(root, os.O_RDONLY | directory | no_follow)
    try:
        for part in relative_parts[:-1]:
            try:
                os.mkdir(part, mode=0o700, dir_fd=directory_fd)
            except FileExistsError:
                pass
            next_directory_fd = os.open(
                part,
                os.O_RDONLY | directory | no_follow,
                dir_fd=directory_fd,
            )
            os.close(directory_fd)
            directory_fd = next_directory_fd
            os.fchmod(directory_fd, 0o700)
        output_fd = os.open(
            relative_parts[-1],
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | no_follow,
            0o600,
            dir_fd=directory_fd,
        )
        os.fchmod(output_fd, 0o600)
        with os.fdopen(output_fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    finally:
        os.close(directory_fd)


def _open_private_output_parent(
    parser: argparse.ArgumentParser,
    target: Path,
) -> int:
    """Open/create a target parent below the owner-only private root."""

    root = PRIVATE_OUTPUT_ROOT.resolve()
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    if _paths_overlap(root, CHECKOUT_ROOT.resolve()):
        parser.error("private output target is not isolated")
    os.chmod(root, 0o700)
    try:
        relative_parts = target.parent.relative_to(root).parts
    except ValueError:
        parser.error("private output target is not isolated")
    no_follow = getattr(os, "O_NOFOLLOW", 0)
    directory = getattr(os, "O_DIRECTORY", 0)
    directory_fd = _open_directory_path_without_symlinks(root)
    owner_uid = os.geteuid()
    try:
        root_stat = os.fstat(directory_fd)
        if (
            not stat.S_ISDIR(root_stat.st_mode)
            or stat.S_IMODE(root_stat.st_mode) != 0o700
            or root_stat.st_uid != owner_uid
        ):
            parser.error("private output target is not isolated")
        for part in relative_parts:
            try:
                os.mkdir(part, mode=0o700, dir_fd=directory_fd)
            except FileExistsError:
                pass
            next_directory_fd = os.open(
                part,
                os.O_RDONLY | directory | no_follow,
                dir_fd=directory_fd,
            )
            next_stat = os.fstat(next_directory_fd)
            if (
                not stat.S_ISDIR(next_stat.st_mode)
                or next_stat.st_uid != owner_uid
            ):
                os.close(next_directory_fd)
                parser.error("private output target is not isolated")
            os.fchmod(next_directory_fd, 0o700)
            os.close(directory_fd)
            directory_fd = next_directory_fd
        return directory_fd
    except BaseException:
        os.close(directory_fd)
        raise


def _write_early_run_member_exclusive(
    directory_fd: int,
    filename: str,
    payload: Mapping[str, Any],
) -> None:
    """Write and fsync one fixed-name member inside an uncommitted run."""

    if filename not in EARLY_RUN_EXACT3_FILENAMES:
        raise ValueError("early exact3 member invalid")
    no_follow = getattr(os, "O_NOFOLLOW", 0)
    output_fd = os.open(
        filename,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | no_follow,
        0o600,
        dir_fd=directory_fd,
    )
    os.fchmod(output_fd, 0o600)
    with os.fdopen(output_fd, "wb") as handle:
        handle.write(_pretty_json_bytes(payload))
        handle.flush()
        os.fsync(handle.fileno())


def _rename_directory_noreplace(
    parent_fd: int,
    source_name: str,
    target_name: str,
) -> None:
    """Commit with Linux renameat2(RENAME_NOREPLACE), or fail closed."""

    libc = ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(libc, "renameat2", None)
    if renameat2 is None:
        raise OSError("atomic no-replace directory rename unavailable")
    renameat2.argtypes = (
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    )
    renameat2.restype = ctypes.c_int
    result = renameat2(
        parent_fd,
        os.fsencode(source_name),
        parent_fd,
        os.fsencode(target_name),
        1,  # RENAME_NOREPLACE
    )
    if result != 0:
        error_number = ctypes.get_errno()
        raise OSError(error_number, os.strerror(error_number))


def _preflight_rename_directory_noreplace(parent_fd: int) -> None:
    """Prove no-replace support on the exact output filesystem pre-run."""

    token = f"{os.getpid()}-{os.urandom(16).hex()}"
    source_name = f".cmee-renameat2-source-{token}"
    target_name = f".cmee-renameat2-target-{token}"
    source_created = False
    target_created = False
    try:
        os.mkdir(source_name, mode=0o700, dir_fd=parent_fd)
        source_created = True
        os.mkdir(target_name, mode=0o700, dir_fd=parent_fd)
        target_created = True
        try:
            _rename_directory_noreplace(parent_fd, source_name, target_name)
        except OSError as error:
            if error.errno != errno.EEXIST:
                raise
        else:
            raise OSError("atomic no-replace directory rename unavailable")
    finally:
        if source_created:
            try:
                os.rmdir(source_name, dir_fd=parent_fd)
            except FileNotFoundError:
                pass
        if target_created:
            try:
                os.rmdir(target_name, dir_fd=parent_fd)
            except FileNotFoundError:
                pass


def _prepare_early_run_exact3(
    parser: argparse.ArgumentParser,
    target: Path,
) -> tuple[int, str, int]:
    """Create the attempt marker before any generation call begins.

    A same-target staging directory is an attempt-consumed marker.  If a
    process is killed after this point, the next invocation fails terminally
    instead of silently retrying the protected actual run.
    """

    parent_fd = _open_private_output_parent(parser, target)
    staging_name = EARLY_ACTUAL_STAGING_DIRECTORY_NAME
    try:
        _preflight_rename_directory_noreplace(parent_fd)
        try:
            os.stat(target.name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise FileExistsError("early actual run output already exists")
        try:
            os.mkdir(staging_name, mode=0o700, dir_fd=parent_fd)
        except FileExistsError:
            raise RuntimeError("RUN_RESULT_UNKNOWN_TERMINAL") from None
        no_follow = getattr(os, "O_NOFOLLOW", 0)
        directory = getattr(os, "O_DIRECTORY", 0)
        staging_fd = os.open(
            staging_name,
            os.O_RDONLY | directory | no_follow,
            dir_fd=parent_fd,
        )
        os.fchmod(staging_fd, 0o700)
        os.fsync(parent_fd)
        return parent_fd, staging_name, staging_fd
    except BaseException:
        os.close(parent_fd)
        raise


def _close_early_run_exact3_transaction(
    transaction: tuple[int, str, int],
) -> None:
    """Close descriptors while retaining the terminal attempt marker."""

    parent_fd, _staging_name, staging_fd = transaction
    if staging_fd >= 0:
        try:
            os.close(staging_fd)
        except OSError:
            pass
    if parent_fd >= 0:
        try:
            os.close(parent_fd)
        except OSError:
            pass


def _validate_early_exact3_payloads(
    *,
    body_free_machine_packet: Mapping[str, Any],
    known_visible_packet: Mapping[str, Any],
    private_packet: Mapping[str, Any],
) -> None:
    """Validate all exact3 schemas and their cross-packet bindings."""

    _known, withheld = _validate_early_body_free_machine_packet(
        body_free_machine_packet,
        require_clear=False,
    )
    _validate_early_known_visible_packet(
        known_visible_packet,
        body_free_known_summary=body_free_machine_packet[
            "known_exact4_body_free"
        ],
    )
    _validate_early_private_packet(
        private_packet,
        early_attempt_id=body_free_machine_packet["early_attempt_id"],
        runtime_repo_head=body_free_machine_packet["runtime_repo_head"],
        design_repo_head=body_free_machine_packet["design_repo_head"],
        withheld_input_raw_sha256=body_free_machine_packet[
            "withheld_input_raw_sha256"
        ],
        withheld_set_digest=withheld["withheld_set_digest"],
        language_core_identity=body_free_machine_packet[
            "language_core_identity"
        ],
        stage1_runtime_integration_identity=body_free_machine_packet[
            "stage1_runtime_integration_identity"
        ],
        known_visible_packet=known_visible_packet,
        body_free_withheld_summary=withheld,
    )
    if (
        body_free_machine_packet["known_exact4_body_free"][
            "known_visible_packet_sha256"
        ]
        != _canonical_sha256(known_visible_packet)
        or body_free_machine_packet["private_packet_sha256"]
        != _canonical_sha256(private_packet)
    ):
        raise ValueError("early exact3 binding invalid")


def _commit_early_run_exact3(
    transaction: tuple[int, str, int],
    target: Path,
    *,
    body_free_machine_packet: Mapping[str, Any],
    known_visible_packet: Mapping[str, Any],
    private_packet: Mapping[str, Any],
) -> None:
    """Atomically publish fixed-name exact3 at the sole commit point."""

    parent_fd, staging_name, staging_fd = transaction
    closed = False
    try:
        _validate_early_exact3_payloads(
            body_free_machine_packet=body_free_machine_packet,
            known_visible_packet=known_visible_packet,
            private_packet=private_packet,
        )

        members = (
            (EARLY_RUN_KNOWN_VISIBLE_FILENAME, known_visible_packet),
            (EARLY_RUN_PRIVATE_PACKET_FILENAME, private_packet),
            (EARLY_RUN_BODY_FREE_MACHINE_FILENAME, body_free_machine_packet),
        )
        for filename, payload in members:
            _write_early_run_member_exclusive(staging_fd, filename, payload)
        os.fsync(staging_fd)
        os.close(staging_fd)
        transaction = (parent_fd, staging_name, -1)
        _rename_directory_noreplace(parent_fd, staging_name, target.name)
        os.fsync(parent_fd)
        os.close(parent_fd)
        closed = True
    finally:
        if not closed:
            _close_early_run_exact3_transaction(transaction)


def _read_committed_early_exact3_bytes(
    run_target: Path,
) -> dict[str, bytes]:
    """Read the committed fixed-name exact3 through owner-only dirfds."""

    root = PRIVATE_OUTPUT_ROOT.resolve()
    if run_target != root / EARLY_ACTUAL_RUN_DIRECTORY_NAME:
        raise ValueError("early exact3 private run directory invalid")
    no_follow = getattr(os, "O_NOFOLLOW", 0)
    directory = getattr(os, "O_DIRECTORY", 0)
    owner_uid = os.geteuid()
    root_fd = -1
    run_fd = -1
    try:
        root_fd = _open_directory_path_without_symlinks(root)
        root_stat = os.fstat(root_fd)
        if (
            not stat.S_ISDIR(root_stat.st_mode)
            or stat.S_IMODE(root_stat.st_mode) != 0o700
            or root_stat.st_uid != owner_uid
        ):
            raise ValueError("early exact3 private run directory invalid")
        run_fd = os.open(
            EARLY_ACTUAL_RUN_DIRECTORY_NAME,
            os.O_RDONLY | directory | no_follow,
            dir_fd=root_fd,
        )
        run_stat = os.fstat(run_fd)
        if (
            not stat.S_ISDIR(run_stat.st_mode)
            or stat.S_IMODE(run_stat.st_mode) != 0o700
            or run_stat.st_uid != owner_uid
            or set(os.listdir(run_fd)) != set(EARLY_RUN_EXACT3_FILENAMES)
        ):
            raise ValueError("early exact3 private run directory invalid")

        result: dict[str, bytes] = {}
        for filename in EARLY_RUN_EXACT3_FILENAMES:
            member_fd = os.open(
                filename,
                os.O_RDONLY | no_follow,
                dir_fd=run_fd,
            )
            try:
                member_stat = os.fstat(member_fd)
                if (
                    not stat.S_ISREG(member_stat.st_mode)
                    or stat.S_IMODE(member_stat.st_mode) != 0o600
                    or member_stat.st_uid != owner_uid
                    or member_stat.st_nlink != 1
                    or not 0 < member_stat.st_size <= 1024 * 1024
                ):
                    raise ValueError("early exact3 private member invalid")
                with os.fdopen(member_fd, "rb") as handle:
                    member_fd = -1
                    result[filename] = handle.read()
            finally:
                if member_fd >= 0:
                    os.close(member_fd)
        return result
    except OSError:
        raise ValueError("early exact3 private run directory invalid") from None
    finally:
        if run_fd >= 0:
            os.close(run_fd)
        if root_fd >= 0:
            os.close(root_fd)


def _validate_early_exact3_member_bytes(
    member_bytes: Mapping[str, bytes],
) -> dict[str, dict[str, Any]]:
    """Reconstruct exact member objects and enforce byte/schema bindings."""

    if type(member_bytes) is not dict or tuple(member_bytes) != (
        EARLY_RUN_EXACT3_FILENAMES
    ):
        raise ValueError("early exact3 member set invalid")
    payloads: dict[str, dict[str, Any]] = {}
    for filename in EARLY_RUN_EXACT3_FILENAMES:
        raw = member_bytes[filename]
        if type(raw) is not bytes or not 0 < len(raw) <= 1024 * 1024:
            raise ValueError("early exact3 member set invalid")
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ValueError("early exact3 member set invalid") from None
        if type(payload) is not dict or raw != _pretty_json_bytes(payload):
            raise ValueError("early exact3 member set invalid")
        payloads[filename] = payload

    _validate_early_exact3_payloads(
        body_free_machine_packet=payloads[
            EARLY_RUN_BODY_FREE_MACHINE_FILENAME
        ],
        known_visible_packet=payloads[EARLY_RUN_KNOWN_VISIBLE_FILENAME],
        private_packet=payloads[EARLY_RUN_PRIVATE_PACKET_FILENAME],
    )
    return payloads


def build_early_private_review_master_bytes(
    member_bytes: Mapping[str, bytes],
) -> bytes:
    """Build the deterministic body-full single-file review master."""

    payloads = _validate_early_exact3_member_bytes(member_bytes)
    machine = payloads[EARLY_RUN_BODY_FREE_MACHINE_FILENAME]
    master = {
        "schema_version": EARLY_PRIVATE_REVIEW_MASTER_SCHEMA_VERSION,
        "master_alias": EARLY_PRIVATE_REVIEW_MASTER_ALIAS,
        "master_kind": EARLY_PRIVATE_REVIEW_MASTER_KIND,
        "exact3_schema_version": EARLY_RUN_EXACT3_SCHEMA_VERSION,
        "packet_id": machine["packet_id"],
        "bounded_unit_id": machine["bounded_unit_id"],
        "early_attempt_id": machine["early_attempt_id"],
        "runtime_repo_head": machine["runtime_repo_head"],
        "design_repo_head": machine["design_repo_head"],
        "language_core_identity": machine["language_core_identity"],
        "stage1_runtime_integration_identity": machine[
            "stage1_runtime_integration_identity"
        ],
        "withheld_input_raw_sha256": machine[
            "withheld_input_raw_sha256"
        ],
        "withheld_set_digest": machine["withheld_set_digest"],
        "member_order": list(EARLY_RUN_EXACT3_FILENAMES),
        "members": [
            {
                "name": filename,
                "media_type": EARLY_PRIVATE_REVIEW_MASTER_MEMBER_MEDIA_TYPE,
                "byte_size": len(member_bytes[filename]),
                "sha256": hashlib.sha256(member_bytes[filename]).hexdigest(),
                "raw_base64": base64.b64encode(
                    member_bytes[filename]
                ).decode("ascii"),
            }
            for filename in EARLY_RUN_EXACT3_FILENAMES
        ],
    }
    return _canonical_json_line_bytes(master)


def _private_review_master_receipt(
    *,
    master: Mapping[str, Any],
    master_bytes: bytes,
    operation: str,
) -> dict[str, Any]:
    canonical_sha256_by_name: dict[str, str] = {}
    for member in master["members"]:
        raw = base64.b64decode(member["raw_base64"], validate=True)
        payload = json.loads(raw.decode("utf-8"))
        canonical_sha256_by_name[member["name"]] = _canonical_sha256(payload)
    return {
        "schema_version": (
            EARLY_PRIVATE_REVIEW_MASTER_RECEIPT_SCHEMA_VERSION
        ),
        "operation": operation,
        "master_alias": EARLY_PRIVATE_REVIEW_MASTER_ALIAS,
        "master_kind": master["master_kind"],
        "exact3_schema_version": master["exact3_schema_version"],
        "private_review_master_sha256": hashlib.sha256(
            master_bytes
        ).hexdigest(),
        "packet_id": master["packet_id"],
        "bounded_unit_id": master["bounded_unit_id"],
        "early_attempt_id": master["early_attempt_id"],
        "runtime_repo_head": master["runtime_repo_head"],
        "design_repo_head": master["design_repo_head"],
        "language_core_identity": master["language_core_identity"],
        "stage1_runtime_integration_identity": master[
            "stage1_runtime_integration_identity"
        ],
        "withheld_input_raw_sha256": master[
            "withheld_input_raw_sha256"
        ],
        "withheld_set_digest": master["withheld_set_digest"],
        "exact3_member_count": len(EARLY_RUN_EXACT3_FILENAMES),
        "exact3_member_order": list(EARLY_RUN_EXACT3_FILENAMES),
        "known_visible_packet_sha256": canonical_sha256_by_name[
            EARLY_RUN_KNOWN_VISIBLE_FILENAME
        ],
        "private_packet_sha256": canonical_sha256_by_name[
            EARLY_RUN_PRIVATE_PACKET_FILENAME
        ],
        "body_free_machine_packet_sha256": canonical_sha256_by_name[
            EARLY_RUN_BODY_FREE_MACHINE_FILENAME
        ],
        "reader": EARLY_PRIVATE_REVIEW_MASTER_READER,
        "lifecycle": EARLY_PRIVATE_REVIEW_MASTER_LIFECYCLE,
        "body_payload_present": False,
        "private_text_published": False,
        "source_actual_run_count": 1,
        "source_actual_retry_count": 0,
        "source_actual_rerun_count": 0,
        "seal_or_validation_actual_run_invoked": False,
    }


def validate_early_private_review_master_receipt(
    payload: object,
    *,
    body_free_machine_packet: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate the body-free bridge from exact3 to the durable master."""

    _validate_early_body_free_machine_packet(
        body_free_machine_packet,
        require_clear=False,
    )
    expected_keys = (
        "schema_version",
        "operation",
        "master_alias",
        "master_kind",
        "exact3_schema_version",
        "private_review_master_sha256",
        "packet_id",
        "bounded_unit_id",
        "early_attempt_id",
        "runtime_repo_head",
        "design_repo_head",
        "language_core_identity",
        "stage1_runtime_integration_identity",
        "withheld_input_raw_sha256",
        "withheld_set_digest",
        "exact3_member_count",
        "exact3_member_order",
        "known_visible_packet_sha256",
        "private_packet_sha256",
        "body_free_machine_packet_sha256",
        "reader",
        "lifecycle",
        "body_payload_present",
        "private_text_published",
        "source_actual_run_count",
        "source_actual_retry_count",
        "source_actual_rerun_count",
        "seal_or_validation_actual_run_invoked",
    )
    if type(payload) is not dict or set(payload) != set(expected_keys):
        raise ValueError("early private review master receipt invalid")
    machine_bindings = {
        "packet_id": body_free_machine_packet.get("packet_id"),
        "bounded_unit_id": body_free_machine_packet.get("bounded_unit_id"),
        "early_attempt_id": body_free_machine_packet.get("early_attempt_id"),
        "runtime_repo_head": body_free_machine_packet.get("runtime_repo_head"),
        "design_repo_head": body_free_machine_packet.get("design_repo_head"),
        "language_core_identity": body_free_machine_packet.get(
            "language_core_identity"
        ),
        "stage1_runtime_integration_identity": body_free_machine_packet.get(
            "stage1_runtime_integration_identity"
        ),
        "withheld_input_raw_sha256": body_free_machine_packet.get(
            "withheld_input_raw_sha256"
        ),
        "withheld_set_digest": body_free_machine_packet.get(
            "withheld_set_digest"
        ),
    }
    canonical_bindings = {
        "known_visible_packet_sha256": body_free_machine_packet.get(
            "known_exact4_body_free", {}
        ).get("known_visible_packet_sha256"),
        "private_packet_sha256": body_free_machine_packet.get(
            "private_packet_sha256"
        ),
        "body_free_machine_packet_sha256": _canonical_sha256(
            body_free_machine_packet
        ),
    }
    if (
        payload["schema_version"]
        != EARLY_PRIVATE_REVIEW_MASTER_RECEIPT_SCHEMA_VERSION
        or payload["operation"]
        not in {
            "SEALED_NEW",
            "SEALED_IDENTICAL_EXISTING",
            "VALIDATED_FRESH_MATERIALIZATION",
        }
        or payload["master_alias"] != EARLY_PRIVATE_REVIEW_MASTER_ALIAS
        or payload["master_kind"] != EARLY_PRIVATE_REVIEW_MASTER_KIND
        or payload["exact3_schema_version"]
        != EARLY_RUN_EXACT3_SCHEMA_VERSION
        or type(payload["private_review_master_sha256"]) is not str
        or re.fullmatch(
            r"[0-9a-f]{64}", payload["private_review_master_sha256"]
        )
        is None
        or any(payload[key] != value for key, value in machine_bindings.items())
        or any(
            payload[key] != value for key, value in canonical_bindings.items()
        )
        or type(payload["exact3_member_count"]) is not int
        or payload["exact3_member_count"] != len(EARLY_RUN_EXACT3_FILENAMES)
        or payload["exact3_member_order"]
        != list(EARLY_RUN_EXACT3_FILENAMES)
        or payload["reader"] != EARLY_PRIVATE_REVIEW_MASTER_READER
        or payload["lifecycle"] != EARLY_PRIVATE_REVIEW_MASTER_LIFECYCLE
        or payload["body_payload_present"] is not False
        or payload["private_text_published"] is not False
        or payload["seal_or_validation_actual_run_invoked"] is not False
        or type(payload["source_actual_run_count"]) is not int
        or payload["source_actual_run_count"] != 1
        or any(
            type(payload[field]) is not int or payload[field] != 0
            for field in (
                "source_actual_retry_count",
                "source_actual_rerun_count",
            )
        )
    ):
        raise ValueError("early private review master receipt invalid")

    return {key: payload[key] for key in expected_keys}


def validate_early_private_review_master_bytes(
    master_bytes: bytes,
    *,
    expected_master_sha256: str,
    operation: str = "VALIDATED_FRESH_MATERIALIZATION",
) -> tuple[dict[str, Any], dict[str, bytes]]:
    """Validate a fresh master and reconstruct byte-identical exact3."""

    if (
        type(master_bytes) is not bytes
        or not 0 < len(master_bytes) <= 4 * 1024 * 1024
        or re.fullmatch(r"[0-9a-f]{64}", expected_master_sha256) is None
        or hashlib.sha256(master_bytes).hexdigest()
        != expected_master_sha256
    ):
        raise ValueError("early private review master invalid")
    try:
        master = json.loads(master_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError("early private review master invalid") from None
    top_keys = {
        "schema_version",
        "master_alias",
        "master_kind",
        "exact3_schema_version",
        "packet_id",
        "bounded_unit_id",
        "early_attempt_id",
        "runtime_repo_head",
        "design_repo_head",
        "language_core_identity",
        "stage1_runtime_integration_identity",
        "withheld_input_raw_sha256",
        "withheld_set_digest",
        "member_order",
        "members",
    }
    member_keys = {
        "name",
        "media_type",
        "byte_size",
        "sha256",
        "raw_base64",
    }
    if (
        type(master) is not dict
        or set(master) != top_keys
        or master["schema_version"]
        != EARLY_PRIVATE_REVIEW_MASTER_SCHEMA_VERSION
        or master["master_alias"] != EARLY_PRIVATE_REVIEW_MASTER_ALIAS
        or master["master_kind"] != EARLY_PRIVATE_REVIEW_MASTER_KIND
        or master["exact3_schema_version"] != EARLY_RUN_EXACT3_SCHEMA_VERSION
        or master["early_attempt_id"] != EARLY_ACTUAL_ATTEMPT_ID
        or master["member_order"] != list(EARLY_RUN_EXACT3_FILENAMES)
        or type(master["members"]) is not list
        or len(master["members"]) != len(EARLY_RUN_EXACT3_FILENAMES)
        or master_bytes != _canonical_json_line_bytes(master)
    ):
        raise ValueError("early private review master invalid")

    reconstructed: dict[str, bytes] = {}
    for expected_name, member in zip(
        EARLY_RUN_EXACT3_FILENAMES,
        master["members"],
        strict=True,
    ):
        if (
            type(member) is not dict
            or set(member) != member_keys
            or member["name"] != expected_name
            or member["media_type"]
            != EARLY_PRIVATE_REVIEW_MASTER_MEMBER_MEDIA_TYPE
            or type(member["byte_size"]) is not int
            or not 0 < member["byte_size"] <= 1024 * 1024
            or type(member["sha256"]) is not str
            or re.fullmatch(r"[0-9a-f]{64}", member["sha256"]) is None
            or type(member["raw_base64"]) is not str
        ):
            raise ValueError("early private review master invalid")
        try:
            raw = base64.b64decode(member["raw_base64"], validate=True)
        except (ValueError, binascii.Error):
            raise ValueError("early private review master invalid") from None
        if (
            len(raw) != member["byte_size"]
            or hashlib.sha256(raw).hexdigest() != member["sha256"]
            or base64.b64encode(raw).decode("ascii") != member["raw_base64"]
        ):
            raise ValueError("early private review master invalid")
        reconstructed[expected_name] = raw

    payloads = _validate_early_exact3_member_bytes(reconstructed)
    machine = payloads[EARLY_RUN_BODY_FREE_MACHINE_FILENAME]
    binding_keys = (
        "packet_id",
        "bounded_unit_id",
        "early_attempt_id",
        "runtime_repo_head",
        "design_repo_head",
        "language_core_identity",
        "stage1_runtime_integration_identity",
        "withheld_input_raw_sha256",
        "withheld_set_digest",
    )
    if any(master[key] != machine[key] for key in binding_keys):
        raise ValueError("early private review master invalid")
    return (
        _private_review_master_receipt(
            master=master,
            master_bytes=master_bytes,
            operation=operation,
        ),
        reconstructed,
    )


def _read_private_review_master_file(target: Path) -> bytes:
    """Read the fixed master through an owner-only, single-link inode."""

    root = PRIVATE_OUTPUT_ROOT.resolve()
    if target != root / EARLY_PRIVATE_REVIEW_MASTER_ALIAS:
        raise ValueError("early private review master path invalid")
    no_follow = getattr(os, "O_NOFOLLOW", 0)
    owner_uid = os.geteuid()
    root_fd = -1
    file_fd = -1
    try:
        root_fd = _open_directory_path_without_symlinks(root)
        root_stat = os.fstat(root_fd)
        if (
            not stat.S_ISDIR(root_stat.st_mode)
            or stat.S_IMODE(root_stat.st_mode) != 0o700
            or root_stat.st_uid != owner_uid
        ):
            raise ValueError("early private review master path invalid")
        file_fd = os.open(
            EARLY_PRIVATE_REVIEW_MASTER_ALIAS,
            os.O_RDONLY | no_follow,
            dir_fd=root_fd,
        )
        file_stat = os.fstat(file_fd)
        if (
            not stat.S_ISREG(file_stat.st_mode)
            or stat.S_IMODE(file_stat.st_mode) != 0o600
            or file_stat.st_uid != owner_uid
            or file_stat.st_nlink != 1
            or not 0 < file_stat.st_size <= 4 * 1024 * 1024
        ):
            raise ValueError("early private review master path invalid")
        with os.fdopen(file_fd, "rb") as handle:
            file_fd = -1
            return handle.read()
    except OSError:
        raise ValueError("early private review master path invalid") from None
    finally:
        if file_fd >= 0:
            os.close(file_fd)
        if root_fd >= 0:
            os.close(root_fd)


def seal_early_private_review_master(
    parser: argparse.ArgumentParser,
    *,
    run_target: Path,
    master_target: Path,
) -> dict[str, Any]:
    """Seal or idempotently reuse the deterministic master without rerun."""

    member_bytes = _read_committed_early_exact3_bytes(run_target)
    master_bytes = build_early_private_review_master_bytes(member_bytes)
    expected_sha256 = hashlib.sha256(master_bytes).hexdigest()
    root = PRIVATE_OUTPUT_ROOT.resolve()
    if master_target != root / EARLY_PRIVATE_REVIEW_MASTER_ALIAS:
        raise ValueError("early private review master path invalid")
    try:
        existing = _read_private_review_master_file(master_target)
    except ValueError:
        try:
            master_target.lstat()
        except FileNotFoundError:
            existing = None
        else:
            raise
    if existing is not None:
        if existing != master_bytes:
            raise ValueError("early private review master existing mismatch")
        receipt, _reconstructed = validate_early_private_review_master_bytes(
            existing,
            expected_master_sha256=expected_sha256,
            operation="SEALED_IDENTICAL_EXISTING",
        )
        return receipt

    root_fd = _open_private_output_parent(parser, master_target)
    staging_name = (
        f".{EARLY_PRIVATE_REVIEW_MASTER_ALIAS}.staging-"
        f"{os.getpid()}-{os.urandom(16).hex()}"
    )
    stage_created = False
    operation = "SEALED_NEW"
    try:
        no_follow = getattr(os, "O_NOFOLLOW", 0)
        stage_fd = os.open(
            staging_name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | no_follow,
            0o600,
            dir_fd=root_fd,
        )
        stage_created = True
        os.fchmod(stage_fd, 0o600)
        with os.fdopen(stage_fd, "wb") as handle:
            handle.write(master_bytes)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            _rename_directory_noreplace(
                root_fd,
                staging_name,
                EARLY_PRIVATE_REVIEW_MASTER_ALIAS,
            )
        except OSError as error:
            if error.errno != errno.EEXIST:
                raise
            operation = "SEALED_IDENTICAL_EXISTING"
        else:
            stage_created = False
            os.fsync(root_fd)
    finally:
        if stage_created:
            try:
                os.unlink(staging_name, dir_fd=root_fd)
            except FileNotFoundError:
                pass
        os.close(root_fd)

    materialized = _read_private_review_master_file(master_target)
    if materialized != master_bytes:
        raise ValueError("early private review master existing mismatch")
    receipt, _reconstructed = validate_early_private_review_master_bytes(
        materialized,
        expected_master_sha256=expected_sha256,
        operation=operation,
    )
    return receipt


def _validate_fresh_private_review_master_materialization(
    *,
    master_bytes: bytes,
    private_review_master_receipt: object,
) -> tuple[dict[str, Any], dict[str, bytes]]:
    """Bind a fresh body-full master read to its body-free receipt."""

    if type(private_review_master_receipt) is not dict:
        raise ValueError("early private review master fresh binding invalid")
    expected_sha256 = private_review_master_receipt.get(
        "private_review_master_sha256"
    )
    if (
        type(expected_sha256) is not str
        or re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None
    ):
        raise ValueError("early private review master fresh binding invalid")
    derived_receipt, reconstructed = (
        validate_early_private_review_master_bytes(
            master_bytes,
            expected_master_sha256=expected_sha256,
            operation="VALIDATED_FRESH_MATERIALIZATION",
        )
    )
    machine = json.loads(
        reconstructed[EARLY_RUN_BODY_FREE_MACHINE_FILENAME].decode("utf-8")
    )
    validated_receipt = validate_early_private_review_master_receipt(
        private_review_master_receipt,
        body_free_machine_packet=machine,
    )
    if (
        validated_receipt["operation"]
        != "VALIDATED_FRESH_MATERIALIZATION"
        or validated_receipt != derived_receipt
    ):
        raise ValueError("early private review master fresh binding invalid")
    return validated_receipt, reconstructed


def build_early_known_review_auxiliary_bytes(
    *,
    master_bytes: bytes,
    private_review_master_receipt: object,
) -> bytes:
    """Build Ultra's known-only auxiliary from one fresh-validated master."""

    receipt, reconstructed = (
        _validate_fresh_private_review_master_materialization(
            master_bytes=master_bytes,
            private_review_master_receipt=private_review_master_receipt,
        )
    )
    known_visible_payload = json.loads(
        reconstructed[EARLY_RUN_KNOWN_VISIBLE_FILENAME].decode("utf-8")
    )
    auxiliary = {
        "schema_version": EARLY_KNOWN_REVIEW_AUXILIARY_SCHEMA_VERSION,
        "auxiliary_kind": EARLY_KNOWN_REVIEW_AUXILIARY_KIND,
        "auxiliary_alias": EARLY_KNOWN_REVIEW_AUXILIARY_ALIAS,
        "early_attempt_id": EARLY_ACTUAL_ATTEMPT_ID,
        "private_review_master_sha256": receipt[
            "private_review_master_sha256"
        ],
        "known_visible_packet_sha256": receipt[
            "known_visible_packet_sha256"
        ],
        "known_visible_payload": known_visible_payload,
    }
    return _canonical_json_line_bytes(auxiliary)


def _early_known_review_auxiliary_receipt(
    *,
    auxiliary: Mapping[str, Any],
    auxiliary_bytes: bytes,
    operation: str,
) -> dict[str, Any]:
    return {
        "schema_version": (
            EARLY_KNOWN_REVIEW_AUXILIARY_RECEIPT_SCHEMA_VERSION
        ),
        "operation": operation,
        "auxiliary_alias": EARLY_KNOWN_REVIEW_AUXILIARY_ALIAS,
        "auxiliary_kind": EARLY_KNOWN_REVIEW_AUXILIARY_KIND,
        "early_attempt_id": EARLY_ACTUAL_ATTEMPT_ID,
        "private_review_master_sha256": auxiliary[
            "private_review_master_sha256"
        ],
        "known_visible_packet_sha256": auxiliary[
            "known_visible_packet_sha256"
        ],
        "early_known_review_auxiliary_sha256": hashlib.sha256(
            auxiliary_bytes
        ).hexdigest(),
        "reader": EARLY_KNOWN_REVIEW_AUXILIARY_READER,
        "lifecycle": EARLY_KNOWN_REVIEW_AUXILIARY_LIFECYCLE,
        "body_payload_present": False,
        "private_text_published": False,
        "source_actual_run_count": 1,
        "source_actual_retry_count": 0,
        "source_actual_rerun_count": 0,
        "seal_or_validation_actual_run_invoked": False,
    }


def validate_early_known_review_auxiliary_receipt(
    payload: object,
    *,
    body_free_machine_packet: Mapping[str, Any],
    private_review_master_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate the body-free bridge from fresh master to known auxiliary."""

    master_receipt = validate_early_private_review_master_receipt(
        private_review_master_receipt,
        body_free_machine_packet=body_free_machine_packet,
    )
    expected_keys = (
        "schema_version",
        "operation",
        "auxiliary_alias",
        "auxiliary_kind",
        "early_attempt_id",
        "private_review_master_sha256",
        "known_visible_packet_sha256",
        "early_known_review_auxiliary_sha256",
        "reader",
        "lifecycle",
        "body_payload_present",
        "private_text_published",
        "source_actual_run_count",
        "source_actual_retry_count",
        "source_actual_rerun_count",
        "seal_or_validation_actual_run_invoked",
    )
    if type(payload) is not dict or set(payload) != set(expected_keys):
        raise ValueError("early known review auxiliary receipt invalid")
    if (
        master_receipt["operation"] != "VALIDATED_FRESH_MATERIALIZATION"
        or payload["schema_version"]
        != EARLY_KNOWN_REVIEW_AUXILIARY_RECEIPT_SCHEMA_VERSION
        or payload["operation"]
        not in {
            "SEALED_NEW",
            "SEALED_IDENTICAL_EXISTING",
            "VALIDATED_FRESH_MATERIALIZATION",
        }
        or payload["auxiliary_alias"]
        != EARLY_KNOWN_REVIEW_AUXILIARY_ALIAS
        or payload["auxiliary_kind"]
        != EARLY_KNOWN_REVIEW_AUXILIARY_KIND
        or payload["early_attempt_id"] != EARLY_ACTUAL_ATTEMPT_ID
        or payload["early_attempt_id"]
        != body_free_machine_packet["early_attempt_id"]
        or payload["private_review_master_sha256"]
        != master_receipt["private_review_master_sha256"]
        or payload["known_visible_packet_sha256"]
        != master_receipt["known_visible_packet_sha256"]
        or type(payload["early_known_review_auxiliary_sha256"]) is not str
        or re.fullmatch(
            r"[0-9a-f]{64}",
            payload["early_known_review_auxiliary_sha256"],
        )
        is None
        or payload["reader"] != EARLY_KNOWN_REVIEW_AUXILIARY_READER
        or payload["lifecycle"]
        != EARLY_KNOWN_REVIEW_AUXILIARY_LIFECYCLE
        or payload["body_payload_present"] is not False
        or payload["private_text_published"] is not False
        or payload["seal_or_validation_actual_run_invoked"] is not False
        or type(payload["source_actual_run_count"]) is not int
        or payload["source_actual_run_count"] != 1
        or any(
            type(payload[field]) is not int or payload[field] != 0
            for field in (
                "source_actual_retry_count",
                "source_actual_rerun_count",
            )
        )
    ):
        raise ValueError("early known review auxiliary receipt invalid")
    return {key: payload[key] for key in expected_keys}


def validate_early_known_review_auxiliary_bytes(
    auxiliary_bytes: bytes,
    *,
    expected_auxiliary_sha256: str,
    master_bytes: bytes,
    private_review_master_receipt: object,
    operation: str = "VALIDATED_FRESH_MATERIALIZATION",
) -> dict[str, Any]:
    """Validate known-only bytes against a fresh master and receipt."""

    if (
        type(auxiliary_bytes) is not bytes
        or not 0 < len(auxiliary_bytes) <= 2 * 1024 * 1024
        or type(expected_auxiliary_sha256) is not str
        or re.fullmatch(r"[0-9a-f]{64}", expected_auxiliary_sha256) is None
        or hashlib.sha256(auxiliary_bytes).hexdigest()
        != expected_auxiliary_sha256
        or operation
        not in {
            "SEALED_NEW",
            "SEALED_IDENTICAL_EXISTING",
            "VALIDATED_FRESH_MATERIALIZATION",
        }
    ):
        raise ValueError("early known review auxiliary invalid")
    master_receipt, reconstructed = (
        _validate_fresh_private_review_master_materialization(
            master_bytes=master_bytes,
            private_review_master_receipt=private_review_master_receipt,
        )
    )
    try:
        auxiliary = json.loads(auxiliary_bytes.decode("utf-8"))
        known_visible_payload = json.loads(
            reconstructed[EARLY_RUN_KNOWN_VISIBLE_FILENAME].decode("utf-8")
        )
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError("early known review auxiliary invalid") from None
    expected_keys = {
        "schema_version",
        "auxiliary_kind",
        "auxiliary_alias",
        "early_attempt_id",
        "private_review_master_sha256",
        "known_visible_packet_sha256",
        "known_visible_payload",
    }
    if (
        type(auxiliary) is not dict
        or set(auxiliary) != expected_keys
        or auxiliary["schema_version"]
        != EARLY_KNOWN_REVIEW_AUXILIARY_SCHEMA_VERSION
        or auxiliary["auxiliary_kind"]
        != EARLY_KNOWN_REVIEW_AUXILIARY_KIND
        or auxiliary["auxiliary_alias"]
        != EARLY_KNOWN_REVIEW_AUXILIARY_ALIAS
        or auxiliary["early_attempt_id"] != EARLY_ACTUAL_ATTEMPT_ID
        or auxiliary["private_review_master_sha256"]
        != master_receipt["private_review_master_sha256"]
        or auxiliary["known_visible_packet_sha256"]
        != master_receipt["known_visible_packet_sha256"]
        or auxiliary["known_visible_payload"] != known_visible_payload
        or _canonical_sha256(auxiliary["known_visible_payload"])
        != auxiliary["known_visible_packet_sha256"]
        or auxiliary_bytes != _canonical_json_line_bytes(auxiliary)
    ):
        raise ValueError("early known review auxiliary invalid")
    return _early_known_review_auxiliary_receipt(
        auxiliary=auxiliary,
        auxiliary_bytes=auxiliary_bytes,
        operation=operation,
    )


def _read_early_known_review_auxiliary_file(target: Path) -> bytes:
    """Read the fixed known-only auxiliary through an owner-only inode."""

    root = PRIVATE_OUTPUT_ROOT.resolve()
    if target != root / EARLY_KNOWN_REVIEW_AUXILIARY_ALIAS:
        raise ValueError("early known review auxiliary path invalid")
    no_follow = getattr(os, "O_NOFOLLOW", 0)
    owner_uid = os.geteuid()
    root_fd = -1
    file_fd = -1
    try:
        root_fd = _open_directory_path_without_symlinks(root)
        root_stat = os.fstat(root_fd)
        if (
            not stat.S_ISDIR(root_stat.st_mode)
            or stat.S_IMODE(root_stat.st_mode) != 0o700
            or root_stat.st_uid != owner_uid
        ):
            raise ValueError("early known review auxiliary path invalid")
        file_fd = os.open(
            EARLY_KNOWN_REVIEW_AUXILIARY_ALIAS,
            os.O_RDONLY | no_follow,
            dir_fd=root_fd,
        )
        file_stat = os.fstat(file_fd)
        if (
            not stat.S_ISREG(file_stat.st_mode)
            or stat.S_IMODE(file_stat.st_mode) != 0o600
            or file_stat.st_uid != owner_uid
            or file_stat.st_nlink != 1
            or not 0 < file_stat.st_size <= 2 * 1024 * 1024
        ):
            raise ValueError("early known review auxiliary path invalid")
        with os.fdopen(file_fd, "rb") as handle:
            file_fd = -1
            return handle.read()
    except OSError:
        raise ValueError("early known review auxiliary path invalid") from None
    finally:
        if file_fd >= 0:
            os.close(file_fd)
        if root_fd >= 0:
            os.close(root_fd)


def seal_early_known_review_auxiliary(
    parser: argparse.ArgumentParser,
    *,
    master_target: Path,
    private_review_master_receipt: object,
    auxiliary_target: Path,
) -> dict[str, Any]:
    """Seal or idempotently reuse Ultra's deterministic known-only file."""

    master_bytes = _read_private_review_master_file(master_target)
    auxiliary_bytes = build_early_known_review_auxiliary_bytes(
        master_bytes=master_bytes,
        private_review_master_receipt=private_review_master_receipt,
    )
    expected_sha256 = hashlib.sha256(auxiliary_bytes).hexdigest()
    root = PRIVATE_OUTPUT_ROOT.resolve()
    if auxiliary_target != root / EARLY_KNOWN_REVIEW_AUXILIARY_ALIAS:
        raise ValueError("early known review auxiliary path invalid")
    try:
        existing = _read_early_known_review_auxiliary_file(auxiliary_target)
    except ValueError:
        try:
            auxiliary_target.lstat()
        except FileNotFoundError:
            existing = None
        else:
            raise
    if existing is not None:
        if existing != auxiliary_bytes:
            raise ValueError("early known review auxiliary existing mismatch")
        return validate_early_known_review_auxiliary_bytes(
            existing,
            expected_auxiliary_sha256=expected_sha256,
            master_bytes=master_bytes,
            private_review_master_receipt=private_review_master_receipt,
            operation="SEALED_IDENTICAL_EXISTING",
        )

    root_fd = _open_private_output_parent(parser, auxiliary_target)
    staging_name = (
        f".{EARLY_KNOWN_REVIEW_AUXILIARY_ALIAS}.staging-"
        f"{os.getpid()}-{os.urandom(16).hex()}"
    )
    stage_created = False
    operation = "SEALED_NEW"
    try:
        no_follow = getattr(os, "O_NOFOLLOW", 0)
        stage_fd = os.open(
            staging_name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | no_follow,
            0o600,
            dir_fd=root_fd,
        )
        stage_created = True
        os.fchmod(stage_fd, 0o600)
        with os.fdopen(stage_fd, "wb") as handle:
            handle.write(auxiliary_bytes)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            _rename_directory_noreplace(
                root_fd,
                staging_name,
                EARLY_KNOWN_REVIEW_AUXILIARY_ALIAS,
            )
        except OSError as error:
            if error.errno != errno.EEXIST:
                raise
            operation = "SEALED_IDENTICAL_EXISTING"
        else:
            stage_created = False
            os.fsync(root_fd)
    finally:
        if stage_created:
            try:
                os.unlink(staging_name, dir_fd=root_fd)
            except FileNotFoundError:
                pass
        os.close(root_fd)

    materialized = _read_early_known_review_auxiliary_file(auxiliary_target)
    if materialized != auxiliary_bytes:
        raise ValueError("early known review auxiliary existing mismatch")
    return validate_early_known_review_auxiliary_bytes(
        materialized,
        expected_auxiliary_sha256=expected_sha256,
        master_bytes=master_bytes,
        private_review_master_receipt=private_review_master_receipt,
        operation=operation,
    )


def _read_body_free_json(
    parser: argparse.ArgumentParser,
    target: Path,
) -> object:
    """Read a bounded body-free finalization input without echoing content."""

    try:
        file_stat = target.stat()
        if (
            not stat.S_ISREG(file_stat.st_mode)
            or not 0 < file_stat.st_size <= 64 * 1024
        ):
            parser.error("early finalization body-free input invalid")
        with target.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        parser.error("early finalization body-free input invalid")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--body-full-output", type=Path)
    parser.add_argument("--runtime-repo-head")
    parser.add_argument("--design-repo-head")
    parser.add_argument("--early-actual", action="store_true")
    parser.add_argument("--early-attempt-id")
    parser.add_argument(
        "--seal-early-private-review-master",
        action="store_true",
    )
    parser.add_argument(
        "--validate-early-private-review-master",
        action="store_true",
    )
    parser.add_argument("--early-private-review-master", type=Path)
    parser.add_argument("--expected-private-review-master-sha256")
    parser.add_argument(
        "--seal-early-known-review-auxiliary",
        action="store_true",
    )
    parser.add_argument(
        "--validate-early-known-review-auxiliary",
        action="store_true",
    )
    parser.add_argument("--early-known-review-auxiliary", type=Path)
    parser.add_argument("--expected-early-known-review-auxiliary-sha256")
    parser.add_argument("--finalize-early-actual", action="store_true")
    parser.add_argument("--withheld-input", type=Path)
    parser.add_argument("--known-visible-output", type=Path)
    parser.add_argument("--early-run-output-dir", type=Path)
    parser.add_argument("--early-machine-body-free-input", type=Path)
    parser.add_argument("--early-master-body-free-input", type=Path)
    parser.add_argument(
        "--early-known-auxiliary-body-free-input",
        type=Path,
    )
    parser.add_argument("--early-pro-body-free-input", type=Path)
    parser.add_argument("--early-ultra-body-free-input", type=Path)
    args = parser.parse_args()
    finalizer_inputs = (
        args.early_machine_body_free_input,
        args.early_master_body_free_input,
        args.early_known_auxiliary_body_free_input,
        args.early_pro_body_free_input,
        args.early_ultra_body_free_input,
    )
    master_modes = (
        args.seal_early_private_review_master,
        args.validate_early_private_review_master,
    )
    auxiliary_modes = (
        args.seal_early_known_review_auxiliary,
        args.validate_early_known_review_auxiliary,
    )
    if any(auxiliary_modes):
        seal_mode, validate_mode = auxiliary_modes
        if (
            all(auxiliary_modes)
            or any(master_modes)
            or args.early_actual
            or args.finalize_early_actual
            or args.body_full_output is not None
            or args.withheld_input is not None
            or args.known_visible_output is not None
            or args.early_run_output_dir is not None
            or args.runtime_repo_head is not None
            or args.design_repo_head is not None
            or args.early_machine_body_free_input is not None
            or args.early_known_auxiliary_body_free_input is not None
            or args.early_pro_body_free_input is not None
            or args.early_ultra_body_free_input is not None
            or args.early_master_body_free_input is None
            or args.early_attempt_id != EARLY_ACTUAL_ATTEMPT_ID
            or args.early_private_review_master is None
            or args.expected_private_review_master_sha256 is not None
            or args.early_known_review_auxiliary is None
            or (
                seal_mode
                and args.expected_early_known_review_auxiliary_sha256
                is not None
            )
            or (
                validate_mode
                and re.fullmatch(
                    r"[0-9a-f]{64}",
                    str(
                        args.expected_early_known_review_auxiliary_sha256
                        or ""
                    ),
                )
                is None
            )
        ):
            parser.error("early known review auxiliary mode invalid")
        master_target = _private_input_target(
            parser,
            args.early_private_review_master,
        )
        auxiliary_target = _private_input_target(
            parser,
            args.early_known_review_auxiliary,
        )
        private_root = Path(
            os.path.abspath(os.fspath(PRIVATE_OUTPUT_ROOT))
        )
        if (
            master_target
            != private_root / EARLY_PRIVATE_REVIEW_MASTER_ALIAS
            or auxiliary_target
            != private_root / EARLY_KNOWN_REVIEW_AUXILIARY_ALIAS
        ):
            parser.error("early known review auxiliary path invalid")
        master_receipt = _read_body_free_json(
            parser,
            args.early_master_body_free_input,
        )
        try:
            if seal_mode:
                receipt = seal_early_known_review_auxiliary(
                    parser,
                    master_target=master_target,
                    private_review_master_receipt=master_receipt,
                    auxiliary_target=auxiliary_target,
                )
            else:
                master_bytes = _read_private_review_master_file(master_target)
                auxiliary_bytes = (
                    _read_early_known_review_auxiliary_file(auxiliary_target)
                )
                receipt = validate_early_known_review_auxiliary_bytes(
                    auxiliary_bytes,
                    expected_auxiliary_sha256=(
                        args.expected_early_known_review_auxiliary_sha256
                    ),
                    master_bytes=master_bytes,
                    private_review_master_receipt=master_receipt,
                )
        except (OSError, ValueError, RuntimeError, json.JSONDecodeError):
            parser.error("early known review auxiliary validation invalid")
        print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
        return 0
    if any(master_modes):
        seal_mode, validate_mode = master_modes
        if (
            all(master_modes)
            or args.early_actual
            or args.finalize_early_actual
            or args.body_full_output is not None
            or args.withheld_input is not None
            or args.known_visible_output is not None
            or args.runtime_repo_head is not None
            or args.design_repo_head is not None
            or any(target is not None for target in finalizer_inputs)
            or any(auxiliary_modes)
            or args.early_known_review_auxiliary is not None
            or args.expected_early_known_review_auxiliary_sha256 is not None
            or args.early_attempt_id != EARLY_ACTUAL_ATTEMPT_ID
            or args.early_private_review_master is None
            or (seal_mode and args.early_run_output_dir is None)
            or (
                seal_mode
                and args.expected_private_review_master_sha256 is not None
            )
            or (validate_mode and args.early_run_output_dir is not None)
            or (
                validate_mode
                and re.fullmatch(
                    r"[0-9a-f]{64}",
                    str(args.expected_private_review_master_sha256 or ""),
                )
                is None
            )
        ):
            parser.error("early private review master mode invalid")
        master_target = _private_input_target(
            parser,
            args.early_private_review_master,
        )
        if master_target != (
            Path(os.path.abspath(os.fspath(PRIVATE_OUTPUT_ROOT)))
            / EARLY_PRIVATE_REVIEW_MASTER_ALIAS
        ):
            parser.error("early private review master path invalid")
        try:
            if seal_mode:
                run_target = _private_input_target(
                    parser,
                    args.early_run_output_dir,
                )
                if run_target != (
                    Path(os.path.abspath(os.fspath(PRIVATE_OUTPUT_ROOT)))
                    / EARLY_ACTUAL_RUN_DIRECTORY_NAME
                ):
                    parser.error("early exact3 private run directory invalid")
                receipt = seal_early_private_review_master(
                    parser,
                    run_target=run_target,
                    master_target=master_target,
                )
            else:
                master_bytes = _read_private_review_master_file(master_target)
                receipt, _reconstructed = (
                    validate_early_private_review_master_bytes(
                        master_bytes,
                        expected_master_sha256=(
                            args.expected_private_review_master_sha256
                        ),
                    )
                )
        except (OSError, ValueError, RuntimeError, json.JSONDecodeError):
            parser.error("early private review master validation invalid")
        print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
        return 0
    if args.finalize_early_actual:
        if (
            any(target is None for target in finalizer_inputs)
            or args.early_actual
            or args.body_full_output is not None
            or args.withheld_input is not None
            or args.known_visible_output is not None
            or args.early_run_output_dir is not None
            or args.early_attempt_id is not None
            or args.runtime_repo_head is not None
            or args.design_repo_head is not None
            or any(master_modes)
            or args.early_private_review_master is not None
            or args.expected_private_review_master_sha256 is not None
            or any(auxiliary_modes)
            or args.early_known_review_auxiliary is not None
            or args.expected_early_known_review_auxiliary_sha256 is not None
        ):
            parser.error("early finalization requires body-free input exact5")
        try:
            (
                machine_packet,
                master_receipt,
                auxiliary_receipt,
                pro_result,
                ultra_result,
            ) = (
                _read_body_free_json(parser, target)
                for target in finalizer_inputs
                if target is not None
            )
            receipt = finalize_early_actual_body_free(
                body_free_machine_packet=machine_packet,
                private_review_master_receipt=master_receipt,
                early_known_review_auxiliary_receipt=auxiliary_receipt,
                pro_human_read_result=pro_result,
                ultra_known_technical_result=ultra_result,
            )
        except ValueError:
            parser.error("early finalization binding invalid")
        print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
        return (
            0
            if receipt["early_actual_status"]
            == "LANGUAGE_VIABILITY_OBSERVED"
            else 1
        )
    if any(target is not None for target in finalizer_inputs):
        parser.error("early finalization inputs require finalization mode")
    if (
        args.early_private_review_master is not None
        or args.expected_private_review_master_sha256 is not None
        or args.early_known_review_auxiliary is not None
        or args.expected_early_known_review_auxiliary_sha256 is not None
    ):
        parser.error("early review artifact requires matching mode")
    if args.early_actual:
        if (
            args.withheld_input is None
            or args.early_run_output_dir is None
            or args.early_attempt_id != EARLY_ACTUAL_ATTEMPT_ID
            or args.known_visible_output is not None
            or args.body_full_output is not None
        ):
            parser.error(
                "early actual requires isolated input and transactional exact3 output"
            )
        input_target = _private_input_target(parser, args.withheld_input)
        run_output_target = _private_output_target(
            parser,
            args.early_run_output_dir,
        )
        if run_output_target != (
            PRIVATE_OUTPUT_ROOT.resolve() / EARLY_ACTUAL_RUN_DIRECTORY_NAME
        ):
            parser.error("early actual attempt output slot binding invalid")
        if _paths_overlap(input_target, run_output_target):
            parser.error("early actual input and exact3 output must be distinct")
        _require_new_private_output_targets(
            parser,
            (run_output_target,),
        )
        _require_unconsumed_early_attempt(parser, run_output_target)
        if (
            re.fullmatch(r"[0-9a-f]{40}", str(args.runtime_repo_head or ""))
            is None
            or re.fullmatch(r"[0-9a-f]{40}", str(args.design_repo_head or ""))
            is None
        ):
            parser.error("early private packet repo head binding invalid")
        try:
            _validate_early_runtime_checkout(args.runtime_repo_head)
            _current_frozen_early_identity_pair()
            (
                withheld_payload,
                withheld_input_raw_sha256,
            ) = _read_private_json_and_raw_sha256(input_target)
            _validate_frozen_withheld_early_payload(
                withheld_payload,
                raw_sha256=withheld_input_raw_sha256,
            )
        except (OSError, ValueError, RuntimeError, json.JSONDecodeError):
            parser.error("early actual private preflight failed")
        try:
            transaction = _prepare_early_run_exact3(
                parser,
                run_output_target,
            )
        except RuntimeError:
            parser.error("early actual RUN_RESULT_UNKNOWN_TERMINAL; retry prohibited")
        except OSError:
            parser.error("early actual transaction preflight failed")
        try:
            body_free_packet, known_visible, private_packet = run_early_actual(
                withheld_private_payload=withheld_payload,
                withheld_input_raw_sha256=withheld_input_raw_sha256,
                early_attempt_id=args.early_attempt_id,
                runtime_repo_head=args.runtime_repo_head,
                design_repo_head=args.design_repo_head,
            )
            _validate_early_runtime_checkout(args.runtime_repo_head)
            _commit_early_run_exact3(
                transaction,
                run_output_target,
                body_free_machine_packet=body_free_packet,
                known_visible_packet=known_visible,
                private_packet=private_packet,
            )
        except (OSError, ValueError, RuntimeError, json.JSONDecodeError):
            _close_early_run_exact3_transaction(transaction)
            parser.error(
                "early actual RUN_RESULT_UNKNOWN_TERMINAL; retry prohibited"
            )
        print(json.dumps(body_free_packet, ensure_ascii=False, sort_keys=True))
        return (
            0
            if _early_exact8_machine_is_clear(
                body_free_packet["known_exact4_body_free"],
                body_free_packet["withheld_exact4_body_free"],
            )
            else 1
        )
    if (
        args.withheld_input is not None
        or args.known_visible_output is not None
        or args.early_run_output_dir is not None
        or args.early_attempt_id is not None
    ):
        parser.error("early-only input or output requires early actual mode")
    target: Path | None = None
    if args.body_full_output is not None:
        target = _private_output_target(parser, args.body_full_output)
        if (
            re.fullmatch(r"[0-9a-f]{40}", str(args.runtime_repo_head or ""))
            is None
            or re.fullmatch(r"[0-9a-f]{40}", str(args.design_repo_head or ""))
            is None
        ):
            parser.error("private packet repo head binding invalid")
    body_free, full = run(
        runtime_repo_head=args.runtime_repo_head if target is not None else None,
        design_repo_head=args.design_repo_head if target is not None else None,
    )
    if target is not None:
        root = PRIVATE_OUTPUT_ROOT.resolve()
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
        if _paths_overlap(root, CHECKOUT_ROOT.resolve()):
            parser.error("private output target is not isolated")
        os.chmod(root, 0o700)
        no_follow = getattr(os, "O_NOFOLLOW", 0)
        directory = getattr(os, "O_DIRECTORY", 0)
        relative_parts = target.relative_to(root).parts
        directory_fd = os.open(root, os.O_RDONLY | directory | no_follow)
        try:
            for part in relative_parts[:-1]:
                try:
                    os.mkdir(part, mode=0o700, dir_fd=directory_fd)
                except FileExistsError:
                    pass
                next_directory_fd = os.open(
                    part,
                    os.O_RDONLY | directory | no_follow,
                    dir_fd=directory_fd,
                )
                os.close(directory_fd)
                directory_fd = next_directory_fd
                os.fchmod(directory_fd, 0o700)
            output_fd = os.open(
                relative_parts[-1],
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | no_follow,
                0o600,
                dir_fd=directory_fd,
            )
            os.fchmod(output_fd, 0o600)
            with os.fdopen(output_fd, "w", encoding="utf-8") as handle:
                handle.write(json.dumps(full, ensure_ascii=False, indent=2) + "\n")
        finally:
            os.close(directory_fd)
    print(json.dumps(body_free, ensure_ascii=False, sort_keys=True))
    # Candidate generation gaps are reported, not hidden by fixture tuning.
    # A complete packet is not the same thing as a successful candidate run.
    return 0 if body_free["structural_trace_valid_count"] == len(EXACT8) else 1


if __name__ == "__main__":
    raise SystemExit(main())
