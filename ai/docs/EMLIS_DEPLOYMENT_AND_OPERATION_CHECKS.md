# Cocolon CMEE 問いシステム — 後日の適用・運用確認

作成日：2026-09-11 JST  
担当：Ultra華恋  
版：1.0  
対応設計：Mashの添付「問いシステム技術設計 v1.2」。実装記録は[既存handoffの末尾Q4節](CMEE_V1A_I1SX_CurrentStateAndNextWorkHandoff_20260816.md)
位置づけ：Q2〜Q4のコード実装から分けた、実際の環境への適用・確認・商品判断・公開作業の一覧。

## 1. この資料の役割

**この資料の未実施項目は、Q3・Q4のコード実装を止める条件ではありません。** 現在は華恋が実装し、利用可能な検証環境で動作と実出力を確認します。実DB、実行環境、端末、実課金連携などが利用できる段階で、本書の該当項目を実施します。

分けるのは「実際の環境で適用・確認する作業」です。認証、保存、削除、再開、プラン、API互換、失敗時の処理を後回しにする意味ではありません。それらの設計・コード・migration・画面・検証は各Qに含めます。

| 区分 | 完了の意味 | 次のコード実装との関係 |
|---|---|---|
| Q1〜Q4の実装 | 必要な処理がコードにあり、華恋が実行可能な検証と実出力を確認したこと。 | その単位の実装上の残件を解決して次へ進みます。 |
| 適用・環境確認 | 対象DB・API・アプリへ配置し、その環境で動くことを確認したこと。 | 準備できるまで別件として残します。未実施だけでQ3・Q4を止めません。 |
| 正式な商品判断 | 対象の保存済み出力・体験をMashが判断したこと。 | 華恋の本文確認や機械検証と分けます。 |
| 公開・運用開始 | 対象版を利用者へ提供する経路を有効にし、稼働を確認したこと。 | 実装完了だけで自動実行しません。 |

正式な商品判断は、必ず実機で行わなければならない作業ではありません。保存済み本文を読む判断と、端末上の体験確認は分けられます。いずれも今回のコード実装の完了判定へ混ぜません。

## 2. 作成時点の状態

| 対象 | 状態 |
|---|---|
| Q1 | 実装完了。専用53件成功を前の実装作業で確認。 |
| Q2 | 実装完了。専用32件、RN新規9件＋既存36件成功。Q3へ進行可能。 |
| Q2のDB検証 | 検証用PostgreSQL WASM（PGlite）に実migrationを適用し、実RPCを実行済み。稼働DBへは未適用。 |
| Q2の画面検証 | 実hook／componentをReact rendererで検証済み。端末の視認・キーボード・OS動作は未確認。 |
| Q3・Q4 | Q3実装済み。Q4は公開mode・単一路・停止復旧・互換・RN統合を実装検証し、本文修正も実施。品質残件は既存handoffのQ4節で管理。本書の実環境項目は未実施。 |
| 商品品質 | NOT_CLEARを継承。保存済み合成本文の再掲・定型的な受け取り等の課題を保持。 |
| 今回の作業 | Q4コード・自動検証・保存済み実本文の確認と既存PR3/30資料の更新。稼働DB適用・端末・実課金・正式商品判断・merge・deployは未実施。詳細は既存handoff末尾Q4節。 |

検証の詳細は[Q2開発資料](EMLIS_Q2_DEVELOPMENT.md)を参照します。保存済みの件数を今回の新規実行へ数えません。

## 3. Q2から分離した適用・確認

以下はいずれも作成時点で未実施です。実行対象の版と環境が整った時点で、華恋ができる操作は華恋が行います。

| 項目 | 実際の環境で行うこと | 確認する結果 |
|---|---|---|
| DBへの適用 | 対象が開発環境か本番環境かを確認し、既存schema・migration履歴と適用予定SQLを照合して適用します。 | thread／event／RPC／FK／index／RLS・grantが予定どおり存在し、既存入力と他機能のデータが保持される。 |
| 認証・接続 | 実際のアプリの本人sessionからAPIへ接続し、APIから対象DBへ到達することを確認します。未認証・別人・親入力なし・閲覧範囲外も確認します。 | 本人の保存済みthreadだけを取得・操作できる。clientのuser／plan／source申告で権限を変えられない。 |
| 入力後と履歴の導線 | 通常入力を保存し、初回本文・任意の問い・回答後本文を読みます。同じ入力を履歴から再取得します。 | 元入力は一件のまま。保存された同じthreadを読め、Piece返信・チュートリアル・既存入力体験に重複表示や終了不能がない。 |
| 通信切断・同時操作 | 回答送信中、意味確定後、本文保存後の通信切断や、複数接続からの同時操作を検証用データで確認します。親削除・権限変更と処理完了の競合も対象にします。 | 保存結果を再取得できる。同じ回答・質問枠を二重に増やさない。訂正済み意味を戻さず、古い処理が削除後や新しい試行の後に書き込まない。 |
| 中断・再開・アカウント変更 | 画面を閉じる、アプリを終了する、再起動する、ログアウト／別アカウントへ切り替える動作を確認します。 | 閉じる操作をスキップ扱いにしない。保存済みの問いと回答を復元し、未送信下書きは初期仕様どおり消去する。他人や閉じた画面へ遅い通信結果が出ない。 |
| 日付・端末表示 | 元入力日と異なる日に回答した記録、timezone境界、長い本文・回答、文字サイズ、キーボード・スクロール・操作の到達性を端末で確認します。 | 元記録日・回答日・言葉の対象時点を混ぜない。本文・質問・回答欄・終了操作が読めて使える。対応対象のiOS／Android環境で確認範囲を記録する。 |
| 処理時間 | APIの処理時間、worker中断、ネットワーク／proxyの制限を対象環境で測ります。 | 処理中のまま残り続けず、期限切れと保存結果不明を区別する。必要な場合だけ実測を根拠に既存設定・コードを調整する。 |

Q2では、本人の回答保存・意味確定・本文保存を分けています。実環境でも「回答は保存済み」「意味は更新済みだが本文は未成立」「内容変更なし」「保存結果を確認できない」が混同されないことを確認します。再試行可能な一時障害では、保存済み回答を使い、本人へ回答の再入力を求めません。

## 4. Q3から分離する実環境確認

Q3で実装する有料プラン・複数round・frameを対象にします。以下の確認を待つ間も、その処理と自動検証はQ3で実装します。

| 項目 | 後日行うこと | Q3の実装に残すもの |
|---|---|---|
| 実際の課金連携 | 採用済み課金経路の検証環境で、契約・変更・解約等がserverの現在権限へ反映されることを確認します。実際の課金発生をこの文書だけで開始しません。 | server側プラン判定、開始時と現在の枠、upgrade／downgrade時の処理。課金イベントを待たず権限変化の入力を使って検証。 |
| 有料source・frame | 実行環境の許可された検証用履歴・frameを使い、取得・訂正・撤回・削除・権限変更後の再利用を確認します。 | Freeに別入力履歴を混ぜない、PlusとPremiumの範囲分離、根拠・暫定性・修正可能性、古い本文やframeから訂正済み解釈を復活させない処理。 |
| Premiumの続行体験 | 回答後の本文を読み、本人が続行して2問目・3問目へ進み、停止・再開・通信切断・プラン変更を端末で確認します。 | 本人続行、各roundの保存と本文、同じ焦点の聞き直し防止、三問上限、四問目を出さないこと、API／RNの状態遷移。 |
| Q2データからの移行 | Q2で保存したthreadを含む対象環境へQ3用migrationを適用し、旧記録の再取得と進行状態を確認します。 | 追加migration、旧profile読取り、保存版の互換、開始時の枠を勝手に増やさない処理。検証用DBでの移行試験はQ3に含める。 |

料金・保持期間や課金方式をこの資料で新たに変更しません。実履歴の収集や個人データの持ち出しも確認のために自動追加しません。利用できる検証用データと既存の許可範囲を使います。

## 5. 旧Q4から分離した正式確認・公開作業

Q4には、現在の環境で確認できる実装統合・本文の確認と修正・互換性・公開接続のコード準備を残します。本節は、それらを実際に適用・判断・有効化する作業です。

| 項目 | 後日行うこと | 今の実装側に残す責務 |
|---|---|---|
| Mashの正式な商品判断 | 対象集合の保存済み初回本文・問い・回答・回答後本文を、同じ結果のまま提示し、実際の判断を記録します。端末上の体験確認が必要な部分は別途行います。 | 華恋による対象全件の本文読取り、明白な低品質と意味不具合の修正、集合での反復・偏り・回帰の確認。機械成功を商品PASSにしない。 |
| 配置・旧clientとの接続 | 対象APIとアプリを環境へ配置し、旧／新client・保存版・認証・設定・timeoutが組み合わさって動くことを確認します。 | response契約、公開用の実行modeと経路選択、互換処理、移行・設定手順をQ4で用意し検証する。 |
| 本番への切替 | 対象版・適用済みmigration・設定・公開判断がそろった状態で、承認された公開操作を実施します。 | 一つの生成ownerを選び、旧I5とCMEEを二重実行しない接続。原入力保存・国家dispatch・他中核との境界。 |
| 停止・復旧・稼働確認 | 問題発生時の停止・復旧手順と、切替後の保存・再取得・エラー・処理時間を実環境で確認します。 | 保存済みの回答・意味訂正・履歴を消さない停止方法、処理中threadの扱い、互換範囲を限定した戻し方。個人の本文を一般ログへ出さない。 |

旧生成経路へ戻すだけで、保存済み回答や確定した訂正が無視される場合、それを正常な復旧にしません。Q4で、処理停止・保存済み結果の閲覧・互換性を踏まえた回復方法を用意します。既存の運用手段で足りる場合は、新しい監査基盤や切替基盤を追加しません。

## 6. Q2〜Q4開発接続の具体的な手順

これは、対象となる開発環境が使える段階の手順です。現行Q4の設定とbootstrap readerを使い、Q2/Q3の保存profileを確認します。初回配置の読取確認は§9に従います。以下の設定変更・DB適用・端末操作を、この資料の更新だけで実施済みまたは公開承認済みとはしません。

1. 対象API・DB・アプリの版と接続先を確定します。開発用データで確認できる対象を選びます。
2. `supabase/migrations/20260911020509_emlis_input_threads_q2.sql`と対象のmigration履歴・親schemaを照合します。同じオブジェクトが既にある場合、再作成や削除で押し通さず差分を確認します。
3. 未適用で整合するmigrationを対象DBへ適用し、table／RPC／FK／権限を確認します。Q3の変更を含む版なら、その版の追加migrationまで必要な順に適用します。
4. §9の読取確認後、開発対象APIに`COCOLON_EMLIS_THREAD_MODE=development`、`COCOLON_ENV=development`、`COCOLON_EMLIS_THREAD_DEVELOPMENT=true`を設定します。明示MODEが優先されるため、read_onlyを残して後二つだけを設定しても書込みは始まりません。開発確認にactiveや公開承認値を使いません。API・認証・DBが手順1で選んだ同じ環境であることを確認します。
5. 対象アプリが実際に採用する`lib/apiClient.js`の`API_BASE_URL`を確認し、開発APIへ接続するビルドを使います。RN CLI構成では、既存`babel.config.js`が公開API URLだけを`lib/compat/legacyWireContracts.js`へ埋め込みます。優先順は`EXPO_PUBLIC_API_BASE_URL` → `EXPO_PUBLIC_PIECE_API_URL` → `EXPO_PUBLIC_ANALYSIS_API_URL` → `EXPO_PUBLIC_MYMODEL_API_URL`で、空白のみの値を飛ばし、全未指定なら既存の本番hostを使います。開発確認では最優先の`EXPO_PUBLIC_API_BASE_URL`を手順1の開発URLへ明示設定します。稼働中のMetroを停止し、その値を設定したshellで`npm start`を起動してbundleを再作成・再取得します。埋込みbundleを作るnative buildでも、実際にJavaScriptをbundleするprocessへ同じ値を渡して再buildします。端末の実行時設定だけでは変更されず、dotenv自動読込みも追加していません。既存`metro.config.js`はこの4値をcacheVersionへ含めます。u79で実preset／Metroの合成module bundleは確認済みですが、実際のアプリbuild・接続先・認証/DBの組合せは対象端末で確認します。同じAPIから`/app/bootstrap`を再取得し、`feature_flags.emlis_threads_enabled=true`でreaderが有効になることを確認します。廃止済みの`Q2_DEVELOPMENT_OPT_IN`は変更しません。保存済みthread DTOの`can_write=true`を確認してから回答操作へ進みます。履歴検索・Emlis取得/回答・履歴操作も同じ設定APIへ到達することを確認します。
6. 本書§3の入力保存・回答・履歴・失敗／再開を順に確認し、結果と実際の差分を残します。必要に応じて§4のQ3項目を続けます。

Q4のreaderはdebug/release共通ですが、書込みはserverのmodeで制御します。公開用mode・経路はコードにあり、実際の有効化は§5です。開発設定を公開承認へ読み替えません。

現在の実装値は、threadの各attemptが30秒、既存の元submit budgetが3秒、専用RN clientのtimeoutが35秒です。実環境での処理時間と制限を確認して必要な場合に見直します。機能確認のために期限を無制限にしたり、保存結果不明を無条件の再生成へ変えたりしません。

## 7. 確認結果の残し方と、実装へ戻す場合

既存の開発資料・handoffへ、対象の版、環境、行った操作、期待した結果、実際の結果、残る問題を短く記録します。未実施・確認成功・不具合を区別し、個人の原文・回答・内部根拠を一般ログや公開資料へ載せません。新しい証明用の仕組みは作りません。

- 接続先・設定・適用順の問題なら、対象環境の設定・適用作業として直します。
- 保存の欠落、別人の参照、重複回答、訂正の復活、枠の不整合、画面の操作不能等があれば、その機能のコード不具合として修正します。
- いまのソースや検証でも確認できる不足は、この資料へ送って放置せず、該当Qの実装に含めます。
- Mashしかできない端末・画面操作が残った場合だけ、華恋側でできる確認と準備を終えてから、必要な操作を具体的に依頼します。

Q2の実装は完了しており、この資料を先に全件完了しないとQ3へ進めない、という扱いにはしません。Q3・Q4の実装結果、商品判断、環境確認、公開状況はそれぞれ正確に記録します。

## 8. Q3開始前の参照版（Q2履歴）

下記SHAはQ2時点。Q3は追加migration `20260911041749_emlis_q3_plan_rounds.sql`を含む既存PRの最新headを使用する。作成時に確認したPRは、いずれもopen／Draft／unmergedです。後日の実施時はその時点の対象版を確認します。

- [mashos-api PR #3](https://github.com/MassyuRed/mashos-api/pull/3)：`d67bb771c65564bb8341738366a8aea4e0f85887`。
- [Cocolon PR #30](https://github.com/MassyuRed/Cocolon/pull/30)：`f7b29302aaa18a59de1f42c12a5bad86349a6668`。
- [Q2 migration](https://github.com/MassyuRed/mashos-api/blob/d67bb771c65564bb8341738366a8aea4e0f85887/supabase/migrations/20260911020509_emlis_input_threads_q2.sql)。
- [Q2 service](https://github.com/MassyuRed/mashos-api/blob/d67bb771c65564bb8341738366a8aea4e0f85887/ai/services/ai_inference/emlis_thread_service.py)、[API設定](https://github.com/MassyuRed/mashos-api/blob/d67bb771c65564bb8341738366a8aea4e0f85887/ai/services/ai_inference/emlis_thread_config.py)、[RN client](https://github.com/MassyuRed/Cocolon/blob/f7b29302aaa18a59de1f42c12a5bad86349a6668/lib/api/emlisThreadApi.js)。


## 9. Q4の設定・停止・保存版の回復手順

設定のownerは`emlis_thread_config.py`。以下は適用準備であり、今回環境の値を有効化した記録ではない。

| COCOLON_EMLIS_THREAD_MODE | 読取り | 新規・回答・続行・frame・retry | 旧submitへの本文 |
|---|---|---|---|
| 未設定 | 旧二重development gateが真ならdevelopment、それ以外legacy | 同左 | 同左 |
| legacy | thread API無効 | 無効 | 従来I5。thread使用後の復旧先にはしない |
| development | 有効 | COCOLON_ENV=development と COCOLON_EMLIS_THREAD_DEVELOPMENT=true の両方が必要 | Q2/Q3の開発互換どおり空。専用readerで閲覧 |
| active | 有効 | COCOLON_EMLIS_THREAD_RELEASE_APPROVED=true が別途必要 | 保存済みcurrent_observationだけを従来comment_textへ投影 |
| read_only | 有効 | 503 application_paused | 保存済みcurrent_observationだけ。再生成しない |
| 不明な値、条件未成立のactive/development | 有効（read_onlyへ縮退） | 503 application_paused | 保存済みcurrent_observationだけ |

1. 対象版を既存PR3/30の確認済みcommitとして指定する。Q2 migration `20260911020509_emlis_input_threads_q2.sql`、次にQ3追加 `20260911041749_emlis_q3_plan_rounds.sql`が必要。Q4の追加DDLはなく、旧migrationを再作成・改変しない。未適用の環境ではreaderも有効にしない。
2. 初回配置では全API replicaをread_onlyとして起動し、本人認証・旧Q2/Q3保存版の取得、can_write=false、POST拒否、bootstrapのreader通知を確認する。新アプリはbootstrapを再取得する。旧アプリは既存passed＋comment_textの契約を使う。
3. 公開承認・環境確認が整った場合だけactiveと独立承認値を対象版へ設定する。アプリのフラグを変えるだけでは書込みを許可しない。旧I5との二重生成を避け、thread側失敗でI5をfallback作者として呼ばない。
4. 停止時は既存の配置手段で全writer replicaをread_onlyへ切り替え、旧active workerをdrain/停止する。modeはprocess環境値であり、全replicaへ即時伝播するDB共通kill switchではない。部分切替中を全停止とは記録しない。
5. 確認できた処理中の停止では、回答・確定意味・質問枠を保持したまま既存attemptをworker_interruptedとして閉じる。停止下で許すcommitは既存attemptの失敗処理だけで、新しい意味・本文・質問は書かない。processの強制消失等で結果が不明なら既存deadline後にsave_result_unknownを表示し、自動retryしない。
6. 回復は保存版互換のあるQ4 reader/writerで行う。GETで現在revisionと操作receiptを確認し、再開可能な確認済み一時障害だけ本人のretry_responseで同じ回答・operation・source/checkpointから新attemptを一つ作る。回答の再入力や質問枠追加は行わない。成功済み本文のACK消失ならGETで保存本文を戻す。
7. threadを使い始めた後はlegacyへの単純切戻しを正常回復としない。旧I5は保存済みの本人回答・撤回・訂正を無視するため、互換版が準備できるまではread_onlyを維持する。table/eventを削除するdown migrationや古いcheckpointへのpointer巻戻しは行わない。

current_observationがない場合、旧clientへ旧本文をpassedとして渡さない。新readerは履歴本文を別欄で表示する。処理中・結果不明・競合時のcacheは「前回確認した観測」と表示し、送信可否はserver側で再検証する。質問・回答・内部sourceを一般ログへ送らない。


## 10. 2026-10-03 u83 — 接続先の読取結果と適用準備

対象sourceはCocolon `84ada16b27066abe8d7255dff959c8edd8f95ad3`、API `773d2d9b5a1641538e2a79e994b8236f2dc7f5f1`。本節は§6の対象確定を進める記録であり、DB適用・配置・有効化・配布の実施記録や承認ではありません。

| 対象 | 今回確認できたこと | 残る確認 |
|---|---|---|
| app→API | API既定値は `https://mashos-api.onrender.com`。公開URLをbuild時に変える仕組みは§6のとおり。 | 実機向けAPIの選定と稼働revision・mode。3つの公開GETはこの環境でread timeoutとなり、状態を取得できなかった。 |
| app認証 | `lib/supabase.ts` はproject `oeahmpmigszggnkyiivq` に固定。API URL変更だけでは認証先は変わらない。 | serverが同じprojectの認証/DBを使うこと。固定認証先だけからAPIの実接続DBを推定しない。 |
| DB候補 | Supabaseで `cocolon-project` / ACTIVE_HEALTHY、取得したbranch一覧はmainのみ。Emlis保存用schemaは未導入。 | この共有projectを今回の実機確認に使う対象として確定すること。mainであることは開発専用を意味しない。 |
| iOS配布 | 過去のMashの明示選択はTestFlight。現行 `.github/workflows/ios-build.yml` は署名・archive・TestFlight uploadまで含む。 | 今回の端末OS版・build・接続先。workflowにAPI URLの選択input/envはなく、dispatchは未実施。 |

### DB catalogと既存SQLの照合

管理情報・catalogだけを読み、個人の入力/回答行は取得していません。migration履歴は空でしたが、それだけでSQL未導入とは判定していません。`public.emotions` / `public.profiles` は存在します。一方、`public.emlis_input_threads` / `public.emlis_thread_events` / `public.emlis_frame_feedback` と `emlis_parent_source` / `emlis_parent_visible` / `emlis_thread_read` / `emlis_thread_commit` / `emlis_thread_context` はcatalogにありません。

SQLで参照する親列を照合しました。`auth.users.id`、`emotions.id`、`profiles.id` はuuidの主キーです。`emotions.user_id` はuuid、`emotions` / `category` はtext[]、`memo` / `memo_action` はtext、`emotion_details` はjsonb、`created_at` はtimestamp without time zone、`profiles.subscription_tier` はtextです。参照列/型/主キーの存在確認であり、実適用の成功や全権限・実データ互換を保証するものではありません。

対象が確定した後に検討する既存migrationは、API上記HEADの次の2本です。SQLは変更していません。

| 順 | path | SHA-256 |
|---|---|---|
| 1 | `supabase/migrations/20260911020509_emlis_input_threads_q2.sql` | `8ec3369d5377046d933daaccc39123b7e92b7c1c33339136fdbc1a56a379c88f` |
| 2 | `supabase/migrations/20260911041749_emlis_q3_plan_rounds.sql` | `75a40ed8560651280fe913d2051a03fe2e77ee8cab25c91e512a985cc9a8a719` |

Q2はthread/eventとRPCを追加し、Q3はその保存構造を拡張してframe feedback/contextを追加します。RLSを有効にし、一般clientへ直接操作を許可せずservice_roleへ必要な権限を与える既存SQLです。親入力やprofileの行を書換えるSQLではありませんが、共有DBへtable・function・FK・index・権限等を追加する変更です。Q3はQ2の後に適用する必要があります。実適用や実DBの互換検証は未実施です。

### 再開位置

Renderの管理情報を読む連携は検索で見つかり、未導入・未接続だったため利用を提案しました。接続されたら、既存serviceの配置revision・実URL・接続project identityを読取りで確認します。secret値や利用者の本文を記録へ掲載しません。API/DB/appの対象を確定する前に、appの固定認証先へmigrationを先行適用しません。

対象が一致し、開発確認に使う範囲が確定したら、直前のschema・migration履歴とSQL identityを再照合し、Rule18 §11.3でstanding delegation外とされる実DB適用の個別承認を得ます。対象不一致・既存objectとの衝突・SQL差分があれば適用を止めます。適用結果が不明なら履歴/catalogを確認し、削除・再作成や盲目的な再実行へ進みません。配置・mode変更・TestFlight送信も今回の読取作業には含めません。以後のread_only→development→入力/回答/保存再表示は§6/§9の順序で確認します。


## 11. 2026-10-03 u84 — Renderの配置実態と次の限定読取

MashがRenderを導入し、「まっしゅ's workspace」の読取利用を明示許可した後に確認しました。§10の未接続状態から前進した記録です。設定変更・配置操作は行っていません。

| 項目 | Renderで取得した値 |
|---|---|
| Workspace | `まっしゅ's workspace` / `tea-d4pp61idbo4c73bf4hkg` |
| Service | `mashos-api` / `srv-d4ppfpm3jp1c73952bj0` |
| 公開URL | `https://mashos-api.onrender.com` |
| Repository / branch | `MassyuRed/mashos-api` / `main` |
| 最新deploy | `dep-d9v9a1k9v7es7399butg` / `live` |
| 配置commit | `a8ca4ddf7b7ae76bf7b3d73e74e3a5808d623428` |
| 配置完了日時 | `2026-08-14T04:10:58.28849Z`（JST 13:10） |
| 自動配置 | `autoDeploy=yes` / `autoDeployTrigger=commit`。main更新が自動deployにつながる。 |
| root directory | `ai/services/ai_inference` |
| build / start | `pip install -r requirements.txt` / `uvicorn app:app --host 0.0.0.0 --port $PORT` |
| 管理情報上の状態 | `not_suspended`、maintenance無効、1 instance、Virginia、現在free plan。health check pathは空。 |

最新5件のdeploy履歴は先頭がlive、他4件がdeactivatedでした。previewを含む既存service全5件のうち同repoのweb serviceはこの1件のみ（他は3 cron / 1 worker）で、別の既存開発APIは確認できませんでした。

配置commitのGitHub treeとbootstrap実装を照合すると、Emlis thread実装/Q2-Q3 migration/reader flagは含まれていません。現在のPR3 `457e8afa93086893ed1de3d73092515d468c7664` がそのまま稼働中だと扱えません。main更新は配置効果を伴うため、文書確認の延長でmerge・branch変更・deployしません。

### 接続DBの証拠と限界

service読取に環境変数値はなく、専用の環境変数GETもありませんでした。限定したappログ中のHTTP Request行のうち、直近の2026-10-01T20:42:37.508742357Z〜20:42:37.943946783Z（JST 10/02 05:42）の5件は、すべて `oeahmpmigszggnkyiivq.supabase.co` へのHTTP Requestでstatus 200でした。app固定認証projectと一致します。sourceの共有clientもこの配置commitとPR版で同一で、runtimeの `SUPABASE_URL` から接続URLを構成します。

これは最新配置版の稼働期間中に観測した直近の接続実績です。現在の環境設定値の直接確認、Emlis schema導入、本人認証一往復や端末成功を証明しません。本日07:00 UTC以降をHTTP RequestとSupabase hostで絞った検索は0件で、一度だけ過去7日へ広げて上記5件を確認しました。抽出・記録したのはhost/時刻/statusだけで、利用者の本文やpath/query/UUID/tokenを保持・掲載していません。公開health/bootstrapは別の取得経路でも取得不能であり、Renderのliveを公開HTTP成功の代用にしません。

### 次に確認する範囲

当該serviceのDashboard Environmentで、`SUPABASE_URL` のhostと、`COCOLON_EMLIS_THREAD_MODE` / `COCOLON_ENV` / `COCOLON_EMLIS_THREAD_DEVELOPMENT` / `COCOLON_EMLIS_THREAD_RELEASE_APPROVED` の有無・非secret値だけを確認します。認証key/tokenは取得・表示・記録しません。旧配置版は問いシステム設定を使わないため、値があってもEmlis有効化の証拠にはしません。

利用可能なpluginがこの読取を提供しないため、browserでの限定確認に切り替える許可を求めます（利用ツールがplugin不足時のbrowser fallbackに事前許可を要求）。この確認では保存・設定変更・deployを行いません。現在設定と開発対象を確定した後に、§6/§9の順序で既存Q2→Q3・API配置・read_onlyからの確認に必要な個別scopeを提示します。今回のworkspace利用許可は、共有DB適用・新service/課金・main更新・有効化・TestFlight送信を含みません。


## 12. 2026-10-03 u85 — 確定した接続先とDB適用の限定提案（未承認・未実行）

MashがRenderの設定値として `SUPABASE_URL=https://oeahmpmigszggnkyiivq.supabase.co` を直接共有しました。app固定認証先、§11の最近のAPI通信先、今回の設定値が一致します。§11で残したDB identity確認はこれで解消しました。browserのGoogleサインインはgeneric errorで停止したため、管理画面を華恋が読取完了したとはしません。共有画像に新mode用4項目が見当たらないことと、全環境に設定がないことは分けます。この限定DB準備に、追加のbrowser復旧や端末確認を必須前工程として足しません。

### 承認を求める一作業

目的は、既存の入力に紐づくEmlisの応答・問い・回答・frameを保存できるschemaを用意することです。適用しない間は、問いシステム版のAPIを配置しても、このDBで保存・再取得を確認できません。新規のAPI/DB環境やサービスを作らず、既に接続を確認した共有DBへ、既存SQLの追加だけを提案します。このDBを開発専用とは扱いません。

| 項目 | 固定する範囲 |
|---|---|
| 対象 | Supabase `cocolon-project` / project `oeahmpmigszggnkyiivq` の既存DB |
| SQL source | API commit `e49aa0565a59cbc7515d9f7838e8d430b5d29332`。§10の2本・SHA-256を維持。今回変更なし。 |
| 1本目 | `supabase/migrations/20260911020509_emlis_input_threads_q2.sql` / Git blob `2a4d6ee5c1ebe752f16f4ac3a0942e203beabe73` |
| 2本目 | `supabase/migrations/20260911041749_emlis_q3_plan_rounds.sql` / Git blob `b8d45a2748316f5440d0e9a4fe4f8e346a644724` |
| 追加対象 | `emlis_input_threads` / `emlis_thread_events` / `emlis_frame_feedback`、計5function、専用FK/index/制約/RLS/grant。Q3はQ2のtable制約とcommit functionを拡張。 |
| 実施方法 | 適用直前のcatalog/履歴/SQL identity照合→既存Q2→既存Q3の順でmigration適用→適用結果/catalog/権限照合。担当はrootの単一execution owner。 |
| 変更しない範囲 | 既存emotions/profiles/auth.usersの行・現在のAPI配置/main・Render環境設定・機能flag・アプリbuild/配布。認証key/tokenの取得・共有も含めない。 |
| 費用・作業量 | 新service作成・契約plan変更なし。SQL2本と適用前後の確認を一単位とし、別の補助基盤は作らない。所要時間は実施前のため未計測。 |

今回のfresh catalogでは3table/5functionはすべて不在、migration履歴は空、必要な親列/型は存在しました。親id主キーの先行照合は§10の結果を継承し、role/参照権限と併せて実適用直前に照合します。履歴が空だから既存DB全体が空だとは解釈しません。SQLは親の入力行を書き換えませんが、稼働DBへFKや権限を含むDDLを行うため、短時間のlock・競合の可能性はあります。RLSとservice_role限定の権限を保ち、通常clientの直接操作を新たに許可しません。

### 成功・停止条件

成功は、2本の適用記録を確認し、3table/5function、列/制約/index/FK、RLSとgrantがSQLどおりであることをcatalogで照合できた状態です。現行APIや個人の入力を使う書込試験は、この承認対象に含めません。migration履歴の実際のversionはツール応答を記録し、file名のtimestampがそのまま付いたと仮定しません。

対象project、SQL bytes、schema/履歴/権限に想定外の差があれば適用を止めます。失敗・応答不明では履歴とcatalogを読取り確認し、削除・再作成や盲目的な再実行をしません。Q2が成功しQ3が失敗した場合はQ2だけが残り得るため、到達状態を記録して止め、勝手に巻き戻しません。SQLや対象を変更して続ける許可へ広げません。

Rule18 §11.3はdatabase migrationをstanding delegation外とし、最新weekly §2.4/§6.10も実DB適用の個別許可を維持しています。そのため、本提案をMashが承認するまで適用しません。URLの共有は接続先の証拠であり、適用承認ではありません。適用後も問いシステムのAPI版は未配置・機能default OFFのままで、次のAPI配置/開発確認/実機一往復/商品受入れは別の未完了作業として残します。


## 13. 2026-10-03 u86 — Q2/Q3適用済み・事後確認完了

§12の「この2本の適用と、適用後の確認」にMashが明示承認したため、同節の固定範囲を実施しました。§12の承認待ち・未実行はu85時点の記録です。対象は共有Supabase `cocolon-project` / `oeahmpmigszggnkyiivq`。rootが単独で適用し、補助はread-only照合を担当しました。

### 実行したSQLと履歴

API commit `e49aa0565a59cbc7515d9f7838e8d430b5d29332` の2本を再取得し、§10/§12のblob/全文と一致することを確認して、変更せずQ2→Q3の順に適用しました。

| source file（`supabase/migrations/`） | 実際のmigration version / name | 結果 |
|---|---|---|
| `20260911020509_emlis_input_threads_q2.sql` | `20261003085240` / `emlis_input_threads_q2` | success |
| `20260911041749_emlis_q3_plan_rounds.sql` | `20261003085333` / `emlis_q3_plan_rounds` | success |

Q2 blob `2a4d6ee5c1ebe752f16f4ac3a0942e203beabe73`、SHA-256 `8ec3369d5377046d933daaccc39123b7e92b7c1c33339136fdbc1a56a379c88f`。Q3 blob `b8d45a2748316f5440d0e9a4fe4f8e346a644724`、SHA-256 `75a40ed8560651280fe913d2051a03fe2e77ee8cab25c91e512a985cc9a8a719`。履歴のversionはツールが実際に付与した値で、source file名の日付ではありません。

適用直前は対象3table/5function・衝突する型/indexが不在、履歴は空でした。親の必要列/型/主キー、実行roleのpublic CREATEと親REFERENCES、anon/authenticated/service_roleの存在を再照合しました。Q2成功後に2table/4functionとQ3前提制約3件・Q2履歴を確認してからQ3を適用しました。SQL実行失敗・部分適用・rollbackはなく、最終履歴は上表の2件です。

### 事後catalog照合

| 対象 | 確認結果 |
|---|---|
| テーブル/列 | `emlis_input_threads` 19列、`emlis_thread_events` 11列、`emlis_frame_feedback` 8列。全38列の型/NULL/default一致。 |
| 保存制約 | 全28件、うちFK8件。3つのevent pointer FKはDEFERRABLE INITIALLY DEFERRED。Q3のAWAITING_CONTINUE・started_question_limitを含む最終定義に一致。 |
| index | 全12件の列・式・unique・predicateが一致し、全件valid/ready。 |
| 関数 | `emlis_parent_source` / `emlis_parent_visible` / `emlis_thread_read` / `emlis_thread_commit` / `emlis_thread_context` の5件。引数・NULL default・戻り型・language・volatility一致。最終SQLから取り出した本文と保存本文が5件とも全文一致。 |
| 関数実行 | 全件security invoker、search_pathは空。PUBLIC/anon/authenticatedにEXECUTEなし、service_roleにEXECUTEあり。 |
| RLS/table権限 | 全3tableでRLS有効、FORCEなし、policy0。ACLにPUBLIC/anon/authenticatedなし。anon/authenticatedのSELECT/INSERT/UPDATE/DELETE/TRUNCATE/REFERENCES/TRIGGERは全false。service_roleには必要なDML権限があり、環境既定からの追加権限も保持。「4権限だけ」とは扱わない。 |
| 親schema | `auth.users` / `public.emotions` / `public.profiles` の参照対象列/型/NULL性と主キーが適用前後で一致。利用者データ行は取得せず、行snapshot比較はしていない。 |

catalog照合に不一致はなく、§12の成功条件を満たしました。これは保存schemaの配置確認であり、現行APIでの動作試験・実機確認・品質受入れの成功ではありません。適用SQLに親入力行の変更はなく、実API/RPCの書込試験も行っていません。

### 残る作業と境界

問いシステム版APIは未配置です。次は既存設計に沿って配置対象と開発確認の設定を具体化し、実機で入力→応答→回答→更新応答→保存再表示を確認する作業が残ります。API/main/Render設定・flag・build/配布は今回変更していません。追加承認が必要な配置等を今回のDB承認に含めません。

商品0/3・NOT_CLEAR・全体48%・default OFF・両PR Draft/open/unmerged、最新weeklyの作業配分を継承します。source/test/SQL/依存の変更と新しいtest実行はありません。GitHubでは既存4文書に結果だけを記録します。


## 14. 2026-10-03 u87 — read_only設定保存・意図しないmain再配置と続行手順

Mashは§13の次の作業「問いシステム版APIの配置と実機確認」に「進めて」と明示しました。今回の配置と必要設定について承認を取り直しません。初回は§9のread_only確認から進め、正式商品受入れ・active公開承認へ拡張しません。

### 現在の実態

| 項目 | 実測・固定値 |
|---|---|
| 対象 | Render `まっしゅ's workspace / tea-d4pp61idbo4c73bf4hkg`、既存 `mashos-api / srv-d4ppfpm3jp1c73952bj0` |
| 次に配置する固定source | API `7f1f7d92d296caeb913b8cab9599acab3318437d`（u86。以後のu87記録差分を自動で対象へ読み替えない） |
| 実行済み設定要求 | `COCOLON_EMLIS_THREAD_MODE=read_only` だけをMCP `update_environment_variables` の `replace:false` で更新。成功応答あり。 |
| 想定外の実effect | MCPが設定保存に続いてmain deployを自動起動した。単なるsave-onlyではなかった。 |
| 実際のdeploy | `dep-db0ceqe0tbcc73f811d0`、commit `2d2f06dad0d373373cdac63e10734385eefb53ca`、09:14:17Z開始→09:15:28Z live（JST18:15）。 |
| 前のliveとの差 | 親 `a8ca4ddf7b7ae76bf7b3d73e74e3a5808d623428` から `ai/tests/contract/test_api_contract_registry.py` 1本だけ。runtime/build source変更なし。依存の実解決内容や公開HTTP成功まで同一とは主張しない。 |
| 新APIの確認 | 問いシステムPR版は未配置。設定更新成功は同版のread_only有効性確認ではない。 |
| 今回のHTTP確認 | `/healthz` と `/app/bootstrap` は接続失敗。限定startupログ検索0件。RenderのliveをHTTP/認証/DB往復成功の証拠へ代用しない。 |

raw [Render APIの環境変数更新資料](https://api-docs.render.com/reference/update-env-vars-for-service)は自動deployしないと説明しますが、使用したMCP wrapperはdeployを追加で呼びました。rootはAPI資料のeffect境界をMCPにも当てはめた確認不足を認め、応答直後にMashへ報告・追加mutation停止・deploy/commit差分照合を行いました。今後このMCP操作をsave-onlyとして使用しません。PR metadataのbase_shaは現在mainのHEADの代用にせず、必要な場合はbranch自体を読むことも今回の差として保持します。新しい防御基盤やcheckerは作りません。

### 最小の続行操作

既存[Render Dashboard](https://dashboard.render.com/web/srv-d4ppfpm3jp1c73952bj0)の **Manual Deploy → Deploy a specific commit** に、固定SHA `7f1f7d92d296caeb913b8cab9599acab3318437d` を入力して **Deploy Commit**。この一操作だけをMashに依頼します。現在のMCPにはcommit指定/取消/rollback/service branch更新がなく、通常trigger_deployではmainを再配置します。CLIの認証もなく、browserは前回generic sign-in errorで止まっているため、追加ログイン試行を積み重ねません。

[Render公式手順](https://render.com/docs/deploys#deploying-a-specific-commit)ではDashboardのspecific commit配置はautoDeployをOFFにします。mainのmerge・branch変更・新service・plan変更は不要です。これにより、意図しないmain更新で指定版を上書きする経路も止まります。設定の再更新は依頼しません。

### 指定版配置後の確認順

1. Render deployのcommitが上記SHAでliveになったことを確認する。
2. `GET /healthz`、`GET /app/bootstrap` のreader flag trueを確認する。healthはDB疎通を保証しない。
3. 本人sessionで `GET /emlis/threads/by-input/{input_id}` のDTO・can_write=falseと、answers/actions/framesのPOST拒否を確認する。保存threadなしのNOT_CREATEDは保存済み往復成功とは別。実session/入力へ到達できない時は未実施として残す。
4. 開発確認時だけMODE=development / COCOLON_ENV=development / COCOLON_EMLIS_THREAD_DEVELOPMENT=trueの3値を揃える。MCPの自動deployはmainを再選択するため、その時点の配置経路を確認してから行う。active/RELEASE_APPROVED=trueは使わない。
5. TestFlight現行版で入力→初回応答と問い→回答→更新応答→履歴再表示を確認する。

read_onlyで止まるのは共有service全体のEmlis生成です。通常のemotions保存・他API書込は止まりません。developmentもservice全体に作用し、共有Supabaseと合わせてMash専用sandboxとは呼びません。

### 実機への既存経路

Cocolon固定source `10f94c2f6318f25b9ca3e2bf2077f2eb3dd79816` の `.github/workflows/ios-build.yml` は手動workflow、macos-26 / Node18 / iOS15.1以上、既存署名secretでRelease archive→IPA→TestFlight uploadを行います。対象branchは `agent/three-core-cmee-current-structure-20260815`。既存API hostを維持するのでAPI URL input追加やapp main mergeは不要です。APIの指定版配置後にActionsの **iOS TestFlight Build → Run workflow → 対象branch** を使います。pluginにはworkflow_dispatchがなく、古いrunのrerunは使いません。upload完了、TestFlight処理完了、Mash端末への導入、実機成功を別々に確認します。

今回の新規test/ソース/SQL/依存変更・DB変更・TestFlight送信はありません。商品0/3・NOT_CLEAR・全体48%・source既定OFF・両PR Draft/open/unmergedを保持します。


## 15. 2026-10-03 u88 — 指定API配置完了、次は実機用TestFlightビルド

Mashが§14のspecific commit配置を開始したと通知し、rootが実deployを照合しました。

| 確認 | 実際の結果 |
|---|---|
| 指定版 | `7f1f7d92d296caeb913b8cab9599acab3318437d` |
| deploy | `dep-db0cjh1srm7s73f10vb0` / manual / 2026-10-03T09:25:49Z（JST18:25）live |
| 対象 | 既存 `mashos-api / srv-d4ppfpm3jp1c73952bj0`、既存URL・build/start方式を維持 |
| 自動deploy | autoDeploy=no、autoDeployTrigger=off。linked branchはmainのまま。 |
| health | `GET /healthz` → HTTP200、status=ok |
| reader通知 | `GET /app/bootstrap` → HTTP200、feature_flags.emlis_threads_enabled=true |
| 未認証拒否 | ダミーinput UUIDへのthread GET、Authorizationなし→401/Missing bearer token、無効token→401/Invalid or expired access token |
| 限定ログ確認 | 配置開始09:24:20Z以後のerror-level appログは取得範囲0件 |

public HTTPは許可されたネットワーク経路で実際に確認しました。先行u87の接続失敗は履歴に残し、今回の200で上書きして過去の成功とはしません。ここまでで**問いシステム版APIの配置とpublic応答・未認証境界は確認済み**です。本人データ取得、認証済みDTOのcan_write=false、POST503、DB保存往復は未確認。MODE=read_onlyは保存済みですが、reader通知だけでmodeや本人権限の全動作を証明しません。

次は[既存iOS workflow](https://github.com/MassyuRed/Cocolon/actions/workflows/ios-build.yml)の **Run workflow** で、branch `agent/three-core-cmee-current-structure-20260815` を選んで実行します。workflowはu87と同じblob `54c72248e9abf4535c41db75267b657b36359365`。このbranchのiOS手動runは取得時0件、確認した範囲に重複する待機/実行中buildはありません。現PRの既存CI成功と、native build/署名/配布成功は別です。現在のGitHub連携にdispatchがないため、この一操作だけMashへ依頼し、開始後のbuild/log監視・不具合対応は華恋が行います。

初回の実機確認では本人のログイン・接続・read_onlyを確かめます。その後、§14の共有serviceへの作用を保ったままdevelopmentの3値を揃え、入力→応答→回答→更新応答→保存再表示を確認します。環境変数MCPはmain再配置を伴うため使いません。active/RELEASE_APPROVED=trueは不要です。TestFlight送信・端末導入・実機成功はまだ実施済みにしません。

今回ソース・SQL・依存・DB・環境変数の追加変更なし。商品0/3・NOT_CLEAR・全体48%・source既定OFF・両PR Draft/open/unmergedを維持します。


## 16. 2026-10-03 u89 — TestFlightビルド失敗の修正と再実行

[run #59](https://github.com/MassyuRed/Cocolon/actions/runs/37113624603) はPR30 branch、SHA `ce8b95b43a252cdd988e078081396bcf7080c376`、attempt 1で開始しました。Pods・署名素材導入・番号設定までは成功しましたが、archiveはfmtのC++コンパイルで失敗しました。Export IPA/TestFlight uploadはskippedで、版1.0 (5901)は未送信です。

| 確認対象 | 実結果・対応 |
|---|---|
| native環境 | Xcode26.6 (17F113)、iPhoneOS SDK26.5、RN0.77.3、fmt11.0.2 |
| 失敗 | fmt/src/format.ccのcompile。format-inl.hの59/60/1387/1391/1394行でconstevalがconstant expressionではない。exit65。 |
| 既存ownerの修正 | Cocolon ios/Podfileのpost_installで、fmt11.0.2の共有base.hのApple条件1箇所だけを変更し、既存fallbackを全consumerで揃える。17行追加。 |
| 保持する範囲 | 依存版・C++規格・非Apple分岐・RN/署名設定・workflow・API接続先。他fmt版は変更しない。再適用は無変更。 |
| 補助検証 | 公式fmt11.0.2の実ソースをg++ C++20で前処理し、Apple macro=1→0、非Apple=1不変。patched本体のcompileとFMT_STRING整形/system_error/print実行が成功。read-onlyレビューでblockerなし。 |
| 未確認 | 修正版のRuby/CocoaPods処理、Apple Clang/archive、IPA export、TestFlight upload/処理、端末導入・実機往復。Linuxの成功で代用しない。 |

上流の[fmt #4740](https://github.com/fmtlib/fmt/issues/4740)、[React Native #55601](https://github.com/react/react-native/issues/55601)と実headerを照合しました。fmt11.0.2は単純な `-DFMT_USE_CONSTEVAL=0` を検出chainで上書きするため、既存Podfileで共有headerを修正しています。依存更新や新しいbuild基盤は追加しません。

次は[既存iOS workflow](https://github.com/MassyuRed/Cocolon/actions/workflows/ios-build.yml)から **Run workflow → branch agent/three-core-cmee-current-structure-20260815 → Run workflow** を新規実行します。**#59のRe-run jobsは旧SHAのため使いません。** 現GitHub連携はdispatch未対応なので、開始だけMashに依頼します。新runのhead SHAとarchive/uploadを華恋が確認します。TestFlightの表示名だけで判断せず、実際に送信されたversion/buildで識別します。

端末では既存sessionが有効ならそのまま使い、**ホーム→入力履歴→Emlisの観測を開く**を確認します。保存済みthreadがない入力は、現実装でGETのNOT_CREATEDを受けてmodalが閉じる場合があります。これを障害とも保存本文の再表示成功とも決めつけず、保存threadがない時に読取成功を前提条件にして初回生成を止めません。実historyがない場合に、読取確認のためだけの入力作成は求めません。本人sessionのDTO/can_write=false/POST503は未確認として残します。

その後は§14のdevelopment三値と共有serviceの作用範囲を守り、実入力・応答・回答・同じ保存threadの再表示へ進みます。配置済みAPI7f1f7d92…、read_only設定、Q2/Q3 schemaは今回変更していません。商品NOT_CLEAR・source既定OFF・Draft/open/unmergedを保持します。


## 17. 2026-10-03 u90 — native build/IPA成功、TestFlight送信工程で停止

[run #60](https://github.com/MassyuRed/Cocolon/actions/runs/37114827933) は、修正SHA `5266c80b4c5c054e14311616bc44cc630bf0e7ef`、attempt 1、job `111179510393`。09:58:25Z開始、10:07:58Zまでにfailureで完了しました。Pods導入・署名素材導入・archive・Export IPAはすべてsuccessで、前回のfmtコンパイルエラーは実native buildで解消しました。workflow式の予定version/buildは **1.0 (6001)** です。

Upload to TestFlightはfailure。Apple側受領・processing完了・tester配布可能性は未確認で、単なる未実行/skippedではありません。GitHubの詳細jobログ取得が2回Transport closedとなり本文を取得できず、artifactは0件でした。run/job状態は取得済みです。汎用fetchのjob/check-runs URL未対応400を、Apple側や利用者の権限エラーと混同しません。

次はMashに[該当job](https://github.com/MassyuRed/Cocolon/actions/runs/37114827933/job/111179510393) の **Upload to TestFlight** を開き、**エラー部分のみ**をテキスト/スクリーンショットで共有してもらいます。ログ全文や認証情報は不要です。実エラーを読んで原因と必要な修正を決めるまで、再送信・secret交換・新しいworkflow基盤を追加しません。

送信成功後の残件は§16のTestFlight処理/6001の実配布確認と端末導入です。既存ログインを維持して起動・本人履歴を確認し、APIが書込可能になった後で新しい確認入力→応答/問い→回答→更新→同じ保存threadの再表示へ進みます。NOT_CREATEDの閉じる挙動と、保存済み本文を読めたことを分けます。今回API再配置・環境変数・DB・source変更はありません。


## 18. 2026-10-03 u91/u92 — 契約エラーの確認とTestFlight送信成功

u91で共有画像を確認し、#60の送信はHTTP403 / `FORBIDDEN_ERROR.CONTRACT_NOT_VALID`でした。必要なApple契約が有効でないというエラーです。具体的な契約名・未同意の種類は画像だけでは特定しません。Apple公式資料を参照し、Mash本人へAccount Holderの契約確認を案内しました。u92でMashが同意と新しいビルド開始を報告したため、こちらから重複実行はしませんでした。

| 対象 | 確認結果 |
|---|---|
| 新run | [#61](https://github.com/MassyuRed/Cocolon/actions/runs/37115985371)、ID37115985371、attempt1、job111182790896 |
| app source | PR30 branch、`74c7cab7e730a1903fc81e2d3ec34ce7441a2a98`。前回archive成功版5266c80…から既存2文書のみ変更。 |
| 版番号 | workflow式により1.0 (6101)。端末上の実表示は次工程で照合。 |
| archive / IPA | 10:30:07Z archive success、10:30:11Z Export IPA success |
| TestFlight送信 | 10:31:52Z Upload to TestFlight success |
| run全体 | 10:32:06Z（JST19:32）completed/success |
| 未確認 | Apple processing、testerへの配布可能性、端末導入、本人session接続、生成/回答/保存往復 |

今回の送信は成功し、#60の契約エラーによる停止を解消しました。契約への同意はMashの報告であり、アシスタントがAppleアカウント内の契約を確認・承諾したものではありません。step/runの結果を取得し、大容量jobログは再取得していません。

公開health/bootstrapは初回TimeoutError、1回の再試行で200/status=okと200/emlis_threads_enabled=true。Renderの指定live SHA7f1f7d92…・autoDeploy offを読取確認しました。最初のタイムアウト原因は未特定で、cold startと断定しません。API再配置・環境変数・DB変更はありません。

次はTestFlightで **1.0 (6101)** が利用可能になったことをMashが確認し、更新→起動→自分の入力履歴を確認します。既存ログインを保ち、まだ表示されない場合はApple側の処理/配布状態の確認が残ると扱います。現APIはread_onlyのため、この時点を新規Emlis生成・回答・保存成功の確認とはしません。

生成の実機確認へ進む際は§14のdevelopment三値を揃えます。現Render連携にはsave-only/commit指定/branch更新がなく、env更新toolのmain自動deployというu87の実測は変わりません。既存Dashboardで **Save only → Deploy a specific commit（7f1f7d92d296caeb913b8cab9599acab3318437d）** を使う経路が残ります。今回その設定変更はまだ行っていません。
