"""A fixed MERGE prompt may be omitted only from the native greedy enforcer's state keys."""
import json

import numpy as np
import pytest
from lmformatenforcer import StringParser, TokenEnforcer, TokenEnforcerTokenizerData, UnionParser

import analysis_merge_wire as wire
from test_analysis_merge_wire import fixture
from test_emlis_natural_reply_probe_http import probe


@pytest.mark.parametrize('phase', ['PLAN', 'NODES', 'RELATIONS'])
def test_only_compact_analysis_merge_uses_generated_history(phase):
    original = fixture(phase)
    messages = wire.prepare_messages(original)
    material = json.loads(messages[1]['content'])
    assert probe._semantic_merge_prefix_offset('event_plan', material, messages, 123) == 123
    for profile in ('piece', 'natural', 'if', 'event_plan_base', None):
        assert probe._semantic_merge_prefix_offset(profile, material, messages, 123) == 0
    original_material = json.loads(original[1]['content'])
    for kind in ('MERGE', 'LEAF', 'WHOLE'):
        original_material['history_stage']['kind'] = kind
        original[1]['content'] = wire.compact_json(original_material)
        assert probe._semantic_merge_prefix_offset('event_plan', original_material, original, 123) == 0
    # A marker on a LEAF cannot claim the optimized MERGE contract.
    material['history_stage']['kind'] = 'LEAF'
    messages[1]['content'] = wire.compact_json(material)
    with pytest.raises(ValueError):
        probe._semantic_merge_prefix_offset('event_plan', material, messages, 123)


def test_every_legal_tokenization_and_end_of_sequence_survives_rekeying():
    vocabulary = ['P', 'a', 'b', 'c', 'ab', 'ac', 'ba', 'z']
    eos = len(vocabulary)
    words = {'ab', 'ac', 'b', 'ba'}
    def decode(ids):
        return ''.join(vocabulary[i] for i in ids)
    data = TokenEnforcerTokenizerData([(i, text, False) for i, text in enumerate(vocabulary)],
                                      decode, eos, False, eos + 1)

    class Prefix:
        def __init__(self):
            self.token_enforcer = TokenEnforcer(data, UnionParser([StringParser(w) for w in sorted(words)]))

        def __call__(self, batch, sent):
            assert batch == 0
            return self.token_enforcer.get_allowed_tokens(sent.tolist()).allowed_tokens

    full, compact = Prefix(), Prefix()
    prompt = [0, 7, 0]
    histories = [()]
    endings = set()
    while histories:
        history = histories.pop()
        complete = np.array([*prompt, *history])
        assert probe._semantic_prefix_input(complete, 0) is complete
        generated = probe._semantic_prefix_input(complete, len(prompt))
        assert generated.tolist() == list(history)
        before = probe.semantic_free_text_tokens(full, 0, complete, set())
        after = probe.semantic_free_text_tokens(compact, 0, generated, set())
        assert after == before
        spelling = decode(history)
        expected = {i for i, text in enumerate(vocabulary)
                    if any(word.startswith(spelling + text) for word in words)}
        if spelling in words:
            endings.add(history)
            expected.add(eos)
        assert set(after) == expected
        histories.extend((*history, token) for token in after if token != eos)
    assert endings == {(1, 2), (1, 3), (2,), (2, 1), (4,), (5,), (6,)}
    assert () in compact.token_enforcer.prefix_states
    assert all(0 not in key for key in compact.token_enforcer.prefix_states)


def test_real_generator_keeps_the_full_model_prompt_and_one_greedy_sequence(monkeypatch):
    import time
    from lmformatenforcer import JsonSchemaParser
    from test_emlis_natural_reply_probe_http import _event_plan_comparison_generator

    generate, captured, _, _, _ = _event_plan_comparison_generator(monkeypatch, input_count=19)
    messages = wire.prepare_messages(fixture())
    monkeypatch.setattr(probe, 'semantic_json_parser', lambda *_: JsonSchemaParser(
        dict(type='object', properties={}, additionalProperties=False)))

    class Inspected(Exception):
        pass

    def inspect_step(**options):
        assert options['input_ids'].shape == (1, 19)
        assert options['do_sample'] is False and options['num_beams'] == 1
        prompt = np.zeros(19, dtype=int)
        callback = options['prefix_allowed_tokens_fn']
        with pytest.raises(ValueError, match='semantic_merge_single_greedy_sequence_required'):
            callback(1, prompt)
        assert callback(0, prompt)
        assert set(captured['format_prefix'].token_enforcer.prefix_states) == {()}
        raise Inspected

    monkeypatch.setattr(captured['model'], 'generate', inspect_step)
    with pytest.raises(Inspected):
        generate(messages, time.monotonic() + 210, profile='event_plan')
    assert captured['tokenize'][0][0] == messages
