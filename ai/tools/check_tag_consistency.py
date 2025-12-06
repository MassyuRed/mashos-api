#!/usr/bin/env python3
# Simple scanner to find hard-coded 'CocolonAI' occurrences.
import os
target = "CocolonAI"
exts = {".py",".ts",".tsx",".js",".json",".yaml",".yml",".md",".txt",".ini",".env"}
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
hits = []
for dp, dn, fn in os.walk(root):
    for f in fn:
        if os.path.splitext(f)[1] in exts:
            p = os.path.join(dp, f)
            try:
                with open(p,"r",encoding="utf-8") as fh:
                    s=fh.read()
                if target in s:
                    hits.append(p)
            except Exception:
                pass
print("Found hard-coded 'CocolonAI' in:")
for h in hits:
    print(" -", h)
