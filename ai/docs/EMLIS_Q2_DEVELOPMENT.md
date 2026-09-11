# Emlis Q2 — 保存を伴う一往復の開発実装

2026-09-11。MashのQuestion System Technical Design v1.1と「Q1を確認してQ2へ」の指示を使用。Q1の53件を再確認して実装した。Q2のsource・SQL・API・RN実装は既存Draft PR3/30で管理する。Q2のコード実装は完了。2026-09-11修正版v1.2に従いQ3へ進行し、Q3も実装済み。以下はQ2保存profileの記録であり、新規開発入口はQ3 profileを選ぶ。稼働DB適用、端末上の開発アプリ確認、商品合格、本番切替は別作業として未実施。

## 商品と国家システムの境界

保存済みの感情入力に対して、Emlisが観測と必要な一問を返し、本人の回答でその観測を更新する。回答は新しい感情入力ではなく、元の入力に所属する補足source。`emotions`、国家の入力件数、通知、Astor queue、Piece、TodayQuestion、Analysis materialを回答から書き換えない。Q2では全tierともFree相当の現在入力＋回答、一問まで。有料履歴・後続roundはQ3。

`emotion_submit_service.persist_emotion_submission`の元保存・既存fanout後、`emlis_ai_reply_service`の明示development分岐からthreadを開始する。開発分岐は保存済みthread DTOへ一本化し、旧I5本文との二重生成をしない。flag OFFでは従来I5がowner。旧`input_feedback.comment_text`／passed gateを質問statusで拡張しない。Piece publishのmodalには回答欄を追加せず、InputScreenの通常保存とAnalysisHistoryScreenの元入力IDから専用modalを開く。

Q2当時の実行profileは外側の`DEVELOPMENT_APPLICATION` / `q2.free.one_round.v1`で、内部作者を`OFFLINE_CANDIDATE`として呼んでいた。現行Q4は保存profileを保ち、作者へ明示`EMLIS_APPLICATION`を渡す。Q1作者のmode・共有意味/本文契約・既存canonical100の資料を本番利用可能へ昇格しない。HTTP/DB/期限/認証はQ2 serviceが所有し、機械検証は商品判定を代筆しない。

## 保存・API

実DDL ownerは`supabase/migrations/20260911020509_emlis_input_threads_q2.sql`。CLIで新規migrationを作り、稼働環境をread-onlyで調べた`emotions.id/user_id/created_at`、`profiles.subscription_tier`に合わせた。

| 対象 | 責任 |
|---|---|
| `emlis_input_threads` | 元入力ごとに一意、revision、現意味と最後の観測の別参照、回答参照、発行済み数、現在attemptと期限、元source snapshot |
| `emlis_thread_events` | OBSERVATION / QUESTION / ANSWER / MEANING_UPDATE / OPERATION / TERMINALを順序付きで保持。回答raw text、question、意味、artifactはprivate payload |
| `emlis_thread_read` | ownerと元入力の閲覧期間を確認してsnapshotを返すだけ。生成・発行・意味確定なし |
| `emlis_thread_commit` | 親・plan・threadをlockし、元source、現在revision、attemptと期限を再確認。events appendとpointer更新を短い一transactionでcommit |
| `GET /emlis/threads/by-input/{emotion_id}` | 元入力と保存済みtimeline、現在本文、質問、処理状態を返す |
| `POST /emlis/threads/{thread_id}/answers` | expected_revision / idempotency_key / question_id / answer_text / optional authored_at |
| `POST /emlis/threads/{thread_id}/actions` | skip / stop / retry_response。旧Q2 profileはcontinueなし、Q3 profileは明示continueに対応 |

公開wireは`cocolon.emlis_thread.application.v1`。厳密な型とallowlistは`api_emlis_thread.ThreadResponse`。Bearerを既存verified resolverで検証し、clientのuser/plan/source refは受け付けない。200 responsesはprivate, no-store。保存済みQUESTIONだけ公開する。checkpoint、graph、raw bytes、内部source digestはDTOへ渡さない。専用RN clientはerror本文をmonitoringへ送らない。

二つのtableはRLS enabled、anon/authenticatedにtable/RPC権限なし。service_role経由でもRPCが親のownerを確認する。親入力とauth accountのFK cascadeでeventsまで削除する。Freeは既存`publish_governance`と同じ前月・当月JST、Plusは365日、Premiumは既存の無期限の元入力閲覧条件。回答時刻で元記録の保持期限を延長しない。

## 失敗・再開

ANSWER受理、意味checkpoint、本文は三つのcommit境界。回答直後は旧本文を現在から外す。意味訂正後の本文失敗では訂正pointerを保持し、旧本文は履歴としてだけ表示する。NO_MATERIAL_UPDATEは最後の保存本文をそのまま再利用し、作者を再実行しない。未解決/部分反映/変更なしを同一の成功扱いにしない。

same key＋same payloadは元attemptを返す。same key＋異なるpayload、新keyによる既回答questionへの回答は409。同時に来た同じ操作もCAS後に保存結果を照合する。一時DB停止を示す明示SQLSTATE、または確認済みworker cancellationだけ明示retryを許可する。retryは同じoperation・回答・prefix・checkpointを使い新attemptを一つ発行。質問枠を消費しない。本文保存後のACK消失はGETでその本文を返す。

HTTP timeoutや不明な5xxは`save_result_unknown`で自動retryしない。RNは先にGETで照合し、未受理の場合だけ同じpayload/keyを本人が再送できる。期限超過だけではretry可にしない。各attemptは30秒。失効したactive attemptをGET上で無期限処理中にせず、旧attemptからの遅いcommitを拒否する。元submitの既存3秒budgetは維持し、そのcancelが確認できた場合は保存済みthreadから明示retryできる。実機・ネットワーク上のlatencyは別途確認が必要。

modalの「閉じる」は書き込みなし。「今回はスキップ」だけ明示的にquestionを終了する。未回答の質問は履歴から同じquestion IDで再開する。元記録日時と回答日時を表示し、「今」と「その時」はQ1の意味bindingで分ける。下書きはReact memoryのみ。close/logout/切替/取得時の親削除・access喪失で消去し、古い通信結果で再表示しない。

## 開発環境での有効化と検証

Q4現在の設定は下記追記と[適用・運用確認](EMLIS_DEPLOYMENT_AND_OPERATION_CHECKS.md)の§6/§9を使う。Q2当時のRN定数`Q2_DEVELOPMENT_OPT_IN`は廃止済み。APIの`/app/bootstrap`が返す`emlis_threads_enabled`でdebug/release共通のreaderを選び、既定値はfalse。開発書込みには引き続き`COCOLON_ENV=development`と`COCOLON_EMLIS_THREAD_DEVELOPMENT=true`が必要。

Pythonは既存bootstrap lockのCPython3.12.13・pytest8.4.1・46依存。DB testは[公式PGlite](https://pglite.dev/docs/)0.5.8のPostgreSQL WASMに**実migrationとRPC**を適用し、`Q2_PGLITE_MODULE`をそのpackageの絶対pathに設定して実行する。

```sh
cd ai
python -m pytest -q tests/test_emlis_q2_application.py tests/test_cmee_emlis_q1_thread.py -p no:cacheprovider
```

RN検査は`tests/emlis-q2-tools/package.json`の固定test依存を用い、そのnode_modulesをNODE_PATHに指定して `node --test tests/emlis-thread.test.js tests/rn-screen-contracts.test.js`。test-only React rendererであり、native端末の視認・キーボード・復帰の証明とは区別する。PGliteのsingle connection上でCAS interleavingを検査しており、稼働Postgresの複数connection負荷検証とも区別する。

## 2026-09-11の結果と残件

専用Q2 32件、Q1 53件、RN新規9＋既存36件が成功。追加のAPI registry／publish governance／public feedback／diagnostic検査では、今回追加したroute・model・資料は整合。既存public-profile routeに関するregistry検査2件は同じ固定runtimeのQ1 headでも同じ失敗を再現。async testを最初にadapterなしで起動した5件は実行不能だったため、前回と同じstdlib asyncio adapterで実行し全成功。初回のowned failure（registry資料未更新）も修正後に成功。失敗記録を全件PASSに塗り替えない。

公開合成5組（`ai/tests/fixtures/emlis_q2_synthetic_saved_rounds_20260911.json`）の元入力・初回本文・質問・回答後の保存本文を実DB RPCから読み、意味A/Bの違い、「今」の時点表示、訂正後の本文不存在、unknownの本文不変を確認した。再掲と定型的な受け取りは残っており商品NOT_CLEAR。本文全文を読んだことを広範な自由文対応やMashの商品合格へ換算しない。

修正版v1.2によりQ2のコード実装は完了としてQ3へ進行した。現在は既存handoff末尾Q4節が実装・検証・次工程を所有する。開発DB適用、端末上の一往復・再開・復旧、実課金、商品判断と公開は[後日の適用・運用確認](EMLIS_DEPLOYMENT_AND_OPERATION_CHECKS.md)へ分離し、それらの未実施だけでQ3/Q4コード実装を止めない。稼働DBへの変更、merge、deployは行っていない。


## 2026-09-11 Q4 — アプリ統合・互換と停止復旧

現行入口は明示`EMLIS_APPLICATION`。純粋な旧`OFFLINE_CANDIDATE`呼出しは維持し、application modeはEmlis threadを持つrequestだけを受ける。serviceから認証・mode・revision・sourceを検証して同じ作者を呼び、EngineOutcomeのbody-free情報にも実modeを記録する。保存profileのQ2/Q3、元source/checkpointのidentityとwire versionは変えない。

DTOへ`can_write`を追加。read_onlyは現在本文・履歴・pending questionを返し、can_retry/can_continueもfalseにする。GETは生成しない。HTTP・service受理・意味/本文commit前で書込み条件を検証し、確認済み停止だけ既存attemptの失敗終了を許す。旧clientはactive/read_onlyでcurrent_observationを旧comment_textへ読み出し、QUESTION_PENDINGや内部graphを旧public enumへ混ぜない。

RNはbootstrapのemlis_threads_enabledでreaderを開く。最新本文を先頭、元記録と前のやり取りを展開欄に置く。未作成の場合だけ既存modal導線へ戻り、保存結果不明のGET失敗を旧本文で隠さない。409/422はGET後に新revisionで操作でき、不明ACKは元key/payloadを保つ。InputScreenは開始ownerと遅い応答を照合し、4つの入力/Piece書込みは認証取得時も同じuserを確認する。RootNavigatorはuserごとにprivate tab stateを再作成する。

適用順、独立した公開承認値、全replicaの停止、旧版を残す回復は[運用資料§9](EMLIS_DEPLOYMENT_AND_OPERATION_CHECKS.md)を参照。コードとローカル実SQL/React検証、稼働環境への適用は区別する。全検証件数・本文確認・残件は既存handoff末尾Q4節がowner。
