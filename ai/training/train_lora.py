#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CocolonAI LoRA Trainer (template)
Requirements:
  pip install -U transformers datasets peft accelerate pyyaml bitsandbytes

Usage:
  python training/train_lora.py --config configs/model_train.yaml
"""
import os, json, argparse, yaml
from datasets import Dataset
from transformers import (AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer,
                          DataCollatorForLanguageModeling)
try:
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from bitsandbytes.config import BitsAndBytesConfig
    _HAS_BNB = True
except Exception:
    _HAS_BNB = False
    LoraConfig = None
    get_peft_model = None
    prepare_model_for_kbit_training = None
    BitsAndBytesConfig = None

PROMPT_FMT = (
    "### Instruction\n{inst}\n\n"
    "### Input\n{inp}\n\n"
    "### Response\n{out}"
)

def read_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_jsonl(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if not line: continue
            rows.append(json.loads(line))
    return rows

def build_text(ex):
    inst = ex.get("instruction","").strip()
    inp = json.dumps(ex.get("input",{}), ensure_ascii=False)
    out = ex.get("output","").strip()
    return PROMPT_FMT.format(inst=inst, inp=inp, out=out)

def tokenize_function(examples, tokenizer, max_len):
    return tokenizer(examples["text"], truncation=True, max_length=max_len, padding=False)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/model_train.yaml")
    args = ap.parse_args()

    cfg = read_yaml(args.config)
    base = cfg.get("base_model", "mistral-7b")
    max_len = int(cfg.get("max_seq_len", 2048))
    train_file = cfg.get("train_file", "data/train/{{AI_NAME}}_interpret_train.jsonl")
    out_dir = cfg.get("output_dir", "models/lora")
    dtype = cfg.get("dtype", "bfloat16")

    # Tokenizer & model
    tokenizer = AutoTokenizer.from_pretrained(base, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    load_kwargs = {}
    if _HAS_BNB:
        bnb_cfg = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_use_double_quant=True,
                                     bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype="bfloat16")
        load_kwargs.update(dict(device_map="auto", quantization_config=bnb_cfg))

    model = AutoModelForCausalLM.from_pretrained(base, **load_kwargs)
    model.config.use_cache = False

    if LoraConfig is not None:
        if prepare_model_for_kbit_training is not None:
            model = prepare_model_for_kbit_training(model)
        lora = LoraConfig(
            r=int(cfg.get("lora_r",16)),
            lora_alpha=int(cfg.get("lora_alpha",32)),
            target_modules=cfg.get("target_modules", ["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"]),
            lora_dropout=float(cfg.get("lora_dropout",0.05)),
            bias="none",
            task_type="CAUSAL_LM",
        )
        model = get_peft_model(model, lora)

    rows = load_jsonl(train_file)
    ds = Dataset.from_dict({"text":[build_text(r) for r in rows]})
    tokenized = ds.map(lambda e: tokenize_function(e, tokenizer, max_len), batched=True, remove_columns=["text"])
    collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    args_t = TrainingArguments(
        output_dir=out_dir,
        per_device_train_batch_size=int(cfg.get("micro_batch_size",2)),
        gradient_accumulation_steps=int(cfg.get("gradient_accumulation_steps",8)),
        learning_rate=float(cfg.get("learning_rate",1.2e-4)),
        num_train_epochs=float(cfg.get("num_epochs",3)),
        warmup_ratio=float(cfg.get("warmup_ratio",0.03)),
        weight_decay=float(cfg.get("weight_decay",0.0)),
        logging_steps=10,
        save_steps=int(cfg.get("save_steps",500)),
        save_total_limit=2,
        evaluation_strategy="no",
        bf16=(dtype=="bfloat16"),
        fp16=(dtype=="float16"),
        report_to="none"
    )

    trainer = Trainer(model=model, args=args_t, train_dataset=tokenized, data_collator=collator)
    trainer.train()
    trainer.save_model(out_dir)
    print("[ok] training finished ->", out_dir)

if __name__ == "__main__":
    main()
