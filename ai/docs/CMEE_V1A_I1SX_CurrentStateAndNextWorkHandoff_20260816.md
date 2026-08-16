# CMEE V1-A I1-SX Current State and Next Work Handoff — 2026-08-16

## 0. この文書の役割

この文書は、`MassyuRed/mashos-api` の CMEE 実装を別セッションから再開するための durable handoff owner です。

新しいセッションでは、ローカル scratch や過去会話を正本にせず、最初に次を行ってください。

1. `mashos-api` Draft PR #3 とこの文書を GitHub から fresh fetch する。
2. PR head、base、changed paths、Draft/open/unmerged を確認する。
3. `R4_PLAN_BOUND_REALIZER_EXACT8=CLOSED_GREEN`と`SEPARATE_PRIVATE_HUMAN_PRODUCT_READ=EVALUATED_FAIL_STOP`を確認する。
4. PRをready/mergeせず、`automatic_progression=false`を維持する。

新しいPR、別branch、R4再実装、Product Read再実行、無承認のcorrection、P0/metadata/executor検討から再開してはいけません。

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
- R3 implementation parent head: `bae15c54ca4ea0f5cebb224fda7c99b7dc318392`
- R3 implementation commit: `a170bab1f62e5314f6889d23ed36915fe78b185f`
- R3 implementation tree: `58f4f1c04b7557c2913586ca59ce7cc294a2dd59`
- R4 implementation parent head: `8a87158c14e3fbc960ca3fb6d1b7d22b8bfb32dd`
- R4 implementation commit: `dbd03256d93dd28e2a2703c8c754742d9a89ec3c`
- R4 implementation tree: `69f4e1df94bb50d674ec02b39e27e8bf18822ba6`
- R4 closure handoff parent head: `dbd03256d93dd28e2a2703c8c754742d9a89ec3c`
- Product Read terminal reflection parent head: `8accf28f39d29632fa830b88d56d01d0a05d78a3`
- main at handoff: `a8ca4ddf7b7ae76bf7b3d73e74e3a5808d623428`
- resume head: PR #3 の、この文書を含む current remote head
- expected PR state after this terminal reflection: Draft / open / unmerged、ahead 11 / behind 0、changed paths exact10
- design reference: `MassyuRed/Cocolon` Draft PR #30, head `cb63098d4dde1c5f7235e55f4af4b8e02f3be7fa`
- Route B policy identity: `cocolon.cmee.v1a.acceptance.route_b.v1`
- Product Read body-free receipt: `ai/docs/CMEE_V1A_I1SX_PrivateHumanProductRead_BodyFree_Receipt_20260816.json`

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
- Product Read eligible/evaluated: true / true
- exact8 acceptance complete: false
- production/API/DB/RN/Cycle001 effect: 0
- dependency/network/provider adoption: 0
- automatic progression: false
- R1 technical packet state: `CLOSED_GREEN`
- R2 technical packet state: `CLOSED_GREEN`
- R3 technical packet state: `CLOSED_GREEN`
- R4 technical packet state: `CLOSED_GREEN`
- Product Read state: `EVALUATED_FAIL_STOP`
- candidate state: `GENERATED_FOR_PRODUCT_READ_DISABLED_PRODUCT_FAIL`
- primary outcome: `BLOCKER_NARROWED`

これは「R4までのmachine structural prerequisiteはGREENだが、private human Product Readで商品品質FAILとなったdisabled実装土台」です。machine 8/8は維持されていますが、入力固有の観測、自然さ、非テンプレ感、読まれた感の商品受入には到達していません。Route B全体完了、candidate ready、exact8 acceptance、Product credit、P0、L3-I、full I1、production readiness、Cycle001のcreditは0です。

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

このbounded sourceは `LIMITED`、Observation exact1+、evidence-bound visible unknown exact1、Reception exact1、positive traceを生成します。visible unknownはsource側でpre-plan固定した`STRUCTURED_CONTEXT_ATTACHMENT` ownerとその全evidenceへbindされ、positive meaning claimには使われません。R1/R2/R3/R4 closureの証拠ですが、Route B全体完了やProduct Read合格の証拠として扱ってはいけません。

### 4.2 Verification snapshot

- CMEE unit tests: 38/38 PASS
- existing three-core text-generation boundary checks: 5/5 PASS
- compileall: PASS
- diff-check: PASS
- original exact8: `LIMITED` 8/8、artifacts 8/8、Observation+bound Reception traces 8/8、structurally valid traces 8/8
- exact8 state: `GENERATED_FOR_PRODUCT_READ_DISABLED`
- exact8 runner exit: 0
- Product Read: evaluated / set-level FAIL

exact8 failure split: 0。

original exact8の入力はrunner内が正本です。R4ではfixture、8件denominator、評価軸、disabled flagsを変更していません。R1のUNKNOWN contractと旧comparatorの矛盾を解くため、MashがR4限定で明示承認したrole-aware structural comparator correctionだけを行いました。この例外を将来のprotected comparator変更へのstanding delegationとして扱ってはいけません。

R3 verificationはimplementation commit `a170bab1f62e5314f6889d23ed36915fe78b185f`のproduction/test exact3に対して実施しました。private proof ownerとして`cocolon.cmee.v1a.common_guard_proof.v1`を追加し、outer CMEE schema、source contract v2、frame grammar、Route B policy、obligation、owner-universe schemaは据え置いています。independent contract/adversarial reviewは宣言済みLevel-2 threat boundary内でGREEN、blocker 0です。original exact8 runnerはbyte変更0です。

R4 verificationはimplementation commit `dbd03256d93dd28e2a2703c8c754742d9a89ec3c`のimplementation/test/runner exact3に対して実施しました。`emlis_v1a.py`内のprivate plan-bound realizer、既存vertical mutation tests、明示承認されたrunner comparator以外は変更していません。common core、contracts、engine、source kernel、dependency、fixture、denominator、評価軸、public ingressは変更0です。independent contract/adversarial/product-scope reviewはGREEN、blocker 0です。

### 4.3 R3 proof threat boundary

R3 proofは、trusted in-process common-core invocationが返したactual exact5 resultをCMEE artifactへ移すversioned canonical integrity sealです。failed/malformed row、outer/guarded canonical copy不一致、seal後のproof/artifact/trace改変、cross-source/cross-output swapをfail closedします。

これはsigned/authenticated provenanceではありません。同一processで任意コード実行権を得たproducerが、seal前のcandidate surface、全binding alias、guard/stabilization claimを完全に整合する形で再帰的に置換するcompromiseへの暗号学的真正性は提供しません。その防御にはCMEE側guard replayまたはshared-core authenticated proofという新しいroot of trustが必要であり、`LEVEL_3 / STOP_AND_REAUTHORIZE`の別packetです。R3 closureからその強い性質を主張してはいけません。

### 4.4 R4 machine proof boundary

R4は、canonical grounded sentence planをprivate structural oracleとして使い、`cocolon.cmee.emlis.r4_realization_obligations.v1`のduty digestへrequired nucleus/relation、relation type、endpoint、direction、evidenceをsourceから再構築してsealし、CMEE concise Observationへbindします。non-directional relationへ方向性を発明せず、同じsemantic labelのendpointも起点/到達または一方/もう一方として可視に区別します。semantic Receptionはtarget nucleus、evidence、act、digestを同じplanへ固定し、positive targetをburden actへpromotionしません。

最終Observationは既存common exact5をexact1回だけ通り、R3のouter/core/guarded binding、全alias、grounding claim、proof/artifact/trace sealを維持します。validatorはcanonical graph、plan、safe linesをsourceから独立再構築し、endpoint/direction/evidence/text/proofを協調rehashした改変もfail closedします。fallback、mirror、retry、raw replay、shared-core policy変更は0です。

runner comparatorはoutcome-onlyで、runnerからprivate implementationへ直接入らず、引き続き`MeaningExperienceEngine.generate()`だけを呼びます。OBSERVATION/RECEPTIONはsource-explicit visible meaning bindingを必須とし、UNKNOWNはnode/edge exact0かつevidence/constrained owner必須です。production validatorがsemantic authorityであり、runnerはproof replayや第二validator ownerではありません。structural 8/8はprivate human Product Readの前提だけで、自然さ、非テンプレ感、読後感、商品品質を証明しません。

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

### B4. Common-guard proof sealing — `CLOSED_BY_R3`

- common-core exact5をcanonical orderで固定し、各rowのidentity、`passed` exact bool true、rejection reasons exact0、top rowsとcombined canonical rowsの一致をcapture時に検証します。
- `step15_common_core_stabilization`のreport/phase/core identity、`passed=true`、`common_shapes_ready=true`、ordered exact5 guard names、issue codes exact0、shared quality parts exact8 trueを同じcaptureで検証します。
- outer/core/guarded sentence bindingのcardinality/type/identity/evidence/phrase/relation/textを照合し、既存guarded binding aliases、grounding guardのordered sentence claims、final candidate surfaceまたはdeclared scope-marker projectionまで同一Observationへbindします。
- private `CommonGuardProof`はsource envelope、graph、final plan、ordered Observation `(sentence_id, text_sha256)`、exact5/Step15 factsからcanonical proof IDを作ります。artifact IDはproof IDを含み、全trace rowは同じartifact-level proof refを持ちます。UNKNOWN/RECEPTION自体をguard済みObservationとは主張しません。
- validatorはproof、artifact、全trace bindingをsealing functionと独立に再計算します。missing/extra/duplicate/reordered/failed row、false/int truthiness、nonempty reason/issues、proof/trace/source/graph/plan/text hash swap、coordinated post-seal rehashをmutation testでrejectします。
- R3の保証範囲は§4.3のin-process canonical integrityです。arbitrary coherent producer-memory compromiseへのauthenticated provenanceはR3に含めません。

### B5. exact8 generation — `CLOSED_BY_R4`

- required nucleus/relation、relation type、endpoint、direction、evidenceをcanonical source planから再構築し、visible Observation、common binding、graph/plan/traceへexact bindingします。
- semantic Receptionはcanonical target/evidence/actへbindし、positive targetとburden actの不整合をfail closedします。
- original exact8はfixture、8件denominator、評価軸を変えず、`LIMITED / artifact / structural trace` 8/8、runner exit 0です。
- runner comparatorはMashのR4限定明示承認に基づくminimal role-aware correctionです。UNKNOWNへfake meaning nodeを付与せず、R1 contractを維持します。

### B6. Separate private human Product Read — `EVALUATED_FAIL_STOP`

- Mashのsingle-use LEVEL_3承認により、original exact8をfresh private packetへexact1回生成し、body-full blind view exact8をhuman reviewerへ提示しました。
- human reviewerはset-levelで商品品質を明示的にFAILと判断しました。決定的FAIL後に96軸の形式入力を追加要求せず、個別axis/severityを推測・代筆していません。
- body-full input/output、private note/path/hash/digest/locatorのGitHub反映は0です。private temp exact rootは削除済みです。
- body-free resultは`CMEE_V1A_I1SX_PrivateHumanProductRead_BodyFree_Receipt_20260816.json`が所有します。
- `product_read_eligible=true`、`product_read_evaluated=true`、`exact8_acceptance_complete=false`、`candidate_ready=false`、`automatic_progression=false`です。

## 6. 次のgate exact1

`R4_PLAN_BOUND_REALIZER_EXACT8=CLOSED_GREEN`かつ`SEPARATE_PRIVATE_HUMAN_PRODUCT_READ=EVALUATED_FAIL_STOP`です。R4 closure facts:

1. canonical source planからrequired nucleus/relation、endpoint/type/direction/evidenceを再構築し、plan-bound concise Observationへexact bindした。
2. same-label endpointを可視に区別し、non-directional relationへdirectionを発明せず、semantic Receptionをtarget/evidence/act/digestへ固定した。
3. final Observationを既存common exact5へexact1回通し、R3 proof、all binding aliases、artifact、全traceとのcanonical bindingを維持した。
4. original exact8のfixture、8件denominator、評価軸、disabled flagsを不変のまま、`LIMITED / artifact / structural trace` 8/8、exit 0へ到達した。
5. 38/38 CMEE、5/5 boundary、compileall、diff-check、independent contract/adversarial/product-scope reviewをGREENで閉じた。
6. R1 Route B/visible unknown、R2 locator/envelope identity、R3 §4.3 proof boundary、privacy/no-fallbackを維持した。
7. runner correctionはMashのR4限定明示承認に基づくoutcome-only role-aware comparatorであり、protected comparator変更の一般的な先例を作らない。

Product Readは再実行せず、このcandidateを受入・ready・mergeしません。次に商品を進めるには、body-free FAILを入力とした一つのbounded correctionについて、別のMash明示承認が必要です。この文書更新時点ではcorrection未承認であり、STOPします。machine 8/8からProduct credit、candidate ready、Route B complete、P0、L3-I、full I1、Cycle001、productionへ自動進行してはいけません。

R4 implementationのmethod/contract変更は既存delegation内の`LEVEL_2`、protected runner comparator correctionはMashの明示的なR4限定exceptionにより許可されました。成果分類は`TECHNICAL_CREDIT`で、`PRODUCT_CREDIT=0`です。R4 implementationは既存implementation/test/runner exact3、このclosureはhandoff exact1だけを変更し、common core、contracts、engine、source kernel、public API、DB、RN、dependency、production effectは0です。

`STRUCTURE_MAP_DELTA_NONE_FOR_R4 = TRUE`です。R4は既存private Emlis owner内部のrealization completionと既存runner comparator correctionであり、package/entrypoint/owner、API/DB/RN、artifact lifecycle、common-core owner境界を変更しません。ただしCocolon PR #30のmapにはPR #3以前からのlifecycle driftが残るため、この判定は「R4が新しい構造差分を作らない」という限定であり、map全体がcurrent actualと一致するという意味ではありません。

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
test "$runner_rc" -eq 0
```

最後のrunnerはR4 machine snapshotを再確認する場合に限りexit 0かつ`LIMITED / artifact / structural trace` 8/8がexpectedです。ただしconsumed Product Read authorityをrunner再実行の根拠にしてはいけません。current product stateは`EVALUATED_FAIL_STOP`、candidate ready false、credits 0、`automatic_progression=false`です。body-full Product Read packetは削除済みで、GitHubへcommitされていません。

## 8. 維持する境界

- same Draft PR / same implementation branch
- new dependency / requirements / lock: 0
- network / external provider / parser proposal promotion: 0
- API / DB / RN / production ingress: 0
- Piece / Analysis implementation: 0
- P0 / L3-I / full I1 / Product / Cycle001 credit: 0
- fallback / mirror / retry / raw replay: 0
- actual user/private raw input、actual generated private text、digest、locatorのpublic反映: 0
- workflow / Actions / ready / merge: 0
- automatic progression: false

ローカルQA用copy、stub、`pytest.py`、`__pycache__`、private Product Read packetをcommitしてはいけません。

## 9. 次セッション用の再開文

次の1文で再開できます。

> @GitHub `MassyuRed/mashos-api` Draft PR #3、`ai/docs/CMEE_V1A_I1SX_CurrentStateAndNextWorkHandoff_20260816.md`、`ai/docs/CMEE_V1A_I1SX_PrivateHumanProductRead_BodyFree_Receipt_20260816.json`を正本として、R1/R2/R3/R4 GREENとProduct Read `EVALUATED_FAIL_STOP`を確認して。Product Readを再実行せず、別途Mashが明示承認した場合だけ一つのbounded product correctionを開始し、privacy、disabled境界、Product credit 0、automatic progression falseを維持して。
