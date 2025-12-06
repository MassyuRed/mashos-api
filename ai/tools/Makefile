
import:
	python tools/import_logs.py --src data/raw/import_template.csv --mapping tools/import_mapping.yaml --backup

validate:
	python tools/validate_logs.py --src data/raw/logs.jsonl

extract:
	python services/structure_engine/extract.py
