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
    assert nucleus.semantic_frame.modality == 'feeling'
    assert nucleus.semantic_frame.polarity == 'positive'
    assert 'operator:uncertainty' not in nucleus.semantic_frame.attribute_codes
    assert any(code.startswith('source_clause_scope:possibility:')
        for code in nucleus.semantic_frame.attribute_codes)
    assert not any(u.dimension == 'source_explicit_epistemic_limit'
        for u in prepared.original_plan.unknown_boundaries)


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
    prepared = prepare_emlis_meaning(request(
        '友達からの誘いを断って、一人で休めたことにほっとした。'
        'でも、もう誘ってもらえなくなるかもしれないと思うと寂しい。'
        '何が不安なのか、私にもまだわからない。'))
    plan = build_updated_grounded_plan(prepared)
    captured = {}
    bind = response._bind_reception_moves
    def capture(*args, **kwargs):
        captured.update(kwargs)
        return bind(*args, **kwargs)
    monkeypatch.setattr(response, '_bind_reception_moves', capture)
    project_thread_meaning(prepared, plan)
    outcome = captured['meaning_outcome']
    binding = captured['binding']
    assert isinstance(outcome, c.LimitedMeaningOutcome)
    contributions = captured['contributions']
    # Add a competing center with the same real semantic refs. It must not
    # re-enter the already selected LIMITED basis merely by overlapping.
    contributions = (*contributions, replace(contributions[0],
        contribution_id='unselected-overlapping-center', retention='OPTIONAL',
        semantic_refs=contributions[0].semantic_refs[:1]))
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


@pytest.mark.parametrize('experience', [
    '友達からの誘いを断って、一人で休めた',
    '予定を調整して、家で過ごせた',
    '宿題を終えて、庭で遊べた',
    '資料を片づけて、机で読めた',
    '一人で休めた', '家で過ごせた', '資料を読めた',
])
def test_nominal_experience_belongs_to_outer_past_feeling(experience):
    source = experience + 'ことにほっとした。'
    prepared = prepare_emlis_meaning(request(source))
    n, = (n for n in prepared.original_plan.nuclei if n.source_fields == ('memo',))
    assert (n.kind, n.semantic_frame.predicate_kind, n.semantic_frame.modality,
            n.semantic_frame.polarity, n.semantic_frame.time_scope) == (
            'reaction', 'feeling', 'feeling', 'positive', 'past')
    assert prepared.thread.resolver().resolve(n.source_span_ids[0]).raw_text == source[:-1]
    assert not prepared.original_plan.relations
    result = MeaningExperienceEngine().generate(request(source))
    assert result.artifact is not None
    assert source[:-1] in result.artifact.observation
    assert result.question is None


@pytest.mark.parametrize('source', [
    'もう誘ってもらえなくなるかもしれないと思うと寂しい',
    'また誘われるかもしれないと思うと嬉しい',
    '失敗するかもしれないと考えると不安だ',
    '参加できないかもしれないと思うと悲しい',
    '間に合わないかも知れないと考えると怖い',
    '参加できるかもしれないと思うと、とても嬉しい',
    '今後は誘ってもらえないかもしれないと考えると寂しい',
    'これからは参加できるかもしれないと思うと嬉しい',
    '今後も間に合わないかも知れないと考えると怖い',
    'これからも誘われるかもしれないと思うと嬉しい',
    '今後は断ってもらえないかもしれないと考えると怖い',
    '今後も言ってくれないかもしれないと思うと寂しい',
])
def test_cognitive_condition_preserves_inner_possibility_and_outer_feeling(source):
    prepared = prepare_emlis_meaning(request(source + '。'))
    n, = (n for n in prepared.original_plan.nuclei if n.source_fields == ('memo',))
    assert n.kind == 'reaction' and n.semantic_frame.predicate_kind == 'feeling'
    assert n.semantic_frame.modality == 'feeling'
    assert n.semantic_frame.time_scope == 'current_input'
    assert 'operator:uncertainty' not in n.semantic_frame.attribute_codes
    scopes = {parts[1]: (int(parts[2]), int(parts[3]), parts[4])
        for code in n.semantic_frame.attribute_codes if code.startswith('source_clause_scope:')
        for parts in (code.split(':'),)}
    assert 'かも' in source[slice(*scopes['possibility'][:2])]
    assert scopes['possibility'][2] == 'under_present_cognition'
    assert source[slice(*scopes['cognitive_condition'][:2])] in {'と', 'と、'}
    assert scopes['feeling'][2] == 'present_feeling'
    assert not any(u.dimension == 'source_explicit_epistemic_limit'
        for u in prepared.original_plan.unknown_boundaries)
    result = MeaningExperienceEngine().generate(request(source + '。'))
    assert result.artifact is not None and source in result.artifact.observation
    assert result.question is None


@pytest.mark.parametrize('source', [
    '友人が一人で休めたことにほっとした。',
    '友人は疲れていた。一人で休めたことにほっとした。',
    '友人は疲れていた。自分は一人で休めたことにほっとした。',
    '手紙を読んだとして、家で休めたことにほっとした。',
    '手紙を読んだって、家で休めたことにほっとした。',
    '資料を捨てたって、家で休めたことにほっとした。',
    '映画を見たって、家で休めたことにほっとした。',
    '友人によれば誘われるかもしれないと思うと寂しい。',
    '友人によれば、誘われるかもしれないと思うと寂しい。',
    '友人も誘われるかもしれないと思うと寂しい。',
    '友人だって誘われるかもしれないと思うと寂しい。',
    '友人こそ誘われるかもしれないと思うと寂しい。',
    '友人に言わせれば誘われるかもしれないと思うと寂しい。',
    '友人に聞けば誘われるかもしれないと思うと寂しい。',
    '友人の話だと誘われるかもしれないと思うと寂しい。',
    '予定を変更しそうで、家で休めたことにほっとした。',
    '手紙を読んだふりをして、家で休めたことにほっとした。',
    '家で休める予定だったことにほっとした。',
    '友人に休んでほしかったことにほっとした。',
    'また誘われるかもしれないと思うと感じる。',
    'また誘われるかもしれないと思うと落ち着く。',
    '友人は誘いを断って、一人で休めたことにほっとした。',
    '誘いを断ったなら、一人で休めたことにほっとした。',
    '誘いを断って、ことにほっとした。',
    '誘いを断って、一人で休めたことにほっとしなかった。',
    '誘いを断って、一人で休めたことにほっとしたかもしれない。',
    '「一人で休めたことにほっとした」と友人が言った。',
    '一人で休めたことにほっとした？',
    '友人の感想です。一人で休めたことにほっとした。',
    'また誘われるかもしれないと思うと寂しくない。',
    'また誘われるかもしれないと思うと嬉しかった。',
    'また誘われるかもしれないと思うと嬉しいかもしれない。',
    'また誘われるかもしれないと思うと、友人は嬉しい。',
    'もし誘われるかもしれないと思うなら嬉しい。',
    '「また誘われるかもしれないと思うと嬉しい」と友人が言った。',
    'また誘われるかもしれないと思うと嬉しい？',
    '友人の感想です。また誘われるかもしれないと思うと嬉しい。',
    '友人は悩んでいた。自分は誘われるかもしれないと思うと嬉しい。',
    '今後は友人も誘われるかもしれないと思うと寂しい。',
    'これからは友人こそ誘われるかもしれないと思うと寂しい。',
    '今後は友人って誘ってもらえないかもしれないと思うと寂しい。',
    '今後は先生ってくれないかもしれないと思うと寂しい。',
    'これからは母ってもらえないかもしれないと思うと寂しい。',
    '今後は資料ってもらえるかもしれないと思うと嬉しい。',
    '友人は今後も誘われるかもしれないと思うと寂しい。',
    '今後は誘われるかもしれないと思うと寂しかった。',
    '今後は誘われるかもしれないと思うと寂しくない。',
    '今後は誘われるかもしれないと思うと寂しいかもしれない。',
    'これからは誘われるかもしれないと思うと、友人は寂しい。',
    '今後はこれからは誘われるかもしれないと思うと寂しい。',
    '「今後は誘われるかもしれないと思うと寂しい」と友人が言った。',
])
def test_nested_feeling_does_not_borrow_report_topic_or_unasserted_host(source):
    plan = prepare_emlis_meaning(request(source)).original_plan
    assert not any(set(n.semantic_frame.attribute_codes) & {
        'lexical:source_cognitive_feeling', 'lexical:source_nominal_past_feeling'}
        for n in plan.nuclei)


PAST_AND_PREDICTED_FEELING = (
    '友達からの誘いを断って、一人で休めたことにほっとした。'
    'でも、もう誘ってもらえなくなるかもしれないと思うと寂しい。')


@pytest.mark.parametrize('source', [PAST_AND_PREDICTED_FEELING,
    '予定を調整して、家で過ごせたことに安心した。でも、失敗するかもしれないと考えると不安だ。',
    '友人の誘いを断って、一人で休めたことにほっとした。でも、今後は誘ってもらえないかもしれないと考えると寂しい。',
    '友人の誘いを断って、一人で休めたことにほっとした。でも、これからは誘ってもらえないかもしれないと考えると寂しい。',
    '宿題を終えて、庭で遊べたことにうれしかった。でも、参加できないかもしれないと思うと悲しい。'])
@pytest.mark.parametrize('unknown', ['', '何が不安なのか、私にもまだわからない。'])
def test_past_and_current_feelings_keep_their_full_objects_and_distinct_times(source, unknown):
    from test_cmee_emlis_received_discourse import actual, inverse
    ctx = actual(request=request(source + unknown))
    result, plan, _, _, _ = ctx
    memo = [n for n in plan.nuclei if n.source_fields == ('memo',) and n.kind == 'reaction']
    assert [(n.semantic_frame.polarity, n.semantic_frame.time_scope) for n in memo] == [
        ('positive', 'past'), ('negative', 'current_input')]
    assert len([r for r in plan.relations if r.type == 'contrast']) == 1
    assert '同時' not in result.artifact.text
    for clause in source.rstrip('。').split('。でも、'):
        assert clause in result.artifact.observation and clause in result.artifact.reception
    assert inverse(ctx, result.artifact.reception, without_author=True).passed
    public = MeaningExperienceEngine().generate(request(source + unknown))
    assert public.artifact is not None and public.artifact.text == result.artifact.text
    assert public.body_sufficiency == ('LIMITED' if unknown else 'SUFFICIENT')
    assert public.question is None
    if unknown:
        assert unknown.rstrip('。') in public.artifact.observation


@pytest.mark.parametrize('unknown', ['', '何が不安なのか、私にもまだわからない。'])
@pytest.mark.parametrize('section,change', [
    ('observation', 'short_left'), ('observation', 'short_right'),
    ('observation', 'possibility'), ('observation', 'condition'),
    ('observation', 'negation'), ('observation', 'past'),
    ('observation', 'reverse'), ('observation', 'simultaneous'),
    ('observation', 'cause'), ('observation', 'extra_claim'),
    ('reception', 'short_left'), ('reception', 'short_right'),
    ('reception', 'possibility'), ('reception', 'condition'),
    ('reception', 'negation'), ('reception', 'past'),
    ('reception', 'reverse'), ('reception', 'cause'),
    ('reception', 'collapse'), ('reception', 'actor'),
    ('reception', 'negative_reception'), ('reception', 'extra_claim'),
])
def test_body_reader_rejects_scope_object_time_and_contrast_loss_without_author(unknown, section, change):
    from types import SimpleNamespace
    from unittest.mock import patch
    import emlis_ai_grounded_human_reception as reception
    import emlis_ai_grounded_observation_gate as gate
    from test_cmee_emlis_received_discourse import actual
    ctx = actual(request=request(PAST_AND_PREDICTED_FEELING + unknown))
    result, plan, sentence, resolver, selected = ctx
    artifact = result.artifact
    before = getattr(artifact, section)
    left, right = PAST_AND_PREDICTED_FEELING.rstrip('。').split('。でも、')
    if change == 'reverse':
        after = before.replace(left, '__LEFT__').replace(right, left).replace('__LEFT__', right)
    elif change == 'simultaneous':
        after = before.replace('の一方で', 'と').replace('とあります。', 'が、異なる向きのまま同時にあります。')
    elif change == 'actor':
        after = '友人が' + before
    elif change == 'extra_claim':
        rows = before.split('\n')
        rows[0] += '承認を求めているのですね。'
        after = '\n'.join(rows)
    else:
        old, new = {
            'short_left': (left, 'ほっとした'),
            'short_right': (right, '寂しい'),
            'possibility': ('かもしれないと思う', 'と思う'),
            'condition': ('と思うと寂しい', 'と思って寂しい'),
            'negation': ('誘ってもらえなくなる', '誘ってもらえる'),
            'past': ('ほっとした', 'ほっとする'),
            'cause': ('の一方で', 'ので') if section == 'observation' else ('こととの違いをどちらの側も残したまま、', 'ことへの原因を'),
            'collapse': ('どちらの側も残したまま、', '結局は寂しさだけを、'),
            'negative_reception': ('感じています。', '感じていません。'),
        }[change]
        after = before.replace(old, new)
    assert before != after
    def read(body):
        return gate.evaluate_grounded_surface_body_inverse(body=body.encode(), plan=plan,
            sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected)
    with patch.object(gate, 'replay_source_grounded_human_reception_from_plan',
                      return_value=SimpleNamespace(text=artifact.reception)) as replay, patch.object(
            reception, '_author_source_grounded_reception_clauses', side_effect=AssertionError('author is not an oracle')):
        assert read(artifact.text).passed
        replay.return_value = SimpleNamespace(text=after if section == 'reception' else artifact.reception)
        rejected = read(artifact.text.replace(before, after))
        assert not rejected.passed
        assert any('replay_mismatch' not in code for code in rejected.failure_codes)


def test_pre_scope_checkpoint_rederives_the_complete_old_meaning_without_relabelling():
    import hashlib
    import json
    from dataclasses import asdict
    # Frozen from API 9d62ab2 using this identical public request, before u319.
    old = {
        'checkpoint_id': 'emlis-checkpoint-85e3cdf91b58b0380a50ea4adc670ed97f0bdaa63f1046b31e3428a62a017910',
        'source_prefix_ref': 'emlis-q3-source-prefix-21fc20af4ab6b6ace394b10c402b799738b5394e9232d2eb55d789b5ed2ba70e',
        'base_meaning_ref': 'emlis-base-meaning-5a03567851fae6f8800b01b0908127b6f396947dc9b255a5533bd4b478093229',
        'answer_update': None, 'assessment_status': 'RESOLVED',
        'accepted_update_refs': [], 'inactive_claim_refs': [], 'unresolved_parts': [],
        'semantic_schema_version': 'cocolon.cmee.emlis_answer_meaning.v1',
    }
    req = request(PAST_AND_PREDICTED_FEELING)
    fresh = prepare_emlis_meaning(req)
    assert not fresh.legacy_cognitive_feeling_scope and fresh.checkpoint.checkpoint_id != old['checkpoint_id']
    frozen = replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=old['checkpoint_id']))
    restored = prepare_emlis_meaning(frozen)
    assert restored.legacy_cognitive_feeling_scope
    assert json.loads(json.dumps(asdict(restored.checkpoint))) == old
    def digest(rows):
        return hashlib.sha256(json.dumps([asdict(row) for row in rows], sort_keys=True,
            separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
    assert digest(restored.original_plan.nuclei) == '48ea8d2206a0ba375d1ff28e5136ffd892b9866e2b7e2679a107426780afcfcb'
    assert digest(restored.original_plan.relations) == 'c74eb08244cd0d9ade3fdbc349e7a7a4d493e29f6d08e8b1864c8b21586e0695'
    result = MeaningExperienceEngine().generate(frozen)
    assert result.artifact is None and json.loads(json.dumps(asdict(result.meaning_checkpoint))) == old
    with pytest.raises(ValueError, match='emlis_checkpoint_source_prefix_mismatch'):
        prepare_emlis_meaning(replace(req, emlis_thread=replace(req.emlis_thread,
            prepared_meaning_checkpoint_ref='foreign-checkpoint')))


@pytest.mark.parametrize('memo,retained', [
    ('すぐに納得し合えたわけではなく、少し気まずい時間もあった。それでも話が終わった後、違うままでも会話を続けられたことにほっとした。',
     '話が終わった後、違うままでも会話を続けられた'),
    ('すれ違った後も、こちらの話を聞く時間を作ってくれたことがうれしかった。全部分かり合えたとは思わないけれど、関係を諦めずに話せたことで少し安心した。',
     '関係を諦めずに話せたことで少し安心した'),
])
def test_existing_nominal_feelings_keep_their_source_owner_and_reception(memo, retained):
    req = request(memo)
    prepared = prepare_emlis_meaning(req)
    assert any('lexical:source_nominal_past_feeling' in n.semantic_frame.attribute_codes
        and n.semantic_frame.polarity == 'positive' and n.semantic_frame.time_scope == 'past'
        for n in prepared.original_plan.nuclei)
    result = MeaningExperienceEngine().generate(req)
    assert result.artifact is not None and retained in result.artifact.reception


@pytest.mark.parametrize('prefix', ['今後は', '今後も', 'これからは', 'これからも'])
def test_temporal_topic_stays_inside_possible_object_and_does_not_expand_bare_cognition(prefix):
    from emlis_ai_grounded_observation_plan import (
        _source_cognitive_feeling_parts, _source_current_cognition_parts)
    cognitive = prefix + '誘われるかもしれないと思う'
    source = cognitive + 'と寂しい'
    parts, polarity = _source_cognitive_feeling_parts(source)
    possibility, = ((a, b, scope) for role, a, b, scope in parts if role == 'possibility')
    assert source[possibility[0]:possibility[1]] == prefix + '誘われるかもしれない'
    assert possibility[2] == 'under_present_cognition' and polarity == 'negative'
    # Bare cognition keeps its pre-u320 admission and ranges. Kana これからも
    # already worked; 今後も had 今 consumed by the outer now prefix.
    bare = _source_current_cognition_parts(cognitive)
    assert (bare is None) == prefix.endswith('は')
    if bare is not None:
        assert bare[0][1] == (1 if prefix == '今後も' else 0)
    legacy = _source_cognitive_feeling_parts(source, _legacy_cognitive_temporal_topic=True)
    assert (legacy is not None) == (prefix == 'これからも')


@pytest.mark.parametrize('old,new', [
    ('今後は', ''), ('今後は', '以前は'),
    ('かもしれない', ''), ('と考えると', 'と考えたときは'),
])
def test_temporal_object_cannot_be_removed_retimed_or_asserted_by_body_reader(old, new):
    from test_cmee_emlis_received_discourse import actual, inverse
    source = ('友人の誘いを断って、一人で休めたことにほっとした。'
              'でも、今後は誘ってもらえないかもしれないと考えると寂しい。')
    context = actual(request=request(source))
    reception = context[0].artifact.reception
    changed = reception.replace(old, new)
    assert changed != reception
    assert not inverse(context, changed, without_author=True).passed


@pytest.mark.parametrize('case_index', range(4))
def test_pre_temporal_topic_checkpoint_keeps_complete_u319_meaning(case_index):
    import hashlib
    import json
    from dataclasses import asdict
    from pathlib import Path
    frozen = json.loads((Path(__file__).parent / 'fixtures' /
        'cmee_emlis_u319_temporal_topic_checkpoint_v1.json').read_text())
    assert frozen['source_commit'] == 'd780c315ddad621120ff6399e5d1e8c05e7a3310'
    row = frozen['cases'][case_index]
    req = request(row['memo'])
    fresh = prepare_emlis_meaning(req)
    changed = row['case_id'] != 'original03'
    assert (fresh.checkpoint.checkpoint_id != row['checkpoint']['checkpoint_id']) == changed
    saved = replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=row['checkpoint']['checkpoint_id']))
    restored = prepare_emlis_meaning(saved)
    assert restored.legacy_cognitive_temporal_topic == changed
    assert not restored.legacy_cognitive_feeling_scope
    assert json.loads(json.dumps(asdict(restored.checkpoint))) == row['checkpoint']
    for name in ('nuclei', 'relations'):
        data = json.dumps([asdict(n) for n in getattr(restored.original_plan, name)],
            ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
        assert hashlib.sha256(data).hexdigest() == row['original_' + name + '_sha256']
    result = MeaningExperienceEngine().generate(saved)
    old = row['public_result']
    assert result.status.value == old['status']
    assert (result.artifact.text if result.artifact else None) == old['body']
    assert list(result.reason_codes) == old['reason_codes']
    assert json.loads(json.dumps(asdict(result.meaning_checkpoint))) == row['checkpoint']
    assert json.loads(json.dumps(asdict(result.question_decision))) == old['question_decision']


# u324: the existing present-feeling/unresolved-reason pair keeps its SELF
# cognitive host. This is not a new reason or an inferred explanation.
FEELING_REASON_SELF_CASES = [
    ('なんだかしんどい。その理由はまだ分からない。',
     'なんだかしんどくて、その理由はまだ分からないのですね。'),
    ('少し怖い。その理由は自分でもまだ分からない。',
     '少し怖くて、その理由はご自身でもまだ分からないのですね。'),
    ('少し怖い。なぜそう感じるのか、私にもよく分からない。',
     '少し怖くて、なぜそう感じるのか、あなたにもよく分からないのですね。'),
    ('なんとなく寂しい。どうしてそう感じるのか、自分でもはっきりわからない。',
     'なんとなく寂しくて、どうしてそう感じるのか、ご自身でもはっきりわからないのですね。'),
    ('私はつらい。その理由が自分にはわからない。',
     'あなたはつらくて、その理由がご自身にはわからないのですね。'),
    ('僕は少し怖い。その理由は僕にもまだ分からない。',
     'あなたは少し怖くて、その理由はあなたにもまだ分からないのですね。'),
    ('何だか重い。その理由は俺にも分からない。',
     '何だか重くて、その理由はあなたにも分からないのですね。'),
]


@pytest.mark.parametrize('memo,expected', FEELING_REASON_SELF_CASES)
def test_feeling_reason_self_scope_delivers_both_present_hosts(memo, expected):
    from test_cmee_emlis_received_discourse import actual
    from test_cmee_emlis_detached_observation import read_body
    from emlis_ai_grounded_observation_plan import _source_feeling_reason_group
    context = actual(request=request(memo))
    outcome, plan, _, _, _ = context
    group = _source_feeling_reason_group(plan.nuclei, plan.relations)
    assert len(group) == 2
    assert group[1].kind == group[1].semantic_frame.predicate_kind == 'uncertainty'
    assert not {'operator:contrast', 'semantic_role:embedded_turn'} & set(group[1].semantic_frame.attribute_codes)
    assert outcome.artifact.reception == expected
    unknown = expected.split('くて、', 1)[1]
    assert unknown in outcome.artifact.observation
    assert read_body(context, outcome.artifact.text).passed
    result = MeaningExperienceEngine().generate(request(memo))
    assert result.artifact.text == outcome.artifact.text
    assert result.question is None and result.question_decision.disposition == 'END'


@pytest.mark.parametrize('memo', [
    '少し怖い。その理由は友人には分からない。',
    '少し怖い。その理由は彼女にも分からない。',
    '友人は少し怖い。その理由は自分でも分からない。',
    '少し怖い。友人はその理由が分からない。',
    '少し怖い。その理由は私が聞いても分からない。',
    '少し怖い。その理由は自分でも分からないと言った。',
    '少し怖い。その理由は自分でも分からないと思う。',
    '少し怖い。その理由は自分でも分からなかった。',
    '少し怖い。その理由は自分でもまだ分からない？',
    '少し怖い。もしその理由は自分でも分からないなら休む。',
    '「少し怖い。その理由は自分でも分からない」と友人が言った。',
    '少し怖い。自分でも何が嫌なのか分からない。',
    'なんだかしんどい。何が嫌なのか、自分でもよくわからない。',
    '少し怖い。行動の理由は自分でも分からない。',
    '少し怖い。昨日の理由は自分でも分からない。',
    '少し怖い。なぜ友人がそう感じるのか、私にも分からない。',
    '少し怖い。寂しい。その理由は自分でも分からない。',
    '少し怖かった。その理由は自分でも分からない。',
    '私も少し怖い。その理由は自分でも分からない。',
])
def test_feeling_reason_self_scope_requires_unique_unreported_current_owner(memo):
    from emlis_ai_grounded_observation_plan import _source_feeling_reason_group
    plan = prepare_emlis_meaning(request(memo)).original_plan
    assert not _source_feeling_reason_group(plan.nuclei, plan.relations)


@pytest.fixture(scope='module')
def feeling_reason_self_context():
    from test_cmee_emlis_received_discourse import actual
    return actual(request=request('私は少し怖い。その理由は自分でもまだよく分からない。'))


@pytest.mark.parametrize('section', ['observation', 'reception'])
@pytest.mark.parametrize('old,new', [
    ('ご自身でも', '私でも'), ('ご自身でも', '彼女でも'), ('ご自身でも', ''),
    ('ご自身でも', 'ご自身には'), ('まだよく', 'まだ'), ('まだよく', ''),
    ('分からない', '分かった'), ('分からない', '分からなかった'),
    ('その理由', '行動の理由'), ('その理由はご自身でもまだよく分からないのですね。', ''),
])
def test_feeling_reason_self_inverse_rejects_changed_owner_scope_or_unknown(feeling_reason_self_context, section, old, new):
    from test_cmee_emlis_detached_observation import read_body
    context = feeling_reason_self_context
    artifact = context[0].artifact
    original = getattr(artifact, section)
    changed = original.replace(old, new)
    assert changed != original
    body = artifact.text.replace(original, changed)
    assert not read_body(context, body).passed


@pytest.mark.parametrize('ending', ['のです。', 'のだと受け取りました。'])
def test_feeling_reason_self_inverse_accepts_equivalent_acknowledgement(feeling_reason_self_context, ending):
    from test_cmee_emlis_received_discourse import inverse
    context = feeling_reason_self_context
    follow = context[0].artifact.reception.replace('のですね。', ending)
    assert inverse(context, follow, without_author=True).passed


@pytest.mark.parametrize('case_index', range(4))
def test_pre_self_reason_checkpoint_rederives_complete_u323_meaning(case_index):
    import hashlib
    import json
    from dataclasses import asdict
    from pathlib import Path
    frozen = json.loads((Path(__file__).parent / 'fixtures' /
        'cmee_emlis_u323_feeling_reason_checkpoint_v1.json').read_text())
    assert frozen['source_commit'] == 'a1925d5d761b397aee9f939fc42a1d9305c4a19f'
    row = frozen['cases'][case_index]
    req = request(row['memo'])
    fresh = prepare_emlis_meaning(req)
    changed = case_index != 3
    assert (fresh.checkpoint.checkpoint_id != row['checkpoint']['checkpoint_id']) == changed
    saved = replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=row['checkpoint']['checkpoint_id']))
    restored = prepare_emlis_meaning(saved)
    assert restored.legacy_feeling_reason_self_scope == changed
    assert not restored.legacy_cognitive_temporal_topic
    assert json.loads(json.dumps(asdict(restored.checkpoint))) == row['checkpoint']
    for name in ('nuclei', 'relations'):
        data = json.dumps([asdict(n) for n in getattr(restored.original_plan, name)],
            ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
        assert hashlib.sha256(data).hexdigest() == row['original_' + name + '_sha256']
    result = MeaningExperienceEngine().generate(saved)
    old = row['public_result']
    assert result.status.value == old['status']
    assert (result.artifact.text if result.artifact else None) == old['body']
    assert list(result.reason_codes) == old['reason_codes']
    assert json.loads(json.dumps(asdict(result.meaning_checkpoint))) == row['checkpoint']
    assert json.loads(json.dumps(asdict(result.question_decision))) == old['question_decision']
    with pytest.raises(ValueError, match='emlis_checkpoint_source_prefix_mismatch'):
        prepare_emlis_meaning(replace(req, emlis_thread=replace(req.emlis_thread,
            prepared_meaning_checkpoint_ref='foreign-feeling-reason-checkpoint')))
