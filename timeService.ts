/**
 * timeService
 * ------------------------------------------------------------
 * 端末ローカル時刻の取得・管理を担う。外部依存なし。
 */
import type { MashTime, TimeConfig } from './types';

/** 内部用：安全なDate生成（freezeTo対応） */
function resolveNow(freezeTo?: Date | string | number | null): Date {
  if (freezeTo === undefined || freezeTo === null) return new Date();
  if (freezeTo instanceof Date) return new Date(freezeTo.getTime());
  if (typeof freezeTo === 'number') return new Date(freezeTo);
  // 文字列はISOとして解釈を試みる
  return new Date(freezeTo);
}

/**
 * TimeAdapterの生成
 * - mode: 'off' の場合は undefined を返す側で扱うことを推奨（呼び出し側で渡さない）
 * - mode: 'snapshot' は毎回 new Date()
 * - mode: 'interval' は指定間隔で購読可能（subscribe）
 */
export function createTimeAdapter(cfg: TimeConfig): MashTime & { __dispose?: () => void } {
  const baseNow = () => resolveNow(cfg.freezeTo ?? null);

  if (cfg.mode === 'snapshot' || cfg.mode === 'off') {
    // 'off'でも呼び出し側で「未定義を渡す」想定。ここはsnapshot相当の挙動。
    return {
      now: () => baseNow(),
    };
  }

  // interval モード
  const listeners = new Set<(d: Date) => void>();
  const intervalMs = typeof cfg.intervalMs === 'number' ? cfg.intervalMs : 60000;
  let timer: any = null;

  const start = () => {
    stop();
    timer = setInterval(() => {
      const t = baseNow();
      listeners.forEach((fn) => {
        try { fn(t); } catch {}
      });
    }, intervalMs);
  };
  const stop = () => {
    if (timer) {
      clearInterval(timer);
      timer = null;
    }
  };

  // 起動
  start();

  return {
    now: () => baseNow(),
    subscribe: (cb: (d: Date) => void) => {
      listeners.add(cb);
      // 初期通知
      try { cb(baseNow()); } catch {}
      return () => {
        listeners.delete(cb);
      };
    },
    __dispose: () => stop(),
  };
}
