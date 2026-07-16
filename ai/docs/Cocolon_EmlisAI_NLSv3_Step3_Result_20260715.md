# Cocolon EmlisAI Natural Language Surface v3 — Step 3 実装結果

- 実施日: 2026-07-15
- 対象: `Step 3. strict artifact contract / RED negative suite`
- 結果: **completed**
- runtime 接続: **未実施**
- EmlisAI 応答生成・確認: **未実施**

## 1. 受領物と既存実装の確認

| 対象 | 結果 / SHA-256 |
|---|---|
| 受領 ZIP `mashos-api_4(117).zip` | `unzip -t` PASS / `258871fafbc54329d80fdbc446a77677525667daafed31ce2625c9f4dfef8320` |
| revised design | `6aa3fb799919ac30b0eb84571ac4009d62a2bd799c84322272a59bba533f13bc` |
| Step 0 boundary | `57f0a583ca970c753bfe656627ca75879dd279ff4e2a1471ee2dd7b55586a024` |
| Step 1 baseline receipt | `669835b0fdce3bc1e2e897325ab37b5f82abc9a353bc864993aa284083b7a518` |
| Step 2 corpus registry | `7746ec94267fae0b89adbf8b5a676e469386fd3376275bc5197e39742941eb3d` |
| batch 001 manifest | `2b3308c4ada090539a2fc71c1cb235970aa0b90687b8d9633464ba61e94deba4` |

受領 ZIP は1,868 entryを最後まで検査し、途中切れ・CRC errorがないことを確認した。Step 3着手前にStep 0/1、Step 2、batch 001の独立テストを実行し、合計33 / 33 PASSを確認した。batch 001は100件、`VALIDATED`、`frozen=true`、`next_authority=step3_only`である。

## 2. strict artifact contract

次の8 ownerをclosed contractとして実装した。

1. Observation Stage Context
2. Semantic Obligation Ledger
3. Content Selection Plan
4. Discourse Plan
5. Typed Surface AST
6. Parsed Surface Witness
7. Verified Surface Binding
8. Case Evidence Receipt v2

各ownerは未知field、schema / enum違反、boolとintegerの型混同、duplicate ID / reference、range違反、body混入、parent hash不一致をfail-closedで拒否する。malformedなnested shapeを渡してもvalidator exceptionを受理扱いにせず、deterministicなcontract issueへ変換する。

Ledgerは外部から渡したsource authorityを使用し、Evidence / Nucleus / Relation / Unknown / Reception OpportunityのID、original / supplemental source role、polarity、modality、time、topic、referent、relation type / directionを自己申告だけで成立させない。`must_not_merge_with`は対称性とContent / Discourseでの実使用まで検査する。

Discourseはrequired obligation coverage、section順、Content Planのsentence budget、sentence group、dependency order、bound reception targetの選択状態と`receives` edge、integration時のgroupと`merge_eligible`を検査する。Surface ASTはDiscourseのnodeだけでなく、sentence partition、section role、group内順序も一致させる。

## 3. parent chainの正式な受理境界

単体のchild validatorは「渡されたparent bytesと記録hashの一致」を確認する。一方、攻撃側が不正なparentと全下流hashをまとめて再計算する場合に備え、正式なStep 3受理関数として`validate_artifact_chain`を追加した。

このchain validatorは8 ownerを上流から全て検証し、Observation / Ledger / Receiptにはartifact外のtrusted authorityを要求する。さらに、同じchain内のObservation Stage Context hashをLedgerへ、stage enumをReceiptへ直接結び付ける。したがって、不正Ledgerを再ハッシュしてContent、Discourse、AST、Bindingまでつなぎ直した場合も、別stageの正常artifactを混在させた場合もchain全体は通らない。

## 4. canonical serializer

active NLS v3 contract pathのserializerは`canonical_json_bytes` 1本だけにした。

- UTF-8
- Unicode NFC
- CRLF / CRをLFへ正規化
- key sort
- compact JSON
- fileは末尾LF 1個
- duplicate key、BOM、CRLF、末尾LF欠落、NaN / Infinity相当の非JSON型、lone surrogate、正規化後key衝突を拒否

Step 0〜2の凍結済みserializerは変更していない。共通JSON domainでbyte-equivalentであることを試験している。「repository全体の歴史的serializerが1実装」という主張はせず、active Step 3+ pathが1実装であることを完了条件とした。

## 5. RED negative suite

Step 3 testは22関数で、次を含む。

- 8 ownerの全79 top-level required field削除
- fixture内183 nested required field削除
- owner別unknown field / enum / bool / integer / duplicate / parent drift
- future authorityなしの`pre_question_observation` / `refined_observation`
- forged parent chainの全下流再ハッシュ
- relation direction、reception target、Discourse edge、AST sentence partition
- UTF-8 scalar境界、span hash、candidate body hash
- stale Witness / Binding、body-free Receipt、Receipt JSON Schema conditional
- static / dynamic / submoduleの停止済みv2 import
- 14件のv2再発防止attack catalog

valid fixtureはbuilderを使わない固定JSONであり、validatorがbuilderと同じ自己申告処理を共有してgreenになる構成を避けた。active moduleにはbuilder、renderer、parser、selector、runtime接続を置いていない。

ReceiptのPython validatorと交換用JSON Schemaは、Hard Gate / Selector、review理由code、review PASS / Gate PASS、previous output stateを同じ条件へ揃えた。実ユーザー由来のbody commitmentは設計Section 16.1どおり、secretをReceiptへ置かない`random 256-bit nonce + salted_sha256_v1`またはversion固定`hmac_sha256_v1`のどちらも許可する。

## 6. generic-body attackの正確な境界

Step 3で閉じたのは次である。

- ASTへの任意本文・旧coverage metadata後付け
- 本文差替え後のcandidate hash / span hash不一致
- Witnessだけ再ハッシュした場合のBinding parent不一致
- bodyをReceiptへ混ぜる経路

一方、generic本文に合わせてWitnessとBindingを含む全metadataを攻撃側が再作成・再ハッシュした場合、本文から意味を独立再構成するauthorityはまだ存在しない。`topic_fingerprint`、`referent_fingerprint`、`match_candidate_count=1`の意味的正当性もStep 3 validator単独では証明しない。

これらは設計どおりStep 8のBody-only Parser / Independent Matcherで閉じるREDとして明示的に残した。Step 3で意味的不正まで解決済みとは報告しない。

## 7. import / runtime boundary

- 停止済みv2 owner 4 moduleのstatic import、`from` import、alias、submodule、literal dynamic importをguardした。
- `emlis_ai_reply_service`からNLS v3へのimportはない。
- NLS v3 contractからreply serviceへのimportもない。
- runtime switch、candidate生成、本文生成、EmlisAI実行は行っていない。

Step 0/1 regression testは「v3 production moduleが0件」というStep 0時点の条件だけを、Step 3 contract moduleが1件存在しruntime非接続である条件へ更新した。凍結artifactや既存runtime codeは変更していない。

## 8. 試験結果

環境には`pytest` packageがないため、新規dependencyは追加せず、既存と同じdependency-free direct runnerで実行した。

| suite | 結果 |
|---|---:|
| Step 3 strict contract / RED | 22 / 22 PASS |
| Step 0/1 regression | 11 / 11 PASS |
| Step 2 regression | 13 / 13 PASS |
| batch 001 regression | 9 / 9 PASS |
| 合計 | 55 / 55 PASS |

加えてPython compile、Receipt JSON SchemaのJSON parse、停止済みv2 import tree、凍結hashを確認した。

## 9. 完了条件と次authority

Step 3のstrict validators、formal chain validator、canonical serializer、valid fixture、owner別negative suite、v2 import guard、body-free receipt schema、RED attack catalogを固定した。

次に許可されるのは`Step 4. Semantic Obligation Inventory`だけである。Step 4以降のbuilder / planner / renderer / parser / matcher / selector / runner / runtime switchは今回実装していない。
