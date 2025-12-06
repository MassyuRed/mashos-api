.PHONY: help serve-ai train-ai build-data check

help:
	@echo "Targets:"
	@echo "  make serve-ai     - Run FastAPI dev server"
	@echo "  make train-ai     - Train LoRA using configs/model_train.yaml"
	@echo "  make build-data   - Run Structure Engine on sample data"
	@echo "  make check        - Quick sanity checks"

serve-ai:
	cd ai/services/ai_inference && uvicorn app:app --reload

train-ai:
	cd ai && pip install -r training/requirements.txt && python training/train_lora.py --config configs/model_train.yaml

build-data:
	cd ai && python services/structure_engine/extract.py

check:
	cd ai && python -m compileall .
