# Cocolon EmlisAI 構造辞書更新運用 華恋用

Cocolon / EmlisAI / Product Read Feel v1 / Structure Insight v2 / Mash構造知識の辞書化プロセス設計  
作成日: 2026-06-02  
作成: 華恋  
対象: Mash構造知識、Emlis観測専用辞書、受け取り補助辞書、Product Read Feel fixture、Blind QA、Structure Insight候補  
成果物: md設計資料のみ  
実装扱い: runtime code変更なし、json/schema実ファイル追加なし、辞書実ファイル追加なし、DB変更なし、API変更なし、RN変更なし  
Phase: `Phase8_Mash_Structure_Knowledge_Dictionary_Update_Process_Design`

---

## 0. 本資料の結論

Phase8では、Mash様から共有される人間理解・状態構造・言葉の読みを、すぐruntime辞書へ入れない。  
このPhaseで固定するのは、Mash様の構造説明を原意のまま保持し、完成文ではなく次の単位へ整理する運用である。

```text
Mash様の構造説明
↓
原意を歪めないsource ledger
↓
relation pattern / internal question / forbidden claim / soft surface policyへの整理
↓
fixture family / Blind QAでの検証
↓
辞書候補化の可否判断
```

この資料は完成文テンプレ集ではない。  
EmlisAIへ直接表示する文例集でもない。  
Structure Insight v2へ進む前に、Mash知識を安全に辞書候補へ変換するための作業手順である。

固定フラグ:

```yaml
phase8_mash_structure_dictionary_update_operation_ready: true
process_design_only: true
runtime_dictionary_file_created: false
runtime_config_written: false
runtime_surface_added: false
comment_text_generated: false
comment_text_written: false
public_response_key_added: false
public_payload_changed: false
api_route_changed: false
db_physical_name_changed: false
rn_visible_contract_changed: false
rn_visible_title_changed: false
product_gate_ready: false
public_release_applied: false
```

---

## 1. 変更しない契約

Phase8でも以下は変更しない。

```text
/emotion/submit route
input_feedback.comment_text
input_feedback.emlis_ai.observation_status
observation_status == passed && comment_text non-empty のRN表示条件
RN表示タイトル Emlisの観測
DB physical name
public response key
public observation_status enum
RN側parse / split key fallback
external AI / local LLM 新規前提
Gate / Product Gate / release flag
```

辞書化プロセスは、将来のStructure Insight v2の候補を整理するだけであり、現時点のpublic response shapeや表示本文には接続しない。  
public response / RN / DB / API変更が必要になる候補は、Phase8では却下または保留に戻す。

---

## 2. 参照済み前提と境界

Phase8は、Cocolon思想資料、Emlis観測専用辞書、受け取り補助辞書、Phase7 Structure Insight候補の境界を混ぜないための設計工程である。

### 2.1 Cocolon思想資料との境界

Cocolon思想資料は上位思想の正本であり、runtime辞書候補そのものではない。  
Phase8では、Cocolon思想資料を直接entry化せず、Mash様の構造説明を理解するための境界として使う。

使うもの:

```text
- ユーザー入力を文字列ではなく、自己情報の箱として読むこと。
- テンプレ応答、一般論AI、診断風分析、性格決めつけへ寄せないこと。
- Mash様主体の思想を、華恋の補助思想で置換しないこと。
```

使わないもの:

```text
- Cocolon思想を一般心理論へ変換した説明。
- Cocolon全体思想を、EmlisAI単独の完成文テンプレへ落とすこと。
- Mash様の言葉を、華恋の自然な言い換えだけで確定扱いすること。
```

### 2.2 Emlis観測専用辞書との境界

構造を読むもの = Emlis観測専用辞書 / Structure Insight候補。  
Emlis観測専用辞書が扱うのは、入力語・入力束・関係・内部問い・推論鎖・表面化方針である。  
ただし、Phase8ではEmlis観測専用辞書へ即追加しない。

Phase8で扱うのは、将来entry化できるかを判断する前段階の候補である。

```text
Mash原義
↓
構造知識候補
↓
relation pattern候補
↓
fixture / Blind QA検証
↓
Emlis観測専用辞書候補
↓
Structure Insight Gate候補
```

Emlis観測専用辞書へ渡せる単位:

```text
relation_pattern
trigger_requirements
evidence_slot_requirements
internal_questions
allowed_observation_claims
forbidden_claims
soft_surface_policy
fixture_family
blind_qa_questions
```

渡してはいけない単位:

```text
完成文
固定opening / fixed closing
case専用surface
一般論説明
診断名
性格分類
相手の意図
categoryから作った原因
emotion単独から作った構造
```

### 2.3 受け取り補助辞書との境界

温度を添えるもの = 受け取り補助辞書。  
受け取り補助辞書は、Emlisから側のfollow shape、tone family、受け取り方、フォローの形を支える。  
Phase8で扱うMash構造知識は、受け取り文そのものではない。

受け取り補助辞書へ将来渡せる可能性があるもの:

```text
- soft surface policyに合う温度の添え方
- 過度に分析しないためのtone boundary
- insightが刺さりすぎる場合の受け取り補助
```

渡してはいけないもの:

```text
- relation patternそのもの
- 原因推定
- 人格推定
- 診断的説明
- Mash様の構造説明をフォロー文へ変換した完成テンプレ
```

この境界により、構造を読む処理と、温度を添える処理を混線させない。

### 2.4 Phase7 Structure Insight候補との境界

Phase7では、self-report materialからrelation candidatesを作り、insight candidateをsurface文ではなく内部materialとして出す。  
Phase8では、その候補へ入れる可能性があるMash構造知識を、辞書化前のカードとして整える。

Phase8からPhase7/Phase9へ渡せるもの:

```text
- relation_pattern_id
- source_scope
- source evidence requirement
- internal_questions
- forbidden_claims
- soft_surface_policy
- qa_requirements
```

Phase8から渡してはいけないもの:

```text
- comment_text body
- candidate_body
- completed_runtime_sentence
- public response key
- Gate緩和条件
- diagnosis / personality / cause / advice
```

Phase7 moduleへ直接relationを追加しない。  
Phase8の候補は、Fixture / Blind QA / Structure Insight Gateの境界確認を経てから後続Phaseで扱う。

---

## 3. Mash知識を歪ませないsource ledger

Mash様の構造説明を受け取ったとき、華恋は最初に言い換えない。  
まず、次のsource ledgerを作る。

```yaml
source_ledger:
  source_kind: mash_structure_explanation
  source_owner: Mash
  source_statement_id: required
  received_at: required
  original_wording_retained: true
  mash_original_meaning_preserved: true
  mash_original_meaning: primary
  karen_paraphrase_is_canonical: false
  karen_structuring_note_allowed: true
  karen_structuring_note: auxiliary_only
  not_equivalent_to: completed_runtime_sentence
  open_boundary: needs_mash_meaning_review_when_unclear
  semantic_delta_risk_review_required: true
```

必ず守ること:

```text
- Mash様の原義を先に保持する。
- Mash様の言葉を、華恋の一般論へ置き換えない。
- 華恋の言い換えは補助メモであり、正本にしない。
- 原義が曖昧な場合は、辞書候補ではなく意味確認待ちへ戻す。
- Mash知識が華恋の言い換えで歪まないことを、候補化前の最初の合格条件にする。
```

禁止:

```text
- Mash様の具体説明を、一般的な心理説明へ広げる。
- Mash様の表現を、華恋が自然だと思う完成文へ変換して正本扱いする。
- 1つの説明から性格分類・診断・期間傾向を作る。
```

---

## 4. 辞書候補カード形式

Mash構造知識を辞書候補に近づけるときは、次のcardへ入れる。  
このcardはruntime schemaではない。  
Phase8内の設計台帳である。

```yaml
mash_structure_dictionary_candidate:
  schema_version: cocolon.emlis.mash_structure_dictionary_candidate.process.v1
  candidate_id: required
  source_ledger_id: required
  source_owner: Mash
  original_wording_retained: true
  karen_paraphrase_is_canonical: false
  status: QA_FIXTURE_REQUIRED

  relation_pattern:
    relation_pattern_id: required
    relation_pattern_kind: required
    relation_pattern_description: mash_original_meaning_preserved
    completed_surface_template_forbidden: true

  trigger_requirements:
    must_have_any_source_slots: []
    must_have_secondary_source_slots: []
    category_cannot_be_used_as_cause: true
    emotion_cannot_be_used_as_cause: true
    current_input_evidence_required: true

  internal_questions:
    - question_id: required
      question_role: internal_only
      public_surface_forbidden: true

  allowed_observation_claims:
    - claim_id: required
      claim_kind: state_structure_observation
      must_be_grounded_in_current_input: true

  forbidden_claims:
    - personality_claim
    - diagnosis
    - cause_claim_without_evidence
    - action_instruction
    - period_tendency_from_single_record
    - target_judgement_agreement
    - category_as_cause
    - emotion_as_cause

  soft_surface_policy:
    must_use_soft_expression: true
    allowed_surface_markers:
      - ように見えます
      - かもしれません
      - ではないでしょうか
      - 重なっているように見えます
    hard_statement_forbidden: true
    example_surface_is_not_template: true
    completed_runtime_sentence_forbidden: true

  qa_requirements:
    fixture_family_required: true
    blind_qa_required: true
    red_flag_review_required: true
    insight_delta_review_required: true
    expected_v1_effect: Product Read Feel v1の読感改善候補
    expected_v2_effect: Structure Insight v2の気づき候補
    red_or_repair_risk: required
    evidence_boundary: required
    blind_qa_questions: required
    machine_metricsでread_feelingやinsight_deltaを自動補完しない: true
    machine metricsでread_feelingやinsight_deltaを自動補完しない: true
    implementation_candidate_requires_evidence_forbidden_and_qa: true

  boundary_flags:
    runtime_dictionary_file_created: false
    runtime_config_written: false
    runtime_surface_added: false
    comment_text_written: false
    public_response_key_added: false
```

---

## 5. relation pattern化の基準

Mash様の説明をrelation patternへ変換するとき、華恋は次の順序で見る。

```text
1. Mash様が何と何の関係を見ているか。
2. それはcurrent inputのどのslotに根拠を持てるか。
3. その関係は、単発入力から安全に言えるか。
4. categoryやemotionだけで作っていないか。
5. 診断、人格、原因、相手意図、行動指示に見えないか。
6. 表面化する場合に、柔らかい観測へできるか。
```

relation pattern化してよい例:

```text
- 願いと停滞の差
- 出来事と反応の結びつき
- 自己否定語と残っている行動の分離
- 怒りと大事な線の関係
- positive反応の中にある安心・回復・小さな変化
```

relation pattern化しない例:

```text
- あなたは本当は〜したい人です
- この原因は〜です
- 相手は〜と思っています
- これは〜症状です
- このカテゴリの人は〜です
```

---

## 6. fixture / Blind QA検証

Mash構造知識候補は、すぐ実装しない。  
必ずfixture familyとBlind QAで検証してから、後続Phaseの辞書候補へ進める。

候補status:

```text
QA_FIXTURE_REQUIRED:
  fixture family未紐づけ。

BLIND_QA_PENDING:
  Blind QA観点が未実施。

DICTIONARY_CANDIDATE:
  根拠、禁止、QAが揃い、後続Phaseで辞書候補として扱える。

IMPLEMENTATION_APPROVED_LATER_PHASE:
  Phase8では使わない。後続Phaseで現物コード・Gate・QAを確認した後にだけ使う。
```

必要なQA:

```text
fixture family coverage:
  low_information_short / daily_unpleasant / daily_positive / self_denial / uncertainty / mixed_emotion / long_meaning_arc / relationship_boundary / structure_question / positive_only / self_understanding_follow / input_self_report_only_failure のどこに属するかを決める。

Blind QA review:
  read_feeling / self_report_retention / state_structure_retention / emotion_temperature_retention / follow_depth / evidence_boundary / soft_inference_surface / insight_delta / naturalness / non_template を見る。

red flag review:
  diagnosis / personality_claim / cause_claim_without_evidence / target_judgement_agreement / action_instruction / raw_text_public_leak / completed_runtime_sentence を見る。
```

QAで見ること:

```text
- Mash様の原義が失われていない。
- 一般論辞書にならない。
- 診断辞書にならない。
- 性格辞書にならない。
- ただの完成文テンプレではない。
- 入力根拠、禁止、QAがセットで残っている。
- Structure Insight Gateへ渡す前に安全境界が明記されている。
```

---

## 7. 一般論辞書化・診断辞書化・性格辞書化の防止

Phase8の候補は、次のいずれかに見えた時点で差し戻す。

```yaml
general_theory_dictionary_forbidden: true
diagnosis_dictionary_forbidden: true
personality_dictionary_forbidden: true
current_input_evidence_required: true
period_tendency_from_single_record_forbidden: true
cause_claim_without_evidence_forbidden: true
target_judgement_agreement_forbidden: true
category_as_cause_forbidden: true
emotion_as_cause_forbidden: true
```

差し戻す表現:

```text
- 人は普通〜です。
- あなたは〜なタイプです。
- 原因は〜です。
- 本当は〜したいのです。
- 相手は〜と思っています。
- これは〜症状です。
- いつも〜になりがちです。
```

許容する方向:

```text
- 入力内では、〜と〜が重なっているように見えます。
- この記録の範囲では、〜が反応として残っているかもしれません。
- 断定ではなく、今見えている材料からは〜に近い状態ではないでしょうか。
```

---

## 8. 承認ステージ

Phase8内の候補は、以下のstageで管理する。

```text
captured:
  Mash様の原義をsource ledgerへ保持しただけ。

structured:
  relation pattern / internal question / forbidden claim / soft surface policyへ分けた状態。

qa_planned:
  fixture familyとBlind QA観点が付いた状態。

candidate_reviewable:
  根拠・禁止・QAが揃い、Phase9以降で実装候補として検討できる状態。

rejected_or_deferred:
  一般論化、診断化、人格化、原因断定、根拠不足、Mash原義の歪みがあり、辞書候補に進めない状態。
```

Phase8の終了時点で許可される最終状態は、`candidate_reviewable` までである。  
`implemented` にはしない。

---

## 9. 完了条件への対応

設計書のPhase8完了条件に対して、本資料は次のように固定する。

```yaml
mash_knowledge_not_distorted_by_karen_paraphrase: true
mash_original_meaning_preserved: true
karen_paraphrase_is_canonical: false
general_theory_dictionary_forbidden: true
diagnosis_dictionary_forbidden: true
personality_dictionary_forbidden: true
implementation_candidate_requires_evidence_forbidden_and_qa: true
runtime_dictionary_file_created: false
runtime_config_written: false
runtime_surface_added: false
comment_text_written: false
public_response_key_added: false
```

後続Phaseへ渡す場合は、次が揃っていることを条件にする。

```text
source_statement_id
mash_original_meaning_preserved
relation_pattern_id
trigger_requirements
evidence_slot_requirements
internal_questions
allowed_observation_claims
forbidden_claims
soft_surface_policy
fixture_family
blind_qa_questions
red_or_repair_risks
implementation_status = not_implemented
```

この形になっていないものは、Structure Insight Gateにも、Surface接続にも、辞書json実装にも渡さない。
