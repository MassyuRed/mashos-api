# MashOS/ai Migration Report

Date: 2025-10-27

This report documents the automated migration of the Cocolon AI module into **MashOS/ai**.

## Summary

- Source archives: `ai.zip`, `tools.zip`
- Destination root: `MashOS/ai`
- Copied files: 44
- Skipped existing files (kept destination): 20
- Merged training files (missing only): 0
- Textual path updates (`Cocolon/ai` → `MashOS/ai` etc.): 0 replacements across 0 files.

## Path Updates
The following files had path strings updated:



## Notes
- Tools duplication under `tools/tools/*` was flattened into `MashOS/ai/tools/`.
- Training assets from `tools/training/` were merged into `MashOS/ai/training/` **only when missing** to avoid overwriting your primary training scripts.
- No renaming of `AI_NAME` / `APP_NAME` tags was performed.

## Next Steps (suggested)
1. Update any external build scripts that `cd Cocolon/ai` to use `cd MashOS/ai`.
2. (Optional) Remove leftover duplicate utilities after verifying your workflows:
   - `MashOS/ai/tools/tools/*` should not exist after this migration.
3. Run quick health checks:
   ```bash
   cd MashOS/ai
   make -n || true
   python -m compileall .
   ```
4. If you use FastAPI locally:
   ```bash
   cd MashOS/ai/services/ai_inference
   uvicorn app:app --reload
   ```

——
Generated automatically by “共鳴構造モード”.
