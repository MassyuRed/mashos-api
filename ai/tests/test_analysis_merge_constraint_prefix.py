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


def _request_relation_messages(first, second, report, third, *, version=wire.REQUEST_PROGRESS_VERSION):
    from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
    from test_analysis_merge_transport import _request_progress_material, source_merge
    from test_analysis_occurrence_v17_record_owners import packet

    material = _request_progress_material(first, second, report)
    stage = source_merge([material['fields'][0]['text'], material['fields'][1]['text'], third])
    plan = core.admit_semantic_node_local_v4_plan_response(
        stage, packet(stage, [[[(1, first)]], [[(2, second)]], [[(3, third)]]]), merge_anchors=True)
    messages = core.semantic_node_local_v4_wire_messages(stage, 'NODES', plan=plan)
    codec = wire.response_codec(messages)
    entries = {}
    for name, spec in probe.semantic_output_schema(messages)['properties']['nodes']['properties'].items():
        properties = spec['properties']
        unit = properties['units']['properties']['u1']['properties']
        facts = {key: value['enum'][0] for key, value in unit['fact_parts']['properties'].items()}
        entries[name] = dict(units={'u1': dict(evidence_ref=name+'.u1', source_mode='RECORDED', fact_parts=facts, unknowns=[])},
                             node_kind='STATE_CONTEXT', perspective='SELF', title=properties['title']['enum'][0],
                             meaning=properties['meaning'].get('enum', [''])[0])
    nodes = core.admit_semantic_node_local_v4_nodes_response(stage, plan, dict(
        schema_version=core._semantic_v4_schema('NODES'), plan_sha256=codec.binding, nodes=entries))
    return core.semantic_node_local_v4_wire_messages(stage, 'RELATIONS', plan=plan, nodes=nodes,
                                                      wire_version=version)


@pytest.mark.parametrize('proposal,report,reply,can_follow', [
    ('提案したが、送信したかは確認していない', 'があった', 'に返事をし、家具は注文していない', True),
    ('提案した', 'が届いた', 'が届いたが、まだ返事はしていない', True),
    ('提案した', 'は来ていない', 'に返事をしていない', False),
    ('提案した', 'があったかは分からない', 'に返事をしたかは分からない', False),
    ('提案した', 'が届いたら確認する', 'に返事をする予定だ', False),
    ('提案しなかった', 'が届いた', 'が届いた', False),
])
def test_native_request_decision_and_free_edge_prefixes_retain_source_status(proposal, report, reply, can_follow):
    from test_analysis_node_local_native_profile import advance

    first = '案内所への部品依頼を' + proposal + '。'
    second = '同僚の交換部品の依頼連絡' + reply + '。'
    third = '展示会では、準備の段取りを見直した。'
    messages = _request_relation_messages(first, second, '同僚から交換部品を案内所へ頼んだと連絡' + report + '。', third)
    codec = wire.response_codec(messages)
    pair, = codec.comparisons
    overview = dict(node_refs=['n1', 'n2', 'n3'], title_proposal='', title='3件の記録を振り返って')
    blank = codec.encode(dict(schema_version=wire.MODEL_SCHEMA+'.relations', nodes_sha256=codec.binding,
                              qualification_review={}, edges=[], overview=overview))
    follow = ['FOLLOW_REQUEST', '交換部品', 1, '後の記録では、', 1]
    compare = ['COMPARE', '交換部品', 1, '一方、', 1]
    def raw(decision, edges=()):
        return wire.compact_json(dict(blank, comparisons=[decision], edges=list(edges)))

    alphabet = ''.join(dict.fromkeys(wire.compact_json(messages) + raw(follow) + raw(compare) +
                                    wire.compact_json(wire.COMPARISON_SKIPS) + '先の記録では、 '))
    native = probe.semantic_json_parser(messages, alphabet)
    for decision in (compare, *wire.COMPARISON_SKIPS):
        completed = advance(native, raw(decision))
        assert completed.can_end()
        edges = json.loads(completed.projected_prefix())['edges']
        assert [edge['label'] for edge in edges] == ([first + '一方、' + second] if decision == compare else [])
    prefix = raw(follow).split('FOLLOW_REQUEST', 1)[0]
    assert ('F' in advance(native, prefix).get_allowed_characters()) is can_follow
    if can_follow:
        completed = advance(native, raw(follow))
        assert completed.can_end()
        edge, = json.loads(completed.projected_prefix())['edges']
        assert edge['relation_kind'] == 'SHARED_MEANING' and edge['label'] == first+'後の記録では、'+second

    # A decision to decline the offered pair reserves its sources in both directions.
    reversed_pair = dict(pair, left=pair['right'], right=pair['left'])
    for direction, label in ((pair, first + '後の記録では、' + second), (reversed_pair, second + '後の記録では、' + first)):
        forged = dict(wire.comparison_endpoints(direction), label=label, relation_kind='SHARED_MEANING')
        edge_prefix = raw('DIFFERENT_SUBJECT', [forged]).split('}],"overview"', 1)[0]
        assert '}' not in advance(native, edge_prefix).get_allowed_characters()
    ordinary = dict(wire.comparison_endpoints(pair), to='n3', to_unit='n3.u1', to_source=third[:16],
                    label=first + '後の記録では、' + third, relation_kind='SHARED_MEANING')
    completed = advance(native, raw('DIFFERENT_SUBJECT', [ordinary]))
    assert completed.can_end() and json.loads(completed.projected_prefix())['edges'] == [ordinary]


def test_native_plan_retains_the_prior_speakers_evidence_at_eight_slots():
    from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
    from test_analysis_merge_action_sources import stage_with_action
    from test_analysis_merge_attributed_account import RECEPTION, SELF, WORDS
    from test_analysis_merge_speaker_context import LIMIT, REFERENCE, REPLY, STANCE, WISH
    from test_analysis_node_local_native_profile import accepts
    from test_analysis_occurrence_v17_record_owners import packet

    contact = '準備を終えてから車掌へ短い報告を送り、駅名を確認できるか尋ねた。'
    received = '昼過ぎに駅名が届き、候補の表を作り直した。'
    previous = '途中で、係員が小さな合図を返したことが話題になった。'
    corrected = '私はそこを見落としていたので、返事がなかったという説明を直した。'
    hold = 'ただ、その合図がどんな意図で送られたのかはまだ分からない。'
    first = '監督と希望を話し、自分の解釈を説明した。駅名について車掌へ報告した。'
    second = '返答後に表を書き直した。途中で事実の説明を修正した。'
    memo = '\n\n'.join((WISH+REPLY+LIMIT, STANCE+REFERENCE, SELF, WORDS+RECEPTION,
                        previous+corrected+hold, contact, received))
    stage = stage_with_action(memo, first+second, (SELF, WORDS+RECEPTION, received))
    for version in (wire.REQUEST_SUBJECT_VERSION, wire.REQUEST_PROGRESS_VERSION):
        messages = core.semantic_node_local_v4_wire_messages(stage, wire_version=version)
        codec = wire.response_codec(messages)
        units = [[(2,first), (1,WISH), (1,REPLY+LIMIT), (1,STANCE+REFERENCE)],
                 [(2,second), (1,received), (1,previous+corrected), (1,hold)]]
        def native_accepts(entries):
            return accepts(codec.encode(packet(stage, [entries])), messages)
        assert native_accepts(units)
        for position in (2, 3):
            first_unit = list(units[0])
            first_unit[position] = (1, WORDS+RECEPTION)
            assert not native_accepts([first_unit, units[1]])


@pytest.mark.parametrize('proposal,update,reply,follows', [
    ('提案したが、送ったかは確認していない', 'があった', 'に返事をし、注文はしていない', True),
    ('提案した', 'が届いた', 'が届いたが、まだ返事はしていない', True),
    ('提案しなかった', 'が届いた', 'が届いた', False),
    ('提案した', 'が届いたら確認する', 'に返事をする予定だ', False),
])
def test_native_judgments_share_one_prefix_and_bind_the_reported_request(proposal, update, reply, follows):
    from test_analysis_node_local_native_profile import advance

    left = '案内所への部品依頼を' + proposal + '。'
    right = '同僚の交換部品の依頼連絡' + reply + '。'
    witness = '同僚から交換部品を案内所へ頼んだと連絡' + update + '。'
    messages = _request_relation_messages(left, right, witness, '雑誌の記事を整理した。', version=wire.JUDGMENT_VERSION)
    codec = wire.response_codec(messages)
    candidate, = json.loads(messages[1]['content'])['comparison_candidates']
    assert [candidate[key]['sentences'] for key in ('left', 'right')] == [[left], [right]]
    assert candidate['left']['recorded_on'] < candidate['right']['recorded_on']
    assert candidate['subject'] == '交換部品' and candidate['subject_witness']['recipient'] == '案内所'
    assert candidate['subject_witness']['right']['quote'] == witness
    menu = candidate['judgment_choices']
    kinds = {'対照': 'CONTEXT_CONTRAST', '別件': None, '材料不足': None}
    if follows:
        kinds['同じ依頼の経過'] = 'SHARED_MEANING'
    assert {row[0] for row in menu} == set(kinds)
    assert all(len(row) == 5 and row[1:3] == ['交換部品', 1] and row[4] == 1 for row in menu)
    overview = dict(node_refs=['n1', 'n2', 'n3'], title_proposal='', title='3件の記録を振り返って')
    blank = codec.encode(dict(schema_version=wire.MODEL_SCHEMA + '.relations', nodes_sha256=codec.binding,
                              qualification_review={}, edges=[], overview=overview))
    alphabet = ''.join(dict.fromkeys(wire.compact_json(messages) + wire.compact_json(blank) +
                                    '対同別材先の記録では、別の宛先123 '))
    native = probe.semantic_json_parser(messages, alphabet)
    start = wire.compact_json(blank).split('"comparisons":[', 1)[0] + '"comparisons":[["'
    assert set(advance(native, start).get_allowed_characters()) == {name[0] for name in kinds}
    for choice in menu:
        physical = dict(blank, comparisons=[choice])
        completed = advance(native, wire.compact_json(physical))
        assert completed.can_end()
        logical = codec.decode(physical)
        assert json.loads(completed.projected_prefix()) == logical
        assert codec.encode(logical, comparison_decisions=[choice]) == physical
        kind = kinds[choice[0]]
        assert [(e['relation_kind'], e['from'], e['to'], e['label'])
                for e in logical['edges']] == ([(kind, 'n1', 'n2', left + choice[3] + right)] if kind else [])
    for forged in (['同じ依頼の経過','別の宛先',1,'後の記録では、',1],
                   ['同じ依頼の経過','交換部品',1,'先の記録では、',1],
                   ['別件','交換部品',1,'線なし',2], 'DIFFERENT_SUBJECT'):
        physical = dict(blank, comparisons=[forged])
        with pytest.raises(ValueError):
            advance(native, wire.compact_json(physical))
        with pytest.raises(ValueError):
            codec.decode(physical)


def test_a_different_addressee_does_not_get_a_shared_request_judgment():
    from test_analysis_node_local_native_profile import advance

    messages = _request_relation_messages('案内所への部品依頼を提案した。', '同僚の交換部品の依頼連絡に返事をした。',
        '同僚から交換部品を救護班へ頼んだと連絡があった。', '雑誌の記事を整理した。', version=wire.JUDGMENT_VERSION)
    codec = wire.response_codec(messages)
    assert not codec.comparisons
    blank = codec.encode(dict(schema_version=wire.MODEL_SCHEMA + '.relations', nodes_sha256=codec.binding,
        qualification_review={}, edges=[], overview=dict(node_refs=['n1', 'n2', 'n3'], title_proposal='', title='3件の記録を振り返って')))
    false_review = dict(blank)
    false_review['comparisons'] = [['同じ依頼の経過','交換部品',1,'後の記録では、',1]]
    good, bad = wire.compact_json(blank), wire.compact_json(false_review)
    alphabet = ''.join(dict.fromkeys(wire.compact_json(messages) + good + bad + ' '))
    native = probe.semantic_json_parser(messages, alphabet)
    assert advance(native, good).can_end()
    with pytest.raises(ValueError):
        advance(native, bad)
    with pytest.raises(ValueError):
        codec.decode(false_review)


def test_v10_never_enters_a_reserved_free_edge_without_a_legal_closing_token():
    from test_analysis_node_local_native_profile import advance

    first = '案内所への部品依頼を提案した。'
    second = '同僚の交換部品の依頼連絡に返事をした。'
    third = '展示会では、準備の段取りを見直した。'
    messages = _request_relation_messages(first, second,
        '同僚から交換部品を案内所へ頼んだと連絡があった。', third, version=wire.JUDGMENT_VERSION)
    codec = wire.response_codec(messages)
    pair, = codec.comparisons
    endpoints = wire.comparison_endpoints(pair)
    rejected = dict(endpoints, label=first + '後の記録では、' + second, relation_kind='SHARED_MEANING')
    unrelated = dict(endpoints, to='n3', to_unit='n3.u1', to_source=third[:16],
        label=first + '後の記録では、' + third, relation_kind='SHARED_MEANING')
    offer = next(choice for choice in codec.judgments[0] if choice[0] == '同じ依頼の経過')
    decline = next(choice for choice in codec.judgments[0] if choice[0] == '別件')
    blank = codec.encode(dict(schema_version=wire.MODEL_SCHEMA + '.relations', nodes_sha256=codec.binding,
        qualification_review={}, edges=[], overview=dict(node_refs=['n1', 'n2', 'n3'],
        title_proposal='', title='3件の記録を振り返って')))
    words = wire.compact_json(messages) + wire.compact_json([blank, rejected, unrelated, offer, decline])
    alphabet = ''.join(dict.fromkeys(words))
    native = probe.semantic_json_parser(messages, alphabet)

    def render(decision, edges):
        return wire.compact_json(dict(blank, comparisons=[decision], edges=edges))

    for comparison in (offer, decline):
        for edges in ([], [unrelated]):
            raw = render(comparison, edges)
            completed = advance(native, raw)
            assert completed.can_end()
            assert json.loads(completed.projected_prefix()) == codec.decode(json.loads(raw))
        # Rejection must precede label authoring. At the old terminal check
        # `}` was forbidden only after there was no other edge choice left.
        with pytest.raises(ValueError):
            advance(native, render(comparison, [rejected]).split(',"label":', 1)[0])
