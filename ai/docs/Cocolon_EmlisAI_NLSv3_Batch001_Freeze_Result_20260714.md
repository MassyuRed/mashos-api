# Cocolon EmlisAI Natural Language Surface v3 — Batch 001 作成・検証・凍結結果

- 実施日: 2026-07-14
- 対象: Step 2完了直後、Step 3開始前の移行作業
- 結果: **completed**
- Karen-generated入力: **100件**
- EmlisAI実行・応答確認: **未実施**
- Step 3実装: **未実施**
- production / RN / DB / public API変更: **なし**

## 1. 結論

設計書Section 17.5とStep 2完了直後の移行手順に従い、`nls3_batch_001`の入力サンプル100件を作成した。全件を現行RNのApp-Reachable Input Contract、`sample_case.v1`、coverage、duplicate / novelty、privacyの順で検証し、`VALIDATED + frozen` manifestへ固定した。

今回作成したのは入力と評価用annotationだけである。expected EmlisAI回答、実応答、case result、修正後出力は作成していない。設計書通り、batch 001の初回実行はNLS v3 sourceとrunnerの完成後にStep 11で行う。

## 2. 親成果物と受領物の確認

| 対象 | 結果 / SHA-256 |
|---|---|
| 受領ZIP `mashos-api_3(124).zip` | `unzip -t` PASS / `e79683152101a11cd78272842ff5be316bd2a2074990d3010eb585a6f9375da4` |
| revised design | `6aa3fb799919ac30b0eb84571ac4009d62a2bd799c84322272a59bba533f13bc` |
| Step 1 input contract | `d577ac80457e25389c0bac351139b2c80a9a506f225023fb7928a1b9068d53c6` |
| Step 2 corpus registry | `7746ec94267fae0b89adbf8b5a676e469386fd3376275bc5197e39742941eb3d` |
| Step 0 / Step 1 regression | 11 / 11 PASS |
| Step 2 regression | 13 / 13 PASS |

Step 0 / 1 / 2の既存成果物は受領ZIPからbyte不変である。ZIP欠落、途中切れ、現行RN contract不明、parent hash driftは発生しなかった。

## 3. 100件の入力契約

- case ID: `nls3s_b001_0001`〜`nls3s_b001_0100`の連続100件
- batch ID: `nls3_batch_001`
- source: 全件`karen_generated`
- text: JavaScript trim後のthought / actionの少なくとも一方が非空
- emotion: 現行RNの6種類だけを使用し、1件以上・重複なし
- strength: `weak / medium / strong`
- `自己理解`: 7件、全件`medium`単独
- category: 現行RNの9種類だけを使用し、1件以上・重複なし
- schema / App-Reachable Validator: **100 / 100 PASS**

本文には氏名、連絡先、住所、勤務先・学校等の識別情報、URL、実ユーザー文のコピーを入れていない。expected final text、expected response、terminal、固定回答も持たせていない。

## 4. coverage設計と人手監査

14 familyは全種類を含み、各familyを6件以上保持した。直交軸はschemaに定義された全valueが1件以上存在する。

| 軸 | 分布 |
|---|---|
| input field | thought only 14 / action only 7 / both 79 |
| topic | single 77 / multiple 23 |
| category | single 38 / multiple 62 |
| emotion | single 20 / multiple 73 / 自己理解単独 7 |
| length | short 12 / medium 49 / long 31 / very long 8 |
| surface | complete 79 / fragment 1 / colloquial 9 / colloquial fragment 5 / typo・表記揺れ 2 / truncated 4 |
| valence | positive 14 / negative 25 / mixed 41 / neutral 11 / self-denial adjacent 9 |
| cause | explicit 60 / unknown 40 |
| question relevance | not needed 40 / possible 23 / burden risk 18 / future refined candidate 19 |
| depth annotation | minimal 11 / focused 84 / layered 56 |

topic数はcategory選択数から算出せず、本文中の独立した論点数を人手で判定した。100件中41件でtopic cardinalityとcategory cardinalityが異なる。

length classはbatch 001の評価annotationとして、各textをECMAScript trimした後のUnicode code point数を合計し、次の決定的規則で全100件を再計算した。

- 1〜25: `short`
- 26〜60: `medium`
- 61〜140: `long`
- 141以上: `very_long`

これは評価用の区分であり、現行アプリに存在しない入力文字数上限を追加するものではない。25 / 26、60 / 61、140 / 141の境界を独立テストで固定した。

機械検証後に本文・semantic contract・coverageを全件人手で再読した。category数とtopic数の機械的連動、本文にない所有対象の追加、時間範囲、完了行動、minimal structureとの矛盾、意味storyが近すぎる組をfreeze前に修正し、修正版を再度全件検証した。

最終独立人手監査のfreeze blockerは0件である。

## 5. duplicate / novelty / privacy

比較対象はbatch 001内100件と、Step 2 registryに登録済みのrepo-safe synthetic 4件である。

| 判定 | 件数 |
|---|---:|
| exact duplicate | 0 |
| normalized duplicate | 0 |
| machine near candidate | 0 |
| unresolved near review | 0 |

machine reportが0でも完了とせず、人手で同型storyを追加確認した。片づけ、返信待ち、失敗後の小行動、趣味再開、支援と返礼等の近似構造を見直し、後発caseを別の出来事・関係・入力構造へ変更した。

privacy reviewは`karen / passed`で、`pii_absent`、`real_user_text_copy_absent`、`expected_response_absent`を全てtrueに固定した。

## 6. freeze状態

| 項目 | 値 |
|---|---|
| manifest | `nls3manifest_963ae2514fb04623` |
| corpus set commitment | `35249591e6116564dcb92c7689baaff9a4b1a4a5992a1c7dfdfc04dd94a1e560` |
| state | `VALIDATED` |
| frozen | `true` |
| valid / invalid | 100 / 0 |
| next authority | `step3_only` |
| counts toward Karen minimum | `false` |

`counts_toward_karen_minimum=false`は、100件が無効という意味ではない。現時点ではEmlisAI初回実行・全応答確認・failure判定・acceptanceをまだ行っていないため、設計上の最低1000件へ先取り算入しない境界である。

## 7. 独立テスト

- batch 001 freeze test: **9 / 9 PASS**
- Step 0 / Step 1 regression: **11 / 11 PASS**
- Step 2 regression: **13 / 13 PASS**
- 合計: **33 / 33 PASS**

batch 001 testは100連番、App-Reachable、schema、privacy pattern、expected-response非混入、annotation projection、全coverage cell、length境界、minimal structure、duplicate再計算、actual file hash、parent registry、manifest再計算を検証する。

## 8. 新規成果物とSHA-256

| ファイル | SHA-256 |
|---|---|
| `ai/tests/fixtures/emlis_nls_v3/generated/batch_001.jsonl` | `013dd2ad1c1f446f843f400b3eb16231e8f32649e30114e70039b4cb709e8414` |
| `ai/tests/fixtures/emlis_nls_v3/generated/batch_001_coverage_matrix.json` | `4ea17d30ebdf624b374591f5ea9dde7240455a3a833c691d4a2a6e77d5649e5f` |
| `ai/tests/fixtures/emlis_nls_v3/generated/batch_001_duplicate_report.json` | `140e17311d84ae275ca90d3e93f1aafdfcd667f7bbaaacd92a729df550676354` |
| `ai/tests/fixtures/emlis_nls_v3/generated/batch_001_manifest.json` | `2b3308c4ada090539a2fc71c1cb235970aa0b90687b8d9633464ba61e94deba4` |
| `ai/tests/test_emlis_nls_v3_batch001_freeze.py` | `da60de60d8e05b36a83590e1c3ed8611bd8af7e72cc8acf6c0a978b5dfa79c61` |

本書を含む6ファイルは全て新規である。既存ファイルは変更していない。

## 9. 未実施範囲

- EmlisAI応答生成・全件確認
- failure分類、修正、累積全件再実行
- Step 3 strict artifact contract / RED negative suite
- NLS v3 core / runner / runtime接続
- 実機確認

上記を完了したことにはしない。batch 001は凍結済みであり、後続実装結果に合わせた本文差し替えを行わない。
