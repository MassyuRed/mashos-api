/**
 * mywebCore
 * ------------------------------------------------------------
 * MyWeb用の週報・月報関連ロジック。ローカル時間前提で判定。
 */
import type { PeriodRange } from './types';

/** 日付の 00:00:00.000 を返す（ローカル時間基準） */
function startOfDay(d: Date): Date {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate(), 0, 0, 0, 0);
}
/** 日付の 23:59:59.999 を返す（ローカル時間基準） */
function endOfDay(d: Date): Date {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate(), 23, 59, 59, 999);
}
/** 週の開始（ローカル日曜 00:00）を求める */
function startOfWeekSunday(d: Date): Date {
  const day = d.getDay(); // 0:Sun
  const s = startOfDay(new Date(d.getFullYear(), d.getMonth(), d.getDate()));
  s.setDate(s.getDate() - day);
  return s;
}
/** 週の終了（ローカル土曜 23:59:59.999） */
function endOfWeekSaturday(d: Date): Date {
  const s = startOfWeekSunday(d);
  const e = new Date(s.getFullYear(), s.getMonth(), s.getDate() + 6, 23, 59, 59, 999);
  return e;
}
/** 月初（ローカル月初 00:00） */
function startOfMonth(d: Date): Date {
  return new Date(d.getFullYear(), d.getMonth(), 1, 0, 0, 0, 0);
}
/** 月末（ローカル最終日 23:59:59.999） */
function endOfMonth(d: Date): Date {
  return new Date(d.getFullYear(), d.getMonth() + 1, 0, 23, 59, 59, 999);
}

/** ▼ トリガ判定（配信タイミング） */
export function isWeeklyReportTrigger(d: Date): boolean {
  // 毎週日曜 07:00（ローカル）
  return d.getDay() === 0 && d.getHours() === 7 && d.getMinutes() === 0;
}
export function isMonthlyReportTrigger(d: Date): boolean {
  // 毎月1日 07:00（ローカル）
  return d.getDate() === 1 && d.getHours() === 7 && d.getMinutes() === 0;
}

/**
 * ちょうど「配信トリガ時刻」に呼ばれたときに出すべき
 * 「直近の“完了済み”期間」の週次レンジを返す。
 * 例：日曜07:00に実行 → 一つ前の週（日曜〜土曜）の範囲
 */
export function getCompletedWeeklyRangeFrom(ref: Date): PeriodRange {
  const thisWeekStart = startOfWeekSunday(ref);
  const lastWeekEnd = new Date(thisWeekStart.getTime() - 1); // 土曜 23:59:59.999
  const lastWeekStart = startOfWeekSunday(new Date(lastWeekEnd.getFullYear(), lastWeekEnd.getMonth(), lastWeekEnd.getDate()));
  return { start: lastWeekStart, end: lastWeekEnd };
}

/** 現在属している週のレンジ（日曜〜土曜） */
export function getCurrentWeeklyRangeContaining(ref: Date): PeriodRange {
  return { start: startOfWeekSunday(ref), end: endOfWeekSaturday(ref) };
}

/**
 * ちょうど「配信トリガ時刻」に呼ばれたときに出すべき
 * 「直近の“完了済み”月次レンジ」を返す。
 * 例：1日07:00に実行 → 前月の範囲
 */
export function getCompletedMonthlyRangeFrom(ref: Date): PeriodRange {
  const thisMonthStart = startOfMonth(ref);
  const lastMonthEnd = new Date(thisMonthStart.getTime() - 1);
  const lastMonthStart = startOfMonth(lastMonthEnd);
  return { start: lastMonthStart, end: lastMonthEnd };
}

/** 現在属している月のレンジ */
export function getCurrentMonthlyRangeContaining(ref: Date): PeriodRange {
  return { start: startOfMonth(ref), end: endOfMonth(ref) };
}
