"""Private inference server for the existing local Qwen3.5-4B cache.

The default remains the bounded personal connection probe.  The explicit
--analysis-service mode serves the ordinary Analysis route until stopped,
with its own output/context/time budgets. No training, downloads, provider
fallback, or automatic request retry occur in either mode.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager, nullcontext
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.metadata import version
import json
import logging
import os
from pathlib import Path
import re
import signal
import threading
import time

MODEL = "Qwen/Qwen3.5-4B"
REVISION = "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"
FIT38_WEIGHTS = "ad8b89e8974df9bfe7e804b8f67bbaac59e6cbb37042c3254fb58ffb64230d0a"
FIT38_CONFIG = "ef4b1aef621fb4e234ce6a05601efb62a987c3cf5d40f3995ca1b72200bab145"
PINS = {"transformers": "5.19.0", "peft": "0.21.2", "accelerate": "1.15.0", "safetensors": "0.8.0"}
SEMANTIC_FORMAT_SOURCE = '817f944fcc8851917c40300a47f62d1defc3ffc3'
PIECE_CANDIDATE_FORMAT = 'piece.field_slots.v1'
PIECE_ADAPTER_NAME = 'piece'


class SourcePrivateConstraintLog(logging.Filter):
    """Upstream error paths must never print decoded prompts or prefixes."""
    def filter(self, record):
        if 'lmformatenforcer' in Path(record.pathname).parts:
            record.msg = 'analysis_generation_constraint_internal_error'
            record.args = ()
            record.exc_info = record.exc_text = record.stack_info = None
        return True


def generation_stage(stage):
    print('analysis_generation_stage=' + stage + ' monotonic=' + str(round(time.monotonic(), 3)), flush=True)


def semantic_free_text_tokens(prefix, batch, sent, blocked, invalid_json_tokens=frozenset()):
    """Exclude raw-control/blank loops only from generated prose, not quotes."""
    allowed = prefix(batch, sent)
    # Source quote candidates contain no raw controls. JSON layout can be
    # compact. Empty decoder entries otherwise enter LMFE's root trie and are
    # allowed at every state without advancing the parser.
    state = prefix.token_enforcer.prefix_states[tuple(sent.tolist())].parser
    key = state.shortcut_key()
    excluded = invalid_json_tokens
    if isinstance(key, tuple) and key[0] == 'json_freetext':
        excluded = invalid_json_tokens | blocked
    allowed = [token for token in allowed if token not in excluded]
    if not allowed:
        raise ValueError('semantic_free_text_tokens_unavailable')
    return allowed


def semantic_output_schema(messages):
    """Constrain protocol and source quotes; meanings remain model-generated."""
    if (type(messages) is not list or len(messages) != 2
            or messages[1].get('role') != 'user'):
        raise ValueError('semantic_material_invalid')
    material = json.loads(messages[1]['content'])
    fields = material.get('fields')
    if type(fields) is not list or not fields:
        raise ValueError('semantic_fields_invalid')
    pairs, seen = [], set()
    for field in fields:
        number, original = field.get('field'), field.get('text')
        if type(number) is not int or number < 1 or number in seen or type(original) is not str:
            raise ValueError('semantic_field_invalid')
        seen.add(number)
        # Long fields stay complete in messages. Offer real, unique spans
        # within the existing quote budget rather than changing any source.
        # Upstream enum parsing does not round-trip every JSON escape. Select
        # literal spans between those characters, without altering material.
        fragments = re.findall(r'[^"\\\x00-\x1f]+', original)
        spans = [fragment[start:start + 4000].strip() for fragment in fragments
            for start in range(0, len(fragment), 2000)]
        spans = list(dict.fromkeys(span for span in spans if span and original.count(span) == 1
            and not re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', span)))
        if spans:
            pairs.append(dict(type='object', properties=dict(field=dict(type='integer', enum=[number]),
                quote=dict(type='string', enum=spans)), required=['field', 'quote'], additionalProperties=False))
    if not pairs:
        raise ValueError('semantic_quotes_unavailable')
    def text(maximum):
        return dict(type='string', minLength=1, maxLength=maximum)
    def obj(properties):
        return dict(type='object', properties=properties, required=list(properties), additionalProperties=False)
    node_ids = ['n' + str(i) for i in range(1, 25)]
    node = obj(dict(node_id=dict(type='string', enum=node_ids),
        node_kind=dict(type='string', enum=['SELF_POSITION', 'TARGET_MEANING', 'CHOICE_OUTPUT', 'STATE_CONTEXT']),
        title=text(80), summary=text(400), explanation=text(3000),
        perspective=dict(type='string', enum=['SELF', 'OBSERVED_INTERACTION']),
        unknowns=dict(type='array', items=text(500), maxItems=4),
        evidence=dict(type='array', items=dict(oneOf=pairs), minItems=1, maxItems=24)))
    edge = obj({'from': dict(type='string', enum=node_ids), 'to': dict(type='string', enum=node_ids),
        'relation_kind': dict(type='string', enum=['SELF_OUTSIDE_GAP', 'CRITERION_EXPRESSION', 'CONTEXT_CONTRAST', 'SHARED_MEANING']),
        'label': text(80), 'explanation': text(1800)})
    return obj(dict(schema_version=dict(type='string', enum=['cocolon.analysis.semantic_map.model.v2']),
        overview=obj(dict(title=text(80), summary=text(2000))),
        nodes=dict(type='array', items=node, minItems=1, maxItems=24),
        edges=dict(type='array', items=edge, maxItems=48)))


def semantic_json_parser(messages, alphabet):
    from lmformatenforcer import CharacterLevelParserConfig, JsonSchemaParser
    # LMFE snapshots alphabet_without_quotes while constructing its context.
    # Updating parser.config later leaves that initial snapshot unchanged.
    return JsonSchemaParser(semantic_output_schema(messages),
        config=CharacterLevelParserConfig(alphabet=alphabet))


def piece_output_schema(messages):
    """Constrain named transport slots, without constraining their meaning."""
    if (type(messages) is not list or len(messages) != 2
            or any(type(message) is not dict for message in messages)
            or [message.get('role') for message in messages] != ['system', 'user']
            or type(messages[1].get('content')) is not str):
        raise ValueError('piece_material_invalid')
    material = json.loads(messages[1]['content'])
    if (type(material) is not dict or material.get('core') != 'piece'
            or material.get('task') != 'PIECE_MODEL_BODY'
            or type(material.get('control')) is not dict):
        raise ValueError('piece_material_invalid')
    slots = material['control'].get('field_slots')
    if (type(slots) is not dict or not 1 <= len(slots) <= 3
            or any(not re.fullmatch(r'(?:memo|memo_action|answer_text_private)_[0-2]', key)
                   or type(value) is not dict for key, value in slots.items())
            or {int(key.rsplit('_', 1)[1]) for key in slots} != set(range(len(slots)))):
        raise ValueError('piece_slots_invalid')
    # This is private decoding order only. The receiver still projects back to
    # the frozen partition order. Decode the separate answer before originals;
    # this does not certify source separation inside either generated value.
    ordered_keys = sorted(slots, key=lambda key: (
        not key.startswith('answer_text_private_'), int(key.rsplit('_', 1)[1])))
    properties = {key: dict(type='string', minLength=1) for key in ordered_keys}
    fields = dict(type='object', properties=properties, required=list(properties), additionalProperties=False)
    return dict(type='object', properties=dict(field_blocks=fields), required=['field_blocks'],
                additionalProperties=False)


def piece_json_parser(messages, alphabet):
    from lmformatenforcer import CharacterLevelParserConfig, JsonSchemaParser
    return JsonSchemaParser(piece_output_schema(messages),
        config=CharacterLevelParserConfig(alphabet=alphabet, force_json_field_order=True))


def _correction_target_context_messages_valid(messages):
    """Admit only a complete, locator-bound AI target context, never arbitrary history."""
    try:
        if (type(messages) is not list or len(messages) != 3
                or any(type(row) is not dict or set(row) != {'role', 'content'} for row in messages)
                or [row['role'] for row in messages] != ['system', 'assistant', 'user']
                or any(type(row['content']) is not str or not row['content'] for row in messages)):
            return False
        context = json.loads(messages[1]['content'])
        material = json.loads(messages[2]['content'])
        if (type(context) is not dict or set(context) != {'ai_interpretation_targets'}
                or type(context['ai_interpretation_targets']) is not list
                or not context['ai_interpretation_targets'] or type(material) is not dict):
            return False
        targets = context['ai_interpretation_targets']
        histories = material.get('past_user_records', [])
        if type(histories) is not list or any(type(row) is not dict for row in histories):
            return False
        records = [('', material.get('current_input_id'), material)]
        records.extend((f'past_user_records[{index}].', row.get('input_id'), row)
                       for index, row in enumerate(histories))
        target_fields = {'source_role', 'context_ref', 'parent_input_id', 'correction_source_path',
                         'correction_id', 'target_event_id', 'target_ai_interpretation'}
        count = 0
        for prefix, parent_id, record in records:
            corrections = record.get('interpretation_corrections', [])
            if type(corrections) is not list:
                return False
            for index, correction in enumerate(corrections):
                if (type(correction) is not dict or count >= len(targets)
                        or correction.get('source_role') != 'USER_INTERPRETATION_CORRECTION'
                        or 'target_ai_interpretation' in correction
                        or type(parent_id) is not str or not parent_id.strip()):
                    return False
                target = targets[count]
                reference = f'ai_interpretation_targets[{count}]'
                if (type(target) is not dict or set(target) != target_fields
                        or any(type(value) is not str or not value.strip() for value in target.values())
                        or target['source_role'] != 'AI_INTERPRETATION_TARGET'
                        or target['context_ref'] != reference
                        or correction.get('target_ai_context_ref') != reference
                        or target['parent_input_id'] != parent_id
                        or target['correction_source_path'] != prefix + f'interpretation_corrections[{index}]'
                        or any(target[key] != correction.get(key) for key in ('correction_id', 'target_event_id'))):
                    return False
                count += 1
        return count == len(targets)
    except (ValueError, TypeError, KeyError):
        return False


def make_handler(generate, *, api_key, model_name, deadline, max_requests,
                 max_new_tokens=2048, request_seconds=23, max_request_bytes=65536,
                 natural_reply=None, natural_queue_seconds=210, piece_revision=None,
                 correction_target_context=False):
    if (type(correction_target_context) is not bool
            or correction_target_context and not natural_reply):
        raise ValueError('correction_target_context_configuration_invalid')
    if piece_revision is not None and (type(piece_revision) is not str
            or not re.fullmatch(r'piece-lora:[0-9a-f]{64}', piece_revision)):
        raise ValueError('piece_adapter_revision_invalid')
    lock = threading.Lock()
    served = 0

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Never log request headers, source, or generated text.

        def reply(self, status, body):
            encoded = json.dumps(body, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            try:
                self.wfile.write(encoded)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def do_GET(self):
            if self.path != "/healthz":
                return self.reply(404, {"error": "not_found"})
            return self.reply(200 if time.monotonic() < deadline else 503,
                              {"status": "ok" if time.monotonic() < deadline else "stopping"})

        def do_POST(self):
            nonlocal served
            authorization = self.headers.get("Authorization", "")
            natural = bool(natural_reply and hmac.compare_digest(authorization, "Bearer " + natural_reply["api_key"]))
            if not natural and not hmac.compare_digest(authorization, "Bearer " + api_key):
                return self.reply(401, {"error": "unauthorized"})
            selected_model = natural_reply["model_name"] if natural else model_name
            selected_tokens = 2048 if natural else max_new_tokens
            selected_seconds = 23 if natural else request_seconds
            selected_bytes = 65536 if natural else max_request_bytes
            if self.path != "/v1/chat/completions":
                return self.reply(404, {"error": "not_found"})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= selected_bytes or self.headers.get("Transfer-Encoding"):
                    raise ValueError
                self.connection.settimeout(5)
                request = json.loads(self.rfile.read(length))
                messages = request["messages"]
                piece = 'candidate_format' in request
                ordinary_messages = (isinstance(messages, list) and len(messages) == 2
                    and [m["role"] for m in messages] == ["system", "user"]
                    and all(isinstance(m["content"], str) and m["content"] for m in messages))
                correction_messages = (correction_target_context and natural and not piece
                    and _correction_target_context_messages_valid(messages))
                if (request.get("model") != selected_model or request.get("stream") is not False
                        or type(request.get("max_tokens")) is not int
                        or request["max_tokens"] != selected_tokens or request.get("temperature") != 0
                        or request.get("chat_template_kwargs") != {"enable_thinking": False}
                        or not (ordinary_messages or correction_messages)):
                    raise ValueError
                if piece:
                    if not natural or request['candidate_format'] != PIECE_CANDIDATE_FORMAT:
                        raise ValueError
                    piece_output_schema(messages)
            except Exception:
                return self.reply(400, {"error": "request_invalid"})
            admitted = lock.acquire(timeout=natural_queue_seconds) if natural else lock.acquire(blocking=False)
            if not admitted:
                return self.reply(429, {"error": "busy"})
            try:
                if (max_requests and served >= max_requests) or time.monotonic() >= deadline:
                    return self.reply(429, {"error": "probe_limit"})
                served += 1
                if not max_requests:
                    generation_stage('admitted')
                end = min(deadline, time.monotonic() + selected_seconds)
                text, finish = (generate(messages, end, profile="piece" if piece else "natural")
                                if natural else generate(messages, end))
                if finish not in {"stop", "length"} or not isinstance(text, str):
                    raise ValueError
                status, body = 200, {"model": selected_model, "choices": [{
                    "index": 0, "finish_reason": finish,
                    "message": {"role": "assistant", "content": text}}]}
                if piece:
                    body['candidate_format'] = PIECE_CANDIDATE_FORMAT
                    if piece_revision is not None:
                        body['revision'] = piece_revision
            except Exception as exc:
                if not max_requests:
                    generation_stage('failed_' + type(exc).__name__)
                status, body = 503, {"error": "generation_unavailable"}
            finally:
                lock.release()
            return self.reply(status, body)
    return Handler


def adapter_identity(adapter, weights_sha256=None, config_sha256=None):
    """Verify an explicitly selected saved candidate; never select a new one."""
    if weights_sha256 is None and config_sha256 is None:
        weights_sha256, config_sha256 = FIT38_WEIGHTS, FIT38_CONFIG
    elif (not adapter or not isinstance(weights_sha256, str) or not isinstance(config_sha256, str)
          or not re.fullmatch(r'[0-9a-f]{64}', weights_sha256)
          or not re.fullmatch(r'[0-9a-f]{64}', config_sha256)):
        raise ValueError('adapter_identity_configuration_invalid')
    if not adapter:
        return None
    path = Path(adapter)
    for name, digest in (("adapter_model.safetensors", weights_sha256), ("adapter_config.json", config_sha256)):
        if hashlib.sha256((path / name).read_bytes()).hexdigest() != digest:
            raise ValueError('saved_adapter_identity_changed')
    return weights_sha256, config_sha256


@contextmanager
def base_inference_context(model):
    try:
        with model.disable_adapter():
            yield
    finally:
        # PEFT re-enabling its adapter can also re-enable LoRA gradients.
        # Restore the serving invariant on both successful and failed forwards.
        model.eval()
        model.requires_grad_(False)


@contextmanager
def piece_inference_context(model, process_stop):
    """Use only the separately loaded Piece adapter, then restore Analysis."""
    previous = model.active_adapter
    if previous != 'default':
        raise ValueError('piece_adapter_state_invalid')
    try:
        model.set_adapter(PIECE_ADAPTER_NAME, inference_mode=True)
        model.eval()
        model.requires_grad_(False)
        yield
    finally:
        try:
            model.set_adapter(previous, inference_mode=True)
            model.eval()
            model.requires_grad_(False)
        except BaseException:
            # A failed restoration must not serve Analysis with Piece weights.
            process_stop.set()
            raise


def load_piece_adapter(model, path, *, weights_sha256, config_sha256,
                       analysis_config, analysis_weights):
    """Load an opt-in independent LoRA; never replace or combine adapters."""
    from peft import PeftConfig, get_peft_model_state_dict
    from safetensors.torch import load_file
    import torch
    identity = adapter_identity(path, weights_sha256, config_sha256)
    config = PeftConfig.from_pretrained(path, local_files_only=True)
    expected_config, selected_config = analysis_config.to_dict(), config.to_dict()
    # The fresh Piece training uses the current adapter's structural config,
    # not its learned tensors. Only train/inference mode may differ on disk.
    for value in (expected_config, selected_config):
        value.pop('inference_mode', None)
    if selected_config != expected_config:
        raise ValueError('piece_adapter_scope_changed')
    expected = load_file(Path(path) / 'adapter_model.safetensors')
    if (set(expected) != set(analysis_weights) or len(expected) != 112
            or sum(t.numel() for t in expected.values()) != 3833856
            or any(expected[key].shape != analysis_weights[key].shape for key in expected)):
        raise ValueError('piece_adapter_saved_weights_scope_changed')
    model.load_adapter(path, adapter_name=PIECE_ADAPTER_NAME,
                       is_trainable=False, local_files_only=True)
    actual = get_peft_model_state_dict(model, adapter_name=PIECE_ADAPTER_NAME)
    original = get_peft_model_state_dict(model)
    if (set(actual) != set(expected) or len(actual) != 112
            or sum(t.numel() for t in actual.values()) != 3833856
            or any(not torch.equal(actual[k].detach().cpu(), expected[k]) for k in expected)
            or set(original) != set(analysis_weights)
            or any(not torch.equal(original[k].detach().cpu(), analysis_weights[k])
                   for k in analysis_weights)):
        raise ValueError('piece_adapter_loaded_weights_changed')
    model.set_adapter('default', inference_mode=True)
    adapter_identity(path, *identity)


def load_generator(adapter, process_stop, *, weights_sha256=None, config_sha256=None,
                   max_new_tokens=2048, context_tokens=8192, semantic_json=False,
                   piece_adapter=None, piece_weights_sha256=None, piece_config_sha256=None):
    if (type(max_new_tokens) is not int or type(context_tokens) is not int
            or not 1 <= max_new_tokens < context_tokens <= 32768):
        raise ValueError("model_token_budget_invalid")
    if os.environ.get("HF_HUB_OFFLINE") != "1" or os.environ.get("TRANSFORMERS_OFFLINE") != "1":
        raise ValueError("offline_cache_required")
    if {name: version(name) for name in PINS} != PINS:
        raise ValueError("model_dependency_changed")
    selected_identity = adapter_identity(adapter, weights_sha256, config_sha256)
    if (piece_adapter is not None or piece_weights_sha256 is not None
            or piece_config_sha256 is not None):
        if (not adapter or not piece_adapter or not semantic_json
                or piece_weights_sha256 is None or piece_config_sha256 is None):
            raise ValueError('piece_adapter_configuration_invalid')
        if (Path(piece_adapter).resolve() == Path(adapter).resolve()
                or piece_weights_sha256 == selected_identity[0]):
            raise ValueError('piece_adapter_must_be_separate')
        adapter_identity(piece_adapter, piece_weights_sha256, piece_config_sha256)
    import torch
    from transformers import AutoTokenizer, Qwen3_5ForConditionalGeneration, StoppingCriteria, StoppingCriteriaList
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise ValueError("single_cuda_device_required")
    tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=REVISION,
        local_files_only=True, trust_remote_code=False)
    model = Qwen3_5ForConditionalGeneration.from_pretrained(MODEL, revision=REVISION,
        dtype=torch.bfloat16, device_map={"": 0}, attn_implementation="sdpa",
        local_files_only=True, trust_remote_code=False)
    if adapter:
        path = Path(adapter)
        from peft import PeftConfig, PeftModel, get_peft_model_state_dict
        from peft.tuners.tuners_utils import check_target_module_exists
        from safetensors.torch import load_file
        config = PeftConfig.from_pretrained(path, local_files_only=True)
        if sum(bool(check_target_module_exists(config, name)) for name, _ in model.named_modules()) != 56:
            raise ValueError("fit38_target_scope_changed")
        expected = load_file(path / "adapter_model.safetensors")
        model = PeftModel.from_pretrained(model, path, is_trainable=False, local_files_only=True)
        actual = get_peft_model_state_dict(model)
        if (set(actual) != set(expected) or len(actual) != 112
                or sum(t.numel() for t in actual.values()) != 3833856
                or any(not torch.equal(actual[k].detach().cpu(), expected[k]) for k in expected)):
            raise ValueError("fit38_loaded_weights_changed")
        if piece_adapter is not None:
            load_piece_adapter(model, piece_adapter,
                weights_sha256=piece_weights_sha256, config_sha256=piece_config_sha256,
                analysis_config=config, analysis_weights=expected)
    model.eval()
    model.requires_grad_(False)
    if model.training or any(p.requires_grad for p in model.parameters()):
        raise ValueError("nontraining_model_required")
    if selected_identity:
        adapter_identity(adapter, *selected_identity)
    tokenizer_data = None
    blocked_free_text = set()
    invalid_json_tokens = set()
    if semantic_json:
        private_log_filter = SourcePrivateConstraintLog()
        logging.getLogger().addFilter(private_log_filter)
        for handler in logging.getLogger().handlers:
            handler.addFilter(private_log_filter)
        from lmformatenforcer.integrations.transformers import build_token_enforcer_tokenizer_data
        distribution = __import__('importlib.metadata', fromlist=['distribution']).distribution('lm-format-enforcer')
        origin = json.loads(distribution.read_text('direct_url.json') or '{}')
        if origin.get('vcs_info', {}).get('commit_id') != SEMANTIC_FORMAT_SOURCE:
            raise ValueError('semantic_format_source_changed')
        tokenizer_data = build_token_enforcer_tokenizer_data(tokenizer,
            vocab_size=min(len(tokenizer), model.get_output_embeddings().weight.shape[0]))
        blocked_free_text = {token for token, decoded, _ in tokenizer_data.regular_tokens
            if not decoded.strip() or any(ord(char) < 32 for char in decoded)}
        invalid_json_tokens = {token for token, decoded, _ in tokenizer_data.regular_tokens
            if not decoded or any(ord(char) < 32 for char in decoded)}

    class Deadline(StoppingCriteria):
        def __init__(self, end):
            self.end, self.expired = end, False

        def __call__(self, input_ids, scores, **kwargs):
            self.expired = process_stop.is_set() or time.monotonic() >= self.end
            return self.expired

    def generate(messages, end, *, profile=None):
        if piece_adapter is not None and process_stop.is_set():
            raise ValueError('generation_stopping')
        if profile not in (None, "natural", "piece"):
            raise ValueError("generation_profile_invalid")
        if profile == "piece" and (not semantic_json or tokenizer_data is None):
            raise ValueError("piece_constraint_unavailable")
        use_semantic_json = semantic_json and profile != "natural"
        base_profile = profile in ("natural", "piece")
        output_budget = 2048 if base_profile else max_new_tokens
        context_budget = 8192 if base_profile else context_tokens
        # Preserve the base identity previously connected for natural replies.
        # The analysis adapter stays loaded; its state is restored on context exit.
        adapter_context = (piece_inference_context(model, process_stop)
            if profile == 'piece' and piece_adapter is not None else
            base_inference_context(model) if base_profile and adapter else nullcontext())
        if use_semantic_json:
            generation_stage('tokenize')
        encoded = tokenizer.apply_chat_template(messages, enable_thinking=False,
            add_generation_prompt=True, tokenize=True, return_dict=True,
            return_tensors="pt", truncation=False)
        count = encoded["input_ids"].shape[-1]
        if count + output_budget > context_budget or time.monotonic() >= end:
            raise ValueError("context_or_deadline_exceeded")
        encoded = {k: v.to(model.device) for k, v in encoded.items()}
        stopping = Deadline(end)
        format_options = {}
        if use_semantic_json:
            generation_stage('constraint')
            from lmformatenforcer.integrations.transformers import build_transformers_prefix_allowed_tokens_fn
            allowed_prefix = build_transformers_prefix_allowed_tokens_fn(
                tokenizer_data, (piece_json_parser if profile == "piece" else semantic_json_parser)(
                    messages, tokenizer_data.tokenizer_alphabet))
            previous_allowed = None
            def private_prefix(batch, sent):
                nonlocal previous_allowed
                progress = len(sent) - count
                measured = progress % 128 == 0
                if measured:
                    generation_stage('prefix_enter_' + str(progress))
                if progress and int(sent[-1]) in invalid_json_tokens:
                    raise ValueError('semantic_nontext_token_generated')
                if progress and previous_allowed is not None and int(sent[-1]) not in previous_allowed:
                    generation_stage('prefix_constraint_violation')
                    raise ValueError('semantic_prefix_constraint_violation')
                allowed = semantic_free_text_tokens(allowed_prefix, batch, sent,
                    set() if profile == "piece" else blocked_free_text, invalid_json_tokens)
                previous_allowed = allowed
                if measured:
                    parser = allowed_prefix.token_enforcer.prefix_states[tuple(sent.tolist())].parser
                    key = parser.shortcut_key()
                    mode = 'free' if isinstance(key, tuple) and key[0] == 'json_freetext' else 'other'
                    generation_stage('prefix_exit_' + str(progress) + '_' + type(parser).__name__
                        + '_' + mode + '_allowed_' + str(len(allowed)))
                return allowed
            format_options['prefix_allowed_tokens_fn'] = private_prefix
            format_options['eos_token_id'] = tokenizer_data.eos_token_id
            generation_stage('decode')
        with adapter_context, torch.inference_mode():
            result = model.generate(**encoded, max_new_tokens=output_budget, do_sample=False,
                num_beams=1, use_cache=True, stopping_criteria=StoppingCriteriaList([stopping]), **format_options)
        tokens = result[0, count:]
        eos = tokenizer_data.eos_token_id if use_semantic_json else model.generation_config.eos_token_id
        eos = eos if isinstance(eos, list) else [eos]
        finish = "stop" if len(tokens) and int(tokens[-1]) in eos and not stopping.expired else "length"
        if use_semantic_json:
            generation_stage('complete_' + finish)
            special = set(tokenizer.all_special_ids) | {token for token, value in tokenizer.added_tokens_decoder.items() if value.special}
            generation_stage('special_count_' + str(sum(int(token) in special for token in tokens)))
        return tokenizer.decode(tokens, skip_special_tokens=True, clean_up_tokenization_spaces=False), finish
    return generate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter")
    parser.add_argument("--adapter-weights-sha256")
    parser.add_argument("--adapter-config-sha256")
    parser.add_argument('--piece-adapter')
    parser.add_argument('--piece-adapter-weights-sha256')
    parser.add_argument('--piece-adapter-config-sha256')
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--max-requests", type=int)
    parser.add_argument("--seconds", type=int)
    parser.add_argument("--analysis-service", action="store_true",
                        help="Serve ordinary Analysis until SIGTERM/SIGINT; no probe-count expiry.")
    parser.add_argument('--natural-reply-model', help='Also serve the existing base natural-reply profile with its separate API key.')
    parser.add_argument('--natural-reply-correction-target-context', action='store_true',
                        help='Admit locator-bound AI correction context for the shared natural profile only.')
    parser.add_argument('--semantic-json', action='store_true', help='Constrain Analysis JSON/source-quote pairs and explicit Piece field slots during generation.')
    parser.add_argument("--max-new-tokens", type=int)
    parser.add_argument("--context-tokens", type=int)
    parser.add_argument("--request-seconds", type=int)
    args = parser.parse_args()
    if args.natural_reply_model and not args.analysis_service:
        parser.error('shared natural reply requires explicit analysis service mode')
    if args.natural_reply_correction_target_context and not args.natural_reply_model:
        parser.error('AI correction context requires the shared natural reply profile')
    natural_reply = None
    if args.natural_reply_model:
        natural_key = os.environ.get("EMLIS_NATURAL_REPLY_API_KEY", "")
        if len(natural_key) < 24 or natural_key == os.environ.get("COCOLON_ANALYSIS_MODEL_API_KEY", ""):
            parser.error('shared natural reply requires its separate existing private key')
        natural_reply = {"api_key": natural_key, "model_name": args.natural_reply_model}
    if args.semantic_json and not args.analysis_service:
        parser.error('semantic JSON generation requires explicit analysis service mode')
    if args.analysis_service:
        if args.max_requests is not None or args.seconds is not None:
            parser.error("analysis service and bounded probe lifetime are separate modes")
        max_new_tokens = 4096 if args.max_new_tokens is None else args.max_new_tokens
        context_tokens = 16384 if args.context_tokens is None else args.context_tokens
        request_seconds = 210 if args.request_seconds is None else args.request_seconds
        if (not 1 <= max_new_tokens <= 8192 or not max_new_tokens < context_tokens <= 32768
                or not 1 <= request_seconds <= 210):
            parser.error("analysis service limits invalid")
        if args.adapter and (args.adapter_weights_sha256 is None or args.adapter_config_sha256 is None):
            parser.error("analysis service requires explicit identity for any selected adapter")
    else:
        if (args.max_requests is None or args.seconds is None
                or not 1 <= args.max_requests <= 18 or not 1 <= args.seconds <= 1800):
            parser.error("bounded probe limits required")
        if any(value is not None for value in (args.max_new_tokens, args.context_tokens, args.request_seconds)):
            parser.error("custom inference budgets require explicit analysis service mode")
        max_new_tokens, context_tokens, request_seconds = 2048, 8192, 23
    if args.adapter_weights_sha256 is not None or args.adapter_config_sha256 is not None:
        if (not args.adapter or not re.fullmatch(r'[0-9a-f]{64}', args.adapter_weights_sha256 or '')
                or not re.fullmatch(r'[0-9a-f]{64}', args.adapter_config_sha256 or '')):
            parser.error('an adapter and both SHA256 values are required together')
    piece_options = {}
    if any(value is not None for value in (args.piece_adapter,
            args.piece_adapter_weights_sha256, args.piece_adapter_config_sha256)):
        if (not args.analysis_service or not args.natural_reply_model or not args.semantic_json
                or not args.adapter or not args.piece_adapter
                or not re.fullmatch(r'[0-9a-f]{64}', args.piece_adapter_weights_sha256 or '')
                or not re.fullmatch(r'[0-9a-f]{64}', args.piece_adapter_config_sha256 or '')):
            parser.error('Piece adapter requires the shared constrained service and both SHA256 values')
        piece_options = dict(piece_adapter=args.piece_adapter,
            piece_weights_sha256=args.piece_adapter_weights_sha256,
            piece_config_sha256=args.piece_adapter_config_sha256)
    key = (os.environ.get("COCOLON_ANALYSIS_MODEL_API_KEY", "") if args.analysis_service
           else os.environ.get("EMLIS_NATURAL_REPLY_API_KEY", ""))
    if len(key) < 24:
        parser.error("a private API key of at least 24 characters is required")
    stop = threading.Event()
    deadline = float("inf") if args.analysis_service else time.monotonic() + args.seconds
    # Hard process bound also covers model loading and a blocked GPU forward.
    # No model or adapter is ever being written when this process terminates.
    if not args.analysis_service:
        signal.signal(signal.SIGALRM, signal.SIG_DFL)
        signal.setitimer(signal.ITIMER_REAL, args.seconds)
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    identity_options = (dict(weights_sha256=args.adapter_weights_sha256,
                             config_sha256=args.adapter_config_sha256)
                        if args.adapter_weights_sha256 is not None else {})
    runtime_options = (dict(max_new_tokens=max_new_tokens, context_tokens=context_tokens)
                       if args.analysis_service else {})
    if args.semantic_json:
        runtime_options['semantic_json'] = True
    generator = load_generator(args.adapter, stop, **identity_options, **runtime_options, **piece_options)
    server = ThreadingHTTPServer(("0.0.0.0", args.port), make_handler(generator,
        api_key=key, model_name=args.model_name, deadline=deadline,
        max_requests=0 if args.analysis_service else args.max_requests,
        max_new_tokens=max_new_tokens, request_seconds=request_seconds,
        max_request_bytes=262144 if args.analysis_service else 65536,
        natural_reply=natural_reply,
        correction_target_context=args.natural_reply_correction_target_context,
        piece_revision='piece-lora:' + args.piece_adapter_weights_sha256 if piece_options else None))
    server.timeout = 1
    try:
        while not stop.is_set() and time.monotonic() < deadline:
            server.handle_request()
    finally:
        stop.set()
        server.server_close()


if __name__ == "__main__":
    main()
