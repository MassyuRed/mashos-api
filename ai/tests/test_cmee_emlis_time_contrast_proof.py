"""Whole-field source evidence, not an unbound connective, permits repair."""
from dataclasses import replace
import json
from pathlib import Path
import pytest
import emlis_ai_grounded_observation_plan as gp
from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
from test_cmee_emlis_source_scope_regressions import request


def old_plan(fixture, case):
    rows = json.loads((Path(__file__).parent / 'fixtures' / fixture).read_text())['cases']
    row = next(r for r in rows if r['case'] == case)
    req = request(row['memo'])
    req = replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=row['q3']['checkpoint_id']))
    prepared = prepare_emlis_meaning(req)
    return build_updated_grounded_plan(prepared), prepared.thread.original


@pytest.mark.parametrize('case', ['shikashi', 'shikashi_forward', 'shikashi_then'])
@pytest.mark.parametrize('mutation', [
    'cause', 'foreign_provenance', 'extra_provenance', 'foreign_arc', 'missing_span',
    'inferred', 'optional', 'extra_nucleus', 'other_owner', 'foreign_field',
    'already_fragment', 'unbound_marker', 'wrong_source_slice', 'trailing_claim',
    'quoted_source', 'unproved_time',
])
def test_inline_marker_cannot_relabel_unproved_source_order(case, mutation):
    plan, original = old_plan('cmee_emlis_u342_inline_contrast_v1.json', case)
    nuclei, relations, spans, source = plan.nuclei, plan.relations, original.evidence_spans, original.normalized_current_input
    order = next(r for r in relations if 'whole_input_source_order' in r.source_relation_ids)
    right = next(n for n in nuclei if n.nucleus_id == order.to_nucleus_id)
    kwargs = {
        'cause': {'type': 'user_stated_cause'},
        'foreign_provenance': {'source_relation_ids': ('foreign',)},
        'extra_provenance': {'source_relation_ids': (*order.source_relation_ids, 'foreign')},
        'foreign_arc': {'source_meaning_arc_keys': ('foreign',)},
        'missing_span': {'source_span_ids': order.source_span_ids[:1]},
        'inferred': {'grounding_kind': 'bounded_structural_inference'
            if order.grounding_kind == 'user_stated_relation' else 'user_stated_relation'},
        'optional': {'retention': 'should' if order.retention == 'required' else 'required'},
    }.get(mutation, {})
    relations = tuple(replace(r, **kwargs) if r == order else r for r in relations)
    if mutation == 'extra_nucleus': nuclei = (*nuclei, replace(right, nucleus_id='foreign'))
    elif mutation in {'other_owner', 'unproved_time', 'already_fragment', 'foreign_field'}:
        frame = right.semantic_frame
        frame = replace(frame, **({'actor': 'other'} if mutation == 'other_owner' else
            {'time_scope': 'future'} if mutation == 'unproved_time' else
            {'attribute_codes': (*frame.attribute_codes, 'source_fragment_scalar_range:0:3')}
            if mutation == 'already_fragment' else {}))
        changed = replace(right, semantic_frame=frame,
            source_fields=('answer_text_private',) if mutation == 'foreign_field' else right.source_fields)
        nuclei = tuple(changed if n == right else n for n in nuclei)
    elif mutation in {'unbound_marker', 'wrong_source_slice'}:
        spans = tuple(replace(s, **({'raw_text': s.raw_text.replace('しかし', 'だから')}
            if mutation == 'unbound_marker' else {'start_index': s.start_index + 1}))
            if s.span_id == right.source_span_ids[0] else s for s in spans)
    elif mutation in {'trailing_claim', 'quoted_source'}:
        source = dict(source, memo=source['memo'] + '明日は休みたい。' if mutation == 'trailing_claim'
            else '「' + source['memo'] + '」')
    assert gp._final_source_inline_time_contrast(nuclei, relations, spans, source) == (nuclei, relations)


@pytest.mark.parametrize('mutation', [
    'missing_marker', 'foreign_marker', 'duplicate_marker', 'other_owner',
    'future_time', 'extra_nucleus', 'foreign_field', 'unbound_marker', 'trailing_claim',
])
def test_deictic_phrase_alone_cannot_create_a_past_assertion(mutation):
    plan, original = old_plan('cmee_emlis_u342_past_then_v1.json', 'past_then')
    nuclei, relations, spans, source = plan.nuclei, plan.relations, original.evidence_spans, original.normalized_current_input
    edge = next(r for r in relations if r.type == 'contrast')
    past = next(n for n in nuclei if n.nucleus_id == edge.to_nucleus_id)
    if mutation.endswith('marker') and mutation != 'unbound_marker':
        refs = tuple(r for r in edge.source_relation_ids if not r.startswith('evidence_relation_marker:'))
        refs += () if mutation == 'missing_marker' else ('evidence_relation_marker:foreign',) if mutation == 'foreign_marker' else ('evidence_relation_marker:s2',) * 2
        relations = tuple(replace(r, source_relation_ids=refs) if r == edge else r for r in relations)
    elif mutation == 'extra_nucleus': nuclei = (*nuclei, replace(past, nucleus_id='foreign'))
    elif mutation in {'other_owner', 'future_time', 'foreign_field'}:
        frame = replace(past.semantic_frame, **({'actor': 'other'} if mutation == 'other_owner'
            else {'time_scope': 'future'} if mutation == 'future_time' else {}))
        changed = replace(past, semantic_frame=frame,
            source_fields=('answer_text_private',) if mutation == 'foreign_field' else past.source_fields)
        nuclei = tuple(changed if n == past else n for n in nuclei)
    elif mutation == 'unbound_marker':
        spans = tuple(replace(s, raw_text='でも') if s.span_id == 's2' else s for s in spans)
    else: source = dict(source, memo=source['memo'] + '明日は休みたい。')
    assert gp._final_source_past_then_contrast_nuclei(nuclei, relations, spans, source) == nuclei


def test_unknown_checkpoint_cannot_select_legacy_time_meaning():
    req = request('今は疲れている。しかし、昨日は友達と話せて嬉しかった。')
    checkpoint = prepare_emlis_meaning(req).checkpoint.checkpoint_id
    checkpoint = checkpoint[:-1] + ('0' if checkpoint[-1] != '0' else '1')
    req = replace(req, emlis_thread=replace(req.emlis_thread, prepared_meaning_checkpoint_ref=checkpoint))
    with pytest.raises(ValueError, match='emlis_checkpoint_source_prefix_mismatch'):
        prepare_emlis_meaning(req)


@pytest.fixture(scope='module')
def inline_context():
    from test_cmee_emlis_received_discourse import actual
    return actual(request=request('今は疲れている。しかし、昨日は友達と話せて嬉しかった。'))


@pytest.mark.parametrize('mutation', ['start', 'end', 'missing_range', 'duplicate_range',
    'missing_role', 'foreign_source', 'legacy_range'])
def test_clause_fragment_cannot_erase_time_or_reinterpret_source(inline_context, mutation):
    from test_cmee_emlis_detached_observation import read_body
    result, plan, sentence, resolver, selected = inline_context
    edge = next(r for r in plan.relations if r.retention == 'required')
    target = next(n for n in plan.nuclei if n.nucleus_id == edge.to_nucleus_id)
    codes = target.semantic_frame.attribute_codes
    scalar = next(c for c in codes if c.startswith('source_fragment_scalar_range:'))
    _, start, end = scalar.split(':')
    changed = {
        'start': (f'source_fragment_scalar_range:{int(start) + 3}:{end}',),
        'end': (f'source_fragment_scalar_range:{start}:{int(end) - 1}',),
        'missing_range': (), 'duplicate_range': (scalar, scalar),
    }.get(mutation)
    if changed is not None:
        codes = tuple(c for c in codes if c != scalar) + changed
    elif mutation == 'missing_role': codes = tuple(c for c in codes if c != 'semantic_role:generic_relation_fragment')
    elif mutation == 'foreign_source': codes = tuple('source_fragment_scalar_source:foreign' if c.startswith('source_fragment_scalar_source:') else c for c in codes)
    else: codes = (*codes, 'surface_scalar_range:0:1')
    nuclei = tuple(replace(n, semantic_frame=replace(n.semantic_frame, attribute_codes=codes)) if n == target else n for n in plan.nuclei)
    changed_plan = replace(plan, nuclei=nuclei)
    assert not gp._source_owned_complete_contrast_pair(edge, nuclei,
        resolver.resolve_many(resolver.span_ids), {'memo': '今は疲れている。しかし、昨日は友達と話せて嬉しかった。'})
    assert read_body(inline_context, result.artifact.text).passed
    assert not read_body((result, changed_plan, sentence, resolver, selected), result.artifact.text).passed
