"""One bounded, offline fresh Piece LoRA fit; no inference or adoption.

Reuses the assistant-only CE window from material_v4_target4_trial.train_phase.
The scope config supplies architecture only. No prior adapter weights are read.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
from importlib.metadata import version
import json
import math
import os
from pathlib import Path
import random
import re
import signal
import sys
import time

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1])]
from serve_emlis_natural_reply import MODEL, REVISION, PINS, piece_output_schema


def require(condition, code):
    if not condition:
        raise ValueError(code)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, 'duplicate_json_key')
        value[key] = item
    return value


def read_json(path):
    def invalid(_):
        raise ValueError('nonfinite_json')
    return json.loads(Path(path).read_text(encoding='utf-8'),
                      object_pairs_hook=unique_object, parse_constant=invalid)


def validate_settings(*, output, max_seconds, updates, learning_rate, seed):
    require(not Path(output).exists(), 'output_already_exists_no_resume')
    require(type(max_seconds) is int and 1 <= max_seconds <= 480, 'max_seconds_invalid')
    require(type(updates) is int and 1 <= updates <= 48, 'updates_invalid')
    require(type(learning_rate) in (int, float) and math.isfinite(learning_rate)
            and 0 < learning_rate <= 1e-4, 'learning_rate_invalid')
    require(type(seed) is int and 0 <= seed < 2**32, 'seed_invalid')


def validate_scope(config):
    expected = {'q_proj', 'k_proj', 'v_proj', 'o_proj'} | {
        str(layer) + '.mlp.' + projection for layer in range(3, 32, 4)
        for projection in ('gate_proj', 'up_proj', 'down_proj')}
    require(type(config) is dict and config.get('peft_type') == 'LORA'
            and config.get('task_type') == 'CAUSAL_LM'
            and config.get('base_model_name_or_path') == MODEL
            and type(config.get('r')) is int and config['r'] == 8
            and config.get('lora_alpha') == 16 and config.get('lora_dropout') == 0
            and config.get('bias') == 'none' and config.get('init_lora_weights') is True,
            'scope_config_invalid')
    modules = config.get('target_modules')
    require(type(modules) is list and len(modules) == len(expected)
            and set(modules) == expected, 'scope_modules_changed')
    require(all(not config.get(key) for key in (
        'modules_to_save', 'target_parameters', 'trainable_token_indices',
        'layers_to_transform', 'exclude_modules', 'rank_pattern', 'alpha_pattern',
        'use_dora', 'use_rslora', 'use_qalora', 'fan_in_fan_out')),
        'scope_extra_trainable_configuration')


def validate_rows(packet):
    require(type(packet) is dict and packet.get('all_fictional') is True,
            'fictional_data_required')
    rows = packet.get('rows')
    require(type(rows) is list and len(rows) == 24, 'exact_24_training_rows_required')
    ids, texts = set(), set()
    for row in rows:
        require(type(row) is dict and type(row.get('id')) is str
                and re.fullmatch(r'[A-Za-z0-9_.:-]{1,80}', row['id'])
                and row['id'] not in ids, 'training_id_invalid_or_duplicate')
        ids.add(row['id'])
        messages = row.get('messages')
        require(type(messages) is list and len(messages) == 2
                and all(type(message) is dict for message in messages)
                and [message.get('role') for message in messages] == ['system', 'user']
                and all(type(message.get('content')) is str and message['content'] for message in messages),
                'training_messages_invalid')
        schema = piece_output_schema(messages)
        material = json.loads(messages[1]['content'], object_pairs_hook=unique_object)
        slots = material['control']['field_slots']
        keys = schema['properties']['field_blocks']['required']
        text = tuple(slots[key].get('literal') for key in keys)
        require(all(type(value) is str and value.strip() for value in text)
                and text not in texts, 'training_source_text_missing_or_duplicate')
        texts.add(text)
        target = row.get('assistant_target')
        require(type(target) is str and target, 'assistant_target_invalid')
        candidate = json.loads(target, object_pairs_hook=unique_object)
        require(type(candidate) is dict and list(candidate) == ['field_blocks']
                and type(candidate['field_blocks']) is dict
                and list(candidate['field_blocks']) == keys
                and all(type(value) is str and value.strip() and '\n' not in value and '\r' not in value
                        for value in candidate['field_blocks'].values()), 'assistant_target_shape_invalid')
    return rows


def encode_training(tokenizer, row, *, context_tokens=8192, output_tokens=2048):
    """Keep every source token and train only the full assistant/EOS tail."""
    prompt = tokenizer.apply_chat_template(row['messages'], enable_thinking=False,
        add_generation_prompt=True, tokenize=True, return_dict=False, truncation=False)
    full = tokenizer.apply_chat_template(row['messages'] + [dict(role='assistant', content=row['assistant_target'])],
        enable_thinking=False, add_generation_prompt=False, tokenize=True, return_dict=False, truncation=False)
    require(type(prompt) is list and type(full) is list and len(prompt) > 0
            and full[:len(prompt)] == prompt and len(full) > len(prompt), 'chat_template_prefix_changed')
    require(len(prompt) + output_tokens <= context_tokens and len(full) <= context_tokens
            and len(full) - len(prompt) <= output_tokens, 'training_context_or_target_exceeded')
    require(tokenizer.decode(full[len(prompt):], skip_special_tokens=False,
        clean_up_tokenization_spaces=False) == row['assistant_target'] + '<|im_end|>\n',
        'assistant_eos_tail_changed')
    return dict(input_ids=full, labels=[-100] * len(prompt) + full[len(prompt):],
        loss_start=len(prompt) - 1, logits_positions=len(full) - len(prompt) + 1,
        prompt_tokens=len(prompt), target_tokens=len(full) - len(prompt))


def write_report(output, report):
    temporary = output / 'report.json.tmp'
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(output / 'report.json')


def run(args):
    validate_settings(output=args.output, max_seconds=args.max_seconds, updates=args.updates,
                      learning_rate=args.learning_rate, seed=args.seed)
    require(os.environ.get('HF_HUB_OFFLINE') == '1'
            and os.environ.get('TRANSFORMERS_OFFLINE') == '1', 'offline_cache_required')
    require({name: version(name) for name in PINS} == PINS, 'model_dependency_changed')
    require(args.scope_config.name == 'adapter_config.json' and args.scope_config.is_file(),
            'scope_config_filename_invalid')
    packet, scope = read_json(args.data), read_json(args.scope_config)
    rows = validate_rows(packet)
    validate_scope(scope)
    scope_sha = digest(args.scope_config)
    data_sha = digest(args.data)
    args.output.mkdir()  # Atomic refusal of a completed, partial or concurrent run.
    start = time.monotonic()
    deadline = start + args.max_seconds
    with (args.output / 'run.lock').open('x', encoding='utf-8') as lock:
        json.dump(dict(pid=os.getpid(), seed=args.seed, data_sha256=data_sha,
                       updates=args.updates, max_seconds=args.max_seconds, resume=False), lock)
    report = dict(status='STARTED_NOT_ADOPTED', model=MODEL, revision=REVISION, pins=PINS,
        seed=args.seed, data_sha256=data_sha, scope_config_sha256=scope_sha,
        runner_sha256=digest(__file__), training_initial='FRESH_BASE_NEW_RANDOM_LORA_CONFIG_ONLY',
        old_adapter_weights_read=False, model_loads=0, updates=0, measurement_forwards=0,
        model_generations=0, learning_rate=args.learning_rate, max_seconds=args.max_seconds,
        requested_updates=args.updates, steps=[], measurements=[], checkpoints=[],
        optimizer_and_rng_saved=False, normal_adoption=False)
    def save():
        report['process_seconds'] = round(time.monotonic() - start, 3)
        write_report(args.output, report)
    def check_deadline():
        if time.monotonic() >= deadline:
            raise TimeoutError('piece_training_process_budget_exceeded')
    def expire(*_):
        raise TimeoutError('piece_training_process_budget_exceeded')
    previous_alarm = signal.signal(signal.SIGALRM, expire)
    signal.setitimer(signal.ITIMER_REAL, args.max_seconds)
    model = optimizer = trainable = saved = actual = loaded = None
    try:
        save()
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=REVISION,
            local_files_only=True, trust_remote_code=False)
        # Every encoding completes on CPU before allocating/loading the model.
        encoded = {}
        for row in rows:
            check_deadline()
            encoded[row['id']] = encode_training(tokenizer, row)
        ids = [row['id'] for row in rows]
        measurement_ids = [ids[0], ids[-1]]
        report.update(status='CPU_ENCODED_NOT_ADOPTED', training_rows=len(encoded),
            measurement_ids=measurement_ids, token_counts={key: {name: item[name]
                for name in ('prompt_tokens', 'target_tokens')} for key, item in encoded.items()})
        save()
        import torch
        import torch.nn.functional as F
        from transformers import Qwen3_5ForConditionalGeneration
        from peft import PeftConfig, PeftModel, get_peft_model, get_peft_model_state_dict
        from safetensors.torch import load_file
        require(torch.cuda.is_available() and torch.cuda.device_count() == 1, 'single_cuda_device_required')
        random.seed(args.seed); torch.manual_seed(args.seed); torch.cuda.manual_seed_all(args.seed)
        report.update(torch=torch.__version__, gpu=torch.cuda.get_device_name(0))
        check_deadline()
        model = Qwen3_5ForConditionalGeneration.from_pretrained(MODEL, revision=REVISION,
            dtype=torch.bfloat16, device_map={'': 0}, attn_implementation='sdpa',
            local_files_only=True, trust_remote_code=False)
        report['model_loads'] += 1
        # PeftConfig reads config only; no PeftModel/adapter weight load occurs.
        config = PeftConfig.from_pretrained(args.scope_config.parent, local_files_only=True)
        config.inference_mode = False
        model = get_peft_model(model, config)
        named = [(name, parameter) for name, parameter in model.named_parameters() if parameter.requires_grad]
        trainable = [parameter for _, parameter in named]
        require(len(trainable) == 112 and sum(p.numel() for p in trainable) == 3833856
                and all('lora_' in name and p.dtype == torch.float32 for name, p in named), 'fresh_lora_scope_changed')
        require(all(torch.count_nonzero(p).item() == 0 for name, p in named if 'lora_B' in name),
                'fresh_lora_initialization_changed')
        require(all(module.p == 0 for module in model.modules() if isinstance(module, torch.nn.Dropout))
                and getattr(getattr(model.config, 'text_config', model.config), 'attention_dropout', None) == 0,
                'training_dropout_changed')
        named = None
        model.config.use_cache = False
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
        model.enable_input_require_grads()
        torch.cuda.reset_peak_memory_stats()
        def loss(item):
            input_ids = torch.tensor([item['input_ids']], dtype=torch.long, device='cuda:0')
            out = model(input_ids=input_ids, attention_mask=torch.ones_like(input_ids),
                logits_to_keep=item['logits_positions'], use_cache=False)
            gold = torch.tensor(item['labels'][item['loss_start'] + 1:], dtype=torch.long, device='cuda:0')
            require(out.logits.shape[:2] == (1, item['logits_positions']) and bool((gold >= 0).all()),
                    'assistant_loss_window_changed')
            return F.cross_entropy(out.logits[0, :-1, :].float(), gold)
        def measure(phase):
            model.eval()
            values = {}
            with torch.no_grad():
                for key in measurement_ids:
                    check_deadline()
                    value = loss(encoded[key])
                    require(bool(torch.isfinite(value)), 'measurement_nonfinite')
                    values[key] = float(value)
                    report['measurement_forwards'] += 1
            report['measurements'].append(dict(phase=phase, losses=values))
            save()
        def preserve(path):
            check_deadline()
            model.save_pretrained(path, safe_serialization=True)
            weights = load_file(path / 'adapter_model.safetensors')
            current = get_peft_model_state_dict(model)
            require(len(weights) == len(current) == 112 and set(weights) == set(current)
                and all(bool(torch.isfinite(t).all()) and t.dtype == torch.float32
                        and torch.equal(t, current[key].detach().cpu()) for key, t in weights.items()),
                    'saved_adapter_tensor_changed')
            return weights
        measure('before')
        model.train()
        optimizer = torch.optim.AdamW(trainable, lr=args.learning_rate, weight_decay=0.)
        for step in range(1, args.updates + 1):
            check_deadline()
            key = ids[(step - 1) % len(ids)]
            optimizer.zero_grad(set_to_none=True)
            value = loss(encoded[key])
            require(bool(torch.isfinite(value)), 'training_loss_nonfinite')
            value.backward()
            require(all(p.grad is None or bool(torch.isfinite(p.grad).all()) for p in trainable),
                    'training_gradient_nonfinite')
            norm = torch.nn.utils.clip_grad_norm_(trainable, 1.)
            require(bool(torch.isfinite(norm)), 'training_gradient_norm_nonfinite')
            optimizer.step()
            report['updates'] = step
            report['steps'].append(dict(step=step, id=key, loss=float(value.detach()), gradient_norm=float(norm)))
            save()
            if step == 24 and step < args.updates:
                checkpoint = args.output / 'checkpoint_24'
                preserve(checkpoint)
                report['checkpoints'].append(dict(updates=step, path=checkpoint.name,
                    weights_sha256=digest(checkpoint / 'adapter_model.safetensors')))
                save()
        optimizer.zero_grad(set_to_none=True)
        optimizer = None
        measure('after')
        require(report['updates'] == args.updates and report['measurement_forwards'] == 4,
                'training_counts_changed')
        adapter = args.output / 'adapter'
        saved = preserve(adapter)
        report.update(weights_sha256=digest(adapter / 'adapter_model.safetensors'),
                      config_sha256=digest(adapter / 'adapter_config.json'))
        # Reload the saved candidate onto a second fresh base. It is never a
        # resume or an Analysis-weight initialisation; every saved value matches.
        model = optimizer = trainable = actual = value = None
        gc.collect(); torch.cuda.empty_cache(); torch.cuda.synchronize()
        check_deadline()
        model = Qwen3_5ForConditionalGeneration.from_pretrained(MODEL, revision=REVISION,
            dtype=torch.bfloat16, device_map={'': 0}, attn_implementation='sdpa',
            local_files_only=True, trust_remote_code=False)
        report['model_loads'] += 1
        model = PeftModel.from_pretrained(model, adapter, is_trainable=False, local_files_only=True)
        model.eval(); model.requires_grad_(False)
        loaded = get_peft_model_state_dict(model)
        require(not model.training and not any(p.requires_grad for p in model.parameters())
                and len(loaded) == len(saved) == 112 and set(loaded) == set(saved)
                and all(bool(torch.isfinite(t).all()) and torch.equal(t.detach().cpu(), saved[key])
                        for key, t in loaded.items()), 'saved_reload_tensor_changed')
        require(digest(args.scope_config) == scope_sha and digest(args.data) == data_sha,
                'input_data_or_scope_changed')
        check_deadline()
        report.update(status='COMPLETE_NOT_ADOPTED', saved_reload_tensor_identity=True,
            peak_allocated_gib=torch.cuda.max_memory_allocated() / 2**30,
            peak_reserved_gib=torch.cuda.max_memory_reserved() / 2**30)
    except BaseException as exc:
        # Error class/code only: upstream exceptions can contain private text.
        report.update(status='FAILED_NOT_ADOPTED', error_type=type(exc).__name__)
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_alarm)
        model = optimizer = trainable = saved = actual = loaded = None
        gc.collect()
        save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--scope-config', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--max-seconds', type=int, default=480)
    parser.add_argument('--updates', type=int, default=48)
    parser.add_argument('--learning-rate', type=float, default=1e-4)
    parser.add_argument('--seed', type=int, default=20261109)
    try:
        run(parser.parse_args())
    except BaseException as exc:
        # Do not let a tokenizer/model exception print private prompt text.
        print('piece_training_failed_' + type(exc).__name__, file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == '__main__':
    main()
