# Post Migration Checklist

- [ ] Update any CI/CD scripts that still `cd Cocolon/ai`.
- [ ] Verify `configs/app_ids.yaml` values (AI_NAME / APP_NAME / PROJECT_NAME).
- [ ] Confirm `data/raw/logs.jsonl` path in your ingestion job.
- [ ] Run Structure Engine and check `data/processed/features.json`.
- [ ] Decide the base model in `configs/model_train.yaml`.
- [ ] If you have LoRA weights already, wire them in `services/ai_inference/app.py`.
- [ ] Remove `ai/tools/tools/*` after manual verification.
