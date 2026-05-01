# -*- coding: utf-8 -*-
"""self_structure_section_text_templates.py (Phase9+)

目的
----
- MyProfile（月次）自己構造分析レポートの「各セクション文言（固定文）」を
  template_id で差し替え可能にする。
- ASTOR（ルールベース組み立て）側の固定文を辞書化し、文面チューニングを
  サーバ更新だけで回しやすくする。

設計
----
- template_id -> phrases(dict) のレジストリ。
- 既存互換を守るため、デフォルト（myprofile_sections_ja_v1）は
  現行の固定文と同等の表現を収録する。
- template は "差分" だけ定義してもよい（default を deep merge して補完）。

注意
----
- ここは /mymodel/infer の prompt テンプレとは別物（レポート本文の固定文）。
- ここを変えると、過去レポートとの差分抽出に影響する可能性があるため、
  summary_title（【要点（答え）】）だけは大きく崩しすぎないのがおすすめ。
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Dict, List


DEFAULT_MYPROFILE_SECTION_TEXT_TEMPLATE_ID = "myprofile_sections_ja_v1"


@dataclass(frozen=True)
class MyProfileSectionTemplateInfo:
    template_id: str
    description: str


# NOTE: テンプレは "差分" だけでもOK。get_* で default と deep merge して補完する。
_MYPROFILE_SECTION_TEMPLATES: Dict[str, Dict[str, Any]] = {
    # --- Default (互換) ---
    DEFAULT_MYPROFILE_SECTION_TEXT_TEMPLATE_ID: {
        # header / summary
        "report_title": "【自己分析レポート】",
        "error_no_user_id": "（ユーザーIDが指定されていないため生成できませんでした）",
        "summary_title": "【要点（答え）】",
        "summary_title_current": "【最近のあなたに見えている役割】",
        "summary_disclaimer_current": "",
        "sec_role_title": "最近の入力から見える役割",
        "sec_background_title": "そうなりやすい背景",
        "sec_flow_title": "反応しやすい場面",
        "sec_emotion_title": "気持ちとのつながり",
        "sec_change_title": "前回から少し変わったところ",
        "summary_disclaimer": "",
        "summary_core": "・最近よく見えているテーマ: {themes}",
        "summary_core_no_data": "・最近よく見えているテーマ: まだ情報がありません",
        "summary_shaky_with_emotions": "・揺れやすい場面: {emotions}が強いとき、判断が硬くなりやすい可能性",
        "summary_shaky_default": "・揺れやすい場面: いくつかのきっかけが重なると、受け止め方が固定されやすい可能性",
        "summary_shaky_no_data": "・揺れやすい場面: まだ情報がありません",
        "summary_steady_deep": "・整える1手: 判断の前に『基準を1行だけ言語化』すると、気持ちを戻しやすい",
        "summary_steady_default": "・整える1手: 揺れた瞬間に「考えたこと1文」「動いたこと1文」を分けて書くと、迷いがほどけやすい",
        "summary_steady_no_data": "・整える1手: まずは短いメモを増やす",
        "summary_one_liner": "・ひとこと: いまは『{core_key}』に近い反応が出やすい状態。判断が硬くなる前に“1行メモ”が効きやすい。",
        "summary_one_liner_no_data": "・ひとこと: まだ入力が少ないため、レポートは簡易版です。短文でOKなので『きっかけ→受け止め方→気持ち→行動』を1セットだけ記録してみてください。",

        # section 1
        "sec1_title": "1. 最近のあなたに見えている役割",
        "sec1_no_data_lines": [
            "まだ入力が少ないため、はっきりした傾向は読み取りきれていません。",
            "短文で大丈夫なので、感情入力やメモ（きっかけ・受け止め方・気持ち・行動）が増えると、次回以降のレポートが具体的になります。",
        ],
        "sec1_core_line_with_gloss": "『{core_key}』に近い反応が出やすく（意味: {gloss}）、判断の起点になっている可能性があります。",
        "sec1_core_line": "『{core_key}』に近い反応が出やすく、判断の起点になっている可能性があります。",
        "sec1_secondary_line": "さらに『{secondary_key}』も重なると、見立てが揺れた瞬間に反応が強く出やすい可能性があります。",
        "sec1_note_line": "",

        # section 2
        "sec2_title": "2. 反応のパターン",
        "sec2_no_data_lines": [
            "反応パターンを特定できるほどの情報は、まだ十分ではありません。",
            "次の4点を、1回だけでもメモしてみてください（短文でOKです）。",
            "・きっかけ（何が起きたか）",
            "・受け止め方（どう受け取ったか）",
            "・感情（何を感じたか）",
            "・行動（どうしたか）",
        ],
        "sec2_pattern_title": "- パターン{index}: 『{structure_key}』",
        "sec2_pattern_flow": "  変化: きっかけ → 受け止め方 → 気持ち → 行動",
        "sec2_pattern_stimulus": "  きっかけ: （例）評価/比較/期待のズレ/未確定など、『{structure_key}』を強めやすい出来事",
        "sec2_pattern_cognition": "  受け止め方: 『{structure_key}』に近い判断が入り、意味づけが固定されやすい",
        "sec2_pattern_emotion": "  感情: {emotion_hint} に寄りやすい",
        "sec2_pattern_action": "  行動: 確認/修正へ向かう、または一時停止して距離を取る",
        "sec2_pattern_memo": "  メモ（例）: {memo}",

        # section 3
        "sec3_title": "3. 安心しやすい場面 / 揺れやすい場面",
        "sec3_stable_heading": "安心しやすい場面:",
        "sec3_shaky_heading": "揺れやすい場面:",
        "sec3_stable_line_1": "・揺れた瞬間に「考えたこと」と「動いたこと」を分けて短文で書けたとき",
        "sec3_stable_line_3": "・忙しい日は短文でもいいのでメモだけは継続できる",
        "sec3_shaky_line_top": "・『{structure_key}』が{intensity_label}で出ている日に、判断が硬直しやすい",
        "sec3_shaky_line_default": "・未確定/比較/評価が重なる場面で、解釈が一気に固定されやすい（視野が狭くなりやすい）",

        # section 4
        "sec4_title": "4. 受け止め方のクセ（あれば）",
        "sec4_no_data_lines": [
            "受け止め方のクセが見えるほどの情報は、まだ十分ではありません。",
            "気づいたときに「考えたこと（1文）」を残すと、次回以降で傾向が見えやすくなります。",
        ],
        "sec4_line_1": "・『{core_key}』が上位に出ているため、判断の起点が“評価/意味づけ”に寄りやすい可能性があります。",
        "sec4_line_2": "・『{secondary_key}』が重なると、白黒を急がず“仮置き”するのが難しくなることがあります。",
        "sec4_line_3": "・対策としては、結論を急がず、見えていることを1行ずつ書き出すのが有効です。",

        # section 5
        "sec5_title": "5. 領域別メモ（仕事/対人/孤独/挑戦/評価など、見えている範囲で）",
        "sec5_domains": ["仕事", "対人", "孤独", "挑戦", "評価"],
        "sec5_domain_with_hints": "- {domain}: 『{hints_joined}』が絡む場面で反応が出やすい可能性",
        "sec5_domain_no_hints": "- {domain}: まだ傾向を判断できるほどの情報がありません。",

        # section 6
        "sec6_title": "6. 次に見てみるポイント（3つ。行動に落ちる形で）",
        "sec6_lines": [
            "・揺れた瞬間に「考えたこと（1文）」と「動いたこと（1文）」を分けて書く",
            "・止まった日は「できなかった」「固まった」も行動として書く",
            "・月に1回だけでいいので「今の暫定結論（1行）」を残す",
        ],

        # section 7
        "sec7_title": "7. 前回との差分（変化点 / 更新点 / 揺れ方の違い）",
        "diff_summary_title": "【前回から見えている変化】",
        "diff_core_compare": "・中心に見えている反応: 前回 {prev} / 今回 {cur}",
        "diff_center_move": "・中心に見えている反応: 『{prev}』→『{cur}』へ少し移っている可能性",
        "diff_center_same": "・中心に見えている反応: 『{cur}』が続いている可能性",
        "diff_center_cur_is_core": "・中心に見えている反応: 今回は『{cur}』が目立っている可能性",
        "diff_center_unknown": "・中心に見えている反応: まだ入力が少ないため、まとまりきっていません",
        "diff_shaky_compare": "・揺れやすい場面: 前回 {prev} / 今回 {cur}",
        "diff_steady_compare": "・安心しやすい場面: 前回 {prev} / 今回 {cur}",
        "diff_new_key": "・新しく目立ち始めた: 『{key}』",
        "diff_faded_key": "・落ち着いた可能性: 『{key}』",
        "diff_data_line": "・データ差分: 『{key}』が{sign}（回数 {count:+d} / 強度差 {intensity:+.1f}）",
        "diff_no_data": "前回と今回の入力が少ないため、差分はまだまとめられません。",
        "diff_prev_missing": "前回は入力が少なく、今回から傾向が見え始めている状態です。",
        "diff_delta_line": "・『{key}』が{sign}（出現回数の差分: {count:+d} / 強度差: {intensity:+.1f}）",
        "diff_no_major": "大きな差分は目立たず、近い出方が続いています。",

        # section 8
        # NOTE: ユーザー向け本文では内部名（MyWeb 等）を出さない
        "sec8_title": "8. 感情の動きとの接続（短く）",
        "sec8_with_top_line_1": "不安/怒りなどの揺れが目立つとき、背景で『{core_key}』に近い反応が出ている可能性があります。",
        "sec8_with_top_line_2": "気持ちの“天気”と、自分の受け止め方のクセを分けて見るほど、回復が速くなります。",
        "sec8_no_data_line": "感情の揺れが見えたら、“きっかけ→受け止め方”のメモを増やすと、つながりが見えやすくなります。",
    },

    # --- Variant examples (差分だけ) ---
    "myprofile_sections_ja_gentle_v1": {
        # 例: トーンだけ少し柔らかく
        "summary_disclaimer": "",
        "sec6_title": "6. 次に見てみるポイント（できそうなものからでOK）",
    },

    "myprofile_sections_ja_compact_v1": {
        # 例: いくつか短縮（必要ならここを増やす）
        "sec2_pattern_stimulus": "  刺激: （例）評価/比較/未確定など、『{structure_key}』を強めやすい出来事",
        "sec3_title": "3. 安心しやすい場面 / 揺れやすい場面",
        "sec8_title": "8. 感情の動きとの接続（短く）",
    },
}


_TEMPLATE_INFOS: Dict[str, MyProfileSectionTemplateInfo] = {
    DEFAULT_MYPROFILE_SECTION_TEXT_TEMPLATE_ID: MyProfileSectionTemplateInfo(
        template_id=DEFAULT_MYPROFILE_SECTION_TEXT_TEMPLATE_ID,
        description="MyProfile（月次）固定文テンプレ（互換・標準）",
    ),
    "myprofile_sections_ja_gentle_v1": MyProfileSectionTemplateInfo(
        template_id="myprofile_sections_ja_gentle_v1",
        description="MyProfile（月次）固定文テンプレ（やわらかめ）",
    ),
    "myprofile_sections_ja_compact_v1": MyProfileSectionTemplateInfo(
        template_id="myprofile_sections_ja_compact_v1",
        description="MyProfile（月次）固定文テンプレ（短め）",
    ),
}


def list_myprofile_section_text_templates() -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for tid, info in sorted(_TEMPLATE_INFOS.items(), key=lambda kv: kv[0]):
        out.append({"template_id": info.template_id, "description": info.description})
    return out


def _deep_merge(dst: Dict[str, Any], src: Dict[str, Any]) -> Dict[str, Any]:
    for k, v in (src or {}).items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            _deep_merge(dst[k], v)  # type: ignore[index]
        else:
            dst[k] = v
    return dst


def get_myprofile_section_phrases(template_id: str) -> Dict[str, Any]:
    """Return phrases dict for template_id. Always returns a fully-populated dict."""
    tid = str(template_id or "").strip() or DEFAULT_MYPROFILE_SECTION_TEXT_TEMPLATE_ID

    base = copy.deepcopy(_MYPROFILE_SECTION_TEMPLATES[DEFAULT_MYPROFILE_SECTION_TEXT_TEMPLATE_ID])
    if tid != DEFAULT_MYPROFILE_SECTION_TEXT_TEMPLATE_ID and tid in _MYPROFILE_SECTION_TEMPLATES:
        _deep_merge(base, copy.deepcopy(_MYPROFILE_SECTION_TEMPLATES[tid]))
    return base


def safe_format(template: str, **kwargs: Any) -> str:
    """Safe str.format: never throws."""
    try:
        return str(template or "").format(**kwargs)
    except Exception:
        return str(template or "")
