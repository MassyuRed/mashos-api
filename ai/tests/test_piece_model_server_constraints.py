"""Piece transport constraints reuse the serving LMFE path; no model calls."""
from copy import deepcopy
from contextlib import contextmanager, nullcontext
import hashlib
import importlib.metadata
import itertools
import json
import sys
import threading
import time
from http.server import ThreadingHTTPServer
from types import SimpleNamespace

import httpx
import pytest

from test_emlis_natural_reply_probe_http import probe


def messages(keys=('memo_0', 'answer_text_private_1')):
    # Literal content is deliberately distinct from admissible free prose.
    slots = {key: {'literal': '合成の元の記録。', 'source_role':
        'SUPPLEMENTAL_ANSWER' if key.startswith('answer_') else 'ORIGINAL_INPUT'} for key in keys}
    material = dict(core='piece', task='PIECE_MODEL_BODY', control={'field_slots': slots})
    return [dict(role='system', content='合成の指示'),
            dict(role='user', content=json.dumps(material, ensure_ascii=False))]


def accepts(selected_messages, packet):
    # Exercise the actual pinned parser, including its initial Unicode alphabet.
    encoded = json.dumps(packet, ensure_ascii=False)
    parser = probe.piece_json_parser(selected_messages, ''.join(dict.fromkeys(encoded)))
    for char in encoded:
        if char not in parser.get_allowed_characters():
            return False
        parser = parser.add_character(char)
    return parser.can_end()


@pytest.mark.parametrize('keys,expected_order', [(('memo_0',), ('memo_0',)),
    (('memo_action_1', 'memo_0'), ('memo_0', 'memo_action_1')),
    (('memo_action_2', 'memo_1', 'memo_0'), ('memo_0', 'memo_1', 'memo_action_2')),
    (('memo_0', 'answer_text_private_1'), ('answer_text_private_1', 'memo_0'))])
def test_actual_parser_fixes_complete_slot_set_but_never_enumerates_original_text(keys, expected_order):
    selected = messages(keys); before = deepcopy(selected)
    schema = probe.piece_output_schema(selected)
    properties = schema['properties']['field_blocks']['properties']
    assert list(properties) == list(expected_order)
    assert schema['properties']['field_blocks']['required'] == list(expected_order)
    assert all(value == {'type': 'string', 'minLength': 1} for value in properties.values())
    # Source copying and independent wording both stay candidates, not proofs.
    assert accepts(selected, {'field_blocks': {key: '合成の元の記録。' for key in expected_order}})
    assert accepts(selected, {'field_blocks': {key: '私 の新しい文章「a」 "b" C:\\tmp。' for key in expected_order}})
    if len(expected_order) > 1:
        assert not accepts(selected, {'field_blocks': {key: '独立した文章。' for key in reversed(expected_order)}})
    assert selected == before


@pytest.mark.parametrize('input_keys', list(itertools.permutations(
    ('memo_0', 'memo_action_1', 'answer_text_private_2'))))
def test_three_slots_force_answer_then_original_index_order_independent_of_input_order(input_keys):
    selected = messages(input_keys)
    order = ('answer_text_private_2', 'memo_0', 'memo_action_1')
    schema = probe.piece_output_schema(selected)['properties']['field_blocks']
    assert list(schema['properties']) == list(order) and schema['required'] == list(order)
    for output_order in itertools.permutations(order):
        assert accepts(selected, {'field_blocks': {key: '独立した文章。' for key in output_order}}) == (output_order == order)


def test_piece_order_constraint_does_not_change_the_analysis_parser_config():
    selected = [dict(role='system', content='合成の指示'), dict(role='user',
        content=json.dumps({'fields': [{'field': 1, 'text': '合成の記録。'}]}, ensure_ascii=False))]
    assert probe.piece_json_parser(messages(), 'abc').config.force_json_field_order is True
    assert probe.semantic_json_parser(selected, 'abc').config.force_json_field_order is False


@pytest.mark.parametrize('packet', [
    {'field_blocks': {'memo_0': '一つだけ。'}},
    {'field_blocks': {'answer_text_private_1': '二。', 'memo_0': '一。', 'memo_2': '追加。'}},
    {'field_blocks': {'memo_0': '一。', 'memo_action_1': '別欄。'}},
    {'field_blocks': {'answer_text_private_1': '', 'memo_0': '一。'}},
    {'field_blocks': {'answer_text_private_1': None, 'memo_0': '一。'}},
    {'field_blocks': {'answer_text_private_1': ['二。'], 'memo_0': '一。'}},
    {'field_blocks': ['一。', '二。']}, {'body_blocks': ['一。', '二。']},
    {'field_blocks': {'answer_text_private_1': '二。', 'memo_0': '一。'}, 'title': '追加'},
])
def test_actual_parser_rejects_missing_extra_renamed_or_non_string_slot(packet):
    assert not accepts(messages(), packet)


def test_value_linebreaks_and_semantics_remain_receiver_responsibilities():
    # Pinned LMFE pattern strings cannot preserve arbitrary JSON escapes. Do
    # not silently narrow valid quoted prose or claim newline/meaning checks.
    assert accepts(messages(), {'field_blocks': {'answer_text_private_1': '他の人の考え。',
                                                  'memo_0': '一行目\n二行目。'}})


@pytest.mark.parametrize('change', [
    lambda material: material.update(core='analysis'),
    lambda material: material.update(task='OTHER'),
    lambda material: material.update(control=[]),
    lambda material: material['control'].update(field_slots={}),
    lambda material: material['control'].update(field_slots={'memo_0': {}, 'memo_1': {}, 'memo_2': {}, 'memo_3': {}}),
    lambda material: material['control'].update(field_slots={'memo_1': {}}),
    lambda material: material['control'].update(field_slots={'other_0': {}}),
    lambda material: material['control'].update(field_slots={'memo_0': None}),
])
def test_piece_schema_rejects_other_task_and_invalid_slot_identity(change):
    selected = messages(); material = json.loads(selected[1]['content']); change(material)
    selected[1]['content'] = json.dumps(material)
    with pytest.raises(ValueError, match='piece_'):
        probe.piece_output_schema(selected)


def packet(*, marker=True, model='natural', tokens=2048, selected_messages=None):
    result = dict(model=model, max_tokens=tokens, temperature=0, stream=False,
        chat_template_kwargs={'enable_thinking': False}, messages=selected_messages or messages())
    if marker:
        result['candidate_format'] = probe.PIECE_CANDIDATE_FORMAT
    return result


def server_for(generate, *, max_requests=0, piece_revision=None):
    server = ThreadingHTTPServer(('127.0.0.1', 0), probe.make_handler(generate,
        api_key='analysis-test-key', model_name='analysis', deadline=float('inf'),
        max_requests=max_requests, max_new_tokens=4096, request_seconds=210,
        natural_reply={'api_key': 'natural-test-key', 'model_name': 'natural'},
        piece_revision=piece_revision))
    worker = threading.Thread(target=server.serve_forever, daemon=True); worker.start()
    return server, worker


def test_piece_http_requires_explicit_natural_marker_and_does_not_consume_invalid_requests():
    calls = []
    raw = '{"field_blocks":{"answer_text_private_1":"二。","memo_0":"一。"}}'
    def generate(selected, deadline, *, profile=None):
        calls.append((deepcopy(selected), profile))
        assert 20 < deadline - time.monotonic() <= 23
        return raw, 'stop'
    server, worker = server_for(generate, max_requests=1)
    try:
        url = f'http://127.0.0.1:{server.server_port}/v1/chat/completions'
        with httpx.Client(trust_env=False) as client:
            def post(payload, key='natural-test-key'):
                return client.post(url, headers={'Authorization': 'Bearer ' + key}, json=payload)
            for invalid_marker in (None, '', 'body_blocks', True, {'format': probe.PIECE_CANDIDATE_FORMAT}):
                assert post({**packet(), 'candidate_format': invalid_marker}).status_code == 400
            assert post(packet(model='analysis', tokens=4096), key='analysis-test-key').status_code == 400
            assert post(packet(selected_messages=[dict(role='system', content='a'),
                dict(role='user', content='{"core":"analysis","fields":[]}')])).status_code == 400
            assert calls == []
            response = post(packet())
            assert response.status_code == 200
            assert response.json() == dict(model='natural', candidate_format=probe.PIECE_CANDIDATE_FORMAT,
                choices=[dict(index=0, finish_reason='stop', message=dict(role='assistant', content=raw))])
            assert calls == [(messages(), 'piece')]
            assert post(packet()).status_code == 429
    finally:
        server.shutdown(); server.server_close(); worker.join(3)


def test_markerless_natural_and_analysis_keep_original_response_bytes():
    calls = []
    def generate(selected, deadline, *, profile=None):
        calls.append(profile)
        return '合成の返事です。', 'stop'
    server, worker = server_for(generate)
    try:
        url = f'http://127.0.0.1:{server.server_port}/v1/chat/completions'
        with httpx.Client(trust_env=False) as client:
            for model, tokens, key in [('natural', 2048, 'natural-test-key'),
                                       ('analysis', 4096, 'analysis-test-key')]:
                response = client.post(url, headers={'Authorization': 'Bearer ' + key},
                    json=packet(marker=False, model=model, tokens=tokens))
                expected = {'model': model, 'choices': [{'index': 0, 'finish_reason': 'stop',
                    'message': {'role': 'assistant', 'content': '合成の返事です。'}}]}
                assert response.status_code == 200
                assert response.content == json.dumps(expected, ensure_ascii=False).encode()
        assert calls == ['natural', None]
    finally:
        server.shutdown(); server.server_close(); worker.join(3)


def test_unavailable_piece_constraint_returns_no_marker_and_never_falls_back():
    calls = []
    def generate(selected, deadline, *, profile=None):
        calls.append(profile)
        raise ValueError('piece_constraint_unavailable')
    server, worker = server_for(generate)
    try:
        response = httpx.post(f'http://127.0.0.1:{server.server_port}/v1/chat/completions',
            trust_env=False, headers={'Authorization': 'Bearer natural-test-key'}, json=packet())
        assert response.status_code == 503
        assert response.json() == {'error': 'generation_unavailable'}
        assert calls == ['piece']
    finally:
        server.shutdown(); server.server_close(); worker.join(3)


def test_piece_adapter_revision_is_server_owned_and_never_added_to_other_profiles():
    calls = []
    revision = 'piece-lora:' + 'c' * 64
    def generate(selected, deadline, *, profile=None):
        calls.append(profile)
        return 'synthetic-raw', 'stop'
    server, worker = server_for(generate, piece_revision=revision)
    try:
        url = f'http://127.0.0.1:{server.server_port}/v1/chat/completions'
        with httpx.Client(trust_env=False) as client:
            for profile, model, tokens, key in [('piece', 'natural', 2048, 'natural-test-key'),
                    ('natural', 'natural', 2048, 'natural-test-key'),
                    (None, 'analysis', 4096, 'analysis-test-key')]:
                payload = packet(marker=profile == 'piece', model=model, tokens=tokens)
                payload['revision'] = 'client-controlled-value'
                response = client.post(url, headers={'Authorization': 'Bearer ' + key}, json=payload)
                expected = dict(model=model, choices=[dict(index=0, finish_reason='stop',
                    message=dict(role='assistant', content='synthetic-raw'))])
                if profile == 'piece':
                    expected.update(candidate_format=probe.PIECE_CANDIDATE_FORMAT, revision=revision)
                assert response.status_code == 200
                assert response.content == json.dumps(expected, ensure_ascii=False).encode()
        assert calls == ['piece', 'natural', None]
    finally:
        server.shutdown(); server.server_close(); worker.join(3)


def synthetic_generator(monkeypatch, *, constrained, input_count=1, with_piece_adapter=False,
                        raw_output=None):
    """Load the real serving closure with a CPU-only deterministic stand-in."""
    from lmformatenforcer.tokenenforcer import TokenEnforcer, TokenEnforcerTokenizerData
    raw = (raw_output if raw_output is not None else
        '{"field_blocks":{"answer_text_private_1":"別の文章。","memo_0":"私 の文章。"}}')
    if with_piece_adapter:
        raw = raw.replace('私 の', '私の')
    alphabet = ''.join(dict.fromkeys('P' + raw + '\n'))
    token_ids = {char: index for index, char in enumerate(alphabet)}
    eos = len(alphabet)
    data = TokenEnforcerTokenizerData([(i, char, False) for i, char in enumerate(alphabet)],
        lambda tokens: ''.join(alphabet[i] for i in tokens if i < eos), eos, False, eos + 1)
    captured = {'generate': [], 'tokenize': []}
    class Sent(list):
        def tolist(self):
            return list(self)
    class Encoded:
        shape = (1, input_count)
        def to(self, device):
            return self
    class Result:
        def __init__(self, tokens):
            self.tokens = tokens
        def __getitem__(self, index):
            row, selection = index
            assert row == 0
            return self.tokens[selection]
    class Tokenizer:
        all_special_ids = [eos, 999]
        added_tokens_decoder = {}
        def __len__(self):
            return eos + 1
        def apply_chat_template(self, selected, **kwargs):
            captured['tokenize'].append((deepcopy(selected), kwargs))
            return {'input_ids': Encoded()}
        def decode(self, tokens, **kwargs):
            assert kwargs == dict(skip_special_tokens=True, clean_up_tokenization_spaces=False)
            return ''.join(alphabet[i] for i in tokens if i < eos)
    class Model:
        training = False
        device = 'synthetic-cpu'
        active_adapter = 'default'
        adapter_enabled = True
        grads = False
        generation_config = SimpleNamespace(eos_token_id=999)
        def eval(self):
            self.training = False
        def requires_grad_(self, enabled):
            assert enabled is False
            self.grads = enabled
        def parameters(self):
            return []
        def named_modules(self):
            return [(f'target_{i}', None) for i in range(56)]
        def set_adapter(self, name, *, inference_mode=False):
            assert name in ('default', probe.PIECE_ADAPTER_NAME)
            self.active_adapter = name
            self.grads = not inference_mode
        @contextmanager
        def disable_adapter(self):
            self.adapter_enabled = False
            try:
                yield
            finally:
                self.adapter_enabled = True
                self.grads = True
        def get_output_embeddings(self):
            return SimpleNamespace(weight=SimpleNamespace(shape=(eos + 1,)))
        def generate(self, **kwargs):
            captured['generate'].append(kwargs)
            if with_piece_adapter:
                captured['adapter_states'].append((self.active_adapter,
                    self.adapter_enabled, self.grads, self.training))
            generated_eos = kwargs.get('eos_token_id', 999)
            sequence = Sent([token_ids['P']] * input_count)
            for token in [token_ids[char] for char in raw] + [generated_eos]:
                if 'prefix_allowed_tokens_fn' in kwargs:
                    assert token in kwargs['prefix_allowed_tokens_fn'](0, sequence)
                sequence.append(token)
            return Result(sequence)
    tokenizer, model = Tokenizer(), Model()
    transformer_stub = SimpleNamespace(AutoTokenizer=SimpleNamespace(from_pretrained=lambda *_a, **_k: tokenizer),
        Qwen3_5ForConditionalGeneration=SimpleNamespace(from_pretrained=lambda *_a, **_k: model),
        StoppingCriteria=object, StoppingCriteriaList=list)
    torch_stub = SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: True, device_count=lambda: 1),
        bfloat16='synthetic-bf16', inference_mode=nullcontext)
    if with_piece_adapter:
        weights = synthetic_weights('analysis')
        config = SimpleNamespace(to_dict=lambda: {'structural_config': 'fixed'})
        monkeypatch.setitem(sys.modules, 'peft', SimpleNamespace(
            PeftConfig=SimpleNamespace(from_pretrained=lambda *_a, **_k: config),
            PeftModel=SimpleNamespace(from_pretrained=lambda *_a, **_k: model),
            get_peft_model_state_dict=lambda *_a, **_k: weights))
        monkeypatch.setitem(sys.modules, 'peft.tuners.tuners_utils', SimpleNamespace(
            check_target_module_exists=lambda *_: True))
        monkeypatch.setitem(sys.modules, 'safetensors.torch', SimpleNamespace(load_file=lambda *_: weights))
        torch_stub.equal = lambda left, right: left == right
        monkeypatch.setattr(probe, 'adapter_identity', lambda *_a, **_k: ('a' * 64, 'b' * 64))
        def load_piece(selected, path, **kwargs):
            assert selected is model and path == 'piece-cpu'
            assert kwargs == dict(weights_sha256='c' * 64, config_sha256='d' * 64,
                analysis_config=config, analysis_weights=weights)
        monkeypatch.setattr(probe, 'load_piece_adapter', load_piece)
        captured['adapter_states'] = []
        captured['model'] = model
    class Prefix:
        def __init__(self, selected_data, parser):
            assert selected_data is data
            self.token_enforcer = TokenEnforcer(data, parser)
        def __call__(self, batch, sent):
            return self.token_enforcer.get_allowed_tokens(sent.tolist()).allowed_tokens
    monkeypatch.setitem(sys.modules, 'torch', torch_stub)
    monkeypatch.setitem(sys.modules, 'transformers', transformer_stub)
    monkeypatch.setitem(sys.modules, 'lmformatenforcer.integrations.transformers', SimpleNamespace(
        build_token_enforcer_tokenizer_data=lambda *_a, **_k: data,
        build_transformers_prefix_allowed_tokens_fn=Prefix))
    monkeypatch.setattr(importlib.metadata, 'distribution', lambda name: SimpleNamespace(
        read_text=lambda filename: json.dumps({'vcs_info': {'commit_id': probe.SEMANTIC_FORMAT_SOURCE}})))
    monkeypatch.setattr(probe, 'version', lambda name: probe.PINS[name])
    monkeypatch.setenv('HF_HUB_OFFLINE', '1'); monkeypatch.setenv('TRANSFORMERS_OFFLINE', '1')
    options = dict(piece_adapter='piece-cpu', piece_weights_sha256='c' * 64,
                   piece_config_sha256='d' * 64) if with_piece_adapter else {}
    generator = probe.load_generator('analysis-cpu' if with_piece_adapter else None,
        threading.Event(), max_new_tokens=4096,
        context_tokens=16384, semantic_json=constrained, **options)
    return generator, captured, raw, eos


def test_piece_generation_uses_actual_mask_single_generate_base_budget_and_mask_eos(monkeypatch):
    generator, captured, raw, eos = synthetic_generator(monkeypatch, constrained=True)
    assert generator(messages(), time.monotonic() + 23, profile='piece') == (raw, 'stop')
    assert len(captured['generate']) == 1
    options = captured['generate'][0]
    assert options['max_new_tokens'] == 2048 and options['eos_token_id'] == eos
    assert options['do_sample'] is False and options['num_beams'] == 1
    assert callable(options['prefix_allowed_tokens_fn'])
    assert captured['tokenize'][0] == (messages(), dict(enable_thinking=False,
        add_generation_prompt=True, tokenize=True, return_dict=True, return_tensors='pt', truncation=False))


def test_piece_mask_unavailable_fails_before_tokenization_or_generation(monkeypatch):
    generator, captured, _, _ = synthetic_generator(monkeypatch, constrained=False)
    with pytest.raises(ValueError, match='piece_constraint_unavailable'):
        generator(messages(), time.monotonic() + 23, profile='piece')
    assert captured == {'generate': [], 'tokenize': []}


@pytest.mark.parametrize('constrained', [False, True])
def test_normal_natural_generation_remains_unconstrained_with_its_existing_budget(monkeypatch, constrained):
    generator, captured, raw, _ = synthetic_generator(monkeypatch, constrained=constrained)
    assert generator(messages(), time.monotonic() + 23, profile='natural') == (raw, 'stop')
    assert len(captured['generate']) == 1
    options = captured['generate'][0]
    assert options['max_new_tokens'] == 2048
    assert 'prefix_allowed_tokens_fn' not in options and 'eos_token_id' not in options


def test_piece_cannot_borrow_the_larger_analysis_context_budget(monkeypatch):
    generator, captured, _, _ = synthetic_generator(monkeypatch, constrained=True, input_count=6145)
    with pytest.raises(ValueError, match='context_or_deadline_exceeded'):
        generator(messages(), time.monotonic() + 23, profile='piece')
    assert captured['generate'] == []


class SyntheticWeight:
    def __init__(self, value, size=1):
        self.value, self.size = value, size
        self.shape = (size,)
    def numel(self):
        return self.size
    def detach(self):
        return self
    def cpu(self):
        return self
    def __eq__(self, other):
        return isinstance(other, SyntheticWeight) and (self.value, self.size) == (other.value, other.size)


def synthetic_weights(value):
    return {f'lora_{i}': SyntheticWeight(value, 3833856 - 111 if i == 0 else 1)
            for i in range(112)}


def test_optional_piece_adapter_is_selected_only_for_piece_and_restored_before_base_or_analysis(monkeypatch):
    generator, captured, raw, _ = synthetic_generator(monkeypatch, constrained=True,
        with_piece_adapter=True)
    # This tests routing through the serving closure, not Analysis semantics.
    monkeypatch.setattr(probe, 'semantic_json_parser', probe.piece_json_parser)
    for profile in (None, 'piece', 'natural', None, 'piece', None):
        assert generator(messages(), time.monotonic() + 23, profile=profile) == (raw, 'stop')
        assert captured['model'].active_adapter == 'default'
        assert captured['model'].grads is False and captured['model'].training is False
    assert captured['adapter_states'] == [
        ('default', True, False, False), ('piece', True, False, False),
        ('default', False, False, False), ('default', True, False, False),
        ('piece', True, False, False), ('default', True, False, False)]
    assert [row['max_new_tokens'] for row in captured['generate']] == [4096, 2048, 2048, 4096, 2048, 4096]


@pytest.mark.parametrize('failure', ['generate', 'select', 'restore'])
def test_piece_adapter_failure_restores_analysis_or_stops_serving(monkeypatch, failure):
    generator, captured, _, _ = synthetic_generator(monkeypatch, constrained=True,
        with_piece_adapter=True)
    model = captured['model']
    original_select = model.set_adapter
    def select(name, **kwargs):
        if failure == 'select' and name == 'piece' or failure == 'restore' and name == 'default':
            raise RuntimeError('synthetic selection failure')
        original_select(name, **kwargs)
    monkeypatch.setattr(model, 'set_adapter', select)
    if failure == 'generate':
        monkeypatch.setattr(model, 'generate', lambda **_: (_ for _ in ()).throw(RuntimeError('synthetic generation failure')))
    with pytest.raises(RuntimeError):
        generator(messages(), time.monotonic() + 23, profile='piece')
    if failure == 'restore':
        with pytest.raises(ValueError, match='generation_stopping'):
            generator(messages(), time.monotonic() + 23, profile='natural')
    else:
        assert model.active_adapter == 'default' and model.grads is False and model.training is False


def adapter_loader_fixture(monkeypatch, tmp_path):
    folder = tmp_path / 'piece'
    folder.mkdir()
    (folder / 'adapter_model.safetensors').write_bytes(b'synthetic-independent-piece-weights')
    (folder / 'adapter_config.json').write_text('{"synthetic":"configuration"}')
    identity = tuple(hashlib.sha256((folder / name).read_bytes()).hexdigest()
        for name in ('adapter_model.safetensors', 'adapter_config.json'))
    config_values = dict(r=8, target_modules={'fixed_q', 'fixed_mlp'}, inference_mode=False)
    config = SimpleNamespace(to_dict=lambda: deepcopy(config_values))
    analysis_config = SimpleNamespace(to_dict=lambda: dict(r=8,
        target_modules={'fixed_q', 'fixed_mlp'}, inference_mode=True))
    original, expected = synthetic_weights('analysis'), synthetic_weights('piece')
    class Model:
        active_adapter = 'default'
        loaded = []
        def load_adapter(self, path, **kwargs):
            self.loaded.append((path, kwargs))
        def set_adapter(self, name, **kwargs):
            assert name == 'default' and kwargs == {'inference_mode': True}
            self.active_adapter = name
    model = Model()
    states = {'default': deepcopy(original), 'piece': deepcopy(expected)}
    monkeypatch.setitem(sys.modules, 'peft', SimpleNamespace(
        PeftConfig=SimpleNamespace(from_pretrained=lambda path, **kwargs: config),
        get_peft_model_state_dict=lambda selected, adapter_name='default': states[adapter_name]))
    monkeypatch.setitem(sys.modules, 'safetensors.torch', SimpleNamespace(load_file=lambda _: expected))
    monkeypatch.setitem(sys.modules, 'torch', SimpleNamespace(equal=lambda left, right: left == right))
    def load(**changes):
        options = dict(weights_sha256=identity[0], config_sha256=identity[1],
            analysis_config=analysis_config, analysis_weights=original)
        options.update(changes)
        return probe.load_piece_adapter(model, folder, **options)
    return load, model, config_values, states, expected


def test_piece_loading_retains_analysis_weights_and_uses_a_distinct_frozen_adapter(monkeypatch, tmp_path):
    load, model, _, states, expected = adapter_loader_fixture(monkeypatch, tmp_path)
    before = deepcopy(states['default'])
    load()
    assert model.loaded == [(tmp_path / 'piece', dict(adapter_name='piece',
        is_trainable=False, local_files_only=True))]
    assert states['default'] == before and states['piece'] == expected
    assert model.active_adapter == 'default'


@pytest.mark.parametrize('damage', ['hash', 'scope', 'saved_shape', 'loaded_piece', 'analysis'])
def test_piece_loading_refuses_wrong_identity_scope_or_modified_adapter_weights(monkeypatch, tmp_path, damage):
    load, model, config, states, expected = adapter_loader_fixture(monkeypatch, tmp_path)
    if damage == 'scope':
        config['r'] = 16
    elif damage == 'saved_shape':
        expected['lora_0'].shape = (1,)
    elif damage == 'loaded_piece':
        states['piece']['lora_1'] = SyntheticWeight('changed')
    elif damage == 'analysis':
        states['default']['lora_1'] = SyntheticWeight('changed')
    with pytest.raises(ValueError):
        load(**({'weights_sha256': '0' * 64} if damage == 'hash' else {}))
    if damage in ('hash', 'scope', 'saved_shape'):
        assert model.loaded == []


@pytest.mark.parametrize('analysis,piece,weights,constrained', [
    (None, 'piece', 'c' * 64, True), ('analysis', 'piece', 'c' * 64, False),
    ('analysis', 'analysis', 'c' * 64, True), ('analysis', 'piece', 'a' * 64, True),
])
def test_piece_loader_refuses_missing_shared_constraint_or_reusing_analysis_before_model_load(
        monkeypatch, analysis, piece, weights, constrained):
    monkeypatch.setenv('HF_HUB_OFFLINE', '1'); monkeypatch.setenv('TRANSFORMERS_OFFLINE', '1')
    monkeypatch.setattr(probe, 'version', lambda name: probe.PINS[name])
    monkeypatch.setattr(probe, 'adapter_identity', lambda *_a, **_k: ('a' * 64, 'b' * 64))
    with pytest.raises(ValueError, match='piece_adapter_'):
        probe.load_generator(analysis, threading.Event(), semantic_json=constrained,
            piece_adapter=piece, piece_weights_sha256=weights, piece_config_sha256='d' * 64)


@pytest.mark.parametrize('extra', [
    ['--piece-adapter', 'piece'], ['--piece-adapter-weights-sha256', 'c' * 64],
    ['--piece-adapter', 'piece', '--piece-adapter-weights-sha256', 'c' * 64,
     '--piece-adapter-config-sha256', 'd' * 64],
])
def test_piece_cli_rejects_incomplete_or_non_shared_configuration_before_loading(monkeypatch, extra):
    monkeypatch.setenv('COCOLON_ANALYSIS_MODEL_API_KEY', 'synthetic-analysis-private-key')
    monkeypatch.setattr(sys, 'argv', ['serve', '--analysis-service', '--model-name', 'analysis'] + extra)
    monkeypatch.setattr(probe, 'load_generator', lambda *_a, **_k: pytest.fail('invalid Piece configuration loaded'))
    with pytest.raises(SystemExit) as exc:
        probe.main()
    assert exc.value.code == 2


def test_piece_cli_passes_explicit_identity_without_changing_analysis_selection(monkeypatch):
    class Loaded(Exception):
        pass
    captured = {}
    def load(adapter, stop, **kwargs):
        captured.update(adapter=adapter, **kwargs)
        raise Loaded
    monkeypatch.setenv('COCOLON_ANALYSIS_MODEL_API_KEY', 'synthetic-analysis-private-key')
    monkeypatch.setenv('EMLIS_NATURAL_REPLY_API_KEY', 'synthetic-natural-private-key')
    monkeypatch.setattr(probe, 'load_generator', load)
    monkeypatch.setattr(probe.signal, 'signal', lambda *_: None)
    monkeypatch.setattr(sys, 'argv', ['serve', '--analysis-service', '--model-name', 'analysis',
        '--adapter', 'analysis-path', '--adapter-weights-sha256', 'a' * 64,
        '--adapter-config-sha256', 'b' * 64, '--natural-reply-model', 'natural', '--semantic-json',
        '--piece-adapter', 'piece-path', '--piece-adapter-weights-sha256', 'c' * 64,
        '--piece-adapter-config-sha256', 'd' * 64])
    with pytest.raises(Loaded):
        probe.main()
    assert captured == dict(adapter='analysis-path', weights_sha256='a' * 64,
        config_sha256='b' * 64, semantic_json=True, max_new_tokens=4096, context_tokens=16384,
        piece_adapter='piece-path', piece_weights_sha256='c' * 64, piece_config_sha256='d' * 64)
