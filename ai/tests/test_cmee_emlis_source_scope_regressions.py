"""Source ownership and post-selection regressions from the 2026-10-17 audit."""

from dataclasses import replace

import pytest

from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine import contracts as c, emlis_stage1_response as response
from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
from emlis_ai_grounded_observation_plan import _has_predicative_constraint_operator
from test_cmee_emlis_q1_thread import initial


def request(memo):
    req = initial(memo)
    return replace(req, execution_mode='EMLIS_APPLICATION',
        emlis_thread=replace(req.emlis_thread, capability_snapshot='Q3_FREE'))


@pytest.mark.parametrize('text,expected', [
    ('遅れるかもしれないと考えている。', False),
    ('遅れるかも知れないという心配がある。', False),
    ('遅れるかもしれないときは連絡する。', False),
    ('また誘われるかもしれないと思うと嬉しい。', False),
    ('もう誘ってもらえなくなるかもしれないと思うと寂しい。', False),
    ('資料を渡さないと困る。', True),
    ('帰らないといけない。', True),
    ('参加できないかもしれないと思う。', True),
    ('遅れるかもしれないと思うが、連絡しないと困る。', True),
    ('間に合うかも知れないと思うが、参加は難しい。', True),
])
def test_possibility_suffix_does_not_own_conditional_constraint(text, expected):
    assert _has_predicative_constraint_operator(text) is expected


def test_possibility_source_retains_uncertainty_without_false_constraint():
    prepared = prepare_emlis_meaning(request('また誘われるかもしれないと思うと嬉しい。'))
    nucleus, = (n for n in prepared.original_plan.nuclei if n.source_fields == ('memo',))
    assert nucleus.kind != 'constraint'
    assert 'operator:constraint' not in nucleus.semantic_frame.attribute_codes
    assert 'operator:uncertainty' in nucleus.semantic_frame.attribute_codes
    # The remaining outer-feeling scope defect is not silently accepted here
    # as a successful understanding of this compound source.


@pytest.mark.parametrize('unknown', [
    '何が嫌なのか、自分でもよくわからない',
    '何が嫌なのか、自分でもはっきり分からない',
    '何が嫌なのか私にもまだわからない',
    'どこが嫌なのか、自分でもよくわからない',
    '何が不安なのか、自分でもよくわからない',
    '何がつらいのか、私にもまだわからない',
])
def test_explicit_self_cognition_keeps_unknown_and_restores_body(unknown):
    req = request('なんだかしんどい。' + unknown + '。')
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    nucleus, = (n for n in plan.nuclei if n.kind == 'uncertainty')
    assert nucleus.semantic_frame.predicate_kind == 'uncertainty'
    assert nucleus.semantic_frame.modality == 'uncertain'
    assert nucleus.semantic_frame.actor == 'current_user'
    boundary, = (b for b in plan.unknown_boundaries if b.dimension == 'source_explicit_epistemic_limit')
    assert boundary.affected_nucleus_ids == (nucleus.nucleus_id,)
    assert boundary.evidence_span_ids == nucleus.source_span_ids
    projection = project_thread_meaning(prepared, plan)
    assert projection.premeaning.material_unknown_refs
    direct = tuple(row for row in projection.premeaning.observation_contribution_rows
        if row.contribution_kind is c.ObservationContributionKind.PRESERVE_UNFINISHED)
    assert len(direct) == 1 and direct[0].retention == 'REQUIRED'
    result = MeaningExperienceEngine().generate(req)
    assert result.artifact is not None
    assert result.body_sufficiency == 'LIMITED'
    assert unknown in result.artifact.observation
    assert result.question is None and result.question_decision.disposition == 'END'


@pytest.mark.parametrize('source', [
    '友達は何が嫌なのか、自分でもよくわからない。',
    '何が嫌なのか、友達は自分でもよくわからない。',
    '「何が嫌なのか、自分でもよくわからない」と友達が言った。',
    '何が嫌なのか、自分でもよくわからないと言った。',
    '何が嫌なのか、自分でもよくわからないと思う。',
    'もし何が嫌なのか、自分でもよくわからないなら休む。',
    '何が嫌なのか、自分でもよくわからなかった。',
    '何が嫌なのか、自分でもよくわからない？',
    '友人の感想です。何が不安なのか、自分でもよくわからない。',
    '友人は話した。何が嫌なのか、自分でもよくわからない。',
    '友人の話。何が嫌なのか、自分でもよくわからない。',
    '友人によると。何が嫌なのか、自分でもよくわからない。',
    '友人は悩んでいた。何が不安なのか、自分でもよくわからない。',
])
def test_self_cognition_does_not_borrow_foreign_reported_or_nonpresent_owner(source):
    plan = prepare_emlis_meaning(request(source)).original_plan
    assert not any(n.kind == n.semantic_frame.predicate_kind == 'uncertainty'
        and n.semantic_frame.actor == 'current_user'
        and n.semantic_frame.time_scope in {'present', 'current_input'}
        for n in plan.nuclei)


def test_limited_reception_uses_selected_basis_and_keeps_required_coverage(monkeypatch):
    from cocolon_meaning_experience_engine.emlis_stage1_composition import Stage1CompositionError
    prepared = prepare_emlis_meaning(request(
        '友達からの誘いを断って、一人で休めたことにほっとした。'
        'でも、もう誘ってもらえなくなるかもしれないと思うと寂しい。'))
    plan = build_updated_grounded_plan(prepared)
    captured = {}
    bind = response._bind_reception_moves
    def capture(*args, **kwargs):
        captured.update(kwargs)
        return bind(*args, **kwargs)
    monkeypatch.setattr(response, '_bind_reception_moves', capture)
    # This original audit case still has a separate unknown-source defect.
    # The selection/binding invariant must hold before that guard stops it.
    with pytest.raises(Stage1CompositionError, match='LIMITED_RECEPTION_CAPABILITY_GAP_STOP'):
        project_thread_meaning(prepared, plan)
    outcome = captured['meaning_outcome']
    binding = captured['binding']
    assert isinstance(outcome, c.LimitedMeaningOutcome)
    contributions = captured['contributions']
    assert any(row.contribution_id not in outcome.retained_layer1_refs for row in contributions)
    reception = plan.response_plan.human_reception_plan
    moves = bind(reception, binding=binding,
        contributions=contributions, meaning_outcome=outcome)
    for move in moves:
        assert {row.contribution_id for row in move.basis_contributions} <= set(outcome.retained_layer1_refs)
        covered = {ref for row in move.basis_contributions for ref in row.semantic_refs}
        required = {response._node_ref(binding.nucleus_to_node[nid])
            for nid in (*move.move.target_nucleus_ids, *move.move.support_nucleus_ids)}
        assert required <= covered
    for retained in ((), tuple(row.contribution_id for row in contributions
            if row.contribution_id not in outcome.retained_layer1_refs)):
        with pytest.raises(c.CMEEStage1ContractError, match='stage1_reception_required_target_unbound'):
            bind(reception, binding=binding,
                contributions=contributions, meaning_outcome=replace(outcome, retained_layer1_refs=retained))


@pytest.mark.parametrize('first', [
    '友達と話せて嬉しかった', '友達と会えて嬉しかった',
    '友人と話せて楽しかった', '散歩できて嬉しかった',
])
def test_short_endpoint_retains_actual_contrast_through_body(first):
    req = request(first + '。でも、疲れた。')
    plan = prepare_emlis_meaning(req).original_plan
    relation, = (r for r in plan.relations if r.retention == 'required')
    assert relation.type == 'contrast' and relation.grounding_kind == 'user_stated_relation'
    assert any(ref.startswith('evidence_relation_marker:') for ref in relation.source_relation_ids)
    result = MeaningExperienceEngine().generate(req)
    assert result.artifact is not None
    assert first in result.artifact.observation and '疲れた' in result.artifact.observation
    assert '異なる向きのまま同時にあります' in result.artifact.observation
    assert 'この順' not in result.artifact.observation


@pytest.mark.parametrize('mutation', ['field', 'direction', 'missing_marker',
    'intervening_source', 'explicit_edge', 'multiple_markers'])
def test_recovered_marker_requires_unique_adjacent_source_and_detector_provenance(mutation):
    from emlis_ai_grounded_observation_plan import _final_stage1_normalize_relation_authority
    prepared = prepare_emlis_meaning(request('友達と話せて嬉しかった。でも、疲れた。'))
    plan = prepared.original_plan
    spans = tuple(prepared.thread.resolver().resolve_many(prepared.thread.resolver().span_ids))
    relation, = (r for r in plan.relations if r.retention == 'required')
    relation = replace(relation, type='attempt_and_block', source_relation_ids=tuple(
        ref for ref in relation.source_relation_ids if not ref.startswith('evidence_relation_marker:')))
    marker, = (s for s in spans if s.detected_type == 'relation_marker')
    if mutation == 'field':
        spans = tuple(replace(s, source_field='memo_action') if s == marker else s for s in spans)
    elif mutation == 'direction':
        relation = replace(relation, from_nucleus_id=relation.to_nucleus_id, to_nucleus_id=relation.from_nucleus_id)
    elif mutation == 'missing_marker':
        spans = tuple(s for s in spans if s != marker)
    elif mutation == 'intervening_source':
        spans += (replace(marker, span_id='intervening', detected_type='event', raw_text='別の出来事'),)
    elif mutation == 'multiple_markers':
        spans += (replace(marker, span_id='second-marker'),)
    else:
        relation = replace(relation, source_relation_ids=('explicit.e1', *relation.source_relation_ids))
    assert _final_stage1_normalize_relation_authority((relation,), plan.nuclei, spans)[0].type == 'attempt_and_block'
