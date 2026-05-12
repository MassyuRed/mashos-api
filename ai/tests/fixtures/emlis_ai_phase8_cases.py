# -*- coding: utf-8 -*-
from __future__ import annotations

PHASE8_CASES = [
    {
        "case_id": "mixed_positive_anxiety",
        "emotion": "不安",
        "category": "人間関係",
        "memo": """今日は久しぶりに友達と話せて楽しかった。
ちゃんと笑えたし、少し元気になれた気がする。
でも帰ってきて一人になったら、また急に不安になった。
楽しかったはずなのに、なんでこんなに落ちるんだろうって思う。""",
        "expected_profile": "mixed_positive_anxiety",
        "expected_passed": True,
        "must_contain_any": [["友達", "楽しかった"], ["元気"], ["一人", "不安"]],
    },
    {
        "case_id": "anger_hurt_boundary",
        "emotion": "怒り",
        "category": "人間関係",
        "memo": """相手の言い方がきつくて腹が立った。
こっちはちゃんと考えて話してるのに、なんであんな言い方されなきゃいけないのか分からない。
怒ってるけど、本当は大事に扱われなかったことがしんどい。
もう話すのが面倒になってきた。""",
        "expected_profile": "anger_hurt_boundary",
        "expected_passed": True,
        "must_contain_any": [["言い方", "怒り"], ["大事に扱われ"], ["面倒"]],
    },
    {
        "case_id": "short_ambiguous_low_evidence",
        "emotion": "不安",
        "category": "生活",
        "memo": """なんか今日は全部だるい。
何もしたくない。""",
        "expected_profile": "short_ambiguous_low_evidence",
        "expected_passed": False,
        "must_contain_any": [],
    },
    {
        "case_id": "self_understanding_loop",
        "emotion": "自己理解",
        "category": "学習",
        "memo": """また考えすぎて動けなくなった。
やることは分かってるのに、先のことを考え始めると止まらなくなる。
たぶん完璧にやろうとしすぎてる。
でも適当にやるのも怖い。""",
        "expected_profile": "self_understanding_loop",
        "expected_passed": True,
        "must_contain_any": [["考えすぎ", "動け"], ["分かって", "止まら"], ["完璧", "適当"]],
    },
    {
        "case_id": "positive_progress",
        "emotion": "喜び",
        "category": "生活",
        "memo": """今日は少しだけ部屋を片付けられた。
大きなことじゃないけど、ずっと気になってた場所だったから少し気持ちが軽い。
ちゃんとできた感じがして嬉しい。""",
        "expected_profile": "positive_progress",
        "expected_passed": True,
        "must_contain_any": [["片付け"], ["気持ち", "軽"], ["できた", "嬉し"]],
    },
    {
        "case_id": "relationship_approach_avoidance",
        "emotion": "不安",
        "category": "人間関係",
        "memo": """本当はもっと頼りたい。
でも頼ったら迷惑だと思われそうで言えない。
相手に嫌われたいわけじゃないし、重いと思われるのも怖い。
でも一人で抱えるのも限界に近い。""",
        "expected_profile": "relationship_approach_avoidance",
        "expected_passed": True,
        "must_contain_any": [["頼りたい"], ["迷惑"], ["嫌われ", "重い"], ["限界"]],
    },
    {
        "case_id": "real_user_reality_escape_tension",
        "emotion": "自己理解",
        "category": "生活",
        "memo": """ずっと家にいて、リラックスできて自分のことを
優先して色々整えたりお家のことも出来るから
嬉しいんだけど、ふって気が抜けたときに現実と
向き合うことがあるからその時にダメージでかい
あぁ、今の生活不便だな、と。
気をつけなきゃ行けないこと、全部無視して普通に
生活したい。でもそうしたらもっと悪化する
そんなの分かってる。たまに逃げ出したくなる""",
        "expected_profile": "reality_escape_tension",
        "expected_passed": True,
        "must_contain_any": [["リラックス", "優先"], ["現実", "不便"], ["生活したい", "悪化"], ["逃げ出"]],
    },
]

PHASE8_FORBIDDEN_SURFACES = (
    "がつながっています",
    "同じ中にあります",
    "なんであが",
    "考え始めが",
    "悪化するが",
    "不安。",
    "怒り。",
    "喜び。",
    "自己理解。",
)

# Phase8-R0: 既存7ケースと同じ構造を、別語彙の入力でも扱えることを固定する。
# これは正解文一致ではなく、profile / must_keep 構造 / forbidden surface で見る回帰fixture。
PHASE8_GENERALIZATION_CASES = [
    {
        "case_id": "mixed_positive_anxiety_variant_walk_home",
        "emotion": "不安",
        "category": "生活",
        "memo": """今日は仕事で疲れていたけれど、帰りに少し散歩したら落ち着いた。
夜になって静かになったら、明日の失敗のことが急に不安になった。
さっきほっとしていた分、落差が大きかった。""",
        "expected_profile": "mixed_positive_anxiety",
        "expected_passed": True,
        "must_contain_any": [["散歩", "落ち着"], ["夜", "不安"], ["失敗", "落差"]],
        "must_not_contain": ["友達", "楽しか", "笑え", "元気", "一人になった"],
    },
    {
        "case_id": "anger_hurt_boundary_variant_lightly_handled",
        "emotion": "怒り",
        "category": "人間関係",
        "memo": """相手の返し方が雑で、すごくむっとした。
こっちは丁寧に伝えようとしていたのに、軽く扱われた感じがしてしんどい。
もう説明する気力がなくなっている。""",
        "expected_profile": "anger_hurt_boundary",
        "expected_passed": True,
        "must_contain_any": [["返し方", "雑"], ["むっと"], ["軽く扱われ", "しんど"], ["説明", "気力"]],
        "must_not_contain": ["言い方がきつ", "腹が立", "大事に扱われなかった", "話すのが面倒"],
    },
    {
        "case_id": "self_understanding_loop_variant_failure_fear",
        "emotion": "自己理解",
        "category": "学習",
        "memo": """やることは見えているのに、明日のことを考えると手が止まる。
失敗が怖くて、ちゃんとできない気がして進めない。
でも何もしないままなのも嫌だ。""",
        "expected_profile": "self_understanding_loop",
        "expected_passed": True,
        "must_contain_any": [["見えて", "手が止ま"], ["失敗", "怖"], ["ちゃんとできない"], ["進めない", "嫌"]],
        "must_not_contain": ["考えすぎ", "完璧", "適当"],
    },
    {
        "case_id": "positive_progress_variant_dishes_kitchen",
        "emotion": "喜び",
        "category": "生活",
        "memo": """今日は洗い物を少し終えた。
ずっと気になっていた台所が整って、気持ちが落ち着いた。
自分でも少し進められた感じがしてほっとした。""",
        "expected_profile": "positive_progress",
        "expected_passed": True,
        "must_contain_any": [["洗い物"], ["台所", "整"], ["気持ち", "落ち着"], ["進め", "ほっと"]],
        "must_not_contain": ["片付け", "気持ちが軽", "ちゃんとでき", "嬉しい"],
    },
    {
        "case_id": "relationship_approach_avoidance_variant_consult_time_burden",
        "emotion": "不安",
        "category": "人間関係",
        "memo": """本当は相談したい。
でも相手の時間を奪う気がして、なかなか言い出せない。
助けを借りたいのに、困らせそうで怖い。
このまま一人で考え続けるのはつらい。""",
        "expected_profile": "relationship_approach_avoidance",
        "expected_passed": True,
        "must_contain_any": [["相談したい"], ["時間を奪う"], ["助け", "困らせ"], ["一人", "つらい"]],
        "must_not_contain": ["頼りたい", "迷惑", "嫌われ", "重い", "限界"],
    },
    {
        "case_id": "reality_escape_tension_variant_usual_life_health",
        "emotion": "自己理解",
        "category": "生活",
        "memo": """家にいると少し安心できるし、自分のペースで過ごせるのはありがたい。
でも外に出る準備や移動のことを考えると、今の生活の不便さが急に重くなる。
いつも通りに過ごしたいけど、そのまま動くとまた体調が崩れそうで怖い。
全部投げ出したくなる時がある。""",
        "expected_profile": "reality_escape_tension",
        "expected_passed": True,
        "must_contain_any": [["安心", "ペース"], ["生活", "不便"], ["いつも通り", "体調"], ["投げ出"]],
        "must_not_contain": ["リラックス", "自分を優先", "普通に生活したい", "悪化", "逃げ出"],
    },
]

