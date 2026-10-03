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
