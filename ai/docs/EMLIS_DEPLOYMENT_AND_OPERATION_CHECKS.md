# Cocolon CMEE 問いシステム — 後日の適用・運用確認

> 2026-10-04 u101現在地：Analysis V2対応TestFlight 1.0 (6201)のarchive/export/upload成功。run62/37155776248、build SHA b11d1b321…、JST06:51完了。Apple処理/端末導入・本人入力→保存→再表示は未確認。API指定版liveはu100、最新native結果は末尾u101。

> 2026-10-04 u100現在地：指定Analysis API315f5b5…がRenderでlive。healthz/bootstrap200と未認証self-structure/status401を実確認。分析developmentはMashの設定手順実行報告、本人生成成功は未確認。次はPR30 branchから新規TestFlight build、本人入力→保存→再表示。詳細は末尾u100。

> 2026-10-04 u99現在地：Mashが分析API配置・development有効化・新版TestFlight送信と必要な管理画面操作を承認済み。再承認不要。RenderはGoogleパスキー確認待ち、GitHub管理画面も未ログイン。配置/設定変更/新buildは未開始。再開は認証の続きから。詳細は末尾u99。

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


## 19. 2026-10-04 JST u98 — Analysis開発配置の対象確認、配置・有効化の個別判断待ち

Mashの「分析構造の実装に進んで」を受け、添付前回txt、必須前提・作業ルール、全体構造/国家system/Analysis全file map、weekly20261003の最小実機方針、u96/u97とfresh sourceを確認した。今回の実装前確認で新しい接続不良は見つからず、追加の意味品質作業へ逸れずに、未完了のAPI配置・native接続を次の一作業へ固定する。コード・検査の変更はない。System Contextの生成済みsnapshotをfresh判定の代用にせず、GitHubの固定head/treeと対象実ファイルを直接読んだ。

### 今回の読取事実

- PR3 source `315f5b5dacb866e62805cfd6a906984c193dcc76`、PR30 source `dd47c0aa31cd662a313aeb137b469252e36b3e19`。両方Draft/open/unmerged。
- Render `mashos-api / srv-d4ppfpm3jp1c73952bj0` は `7f1f7d92d296caeb913b8cab9599acab3318437d` / `dep-db0cjh1srm7s73f10vb0` がlive、linked branch=main、autoDeploy=no/off。分析追加前の版である。環境変数の値は今回再取得しておらず、Emlis read_onlyは前回記録からの引継ぎ。
- Supabase catalogの読取で `analysis_observed_artifacts` の存在、RLS=true、anon/authenticated SELECT=falseを再確認。migration再適用・実利用者の入力/本文取得は0。
- 最新iOS workflow_dispatchはrun61/37115985371、source `74c7cab7e730a1903fc81e2d3ec34ce7441a2a98`、success。現sourceとのcompareでV2 renderer/contract/latest/viewer追加を確認したため、既存6101は分析V2確認版として使えず、新しいbuildが必要。端末導入の確認はまだない。
- API/RNの独立read-only reviewとrootのsource確認では、latest要求→snapshot/CMEE→commit→同UUID再読取→V2表示/既読の接続に新しいblocking mismatchなし。これは実行検査・実利用者往復の成功ではない。u96/u97の検査数を今回再実行した件数へ加算しない。

### Mashへ提示する限定実行範囲（未実行・承認待ち）

1. 既存Render serviceに上記API source版を指定commitとして配置し、`COCOLON_ANALYSIS_OBSERVED_MODE=development` を設定する。これは共有serviceの認証済みself-structure経路全体への作用で、Mashだけのuser allowlistではない。Emlisの設定、料金、DB schema、旧worker/cronはこの操作で変更しない。全旧generation入口を止めたglobal cutoverとは扱わない。
2. PR30 branch `agent/three-core-cmee-current-structure-20260815` から既存iOS TestFlight Buildを新規実行し、V2対応版を作成/送信する。上記app sourceが必須baseline。開始直前のhead差分を確認し、実際のrun SHAとversion/buildを記録する。旧runの再実行を新sourceのbuildにしない。
3. 配置SHA/live・health・未認証拒否・build/送信結果を華恋が確認し、本人端末で保存済み入力→分析表示→閉じる/再表示の一往復を確認する。文章/図の一致と同じ保存identityを確認し、未対応sourceは未生成として扱う。private本文/tokenをGitHubへ記録しない。
4. 生成停止が必要なら同じAPI版でread_onlyへ移し、保存済V2の読取を維持する。offや旧APIへの無条件切戻しでV2保存を不可視にしない。

Render連携のtrigger_deployにはcommit指定がなく、env更新MCPにはu87でmain deployを起動した実測があるため、この二つを使って対象版配置を代行しない。公式DashboardのEnvironment **Save only** → **Manual Deploy / Deploy a specific commit**を使う（[deploy docs](https://render.com/docs/deploys)、[env docs](https://render.com/docs/configure-environment-variables)）。GitHub連携にはworkflow_dispatchがない。承認後、利用可能な承認済み操作経路を確認し、必要な開始操作だけをMashへ依頼する。未承認のbrowser fallback、secret取得、新service追加、main mergeは行わない。

Rule18 §11.3とu96/u97末尾が実配置・有効化・native配布をDB追加承認と分離しているため、この範囲の個別承認を求める。前回DB適用承認を再質問しない。今回は既存引継ぎと運用資料への記録のみで、API/RN source・test・SQL・稼働設定・deploy・native build/配布は未変更。STRUCTURE_MAP_DELTA_NONE（owner、route、source構成変更なし）。primary outcomeはBLOCKER_NARROWED、商品0/3・NOT_CLEAR・全体48%を保持し、分析完成とはしない。


## 20. 2026-10-04 JST u99 — 配置・有効化・TestFlight送信の承認受領、管理画面認証から再開

Mashはu98で提示した「必要な管理画面操作も含め、この範囲を進めてよいでしょうか？」に「進めていいよ、お願い」と明示承認した。指定API配置、分析development、PR30からの新規TestFlight作成/送信、本人入力から保存再表示までの確認と必要な管理画面操作は承認済み。同範囲の再承認を要求しない。u98の「個別判断待ち」は履歴であり、現在の残件は実行と認証である。

- 配置対象APIは `315f5b5dacb866e62805cfd6a906984c193dcc76`、既存Render `srv-d4ppfpm3jp1c73952bj0`。Dashboardで `COCOLON_ANALYSIS_OBSERVED_MODE=development` を **Save only** し、**Deploy a specific commit** を使う。linked mainのdeployを起動するenv更新MCP/汎用triggerは使わない。Emlis設定・DB・料金・worker/cron・main/mergeは範囲外のまま。
- 再開時にRender deploy一覧を再読し、`7f1f7d92d296caeb913b8cab9599acab3318437d` / `dep-db0cjh1srm7s73f10vb0` が依然liveと確認。新しい配置は開始していない。実環境の変数変更も未実施。
- 承認済みbrowser経路で対象Render画面を開いたところ未ログイン。安全な認証UIでMashがGoogleを選択し、手動操作への移行後、再開時の表示はパスキー本人確認待ちだった。認証成功とは扱わない。認証情報の取得/転記はしない。GitHubのworkflow画面も未ログインで新規実行ボタンはまだ利用不可。
- GitHub連携で最新iOS run61/37115985371、source74c7cab7…、successを再確認し、queued/in_progressに新しいiOS runなし。PR30確認時headは3c62e2cd…（u98記録のみ、product baseline dd47c0aa…）。今回の記録もdocs-onlyであり、新規dispatch時の実head/run SHAを改めて記録する。workflowは既存 `.github/workflows/ios-build.yml` の `workflow_dispatch`、branch `agent/three-core-cmee-current-structure-20260815`。run61のrerunを新sourceのbuildとして代用しない。新build番号は実run確定まで未確定。
- 実機の最小確認は新版で「分析 → わたしマップ」を開き、文章・項目・件数・線・未確定表示を読み、入力変更や強制更新を挟まず「こころ天気」へ切替えてから「わたしマップ」を再表示する。初回最新artifactの再表示を確認し、月次用の「わたしマップの履歴」への出現を条件にしない。保存identityはAPI側で照合する。空/422等は実表示を記録し、未対応sourceを成功扱いしない。

今回は既存3文書への承認/再開地点記録のみ。新規source/test/SQL/依存/workflow変更、DB適用、配置、環境変数変更、native build/送信、実本人往復の成功は0。STRUCTURE_MAP_DELTA_NONE。商品0/3・NOT_CLEAR・全体48%を保持。認証後に承認済み実行をそのまま再開し、準備や記録更新を商品進捗へ換算しない。


## 21. 2026-10-04 JST u100 — 指定Analysis API配置liveと公開稼働/認証拒否確認、新版native開始待ち

MashがRenderを自分のブラウザで操作すると指示したため、承認済み範囲のEnvironment `COCOLON_ANALYSIS_OBSERVED_MODE=development` → **Save only** → **Deploy a specific commit** の手順を渡した。Mashから「開始したー」と報告を受け、華恋はRender連携の読取と公開HTTPで事後確認した。Cloud Browserログイン待ちはRenderの実行blockerではなくなった。

### 確認した実配置

- service `mashos-api / srv-d4ppfpm3jp1c73952bj0`、deploy `dep-db0n8lnavr4c738g3s5g`、manual。
- exact commit `315f5b5dacb866e62805cfd6a906984c193dcc76`。開始2026-10-03T21:32:06Z、**live/finished 21:33:30Z（2026-10-04 JST06:33）**。旧7f1f7d92…のままとは扱わない。
- 配置後service再読取：linked branch=main、autoDeploy=no/off。source/依存/workflow/main/merge/料金/DBの追加変更なし。既存DB migrationを再適用していない。
- live後の実HTTP GET：`/healthz` **200** / status=ok、`/app/bootstrap` **200** / emlis_threads_enabled=true、未認証 `/self-structure/latest/status` **401** / Bearer token required。private本文・本人tokenを使わず、生成/writeを伴う確認はしていない。
- **Analysis modeは未認証APIでは判別できない**。exact sourceのbootstrapにAnalysis flagはなく、self-structureはmode分岐より先に認証する。development設定は手順に対するMashの実行報告であり、環境変数値の独立取得や本人生成成功とは区別する。emlis_threads_enabled=trueもEmlis developmentの証拠ではない。
- ログ読取toolはworkspace未選択で取得不可だった。配置statusとHTTPの直接確認で必要な初期稼働を検証し、ログ取得成功とはしない。新規秘密情報取得・credential操作なし。

### 残る最小一往復

新しいiOS runはまだなく、最新run61/37115985371成功、TestFlight6101は分析V2前の版。GitHub管理画面は未ログインで、新規workflow_dispatchは接続toolにない。既存 `iOS TestFlight Build / .github/workflows/ios-build.yml` の **Run workflow** で `agent/three-core-cmee-current-structure-20260815` branchを選択し、新規開始する必要がある。旧run61の再実行はしない。開始前確認head a811481c…（u99文書のみ、app product baseline dd47c0aa…）、このu100も文書のみ。実runのhead SHA・build番号・送信結果は開始後に記録する。

native更新後、本人の保存入力がある「分析 → わたしマップ」を開き、文章/図、入力を変えず「こころ天気」へ切替後の再表示を確認する。同UUID保存の検証は本人認証後に行う。空/422/unsupportedは未生成として記録する。月次履歴への出現は初回latest確認条件にしない。

今回の前進は**指定APIの実配置と初期HTTP確認**。本人入力の生成・immutable保存・再表示、native build/送信・端末導入、商品受入れは未完了。既存3文書のみ更新し、STRUCTURE_MAP_DELTA_NONE、全体48%・商品0/3/NOT_CLEARを維持。配置/有効化/native配布の承認はu99から継続し、再承認待ちへ戻さない。


## 22. 2026-10-04 JST u101 — Analysis V2対応TestFlight 1.0 (6201)送信成功、本人端末確認へ

Mashが既存workflowの新規実行を開始した。華恋は新しいrunを読取確認し、二重起動・旧runの再実行を行わず、工程完了まで監視した。

- **iOS TestFlight Build run62 / 37155776248 / attempt1**、job `111298739887`。
- branch `agent/three-core-cmee-current-structure-20260815`、実build SHA **`b11d1b321b4b1fb5497e866c8fc2edf3c25600ba`**。分析V2のcontract/renderer/latest/viewerを含むdd47c0aa…の後にu98〜u100の文書のみ追加した版。送信sourceと今後の記録HEADを区別する。
- 実workflowの式は `62 * 100 + 1 = 6201`。iOS MARKETING_VERSION=1.0、CFBundleVersionをこの値でarchiveへ渡すため版は **1.0 (6201)**。
- Build iOS archive **success**（21:49:39Z）、Export IPA **success**（21:49:49Z）、Upload to TestFlight **success**（21:51:38Z）。jobは21:51:44Z、workflow全体は21:51:45Z（JST06:51）**success/completed**。run metadataとsteps/timestampsを別読取で照合した。
- [run62](https://github.com/MassyuRed/Cocolon/actions/runs/37155776248)。secret・署名素材・認証tokenの値は取得していない。途中のarchive継続表示と最終成功を区別し、機械待ちを失敗とは扱っていない。
- Apple側processing完了・tester向け利用可能・本人端末への更新はまだ確認していない。送信成功を端末導入/本人接続成功へ換算しない。

次はTestFlightで **1.0 (6201)** へ更新し、既存本人アカウント/保存入力で「分析 → わたしマップ」を開く。「記録から見えるわたし」「観測された内容」「まだ確定していない部分」「文章で読む」の実表示、観測カード/文章/図の一致を確認する。入力変更や強制更新を挟まず「こころ天気」へ切替えて戻り、同じ内容を再表示できるか確かめる。

**保存identityの境界**：rendererは保存UUID/`projection_of`をユーザー画面へ表示しない。見た目が同じだけで同一immutable保存identityの実照合を完了したとはしない。認証済み本人API応答等との照合は残件。今回本人認証での生成・保存・再読取を実行していない。月次用履歴への出現は初回latest確認条件にしない。

u100で確認済みの配置API315f5b5… / deploy dep-db0n8lnavr4c738g3s5g、health/bootstrap200・未認証status401を継承。このturnでAPI再配置・環境変数・DBを変更していない。development設定はMashの手順実行報告であり、未認証bootstrapによる独立証明とはしない。

今回の記録変更は既存3文書と既存PR3/30の説明更新のみ。source/test/SQL/依存/workflowの新規変更・追加検査は0、STRUCTURE_MAP_DELTA_NONE。新版native archive/export/upload成功は実施済みの前進として記録するが、商品0/3・NOT_CLEAR・全体48%は保持し、本人実機の分析一往復を次の確認点とする。


## 23. 2026-10-04 JST u119 — 期間比較と内容修正版の適用候補

**u120でMash承認を受領し、DB適用・照合まで完了。現在地は§24。以下はu119で固定した実行範囲。** u118までの実装を共有API/DBと本人端末へ接続する範囲を固定する。§20の旧版315f5b5の配置承認は完了済みとして保持し、今回の新migration/比較有効化の許可へ拡張しない。Rule18 §11.3およびu117に従い、実環境を変える直前の判断として提示する。

| 対象 | 固定する内容 |
|---|---|
| DB | 共有Supabase `cocolon-project / oeahmpmigszggnkyiivq`。専用開発DBとは呼ばない。 |
| SQL | API `42ff019975a5d94c3c6de2a63623fb0864630ed4` の `supabase/migrations/20261004041627_analysis_period_comparison.sql` だけ。SHA-256 `c8e107dbbfb8705641ba08ba639231f136baf7443caa3eacadb6e51fb507f4b2`。 |
| API | 既存Render `mashos-api / srv-d4ppfpm3jp1c73952bj0`、workspace `tea-d4pp61idbo4c73bf4hkg`、同URL。指定commitは `42ff019975a5d94c3c6de2a63623fb0864630ed4`。 |
| app | Cocolon `cd83cf9e70c7c7b603d65aac8a8d8afed7e892d8` を製品source基準とし、既存PR30 branchから新規iOS TestFlight Build。今回以後のdocs-only commitは製品差分を照合して実run SHAを記録する。 |
| 初期設定 | 新APIは `COCOLON_ANALYSIS_OBSERVED_MODE=read_only`、`COCOLON_ANALYSIS_PERIOD_COMPARISON_MODE=off` で保存読取を確認する。 |
| 確認用設定 | 対応APIと新nativeを確認後、上記2値をともに `development` にする。共有serviceの認証済み分析経路全体へ作用し、Mash専用allowlistではない。 |

### 読取確認済みの実状態

- SupabaseはACTIVE_HEALTHY／Postgres17.4.1.074。適用履歴はQ2、Q3、旧分析 `20261003204421` の3件。比較snapshot RPCはまだ存在しない。
- 比較SQLが置換する旧CHECK名と定義、RLS=true、anon/authenticatedの表/RPC権限なし、service_roleの必要権限、親変更trigger4本が候補の前提に一致する。旧commit/read/invalidate/source_snapshotのDB関数本文4件も元SQLと全文一致。
- Render liveは `315f5b5dacb866e62805cfd6a906984c193dcc76`／`dep-db0n8lnavr4c738g3s5g`、linked main・autoDeploy=no/off。設定値自体は今回未取得。接続先DB・分析developmentは過去のMash報告を継承する。
- 最新nativeはrun62/37155776248、source `b11d1b321b4b1fb5497e866c8fc2edf3c25600ba`、TestFlight1.0(6201)。旧RNは比較状態を受理しても比較本文を表示しないため、新RN2fileを含むbuildが必要。
- 稼働版との差はAPI13file（runtime5/test5/docs2/SQL1）、app7file（RN2/test1/docs4）。元migration、依存、workflow、別coreのsourceは変更しない。

### 承認後の実行順

1. 直前に対象DB/project、migration履歴、旧CHECK/関数/ACL、source SQLのbytesを再照合する。同migrationまたは新RPCが既にある、関数/制約の前提が違う場合は再適用せず差分を確認する。
2. Supabase apply_migrationで上記SQLだけを適用する。新tableや既存保存行の書換えはなく、制約2件・比較snapshot RPC1・既存commit/read/invalidatorの拡張とRPC権限が対象。旧単期のguard/private v1/保存identityを維持する。適用後は実migration履歴名、関数本文、制約、RLS/ACL/triggerをcatalogで照合する。SQL sourceのtimestampを実履歴時刻と混同しない。失敗・相違ならAPI有効化へ進まない。
3. 既存PR30 branchでiOS TestFlight Buildを新規開始する。旧runのrerunは使わない。開始直前のheadと上記製品sourceとの差を確認し、実run SHA・archive/export/upload・version/buildを記録する。6201を新比較版とみなさない。
4. Render DashboardのEnvironmentで初期設定2値を **Save only**。**Manual Deploy → Deploy a specific commit** で上記API SHAを配置する。旧linked mainのLatest commit配置を使わない。live SHA、health200、未認証self-structure/status401、保存読取を確認する。healthだけでDB・本人認証の往復成功とはしない。
5. 新nativeを本人端末へ導入した後、確認用の2値を **Save only** し、同じ指定API commitを再配置する。比較を有効化できたことを認証済み生成で確認する。設定値の変更報告だけを比較生成成功とみなさない。
6. 既存本人sessionでわたしマップを明示更新し、比較表示と文章/図を確認する。当日の旧保存結果はflag変更だけでは自動再生成されないため、旧結果の再表示を比較生成の証拠にしない。以後は入力変更や強制更新を挟まず再表示し、同じ保存identity/本文/図を確認する。前期間なしはNO_PREVIOUS、未解釈は422、期限外は既存eligibilityに従う。端末の同じ見た目だけで保存UUIDの照合成功とはしない。実データの本文/tokenを公開GitHubへ載せない。

Renderのenv更新MCPは過去にmain deployを追加実行し、現trigger_deployはcommit指定を持たない。この2つで上記操作を代替しない。既存Dashboardの [specific commit](https://render.com/docs/deploys#deploying-a-specific-commit) と [Save only](https://render.com/docs/configure-environment-variables) を使用する。GitHub連携に新規workflow_dispatchはなく、開始操作が必要なら既存workflow画面を使う。以前のMash本人ブラウザでの実行希望を尊重し、華恋はできる読取/照合/DB操作を担う。新たなsecret取得・新service・plan変更は不要。

### 停止と復旧

新版で作る保存結果には、比較がなくても注記/不一致が含まれ得る。旧315f5b5は比較NO_PREVIOUS・注記0・不一致0だけを受理するため、比較flag OFFを旧APIへ戻す許可や互換性の証拠にしない。停止時は対応する新API/schemaを維持し、`OBSERVED_MODE=read_only`・比較offへ移す。同じ指定commitで設定を反映し、新規分析生成を止めて既存保存読取を保つ。保存行を消して旧版へ戻すことや、旧schemaを逆適用することはこの範囲に含まない。

この作業で増えるのはSQL1本の適用、既存APIの指定版配置/設定、既存経路の新native buildと確認。新サービス/依存/料金プラン/課金契約を追加せず、既存build枠を使用する。共有serviceの生成停止・developmentは全認証済み分析経路に及ぶ。Emlis設定、IF、global cutover、main/merge、正式商品受入れは今回の対象外。

u118の181検査/606 subtests・RN13検査、u117の隔離SQL58項目は既存候補検証として継承する。今回は読取照合と手順確定で、新規test/稼働writeは未実行。商品0/3・NOT_CLEAR・48%を再採点しない。


## 24. 2026-10-04 JST u120 — 承認受領・比較migration適用完了

Mashが§23の全範囲へ「進めていいよ」と明示承認。再承認は求めず、同節の対象/順序を維持して実行する。

**DBは適用済み。** `cocolon-project / oeahmpmigszggnkyiivq` へ指定SQLを無変更で適用し、successを確認した。実migration履歴は `20261004051211 / analysis_period_comparison`（source filenameは `20261004041627_analysis_period_comparison.sql`）。直前の旧schema/権限/履歴とSQL blob/hashは§23の前提どおりだった。

追加/置換4関数の実本文がSQLと全文一致。security/volatility/search_path、invalidateだけのUTC設定、service_role限定RPC権限、validatedな制約14件、RLSと表権限、既存trigger5本を確認。非変更3関数・他の制約/表権限も不変。個人入力/保存本文/ユーザーID/secretの取得、既存行の書換えや本人生成試験は行っていない。

**次は開始操作。** GitHub連携には新規workflow_dispatchがなく、確認したworkflow画面も未ログイン。Renderは前回のMash本人ブラウザでの操作希望を継承する。

1. [iOS TestFlight Build](https://github.com/MassyuRed/Cocolon/actions/workflows/ios-build.yml) → **Run workflow** → branch `agent/three-core-cmee-current-structure-20260815` → **Run workflow**。旧runのrerunをしない。現在の製品sourceはcd83cf9…と同じで、今回の記録もdocs-only。
2. [Render mashos-api](https://dashboard.render.com/web/srv-d4ppfpm3jp1c73952bj0) → **Environment**。次の2値を保存する。`COCOLON_ANALYSIS_OBSERVED_MODE=read_only`、`COCOLON_ANALYSIS_PERIOD_COMPARISON_MODE=off`。保存は **Save only**。
3. **Manual Deploy → Deploy a specific commit** に `42ff019975a5d94c3c6de2a63623fb0864630ed4` を指定して開始する。Latest commit/mainを選ばない。
4. 華恋が実run/deployのsource・結果を照合する。新native導入後のdevelopment2値への変更は§23手順5として続け、現段階のread_only確認と混ぜない。

この時点のAPIはまだ315f5b5…、native最新は6201。設定/配置/新build成功や比較生成の完了へ読み替えない。生成停止と旧保存読取維持は§23の手順を使用する。同範囲の承認は継続しており、残件は実行・配置後確認・本人端末の往復である。


## 25. 2026-10-04 JST u121 — API指定版live・新nativeの送信結果

Mashの開始報告後、指定API `42ff019975a5d94c3c6de2a63623fb0864630ed4` のmanual deploy `dep-db0u5lid0e5s73d7if7g` が **05:24:47Z（JST14:24）live** と確認した。既存service/URL/plan、linked main・autoDeploy=no/offを維持。実HTTPはhealthz200/status=ok、bootstrap200、未認証self-structure/latest/status401。05:23:34〜05:25:19Zのapp/errorログ0件。DB比較migrationはu120で適用済み、今回は再適用なし。

初期read_only/比較offはMashの設定手順実行報告を継承する。環境変数値を独立取得していないため、HTTP200やbootstrapをAnalysis modeの証明にはしない。

**新nativeの作成・送信も成功。** [iOS run63 / 37179645655](https://github.com/MassyuRed/Cocolon/actions/runs/37179645655)、attempt1、job111369421691。実build SHAは `b5098c6001c3c2ee6f8952163164360da3f4eac6`、指定PR30 branch。製品基準cd83cf9…との差は既存2文書のみ。workflow式63×100+1とbuild番号設定成功・archive引数から **1.0（6301）** を確認。archive05:34:08Z、IPA export05:34:14Z、TestFlight upload05:35:41Zがsuccess。job完了・run更新は **05:35:48Z（JST14:35:48）completed/success**。rootは補助担当が取得したrun/全stepsの実tool結果を確認した。Apple側processing・tester利用可能・端末導入は未確認。署名素材/secretは取得していない。

次はTestFlightに新版が表示されたら更新し、既存本人sessionで **分析 → わたしマップ** を開いて以前の保存結果を表示できるか確認する。Apple処理/配布可能性・端末導入・本人API/保存identityの照合は送信成功だけでは成立しない。空表示/エラーは実態を確認し、架空の保存行を作って通さない。

通常の分析タブはembedded/hideHeaderで、単独screenの「更新」ボタンは表示しない。§23手順6の明示更新を通常タブのボタンとして案内しない。比較有効化後の生成確認は、本人の通常の新入力保存でlatestを失効させて分析を表示する等、実際に使える入口を用いる。入力内容や過去記録を検査のために捏造しない。

新版導入・保存読取確認後、承認済みの次操作として **COCOLON_ANALYSIS_OBSERVED_MODE=development / COCOLON_ANALYSIS_PERIOD_COMPARISON_MODE=development** をSave onlyし、**同じ指定API42ff019…** を再配置する。旧APIへの切戻しやmainの汎用deployは行わない。同範囲の再承認は不要。

今回は配置/送信の事後確認と既存記録更新。source/test/SQL/依存の新規変更・追加検査0。本人端末往復・比較生成・正式商品判断は残件として保持する。

## 26. 2026-10-04 JST u122 — 保存結果なし表示の修正と承認済み生成再開

端末の「取得エラー」は、HTTP成功時の空本文/metaをRNが例外化する経路で発生する。画像時刻前後のlatest/ensure・statusは200、記録されたDB通信エラーは0。入力不足・本人データ消失・保存読取成功を断定しない。実応答本文とenv値の独立取得はしていない。

APIは適格な保存結果がない場合に正常空envelopeを返し、read_onlyでは新規生成しない。RNをその正常空envelopeの専用表示へ修正し、空結果を既読にせず、HTTP/通信失敗・不正versionは引き続き拒否する。関連RN17検査成功、詳細は06/API handoff末尾u122。修正版RNは6301未収録、後続buildで反映する。

旧保存の表示成功が得られないために生成を永久に止める前提にはしない。DB適用と対応API/newnative送信は成立済みで、次の生成再開はu120で承認済み。Mash本人のRender操作希望を継承し、同じ既存serviceで以下を実行する。

1. [Render mashos-api](https://dashboard.render.com/web/srv-d4ppfpm3jp1c73952bj0) → Environment → `COCOLON_ANALYSIS_OBSERVED_MODE=development` と `COCOLON_ANALYSIS_PERIOD_COMPARISON_MODE=development` を **Save only**。
2. **Manual Deploy → Deploy a specific commit** で `42ff019975a5d94c3c6de2a63623fb0864630ed4`。最新mainや新しい記録commitを配置しない。
3. 開始後、華恋が指定SHA/live/通信を確認する。本人端末の6301で「分析 → わたしマップ」を再取得する。空結果なら次のensureで生成可能になる。画面が保持される場合はアプリを開き直して再取得する。
4. 既存の同日保存が表示された場合、flagだけで再生成されない。本人の通常の新入力保存→分析表示等の既存入口で生成・比較を確認する。検査用の架空入力・過去入力の捏造・DB保存行削除はしない。
5. 生成結果の表示後、入力変更や強制更新を挟まず再表示を確認する。端末の同じ見た目は保存UUID照合の代替ではない。前期間なしのNO_PREVIOUS、材料未対応等の422を比較成功としない。

今回の環境変更/再配置/新native開始は未実行。2値の設定は認証済み分析経路全体へ作用する。停止が必要なら対応APIを維持してread_only/比較offに戻し、旧315f5b5や旧schemaへ切り戻さない。同範囲の再承認不要。表示修正版の追加native buildを生成再開の必須条件にはしない。

## 27. 2026-10-04 JST u123 — development手順後の再配置live

§26の手順開始をMashが報告。新deploy `dep-db0vo2ou01pc73c5psa0` は指定API `42ff019975a5d94c3c6de2a63623fb0864630ed4` で **07:12:32Z（JST16:12）live**。rootの実HTTPでhealthz200/status=ok、bootstrap200、未認証status401。既存URL・linked main・autoDeploy=no/offを維持した。

development2値の設定はMashの手順実施報告で、値を独立取得していない。read-only補助担当の07:11:07〜07:12:43.931Zログ確認はapp/error0件、request型分析path0件。機能有効化・本人生成・比較成功をこれだけでは成立としない。

次は6301のアプリを終了して開き直し、**分析 → わたしマップ**。表示結果を確認し、その後は入力変更/強制更新なしの再表示へ進む。通常タブに「更新」ボタンはない。空状態の表示修正u122は未buildであり、6301は以前の表示処理のまま。エラーが続いた場合は実際の文面・時刻をもとに確認する。新入力や過去記録の捏造、保存行直接変更、旧APIへのrollbackは行わない。

今回、新たなenv変更・deploy/build起動・SQL適用なし。本人生成/保存再表示・期間比較の実確認は次の残件。承認済み範囲の継続で再承認不要。

## 28. 2026-10-04 JST u124 — 生成失敗の診断版API候補

端末のanalysis_observed_map_unavailableと同時刻のlatest422を確認した。DB通信エラーは同request_perfで0だが、生成の内部理由は現行ログに残らず、入力不足や前期間の問題とは断定できない。既存realizerに、current/previous/comparisonの段階と固定許可リストの理由だけを記録する限定修正を用意した。raw本文・ID・例外/tracebackを出さず、HTTP/保存/公開DTO/意味生成は変更しない。関連186検査PASS、独立review blocking0。実機の生成復旧は未確認。

新しい配置対象SHAは[PR3先頭](https://github.com/MassyuRed/mashos-api/pull/3)のu124実装commitへ固定する。42ff019は現在稼働中の旧診断版であり、今回の修正を含まない。Mash本人の指定commit配置で進める。通常のtrigger_deployとenv更新MCPは使わない。

1. [既存Render mashos-api](https://dashboard.render.com/web/srv-d4ppfpm3jp1c73952bj0)の **Manual Deploy → Deploy a specific commit** へ、PR3先頭のu124 API SHAを貼り付ける。
2. DB・env値・native buildは今回変更不要。現行development設定と6301で診断できる。latest mainを選ばない。
3. 開始報告後、華恋が配置SHA/liveを確認する。その後、本人アプリを開き直し **分析 → わたしマップ** を一度表示し、失敗時刻のanalysis_observed_generation_unavailableを確認する。
4. ログの段階・固定理由から次の最小修正を判断する。route_not_establishedだけでは空/未解釈を断定できず、表示できた場合も本人生成・保存再表示の確認を分ける。

この節の作成時は未配置であり、旧exact SHAの配置承認や186 PASSを実機復旧へ読み替えない。停止は対応APIを維持したread_only/比較offという既存手順を使い、旧315f5b5へ戻さない。詳細は06/API handoff末尾u124。

## 29. 2026-10-04 JST u125 — 診断版API live・次の端末確認

Mashの指定commit配置後、deploy `dep-db11ebe0tbcc7392hjn0` がAPI `c4db3a3aae70d906ccb7a0c44c4862692b5287c1` で **09:08:07Z（JST18:08）live**。実HTTPでhealthz200/status=ok、bootstrap200、未認証status401。既存service・URL・linked main・autoDeploy=no/offを維持。09:06:53〜09:08:20Zのapp/errorと固定診断ログは各0件、hasMore=false。生成成功や全時間無障害を意味しない。

次は本人のアプリを完全終了して開き直し、**分析 → わたしマップ** を一度表示する。エラーが続いても再配置は不要。操作報告の時刻または画面と合わせて、華恋が固定stage/reasonログを確認する。現在の端末版を使い、追加build・DB/env変更・検査用入力は求めない。通常タブに更新ボタンはない。本人生成/保存再表示は未確認であり、診断版の配置成功と区別する。

今回は配置後の確認のみで、華恋から追加deploy/build/DB/env操作は行っていない。同じ範囲の再承認は不要。詳細は06/API handoff末尾u125。

## 30. 2026-10-04 JST u126 — current生成の要素0件、個人記録読取の確認待ち

Mashの再確認に対応するJST18:14の固定ログ2件は、いずれも `stage=current reason=analysis_observed_route_not_established`。latest422・supabase_errors0、直後status200。source freeze/graph compile後の要素0件であり、前期間比較前に停止している。対象期間が空か、文章の解釈未成立かは未確定。主語省略等の現行coverage制約だけから原因を断定しない。

既存関数/列型の読取は成立したが、本人記録件数・本文有無の集計SELECTは、自動承認レビューにより個人データの明示的読取許可不足で拒否された。記録データ取得なし、迂回再試行なし。次は直近28日の件数・本文有無と、必要時最大3件の原入力memo/memo_actionの非公開読取についてMashの確認を得る。書換え・削除・private本文/IDのGitHub掲載は含めない。

現API c4db3a3…は維持。同じ端末操作・deploy・build・env変更を重ねない。確認後の実資料に合わせ、原因箇所だけの修正を判断する。詳細は06/API handoff末尾u126。


## 31. 2026-10-04 JST u127 — 空期間422の修正候補と端末への反映

許可された直近28日の集計で今回期間が空と確認できた。本文は取得していない。空snapshotをCMEEの生成未成立へ送っていたAPI側を修正し、正しい期間/guard/member形状/比較整合を検証した上で既存の正常空envelopeへ返す。生成・保存を行わずrefreshed=false、月次history_saved=false。記録ありの未解釈422や保存層障害は維持する。API関連191検査とRN17検査が成功、独立read-only reviewでblockingなし。詳細は06/API handoff末尾u127。

今回は既存API1fileとtest2fileの補正で、SQL/共有DB/環境変数の変更は不要。稼働版は引き続き `c4db3a3aae70d906ccb7a0c44c4862692b5287c1`。修正版のexact commitはPR3先頭のu127配置候補として固定する。

1. [Render mashos-api](https://dashboard.render.com/web/srv-d4ppfpm3jp1c73952bj0) → **Manual Deploy → Deploy a specific commit** に、PR3先頭のu127配置候補SHAを指定する。既存設定2値developmentを維持し、Environmentの再保存は不要。
2. [iOS TestFlight Build](https://github.com/MassyuRed/Cocolon/actions/workflows/ios-build.yml) → **Run workflow** → branch `agent/three-core-cmee-current-structure-20260815` → **Run workflow**。u122の正常空画面修正を含む新規buildを開始する。6301のrerunは同修正を含まない。
3. 華恋が実deploy/runのsource SHA、live、health・認証拒否、native archive/export/uploadと実build番号を照合する。API配置だけで6301の空表示が直ったとはしない。
4. 新版がTestFlightで利用可能になった後、端末を更新し **分析 → わたしマップ** の正常空表示を確認する。「現在表示できるわたしマップはありません。」が対象。Apple側利用可能/端末導入をupload成功から推定しない。
5. 本人の通常入力が後日追加されたら、生成・保存再表示・比較の確認へ進む。今の空期間でそれらの成功を確認したとはしない。架空の記録を入力させない。

Mash本人の開始操作希望と、GitHub接続にworkflow_dispatchがなくRender連携にcommit指定deployがない制限を継承。汎用deploy/mainやenv更新MCPを使用しない。同範囲の再承認を求めず、開始後は読取照合を続ける。停止時は対応API/schemaを維持した既存read_only/比較off手順を使い、旧schema/旧APIへの切戻しや保存行削除はしない。

今回の共有DB変更・env変更・deploy/build起動は0。STRUCTURE_MAP_DELTA_NONE。今回の前進は正常不在処理の実装/合成検証であり、本人生成復旧・保存再表示・商品受入れは未成立。商品0/3・NOT_CLEAR・48%を維持。


## 32. 2026-10-04 JST u128 — 空期間補正版live・TestFlight 1.0（6401）送信成功

Mashの開始報告後、指定API `1a42b9ebc25ba9765bdb17658cf47dd631d9f40d` / deploy `dep-db146o2d0e5s73e1bc3g` が **12:16:55Z（JST21:16:55）live** と確認。12:19:51Zの実HTTPはhealthz200/status=ok、bootstrap200、未認証self-structure/latest/status401。12:15:29〜12:20:00Zのapp/errorログ0件・hasMore=false。既存service・URL・linked main・autoDeploy=no/offを維持。環境変数値は今回独立取得していない。

[iOS run64 / 37201625245](https://github.com/MassyuRed/Cocolon/actions/runs/37201625245) は指定source `166343c0b160e787b857a7b9d407b6f0afce756d`、attempt1。u122の正常空表示修正を含む **1.0（6401）** のarchive/export/uploadが全てsuccess。TestFlight送信は12:35:58Z（JST21:35:58）、job111434330974は12:36:07Zに完了、runも12:36:08Z更新でcompleted/success。

次はTestFlightに **1.0（6401）** が表示されたら更新し、既存本人sessionで **分析 → わたしマップ** を開く。直近28日に記録がない状態では「現在表示できるわたしマップはありません。」の正常表示を確認する。Apple側の処理完了/配布可能性・本人端末導入・認証済みの実空応答はまだ未確認。送信成功から推定しない。生成・保存再表示・期間比較は、本人が通常の入力を行った後に別途確認する。

華恋による追加deploy/build起動・DB/env変更はなく、今回は既承認操作の事後確認と既存4文書/PR説明の記録。source/test/SQL/依存変更・検査再実行0。STRUCTURE_MAP_DELTA_NONE。u127のAPI191/RN17 PASSは前回の候補検証として継承。商品0/3・NOT_CLEAR・48%とDraft/open/unmergedを維持する。詳細は06/API handoff末尾u128。

## 33. 2026-10-10 JST — Emlis未表示の原因調査（修正・配置前）

今回の依頼は、処理されるように見えて応答が表示されない原因の調査。前提資料・作業ルール、全体構造01/01A/01B/01Cと両repositoryの全tree、Emlis current map、最新weekly 20261010 §5.5、前回txtを参照した。System Context prepareの成功や全repository全文監査を主張せず、保存済み案内から対象原典を直接確認した。一般的な内容磨き込みには戻らず、本人の新規入力へ実機で応答を返す経路を対象とする。

### 確認した配置・処理

- Renderの稼働APIは `468663c8effc51c1bc33f165313eeb9417d16dc9`（10/06配置）。linked branch main、autoDeploy OFF。PR3調査時headは `d7e1cabf6f3f622f7e0f042d137eb1c29237dd42`。設定画面の画像だけを保存・稼働反映の証拠にせず、実ログのbudgetと稼働deployを照合した。
- 先行失敗はreply budget 3秒のTimeoutError。直近対象は **budget 10秒の内側、約5.94秒でSourceAdmissionError**、reply_timeout=false、表示用本文なし。両者を同じ「待ち時間不足」としない。
- 直近対象は原入力保存201、thread read/context RPC200の後、初回thread commitより前に停止。submit HTTP200は原入力保存の成功で、観測の生成・保存成功ではない。対象原入力は保存済み、thread未作成。読取時点でthread/event保存件数は0。RPCは存在しservice_roleの実行権限もある。
- 直近投稿は起動完了後。対象時間帯にOOM・異常再起動の根拠はなく、資源不足やcold startを今回の例外原因としない。

### 原因と限定再現

任意欄の `memo_action` がSQL NULLで保存される一方、CMEEのsource admissionは `memo` と `memo_action` の両方をstr必須としている。DBからthreadへ渡す境界で空値の扱いが一致していない。

1. `supabase/migrations/20260911020509_emlis_input_threads_q2.sql` の `emlis_parent_source` は、親のmemo/memo_actionをNULLのままJSONへ渡す。
2. `emlis_ai_current_input_bundle.py` はthought_text/action_textを正規化するが、`raw_current_input` は元の値を保持する。
3. `emlis_thread_service._request` はそのraw原本を `freeze_text_source` へ渡す。`source_kernel._source_leaf_values` の文字列検査で `noncanonical_current_input_source_shape` となり、初回thread保存・本文生成に達しない。
4. `emotion_submit_service.py` はreply例外を捕捉し、保存した原入力を成功のまま返しつつ、観測本文を空にする。

配置版の無改変sourceと必要依存だけをロードした、ネットワーク/DB呼出しなしのsource admission検証で再現した。必要最小の非公開原入力1件と合成9条件を確認し、原本の変更は0。片方の任意テキスト欄がNULLなら同じ例外、メモリ上のコピーでNULLだけを空文字へ変える候補ではsource admissionを通過する。両欄空、数値/list等の不正型、secret、非canonical categoryに対する拒否は保持された。

これは **source admission段階の因果確認** であり、修正版serviceの実装、本文生成、SQL保存、API往復、実機復旧の検証ではない。原入力・ユーザー/記録ID・本文/digestはこの公開記録へ載せない。source_kernel、thread_service、current_input_bundle、reply_service、thread_sourceは配置版とPR3調査時headでblob一致を確認したため、単に当時の最新headを配置しても、この不整合は解消しない。

### RNで無表示になる理由と配布差分

- 入力送信timeoutは30秒、thread通信は35秒。配布候補6401のsourceとPR30調査時headで同じ。以前の3秒はbackend内部budgetであり、アプリ側3秒timeoutではない。
- 入力保存後にthread GETを行うが、NOT_CREATEDなら `useEmlisThread.open` が画面を閉じる。旧fallbackはPASSEDかつ本文ありの場合だけ表示するため、今回のように両方ない場合は「記録しました」だけになる。
- GETは読取だけで、未作成の過去観測を生成しない。待機や履歴再表示だけで今回の未保存観測が回復するとは案内しない。
- 最新成功iOS候補は [run64](https://github.com/MassyuRed/Cocolon/actions/runs/37201625245)、source `166343c0b160e787b857a7b9d407b6f0afce756d`、1.0(6401)。archive/export/upload成功を確認。端末の現在導入版は未確認。
- 10/06の「履歴から明示的に開いたとき、未作成の説明を残す」修正はPR30にあり、6401には未収載。直近対象のrequest User-Agentは6301を示すが、現在も同じ端末版とは断定しない。履歴表示修正だけで本文生成が直るわけではない。

### 次の最小修正と残る確認

既存thread application adapterで、コピーした原入力の任意テキスト欄がNULLの場合だけ空文字へ正規化する方針を検討する。source kernelの一般拒否を弱めず、DB原本/source_snapshot/CAS、原文文字列、既存source identity、Q3の本人履歴と保存済み再読の整合を維持する。DB書換え・新schemaはこの原因解消の前提ではない。今回の候補は未実装であり、serviceから生成/保存/再読までの検証が次の作業である。

生成失敗時に理由を受け取れない画面側の残差も区別する。現在の端末build番号と、より新しい未表示の発生日時・入力直後か履歴操作かだけをMashへ確認すればよく、キー・原入力の再提出やログ採取を求めない。

今回の変更は既存資料への調査記録のみ。製品source、test、SQL、稼働DB、環境変数、deploy、native build、mergeの変更・実行は0。STRUCTURE_MAP_DELTA_NONE（既存経路の接続不整合を診断しただけで、構造は変更していない）。調査を実機復旧・正式商品合格へ換算しない。

## 34. 2026-10-10 JST — NULL任意欄のAPI修正と生成・保存・HTTP再取得

MashからAPI側の空欄処理修正と「応答生成→保存→再表示」の検証を明示承認された。端末版は本人確認で **6301**、最新の症状は **10/07、入力直後と履歴から開いた時の両方**。§33の端末版未確認・修正未実施は調査時点の履歴とし、本節を今回の修正状態とする。

### 変更

既存 `ai/services/ai_inference/emlis_thread_service.py::_request` の生成用コピーで、存在する `memo` / `memo_action` が `None` の場合だけ空文字へ変える5行を追加した。文字列のstrip・書換え、欠落key・数値・bool・配列の救済はしない。DB原本、保存 `source_snapshot`、SQLのCAS、本人履歴guardは元のNULLを保持する。共有source kernel、意味/本文作者、公開wire、SQL、依存定義、待機時間は変更していない。Q3の履歴admissionにも同じadapterが適用される。

既存 `ai/tests/test_emlis_q4_application.py` にNULL回帰17件を追加した。新file/owner/routeなし、`STRUCTURE_MAP_DELTA_NONE`。親が最終差分を確認し、独立read-only reviewでもblockingな製品問題なし。

### 確認結果と範囲

- 修正前の同一製品sourceで、片方NULLの現在入力・本人履歴・回答開始の11ケースすべてが `noncanonical_current_input_source_shape` で失敗した。
- 修正後の追加17ケースは全成功。Free/Plus/Premiumの両方のNULL配置で、実reply入口→実作者→実Q2/Q3 migration・RPCの保存→新serviceによるHTTP GETを通した。GETの作者呼出しを禁止しても保存済み本文が同一で、原入力と保存snapshotのNULL、thread/eventsの不変を確認した。
- 回答後の本文保存と再取得、source参照の安定、保存後のNULL→空文字変更に対する409、Plus/Premiumの未thread本人履歴と元guard保持、欠落/不正型/両欄空の拒否も確認した。
- Q2/Q3/Q4全対象は **180 PASS / 17 FAIL（計197）**。追加17件にFAILなし。修正前commit `a5706c0337f135fddbf272130c30d9450a059d80` の無変更worktreeでQ4を同じruntimeで再確認し **109 PASS / 同じ17 FAIL**。失敗nodeとassertion内容は完全一致で、既存の文面・名詞化等の期待と現作者の不一致だった。既存期待の変更、skip、xfailはせず、全検査PASSとは報告しない。Q2/Q3の54件は全成功。
- 途中の修正後初回は追加11 PASS / 6 FAIL。6件は追加テストが読取RPCの毎回変わる `now` まで同一比較した検査側の誤りだった。保存対象比較から読取時刻だけを外し、製品修正は同じ5行のまま上記結果を得た。
- CPython 3.12.14、pytest 8.4.1、PGlite 0.5.8、httpx 0.28.1、FastAPI 0.143.0、Pydantic 2.14.0の隔離runtimeをこの作業で準備・import確認した。旧sessionのruntime信用は継承せず、Cycle001の過去Gateを再開しない。製品依存の更新は0。
- 既に非公開で確認済みの本人原入力1件についても、識別子を隔離用へ置換し、元本文/ラベル/NULL/日時を保持して隔離DBへ入れ、Freeの現在入力経路で実作者の生成・OBSERVATION保存・同一本文の再取得を確認した。公開合成2例も同じ経路で確認し、親が3件の本文全文を読んだ。本人原本・本文・ID・digestは公開しない。

これは隔離PGlite上の実SQLと、実reply/service/API GET経路の確認である。認証主体だけをテスト用に差し替えたHTTP GETで、稼働Supabase/PostgREST、実Bearer、実submitのネットワーク待機、RN端末描画を検証したとはしない。本文の存在・保存一致は確認できたが、実出力には原文再掲・定型的な受け取りが残り、商品品質合格には換算しない。

### 次の配置・実機確認

1. 今回の3ファイルを含むAPI修正commitを指定し、既存[Render mashos-api](https://dashboard.render.com/web/srv-d4ppfpm3jp1c73952bj0)の **Manual Deploy → Deploy a specific commit** で配置する。正確な候補SHAは今回のGitHub反映後の案内を使う。本人の開始操作希望と、Render接続のcommit指定deploy非対応を継承し、汎用deployでmainを配置しない。
2. DB migrationと環境変数の再保存は不要。確認済み10秒budgetを維持する。今回のGitHub反映だけでは、live `468663c8effc51c1bc33f165313eeb9417d16dc9` は切り替わらない。
3. 配置後に華恋がlive commit・health・ログを確認し、その後、6301の本人通常入力1件で入力直後の応答→閉じる→履歴から同じ本文を確認する。今回のAPI修正の確認にnative再buildを追加条件としない。実環境の待機時間・本人権限・描画はこの工程で確定する。
4. 10/07に観測が作られなかった記録は、履歴GETだけでは生成されない。過去行の書換え・自動backfill・架空の本人記録は追加しない。10/06の履歴未作成説明修正は別の未配布RN差分として保持する。

今回の稼働DB/環境変数変更、deploy、native build、mergeは0。修正・隔離検証・GitHub反映と、未実施の実機復旧を区別する。追加の個人情報・キー・ログ提出は現時点で不要。

## 35. 2026-10-10 JST — NULL修正版の配置完了、本人実機確認へ

Mashの「開始した」報告後、指定API `7626e1f6e6cc7b2d8a71b9ea1032b840bbc9799b` のmanual deploy `dep-db4vkrid0e5s73dlrl40` を読取照合した。開始は17:42:22 JST、**17:43:46 JSTにlive**。17:43:42にはApplication startup completeとUvicorn待受を確認した。linked main・autoDeploy OFFは維持され、今回の修正版commitが稼働している。

17:44:09 JSTの実HTTP確認は、`GET /healthz` が200/status=ok、`GET /app/bootstrap` が200かつ `emlis_threads_enabled=true`、未認証thread GETが401。個人入力IDやBearerは使用していない。17:42:22〜17:44:15のappログ取得はhasMore=falseで、起動を阻害する例外・ERRORなし。既存の利用規約/プライバシーURL未設定warningは残るが、今回のEmlis修正による起動停止ではない。華恋からdeploy再起動・環境変数・DB変更は行っていない。

次は本人の6301で、通常の新しい入力を1件送信し、直後のEmlis本文表示→閉じる→履歴から同じ入力を開いた際の同一本文表示を確認する。本文が出なければ発生時刻と画面上の状態を受け、当該処理のログ/保存状態を照合する。10/07の未作成観測をGETだけで回復させる変更はなく、過去入力を確認対象の代わりにしない。

今回成立したのは指定版live・公開HTTP・未認証拒否・起動の確認まで。本人入力の生成/保存、実Bearer、端末描画の成功はまだ未確認。native build、SQL/設定変更、商品品質受入れ、mergeは今回実施していない。既存文書への結果反映だけで、`STRUCTURE_MAP_DELTA_NONE`。

## 36. 2026-10-10 JST — 本人実機で本文表示を確認、内容品質は不合格

17:52 JST、Mashから「内容に関しては品質的に論外ではあるけど、表示はされた」と報告を受けた。添付画面も華恋が直接確認し、Emlisの観測modal内に現在の観測本文とEmlisからの本文が描画されていることを確認した。今回の成立事実は **本人実機で応答本文が表示されたこと**。内容品質の本人評価は **不合格** として分けて保持する。

表示到達を商品完成・内容品質合格・任意入力での安定稼働へ換算しない。履歴から同じ本文を再表示できたとの明示報告は今回なく、保存内容の独立DB照合・再起動後の再表示もこの報告だけで完了にしない。§35の「端末描画未確認」はこの表示1件について更新されたが、未確認の保存往復までは閉じない。

今回は本人報告と添付画面の確認、および既存資料への記録だけ。個人の入力/出力本文・画像・IDは公開資料へ転記せず、追加DB/ログ取得、製品修正、検査再実行、deploy/env変更、native build、mergeは行っていない。`STRUCTURE_MAP_DELTA_NONE`。

## 37. 2026-10-10 JST — 分析取得エラーの原因修正（未配置）

今回の依頼は、通常の感情入力後に分析内容が出ず `analysis_observed_map_unavailable` となる問題の修正。全体構造・全ファイル地図、Analysis current mapと詳細設計、最新weekly 20261010 §5.5、必読事故記録と作業規則を確認した。今の優先は実入力による分析生成・保存再表示への到達であり、一般文法の網羅や表示磨き込みを配置の追加条件にしない。

### 原因と変更範囲

17:52:52 JSTのRender固定診断は `stage=current reason=analysis_observed_route_not_established`。保存入力の取得RPCは200、current graphの要素0件で停止しており、前期間比較の失敗ではない。今回の28日内の本人記録3件を非公開で読取照合したところ、既存compilerの限定文法と明示主語条件で採用できる要素がなかった。稼働APIは§35の `7626e1f6e6cc7b2d8a71b9ea1032b840bbc9799b`。直前のEmlis NULL修正とは別の原因である。

既存 `cores/analysis/intent_compiler.py` と `observed_route_realizer.py` を修正。原入力の行動欄全体が、既存の限定名詞＋「で」＋2〜3仮名の反復表現＋「した／しました」の一節として閉じ、共有の明示action/past/performed witnessを持つ場合に採用する。省略主体はUNSPECIFIEDとし「主体の記載なし」を表示する。原文の全文範囲と出典を保持し、本人・原因・順序を補わない。未解釈のmemoや不足段階はunknownのまま残す。

独立レビューで見つけた後続の否定・仮定・伝聞の切落しと、今日/昨日を名詞に吸収する誤読も修正した。行動欄全体との一致を要求するため、前後に別節や未解析hostがある入力はこの追加分岐で採用しない。原文そのままの無検査表示、空graphの成功扱い、旧mapへのfallbackは追加していない。

新file・API・DTO・共有意味owner・DB schema・SQL・RN・依存定義の変更なし。`STRUCTURE_MAP_DELTA_NONE`。対応設計はCocolon `current_structure/03_analysis_current_structure.md` と `designs/cmee/v1/04_analysis_v1d_v1e_detailed_design.md` §3.20。

### 検証結果

- 新規API回帰を修正前 `631c5843396adaadbcac2a1212e38b18a538e148` へ置いた隔離worktreeで、実FastAPI→service→CMEEが同じ422となることを確認。修正後は200で部分mapを生成し、保存後のGETで作者を呼ばず本文・projection・versionが一致した。AuthとRPCだけが合成で、実環境のBearer/通信ではない。
- 最終sourceのAnalysis vertical・storage・saved period・APIの4集合は **389 PASS**。既存Pydantic root_validator非推奨warningが1件。追加は文法/根拠/未知部分/否定等の保留/SELF改変拒否/丁寧形比較の4検査と、生成→保存→再取得のAPI1検査。比較off/development両方、NULL/空欄を含む合成3件を確認した。
- 既存の実SQL harnessへ公開合成の新文法fixtureを渡し、隔離PGliteで **58 checks PASS**。実migration/RPCの保存・再読、本人権限・tier・入力変更失効・比較を確認した。稼働Supabaseへの書込ではない。
- 本人の今回の3件を含む読取snapshotでも、最終sourceの実service/CMEEで **Free/lightの1要素の部分map** が生成され、合成RPCへの保存後、再生成なしで同一本文を取得できた。原snapshotは不変。全文を読み、実RN表示modelが同じtext/projectionを受け取ることも確認した。入力/出力本文・ID・private evidenceはGitHubへ掲載しない。
- 親の差分確認と別agentの独立レビューを実施し、指摘2点を修正後、今回の表示回復を阻む問題は残っていない。全日本語対応・全内容の分析・商品品質合格を意味しない。

検査runtimeはCPython 3.12.14/pytest 8.4.1/httpx 0.28.1/FastAPI 0.143.0/Pydantic 2.14.0、PGlite 0.5.8をこの作業でimport確認して使用した。新規依存導入なし。旧Gateの再開や、無関係なEmlis既知FAILの修正は今回の範囲に追加していない。

### 次の指定commit配置と実機確認

1. 今回の修正commitをGitHubへ反映・照合した後、案内するexact SHAを[既存Render mashos-api](https://dashboard.render.com/web/srv-d4ppfpm3jp1c73952bj0)の **Manual Deploy → Deploy a specific commit** に指定する。本人の開始操作希望とRender接続のcommit指定deploy非対応を継承し、linked mainを配置する汎用deployは使用しない。
2. 今回のためのDB migration・環境変数変更・native再buildは不要。GitHubへの反映だけでは稼働版は切り替わらない。
3. 開始報告後、華恋が配置SHA/live・health・固定ログを確認する。その後、既存アプリを開き直し **分析 → わたしマップ** を表示し、閉じて再表示する。Analysisのlatest ensure経路が既存入力から生成するため、今回の確認のために新しい感情入力を追加する必要はない。
4. 端末表示と保存後の再表示が成功した時点で、今回の取得エラーの実機復旧を確認する。現在成立しているのは修正・隔離検証までで、修正版の実機描画・稼働DBへの保存は未確認。部分mapの表示回復と内容品質の受入れを分ける。

今回の稼働DB/環境変数変更、deploy、native build、mergeは0。次は指定commit配置であり、同じ入力の再提出・キー・追加の個人情報は不要。
