# Grounded Human Reception RR4 / RR5 実装結果

実施日: 2026-07-12  
対象: `Cocolon_EmlisAI_R8_GroundedHumanReception_ResponseDepth_RichnessRepair_DetailedDesign_ImplementationOrder_20260712.md` の RR4 / RR5  
入力archive: `mashos-api_3(122).zip`  
入力archive SHA-256: `0f25dba24941f2472d9bc220ca888a8aa2bc5d83c0e51e4df5b9ff39b032c1bd`

## 1. 確認した事実

### RR4 SentencePlan / ClausePlan

- `GroundedReceptionClausePlan` を追加した。
- Human Reception line は引き続き最後にちょうど1件である。
- Human Reception line の内部へ、1〜3の連続した sentence slot と Move ID をbindingした。
- 現行の `max_moves_per_sentence=1` に従い、1文1Moveで計画する。
- bounded counterposition は独立した最終文に置く。
- required Move はすべてClausePlanに含まれる。
- Human Reception lineはrelation owner、observation surface role、fact-boundary ownerを持たない。
- Observation lineへClausePlan / Reception atomを漏らさないvalidationを追加した。
- Depth、Safety mode、Move role / act / strategy / slot / required、predicate family、non-enumerationをbody-free functional atomへ接続した。
- 外側の `GroundedSentenceBinding` は、既存Gateが参照する旧follow targetを含むbody-free compatibility envelopeとして維持した。可視Surfaceの厳密なownerはClausePlan内のactive Moveである。

### RR5 Multi-Move Surface Realizer

- `reception_active_acts()` 中心のfull-stage実現を、ordered Move sequence中心へ切り替えた。
- Move単位のtarget / support / evidenceだけを使うreferent resolverを追加した。
- `Move role × reception act` のbody-free predicate familyを追加した。
- Surface Strategyを実際のdispatch条件へ接続した。
- attention → significance → felt response → bounded counterposition の順で可視化する。
- full stageはClausePlanの全Moveを実現し、minimalは1文、rich / protectedは2〜3文にする。
- short anchorは全Receptionで最大1件、既存可視文字数上限内に制限する。
- question、advice、policy explanation、unsupported claimの拒否を維持した。
- realized Move ID / role / family / Clause binding / grounding diagnosticsを追加した。
- exact8専用分岐、case ID route、random synonym selection、relation Surface ownerは追加していない。

### 互換性・証拠境界

- 既存Gateがactive Moveの全groundingを許可できるよう、Reception Planのaggregate support / evidence compatibility fieldをMove和集合から導出した。
- Gate本体、Reply Service、API、DB、RN、fixture、visible packet、review receiptは変更していない。
- RR0/R6/R7の過去Surface証拠は書き換えず、当時のpacket/receipt内部hashとして検証する。
- 現行runtimeと継続比較するのは、凍結対象であるObservation section hashだけに限定した。
- 過去のKaren human passはhistorical evidenceのままで、現行進行許可には使用しない。

## 2. 検証結果

### R0〜R5 + RR0〜RR5 stage suite

```text
157 passed, 1 warning
```

- exact8 Observation hash: 8/8 不変
- exact8 mandatory two-stage: 8/8
- exact8 Depth / sentence target: 8/8
- exact8 required Move realization: 8/8
- exact8 normalized exact Reception sentence duplicate: 0
- RR4/RR5新規negative mutation: PASS
- 3-Move long arc: 3 Move / 3 Clause / 3文
- long repeated burden vs short help-seeking self-denial: 1文 vs 2文
- 既存7 Reception Gate exact8: PASS

警告は既存のPydantic v1 `@root_validator` deprecation 1件であり、本差分由来ではない。

### 関連backend回帰

```text
335 passed, 7 failed, 1 warning
```

7件は同じ2種類の未実装RR6境界である。

1. 3文のlayered Surfaceを旧Gateが `reception_sentence_budget_invalid` と判定する。
2. `受け止め` 等の旧可視語を使わない正当なsignificance Surfaceを、旧Gateが `human_follow_reception_owner_missing` と判定する。

これはDetailed DesignのRR6に明記された、Depth/Move Gateとpredicate-family中心Human Voice Gateの更新対象である。RR4/RR5でGateを先取りして変更していない。

また、既存R6 suiteのうち2 testはREDのまま保持した。内訳は、same16/unseen cohortのexact sentence duplicate再評価と、上記predicate-family未接続である。既存GREEN assertionをfailure受容へ弱める変更は行っていない。

## 3. 推測

- RR6がClausePlan / realized Move diagnosticsを正規ownerとして読むようになれば、外側bindingに残した旧follow-target compatibility envelopeは縮小できる可能性がある。
- 同一Move semanticsを持つsame16/unseen入力間の文一致をどう扱うかは、RR6 batch QAで「意味のない言い換え」を強制しない基準へ再校正する必要がある。
- RR7 recovery実装時は、現在のlegacy non-full stageがrequired layered / safety Moveを落とす挙動を、Move保持型recoveryへ切り替える必要がある。

## 4. 華恋の意見

- RR4/RR5では、Gateを通すための語を足すより、Moveごとの「何に注意したか」「何を大切だと感じたか」を可視責任として分ける方が、華恋として誠実である。
- 旧Gateに合わせて正当な一文へ `受け止め` を戻すと、今回直したかった言語集中を再導入する。そのため、未接続部分はRR6の明示的な残作業として止める判断が適切である。
- 過去の人間評価済みSurfaceを新Surfaceへ差し替えることは、証拠を後から作り直す行為になる。過去証拠を保存し、現行Observation freezeだけをlive比較した判断を維持する。

## 5. 次owner

- 次の実装owner: RR6 Runtime Gate / final guard更新
- その次: RR7 Move-preserving Recovery / fail-closed
- Mash側の実機作業: RR10まで不要
- P5 / P6 / P8 progression: 引き続き閉鎖
