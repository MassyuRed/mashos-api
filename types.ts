/**
 * MashOS Types
 * ------------------------------------------------------------
 * 基本的な型定義。依存を追加せず、React Native/Expoでもそのまま使える構成。
 */
export type Feature = 'input' | 'myweb' | 'flower';

export type TimeMode = 'off' | 'snapshot' | 'interval';

export interface TimeConfig {
  /** 'off' → 反映しない / 'snapshot' → 呼び出し時点の時刻 / 'interval' → 定期更新（subscribe利用可） */
  mode: TimeMode;
  /** intervalモード時のtick間隔(ms)。省略時は60,000（1分）。 */
  intervalMs?: number;
  /** デバッグ・検証用。固定時刻に“凍結”。Date/ISO文字列/epoch(ms)が指定可能。null/未指定で無効。 */
  freezeTo?: Date | string | number | null;
}

export interface MashOSConfig {
  time: {
    /** 既定のTimeConfig（全機能に適用） */
    default: TimeConfig;
    /** 機能別の上書き設定（あればdefaultを上書き） */
    perFeature?: Partial<Record<Feature, TimeConfig>>;
  };
}

export interface MashTime {
  /** 現在時刻（ローカル端末時間）を返す。freezeTo設定時は凍結時刻。 */
  now(): Date;
  /** intervalモードのときのみ利用可。購読を開始し、解除関数を返す。 */
  subscribe?(cb: (d: Date) => void): () => void;
}

export interface EmotionEntry {
  emotions: string[];
  memo?: string;
  /** ISO文字列（例: 2025-10-24T07:00:00.000Z） */
  created_at?: string;
  id?: string;
}

export type ReportType = 'weekly' | 'monthly';

export interface PeriodRange {
  start: Date;
  end: Date;
}


// --- Emotion strength support (保存用の補助型) ---
export type EmotionStrength = 'weak' | 'medium' | 'strong';

export interface EmotionWithStrength {
  /** 感情タグ（例: "喜び" "悲しみ" など） */
  type: string;
  /** 強度（弱/中/強） */
  strength: EmotionStrength;
}

/** Supabaseに保存する1件分のエントリ（後方互換のため追加プロパティは任意） */
export interface EmotionRecord extends EmotionEntry {
  /** 強度付きの感情明細（JSONBとして保存想定: emotion_details） */
  emotion_details?: EmotionWithStrength[];
  /** 平均強度（weak=1, medium=2, strong=3 の平均値） */
  emotion_strength_avg?: number;
}

// ------------------------------------------------------------
// Subscription / Modes (Cocolon)
// ------------------------------------------------------------

/** Subscription tier (single source of truth for UI gating) */
export type SubscriptionTier = 'free' | 'plus' | 'premium';

/** MyProfile output mode (Light / Standard / Deep) */
export type MyProfileMode = 'light' | 'standard' | 'deep';

/** Tier → allowed MyProfile modes */
export const TIER_PERMISSION_MAP: Record<SubscriptionTier, MyProfileMode[]> = {
  free: ['light'],
  plus: ['light', 'standard'],
  premium: ['light', 'standard', 'deep'],
};

export function normalizeSubscriptionTier(
  raw: string | null | undefined,
  fallback: SubscriptionTier = 'free'
): SubscriptionTier {
  const s = (raw ?? '').trim();
  if (!s) return fallback;
  // JP labels
  if (s === '無料' || s === '無課金' || s === 'フリー') return 'free';
  if (s === 'プラス') return 'plus';
  if (s === 'プレミアム') return 'premium';
  // canonical
  const low = s.toLowerCase();
  if (low === 'free') return 'free';
  if (low === 'plus') return 'plus';
  if (low === 'premium') return 'premium';
  return fallback;
}

export function normalizeMyProfileMode(
  raw: string | null | undefined,
  fallback: MyProfileMode = 'light'
): MyProfileMode {
  const s = (raw ?? '').trim();
  if (!s) return fallback;
  // JP labels
  if (s === 'ライト') return 'light';
  if (s === 'スタンダード') return 'standard';
  if (s === 'ディープ') return 'deep';
  const low = s.toLowerCase();
  if (low === 'light') return 'light';
  if (low === 'standard') return 'standard';
  if (low === 'deep') return 'deep';
  return fallback;
}

export function isMyProfileModeAllowed(tier: SubscriptionTier, mode: MyProfileMode): boolean {
  return TIER_PERMISSION_MAP[tier].includes(mode);
}
