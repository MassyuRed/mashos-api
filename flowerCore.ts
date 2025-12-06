
/**
 * flowerCore
 * ------------------------------------------------------------
 * Flower: 解析系の入口。annotateに加えて、InputScreen が必要とする
 * 「flower/climate を含む解析結果」を生成する analyze() を提供。
 */
import type { MashTime } from "./types";

export interface EmotionWithStrength {
  type: string;
  strength?: "weak" | "medium" | "strong";
}

export interface AnalyzeArgs {
  emotions: EmotionWithStrength[];
  memo?: string;
  time?: MashTime;
}

export interface FlowerState {
  flower: {
    toneColor: { h: number; s: number; l: number };
    shape: { spread: number };
    animation: { sway: number; breathAmplitude: number; bloomSpeed: number };
  };
  climate?: { weather: "sunny" | "cloudy" | "rainy" | "night" };
  annotated_at?: string;
}

/** 既存の annotate（時間帯タグ付与の軽量版） */
export interface AnnotateInput<T = Record<string, unknown>> {
  data: T;
  time?: MashTime;
}
export interface Annotation<T = Record<string, unknown>> {
  data: T;
  timeBand?: "night" | "morning" | "afternoon" | "evening";
  annotated_at?: string;
}
export function annotate<T = Record<string, unknown>>(input: AnnotateInput<T>): Annotation<T> {
  const now = input.time?.now();
  const hr = typeof now?.getHours === "function" ? now.getHours() : undefined;
  let timeBand: Annotation["timeBand"] = undefined;
  if (typeof hr === "number") {
    if (hr < 5) timeBand = "night";
    else if (hr < 11) timeBand = "morning";
    else if (hr < 17) timeBand = "afternoon";
    else timeBand = "evening";
  }
  return { data: input.data, timeBand, annotated_at: now ? now.toISOString() : undefined };
}

/**
 * emotions から簡易に「花」と「気象」を生成
 * - 画面のアニメーション要件に合わせた、決定論的な軽量ヒューリスティクス
 * - すべて 0..1 の範囲で出力し、InputScreen 側の hsl% 換算に対応
 */
export function analyze(args: AnalyzeArgs): FlowerState {
  const now = args.time?.now();
  const types = (args.emotions || []).map((e) => e.type);
  const joy = types.includes("喜び") ? 1 : 0;
  const sad = types.includes("悲しみ") ? 1 : 0;
  const anger = types.includes("怒り") ? 1 : 0;
  const anxiety = types.includes("不安") ? 1 : 0;
  const peace = types.includes("平穏") ? 1 : 0;

  // 色相: 喜び=黄 / 悲しみ=青 / 怒り=赤 / 不安=青緑 / 平穏=緑
  const h = joy ? 50 : sad ? 220 : anger ? 0 : anxiety ? 200 : peace ? 120 : 200;
  const s = joy || anger ? 0.70 : sad ? 0.45 : anxiety ? 0.55 : peace ? 0.35 : 0.5;
  const l = peace ? 0.70 : joy ? 0.60 : sad ? 0.45 : anger ? 0.45 : 0.55;

  // 形状・アニメ: 喜び/平穏で開き、悲しみ/不安で揺らぎ強め
  const spread = Math.min(1, (joy + peace) * 0.6 + (types.length >= 3 ? 0.2 : 0));
  const sway = anxiety ? 0.8 : peace ? 0.2 : 0.5;
  const breathAmplitude = joy ? 0.20 : sad ? 0.10 : 0.15;
  const bloomSpeed = joy ? 1.0 : sad ? 0.6 : anxiety ? 0.7 : anger ? 0.8 : 0.9;

  const hour = typeof now?.getHours === "function" ? now.getHours() : undefined;
  const weather: FlowerState["climate"]["weather"] =
    typeof hour === "number"
      ? hour < 5 || hour >= 22
        ? "night"
        : joy
        ? "sunny"
        : sad
        ? "rainy"
        : "cloudy"
      : "cloudy";

  return {
    flower: {
      toneColor: { h, s, l },
      shape: { spread },
      animation: { sway, breathAmplitude, bloomSpeed },
    },
    climate: { weather },
    annotated_at: now ? now.toISOString() : undefined,
  };
}
