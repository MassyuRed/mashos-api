# -*- coding: utf-8 -*-
"""myprofile_section_text_templates.py (Phase9+)

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
        "report_title": "【自己構造分析レポート（月次）】",
        "error_no_user_id": "（ユーザーIDが指定されていないため生成できませんでした）",
        "summary_title": "【要点（答え）】",
        "summary_disclaimer": "※診断ではなく、観測に基づく仮説です。",
        "summary_core": "・核（いちばん出やすい自己テーマ）: {themes}",
        "summary_core_no_data": "・核（いちばん出やすい自己テーマ）: まだ情報がありません",
        "summary_shaky_with_emotions": "・崩れ条件（揺れを強めやすい引き金）: {emotions}が強い場面で、判断が硬くなりやすい可能性",
        "summary_shaky_default": "・崩れ条件（揺れを強めやすい引き金）: 刺激が重なった場面で、意味づけが固定されやすい可能性",
        "summary_shaky_no_data": "・崩れ条件（揺れを強めやすい引き金）: まだ情報がありません",
        "summary_steady_deep": "・安定に寄せるキー（整える1手）: 判断の前に『基準を1行だけ言語化』すると、構造の暴走が収まりやすい",
        "summary_steady_default": "・安定に寄せるキー（整える1手）: 『刺激/解釈/身体』を1行メモすると、揺れがほどけやすい",
        "summary_steady_no_data": "・安定に寄せるキー（整える1手）: まずは短い観測メモを増やす",
        "summary_one_liner": "・ひとこと: いまは『{core_key}』が起点になりやすい状態。判断が硬くなる前に“1行メモ”が効きやすい。",
        "summary_one_liner_no_data": "・ひとこと: 今月は入力が少ないため、レポートは簡易版です。短文でOKなので『刺激→解釈→感情→行動』を1セットだけ記録してみてください。",

        # section 1
        "sec1_title": "1. 今月の輪郭（仮説・1〜4行）",
        "sec1_no_data_lines": [
            "今月は入力が少ないため、はっきりした傾向はまだ読み取れません。",
            "短文で大丈夫なので、感情入力やメモ（刺激・解釈・感情・行動）が増えると、次回以降のレポートが具体的になります。",
        ],
        "sec1_core_line_with_gloss": "核として『{core_key}』が出やすく（意味: {gloss}）、判断の起点になっている可能性があります。",
        "sec1_core_line": "核として『{core_key}』が出やすく、判断の起点になっている可能性があります。",
        "sec1_secondary_line": "さらに『{secondary_key}』が重なると、見立てが揺れた瞬間に構造が濃くなりやすい可能性があります。",
        "sec1_note_line": "※これは診断ではなく、最近の入力から読み取れる“仮の自己モデル”です。",

        # section 2
        "sec2_title": "2. 主要な反応パターン（刺激→認知→感情→行動）",
        "sec2_no_data_lines": [
            "今月は反応パターンを特定できるほどの情報がありません。",
            "次の4点を、1回だけでもメモしてみてください（短文でOKです）。",
            "・刺激（何が起きたか）",
            "・認知（どう解釈したか）",
            "・感情（何を感じたか）",
            "・行動（どうしたか）",
        ],
        "sec2_pattern_title": "- パターン{index}: 『{structure_key}』",
        "sec2_pattern_flow": "  流れ: 刺激 → 認知 → 感情 → 行動",
        "sec2_pattern_stimulus": "  刺激: （例）評価/比較/期待のズレ/未確定など、『{structure_key}』を強めやすい出来事",
        "sec2_pattern_cognition": "  認知: （仮）『{structure_key}』の判断が入り、意味づけが固定されやすい",
        "sec2_pattern_emotion": "  感情: {emotion_hint} に寄りやすい",
        "sec2_pattern_action": "  行動: （仮）確認/修正へ向かう、または一時停止して距離を取る",
        "sec2_pattern_memo": "  観測メモ（例）: {memo}",

        # section 3
        "sec3_title": "3. 安定条件（安心が生まれやすい条件） / 崩れ条件（揺れやすい条件）",
        "sec3_stable_heading": "安定条件:",
        "sec3_shaky_heading": "崩れ条件:",
        "sec3_stable_line_1": "・判断の前に『刺激/解釈/身体』を1行で切り分けられる",
        "sec3_stable_line_deep": "・Deep Insight の回答で自分の基準を言語化できているとき",
        "sec3_stable_line_3": "・忙しい日は短文でもいいので“観測”だけは継続できる",
        "sec3_shaky_line_top": "・『{structure_key}』が{intensity_label}で出ている日に、判断が硬直しやすい",
        "sec3_shaky_line_default": "・未確定/比較/評価が重なる場面で、解釈が一気に固定されやすい（視野が狭くなりやすい）",

        # section 4
        "sec4_title": "4. 思考のクセ・判断のクセ（あれば）",
        "sec4_no_data_lines": [
            "今月は思考のクセが見えるほどの情報がありません。",
            "気づいたときに「考えたこと（1文）」を残すと、次回以降で傾向が見えやすくなります。",
        ],
        "sec4_line_1": "・『{core_key}』が上位に出ているため、判断の起点が“評価/意味づけ”に寄りやすい可能性があります。",
        "sec4_line_2": "・『{secondary_key}』が重なると、白黒を急がず“仮置き”するのが難しくなることがあります。",
        "sec4_line_3": "・対策としては、結論を急がず『観測→仮説』の順に戻すのが有効です。",

        # section 5
        "sec5_title": "5. 領域別メモ（仕事/対人/孤独/挑戦/評価など、見えている範囲で）",
        "sec5_domains": ["仕事", "対人", "孤独", "挑戦", "評価"],
        "sec5_domain_with_hints": "- {domain}: 『{hints_joined}』が絡む場面で自己モデルが動きやすい可能性",
        "sec5_domain_no_hints": "- {domain}: 今月はまだ傾向を判断できません。",

        # section 6
        "sec6_title": "6. 次の観測ポイント（3つ。行動に落ちる形で）",
        "sec6_lines": [
            "・揺れた瞬間に『何が刺激だったか』を1語で書く",
            "・その刺激を『どう解釈したか（1文）』を書いてから、感情ラベルを選ぶ",
            "・強い日は『身体（睡眠/空腹/疲労）』も一緒にメモして、構造と身体を分けて観測する",
        ],

        # section 7
        "sec7_title": "7. 前回との差分（変化点 / 更新点 / 揺れ方の違い）",
        "diff_summary_title": "【差分の要約（前回→今回）】",
        "diff_core_compare": "・核の要点: 前回 {prev} / 今回 {cur}",
        "diff_center_move": "・中心テーマ: 『{prev}』→『{cur}』へ移動した可能性",
        "diff_center_same": "・中心テーマ: 『{cur}』が継続している可能性",
        "diff_center_cur_is_core": "・中心テーマ: 今回は『{cur}』が核になっている可能性",
        "diff_center_unknown": "・中心テーマ: 今月は入力が少ないため、中心テーマはまだ特定できません",
        "diff_shaky_compare": "・崩れ条件: 前回 {prev} / 今回 {cur}",
        "diff_steady_compare": "・安定条件: 前回 {prev} / 今回 {cur}",
        "diff_new_key": "・新しく目立ち始めた: 『{key}』",
        "diff_faded_key": "・落ち着いた可能性: 『{key}』",
        "diff_data_line": "・データ差分: 『{key}』が{sign}（回数 {count:+d} / 強度差 {intensity:+.1f}）",
        "diff_no_data": "前回と今回の入力が少ないため、差分はまだまとめられません。",
        "diff_prev_missing": "前回は入力が少なく、今月から傾向が見え始めている状態です。",
        "diff_delta_line": "・『{key}』が{sign}（出現回数の差分: {count:+d} / 強度差: {intensity:+.1f}）",
        "diff_no_major": "大きな差分は目立たず、構造は安定して推移しています。",

        # section 8
        "sec8_title": "8. 感情構造との接続（MyWebに譲る前提で、短く）",
        "sec8_with_top_line_1": "MyWebで感情の揺れ（不安/怒りなど）が目立つとき、背景で『{core_key}』が立っている可能性があります。",
        "sec8_with_top_line_2": "感情の“天気”と、自己構造の“地形”を分けて見るほど、回復が速くなります。",
        "sec8_no_data_line": "MyWeb（感情傾向）で揺れが見えたら、MyProfile側で“刺激→解釈”の観測を増やすと接続が強くなります。",
    },

    # --- Variant examples (差分だけ) ---
    "myprofile_sections_ja_gentle_v1": {
        # 例: トーンだけ少し柔らかく
        "summary_disclaimer": "※これは診断ではなく、最近の入力からの仮説です。",
        "sec6_title": "6. 次の観測ポイント（できそうなものからでOK）",
    },

    "myprofile_sections_ja_compact_v1": {
        # 例: いくつか短縮（必要ならここを増やす）
        "sec2_pattern_stimulus": "  刺激: （例）評価/比較/未確定など、『{structure_key}』を強めやすい出来事",
        "sec3_title": "3. 安定条件 / 崩れ条件",
        "sec8_title": "8. MyWebとの接続（短く）",
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
