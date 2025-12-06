# MashOS/ai Quickstart (after migration)

## 1) Prepare environment
```bash
cd MashOS/ai
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r training/requirements.txt
```

## 2) (Optional) Run Structure Engine with sample data
```bash
python services/structure_engine/extract.py
cat data/processed/summary.txt
```

## 3) Train LoRA (when train set is ready)
```bash
python training/train_lora.py --config configs/model_train.yaml
```

## 4) Serve API (dev)
```bash
cd services/ai_inference
uvicorn app:app --reload
# POST /v1/{AI_NAME}/interpret
```

## 5) Naming policy
- Keep `{AI_NAME}` / `{APP_NAME}` tags in docs and data to remain rename-safe.
- Use `tools/rename_ai_name.py` (dry-run -> apply) when final names are decided.

## 6) Sanity checks
```bash
cd MashOS/ai
python -m compileall .
```

## 7) Notes
- If you previously scripted `cd Cocolon/ai`, update to `cd MashOS/ai`.
- Tools duplication under `tools/tools/*` was intentionally **not removed** automatically.
  Verify and delete after confirming you no longer need the backup copies.
