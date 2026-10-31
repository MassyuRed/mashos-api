"""Bounded, private probe server for the existing local Qwen3.5-4B cache.

No training, downloads, provider fallback, or automatic request retry. This is
an explicit personal connection probe, not the production hosting decision.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.metadata import version
import json
import os
from pathlib import Path
import signal
import threading
import time

MODEL = "Qwen/Qwen3.5-4B"
REVISION = "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"
FIT38_WEIGHTS = "ad8b89e8974df9bfe7e804b8f67bbaac59e6cbb37042c3254fb58ffb64230d0a"
FIT38_CONFIG = "ef4b1aef621fb4e234ce6a05601efb62a987c3cf5d40f3995ca1b72200bab145"
PINS = {"transformers": "5.19.0", "peft": "0.21.2", "accelerate": "1.15.0", "safetensors": "0.8.0"}


def make_handler(generate, *, api_key, model_name, deadline, max_requests):
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

        def do_POST(self):
            nonlocal served
            if not hmac.compare_digest(self.headers.get("Authorization", ""), "Bearer " + api_key):
                return self.reply(401, {"error": "unauthorized"})
            if self.path != "/v1/chat/completions":
                return self.reply(404, {"error": "not_found"})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 65536:
                    raise ValueError
                self.connection.settimeout(5)
                request = json.loads(self.rfile.read(length))
                messages = request["messages"]
                if (request.get("model") != model_name or request.get("stream") is not False
                        or request.get("max_tokens") != 2048 or request.get("temperature") != 0
                        or request.get("chat_template_kwargs") != {"enable_thinking": False}
                        or not isinstance(messages, list) or len(messages) != 2
                        or [m["role"] for m in messages] != ["system", "user"]
                        or any(not isinstance(m["content"], str) or not m["content"] for m in messages)):
                    raise ValueError
            except Exception:
                return self.reply(400, {"error": "request_invalid"})
            if not lock.acquire(blocking=False):
                return self.reply(429, {"error": "busy"})
            try:
                if served >= max_requests or time.monotonic() >= deadline:
                    return self.reply(429, {"error": "probe_limit"})
                served += 1
                text, finish = generate(messages, min(deadline, time.monotonic() + 23))
                if finish not in {"stop", "length"} or not isinstance(text, str):
                    raise ValueError
                return self.reply(200, {"model": model_name, "choices": [{
                    "index": 0, "finish_reason": finish,
                    "message": {"role": "assistant", "content": text}}]})
            except Exception:
                return self.reply(503, {"error": "generation_unavailable"})
            finally:
                lock.release()
    return Handler


def load_generator(adapter, process_stop):
    if os.environ.get("HF_HUB_OFFLINE") != "1" or os.environ.get("TRANSFORMERS_OFFLINE") != "1":
        raise ValueError("offline_cache_required")
    if {name: version(name) for name in PINS} != PINS:
        raise ValueError("model_dependency_changed")
    if adapter:
        path = Path(adapter)
        for name, digest in (("adapter_model.safetensors", FIT38_WEIGHTS), ("adapter_config.json", FIT38_CONFIG)):
            if hashlib.sha256((path / name).read_bytes()).hexdigest() != digest:
                raise ValueError("fit38_saved_identity_changed")
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
    model.eval()
    model.requires_grad_(False)
    if model.training or any(p.requires_grad for p in model.parameters()):
        raise ValueError("nontraining_model_required")

    class Deadline(StoppingCriteria):
        def __init__(self, end):
            self.end, self.expired = end, False

        def __call__(self, input_ids, scores, **kwargs):
            self.expired = process_stop.is_set() or time.monotonic() >= self.end
            return self.expired

    def generate(messages, end):
        encoded = tokenizer.apply_chat_template(messages, enable_thinking=False,
            add_generation_prompt=True, tokenize=True, return_dict=True,
            return_tensors="pt", truncation=False)
        count = encoded["input_ids"].shape[-1]
        if count + 2048 > 8192 or time.monotonic() >= end:
            raise ValueError("context_or_deadline_exceeded")
        encoded = {k: v.to(model.device) for k, v in encoded.items()}
        stopping = Deadline(end)
        with torch.inference_mode():
            result = model.generate(**encoded, max_new_tokens=2048, do_sample=False,
                num_beams=1, use_cache=True, stopping_criteria=StoppingCriteriaList([stopping]))
        tokens = result[0, count:]
        eos = model.generation_config.eos_token_id
        eos = eos if isinstance(eos, list) else [eos]
        finish = "stop" if len(tokens) and int(tokens[-1]) in eos and not stopping.expired else "length"
        return tokenizer.decode(tokens, skip_special_tokens=True, clean_up_tokenization_spaces=False), finish
    return generate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter")
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--max-requests", type=int, required=True)
    parser.add_argument("--seconds", type=int, required=True)
    args = parser.parse_args()
    if not 1 <= args.max_requests <= 18 or not 1 <= args.seconds <= 1800:
        parser.error("bounded probe limits required")
    key = os.environ.get("EMLIS_NATURAL_REPLY_API_KEY", "")
    if len(key) < 24:
        parser.error("a private API key of at least 24 characters is required")
    stop = threading.Event()
    deadline = time.monotonic() + args.seconds
    # Hard process bound also covers model loading and a blocked GPU forward.
    # No model or adapter is ever being written when this process terminates.
    signal.signal(signal.SIGALRM, signal.SIG_DFL)
    signal.setitimer(signal.ITIMER_REAL, args.seconds)
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    generator = load_generator(args.adapter, stop)
    server = ThreadingHTTPServer(("0.0.0.0", args.port), make_handler(generator,
        api_key=key, model_name=args.model_name, deadline=deadline, max_requests=args.max_requests))
    server.timeout = 1
    try:
        while not stop.is_set() and time.monotonic() < deadline:
            server.handle_request()
    finally:
        stop.set()
        server.server_close()


if __name__ == "__main__":
    main()
