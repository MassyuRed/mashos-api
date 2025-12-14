# -*- coding: utf-8 -*-
"""
Cocolon MyModel Inference API (Release-oriented)
------------------------------------------------
- POST /mymodel/infer : structure-first, privacy-preserving response
- GET  /healthz      : health check
Notes:
- No conversational memory (stateless)
- Rejects date-like/temporal queries and under-informative prompts
- Does NOT persist user content (privacy by design)
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Literal, Tuple

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from structure_dict import build_structure_answer
from api_emotion_submit import (
    register_emotion_submit_routes,
    _extract_bearer_token,
    _resolve_user_id_from_token,
)
from astor_myprofile_persona import build_persona_context_payload
from astor_myweb_insight import generate_myweb_insight_text
from astor_core import AstorEngine, AstorRequest, AstorMode

APP_NAME = os.getenv("MYMODEL_APP_NAME", "Cocolon MyModel")
PORT = int(os.getenv("MYMODEL_PORT", "8765"))
HOST = os.getenv("MYMODEL_HOST", "0.0.0.0")
# For release, set MYMODEL_CORS_ORIGINS to a comma-separated list of allowed origins.
ALLOWED_ORIGINS_RAW = os.getenv("MYMODEL_CORS_ORIGINS", "*")
ALLOWED_ORIGINS = [o.strip() for o in ALLOWED_ORIGINS_RAW.split(",")] if ALLOWED_ORIGINS_RAW else ["*"]

# ---------- App ----------
app = FastAPI(title=APP_NAME, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_emotion_submit_routes(app)

# ASTOR engine for MyWeb insight (構造分析レポート用)
astor_myweb_engine = AstorEngine()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("mymodel")

# ---------- Models ----------
class InputPayload(BaseModel):
    period: Optional[str] = Field(default="30d", description="分析対象期間（例: 7d/30d/12w/3m）")
    ratios: Optional[Dict[str, float]] = Field(default=None, description="感情別割合（例: {'Sadness':0.4,'Calm':0.2}）")
    time_bias: Optional[List[str]] = Field(default=None, description="時間帯バイアス（例: ['morning','evening']）")
    hot_words: Optional[List[str]] = Field(default=None, description="観測語（例: ['孤独','疲労']）")

class InferRequest(BaseModel):
    instruction: str = Field(..., min_length=4, description="一問一答の照会文（時系列を含まないこと）")
    input: Optional[InputPayload] = Field(default=None, description="分析の補助特徴量（省略可）")
    target: Optional[Literal["self", "external"]] = Field(default="self", description="自己/他者（外部）")
    user_id: Optional[str] = Field(default=None, description="ASTOR連携用のユーザーID（任意）")


class InferResponse(BaseModel):
    output: str
    meta: Dict[str, Any] = {}


# ---------- Rules & Utilities ----------
DATE_WORDS = re.compile(r"(いつ|何日|何時|何年度|何年|昨日|明日|先週|来週|先月|来月|去年|来年)")
ISO_DATE = re.compile(r"\b\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2}\b")
JP_DATE = re.compile(r"\b\d{1,2}\s*月\s*\d{1,2}\s*日\b")
MD_DATE = re.compile(r"\b\d{1,2}[-/]\d{1,2}\b")

def contains_date_like(text: str) -> bool:
    return bool(ISO_DATE.search(text) or JP_DATE.search(text) or MD_DATE.search(text) or DATE_WORDS.search(text))

def load_default_features() -> Dict[str, Any]:
    """Attempt to load default features from common repo layouts."""
    candidates = [
        Path(__file__).parent / "ai" / "data" / "processed" / "features.json",           # repo root/ai/...
        Path(__file__).parent / "mashos" / "ai" / "data" / "processed" / "features.json",# repo root/mashos/ai/...
        Path.cwd() / "ai" / "data" / "processed" / "features.json",
        Path.cwd() / "mashos" / "ai" / "data" / "processed" / "features.json",
    ]
    for p in candidates:
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning("Failed to read features.json at %s: %s", p, e)
    # Safe fallback
    return {"period": "30d", "ratios": {"Calm": 0.34, "Joy": 0.24, "Sadness": 0.22, "Anxiety": 0.20}}

def top_emotions(ratios: Dict[str, float], n: int = 2) -> List[str]:
    return [k for k, _ in sorted(ratios.items(), key=lambda kv: kv[1], reverse=True)[:n]] if ratios else []

def intensity_from_len(text: str) -> str:
    n = len(re.sub(r"\s+", "", text))
    return "強い" if n > 60 else "中程度の" if n > 30 else "弱い"


def compose_response(instr: str, payload: Optional[InputPayload], target: str, persona_ctx: Optional[Dict[str, Any]] = None) -> str:
    """
    完全人格型の応答。
    - 一問一答だが会話的な口調
    - 数値や割合の列挙を避け、人格としての「私」が感じ取ったことを伝える
    - 診断・断定はせず、相対的・非断定的に述べる
    """
    import os
    features = payload.dict() if payload else {}
    defaults = load_default_features()

    # 参照可能な特徴（なければ既定）
    ratios = features.get("ratios") or defaults.get("ratios") or {}
    period = features.get("period") or defaults.get("period") or "30d"
    time_bias = features.get("time_bias") or []
    hot_words = features.get("hot_words") or []

    # 簡易言語推定
    lang = detect_lang(instr)

    # 上位感情（最大2）
    def top2(d):
        return [k for k, _ in sorted(d.items(), key=lambda kv: kv[1], reverse=True)[:2]] if d else []
    tops = top2(ratios)
    e1 = tops[0] if len(tops) > 0 else None
    e2 = tops[1] if len(tops) > 1 else None

    # 日本語表示名マップ
    EMO_JA = {"Joy":"喜び","Sadness":"悲しみ","Anxiety":"不安","Anger":"怒り","Calm":"落ち着き"}
    def emo_label_jp(x): 
        return EMO_JA.get(x or "", "感情")

    # 時間帯表現（日本語）
    TB_JA = {"morning":"朝","noon":"昼","afternoon":"午後","evening":"夕方","night":"夜","midnight":"深夜"}
    def time_bias_jp(bias):
        if not bias: 
            return None
        mapped = [TB_JA.get(b, b) for b in bias]
        return "、".join(mapped[:3])

    # ホットワードの表示
    def hot_words_fmt(hw, lang):
        if not hw: 
            return None
        return ("、".join(hw[:4]) if lang=='ja' else ", ".join(hw[:4]))

    # ユーザー名（環境変数で与えられていれば使用）
    user_name = os.getenv("MYMODEL_USER_NAME", None)
    you = user_name if (user_name and lang=='ja') else ("you" if lang=='en' else "あなた")

    # 文章パーツの組立（人格として「私は～と受け取っています」）
    if lang == 'en':
        emo_phrase = (f"{e1}/{e2}" if (e1 and e2) else (e1 or "some feelings"))
        tb_phrase = time_bias and f"— especially around {', '.join(time_bias[:3])}" or ""
        hw_phrase = hot_words_fmt(hot_words, 'en')
        if hw_phrase:
            hw_clause = f", often in contexts related to {hw_phrase}"
        else:
            hw_clause = ""
        line1 = f"As the persona shaped by your records, I sense that {you} tends to experience {emo_phrase} in certain situations{tb_phrase}{hw_clause}."
        return line1
    else:
        # JA
        emo_phrase = (f"{emo_label_jp(e1)}/{emo_label_jp(e2)}" if (e1 and e2) else (emo_label_jp(e1) if e1 else "いくつかの感情"))
        tbp = time_bias_jp(time_bias)
        tb_phrase = f"（とくに{tbp}）" if tbp else ""
        hw_phrase = hot_words_fmt(hot_words, 'ja')
        if hw_phrase:
            hw_clause = f"、{hw_phrase}に触れた場面で少し強まりやすい印象です。"
        else:
            hw_clause = "。"

        # 口調は“人格の私”として、Mash（=あなた）へ語りかける
        line1 = f"私は{you}の記録から形作られた“私”です。{you}は、ある種の状況で{emo_phrase}を感じやすいように私は受け取っています{tb_phrase}{hw_clause}"
        return line1


    r1 = pct(ratios.get(e1, 0))
    r2 = pct(ratios.get(e2, 0))
    bias_txt = f"{'・'.join(time_bias)}に偏在" if time_bias else "特定の時間帯への明確な偏在は未検出"
    hw_txt = "／".join(hot_words[:4]) if hot_words else "観測語なし"

    intent = intensity_from_len(instr)
    scope = "公開範囲" if target == "external" else "全入力"

    lines = [
        f"推定：入力は「{e1}/{e2}」の揺らぎを中心にした{intent}感情駆動。対象は{scope}。",
        f"根拠：期間{period}の記録から {e1}:{r1}, {e2}:{r2}。出現は{bias_txt}。観測語：{hw_txt}。",
        "注記：断定を避け、観測可能な構造のみを述べています。一次情報が不足する照会には応答を抑制します。",
    ]
    return "\n".join(lines)


# ---------- Add-on: Advanced date-like guard (non-destructive) ----------
# This block is auto-injected to extend date/temporal detection without removing original rules.
# It mirrors the patterns used in date_guard.py and exposes a helper used only by /mymodel/infer.
import re as _re_addon
from typing import List as _List, Tuple as _Tuple

_JA_PATTERNS_ADDON = [
    r"\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日?",
    r"\d{1,2}\s*月\s*\d{1,2}\s*日",
    r"\d{4}[-/]\d{1,2}[-/]\d{1,2}",
    r"\d{1,2}[:時]\d{2}(?:[:分]\d{2})?",
    r"(昨日|今日|明日|一昨日|明後日|先週|来週|先月|来月|去年|今年|来年)",
    r"(月|火|水|木|金|土|日)曜日",
    r"(何日|何月|何年|いつ)"
]
_EN_PATTERNS_ADDON = [
    r"\b\d{4}-\d{1,2}-\d{1,2}\b",
    r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:,\s*\d{4})?\b",
    r"\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b",
    r"\b(?:yesterday|today|tomorrow|last\s+(?:week|month|year)|next\s+(?:week|month|year))\b",
    r"\b(?:when|what\s+day|what\s+date)\b",
    r"\b\d{1,2}:\d{2}(?::\d{2})?\b"
]
_JA_RX_ADDON = [_re_addon.compile(p) for p in _JA_PATTERNS_ADDON]
_EN_RX_ADDON = [_re_addon.compile(p, flags=_re_addon.IGNORECASE) for p in _EN_PATTERNS_ADDON]

def _contains_date_like_addon(text: str, lang: str | None = None) -> _Tuple[bool, _List[str]]:
    matches: _List[str] = []
    def scan(rx_list):
        local = []
        for rx in rx_list:
            local.extend(m.group(0) for m in rx.finditer(text))
        return local
    if lang == 'ja':
        matches = scan(_JA_RX_ADDON)
    elif lang == 'en':
        matches = scan(_EN_RX_ADDON)
    else:
        matches = scan(_JA_RX_ADDON) + scan(_EN_RX_ADDON)
    return (len(matches) > 0, matches[:5])

def contains_date_like_adv(text: str) -> bool:
    # Use both the original quick rules and the extended ones
    try:
        base = contains_date_like(text)  # original
    except Exception:
        base = False
    ext, _ = _contains_date_like_addon(text, None)
    return bool(base or ext)
# ---------- End Add-on ----------





# ---------- MyWeb Insight Models ----------
class MyWebInsightRequest(BaseModel):
    user_id: Optional[str] = Field(
        default=None,
        description="ASTOR 構造分析対象のユーザーID（省略時は Authorization から解決）",
    )
    period: Optional[str] = Field(
        default="30d",
        description="分析対象期間（例: 7d/30d/12w/3m）",
    )


class MyWebInsightResponse(BaseModel):
    text: str
    meta: Dict[str, Any] = {}


# ---------- MyWeb Insight Routes ----------
@app.post("/myweb/insight", response_model=MyWebInsightResponse)
async def myweb_insight(
    req: MyWebInsightRequest,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> MyWebInsightResponse:
    """汎用 MyWeb 構造分析レポート。

    - period: "7d", "30d", "12w", "3m" など
    - user_id が指定されていない場合は Authorization: Bearer トークンから解決する。
    """
    # user_id をリクエストボディまたは Authorization ヘッダから解決
    user_id = req.user_id
    if not user_id:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(
                status_code=401,
                detail="Authorization header with Bearer token is required when user_id is omitted",
            )
        try:
            user_id = await _resolve_user_id_from_token(access_token)
        except Exception as exc:
            logger.error("Failed to resolve user_id from token in /myweb/insight: %s", exc)
            raise HTTPException(status_code=401, detail="Invalid authorization token")

    astor_req = AstorRequest(
        mode=AstorMode.MYWEB_INSIGHT,
        user_id=user_id,
        period=req.period or "30d",
    )
    astor_resp = astor_myweb_engine.handle(astor_req)
    if astor_resp.text is None:
        raise HTTPException(status_code=500, detail="ASTOR MyWebInsight failed")

    meta: Dict[str, Any] = dict(astor_resp.meta or {})
    # period 情報が無ければ補完
    meta.setdefault("period", req.period or "30d")
    return MyWebInsightResponse(text=astor_resp.text, meta=meta)


@app.post("/myweb/insight/weekly", response_model=MyWebInsightResponse)
async def myweb_insight_weekly(
    req: MyWebInsightRequest,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> MyWebInsightResponse:
    """週次 MyWeb 構造分析レポート。

    period が指定されていなければ自動的に "7d" を採用する。
    """
    effective_req = MyWebInsightRequest(
        user_id=req.user_id,
        period=req.period or "7d",
    )
    return await myweb_insight(effective_req, authorization=authorization)


@app.post("/myweb/insight/monthly", response_model=MyWebInsightResponse)
async def myweb_insight_monthly(
    req: MyWebInsightRequest,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> MyWebInsightResponse:
    """月次 MyWeb 構造分析レポート。

    period が指定されていなければ自動的に "30d" を採用する。
    """
    effective_req = MyWebInsightRequest(
        user_id=req.user_id,
        period=req.period or "30d",
    )
    return await myweb_insight(effective_req, authorization=authorization)


@app.get("/myweb/insight/weekly", response_model=MyWebInsightResponse)
async def myweb_insight_weekly_get(
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> MyWebInsightResponse:
    """GET 版の週次 MyWeb 構造分析レポート。

    - ボディを送らず Authorization ヘッダだけで呼び出す互換用。
    """
    req = MyWebInsightRequest(user_id=None, period="7d")
    return await myweb_insight(req, authorization=authorization)


@app.get("/myweb/insight/monthly", response_model=MyWebInsightResponse)
async def myweb_insight_monthly_get(
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> MyWebInsightResponse:
    """GET 版の月次 MyWeb 構造分析レポート。

    - ボディを送らず Authorization ヘッダだけで呼び出す互換用。
    """
    req = MyWebInsightRequest(user_id=None, period="30d")
    return await myweb_insight(req, authorization=authorization)


@app.get("/healthz")
def healthz() -> Dict[str, Any]:
    return {"status": "ok", "app": APP_NAME}


@app.post("/mymodel/infer", response_model=InferResponse)
async def infer(
    req: InferRequest,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> InferResponse:
    instr = req.instruction.strip()

    if len(instr) < 4:
        raise HTTPException(status_code=400, detail="情報が足りないため応答できません。")
    if contains_date_like_adv(instr):
        raise HTTPException(status_code=400, detail="この照会は受け付けられません（日付が含まれています）。")

    # ASTOR persona context 用の user_id を解決（body 優先、無ければ Authorization）
    user_id: Optional[str] = req.user_id
    if not user_id and authorization:
        access_token = _extract_bearer_token(authorization)
        if access_token:
            try:
                user_id = await _resolve_user_id_from_token(access_token)
            except Exception as exc:
                logger.warning("ASTOR persona token resolution failed: %s", exc)

    persona_ctx: Optional[Dict[str, Any]] = None
    if user_id:
        try:
            persona_ctx = build_persona_context_payload(user_id=user_id)
        except Exception as exc:
            logger.warning("ASTOR persona context build failed: %s", exc)

    # 1) 構造辞書ベースの“定義質問”であれば、そちらを優先して応答
    lang = detect_lang(instr)
    struct_answer = build_structure_answer(instr, lang=lang)
    if struct_answer:
        logger.info("structure_dict hit for instruction=%r", instr[:80])
        return InferResponse(
            output=struct_answer,
            meta={
                "target": req.target or "self",
                "engine": "structure_dict",
                "version": "1.0.0",
            },
        )

    # 2) 上記に該当しなければ、従来どおり人格ベースの応答を返す
    output = compose_response(instr, req.input, req.target or "self", persona_ctx)

    # Privacy-safe telemetry (no content persisted)
    logger.info("infer called: len=%d target=%s", len(instr), req.target)

    meta: Dict[str, Any] = {"target": req.target or "self", "engine": "rule", "version": "1.0.0"}
    if persona_ctx is not None:
        meta["astor_persona"] = persona_ctx
    return InferResponse(output=output, meta=meta)
# ---------- Entrypoint ----------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host=HOST, port=PORT, log_level="info")

def detect_lang(text: str) -> str:
    """簡易な言語推定: 日本語(ひらがな/カタカナ/漢字)があれば 'ja'、なければ 'en'。"""
    for ch in text:
        if '\u3040' <= ch <= '\u30ff' or '\u4e00' <= ch <= '\u9fff':
            return 'ja'
    return 'en'