"""Public scenarios and answer targets for the DeepInsight theme lane."""

# The IDs stay the same when wording changes. Issued questions use them for
# deduplication even after their wording has left the recent-history window.
THEME_ANGLES = {
    "first_action": "最初に取る行動",
    "priority": "選択の決め手",
    "change": "予定ややり方を変えるきっかけ",
    "boundary": "対象について自分が引き受ける範囲や限度",
    "cue": "決める前に確かめること",
    "outcome": "後でその選択に納得できる手がかり",
}

# Each pattern specifies what kind of answer the question must elicit.
THEME_QUESTION_FORMS = {
    "first_action": "何から始めるかを聞く。文型「〜するために、まず何をしますか？」",
    "priority": "選ぶ基準を聞く。文型「〜は、何を基準に決めますか？」",
    "change": "行動を変える条件を聞く。文型「〜するのは、どんなときですか？」",
    "boundary": "どこまで許容するかを聞く。金額・時間・内容など、対象に合う上限を尋ねる。",
    "cue": "判断前に確認したいことを聞く。文型「〜について、何を確かめておきますか？」",
    "outcome": "あとで納得できる手がかりを聞く。文型「どんなことがあれば、〜してよかったと思いますか？」",
}

THEME_SCENES = {
    "人間関係": {
        "new_people": "初対面の人と話すとき",
        "disagreement": "親しい人と意見が分かれたとき",
        "favors": "人から頼み事を受けたとき",
        "asking_help": "一人で抱えるか人に助けを求めるか迷ったとき",
        "reconnect": "しばらく会っていない人に連絡しようか迷ったとき",
        "group": "何人かで一緒にすることを決めるとき",
        "personal_topic": "個人的なことを誰かに話そうか迷ったとき",
        "conflict_repair": "自分の言葉が相手に違って伝わったと気づいたとき",
        "cancel": "誰かとの約束を変更する必要が出たとき",
        "listening": "相手が話を聞いてほしそうなとき",
        "thanks": "助けてもらった相手に感謝を伝えるとき",
        "distance": "親しい人と会う頻度を考えるとき",
        "group_entry": "すでに会話が始まっている輪に加わるとき",
        "contact_channel": "大切な話をメッセージにするか直接伝えるか迷ったとき",
        "feedback": "人に改善してほしいことを伝えるとき",
    },
    "自分の価値観": {
        "competing_commitments": "自分の大切な予定が二つ重なったとき",
        "money": "限られた予算を何に使うか決めるとき",
        "outside_expectations": "周囲の期待と自分の希望が食い違ったとき",
        "unpopular_choice": "少数派の考えでも自分の意見を伝えるか迷ったとき",
        "promise": "守りたい約束と目の前の都合がぶつかったとき",
        "shortcut": "速く済む方法と納得のいく方法で迷ったとき",
        "giving_credit": "複数の人で出した成果への感謝や評価を伝えるとき",
        "fairness": "全員を同じように扱うか事情に合わせるか迷ったとき",
        "public_private": "誰にも見られない場で自分のルールを守るか迷ったとき",
        "risk": "確実な選択と自分が試したい選択の間で迷ったとき",
        "useful_gift": "人に役立つものと気持ちが伝わるもののどちらを贈るか迷ったとき",
        "change_mind": "以前の自分の意見を見直すきっかけがあったとき",
        "measure": "目に見える評価と自分なりの納得が違ったとき",
        "spare_time": "空いた時間を自分のために使うか誰かのために使うか迷ったとき",
        "ownership": "人に何かを勧められて、応じるか迷ったとき",
    },
    "仕事・学び": {
        "new_method": "仕事や勉強で新しいやり方を試すとき",
        "stuck": "仕事や勉強で手が止まったとき",
        "feedback": "取り組んだことに改善点を指摘されたとき",
        "deadlines": "締め切りの近い作業がいくつか重なったとき",
        "transfer": "学んだことを実際の作業に使ってみるとき",
        "question": "説明を聞いて分からない点が残ったとき",
        "teach": "覚えたことを初めて人に教えるとき",
        "sources": "同じ課題に違う手順を勧める資料を見つけたとき",
        "collaboration": "共同作業で役割を分けるとき",
        "review": "覚えたつもりの内容を復習するとき",
        "error": "提出前に作業の誤りを見つけたとき",
        "scope": "進めている課題に新しい依頼や情報が加わったとき",
        "routine": "集中が途切れやすい日に勉強や作業を始めるとき",
        "experiment": "慣れた手順を別の方法に切り替えるか検討するとき",
        "finish": "区切りまで進んだ仕事や勉強を振り返るとき",
    },
    "日々の過ごし方": {
        "short_day": "自由に使える時間が少ない日",
        "tired_evening": "疲れて帰ってきた日の夜",
        "free_morning": "予定のない休みの日の朝",
        "between_tasks": "用事の間に少しだけ空き時間ができたとき",
        "changed_plans": "その日の予定が急に変わったとき",
        "sleep": "翌朝に予定があり夜の過ごし方を考えるとき",
        "meal": "家で食事を用意する時間が少ないとき",
        "housework": "家の用事がいくつかたまったとき",
        "screen": "スマートフォンを見る時間を見直すとき",
        "weather": "外出の予定が天気で変わりそうなとき",
        "quiet_time": "家の中で一人で落ち着ける時間を取りたいとき",
        "move": "体を動かそうと思って日常の予定に組み込むとき",
        "space": "身の回りの物を整えようと思ったとき",
        "transition": "仕事や勉強を終えて自分の時間に移るとき",
        "rest_day": "休みの日に用事と休息の両方を取り入れたいとき",
    },
    "これからのこと": {
        "first_step": "やってみたいことの最初の一歩を決めるとき",
        "several_goals": "始めてみたいことがいくつかあるとき",
        "change_habits": "暮らしが変わる前に今の習慣を振り返るとき",
        "six_months": "半年後までに少し前に進みたいことを考えるとき",
        "trial": "新しい環境が自分に合うか少し試してみるとき",
        "time_budget": "半年続けるつもりのことに使える時間を考えるとき",
        "learning_goal": "次に身につけたいことを選ぶとき",
        "milestone": "長い目標の途中に小さな区切りを置くとき",
        "uncertainty": "先の状況が読みづらい中で準備を始めるとき",
        "change_place": "これからどんな場所や環境で過ごしたいか考えるとき",
        "postpone": "やりたいことを今始めるか少し先にするか迷ったとき",
        "support": "続けたいことについて誰かの力を借りるか考えるとき",
        "new_role": "今後どんな役割を引き受けてみたいか考えるとき",
        "route_change": "目標はあるものの向かい方を変えようか迷ったとき",
        "leave_space": "先の予定を立てるとき、予定のない時間も取っておきたいとき",
    },
}

# Decision subjects are separate from the displayed scene so the writer can
# ask about a concrete object without restating the scene.
THEME_DECISION_TARGETS = {
    "人間関係": {
        "new_people": "会話の話題",
        "disagreement": "意見が違う相手との話し方",
        "favors": "頼み事を引き受けるかどうか",
        "asking_help": "誰かに助けを求めるかどうか",
        "reconnect": "久しぶりの相手に連絡するかどうか",
        "group": "みんなで一緒にすること",
        "personal_topic": "個人的なことを打ち明けるかどうか",
        "conflict_repair": "誤解が生じた言葉の伝え直し方",
        "cancel": "約束の変更の伝え方",
        "listening": "相手の話の聞き方",
        "thanks": "感謝の伝え方",
        "distance": "親しい人と会う頻度",
        "group_entry": "会話に加わる方法",
        "contact_channel": "大切な話を伝える方法",
        "feedback": "相手への改善点の伝え方",
    },
    "自分の価値観": {
        "competing_commitments": "重なった予定のどちらを優先するか",
        "money": "限られた予算の使い道",
        "outside_expectations": "周囲の期待と自分の希望の優先順位",
        "unpopular_choice": "少数派の意見を伝えるかどうか",
        "promise": "約束と目の前の都合のどちらを優先するか",
        "shortcut": "速さと納得を比べて方法を選ぶこと",
        "giving_credit": "共同の成果への感謝や評価の伝え方",
        "fairness": "全員を同じように扱うか事情に合わせるか",
        "public_private": "自分で決めたルールを守るかどうか",
        "risk": "確実な方と試したい方のどちらを選ぶか",
        "useful_gift": "贈り物を選ぶときに優先すること",
        "change_mind": "以前の意見を変えるかどうか",
        "measure": "周囲の評価と自分の納得のどちらを重く見るか",
        "spare_time": "空いた時間を誰のために使うか",
        "ownership": "人からの勧めに応じるかどうか",
    },
    "仕事・学び": {
        "new_method": "新しいやり方を使い続けるかどうか",
        "stuck": "手が止まった作業の見直し方",
        "feedback": "指摘された点をどう改善するか",
        "deadlines": "締め切りが重なった作業に取りかかる順番",
        "transfer": "学んだことを実際の作業に取り入れる方法",
        "question": "説明で分からなかった点の確かめ方",
        "teach": "覚えた内容を人に教える方法",
        "sources": "資料に載っている手順のどれを使うか",
        "collaboration": "共同作業の役割の分け方",
        "review": "覚えた内容が身についたかの確かめ方",
        "error": "提出前に見つけた誤りの直し方",
        "scope": "新しい依頼を受けたあとの作業の進め方",
        "routine": "集中が途切れやすい日の作業の始め方",
        "experiment": "慣れた手順を別の方法に切り替えるかどうか",
        "finish": "一区切りついた仕事や勉強の振り返り方",
    },
    "日々の過ごし方": {
        "short_day": "時間が少ない日に残しておきたい過ごし方",
        "tired_evening": "疲れて帰った夜の休み方",
        "free_morning": "予定のない休日の朝の過ごし方",
        "between_tasks": "用事の間にできた空き時間の使い道",
        "changed_plans": "変更のあった日の予定の組み直し方",
        "sleep": "夜の過ごし方を変えること",
        "meal": "時間が少ない日の食事の用意の仕方",
        "housework": "たまった家の用事に取りかかる順番",
        "screen": "スマートフォンを見る時間の取り方",
        "weather": "天気に合わせて外出の予定を変えるかどうか",
        "quiet_time": "家で一人で落ち着ける時間の取り方",
        "move": "体を動かす時間を日常に組み込む方法",
        "space": "身の回りを片づける順番",
        "transition": "仕事や勉強のあとに自分の時間へ切り替える方法",
        "rest_day": "休みの日の用事と休息の時間配分",
    },
    "これからのこと": {
        "first_step": "やってみたいことの始め方",
        "several_goals": "取りかかる順番",
        "change_habits": "暮らしを変えても残しておきたい習慣",
        "six_months": "半年後までに取り組みたいこと",
        "trial": "試した環境が自分に合うかどうか",
        "time_budget": "続けたいことに使う時間の決め方",
        "learning_goal": "次に身につけることの選び方",
        "milestone": "長い目標の途中に置く区切り",
        "uncertainty": "見通しの立ちにくい段階で進める準備",
        "change_place": "これから過ごす場所や環境の選び方",
        "postpone": "やりたいことを始める時期",
        "support": "続けたいことに人の力を借りるかどうか",
        "new_role": "これから引き受けてみたい役割",
        "route_change": "目標への向かい方を変えるかどうか",
        "leave_space": "先の予定にゆとりを残す時間の取り方",
    },
}

# These pairs need a more precise answer target than the general angle.
THEME_SCENE_WORDING = {
    ("人間関係", "thanks", "boundary"): "助けてもらった相手に、お礼の品を贈ろうと思ったとき",
    ("自分の価値観", "ownership", "boundary"): "人から勧められたことを少し試そうと思ったとき",
    ("自分の価値観", "fairness", "outcome"): "全員を同じように扱うか事情に合わせるか考えて、対応を決めたとき",
    ("仕事・学び", "new_method", "cue"): "仕事や勉強で新しいやり方を試す前に",
    ("仕事・学び", "routine", "change"): "作業の途中で集中が切れたとき",
    ("日々の過ごし方", "screen", "change"): "ふだんの生活でスマートフォンを見る時間が決まっているとき",
    ("日々の過ごし方", "transition", "change"): "仕事や勉強のあと、自分の時間に切り替えるための時間を取っているとき",
    ("これからのこと", "first_step", "cue"): "やってみたいことが思い浮かんだとき",
    ("これからのこと", "leave_space", "cue"): "先の予定を立てながら、空き時間も残しておきたいとき",
}


THEME_CHOICE_PREMISES = {
    ("自分の価値観", "fairness", "outcome"): "どの対応を選んだかは特定されていない。どちらの対応を選んだ人でも、結果を見て公平だったと思える手がかりを答えられる。",
    ("自分の価値観", "public_private", "first_action"): "ルールを守る選択は未確定。守ると決めた場合の話として尋ねる。",
    ("自分の価値観", "spare_time", "outcome"): "誰のために使うかは未確定。どちらを選んでも答えられるよう、その時間の使い方にあとで納得できる手がかりを聞く。",
    ("仕事・学び", "experiment", "first_action"): "切り替えるかどうかは未確定。二つの方法を試し比べ始める段階を聞く。",
    ("これからのこと", "route_change", "first_action"): "進め方を変えるかどうかは未確定。別の進め方を実際に少し試す行動を聞く。",
    ("これからのこと", "trial", "outcome"): "試したあと、その環境が合うと分かる手がかりを聞く。環境が合うことはまだ分からない。",
}

# Each group asks for the same judgment. Keep all stored keys so that
# either issued position blocks the other, including in archived history.
THEME_EQUIVALENT_POSITIONS = {
    "仕事・学び": (
        (("new_method", "outcome"), ("experiment", "outcome")),
        (("stuck", "change"), ("stuck", "boundary")),
    ),
}

THEME_TARGET_ANGLES = {
    ("人間関係", "personal_topic", "outcome"): "話した場合に打ち明けてよかったと思える相手の反応",
    ("自分の価値観", "ownership", "priority"): "人からの勧めに応じるかどうかを自分で決める基準",
    ("仕事・学び", "new_method", "outcome"): "試したあとに新しいやり方を使い続けようと思う手応え",
    ("日々の過ごし方", "sleep", "change"): "夜の予定を切り上げる条件",
    ("これからのこと", "several_goals", "priority"): "取りかかる順番を決める基準",
    ("仕事・学び", "finish", "change"): "振り返った結果、次の作業で進め方を変える条件",
    ("これからのこと", "change_habits", "change"): "暮らしが変わっても続けたい習慣の、やり方を変える条件",
    ("人間関係", "favors", "boundary"): "頼まれたことのうち、自分で引き受けられる範囲の目安",
    ("人間関係", "cancel", "change"): "約束の変更をどんな方法で相手に伝えるか、その方法を変える条件",
    ("自分の価値観", "money", "boundary"): "一つの使い道に、予算をどこまで使ってよいかを決める目安",
    ("仕事・学び", "deadlines", "boundary"): "一つの作業をどこまで進めてから次の作業に移るかを決める目安",
    ("日々の過ごし方", "screen", "boundary"): "その日のスマートフォンを見る時間をどこで切り上げるかの目安",
    ("これからのこと", "milestone", "boundary"): "途中の一つの区切りまで、どこまで進めるかを決める目安",
}

THEME_TARGET_FORMS = {
    ("人間関係", "new_people", "first_action"): "最初にどんなひと言をかけますか？",
    ("人間関係", "personal_topic", "outcome"): "相手の反応を聞く。文型「相手がどんな反応をすると、〜してよかったと思いますか？」",
    ("仕事・学び", "new_method", "outcome"): "続けたいと思う手応えを聞く。文型「どんな結果なら、〜を続けたいと思いますか？」",
    ("日々の過ごし方", "sleep", "change"): "夜の予定を切り上げる条件を聞く。文型「どんなときに、〜を切り上げますか？」",
    ("人間関係", "favors", "boundary"): "引き受ける範囲を聞く。文型「どこまでなら、〜を引き受けられますか？」",
    ("人間関係", "cancel", "change"): "伝え方を変える条件を聞く。文型「どんなときに、〜の伝え方を変えますか？」",
    ("自分の価値観", "money", "boundary"): "一つの使い道に回す金額の上限を判断する目安を聞く。",
    ("仕事・学び", "deadlines", "boundary"): "一つの作業をいったん終えて次に移る目安を聞く。",
    ("日々の過ごし方", "screen", "boundary"): "見る時間の上限や切り上げる目安を一つ聞く。",
    ("これからのこと", "milestone", "boundary"): "その区切りまでにどこまで進めるか、何を目安に決めますか？",
    ("人間関係", "thanks", "boundary"): "品物にどのくらいまでなら無理なくお金を使えますか？",
    ("自分の価値観", "ownership", "boundary"): "どの程度の負担までなら、引き受けてもいいと思いますか？",
    ("自分の価値観", "measure", "change"): "どんなことがあれば、自分の評価の基準を見直しますか？",
    ("仕事・学び", "new_method", "cue"): "慣れたやり方と何を比べておきますか？",
    ("仕事・学び", "experiment", "priority"): "どちらのやり方を使うか、何を基準に決めますか？",
    ("仕事・学び", "finish", "priority"): "進め方と結果のどちらから振り返るか、何を目安に決めますか？",
    ("仕事・学び", "routine", "change"): "このまま続けるか、いったん区切るかは、何を目安に決めますか？",
    ("日々の過ごし方", "tired_evening", "boundary"): "休む時間を残しながら、家の用事はどこまでできそうですか？",
    ("日々の過ごし方", "between_tasks", "outcome"): "次の用事に移るとき、どんな変化があれば、合間の時間をうまく使えたと感じますか？",
    ("日々の過ごし方", "screen", "change"): "どんな変化があれば、今と違う時間帯に見るようにしますか？",
    ("これからのこと", "several_goals", "priority"): "どれから取りかかるか、何を基準に決めますか？",
    ("これからのこと", "change_habits", "priority"): "今の習慣のうち、新しい暮らしでも続けるものは何を目安に選びますか？",
    ("これからのこと", "uncertainty", "cue"): "これからの予定で、準備を決める前に何を確かめておきますか？",
    ("人間関係", "asking_help", "priority"): "どんなことを手がかりに決めますか？",
    ("人間関係", "group_entry", "priority"): "どんな合図を見て、話に入るタイミングを決めますか？",
    ("自分の価値観", "fairness", "priority"): "どちらを選ぶか、何を目安に決めますか？",
    ("自分の価値観", "fairness", "outcome"): "対応したあと、どんな結果なら公平に扱えたと思いますか？",
    ("自分の価値観", "public_private", "first_action"): "自分のルールを守ると決めた場合、まず何をしますか？",
    ("自分の価値観", "risk", "boundary"): "試したい方がうまくいかなかった場合、どのくらいの不利益まで受け入れられますか？",
    ("自分の価値観", "shortcut", "outcome"): "どんな仕上がりなら、その方法を選んでよかったと思いますか？",
    ("自分の価値観", "spare_time", "outcome"): "どんなことがあれば、その時間の使い方でよかったと思いますか？",
    ("仕事・学び", "scope", "first_action"): "まず何に手をつけますか？",
    ("仕事・学び", "experiment", "first_action"): "二つのやり方を試し比べるために、まず何を試しますか？",
    ("仕事・学び", "feedback", "cue"): "直す箇所を決める前に、指摘された内容の何を確かめますか？",
    ("仕事・学び", "question", "cue"): "人に質問する前に、聞いた説明のどの部分を見直しますか？",
    ("日々の過ごし方", "changed_plans", "first_action"): "最初に何をしますか？",
    ("日々の過ごし方", "free_morning", "cue"): "朝の過ごし方を決める前に、自分の調子について何を確かめますか？",
    ("日々の過ごし方", "space", "boundary"): "疲れすぎないように、一度の片づけをどこで区切りますか？",
    ("日々の過ごし方", "transition", "first_action"): "気持ちに区切りをつけるために、まず何をしますか？",
    ("日々の過ごし方", "transition", "change"): "どんなときに、切り替えにかける時間を短くしますか？",
    ("これからのこと", "first_step", "cue"): "最初の一歩を決める前に、何を確かめておきますか？",
    ("これからのこと", "six_months", "outcome"): "半年後、どんな変化があれば少し前に進めたと感じますか？",
    ("これからのこと", "trial", "outcome"): "試したあと、どんなことがあれば、その環境が自分に合うと感じますか？",
    ("これからのこと", "learning_goal", "boundary"): "一度に身につける内容は、どこまでにしますか？",
    ("これからのこと", "route_change", "first_action"): "別の進め方を少し試すなら、最初にどんなことをしますか？",
    ("これからのこと", "postpone", "boundary"): "始める時期を決めるまでに、準備をどこまで進めておきたいですか？",
    ("これからのこと", "leave_space", "cue"): "空けておく時間を決める前に、動かせない予定について何を確かめておきますか？",
}

# These openings only repeat the authored scene for the specified angle.
# Match the entire leading clause, so a new time, place, or condition survives.
THEME_REPEATED_INTRODUCTIONS = {
    ("人間関係", "asking_help", "priority"): ("誰かに助けを求めるかどうか", "誰かに助けを求めるかどうかは", "誰かに助けを求める際"),
    ("自分の価値観", "ownership", "priority"): ("勧めを断るか受けるか",),
    ("自分の価値観", "ownership", "boundary"): ("勧められたことを試す際",),
    ("自分の価値観", "giving_credit", "first_action"): ("感謝や評価を伝える際",),
    ("仕事・学び", "finish", "change"): ("一区切りついた振り返りでは",),
    ("日々の過ごし方", "move", "first_action"): ("体を動かす時間を日常に組み込むために",),
    ("仕事・学び", "finish", "priority"): ("作業の振り返りで",),
    ("仕事・学び", "routine", "change"): ("集中が途切れたとき", "集中が途切れた際"),
    ("仕事・学び", "new_method", "cue"): ("新しいやり方を試す前に", "試す前に"),
    ("仕事・学び", "scope", "first_action"): ("新しい依頼や情報が加わった直後",),
    ("仕事・学び", "feedback", "cue"): ("改善点を指摘された際",),
    ("日々の過ごし方", "transition", "first_action"): ("仕事や勉強を終えた直後",),
    ("これからのこと", "route_change", "first_action"): ("目標の向かい方を変えようか迷ったとき",),
}

# The displayed scene itself already presents the two alternatives.
THEME_DECISION_IN_SCENE = frozenset({
    ("人間関係", "asking_help", "priority"),
    ("自分の価値観", "ownership", "priority"),
})

# These pairs ask for different answers when both displayed questions match
# the reviewed wording below. Other combinations still require comparison.
THEME_DISTINCT_POSITIONS = {
    "人間関係": (
        (("reconnect", "priority"), ("reconnect", "outcome")),
        (("asking_help", "priority"), ("asking_help", "cue")),
    ),
    "自分の価値観": (
        (("risk", "boundary"), ("ownership", "boundary")),
        (("risk", "boundary"), ("promise", "boundary")),
        (("ownership", "boundary"), ("promise", "boundary")),
        (("measure", "priority"), ("measure", "change")),
    ),
    "仕事・学び": (
        (("experiment", "priority"), ("experiment", "boundary")),
        (("experiment", "priority"), ("new_method", "priority")),
    ),
    "日々の過ごし方": (
        (("transition", "first_action"), ("transition", "outcome")),
    ),
    "これからのこと": (
        (("several_goals", "priority"), ("first_step", "priority")),
        (("several_goals", "priority"), ("change_habits", "priority")),
        (("first_step", "priority"), ("change_habits", "priority")),
    ),
}

# The first body is the writer example. Additional bodies are exact
# previously generated wording reviewed against the current displayed scene.
THEME_VERIFIED_BODIES = {
    ("人間関係", "reconnect", "priority"): (
        "自分から連絡するかどうかは、何を目安に決めますか？",
        "久しぶりの相手に連絡するかどうかは、何を基準に決めますか？",
    ),
    ("人間関係", "reconnect", "outcome"): (
        "連絡したあと、どんなやり取りができたら、声をかけてよかったと思いますか？",
    ),
    ("人間関係", "asking_help", "priority"): (
        "どんなことを手がかりに決めますか？",
    ),
    ("人間関係", "asking_help", "cue"): (
        "頼む相手を決める前に、候補の人について何を確かめておきますか？",
    ),
    ("自分の価値観", "risk", "boundary"): (
        "試したい方がうまくいかなかった場合、どのくらいの不利益まで受け入れられますか？",
    ),
    ("自分の価値観", "ownership", "boundary"): (
        "どの程度の負担までなら、引き受けてもいいと思いますか？",
        "どの程度の負担までなら引き受けていいと思いますか？",
    ),
    ("自分の価値観", "promise", "boundary"): (
        "約束を守るためなら、どこまで負担を引き受けられますか？",
    ),
    ("自分の価値観", "measure", "priority"): (
        "周りからの評価と自分の納得のうち、どちらを重く見るかは何を目安に決めますか？",
    ),
    ("自分の価値観", "measure", "change"): (
        "どんなことがあれば、自分の評価の基準を見直しますか？",
    ),
    ("仕事・学び", "experiment", "priority"): (
        "どちらのやり方を使うか、何を基準に決めますか？",
    ),
    ("仕事・学び", "experiment", "boundary"): (
        "別のやり方を試すなら、どの範囲まで試しますか？",
        "本格的な切り替えをする前に、どの程度の範囲で別の方法を試すつもりですか？",
    ),
    ("仕事・学び", "new_method", "priority"): (
        "どの作業で新しいやり方を試すか、何を目安に決めますか？",
    ),
    ("日々の過ごし方", "transition", "first_action"): (
        "気持ちに区切りをつけるために、まず何をしますか？",
        "区切りをつけるためにまず何をしますか？",
    ),
    ("日々の過ごし方", "transition", "outcome"): (
        "どんな変化があれば、自分の時間に気持ちが切り替わったと感じますか？",
    ),
    ("これからのこと", "several_goals", "priority"): (
        "どれから取りかかるか、何を基準に決めますか？",
        "取りかかる順番を決める基準は何ですか？",
    ),
    ("これからのこと", "first_step", "priority"): (
        "始め方がいくつかあるなら、何を目安に最初の一歩を選びますか？",
    ),
    ("これからのこと", "change_habits", "priority"): (
        "今の習慣のうち、新しい暮らしでも続けるものは何を目安に選びますか？",
    ),
}
