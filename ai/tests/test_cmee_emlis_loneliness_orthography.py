"""The bounded kana adjective keeps source bytes and prior meanings intact."""
from dataclasses import replace
import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
import emlis_ai_grounded_observation_plan as gp
import emlis_ai_grounded_sentence_surface as surface
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.emlis_answer_update import (
    prepare_emlis_meaning, build_updated_grounded_plan, _prepare_emlis_meaning_from_plan)
from cocolon_meaning_experience_engine.emlis_question import original_meaning_plan
from cocolon_meaning_experience_engine.emlis_thread_source import admit_emlis_thread
from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
from test_cmee_emlis_source_scope_regressions import request
from test_cmee_emlis_q1_thread import initial
from test_cmee_emlis_received_discourse import actual
from test_cmee_emlis_detached_observation import read_body
from test_cmee_emlis_relief_cognition import facets
from test_cmee_emlis_contrast_degree import digest
from test_cmee_emlis_time_contrast_source import (
    with_checkpoint, assert_source_unchanged, assert_whole_meaning_matches,
    assert_delivery_matches)


BASELINE = json.loads((Path(__file__).parent / 'fixtures' /
    'cmee_emlis_u343_loneliness_orthography_v1.json').read_text())
QUALIFIED = {'kana', 'unknown', 'self', 'boku_unknown', 'slight', 'very',
    'continuing', 'relief_anz', 'past_possible', 'future_topic', 'unknown_jibun',
    'unknown_past', 'with_question'}
# These sources retain a valid relief/loneliness pair; their separate unknown
# still prevents delivery. Unqualified pairs remain completely unchanged.
OTHER_CHANGED = {'unknown_other', 'unknown_causal'}
CHANGED = QUALIFIED | OTHER_CHANGED


def old_prepare(req):
    thread = admit_emlis_thread(req)
    return _prepare_emlis_meaning_from_plan(req, thread, original_meaning_plan(
        thread, _legacy_cognitive_feeling_orthography=True)).checkpoint


def selection_or_error(prepared, plan):
    try:
        return project_thread_meaning(prepared, plan).selected_reception, None
    except ValueError as error:
        return None, str(error)


@pytest.mark.parametrize('q1', [False, True], ids=['q3', 'q1'])
@pytest.mark.parametrize('row', BASELINE['cases'], ids=lambda row: row['case'])
def test_current_recognition_preserves_source_and_existing_qualification(row, q1):
    assert BASELINE['source_commit'] == '3b7b590bc10e28abf4606bba198c3e0d0e704290'
    frozen = row['q1' if q1 else 'q3']
    req = (initial if q1 else request)(row['memo'])
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    out = MeaningExperienceEngine().generate(req)
    if not q1 and (folder := os.environ.get('CMEE_LONELINESS_BODY_DIR')):
        Path(folder).mkdir(parents=True, exist_ok=True)
        Path(folder, row['case'] + '.json').write_text(json.dumps(dict(
            case=row['case'], memo=row['memo'], body=out.artifact.text if out.artifact else None,
            reasons=list(out.reason_codes)), ensure_ascii=False))
    assert_source_unchanged(prepared, frozen)
    if row['case'] not in CHANGED:
        assert_whole_meaning_matches(prepared, plan, frozen)
        assert_delivery_matches(out, frozen)
        return
    assert prepared.checkpoint.checkpoint_id != frozen['checkpoint_id']
    assert not prepared.legacy_cognitive_feeling_orthography
    selected, error = selection_or_error(prepared, plan)
    if row['case'] in QUALIFIED:
        assert error is None and facets(selected)
        assert out.artifact and 'さびしい' in out.artifact.observation
        assert '私も少し安心しましたが' in out.artifact.reception
        assert '今、耳を傾けていたいです' in out.artifact.reception
        assert 'かもしれない' in out.artifact.observation
        if row['case'] == 'with_question':
            assert out.question and out.question_decision.disposition != 'END'
            assert '褒められた' in out.artifact.observation
            assert '嬉しくなかった' in out.artifact.observation
        else:
            assert out.question is None and out.question_decision.disposition == 'END'
    else:
        assert selected is None or not facets(selected)
        if row['case'] in {'unknown_other', 'unknown_causal'}:
            assert out.artifact is None and error is not None
        elif out.artifact:
            assert '私も少し安心しましたが' not in out.artifact.reception
            assert '今、耳を傾けていたいです' not in out.artifact.reception
    assert not out.automatic_progression
    restored_req = with_checkpoint(req, prepared.checkpoint.checkpoint_id)
    restored = prepare_emlis_meaning(restored_req)
    restored_plan = build_updated_grounded_plan(restored)
    assert digest(restored.checkpoint) == digest(prepared.checkpoint)
    assert digest(restored_plan) == digest(plan)
    assert_source_unchanged(restored, frozen)
    restored_selected, restored_error = selection_or_error(restored, restored_plan)
    assert digest(restored_selected) == digest(selected) and restored_error == error
    restored_out = MeaningExperienceEngine().generate(restored_req)
    assert restored_out.artifact == out.artifact
    assert restored_out.question == out.question
    assert restored_out.question_decision == out.question_decision
    assert restored_out.reason_codes == out.reason_codes


@pytest.mark.parametrize('q1', [False, True], ids=['q3', 'q1'])
@pytest.mark.parametrize('row', BASELINE['cases'], ids=lambda row: row['case'])
def test_u343_checkpoint_restores_full_meaning_selection_and_delivery(row, q1):
    frozen = row['q1' if q1 else 'q3']
    fresh = (initial if q1 else request)(row['memo'])
    assert digest(old_prepare(fresh)) == frozen['checkpoint_sha']
    req = with_checkpoint(fresh, frozen['checkpoint_id'])
    prepared = prepare_emlis_meaning(req)
    assert prepared.legacy_cognitive_feeling_orthography == (row['case'] in CHANGED)
    assert_whole_meaning_matches(prepared, build_updated_grounded_plan(prepared), frozen)
    assert_delivery_matches(MeaningExperienceEngine().generate(req), frozen)


@pytest.fixture(scope='module', params=['very', 'unknown_jibun'])
def context(request):
    row = next(row for row in BASELINE['cases'] if row['case'] == request.param)
    return actual(request=initial(row['memo']))


@pytest.mark.parametrize('mutation', ['feeling', 'certainty', 'source_owner',
    'relief_polarity', 'reaction', 'listening', 'unselected_prediction', 'context_target'])
def test_independent_body_reader_keeps_feeling_facets_and_unknown(context, mutation):
    artifact = context[0].artifact
    body = artifact.text
    if mutation == 'feeling':
        changed = body.replace('さびしい', '嬉しい').replace('さびしさ', '嬉しさ')
    elif mutation == 'certainty':
        changed = body.replace('かもしれない', 'に違いない')
    elif mutation == 'source_owner':
        changed = body.replace('一人で休めた', '友達が休めた')
    elif mutation == 'relief_polarity':
        changed = body.replace('ほっとした', 'ほっとしなかった')
    elif mutation == 'reaction':
        changed = body.replace('私も少し安心しましたが、', '')
    elif mutation == 'listening':
        changed = body.replace('今、耳を傾けていたいです', '違いを感じています')
    elif mutation == 'unselected_prediction':
        changed = body + 'きっとまた誘ってもらえます。'
    elif 'とてもさびしい' in body:
        changed = body.replace('とてもさびしい', 'さびしい')
    else:
        changed = body.replace('何が嫌なのか、ご自身でもよくわからないのですね。', '')
    assert changed != body
    with patch.object(surface, '_realize_line', side_effect=AssertionError('no surface oracle')):
        assert read_body(context, body).passed
        assert not read_body(context, changed).passed


@pytest.mark.parametrize('feeling', ['さびしい', 'さびしいです', '少しだけさびしい',
    'とてもさびしい', 'ずっとさびしい'])
def test_finite_kana_host_preserves_original_scalar_boundaries(feeling):
    antecedent = 'もう誘ってもらえなくなるかもしれないと思うと'
    fragment = antecedent + feeling
    assert gp._source_cognitive_feeling_parts(
        fragment, _legacy_cognitive_feeling_orthography=True) is None
    parts, polarity = gp._source_cognitive_feeling_parts(fragment)
    assert polarity == 'negative'
    role, start, end, scope = next(part for part in parts if part[0] == 'feeling')
    assert (role, start, end, scope) == ('feeling', len(antecedent), len(fragment), 'present_feeling')
    assert fragment[start:end] == feeling
    assert all(0 <= start < end <= len(fragment) for _, start, end, _ in parts)


@pytest.mark.parametrize('fragment', [
    'もう誘ってもらえなくなるかもしれないと思うとさびしくない',
    'もう誘ってもらえなくなるかもしれないと思うとさびしかった',
    'もう誘ってもらえなくなるかもしれないと思うとさびしい？',
    'もう誘ってもらえなくなるかもしれないと思うとさびしいなら休みたい',
    'もう誘ってもらえなくなるかもしれないと思うとさびしいかもしれない',
    'もう誘ってもらえなくなるかもしれないと思うとさびしいと聞いた',
    'もう誘ってもらえなくなるかもしれないと思うとさびしいふりをした',
    'もう誘ってもらえなくなるかもしれないと思ったのでさびしい',
    '「もう誘ってもらえなくなるかもしれないと思うとさびしい」',
    '友達によると、もう誘ってもらえなくなるかもしれないと思うとさびしい',
])
def test_inspection_normalization_does_not_expand_finite_or_owner_grammar(fragment):
    assert gp._source_cognitive_feeling_parts(fragment) is None


@pytest.fixture(scope='module')
def old_kana_context():
    row = next(row for row in BASELINE['cases'] if row['case'] == 'kana')
    prepared = prepare_emlis_meaning(with_checkpoint(request(row['memo']), row['q3']['checkpoint_id']))
    return build_updated_grounded_plan(prepared), prepared.thread.original


@pytest.mark.parametrize('mutation', ['raw_slice', 'owner', 'contrast', 'negative_left', 'foreign_field'])
def test_new_spelling_cannot_bypass_existing_relief_pair_source_proof(old_kana_context, mutation):
    plan, original = old_kana_context
    nuclei, relations, spans = plan.nuclei, plan.relations, original.evidence_spans
    edge, = (edge for edge in relations if edge.type == 'contrast' and edge.retention == 'required')
    left = next(nucleus for nucleus in nuclei if nucleus.nucleus_id == edge.from_nucleus_id)
    right = next(nucleus for nucleus in nuclei if nucleus.nucleus_id == edge.to_nucleus_id)
    marker = 'lexical:source_cognitive_feeling'
    assert marker not in right.semantic_frame.attribute_codes

    def recognize(test_nuclei, test_relations, test_spans):
        return gp._final_source_current_cognition_nuclei(test_nuclei, test_spans,
            original.normalized_current_input, relations=test_relations,
            _legacy_cognitive_self_continuation=False)

    proved = recognize(nuclei, relations, spans)
    assert marker in next(n.semantic_frame.attribute_codes for n in proved if n.nucleus_id == right.nucleus_id)
    if mutation == 'raw_slice':
        spans = tuple(replace(span, start_index=span.start_index + 1)
            if span.span_id == right.source_span_ids[0] else span for span in spans)
    elif mutation == 'contrast':
        relations = tuple(replace(relation, type='user_stated_cause')
            if relation == edge else relation for relation in relations)
    elif mutation == 'negative_left':
        nuclei = tuple(replace(n, semantic_frame=replace(n.semantic_frame, polarity='negative'))
            if n == left else n for n in nuclei)
    elif mutation == 'owner':
        nuclei = tuple(replace(n, semantic_frame=replace(n.semantic_frame, actor='other'))
            if n == right else n for n in nuclei)
    else:
        nuclei = tuple(replace(n, source_fields=('answer_text_private',))
            if n == right else n for n in nuclei)
    assert recognize(nuclei, relations, spans) == nuclei
