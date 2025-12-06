/**
 * MashOS（中枢）
 * ------------------------------------------------------------
 * - 各機能モジュール（input / myweb / flower）を集約
 * - 時間反映の有無・モードを中央設定で制御
 */
import * as InputCore from "./inputCore";
import * as MyWebCore from "./mywebCore";
import * as FlowerCore from "./flowerCore";
import { createTimeAdapter } from "./timeService";
import type { Feature, MashOSConfig, MashTime, TimeConfig } from "./types";

const FEATURES: Feature[] = ["input", "myweb", "flower"];

// 既定設定
let config: MashOSConfig = {
  time: {
    default: { mode: "snapshot" },
    perFeature: {},
  },
};

// 機能ごとのTimeAdapterキャッシュ
const timeMap: Partial<Record<Feature, MashTime | undefined>> = {};
const disposers: Partial<Record<Feature, (() => void) | undefined>> = {};

function mergeConfig(base: MashOSConfig, next: Partial<MashOSConfig>): MashOSConfig {
  const out: MashOSConfig = JSON.parse(JSON.stringify(base));
  if (next.time) {
    out.time = out.time || { default: { mode: "snapshot" }, perFeature: {} as any };
    if (next.time.default) {
      out.time.default = { ...(out.time.default || {}), ...(next.time.default || {}) };
    }
    if (next.time.perFeature) {
      out.time.perFeature = { ...(out.time.perFeature || {}) } as any;
      const src = next.time.perFeature as any;
      for (const k of Object.keys(src)) {
        const prev = (out.time.perFeature as any)[k] || {};
        (out.time.perFeature as any)[k] = { ...prev, ...src[k] };
      }
    }
  }
  return out;
}

function resolveTimeConfig(feature: Feature): TimeConfig {
  const per = (config.time?.perFeature || {}) as Partial<Record<Feature, TimeConfig>>;
  const fallback: TimeConfig = config.time?.default || { mode: "snapshot" };
  return per[feature] || fallback;
}

function rebuildTimeAdapters(): void {
  // dispose existing
  for (const f of FEATURES) {
    const disposer = disposers[f];
    if (typeof disposer === "function") {
      try { disposer(); } catch {}
      disposers[f] = undefined;
    }
  }
  // rebuild
  for (const f of FEATURES) {
    const tc = resolveTimeConfig(f);
    if (tc.mode === "off") {
      timeMap[f] = undefined;
      continue;
    }
    const adapter = createTimeAdapter(tc);
    // optional disposer
    const maybeDispose = (adapter as any).__dispose;
    if (typeof maybeDispose === "function") disposers[f] = maybeDispose;
    timeMap[f] = adapter;
  }
}

// 初期化
rebuildTimeAdapters();

const MashOS = {
  /** 設定を反映（時間関連のみ） */
  configure(next: Partial<MashOSConfig>) {
    config = mergeConfig(config, next);
    rebuildTimeAdapters();
  },

  /** ------- input 領域の窓口 ------- */
  input: {
    buildEntry(payload: InputCore.BuildEntryPayload) {
      return InputCore.buildEntry(payload, { time: timeMap.input });
    },
  },

  /** ------- myweb 領域の窓口 ------- */
  myweb: {
    isWeeklyReportNow() {
      const d = timeMap.myweb?.now() ?? new Date();
      return MyWebCore.isWeeklyReportTrigger(d);
    },
    isMonthlyReportNow() {
      const d = timeMap.myweb?.now() ?? new Date();
      return MyWebCore.isMonthlyReportTrigger(d);
    },
    completedWeeklyRangeForNow() {
      const d = timeMap.myweb?.now() ?? new Date();
      return MyWebCore.getCompletedWeeklyRangeFrom(d);
    },
    completedMonthlyRangeForNow() {
      const d = timeMap.myweb?.now() ?? new Date();
      return MyWebCore.getCompletedMonthlyRangeFrom(d);
    },
    currentWeeklyRange() {
      const d = timeMap.myweb?.now() ?? new Date();
      return MyWebCore.getCurrentWeeklyRangeContaining(d);
    },
    currentMonthlyRange() {
      const d = timeMap.myweb?.now() ?? new Date();
      return MyWebCore.getCurrentMonthlyRangeContaining(d);
    },
  },

  /** ------- flower 領域の窓口 ------- */
  flower: {
    annotate<T = Record<string, unknown>>(data: T) {
      return FlowerCore.annotate({ data, time: timeMap.flower });
    },
    /** InputScreen から使う：花/気象を含む解析 */
    analyze(emotions: FlowerCore.EmotionWithStrength[], memo?: string) {
      return FlowerCore.analyze({ emotions, memo, time: timeMap.flower });
    },
  },

  /** @deprecated 将来削除予定：`MashOS.mymodel` は `MashOS.flower` に統合 */
  mymodel: {
    annotate<T = Record<string, unknown>>(data: T) {
      try { console && console.warn && console.warn("[DEPRECATION] MashOS.mymodel.annotate → MashOS.flower.annotate"); } catch {}
      return FlowerCore.annotate({ data, time: timeMap.flower });
    },
    analyze(emotions: FlowerCore.EmotionWithStrength[], memo?: string) {
      try { console && console.warn && console.warn("[DEPRECATION] MashOS.mymodel.analyze → MashOS.flower.analyze"); } catch {}
      return FlowerCore.analyze({ emotions, memo, time: timeMap.flower });
    },
  },
} as const;

export default MashOS;
