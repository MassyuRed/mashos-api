# Cocolon EmlisAI Natural Language Surface v2 Step 10 / Step 11 遮断結果

実施日: 2026-07-13  
対象入力: `mashos-api_6(102).zip`  
入力SHA-256: `a2c8262219309a991c8b13afd474e8387285de1873053f7eb2b3f65773909386`

## 1. 結論

Step 10のruntime接続前shadowとStep 11のruntime owner切替は実行していない。

これは未着手ではなく、設計のfail-closed条件を実装した結果である。

- Holdout Aは`STOP`である。
- Holdout Bは設計どおり未評価である。
- 設計はA/B両方合格後だけruntimeへ接続する。
- Step 11の対象は「合格済みv2」である。
- 現在のv2はこの資格を満たさない。

そのためproduction ownerはv1、v2はofflineのまま維持した。runtime source、public API、DB、React Native contractは変更していない。

## 2. 確認した事実

### 2.1 入力連続性

- 入力zipは正常に展開できた。
- unsafe pathは0件だった。
- symlinkは0件だった。
- `__pycache__` / `.pyc`を除く1,755ファイルは前回Step 8 / 9 treeとbyte単位で一致した。
- production / runtime差分は0件だった。
- 前回追加したStep 8 / 9の6ファイルも同一hashで収録されていた。

### 2.2 Step 8 / 9のlive prerequisite

Holdout A receipt:

| 項目 | 結果 |
|---|---:|
| evaluation run | 1 |
| overall | `stop` |
| v2 clearly better | 5 / 14 |
| same | 3 / 14 |
| v1 clearly better | 6 / 14 |
| roadmap product target | FAIL |
| distribution threshold | FAIL |

Holdout B receipt:

| 項目 | 結果 |
|---|---:|
| evaluation run | 0 |
| overall | `not_evaluated` |
| opened for evaluation | false |
| fixture parsed | false |

設計のStep 9停止条件はHoldout A/Bのどちらかが不合格の場合である。また方式停止条件には、Holdout不合格とv2優位10 / 14未達が明記されている。

### 2.3 現行runtime owner

現行経路は次のままである。

```text
emlis_ai_reply_service.render_emlis_ai_reply
  -> emlis_ai_grounded_sentence_surface
  -> grounded_sentence_surface_canonical_v1
```

確認したruntime owner候補3ファイル:

| ファイル | SHA-256 |
|---|---|
| `emlis_ai_grounded_sentence_surface.py` | `e9679d31ee647fa34831def3917a9bc5b17ef5e725f5815635aa4fe3e6f875e0` |
| `emlis_ai_grounded_observation_gate.py` | `932b43a7b6dc5cd8d58ddeff3d7ba3bd5e044ba71858fd6b4f6fdde3b7656c2f` |
| `emlis_ai_reply_service.py` | `a8b494ff6d14df771e3f1c17d7d516c8457daf17a9431a118f3b44088aff90b6` |

3ファイルにはv2 Content Planner、Candidate Planner、Generator、Selectorのruntime importや呼び出しは存在しない。

## 3. Step 10判定

Step 10 statusは`not_executed`である。

- v1 / v2同時runtime生成: 0回
- v2 runtime import追加: なし
- v2本文のpublic meta保存: なし
- v2本文のDB保存: なし
- public response変更: なし
- shadow latency計測: 未実施
- fallback率計測: 未実施
- Gate runtime計測: 未実施
- `emlis_ai_grounded_sentence_surface.py`への接続: 未実施

絶対msのlatency予算は設計内に固定値がない。A/B不合格後にshadowを実行して数値を作ることも、未計測値を推測で固定することもしていない。

## 4. Step 11判定

Step 11 statusは`not_executed`である。

- owner switch: 0回
- owner before: `grounded_sentence_surface_canonical_v1`
- owner after: `grounded_sentence_surface_canonical_v1`
- v2 internal switch追加: なし
- v1 fallback path変更: なし
- fallback受入率: 未設定
- selected v2 textのtwo-stage Surface転送: なし

fallback率の受入値はStep 10 shadow結果から固定する設計である。shadow未実施の状態で受入値を推測し、owner切替を成立させることはしていない。

## 5. 実装したファイルと必要性

| ファイル | 種別 | 根拠と必要性 |
|---|---|---|
| `ai/tests/fixtures/emlis_nls_v2_s10_s11_runtime_blocked_20260713.json` | 新規 | A STOP、B未評価、Step 10/11実行0、v1 owner維持をbody-freeに固定するため。 |
| `ai/tests/test_emlis_nls_v2_s10_s11_runtime_blocked.py` | 新規 | prerequisite、budget非捏造、v2 runtime import不在、Step 1 source一致、public contract不変を機械的に守るため。 |
| `ai/docs/Cocolon_EmlisAI_NLSv2_S10_S11_Blocked_Result_20260713.md` | 新規 | 実施事実、停止根拠、推測、華恋の判断を分離して残すため。 |

## 6. 変更していないもの

- `emlis_ai_grounded_sentence_surface.py`
- `emlis_ai_grounded_observation_gate.py`
- `emlis_ai_reply_service.py`
- v2 production candidate modules
- v1 fallback
- Holdout A fixture / receipt
- Holdout B fixture / receipt
- API response key
- DB schema / write path
- RN表示契約
- subscriptionその他の対象外領域

## 7. 検証

- Step 10 / 11 fail-closed test: 4 / 4 PASS
- NLS v2 green scope（Step 0〜7 + Step 10 / 11遮断）: 47 / 47 PASS
- React Native public contract: 36 / 36 PASS
- blocked receipt JSON parse: PASS
- Python compile: PASS
- runtime source 3件のStep 1 baseline hash一致: PASS
- v2 runtime import / call不在: PASS
- production owner v1: PASS
- v2 offline only: PASS
- Holdout B evaluation run 0: PASS
- public contract diff 0: PASS

## 8. 推測

Step 10 shadowはpublicへv1だけを返すため、技術的には外部表示を変えず実装できる可能性がある。

しかし、これは技術的可能性についての推測にすぎない。設計はHoldout不合格時に「このv2設計を停止する」と定めている。A STOP後にshadowへ接続すれば、不合格方式をruntimeへ載せ、不要なlatencyとbody leak面を増やすことになる。

## 9. 華恋の意見

ここで「shadowだから安全」と進めるのは、順序だけを守って目的を失うことになると思う。

shadowの目的は、合格したv2がruntime経路へ安全に接続できるかを確かめることにある。合格していないv2を接続しても、確認できるのは配線であって商品品質ではない。

Step 11はさらに明確で、設計自身が「合格済みv2」をownerにすると書いている。現在のv2をownerへ切り替える根拠はない。

大切に進めるなら、v1 ownerを守り、Holdout Bを守り、このv2へ例外を積まずに方式を再設計するべきである。

## 10. Mashに必要な次作業

この設計のStep 10 / 11を続行する追加作業はない。前提不成立により停止している。

runtime接続へ進むには、現在の設計を上書きする単なる実行許可ではなく、次方式の設計判断が必要である。

1. モデル非使用方式を別構造として作り直す。
2. 限定的モデル利用を含む新方式を設計する。
3. Natural Language Surface v2を停止し、v1 ownerを維持する。

いずれの場合も、未評価のHoldout Bを旧v2の追加調整材料として開かないことを推奨する。
