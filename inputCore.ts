/**
 * inputCore
 * ------------------------------------------------------------
 * 入力画面向けのMashOSロジック。Supabase等の外部依存はここでは持たない。
 */
import type { EmotionEntry } from './types';
import type { MashTime } from './types';

export interface BuildEntryPayload {
  emotions: string[];
  memo?: string;
}
export interface BuildEntryOptions {
  time?: MashTime; // undefined の場合、created_atは付与しない
}

/** 入力データの作成。timeがあれば created_at を付与。 */
export function buildEntry(payload: BuildEntryPayload, opts?: BuildEntryOptions): EmotionEntry {
  const created_at = opts?.time ? opts.time.now().toISOString() : undefined;
  return {
    emotions: payload.emotions,
    memo: payload.memo,
    created_at,
  };
}
