# CMEE V1-A I1-SX Current State and Next Work Handoff — 2026-08-16

## 0. この文書の役割

この文書は、`MassyuRed/mashos-api` の CMEE 実装を別セッションから再開するための durable handoff owner です。

新しいセッションでは、ローカル scratch や過去会話を正本にせず、最初に次を行ってください。

1. `mashos-api` Draft PR #3 とこの文書を GitHub から fresh fetch する。
2. PR head、base、changed paths、Draft/open/unmerged を確認する。
3. 同じ PR・同じ branch 上で、§6 の `R3_EXACT5_GUARD_PROOF_SEALING` から再開する。
4. PRをready/mergeせず、`automatic_progression=false`を維持する。

新しいPR、別branch、P0/metadata/executor検討から再開してはいけません。

## 1. GitHub anchors

- implementation repository: `MassyuRed/mashos-api`
- implementation PR: <https://github.com/MassyuRed/mashos-api/pull/3>
- implementation branch: `agent/cmee-v1a-i1sx-source-explicit-20260815`
- R1 implementation parent head: `461ff03dad2483fa01f30468825f683f22d7f7da`
- R1 implementation commit: `e18bf76e3dbcfe64c9b967ca26ed50ceff4b770f`
- R1 implementation tree: `e0a748fffc295b25fe0050c0f7fbb88957a18d37`
- R2 implementation parent head: `82a642ce1bb68f8b17d4b32501f9433142bb0dda`
- R2 implementation commit: `e5be02bddecb1bc931cde6ddc90bfaa3b244bf74`
- R2 implementation tree: `fc553e1183bfa14570d0523928ba73b49005ffc4`
- this handoff update parent head: `e5be02bddecb1bc931cde6ddc90bfaa3b244bf74`
- main at handoff: `a8ca4ddf7b7ae76bf7b3d73e74e3a5808d623428`
- resume head: PR #3 の、この文書を含む current remote head
- expected PR state after this handoff: Draft / open / unmerged、ahead 6 / behind 0、changed paths exact9
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
- R1 technical packet state: `CLOSED_GREEN`
- R2 technical packet state: `CLOSED_GREEN`

これは「R2まで閉じたdisabled実装土台」です。R1/R2 technical acceptanceだけがGREENであり、Route B全体完了、P0、L3-I、full I1、Product品質、production readiness、Cycle001のcreditは0です。

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

このbounded sourceは `LIMITED`、Observation exact1+、evidence-bound visible unknown exact1、Reception exact1、positive traceを生成します。visible unknownはsource側でpre-plan固定した`STRUCTURED_CONTEXT_ATTACHMENT` ownerとその全evidenceへbindされ、positive meaning claimには使われません。R1/R2 closureの証拠ですが、R3–R4が未完了のためRoute B全体完了証拠として扱ってはいけません。

### 4.2 Verification snapshot

- CMEE unit tests: 31/31 PASS
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

R2 verificationはimplementation commit `e5be02bddecb1bc931cde6ddc90bfaa3b244bf74`のproduction/test exact4に対して実施しました。source contractはbreaking locator/identity semanticsに合わせて`cocolon.cmee.emlis.current_input.text_grounded.v2`へ更新し、frame grammar、Route B policy、obligation、owner-universe schemaは据え置いています。original exact8 runnerはbyte変更0です。

## 5. 未完了blocker

### B1. Route B denominator/disposition authority — `CLOSED_BY_R1`

- source adapterがlegacy grounded plan/providerより前にsource-bound owner universe `U` を固定します。
- required/active owner全件にapproved exact fieldsのRoute B disposition rowがexact1あり、`D=U`、順序、重複0、partition、digestをsourceから再計算して検証します。
- graph、plan、全trace、visible unknown unitは同じsource envelope/version、obligation version、owner universe digestへbindされます。
- provider未実行のownerは`MISSING_OR_INVALID / UNAVAILABLE`として保持し、provider結果を捏造しません。

### B2. LIMITEDに残るunknownのvisible preservation — `CLOSED_BY_R1`

- source-explicitだが非可視な既知情報は`SOURCE_EXPLICIT`のまま`NOT_VISIBLE_UNRESOLVED`とし、unknownへ誤分類しません。
- `PRESERVE_UNKNOWN`はsynthetic meaning ownerではなくExperiencePlan dutyのままです。
- representative `LIMITED`は、actual pre-plan attachment ownerとcurrent-source evidenceへbindした非肯定的visible unknown unit/trace exact1をObservationとReceptionの間に持ちます。
- unresolved required ownerを安全に同じ形で可視化できない場合、artifactなし`UNAVAILABLE`へfail closedします。
- omit、duplicate、coordinated denominator shrink、全disposition field tamper、digest swap、hidden/causal unknown、evidence subset、cross-source refをmutation testでrejectします。

### B3. Original source locator completeness — `CLOSED_BY_R2`

- `EvidenceRef`はcanonical original field bodyに対するfield-relative `scalar_start/end`と、frameに対するabsolute `utf8_start/end`を持ちます。validatorはscalar prefixのUTF-8長からbyte rangeを再計算し、同じraw occurrence・同じraw substringへの一致を検証します。
- canonical raw JSONを再encodeし、fixed exact6 field header/order/length/bodyとtrailing bytes 0をparseします。そのraw sourceからlegacy ledgerを再構築し、`source_span_id / field_path / element_index / scalar range / UTF-8 range`をsupplied refsと順序込みexact照合します。
- repeated equal substring、double-space、tab、単一/連続U+3000、emojiを含むraw↔normalized mappingを再現し、whitespace normalizationはledger surface equivalence比較だけに限定します。raw bytes、digest、locator authorityはnormalizeしません。
- `category.0`をmemo segmentへredirectしてbounds/digests/evidence IDを全再計算するmutation、同一emotion literalのsource-span交換、別occurrenceのscalar/byte混線をrejectします。
- SourceEnvelope IDはrecord/role/schema/source-contract/encoding/label ID+digest/raw SHAのclosed canonical identityから再計算します。record/schema/label metadata swap、field-frame/raw-JSON不一致、noncanonical label、identity swapをfail closedします。
- R1のowner universe、Route B rows、visible unknown、graph/plan/trace binding、body-free privacy、no-fallback境界は維持されています。

### B4. Common-guard proof sealing

- 現在はcommon-coreのpassed flagとguard nameを確認しますが、exact5各guard resultのpass、`step15_common_core_stabilization.passed`、`common_shapes_ready`、empty issue codesをartifact/traceへsealして独立再検証していません。
- failed/tampered guard rowを拒否するmutation testが必要です。

### B5. exact8 generationとProduct Read

- relation endpoint/direction binding、reception semantic compatibility、plan-bound realizer coverageが未完了です。
- exact8 structural generationが揃う前にhuman Product Readを始めてはいけません。
- structural 8/8の後にだけ、private/body-full blind Product Readを別gateとして行います。

## 6. 次の実装packet exact1

次に着手するのは、`R3_EXACT5_GUARD_PROOF_SEALING` だけです。R1/R2を再実装せず、R4、P0、metadata/executor再検討、surface tuningへ移動しません。

R3は既存CMEE artifact/trace validation ownerと必要最小のexisting testsだけを変更候補とします。新module、new helper/control family、dependency、provider、public schema/APIが必要なら、実装前にSTOPして影響範囲を再提示します。

R3 acceptance:

1. common-core exact5各guard resultのidentityと`passed=true`をartifact/trace proofへsealする。
2. `step15_common_core_stabilization.passed=true`、`common_shapes_ready=true`、issue codes exact0を同じproofへsealする。
3. guard proofをartifact/traceへbindして独立再検証し、failedまたはtamperedなguard rowをrejectする。
4. R1のRoute B/visible unknownとR2のsource locator/envelope identity、body-free privacy、no-fallback境界を維持する。
5. original exact8 runner/fixtureは変更せず、実際の結果をそのまま報告する。R3だけで8/8を要求しない。
6. R3 greenをhandoffへ反映した時点でSTOPし、`R4_PLAN_BOUND_REALIZER_EXACT8`へ自動進行しない。

残る順番は `R3_EXACT5_GUARD_PROOF_SEALING` → `R4_PLAN_BOUND_REALIZER_EXACT8` です。各packetで同じDraft PR内を前進させ、packet間のapproval/STOP境界を維持します。

R2のauthority分類は`LEVEL_2 / JOINT_WITHIN_EXISTING_DELEGATION_SCOPE`、成果分類は`TECHNICAL_CREDIT`です。R2 implementationは既存production/test exact4だけを変更し、product credit、Product Read、P0、L3-I、full I1、Cycle001、production creditは0です。

`STRUCTURE_MAP_DELTA_NONE_FOR_R2 = TRUE`です。R2は既存private source/evidence owner内部の契約完成であり、package/entrypoint/owner、API/DB/RN、artifact lifecycle、core境界を変更しません。ただしCocolon PR #30のmapにはPR #3以前からのlifecycle driftが残るため、この判定は「R2が新しい構造差分を作らない」という限定であり、map全体がcurrent actualと一致するという意味ではありません。

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

現時点では最後のrunnerがexit 1かつ0/8であることがexpectedです。R1/R2の成功をrunner exit 0へ読み替えてはいけません。body-full outputは明示指定時だけprivate temp pathへ出し、GitHubへcommitしません。

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

> @GitHub `MassyuRed/mashos-api` Draft PR #3 と `ai/docs/CMEE_V1A_I1SX_CurrentStateAndNextWorkHandoff_20260816.md` を正本として、`R3_EXACT5_GUARD_PROOF_SEALING` から同じbranch上で実装を再開して。R1/R2 closure、original exact8、privacy、disabled境界を維持し、R3の検証結果をDraftへ反映したらR4へ進まずSTOPして。
