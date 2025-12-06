/**
 * MashOS Provider（任意）
 * ------------------------------------------------------------
 * Reactのコンテキスト経由でMashOSを使いたい場合の薄いラッパ。
 * 直接 import { MashOS } from 'mashos' でもOK。
 */
import React, { createContext, useContext, useEffect, PropsWithChildren } from 'react';
import { MashOS } from './index';
import type { MashOSConfig } from './types';

const Ctx = createContext(MashOS);

export function MashOSProvider(props: PropsWithChildren<{ config?: Partial<MashOSConfig> }>) {
  const { children, config } = props;

  useEffect(() => {
    if (config) {
      MashOS.configure(config);
    }
    // configの依存比較は用途に応じて調整
  }, [JSON.stringify(config || {})]);

  return <Ctx.Provider value={MashOS}>{children}</Ctx.Provider>;
}

export function useMashOS() {
  return useContext(Ctx);
}
