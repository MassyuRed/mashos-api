# Emlis 本人宛の通常応答 — 2026-10-31

## 範囲と現在地

Mashが承認した通常入力→自然な返答→保存→非生成の再読のsource準備。Q3の既存SQL・公開DTOを再利用し、private `natural_reply.v1`だけを追加した。新profileは初回本人宛本文のみ。観測用5段packet、意味checkpoint、3種類の可視本文を必須にしない。分析材料は`NOT_GENERATED`であり、返答を本人の事実へ逆流させない。

10/31後続で固定4Bの実18生成と、実本文2件の隔離SQL保存・別service instance再読を確認した（末尾の実測記録）。本番HTTP・配置・新RN配布・本人端末は未実施。Free/Plusの実4B品質、Plus全蓄積からの関連履歴検索、新profileの任意問い・補足・frame訂正の反映、分析材料の生成・採用は未完成。既存本人履歴3/6件の原文受渡しの検査は、その完成とは別。過去記録にも既存Safety ownerを適用し、別Safety/自己否定の記録は通常返信の材料から除外する。過去の危機を今回の状態として扱わない。

## 接続

`emotion submit`で原入力が保存された後、`emlis_ai_reply_service`が共有`emlis_thread_factory`を使う。新profileの場合、admissionから同一の強参照taskで実行し、submit外側3秒による取消から分離する。公開metaの既存`rejection_reasons`にある`thread_reply_pending`は、書込可・provider構成有効の時だけ返す。既存サニタイザを通過することを検査済み。

`EmlisThreadService`はsource/Safetyを確認し、HTTP前のSTARTED、受信した本文のRECEIVED、最終OBSERVATIONをSQL CASで保存する。同sourceへの再取得を禁止。受信保存のACK不明は同attempt/source/context/本文のfresh readが成立した場合だけ回収し、新HTTPを起こさない。最終保存の明確なrollbackは、期限内の明示retryで保存済receiptを使う。結果不明・timeout・取消から自動再生成しない。

thread attemptとnatural処理全体は既存30秒期限。HTTPは最大25秒、GPU提供口にも23秒の単調時計StoppingCriteriaを置く。DBは期限後commitを拒否する。期限内完了・10秒応答の実測成功を意味しない。

非緊急自己否定と別Safety対応を通常providerへ送らない。新profileの専用応答は未接続で、成功した普通の返事へ置換しない。検査で見つかった「自分なんていないほうがいい。」の既存判定漏れは、明示文末形だけ既存self-denial matcherへ補足。明示否定・場所の文を誤昇格しない検査を追加した。

RNは既存DTOの`current_observation.text`を無加工表示する。通常submitのpending時だけ未作成待機を許し、表示中・foreground・同owner/attempt・処理中だけGETする。35秒は新しい自動GETを始める期間の上限で、既存GETの通信期限とは別。失敗・閉じる・owner変更では停止し、共有POST controllerをpollからabortしない。履歴の未作成を新しい生成待ちと扱わない。

## 明示的な構成

既存`COCOLON_EMLIS_THREAD_MODE`とrelease/read/write条件を維持する。その上で、サーバ側にのみ次を設定する。

- `EMLIS_AI_RESPONSE_PROFILE=natural_reply.v1`
- `EMLIS_NATURAL_REPLY_ENDPOINT`：自己hostのHTTPS `/v1/chat/completions`
- `EMLIS_NATURAL_REPLY_MODEL`：提供口の明示model名と完全一致
- `EMLIS_NATURAL_REPLY_API_KEY`：提供口と共有する秘密値。GitHub・端末へ保存しない

provider設定欠落中も保存済本文のGETは可能、新profileの書込は不可。旧threadの保存profile・旧本文・既存問い回答を変更しない。別providerへのfallbackなし。新しい依存・SQL/migration・料金/quota変更なし。

## GPU停止中に準備した提供口

`ai/tools/serve_emlis_natural_reply.py`は既存local cacheだけを使う本人限定probe。Qwen/Qwen3.5-4Bの固定revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`、既存transformers5.19.0/peft0.21.2/accelerate1.15.0/safetensors0.8.0。`HF_HUB_OFFLINE=TRANSFORMERS_OFFLINE=1`を要求し、学習・downloadをしない。CPU検証ではモデルを読み込んでいない。

baseと比べる保存候補はfit38のad8b：weights SHA256 `ad8b89e8974df9bfe7e804b8f67bbaac59e6cbb37042c3254fb58ffb64230d0a`、config SHA256 `ef4b1aef621fb4e234ce6a05601efb62a987c3cf5d40f3995ca1b72200bab145`。直近focus29の初期値として回収済みであり、新ed298856を自動採用しないためこの一つに限定する。品質優位を認定した選択ではない。56対象・112 tensor/3,833,856 paramsの保存/読込一致、非学習を起動時に確認する。後続実測で、このloaderのGPU読込・56対象/112 tensor/3,833,856 params一致・非学習を確認した。

HTTPは認証、同時1件、読込前からのSIGALRMによるprocess hard上限・明示回数上限、context8192/max_new2048、nonthinking、非sampling、EOS完了を条件にする。23秒StoppingCriteriaはtoken境界の判定で、一つのforwardの途中を止める保証ではない。process hard上限とは区別する。期限終了/打切りは成功本文にしない。提供口自身はGPUを停止・再起動・削除せず、常時host契約を決めない。モデル読込には既存学習loaderの固定情報を使用し、後続でloader/direct生成は成立したが、HTTP経由の実GPU疎通は別途必要。

以下は後続実測前の案（実結果と変更は末尾）：追加学習0、baseと保存fit38一つで8入力×2=最大16生成、採用候補の通常接続・保存再読を最大2生成、合計最大18。旧5種類は型を参照し、正解例文への一致を要求せず、未使用3入力を混ぜる。8入力の原文は実行前に固定し、固定応答集や学習教師へ採用しない。GPUの現在単価・接続・実行条件を確認し、準備/読込/保持/回収込みの時間・費用を具体化してから起動する。旧runの承認は再利用しない。

## 検証

- APIの新profile23件、既存Q2/Q3 application54件、既存Safety9件＝重複なし86成功。内訳のうち81件を同一実行、履歴3tier/途中pauseの追加4件と未接続frameを黙って落とさない1件を別実行。実Q3 SQL/RPCは隔離PGlite、provider/HTTP/Authは合成を含む。
- 提供口の実local HTTP 1件成功：認証拒否・不正model拒否・一回生成・回数上限拒否を同じ検査で確認。さらに読込処理を模した子processのhard deadline終了1件成功。GPUは0。
- RN現行34件は29成功/5失敗、変更前31件も26成功/同じ5失敗。新規3件と今回の関連5件は8/8成功。残る5件は旧Piece呼出し文字列期待1、AppRuntimeのreact-native mock欠落3、metro実行依存未用意1。未成功を全suite成功へ変換しない。
- 81件実行以前の2失敗は、自己否定の判定漏れとfactoryの旧DI互換漏れ。修復後の対象19件成功、さらに上記81件/追加4件で確認。pytest初期の素材不足（巨大sourceのcontents空、plugin/fixture不足）は原本取得を補い、製品修正の成功件数に数えない。
- 独立した読取レビューでSTARTED/ACK回収/owner/旧profile/待機表示を点検・修復。実4B本文品質・実機・正式商品受入れの判定ではない。

稼働読取：既存Render serviceはautoDeploy OFF・linked main、Piece private factoryのstartCommandを維持。Supabaseの既存thread/event列をread-only確認。今回のGPU・課金・重み変更・DB書込・配置・build・配布・main mergeは0。正式0/3・54.50％を再採点しない。


## 2026-10-31 後続実測 — 実18生成と隔離SQL保存再読

Mashの新Pod利用・Googleログインからの作業継続指示で、Pod `10o4zhfktg9nc1`/RTX PRO4000 Blackwell24GBへ直接Jupyter接続。空の新Podへ既存固定4依存・公式固定base revision・回収済fit38/ad8bを復元した。Torch2.8.0+cu128/SM120/BF16、既存loader/adapter56対象・112 tensor一致を実測。復元は学習ではなく、重み更新0。固定済み8入力×base/fit38の16生成は全EOS、約0.825〜3.427秒/生成だった。読込・通信・SQLを含む通常30秒の成立ではない。

全16本文をrootと独立read-only監査で読んだ。baseには否定を未完了へ変える本文と本人原文の全文貼返し、fit38には相手の発言を相手の感情へ変える本文と本人の一人称へなり替わる本文があり、両候補とも全体の最低線未達。短い自然な受取りは浅さだけでは不合格にしていない。未記載の可能性補完と、未確定を断定する違反も区別した。

残2生成は、元予定の新入力NR09/10をNOT_RUNとして、共通指示の最小修正後のfit38 NR02/07へ振替え。修正NR02は友人の感情追加が残存。NR07は本人への主語を修復したが、Emlisの「私」使用と不自然な自己感情報告が残った。2件を品質合格にせず、実験指示の製品source採用を取り消し、`natural_reply.py`はbea4ed1fと同一本文へ復帰。元16・修正2・両指示/sourceは非公開原本へ保持した。

元16件のうち妥当なfit38 NR01/08の実本文を使い、原材料JSON全文一致後に既存service/Q3実SQLへmanual bridgeで保存。保存2件、同Python process内の別service instanceでGET4回、既存start2回の同一本文/event・source各1回・OBSERVATION各1・分析NOT_GENERATEDを確認した。GPU時とSQL時のsource prefixは別で、新prefixへ束縛した手動artifact受渡し。追加生成・本番HTTP・API/DB process再起動・実Auth/本番Supabase/RN/本人端末成功ではない。実際に呼ぶHTTP sourceと30秒の端から端の確認は残る。

関連23検証成功（3.54秒/既存warning1）。今回の実測はTECHNICAL_CREDITで、商品採用・正式0/3・54.50％は変えない。共通1500秒枠のsetup前〜終了確認1142.077秒、当該窓の$0.58/h按分約$0.1840。レンタル開始からの総請求額・終了後保持等は未測定。終了後probe processなし/GPU2MiB・0％/ad8bとconfig不変。GPU Stop/restart/delete0、Render/本番DB/RN/main/配置/配布変更0。

非公開原本：`cocolon-natural-reply-actual-20261031.zip`、Library `libfile_0831a417bae0819196da4401cef8fd70`、SHA256 `121d0145b3ad46a09a709469a3e9dc3abde465386e8badeb2005b152c9d49fa7`、60member。raw/messages/元・修正source/予算/実環境/全失敗/SQL再読/終了確認を保持。正解文への一致や追加学習は使用していない。

今回18回の実行は閉鎖し、自動再開しない。次は追加学習に戻らず、学習前4Bへ主体・感情所有とEmlis一人称を保つ最小案を具体化する。修正後8件合格・通常接続・本人端末の完成に換算しない。STRUCTURE_MAP_DELTA_NONE（製品sourceと責務の追加変更なし）。


<a id="natural-base-followup-20261031"></a>
## 2026-10-31 後続2： 学習前4Bの指示/対話/生成条件比較 — 新18生成、通常採用未達

Mashの「作業を進めて」を受け、§17の18生成を再開せず新しい実行を同Jupyterで行った。重み再転送・追加学習なし。全体現在地/作業規則/必読incident/全体設計・file地図/最新weeklyと実sourceを確認し、rootが実行、補助agentはread-only監査を担当した。

### 2026-10-31 後続2：1 条件の変更と結果

| 範囲 | 条件・結果 |
|---|---|
| 最初の8 | 同じbase/8原材料で、前回fit38に試した共通指示と否定/全文貼返しの一文を使用。全EOSだが相手感情追加・本人一人称・全文コピー・要約調が残る |
| 残2 | 当初のHTTP保存NR09/10から、本人が今話しかけている対話場面の指示を使うNR02/07へ振替え。対話口調には変わったが、未記載の心理・関係の保証/助言、Emlisの目撃者化と姉という立場の追加が残り不採用。NR09/10はNOT_RUN |
| 別条件の8追加 | 固定revisionの公式cardを確認し、元product指示/同じ原材料/baseのまま、nonthinking一般用途のsampling値を参照した一組で比較。seed42を各case開始前に固定し一回ずつ。全EOSだが友人の感情追加・存在しない約束・Emlis目撃者/表情創作・理由不明から原因候補/問い・全文コピーが残った |

最後の8追加は華恋が新しい設定差の確認として事前に説明した変更であり、Mashが個別に18という回数を指定した記録にはしない。当初10件のcounter/sourceを残して別counter/sourceで8件、計18件。共通900秒のdeadlineを延ばさず、§17の旧18・既知失敗も変更しない。成功seedの選別、同条件の自動retry、応答の書換え0。18件を全件読んだが商品最低線未達、実験source/prompt/設定を製品採用しない。

### 2026-10-31 後続2：2 公式資料と、実装上の限界

固定revisionの[公式README](https://huggingface.co/Qwen/Qwen3.5-4B/raw/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a/README.md) L1075〜1079はnonthinking一般用途にtemperature0.7/top_p0.8/top_k20/min_p0/presence1.5/repetition1.0を示す。従来のgreedyとの差を比較した。公式推奨であることを失敗原因の証明へ変換しない。

HF5.19にpresenceの標準field/classがなく、生成済tokenだけへ各1回−1.5とする一回限りの同等処理を使用。prompt除外/頻度加算なしの数値assertと独立read-onlyコード監査を実施。max_new2048/23秒は既存の独自上限で、card全条件再現ではない。seed42は選別防止用で、異環境完全再現保証ではない。コピーした実験handlerはtemperature0要求を残すため、今回のsampling generatorとHTTP契約が一致せず、そのまま通常HTTPへ採用できない。今回はdirect呼出しのみ。

### 2026-10-31 後続2：3 保存接続・時間・終了状態

実GPU HTTP→既存service/Q3 SQLのloopback TLS案とsource packはCPU準備のみ。GPUにNode/npmはなく、導入/配置/実HTTPは0。新規の生成/保存2件は未実施で、§17の手動artifact2件を今回のHTTP成功へ数えない。本番Auth/Supabase/RN/本人端末・API/DB process再起動も未実施。製品source/公開DTO/DB/期限/料金/quota/Render/main/配布の差分0。

計測した実行窓の終了確認は775.928秒、元deadline900秒内、表示$0.58/h按分約$0.1250。これに先行する前提確認/CPU準備/転送や終了後の文書整理は含まれず、当初説明した「準備・回収込み15分」を全工程で達成したとは主張しない。レンタル全体/間の待機/終了後保持等の総時間・総請求額は未測定。probe processなし/GPU2MiB・0％/fit38 ad8bとconfig不変。学習/重み更新/Stop/restart/delete0で稼働保持。

### 2026-10-31 後続2：4 次の一手と非公開原本

次は直接学習より先に、**元の指示・原材料・base・sampling・seed42を固定し、提示形式だけ変える比較**を行う案。本人原文を日本語の発話本文として先頭に置き、感情・強度・日時・過去記録は明示した補助情報として全て保持する。JSONが要約対象として読まれる仮説は未検証で、原因/解決と断定しない。8件の全値保持・元JSONへの対応をCPU確認したが、新GPUは未実行。正解文/固定応答や新しい採否checkerは増やさない。

原本`cocolon-natural-base-followup-20261031.zip`（Library libfile_cb5fcb1bf880819187aef6fff6e12c24、61member、SHA25677d8f7bfd3512be53f164b84a55a952119404724ccab472f565ab662e816aa1b）へ全18本文/messages、元10/追加8の変更、実source/数値assert/予算/終了、未実行HTTP案・次の全値保持案を保存。個別本文は公開GitHubへ出さない。

primaryはBLOCKER_NARROWED。通常応答の品質改善や正式受入れとして加算せず、商品0/正式0/3/54.50％・STRUCTURE_MAP_DELTA_NONEを維持。今回の実行は終了し、生成枠・時間・旧counterを遡及変更しない。


<a id="natural-utterance-http-20261031"></a>
## 2026-10-31 後続3： 本人発話提示の比較と実HTTPS→SQL保存再読 — 比較8未達・接続2成立

§18の次案を、別の10生成/900秒枠で実行した。原product SYSTEM、固定base revision、原材料、sampling一組、各call seed42を保持し、user contentの提示形式だけ変更。material_json内のmemo/memo_actionを原文のまま先頭、残るcurrent値とpast_user_recordsを付帯情報として全値保持した。既存材料に元からないcategory等まで保持したとは主張しない。

8比較は全EOS・約1.002〜2.088秒だが、全体の最低線は未達。NR03の明示的に否定された約束の事実化、NR01/06の日本語の崩れ、NR02の助詞/時点表現、NR08の期待から経験へのずれと気分による因果補完が残った。一方NR02での友人感情追加、NR07の本人/Emlisなり替わり、NR08の全文貼返しは今回消えており、部分変化を無かったことにしない。NR04の怒りの疑念は原入力にもあり、創作/断定違反とは数えない。短い受取りや一度の言換えを理由に不合格へ戻さない。JSON提示だけが原因/解決との仮説は確定せず、候補の製品採用なし。

### 後続3：1 実モデル通信から保存・同一本文再読

品質未達を記録後、残2枠は技術接続だけの判定としてNR09/10を実行した。以前の手動artifact注入を使わず、既存render_emlis_ai_replyのpending scheduling/thread GETから実HTTPSで4Bを各1回呼び、同一source prefixの本文を実Q3 migration/RPC SQLへ保存した。保存完了GETまで2.106秒/2.862秒、生成は1.738秒/2.468秒。両本文は自然な受取り候補で、大きな意味反転は見つからなかったが、2件から一般品質合格へ広げない。

同Python process内の別FastAPI app/service instanceでGET各2回、既存start各1回、同一本文/event・source各1回・OBSERVATION各1・分析NOT_GENERATEDを確認。生成末尾改行は既存sourceのstripで除かれ、保存以後の本文は一致する。入力rowはsynthetic insert、Authとfactoryはfixtureへ置換。実emotion/submit全体、本番factory、Supabase Auth、Render、RN、本人端末、API/DB process再起動は未確認。通常商品を動かしたとの成功にはしない。

TLSはlocalhost SANの証明書を明示CAとして検証し、127.0.0.1だけにbind、Bearerはmemory内のみ。鍵/認証値は原本束から除外、Jupyter token転用と公開port拡張0。sampling要求とgeneratorを一致させ、正規sourceへの候補hash一致を開始前、実HTTPuser文とformatter一致を終了時assertした。Python依存をPyPI、Node v24.22.2を公式配布/SHASUMS確認、PGlite0.5.8をnpm ignore-scriptsで隔離導入した。製品sourceの採用変更は0。

### 後続3：2 時間・原本・現在の残件

CPU準備前に900秒deadlineを置き、終了確認316.855秒/10生成、同条件retry/追加学習0で閉じた。当該窓の表示$0.58/h按分は約$0.05105。レンタル全体、待機、記録整理、終了後保持の総請求額は未測定。probe processなし/GPU2MiB・0％/fit38 ad8bとconfig不変、GPU Stop/restart/delete0でPodを保持。ローカルpack作成失敗と終了archive importのpath不足は修復し、GPU再生成にはしていない。

非公開原本は[cocolon-natural-utterance-http-20261031.zip](https://chatgpt.com/library?file_id=libfile_a58ec87554088191a7469d98948187d5&account_id=personal)、42member、2,457,542bytes、SHA256 a496aaf223e9a5f2e7ea810b0ca1efc3d4ae7dbedad05092ed1359744f172ae6。全10本文/messages、実source pack247file/manifest、候補/runner/helper、実HTTP/SQL/DTO、時間/終了確認を保持し、個別本文は公開GitHubへ載せない。

今回減った残件は隔離環境の実HTTPS保存再読で、primary TECHNICAL_CREDIT。一般品質と本人端末は残り、正式0/3・54.50％・PRODUCT_NOT_CLEARを維持。次は失敗した主体/否定/時点の保持と自然な本人宛返答を、従来の複雑な意味JSON教材から切り分け、未使用評価を別に置く最小教材案を具体化する提案。追加生成/学習は開始しておらず、旧counter/失敗を変更しない。通常API配置/RN配布/本人端末の完成にも換算しない。製品owner/公開DTO/DB/RN/期限/料金/quotaの変更なし、STRUCTURE_MAP_DELTA_NONE。


<a id="natural-quality-followup-20261031"></a>
## 2026-10-31 後続4： 再開後の返答品質比較 — 新13生成、未使用2件保存、一般品質は未達

Mashの「処理落ちしているから、続きから再開して」で、§19の原本とfresh PR30/API PR3を再確認した。§19は完了済みとして保持し、rootが実行・書込、補助agentはread-only点検。全体現在地/全体設計・file地図/最新weekly/必読incident/実sourceから通常返答の修復を進めた。

| 条件 | 実際の結果 |
|---|---|
| D：架空の別人の会話例3組だけ追加 | Cと同じbase/SYSTEM/原材料/提示形式/sampling/各call seed42で既知8＋未使用NR11/12、計10生成。全EOS。日本語・不明保持の部分改善があるが、否定された約束の事実化、本人感情の追加、語法の不自然さ等で全体最低線未達。例の人物/出来事の混入は見つからず、候補不採用 |
| D：未使用2件の実HTTPS保存 | NR11/12を実モデルで各1回生成し、既存reply入口/Q3 SQLへ保存。約1.591秒/2.258秒で保存完了GET、同process別app/service GET4回/start2回で同一本文/event、追加生成なし。両本文は最低線候補。本番Auth/通常emotion submit/RN/本人端末の成功ではない |
| E：thinkingのみTrue | 会話例なしのC条件からmodeのみ変更。最大10の最初の1件が23.002秒で最終返答を得られず停止、残9はNOT_RUN。失敗raw保存漏れがあり、marker/内部出力の詳細原因は再構成しない |
| F：検討256token後の終了marker制約 | 初回は14.322秒/EOSで返答を出したが、連続2終了markerを受口が拒否。元raw/hash/失敗を保持し、強制時・間は空白のみ・再開なし・EOS限定のmechanical parser修復を1回実施。9つのCPU境界確認後、初回rawをID/messages一致で再解析し、再生成0。元deadline/budget bytesと全体count1を継承した限定継続はNR02が23.012秒/460token/finish lengthで失敗、検討が続き最終返答は未完成。2度目の失敗で停止、全体2生成・残8はNOT_RUN。新NR13/14も未実行 |

新actual生成はD10＋E1＋F2＝13。F初回の再解析を生成へ加算せず、未完了の検討文を本人本文へ渡さない。通常30秒/生成23秒/max2048を延ばさず、本文の語句/文数は固定しない。E/F/修復案は製品不採用。F childのreasoning_tokensは最後のclose位置で、正確な検討数は最初のclose位置から読む。Dの例3は頻度差が曖昧、payloadのmax18/旧run名は継承された宣言不備で、実budget/counterは10。元bytesを遡及修正せずsidecarへ記録した。

### 後続4：1 終了状態・原本・次の対象

計測窓はD285.317秒、E178.141秒、F修復込み498.988秒で各900秒内。前回表示$0.58/hによる窓按分の合計は約$0.1551。先行確認、窓間、記録整理、保持等を含むレンタル全体の請求額は不明。最新終了確認で生成processなし/GPU2MiB・0％/fit38 ad8bとconfig不変。追加学習/重み更新/GPU Stop/restart/delete0でPod保持。本番DB/Render/RN/配布/main/料金/quota/製品source変更0、STRUCTURE_MAP_DELTA_NONE。商品受入れ0/3と54.50％は維持。

次は通常返答だけを対象にする**架空の教材候補12件とモデル未使用評価2件**をCPU準備。root華恋案でありMash実演/品質承認/訓練済ではない。主体/否定/時点/発言と感情の所有/理由不明を扱い、旧19教材/観測会/凍結評価は不変。評価2にassistant正解文を置かず、原材料を変えず現productのraw JSON提示へそろえた。教師の3つの語法/時点/否定をread-only点検後に最小修正。学習runner/mask/EOS/実token長/更新数/費用時間の固定はまだ必要で、追加学習の実行可能・効果・一般品質成功にはしない。

全実結果・source pack・修復前後・失敗・終了・教材案は[cocolon-natural-reply-quality-followup-20261031.zip](https://chatgpt.com/library?file_id=libfile_6c7af4d2a68881919b3bd4fe8b63e561&account_id=personal)、version1、110member、7,335,671bytes、SHA256432fb4c1fd2fdcedb80285a9145f04e9ba22c8177be72e6280d87b1b77f57f20。個別本文は公開GitHubへ載せない。完成条件は引き続き、一般入力へ自然な返答→通常接続→同本文保存再読→本人端末での一巡であり、今回の部分結果を完成へ換算しない。


<a id="recipient-fit24-20261031"></a>
## 2026-10-31 後続5：通常返答12教師・24更新 — 保存重み再読込と10返答、全体品質は未達

Mashの「作業を進めて」に従い、§20で準備した華恋の架空12教材を、固定Qwen3.5-4Bから作る別LoRAへ各2回、計24更新した。rootが全実行・書込を担当し、補助agentはread-only点検。全体現在地を全文、全体設計・全file地図・最新weekly・観測学習の目的・必読incident・実sourceをfresh確認した。旧fit38を初期値に使わず、通常返答だけを切り分けた。教材はMashの完成実演・品質承認済み教師ではない。旧19教材、観測会、凍結評価は変更しない。

### 後続5：1 実際の学習と保存

| 項目 | 確認事実 |
|---|---|
| 入力・loss | 現productのraw JSON/SYSTEM/非thinking/greedyを維持。既存run_pilot.pyのprefix一致・assistant-only mask・終端・teacher_loss方式を確認し使用。promptは-100、assistant正文＋単一im_end/改行だけ監督。最大train397token、切詰め0 |
| 実更新 | seed42の固定shuffle 2epoch、12行×2＝24 training forward/optimizer。AdamW lr5e-5/weight_decay0/clip1。前後各12のNLL測定forwardは別カウント |
| LoRA | r8/alpha16/dropout0。8full-attention層のq/k/v/o＋MLP gate/up/down、56module・112tensor・3,833,856param。112全tensorが変化、有限F32 |
| 教師適合 | 12行の単純平均NLL 2.026144→1.198713、全12行低下。一般入力の品質合格には換算しない |
| 保存再読 | 別directoryへ保存後にmodel/optimizerを解放し、新しい固定base objectへ非学習reload。全keys/shape/valueが保存112tensorと完全一致、eval/全requires_gradFalse |
| Pod外保全 | 受領safetensorsのSHA一致、112tensor/3,833,856値のF32・有限性を別途確認。旧fit38/ad8bとconfigは実行前後不変 |

新adapterのweights SHA256は `af44fdf40ada403d04b3b5ba1f14b6257b967f679549f1042dbee635ea707ae1`、configは `6568e73e87e56543afbc6b85a81c08b0a816767c353fab2accda10e5d4c5f817`。peak allocated9,418,122,752bytes/reserved9,506,390,016bytes。移行には固定base全重み/tokenizerも必要で、adapterだけの単独完全モデルではない。optimizer/RNGの途中状態は保存せず、学習途中の厳密再開には使えない。

### 後続5：2 全10返答の読了結果

保存版で既知8＋開始時にモデル未使用だったNR13/14を計10生成し、全EOS、約0.548〜2.074秒。既知8は§17のbase比較とmessages/material全文一致、NR13/14は教師から独立しassistant正解文を置かなかった。NR13/14は今回で使用済みとなり、今後の未使用評価へ戻さない。

NR01の文法、NR02の未記載原因・感情補完、NR08の期待から経験への変換は旧base比で改善した。一方、NR03/04は原文全文の再掲、NR13は本人の内語をassistantが語り直し、本人宛返答として未達。NR03の否定文字列保持を意味理解の改善証明には数えない。これら3件を主根拠として**全体最低線は未達、製品採用0**。NR06の語尾反復、NR07の本人の安心への受取りの狭さ、NR14の事務的な温度感は改善余地として分ける。短い受取り・一度の言換えや「承知しました」単独を、新たな不合格条件にはしない。

### 後続5：3 実HTTPS→隔離SQL→同一本文再読

NR13/14は保存adapterを各1回、実HTTPSで呼び、既存render_emlis_ai_replyのpending/thread GETから実Q3 migration/RPC SQLへ保存。保存完了GETまで約2.097秒/2.341秒。source receipt・保存DTO・同Python processの別FastAPI app/service instanceによるGET4回・既存start2回は同一本文/eventで、追加生成なし。source各1回/OBSERVATION各1/分析NOT_GENERATED。手動artifact注入は使わなかった。

入力row/Auth/factoryはfixture。実emotion submit全体、本番factory/Auth/Supabase/Render/API配置/RN配布/本人端末、API/DB process再起動は未確認。TLSはlocalhost SAN/明示CA検証、127.0.0.1だけ、Bearerはmemory内のみ。Jupyter token転用・公開port拡張0。前回の隔離Node/PGlite/Python環境を再利用し、新依存導入0。

### 後続5：4 時間・終了・原本・次の修正対象

CPU準備前からの1200秒枠に対し終了確認419.448秒、一回実行で追加更新/再試行なし。最後に表示された$0.58/hによる当該窓だけの按分は約$0.06758。レンタル全体・待機・記録整理・終了後保持の総時間/総請求額は不明。終了時probe processなし/GPU2MiB・0％。GPU Stop/restart/delete0でPod稼働保持。

全source/固定plan/教師/評価/実encoded-mask/24更新順/loss/前後NLL/新adapterとconfig/全10本文・tokenIDs/HTTP-SQL-DTO/終了/Pod外検証を[cocolon-recipient-fit24-20261031.zip](https://chatgpt.com/library?file_id=libfile_9d7d7721f05081919b7e6edd5905f915&account_id=personal) version2へ保全。50member、16,674,663bytes、SHA256 `fccfdb708573a03ca7edc892c3fd02c898b4c9d10496e6b94ca30e0d2c0bf6ee`。個別本文は公開GitHubへ載せない。初期UNRUN表示と生成8件時点のroot_reviewはその時点の履歴であり、最終summary/全10結果/終了確認を優先する。

今回のprimaryは限定TECHNICAL_CREDIT。全体品質・通常経路・本人端末一巡は残り、PRODUCT_NOT_CLEAR/正式0/3/54.50％維持。次は全文貼返しと本人宛の語りの原因を、教師・提示・実生成の対応から絞る。同じ24更新の繰返しや更新数の自動追加を次の処置にはしない。本人宛返答→通常接続→保存→同本文再読→本人端末の完成条件は保持する。製品source/owner/公開DTO/DB/RN/期限/本番/配布/main/料金/quota変更0、STRUCTURE_MAP_DELTA_NONE。
