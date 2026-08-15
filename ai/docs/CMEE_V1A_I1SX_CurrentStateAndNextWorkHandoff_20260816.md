# CMEE V1-A I1-SX Current State and Next Work Handoff — 2026-08-16

## 0. この文書の役割

この文書は、`MassyuRed/mashos-api` の CMEE 実装を別セッションから再開するための durable handoff owner です。

新しいセッションでは、ローカル scratch や過去会話を正本にせず、最初に次を行ってください。

1. `mashos-api` Draft PR #3 とこの文書を GitHub から fresh fetch する。
2. PR head、base、changed paths、Draft/open/unmerged を確認する。
3. 同じ PR・同じ branch 上で、§6 の `R1_ROUTE_B_DENOMINATOR_AND_LIMITED_UNKNOWN_CLOSURE` から再開する。
4. PRをready/mergeせず、`automatic_progression=false`を維持する。

新しいPR、別branch、P0/metadata/executor検討から再開してはいけません。

## 1. GitHub anchors

- implementation repository: `MassyuRed/mashos-api`
- implementation PR: <https://github.com/MassyuRed/mashos-api/pull/3>
- implementation branch: `agent/cmee-v1a-i1sx-source-explicit-20260815`
- handoff parent head: `d2b2ea5f74478396a3bf27895b0ecc8d0f805dc5`
- handoff parent tree: `d1ac43f1643d18a7c8f2a29f797afa14e13df234`
- main at handoff: `a8ca4ddf7b7ae76bf7b3d73e74e3a5808d623428`
- resume head: PR #3 の、この文書を含む current remote head
- expected PR state after this handoff: Draft / open / unmerged、ahead 2 / behind 0、changed paths exact9
- design reference: `MassyuRed/Cocolon` Draft PR #30, head `cb63098d4dde1c5f7235e55f4af4b8e02f3be7fa`
- Route B policy identity: `cocolon.cmee.v1a.acceptance.route_b.v1`

`Cocolon` PR #30 の architecture/meaning-sovereignty contract は設計参照です。ただし同PR内の `implementation_state=NOT_STARTED` と実装未承認の記録は、その後のMashによるCMEE構築指示と `mashos-api` PR #3 より前の lifecycle snapshot です。以後の disabled WIP 実装の現在地は PR #3 とこの文書が所有します。これは PR #30 の設計を上書きせず、P0、L3-I、production、Product Read、Cycle001 の承認も作りません。

再開時にmainまたはPR headが上記anchorから進んでいた場合は、current remote headをfresh fetchし、このhandoff commitが履歴に残ることとdiffを確認してから続行します。history rewrite、force update、古いheadへの巻き戻しは禁止です。

## 2. 現在地

PR #3 は、docs/schemaだけではなく、次の callable vertical を実コードとして持っています。

`admitted Emlis source → grounded meaning graph → ExperiencePlan → bounded Observation + bound Reception → positive realization trace → EngineOutcome`

現在の正確な状態は次の通りです。

- implementation state: `DRAFT_WIP_DISABLED`
- callable mode: `EMLIS_AI / OBSERVE_AND_CLARIFY / OFFLINE_CANDIDATE`
- supported bounded smoke input: `LIMITED` へ到達
- terminal: `CMEE_V1A_I1SX_TEXT_GROUNDED_VERTICAL_WIP_DISABLED`
- Route B contract complete: false
- candidate ready: false
- Product Read eligible/evaluated: false / false
- exact8 acceptance complete: false
- production/API/DB/RN/Cycle001 effect: 0
- dependency/network/provider adoption: 0
- automatic progression: false

これは「最初のdisabled実装土台」です。Route B完了、full I1、Product品質、production readinessのcreditは0です。

## 3. 実装済み exact8

| path | current responsibility |
|---|---|
| `ai/services/ai_inference/cocolon_meaning_experience_engine/__init__.py` | public CMEE callable/types のexport |
| `ai/services/ai_inference/cocolon_meaning_experience_engine/contracts.py` | immutable private contracts、body-free outcome、graph/plan/trace types |
| `ai/services/ai_inference/cocolon_meaning_experience_engine/source_kernel.py` | current input admission、raw source freeze、evidence binding |
| `ai/services/ai_inference/cocolon_meaning_experience_engine/emlis_v1a.py` | Emlis graph/plan/projection、bounded realization、reception/trace validation |
| `ai/services/ai_inference/cocolon_meaning_experience_engine/engine.py` | exact-one orchestration、status分類、fail-closed outcome |
| `ai/tests/test_cmee_v1a_i1sx_contracts.py` | privacy/admission/enums/locator contract tests |
| `ai/tests/test_cmee_v1a_i1sx_vertical.py` | graph→plan→artifact→trace、tamper/safety/reception/relation tests |
| `ai/tools/cmee_v1a_i1sx_candidate_run.py` | original exact8 body-free candidate runner |

このhandoff documentが9番目のPR pathです。PR #2のCycle WIP module、legacy production ingress、API ownerはimport・変更していません。

## 4. 再現可能な現在の事実

### 4.1 Bounded implementation proof

unit testのsynthetic smoke sourceは次です。

```json
{
  "id": "cmee-vertical-1",
  "memo": "仕事が続いて疲れていて、朝から何も手につかない。",
  "memo_action": "",
  "category": ["仕事"],
  "emotion_details": [{"type": "不安", "strength": "medium"}],
  "emotions": ["不安"],
  "is_secret": false
}
```

このbounded sourceは `LIMITED`、Observation exact1+、Reception exact1、positive traceを生成します。ただし現在は未解決ownerをvisible unknownとして出していないため、Route B完了証拠として扱ってはいけません。

### 4.2 Verification snapshot

- CMEE unit tests: 15/15 PASS
- existing three-core text-generation boundary checks: 5/5 PASS
- compileall: PASS
- original exact8: artifacts 0/8、structurally valid traces 0/8
- exact8 state: `EXACT8_GENERATION_INCOMPLETE_DISABLED`
- exact8 runner exit: 1（既知の正しい失敗）
- Product Read: not performed / not eligible

exact8 failure split:

- 6 × `plan_bound_observation_realizer_unavailable`
- 1 × `bound_human_reception_positive_burden_promotion`
- 1 × `relation_endpoint_binding_not_supported`

original exact8の入力はrunner内が正本です。成功率を上げるためにfixtureを置換・単純化・family化してはいけません。

## 5. 未完了blocker

### B1. Route B denominator/disposition authority

- owner universe `U` が source adapter/core obligation でprovider/legacy planより前に固定されていません。
- 現在の `OwnerDisposition` row は、設計が要求する `owner_class`、`provider_resolution`、`attachment_admission`、`visible_authority`、`visible_claim_refs`、`target_unknown_ref`、`reason_codes` を持っていません。
- `set(D)=U`、source/obligation version、owner universe digestを独立再検証できる形へ閉じる必要があります。

### B2. LIMITEDに残るunknownのvisible preservation

- representative artifactは未解決ownerをtrace constraintに残しますが、visible unknown unitを持ちません。
- source-explicitだが非可視のownerを `UNKNOWN_PRESERVED_LIMITED` と誤分類している箇所があります。
- 未解決required ownerが残る `LIMITED` は、evidence-bound unknown duty/unit/traceを明示するか、`UNAVAILABLE`へfail closedする必要があります。

### B3. Original source locator completeness

- `EvidenceRef`にUTF-8 byte rangeはありますがscalar rangeがありません。
- repeated textの一部は扱えますが、double-space、tab、U+3000など全admitted whitespaceについてraw↔normalized scalar mappingが閉じていません。
- scalar rangeとUTF-8 rangeが同じraw substringを指すことを検証する必要があります。

### B4. Common-guard proof sealing

- 現在はcommon-coreのpassed flagとguard nameを確認しますが、exact5各guard resultのpass、`step15_common_core_stabilization.passed`、`common_shapes_ready`、empty issue codesをartifact/traceへsealして独立再検証していません。
- failed/tampered guard rowを拒否するmutation testが必要です。

### B5. exact8 generationとProduct Read

- relation endpoint/direction binding、reception semantic compatibility、plan-bound realizer coverageが未完了です。
- exact8 structural generationが揃う前にhuman Product Readを始めてはいけません。
- structural 8/8の後にだけ、private/body-full blind Product Readを別gateとして行います。

## 6. 次の実装packet exact1

次に着手するのは、`R1_ROUTE_B_DENOMINATOR_AND_LIMITED_UNKNOWN_CLOSURE` だけです。P0、metadata、executor、surface tuningへ移動しません。

R1の変更対象は原則としてproduction exact3 + tests exact2 = paths exact5です。

1. `contracts.py`
2. `source_kernel.py`
3. `emlis_v1a.py`
4. `test_cmee_v1a_i1sx_contracts.py` の必要最小修正
5. `test_cmee_v1a_i1sx_vertical.py` の必要最小修正

R1 acceptance:

1. source adapter/core obligationが、legacy grounded plan/providerより前に `U = required_owner_refs ∪ active_optional_owner_refs` を固定する。
2. required/active owner全件にexact1の完全なRoute B disposition rowがあり、omit・duplicate・denominator shrinkが0。
3. graph/plan/traceが同じsource version、obligation version、owner universe digestにbindされる。
4. unresolved required ownerを持つ `LIMITED` は、evidence-bound visible unknown duty/unit/traceをexact1+持つ。安全に出せなければartifactなしの`UNAVAILABLE`。
5. `SOURCE_EXPLICIT_VISIBLE`以外のownerをpositive observation/reception claimへ使わない。
6. owner omission、disposition field tamper、universe digest swap、hidden unknown、cross-source refをmutation testでrejectする。
7. body-free privacy、no fallback、production effect0、automatic progression=falseを維持する。
8. original exact8は変更せず、runnerの結果をそのまま報告する。R1だけで8/8を要求せず、fixture tuningをしない。

R1がgreenになった後の順番は `R2_RAW_SCALAR_UTF8_LOCATOR` → `R3_EXACT5_GUARD_PROOF_SEALING` → `R4_PLAN_BOUND_REALIZER_EXACT8` です。各packetで新helper/control familyを増殖させず、同じDraft PR内を前進させます。

## 7. Fresh checkoutでの検証

repository rootから実行します。

```bash
cd ai
PYTHONPATH=services/ai_inference python -m unittest -v \
  tests/test_cmee_v1a_i1sx_contracts.py \
  tests/test_cmee_v1a_i1sx_vertical.py

python -m compileall -q \
  services/ai_inference/cocolon_meaning_experience_engine \
  tests/test_cmee_v1a_i1sx_contracts.py \
  tests/test_cmee_v1a_i1sx_vertical.py \
  tools/cmee_v1a_i1sx_candidate_run.py

PYTHONPATH=services/ai_inference python - <<'PY'
from pathlib import Path
import runpy
ns = runpy.run_path(str(Path("tests/test_cocolon_text_generation_core_boundary.py")))
tests = sorted((name, fn) for name, fn in ns.items() if name.startswith("test_") and callable(fn))
assert len(tests) == 5, len(tests)
for _, fn in tests:
    fn()
print("5/5 PASS")
PY

set +e
PYTHONPATH=services/ai_inference python tools/cmee_v1a_i1sx_candidate_run.py
runner_rc=$?
set -e
test "$runner_rc" -eq 1
```

現時点では最後のrunnerがexit 1かつ0/8であることがexpectedです。R1の成功をrunner exit 0へ読み替えてはいけません。body-full outputは明示指定時だけprivate temp pathへ出し、GitHubへcommitしません。

## 8. 維持する境界

- same Draft PR / same implementation branch
- new dependency / requirements / lock: 0
- network / external provider / parser proposal promotion: 0
- API / DB / RN / production ingress: 0
- Piece / Analysis implementation: 0
- P0 / L3-I / full I1 / Product Read / Cycle001 credit: 0
- fallback / mirror / retry / raw replay: 0
- actual user/private raw input、actual generated private text、digest、locatorのpublic反映: 0
- workflow / Actions / ready / merge: 0
- automatic progression: false

ローカルQA用copy、stub、`pytest.py`、`__pycache__`、private Product Read packetをcommitしてはいけません。

## 9. 次セッション用の再開文

次の1文で再開できます。

> @GitHub `MassyuRed/mashos-api` Draft PR #3 と `ai/docs/CMEE_V1A_I1SX_CurrentStateAndNextWorkHandoff_20260816.md` を正本として、`R1_ROUTE_B_DENOMINATOR_AND_LIMITED_UNKNOWN_CLOSURE` から同じbranch上で実装を再開して。original exact8・privacy・disabled境界を維持し、Draftのまま検証結果まで反映して。
