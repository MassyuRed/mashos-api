/**
 * 設定例：MashOSConfig
 * ------------------------------------------------------------
 * - 既定は'snapshot'（呼び出し時刻を使用）
 * - mymodelだけ時間反映をOFF
 * - mywebはintervalで1分ごとに更新（UIのバナー判定などに活用可能）
 */
import type { MashOSConfig } from './types';

export const mashOSConfigExample: MashOSConfig = {
  time: {
    default: { mode: 'snapshot' },
    perFeature: {
      input: { mode: 'snapshot' },
      myweb: { mode: 'interval', intervalMs: 60000 },
      mymodel: { mode: 'off' },
    },
  },
};
