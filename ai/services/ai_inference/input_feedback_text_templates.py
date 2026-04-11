# -*- coding: utf-8 -*-
"""input_feedback_text_templates.py

感情入力直後コメント（input_feedback.comment_text）の文面テンプレ管理と
選択ロジックをまとめたモジュール。

目的
----
- 感情選択のみでも、強度差・複合差・同条件での複数パターンを出せるようにする。
- memo / memo_action は分析入力ではなく、出力文面のトーン調整材料としてのみ扱う。
- テンプレ群を API 本体から切り出し、文面改善をサーバ更新だけで回しやすくする。

設計メモ
--------
- 出力は「分析」ではなく 1〜2 文の短い受け取りコメント。
- 感情構成から state_key を決め、そこに strength / memo tone を薄く重ねて候補文を作る。
- 同じ感情・同じ強度でも、selection_seed によって安定的に variant を切り替える。
"""

from __future__ import annotations

import copy
import hashlib
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

DEFAULT_INPUT_FEEDBACK_TEXT_TEMPLATE_ID = "input_feedback_ja_v1"
SELF_INSIGHT_EMOTION_TYPE = "自己理解"

_VALID_STRENGTHS = ("weak", "medium", "strong")
_STRENGTH_RANK = {"weak": 0, "medium": 1, "strong": 2}

INPUT_FEEDBACK_HINT_KEYWORDS: Tuple[Tuple[Tuple[str, ...], str], ...] = (
    (("わかって", "分かって", "理解", "聞いて", "受け止め", "伝えたい"), "understood"),
    (("整理", "まとめ", "言葉", "書き出", "整え", "落ち着"), "organize"),
    (("引っか", "もや", "残っ", "まだ", "うまく", "苦しい"), "residual"),
)

_EMOTION_KEY_MAP: Dict[str, str] = {
    "喜び": "joy",
    "悲しみ": "sadness",
    "怒り": "anger",
    "不安": "anxiety",
    "平穏": "calm",
    SELF_INSIGHT_EMOTION_TYPE: "self_insight",
}


@dataclass(frozen=True)
class InputFeedbackTextTemplateInfo:
    template_id: str
    description: str


@dataclass(frozen=True)
class InputFeedbackContext:
    dominant_type: str
    dominant_strength: str
    emotion_types: Tuple[str, ...]
    multiple: bool
    memo_mode: str

    @property
    def emotion_signature(self) -> str:
        return ",".join(self.emotion_types)


@dataclass(frozen=True)
class InputFeedbackSentence:
    role: str
    text: str


_INPUT_FEEDBACK_TEXT_TEMPLATES: Dict[str, Dict[str, Any]] = {
    DEFAULT_INPUT_FEEDBACK_TEXT_TEMPLATE_ID: {
        "fallback_templates": {
            "any": [
                "いまは気持ちをすぐに片づけるより、まずはこの状態を言葉にして受け止めたかったのかもしれません。",
                "気持ちがまだまとまりきらなくても、そのままにせず少し確かめたくなっていたのかもしれません。",
                "はっきり答えを出すより、まず今の感じを自分の中で置き直したかった状態に近そうです。",
            ],
        },
        "tone_templates": {
            "understood": {
                "any": [
                    "解決したいというより、まずはこの感じを分かってほしい気持ちのほうが近そうです。",
                    "答えを急ぐより、いまの気持ちを受け取ってもらいたかったのかもしれません。",
                    "整理より先に、この感覚ごと分かってほしい気持ちが前に出ていそうです。",
                ],
            },
            "organize": {
                "any": [
                    "いまは抱えたままにするより、少しでも自分の中で整えたかった状態に近そうです。",
                    "気持ちを消すというより、言葉にできる形まで落ち着かせたかったのかもしれません。",
                    "そのまま流すより、いったん自分の中で順番をつけたかった感じがあります。",
                ],
            },
            "residual": {
                "any": [
                    "もう言い切れるほど強くはなくても、まだ少しその気持ちの近くにいる感じがあります。",
                    "落ち着いてきていても、完全には離れきっていない余韻が残っていそうです。",
                    "大きくは揺れていなくても、まだ小さく引っかかりが続いている感じがあります。",
                ],
            },
        },
        "state_templates": {
            "self_insight": {
                "any": [
                    "いまは気持ちを片づけるより、まず自分の状態を言葉にして確かめたくなっているのかもしれません。",
                    "答えを出すより先に、いまの自分を少し整理して見ておきたかったのかもしれません。",
                    "自分の中にあるものを、いったん言葉にして輪郭を確かめたかった状態に近そうです。",
                ],
            },
            "sadness": {
                "weak": [
                    "悲しさが強く押し寄せるというより、まだ静かに残っている感じがあります。",
                    "もう大きく揺れてはいなくても、少しだけその気持ちの近くにいるようです。",
                    "気持ちは落ち着きかけていても、完全には抜けきっていない余韻がありそうです。",
                ],
                "medium": [
                    "悲しさをなくしたいというより、いまの形のまま静かに受け止めようとしている感じがあります。",
                    "すぐ切り替えるより、まだその気持ちに少し寄り添っていたい状態に近そうです。",
                    "抱えたままでも、いったんこの気持ちをそのまま見ておきたかったのかもしれません。",
                ],
                "strong": [
                    "いまは気持ちを切り替えたというより、抱えたまま少しずつ整えようとしている状態に近そうです。",
                    "悲しさから離れるより、まずはその重さごと受け止めようとしている感じがあります。",
                    "強く残る気持ちを急いで消すより、そのまま持ちながら整えようとしているのかもしれません。",
                ],
                "any": [
                    "悲しさをなくすより、まずはいまの気持ちの位置を確かめたかったのかもしれません。",
                    "つらさを片づけるより、いまの感じをそのまま受け止め直したい状態に近そうです。",
                ],
            },
            "anxiety": {
                "weak": [
                    "先のことが少し気になりながらも、まだ安心できる位置を探している感じがあります。",
                    "はっきりした不安というより、小さく確かめたさが残っている状態に近そうです。",
                    "大きく揺れるほどではなくても、心のどこかで先を見にいっている感じがあります。",
                ],
                "medium": [
                    "先をはっきりさせたい気持ちよりも、まだ安心できる位置を探している感じが残っています。",
                    "落ち着きたいのに、気持ちのほうはまだ少し先回りしているようです。",
                    "まだ大丈夫と言い切るより、もう少し確かめていたい状態に近そうです。",
                ],
                "strong": [
                    "気持ちを落ち着かせたい一方で、まだ先のことを強く確かめたがっているようです。",
                    "いまは安心するより先に、不安の理由を見張っていたい感じが強そうです。",
                    "落ち着こうとしていても、気持ちのほうはまだかなり前のめりに先を見にいっているようです。",
                ],
                "any": [
                    "安心したい気持ちはありつつ、まだ少し確かめていたさが残っているようです。",
                    "気持ちを静かにしたいのに、心のどこかではまだ先を追っている感じがあります。",
                ],
            },
            "anger": {
                "weak": [
                    "強くぶつけたいというより、小さな引っかかりをそのままにできない感じが残っています。",
                    "怒りそのものより、納得できなさを自分の中で確かめたい状態に近そうです。",
                    "大きく表に出すほどではなくても、まだ線を引き直したい気持ちが残っていそうです。",
                ],
                "medium": [
                    "納得できない感じをそのままにできず、まず自分の中で線を引き直したかったのかもしれません。",
                    "強くぶつけたいというより、引っかかりをどう扱うか決めたかった感じがあります。",
                    "怒りを外へ向けるより、まずは自分の中で整理し直したい状態に近そうです。",
                ],
                "strong": [
                    "いまは納得できない感じをそのままにせず、自分を守る線をはっきりさせたかったのかもしれません。",
                    "強い引っかかりを抱えたまま、まず自分の中で境界を引き直そうとしている感じがあります。",
                    "怒りをそのままぶつけるより、傷つかない位置を強く確かめたかった状態に近そうです。",
                ],
                "any": [
                    "引っかかりを流すより、まず自分の中で納得できる位置を探したかったのかもしれません。",
                    "ただ怒っているというより、何を守りたいのかを確かめたい状態に近そうです。",
                ],
            },
            "joy": {
                "weak": [
                    "大きく気分が上がるというより、少し力が抜けて前向きさが戻りかけている感じがあります。",
                    "うれしさが強く弾けるというより、ほっとする感覚が静かに出てきているようです。",
                    "小さく気持ちがほどけて、少し明るさが戻ってきている状態に近そうです。",
                ],
                "medium": [
                    "うれしさそのものより、少し力が抜けて前向きさが戻ってきた感じが前に出ています。",
                    "気分が上がるというより、安心や手応えがほどよく戻ってきているようです。",
                    "気持ちが軽くなって、少し自然に前を向ける感じが出てきているのかもしれません。",
                ],
                "strong": [
                    "いまは気持ちがかなりほどけて、前向きな感覚がしっかり戻ってきているようです。",
                    "うれしさと一緒に、安心して力が抜ける感覚も強く前に出ていそうです。",
                    "気分の上向きだけでなく、自分の中の明るさがはっきり戻ってきている感じがあります。",
                ],
                "any": [
                    "前向きさが戻ってきて、少し自然に気持ちが開いているようです。",
                    "うれしさの中に、ほっとできる感覚も一緒に出てきているのかもしれません。",
                ],
            },
            "calm": {
                "weak": [
                    "大きく揺れていないというより、落ち着ける位置に戻りかけている途中に近そうです。",
                    "静かになったというより、ようやく自分の中で落ち着く場所を探せている感じがあります。",
                    "気持ちが整いきったというより、少しずつ落ち着きを取り戻しているようです。",
                ],
                "medium": [
                    "大きく揺れていないというより、自分の中で落ち着ける位置へ戻り直している途中に近そうです。",
                    "静かに見えていても、それは気持ちが自然に整ってきている流れなのかもしれません。",
                    "無理に抑えた静けさというより、少しずつ落ち着きが戻ってきている感じがあります。",
                ],
                "strong": [
                    "いまはかなり落ち着ける位置に戻れていて、自分の中の静けさがしっかり保たれている感じがあります。",
                    "気持ちを無理に抑えるというより、安心できる位置にちゃんと戻れているようです。",
                    "静かさを作っているというより、内側の落ち着きがはっきり整っている状態に近そうです。",
                ],
                "any": [
                    "気持ちを押さえ込むより、自然に落ち着ける位置へ戻っていこうとしているようです。",
                    "静かになったというより、自分の中の整う場所へ戻ろうとしている感じがあります。",
                ],
            },
            "mixed": {
                "any": [
                    "気持ちが一つにまとまりきらないままでも、そのままにせず確かめたくなっていたのかもしれません。",
                    "一つに言い切れない感じがありながらも、いまの状態を少し整理して見ておきたかったようです。",
                    "気持ちが重なっていても、そのまま流さず受け止め直したかった状態に近そうです。",
                ],
                "strong": [
                    "いくつかの気持ちが強めに重なっていても、まずはそのままの形で見ておきたかったのかもしれません。",
                    "気持ちが複雑なままでも、急いで一つに決めずに確かめたかった状態に近そうです。",
                ],
            },
            "sadness_mixed": {
                "any": [
                    "悲しさを軸にしながら、ほかの気持ちも重なっていて、まだ少し整理しきれていないようです。",
                    "悲しさの近くに別の気持ちも重なっていて、まだ心の置き場を探している感じがあります。",
                ],
            },
            "anxiety_mixed": {
                "any": [
                    "気がかりを軸にしながら、ほかの気持ちも重なっていて、まだ安心しきれていないようです。",
                    "先を気にする感じのまわりに別の気持ちも重なっていて、少し張りが残っているようです。",
                ],
            },
            "anger_mixed": {
                "any": [
                    "引っかかりを軸にしながら、ほかの気持ちも混ざっていて、まだ気持ちの置き場を探しているようです。",
                    "納得できなさのまわりに別の気持ちも重なっていて、まだ線を引き直したい感じがあります。",
                ],
            },
            "joy_mixed": {
                "any": [
                    "前向きさはありつつも、ほかの気持ちも重なっていて、まだ完全に一色にはなっていないようです。",
                    "明るさが戻りながらも、別の気持ちも一緒に残っていて、少し複雑な重なり方に近そうです。",
                ],
            },
            "calm_mixed": {
                "any": [
                    "落ち着きに戻ろうとしていながらも、別の気持ちがまだ少し重なっているようです。",
                    "静けさはありつつ、内側ではほかの気持ちもまだ完全には離れていない感じがあります。",
                ],
            },
            "calm_sadness": {
                "any": [
                    "もう大きく崩れてはいないけれど、悲しさの余韻はまだ少し残っている感じがあります。",
                    "落ち着いてきてはいても、悲しさだけはまだ静かに残っているようです。",
                    "表面は少し整っていても、内側では悲しさの名残が続いている感じがあります。",
                ],
                "strong": [
                    "落ち着こうとしていても、悲しさはまだはっきり近くに残っているようです。",
                    "揺れのピークは越えていても、悲しさの重さはまだ強めに残っていそうです。",
                ],
            },
            "calm_anxiety": {
                "any": [
                    "落ち着こうとしているのに、気持ちのほうはまだ少し先を気にしているようです。",
                    "静かにしたい気持ちと、まだ確かめていたい気持ちが同時に残っている感じがあります。",
                    "表では落ち着いていても、内側ではまだ少し先回りしているようです。",
                ],
                "strong": [
                    "落ち着きに戻ろうとしていても、不安のほうはまだかなり先を気にしているようです。",
                    "静かにしたいのに、内側では強めの気がかりがまだ残っている感じがあります。",
                ],
            },
            "calm_anger": {
                "any": [
                    "表では静かでも、内側にはまだ引っかかりが少し残っている感じがあります。",
                    "落ち着こうとしていても、納得できなさはまだ小さく残っているようです。",
                    "表面は静かでも、心の中ではまだ線を引き直したい感じが続いていそうです。",
                ],
                "strong": [
                    "静かに戻ろうとしていても、引っかかりの強さはまだはっきり残っているようです。",
                    "表では抑えられていても、内側ではまだ強めの納得できなさが続いている感じがあります。",
                ],
            },
            "calm_sadness_anxiety": {
                "any": [
                    "落ち着きたい気持ちはありつつ、悲しさと不安の余韻がまだ少し重なっているようです。",
                    "静かに戻ろうとしているのに、悲しさと気がかりがまだ残っている感じがあります。",
                    "表では整えようとしていても、内側では悲しさと先への気がかりが続いていそうです。",
                ],
                "strong": [
                    "落ち着こうとしていても、悲しさと不安の重なりはまだ強めに近くにあるようです。",
                    "静けさに戻りかけながらも、悲しさと気がかりがまだかなり残っている感じがあります。",
                ],
            },
            "sadness_anxiety": {
                "weak": [
                    "悲しさを抱えたまま、まだ少し先のことも気にしている状態に近そうです。",
                    "つらさと気がかりが重なっていて、まだ少し安心しきれない感じがあります。",
                ],
                "medium": [
                    "悲しさを抱えたまま、まだ先のことも少し気にしている状態に近そうです。",
                    "つらさと気がかりが重なっていて、まだ安心しきれない感じがあります。",
                    "悲しさの中に不安も混ざっていて、気持ちが休まりきっていないようです。",
                ],
                "strong": [
                    "悲しさと不安がどちらも強めに重なっていて、まだ気持ちを休ませにくい状態に近そうです。",
                    "つらさと気がかりが強く重なっていて、まだかなり安心しきれない感じがあります。",
                    "悲しさの中に不安もはっきり混ざっていて、気持ちが休まりきっていないようです。",
                ],
                "any": [
                    "つらさと気がかりが同時にあって、気持ちの置き場をまだ探している感じがあります。",
                    "悲しさだけでなく先への気がかりも重なっていて、まだ心が休まりきっていないようです。",
                ],
            },
            "anger_anxiety": {
                "any": [
                    "引っかかりを抱えながら、同時に先のことも気にしている感じがあります。",
                    "納得できなさと気がかりが重なっていて、まだ気持ちが張っているようです。",
                    "怒りだけで押しているというより、警戒しながら引っかかりを見ている状態に近そうです。",
                ],
                "strong": [
                    "引っかかりと気がかりが強めに重なっていて、まだかなり気持ちが張っているようです。",
                    "納得できなさと警戒心がどちらも強く残っていて、まだ身構えている感じがあります。",
                ],
            },
            "sadness_anger": {
                "any": [
                    "傷ついた感じと納得できなさが重なって、まだ気持ちの置き場を探しているようです。",
                    "悲しさだけでなく、受け入れきれない引っかかりも同時に残っている感じがあります。",
                    "つらさの中に怒りも混ざっていて、まだうまく下ろしきれていないようです。",
                ],
                "strong": [
                    "悲しさと怒りがどちらも強めに残っていて、まだ気持ちの置き場を見つけにくいようです。",
                    "傷ついた感じと受け入れられなさが重なって、まだかなり下ろしきれていない感じがあります。",
                ],
            },
            "joy_calm": {
                "any": [
                    "気分が上がっているというより、安心や手応えが少し戻ってきている感覚のほうが近そうです。",
                    "うれしさと落ち着きが重なって、ほっとできる位置に戻れている感じがあります。",
                    "明るさと静けさが一緒にあって、力が自然に抜けてきているようです。",
                ],
                "strong": [
                    "うれしさと落ち着きがどちらもしっかり出ていて、安心できる位置にかなり戻れているようです。",
                    "明るさと静けさが強めに重なって、気持ちが大きくほどけている感じがあります。",
                ],
            },
            "joy_anxiety": {
                "any": [
                    "前向きさはありつつも、まだ少し先を確かめていたい気持ちが残っているようです。",
                    "うれしさの中に気がかりも混ざっていて、完全には気を抜ききれていない感じがあります。",
                    "明るい気持ちが戻りながらも、まだ心のどこかで慎重さが残っていそうです。",
                ],
                "strong": [
                    "前向きさがありながらも、気がかりもかなり近くにあって、まだ完全には気を抜けないようです。",
                    "うれしさと慎重さがどちらも強めに出ていて、気持ちが前にも後ろにも引かれている感じがあります。",
                ],
            },
            "joy_sadness": {
                "any": [
                    "明るさがありながらも、まだ少し切なさが残っているような重なり方に近そうです。",
                    "うれしさだけでなく、静かな寂しさも同時にある感じがあります。",
                    "気持ちは上向きでも、まだ手放しきれていないものが小さく残っていそうです。",
                ],
                "strong": [
                    "明るさが戻りながらも、切なさもまだかなり近くに残っているようです。",
                    "前向きさと寂しさがどちらも強めに重なっていて、まだ一色にはなりきっていない感じがあります。",
                ],
            },
            "joy_anger": {
                "any": [
                    "前向きさがありつつも、まだどこかに納得しきれない引っかかりが残っているようです。",
                    "気持ちは少し明るいのに、完全には割り切れていない感じも同時にありそうです。",
                    "明るさが戻りながらも、まだ小さな反発や引っかかりが残っている感じがあります。",
                ],
                "strong": [
                    "明るさと引っかかりがどちらも強めにあり、まだ気持ちが一つに定まりきっていないようです。",
                    "前向きさが出ていても、納得しきれない気持ちもかなり残っている感じがあります。",
                ],
            },
        },
    }
}

_TEMPLATE_INFOS: Dict[str, InputFeedbackTextTemplateInfo] = {
    DEFAULT_INPUT_FEEDBACK_TEXT_TEMPLATE_ID: InputFeedbackTextTemplateInfo(
        template_id=DEFAULT_INPUT_FEEDBACK_TEXT_TEMPLATE_ID,
        description="感情入力直後コメントの標準テンプレート群（強度差・複合差・memo tone 対応）",
    ),
}


def list_input_feedback_text_templates() -> List[InputFeedbackTextTemplateInfo]:
    return list(_TEMPLATE_INFOS.values())



def get_input_feedback_text_template(
    template_id: str = DEFAULT_INPUT_FEEDBACK_TEXT_TEMPLATE_ID,
) -> Dict[str, Any]:
    template = _INPUT_FEEDBACK_TEXT_TEMPLATES.get(template_id)
    if template is None:
        template = _INPUT_FEEDBACK_TEXT_TEMPLATES[DEFAULT_INPUT_FEEDBACK_TEXT_TEMPLATE_ID]
    return copy.deepcopy(template)



def _normalize_strength(value: Any) -> str:
    strength = str(value or "").strip().lower()
    return strength if strength in _VALID_STRENGTHS else "medium"



def _strength_rank(value: Any) -> int:
    return _STRENGTH_RANK.get(_normalize_strength(value), 0)



def _normalize_emotion_details(
    emotion_details: Sequence[Dict[str, Any]],
) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    seen_pairs = set()

    for item in emotion_details or []:
        if not isinstance(item, dict):
            continue
        emotion_type = str(item.get("type") or "").strip()
        if not emotion_type:
            continue
        strength = _normalize_strength(item.get("strength"))
        key = (emotion_type, strength)
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        out.append({"type": emotion_type, "strength": strength})
    return out



def _dominant_emotion_detail(
    emotion_details: Sequence[Dict[str, str]],
) -> Optional[Dict[str, str]]:
    best: Optional[Dict[str, str]] = None
    best_rank = -1
    for item in emotion_details or []:
        rank = _strength_rank(item.get("strength"))
        if rank > best_rank:
            best = item
            best_rank = rank
    return best



def _memo_hint_mode(memo: Optional[str], memo_action: Optional[str]) -> str:
    text = " ".join([str(memo or "").strip(), str(memo_action or "").strip()]).strip()
    if not text:
        return ""
    lower = text.lower()
    for keywords, mode in INPUT_FEEDBACK_HINT_KEYWORDS:
        if any(keyword in text or keyword in lower for keyword in keywords):
            return mode
    return ""



def _emotion_key(emotion_type: str) -> str:
    return _EMOTION_KEY_MAP.get(str(emotion_type or "").strip(), "")



def _build_context(
    *,
    emotion_details: Sequence[Dict[str, Any]],
    memo: Optional[str],
    memo_action: Optional[str],
) -> Optional[InputFeedbackContext]:
    details = _normalize_emotion_details(emotion_details)
    if not details:
        return None

    dominant = _dominant_emotion_detail(details) or {}
    dominant_type = str(dominant.get("type") or "").strip()
    dominant_strength = _normalize_strength(dominant.get("strength"))
    emotion_types = tuple(
        str(item.get("type") or "").strip()
        for item in details
        if str(item.get("type") or "").strip()
    )

    return InputFeedbackContext(
        dominant_type=dominant_type,
        dominant_strength=dominant_strength,
        emotion_types=emotion_types,
        multiple=len(emotion_types) >= 2,
        memo_mode=_memo_hint_mode(memo, memo_action),
    )



def _classify_state_key(ctx: InputFeedbackContext) -> str:
    dominant_key = _emotion_key(ctx.dominant_type)
    emotion_set = set(ctx.emotion_types)

    if ctx.dominant_type == SELF_INSIGHT_EMOTION_TYPE:
        return "self_insight"

    if not ctx.multiple:
        return dominant_key or "mixed"

    if {"平穏", "悲しみ", "不安"}.issubset(emotion_set):
        return "calm_sadness_anxiety"
    if "平穏" in emotion_set and "悲しみ" in emotion_set:
        return "calm_sadness"
    if "平穏" in emotion_set and "不安" in emotion_set:
        return "calm_anxiety"
    if "平穏" in emotion_set and "怒り" in emotion_set:
        return "calm_anger"
    if "喜び" in emotion_set and "平穏" in emotion_set:
        return "joy_calm"
    if "悲しみ" in emotion_set and "不安" in emotion_set:
        return "sadness_anxiety"
    if "怒り" in emotion_set and "不安" in emotion_set:
        return "anger_anxiety"
    if "悲しみ" in emotion_set and "怒り" in emotion_set:
        return "sadness_anger"
    if "喜び" in emotion_set and "不安" in emotion_set:
        return "joy_anxiety"
    if "喜び" in emotion_set and "悲しみ" in emotion_set:
        return "joy_sadness"
    if "喜び" in emotion_set and "怒り" in emotion_set:
        return "joy_anger"

    return f"{dominant_key}_mixed" if dominant_key else "mixed"



def _state_key_chain(ctx: InputFeedbackContext) -> Tuple[str, ...]:
    primary = _classify_state_key(ctx)
    keys: List[str] = [primary]

    if ctx.multiple:
        dominant_key = _emotion_key(ctx.dominant_type)
        dominant_mixed = f"{dominant_key}_mixed" if dominant_key else ""
        if dominant_mixed and dominant_mixed not in keys:
            keys.append(dominant_mixed)
        if "mixed" not in keys:
            keys.append("mixed")

    return tuple(keys)



def _texts_from_values(values: Any) -> List[str]:
    if not isinstance(values, list):
        return []
    out: List[str] = []
    for value in values:
        text = str(value or "").strip()
        if text:
            out.append(text)
    return out


def _bucket_candidates(
    bucket: Optional[Dict[str, Any]],
    *,
    strength: str,
) -> List[str]:
    if not isinstance(bucket, dict):
        return []

    exact = _texts_from_values(bucket.get(strength))
    if exact:
        return _dedupe_keep_order(exact)

    fallback = _texts_from_values(bucket.get("any"))
    return _dedupe_keep_order(fallback)


def _dedupe_keep_order(values: Sequence[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def _build_candidate_templates(
    *,
    template_payload: Dict[str, Any],
    ctx: InputFeedbackContext,
) -> List[str]:
    state_templates = template_payload.get("state_templates") if isinstance(template_payload, dict) else {}
    tone_templates = template_payload.get("tone_templates") if isinstance(template_payload, dict) else {}
    fallback_templates = template_payload.get("fallback_templates") if isinstance(template_payload, dict) else {}

    base_candidates: List[str] = []
    if isinstance(state_templates, dict):
        for key in _state_key_chain(ctx):
            current = _bucket_candidates(state_templates.get(key), strength=ctx.dominant_strength)
            if current:
                base_candidates = current
                break

    tone_candidates: List[str] = []
    if ctx.memo_mode and isinstance(tone_templates, dict):
        tone_candidates = _bucket_candidates(tone_templates.get(ctx.memo_mode), strength=ctx.dominant_strength)

    fallback_candidates = _bucket_candidates(fallback_templates, strength=ctx.dominant_strength)

    if base_candidates and tone_candidates:
        return _dedupe_keep_order(base_candidates + tone_candidates)
    if base_candidates:
        return base_candidates
    if tone_candidates:
        return _dedupe_keep_order(tone_candidates + fallback_candidates)
    return fallback_candidates

def _stable_choice(
    *,
    options: Sequence[str],
    selection_seed: str,
) -> str:
    cleaned = [str(opt or "").strip() for opt in options if str(opt or "").strip()]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    digest = hashlib.sha256(selection_seed.encode("utf-8")).hexdigest()
    index = int(digest[:12], 16) % len(cleaned)
    return cleaned[index]



def _build_observation_comment_from_templates(
    *,
    emotion_details: Sequence[Dict[str, Any]],
    memo: Optional[str],
    memo_action: Optional[str],
    selection_seed: Optional[str] = None,
    template_id: str = DEFAULT_INPUT_FEEDBACK_TEXT_TEMPLATE_ID,
) -> str:
    ctx = _build_context(
        emotion_details=emotion_details,
        memo=memo,
        memo_action=memo_action,
    )
    if ctx is None:
        return ""

    template_payload = get_input_feedback_text_template(template_id=template_id)
    candidates = _build_candidate_templates(
        template_payload=template_payload,
        ctx=ctx,
    )
    if not candidates:
        return ""

    seed_parts = [
        str(selection_seed or "").strip(),
        ctx.dominant_type,
        ctx.dominant_strength,
        ctx.memo_mode,
        ctx.emotion_signature,
        template_id,
    ]
    resolved_seed = "|".join(seed_parts)
    return _stable_choice(options=candidates, selection_seed=resolved_seed)


_EMOTION_FEELING_LABELS: Dict[str, str] = {
    "喜び": "うれしさ",
    "悲しみ": "悲しみ",
    "怒り": "怒り",
    "不安": "不安",
    "平穏": "落ち着き",
}

_EMOTION_RECEIVE_TEMPLATES: Dict[str, Tuple[str, ...]] = {
    "joy": (
        "そのうれしさを受け取ります。",
        "その明るさが戻っていたのですね。",
    ),
    "sadness": (
        "その悲しみを受け取ります。",
        "その悲しさが大きかったのですね。",
    ),
    "anger": (
        "その怒りを受け取ります。",
        "その引っかかりが大きかったのですね。",
    ),
    "anxiety": (
        "その不安を受け取ります。",
        "その気がかりが大きかったのですね。",
    ),
    "calm": (
        "その落ち着きを受け取ります。",
        "その静けさが戻っていたのですね。",
    ),
    "mixed": (
        "その重なりを受け取ります。",
        "その気持ちの重なりがあったのですね。",
    ),
}

_CATEGORY_TOPIC_ANCHORS: Dict[str, str] = {
    "生活": "生活のこと",
    "仕事": "仕事のこと",
    "趣味": "趣味のこと",
    "人間関係": "人間関係のこと",
    "恋愛": "恋愛のこと",
    "健康": "健康のこと",
    "学習": "学びのこと",
    "価値観": "価値観のこと",
    "人生": "人生のこと",
}

_CATEGORY_SELF_INSIGHT_ANCHORS: Dict[str, str] = {
    "生活": "生活の中で",
    "仕事": "仕事の中で",
    "趣味": "趣味の中で",
    "人間関係": "人間関係の中で",
    "恋愛": "恋愛の中で",
    "健康": "健康の中で",
    "学習": "学びの中で",
    "価値観": "価値観の中で",
    "人生": "人生の中で",
}

_SAFE_EXACT_PHRASE_REPLACEMENTS: Dict[str, str] = {
    "たのしかた": "たのしかった",
    "たのしかっt": "たのしかった",
    "かなしかた": "かなしかった",
    "うれしかた": "うれしかった",
    "こわかた": "こわかった",
    "つらかた": "つらかった",
    "しんどかた": "しんどかった",
    "ほんとは": "本当は",
    "ほんとうは": "本当は",
}

_GENERIC_SHORT_PHRASES = {
    "むり",
    "無理",
    "やばい",
    "しんどい",
    "しんどかった",
    "つらい",
    "つらかった",
    "悲しい",
    "悲しかった",
    "かなしかった",
    "不安",
    "不安だった",
    "イライラ",
    "イライラした",
    "嫌",
    "嫌だった",
    "こわい",
    "こわかった",
    "嬉しい",
    "うれしい",
    "うれしかった",
    "楽しかった",
    "たのしかった",
    "疲れた",
    "さみしい",
    "寂しい",
    "もやもや",
}

_SELF_INSIGHT_CUE_RE = re.compile(r"(自分|本当は|と思った|と感じた|と気づいた|と認識した|と理解した|かもしれない)")


def _normalize_categories(raw: Optional[Sequence[str]]) -> Tuple[str, ...]:
    if not raw:
        return ()

    out: List[str] = []
    seen = set()
    for value in raw:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return tuple(out)


def _primary_category(categories: Sequence[str]) -> str:
    for category in categories or ():
        text = str(category or "").strip()
        if text:
            return text
    return ""


def _sanitize_source_text(value: Optional[str]) -> str:
    text = str(value or "")
    text = text.replace("　", " ")
    text = re.sub(r"[ 	]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def _strip_terminal_punctuation(text: str) -> str:
    return str(text or "").strip().rstrip("。！？!?、, ")


def _apply_safe_phrase_replacements(text: str) -> str:
    base = _strip_terminal_punctuation(text)
    if base in _SAFE_EXACT_PHRASE_REPLACEMENTS:
        return _SAFE_EXACT_PHRASE_REPLACEMENTS[base]
    return base


def _combined_source_text(memo: Optional[str], memo_action: Optional[str]) -> str:
    parts = []
    memo_text = _sanitize_source_text(memo)
    memo_action_text = _sanitize_source_text(memo_action)
    if memo_text:
        parts.append(memo_text)
    if memo_action_text:
        parts.append(memo_action_text)
    return "。".join(parts)


def _text_length_bucket(text: str) -> str:
    compact = re.sub(r"\s+", "", str(text or ""))
    length = len(compact)
    if length <= 25:
        return "short"
    if length <= 70:
        return "medium"
    return "long"


def _split_source_clauses(text: str) -> List[str]:
    base = _sanitize_source_text(text)
    if not base:
        return []
    pieces = re.split(r"(?:[。！？!?\n]+|[、,]|けれども|けれど|けど|なのに|のに)", base)
    out: List[str] = []
    seen = set()
    for piece in pieces:
        current = _apply_safe_phrase_replacements(piece)
        current = _strip_terminal_punctuation(current)
        if not current:
            continue
        if current in seen:
            continue
        seen.add(current)
        out.append(current)
    return out


def _looks_like_self_insight(text: str) -> bool:
    return bool(_SELF_INSIGHT_CUE_RE.search(str(text or "")))


def _needs_category_grounding(text: str, *, self_insight: bool) -> bool:
    current = _strip_terminal_punctuation(text)
    if not current:
        return True
    if current in _GENERIC_SHORT_PHRASES:
        return True
    if len(current) <= 4 and not _looks_like_self_insight(current):
        return True
    if self_insight and (len(current) <= 6 and not _looks_like_self_insight(current)):
        return True
    return False


def _pick_repetition_clauses(
    text: str,
    *,
    self_insight: bool,
    bucket: str,
) -> List[str]:
    clauses = _split_source_clauses(text)
    if not clauses:
        return []

    if self_insight:
        cue_clauses = [clause for clause in clauses if _looks_like_self_insight(clause)]
        working = cue_clauses or clauses
    else:
        working = clauses

    if bucket in {"short", "medium"}:
        return working[:1]

    picked: List[str] = []
    first = working[0]
    picked.append(first)
    for clause in reversed(working):
        if clause != first:
            picked.append(clause)
            break
    return picked[:2]


def _category_topic_anchor(category: str) -> str:
    return _CATEGORY_TOPIC_ANCHORS.get(str(category or "").strip(), "")


def _category_self_insight_anchor(category: str) -> str:
    return _CATEGORY_SELF_INSIGHT_ANCHORS.get(str(category or "").strip(), "")


def _is_self_insight_context(ctx: InputFeedbackContext) -> bool:
    return ctx.dominant_type == SELF_INSIGHT_EMOTION_TYPE


def _emotion_label_for_sentence(emotion_type: str) -> str:
    return _EMOTION_FEELING_LABELS.get(str(emotion_type or "").strip(), str(emotion_type or "").strip())


def _sorted_emotion_labels(ctx: InputFeedbackContext) -> List[str]:
    labels = []
    for emotion_type in ctx.emotion_types:
        if emotion_type == SELF_INSIGHT_EMOTION_TYPE:
            continue
        label = _emotion_label_for_sentence(emotion_type)
        if label and label not in labels:
            labels.append(label)
    return labels


def _build_emotion_echo_sentence(ctx: InputFeedbackContext) -> str:
    labels = _sorted_emotion_labels(ctx)
    if not labels:
        return ""
    if len(labels) == 1:
        return f"{labels[0]}があったのですね。"
    if len(labels) == 2:
        return f"{labels[0]}と{labels[1]}が重なっていたのですね。"
    return "いくつかの気持ちが重なっていたのですね。"


def _build_receive_sentence(ctx: InputFeedbackContext, selection_seed: str) -> str:
    key = "mixed" if ctx.multiple else (_emotion_key(ctx.dominant_type) or "mixed")
    candidates = _EMOTION_RECEIVE_TEMPLATES.get(key) or _EMOTION_RECEIVE_TEMPLATES["mixed"]
    return _stable_choice(options=candidates, selection_seed=selection_seed)


def _build_normal_category_fallback(*, category: str, ctx: InputFeedbackContext) -> str:
    anchor = _category_topic_anchor(category)
    if not anchor:
        labels = _sorted_emotion_labels(ctx)
        if labels:
            if len(labels) == 1:
                return f"{labels[0]}が大きかったのですね。"
            if len(labels) == 2:
                return f"{labels[0]}と{labels[1]}が重なっていたのですね。"
        return "いまの気持ちが大きかったのですね。"

    key = "mixed" if ctx.multiple else (_emotion_key(ctx.dominant_type) or "mixed")
    if key == "sadness":
        return f"{anchor}で、悲しさが大きかったのですね。"
    if key == "anxiety":
        return f"{anchor}で、不安が大きかったのですね。"
    if key == "anger":
        return f"{anchor}で、引っかかりが大きかったのですね。"
    if key == "joy":
        return f"{anchor}で、うれしい気持ちがあったのですね。"
    if key == "calm":
        return f"{anchor}で、落ち着きたい気持ちがあったのですね。"
    return f"{anchor}で、いくつかの気持ちが重なっていたのですね。"


def _render_normal_echo_sentence(*, phrase: str, category: str, ctx: InputFeedbackContext) -> str:
    current = _apply_safe_phrase_replacements(phrase)
    current = _strip_terminal_punctuation(current)
    if not current or _needs_category_grounding(current, self_insight=False):
        return _build_normal_category_fallback(category=category, ctx=ctx)
    return f"{current}のですね。"


def _build_self_insight_category_fallback(category: str) -> str:
    anchor = _category_self_insight_anchor(category)
    if anchor:
        return f"{anchor}、自分のことを見つめたのですね。"
    return "自分のことを見つめたのですね。"


def _render_self_insight_echo_sentence(*, phrase: str, category: str) -> str:
    current = _apply_safe_phrase_replacements(phrase)
    current = _strip_terminal_punctuation(current)
    anchor = _category_self_insight_anchor(category)
    prefix = f"{anchor}、" if anchor else ""

    if not current or _needs_category_grounding(current, self_insight=True):
        return _build_self_insight_category_fallback(category)

    if current.startswith("自分は"):
        if re.search(r"(と思った|と感じた|と気づいた|と認識した|と理解した)$", current):
            return f"{prefix}{current}のですね。"
        if current.endswith("かもしれない"):
            return f"{prefix}{current}と感じたのですね。"
        return f"{prefix}{current}と認識したのですね。"

    if current.startswith("本当は"):
        if re.search(r"(と思った|と感じた|と気づいた)$", current):
            return f"{prefix}{current}のですね。"
        return f"{prefix}{current}のだと気づいたのですね。"

    if re.search(r"(と思った|と感じた|と気づいた|と認識した|と理解した)$", current):
        return f"{prefix}{current}のですね。"

    return f"{prefix}{current}と感じたのですね。"


def _build_normal_agreement_sentence(*, phrase: str, category: str, ctx: InputFeedbackContext) -> str:
    category_anchor = _category_topic_anchor(category)
    key = "mixed" if ctx.multiple else (_emotion_key(ctx.dominant_type) or "mixed")

    if category_anchor:
        if key == "joy":
            return f"{category_anchor}だと、うれしくなりますよね。"
        if key == "sadness":
            return f"{category_anchor}だと、悲しく感じますよね。"
        if key == "anxiety":
            return f"{category_anchor}だと、不安になりますよね。"
        if key == "anger":
            return f"{category_anchor}だと、引っかかりも残りますよね。"
        if key == "calm":
            return f"{category_anchor}だと、ほっとしますよね。"
        return f"{category_anchor}だと、気持ちが揺れますよね。"

    if key == "joy":
        return "そう感じるとうれしいですよね。"
    if key == "sadness":
        return "そう感じるのは自然ですよね。"
    if key == "anxiety":
        return "そう不安になるのも自然ですよね。"
    if key == "anger":
        return "そう引っかかるのも自然ですよね。"
    if key == "calm":
        return "そういうときは、ほっとしますよね。"
    return "いくつかの気持ちが重なることもありますよね。"


def _build_self_insight_receive_sentence(*, phrase: str, selection_seed: str) -> str:
    current = _strip_terminal_punctuation(phrase)
    if "本当は" in current or "気づ" in current:
        candidates = (
            "そうやって自分の状態を受け取ったのですね。",
            "その気づきを言葉にしたのですね。",
        )
    elif current.startswith("自分は"):
        candidates = (
            "そうやって自分を理解したのですね。",
            "そうやって自分の反応を見つめたのですね。",
        )
    else:
        candidates = (
            "そうやって自分を見つめたのですね。",
            "その見方を言葉にしたのですね。",
        )
    return _stable_choice(options=candidates, selection_seed=selection_seed)


def _build_self_insight_agreement_sentence(*, phrase: str, category: str) -> str:
    current = _strip_terminal_punctuation(phrase)
    if "本当は" in current or "気づ" in current:
        return "そこに気づくのは重たいことですよね。"
    if current.startswith("自分は") or _looks_like_self_insight(current):
        return "そう認識するのは自然ですよね。"
    anchor = _category_self_insight_anchor(category)
    if anchor:
        return f"{anchor}で、そう感じることもありますよね。"
    return "そう理解したくなるのも無理はないですよね。"


def _build_long_summary_sentence(*, ctx: InputFeedbackContext, self_insight: bool, clause_count: int) -> str:
    if clause_count <= 1:
        return ""
    if self_insight:
        return "その見方が、自分の中で大きかったのですね。"
    if ctx.multiple:
        return "いくつかの気持ちが重なっていたのですね。"
    return "その出来事が、大きく残っていたのですね。"


def _ensure_sentence(text: str) -> str:
    current = str(text or "").strip()
    if not current:
        return ""
    if current[-1] not in "。！？!?":
        current = f"{current}。"
    return current


def _smooth_repeated_endings(sentences: List[str]) -> List[str]:
    out: List[str] = []
    prev = ""
    prev_prev = ""
    for sentence in sentences:
        current = _ensure_sentence(sentence)
        if not current:
            continue

        if prev.endswith("のですね。") and current.endswith("のですね。"):
            current = current.replace("があったのですね。", "があったようですね。")
            current = current.replace("が重なっていたのですね。", "が重なっていたようですね。")
            if current.endswith("のですね。"):
                current = current[:-5] + "ようですね。"

        if prev.endswith("ですよね。") and current.endswith("ですよね。"):
            if "自然ですよね。" not in current:
                current = current[:-5] + "のも自然ですよね。"
            else:
                current = current[:-5] + "こともありますよね。"

        if prev.endswith("受け取ります。") and current.endswith("受け取ります。"):
            current = current.replace("受け取ります。", "があったのですね。")

        if prev_prev and prev_prev == current:
            continue

        out.append(current)
        prev_prev = prev
        prev = current
    return out


def _dedupe_semantically_close_sentences(sentences: List[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for sentence in sentences:
        normalized = re.sub(r"[。！？!?、,\s]", "", sentence)
        normalized = normalized.replace("ようですね", "のですね")
        normalized = normalized.replace("自然ですよね", "ですよね")
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        out.append(sentence)
    return out


def _render_feedback_parts(parts: Sequence[InputFeedbackSentence]) -> str:
    sentences = [part.text for part in parts if str(part.text or "").strip()]
    sentences = _dedupe_semantically_close_sentences(sentences)
    sentences = _smooth_repeated_endings(sentences)
    return "".join(sentences).strip()


def _build_normal_feedback_parts(
    *,
    ctx: InputFeedbackContext,
    memo: Optional[str],
    memo_action: Optional[str],
    categories: Sequence[str],
    selection_seed: str,
    observation_comment: str,
) -> List[InputFeedbackSentence]:
    parts: List[InputFeedbackSentence] = []
    source_text = _combined_source_text(memo, memo_action)
    primary_category = _primary_category(categories)

    if source_text:
        bucket = _text_length_bucket(source_text)
        clauses = _pick_repetition_clauses(source_text, self_insight=False, bucket=bucket)
        for clause in clauses:
            sentence = _render_normal_echo_sentence(phrase=clause, category=primary_category, ctx=ctx)
            if sentence:
                parts.append(InputFeedbackSentence(role="echo", text=sentence))

        emotion_sentence = _build_emotion_echo_sentence(ctx)
        if emotion_sentence:
            parts.append(InputFeedbackSentence(role="emotion", text=emotion_sentence))

        if bucket == "long":
            summary_sentence = _build_long_summary_sentence(
                ctx=ctx,
                self_insight=False,
                clause_count=len(clauses),
            )
            if summary_sentence:
                parts.append(InputFeedbackSentence(role="summary", text=summary_sentence))

        agreement_phrase = clauses[-1] if clauses else source_text
        agreement_sentence = _build_normal_agreement_sentence(
            phrase=agreement_phrase,
            category=primary_category,
            ctx=ctx,
        )
        if agreement_sentence:
            parts.append(InputFeedbackSentence(role="agreement", text=agreement_sentence))
    else:
        emotion_sentence = _build_emotion_echo_sentence(ctx)
        if emotion_sentence:
            parts.append(InputFeedbackSentence(role="emotion", text=emotion_sentence))
        receive_sentence = _build_receive_sentence(ctx, selection_seed)
        if receive_sentence:
            parts.append(InputFeedbackSentence(role="receive", text=receive_sentence))

    if observation_comment:
        parts.append(InputFeedbackSentence(role="observation", text=observation_comment))

    return parts


def _build_self_insight_feedback_parts(
    *,
    ctx: InputFeedbackContext,
    memo: Optional[str],
    memo_action: Optional[str],
    categories: Sequence[str],
    selection_seed: str,
) -> List[InputFeedbackSentence]:
    parts: List[InputFeedbackSentence] = []
    source_text = _combined_source_text(memo, memo_action)
    primary_category = _primary_category(categories)
    bucket = _text_length_bucket(source_text) if source_text else "short"
    clauses = _pick_repetition_clauses(source_text, self_insight=True, bucket=bucket)

    if clauses:
        first_sentence = _render_self_insight_echo_sentence(phrase=clauses[0], category=primary_category)
        if first_sentence:
            parts.append(InputFeedbackSentence(role="echo", text=first_sentence))
        if bucket == "long" and len(clauses) >= 2:
            second_sentence = _render_self_insight_echo_sentence(phrase=clauses[-1], category="")
            if second_sentence and second_sentence != first_sentence:
                parts.append(InputFeedbackSentence(role="echo", text=second_sentence))
    else:
        parts.append(
            InputFeedbackSentence(
                role="echo",
                text=_build_self_insight_category_fallback(primary_category),
            )
        )

    key_phrase = clauses[-1] if clauses else source_text
    receive_sentence = _build_self_insight_receive_sentence(
        phrase=key_phrase,
        selection_seed=selection_seed,
    )
    if receive_sentence:
        parts.append(InputFeedbackSentence(role="receive", text=receive_sentence))

    if bucket == "long":
        summary_sentence = _build_long_summary_sentence(
            ctx=ctx,
            self_insight=True,
            clause_count=len(clauses),
        )
        if summary_sentence:
            parts.append(InputFeedbackSentence(role="summary", text=summary_sentence))

    agreement_sentence = _build_self_insight_agreement_sentence(
        phrase=key_phrase,
        category=primary_category,
    )
    if agreement_sentence:
        parts.append(InputFeedbackSentence(role="agreement", text=agreement_sentence))

    return parts


def build_input_feedback_comment(
    *,
    emotion_details: Sequence[Dict[str, Any]],
    memo: Optional[str],
    memo_action: Optional[str],
    category: Optional[Sequence[str]] = None,
    selection_seed: Optional[str] = None,
    template_id: str = DEFAULT_INPUT_FEEDBACK_TEXT_TEMPLATE_ID,
) -> str:
    ctx = _build_context(
        emotion_details=emotion_details,
        memo=memo,
        memo_action=memo_action,
    )
    if ctx is None:
        return ""

    categories = _normalize_categories(category)
    resolved_seed = "|".join(
        [
            str(selection_seed or "").strip(),
            ctx.dominant_type,
            ctx.dominant_strength,
            ctx.memo_mode,
            ctx.emotion_signature,
            template_id,
            ",".join(categories),
        ]
    )

    if _is_self_insight_context(ctx):
        parts = _build_self_insight_feedback_parts(
            ctx=ctx,
            memo=memo,
            memo_action=memo_action,
            categories=categories,
            selection_seed=resolved_seed,
        )
        return _render_feedback_parts(parts)

    observation_comment = _build_observation_comment_from_templates(
        emotion_details=emotion_details,
        memo=memo,
        memo_action=memo_action,
        selection_seed=selection_seed,
        template_id=template_id,
    )
    parts = _build_normal_feedback_parts(
        ctx=ctx,
        memo=memo,
        memo_action=memo_action,
        categories=categories,
        selection_seed=resolved_seed,
        observation_comment=observation_comment,
    )
    return _render_feedback_parts(parts)
