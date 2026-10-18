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
        assert clause in result.artifact.observation
        if 'その寂しさにも' not in result.artifact.reception:
            assert clause in result.artifact.reception
    if 'その寂しさにも' in result.artifact.reception:
        # Approved joint retention: the independent reader must resolve both
        # short references from the complete actual Layer-1 source clauses.
        assert any('source_relief_cognition_anaphora:v1' in n.semantic_frame.attribute_codes for n in memo)
        assert 'と聞いて、私も少し安心しましたが、その寂しさにも、今、耳を傾けていたいです。' in result.artifact.reception
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
    if section == 'reception' and 'その寂しさにも' in before:
        old, new = {
            'short_left': ('ほっとしたと聞いて、', ''),
            'short_right': ('その寂しさにも、', ''),
            'possibility': ('その寂しさ', '必ず誘われない寂しさ'),
            'condition': ('その寂しさ', '現実に誘われなくなった寂しさ'),
            'negation': ('その寂しさ', 'その嬉しさ'),
            'past': ('ほっとした', 'ほっとする'),
            'reverse': ('ほっとしたと聞いて、', 'その寂しさと聞いて、'),
            'cause': ('と聞いて、', 'ので、'),
            'collapse': ('ほっとしたと聞いて、私も少し安心しましたが、', ''),
            'actor': ('私も少し', '友人も少し'),
            'negative_reception': ('安心しましたが', '安心しませんでしたが'),
            'extra_claim': ('です。', 'です。承認を求めているのですね。'),
        }[change]
        after = before.replace(old, new)
    elif change == 'reverse':
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
    from test_cmee_emlis_detached_observation import read_body
    body = context[0].artifact.text
    changed = body.replace(old, new)
    assert changed != body
    assert not read_body(context, changed).passed


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
    new_reference = any('source_relief_cognition_anaphora:v1' in n.semantic_frame.attribute_codes
                        for n in fresh.original_plan.nuclei)
    assert (fresh.checkpoint.checkpoint_id != row['checkpoint']['checkpoint_id']) == (changed or new_reference)
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
    new_reference = any('source_relief_cognition_anaphora:v1' in n.semantic_frame.attribute_codes
                        for n in fresh.original_plan.nuclei)
    assert (fresh.checkpoint.checkpoint_id != row['checkpoint']['checkpoint_id']) == (changed or new_reference)
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


# u325: restore both already-selected objects, without converting wh-object
# uncertainty into a reason or altering the selected subjective proposition.
@pytest.mark.parametrize('case_index', range(10))
def test_unknown_object_receives_selected_sources_with_unchanged_saved_meaning(case_index):
    import hashlib
    import json
    from dataclasses import asdict
    from pathlib import Path
    from test_cmee_emlis_received_discourse import actual
    from test_cmee_emlis_detached_observation import read_body
    frozen = json.loads((Path(__file__).parent / 'fixtures' /
        'cmee_emlis_u324_unknown_object_checkpoint_v1.json').read_text())
    assert frozen['source_commit'] == '0f78a0e25dd74a40aaedb28327658799ee1aa43b'
    row = frozen['cases'][case_index]
    req = request(row['memo'])
    req = replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=row['checkpoint']['checkpoint_id']))
    p = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(p)
    projection = project_thread_meaning(p, plan)
    def digest(obj):
        return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assert json.loads(json.dumps(asdict(p.checkpoint))) == row['checkpoint']
    for name in ('nuclei', 'relations'):
        assert digest([asdict(n) for n in getattr(plan, name)]) == row[name + '_sha256']
    selected = asdict(projection.selected_reception)
    # Reference realization participates in the grounding seal. Its identity
    # must be renewed; the complete selected semantic content stays identical.
    assert digest({k:v for k,v in selected.items() if k not in {'input_ref', 'grounding_ref'}}) == row['selected_content_sha256']
    assert selected['input_ref'] != row['selected_input_ref']
    assert selected['grounding_ref'] != row['grounding_ref']
    context = actual(request=req)
    result = context[0]
    assert result.artifact.text != row['body']
    assert result.artifact.observation == row['body'].split('\n\nEmlisから：\n')[0].split('見えたこと：\n')[1]
    follow = result.artifact.reception
    assert '今ここに置かれた言葉' not in follow and 'まだ定まらないこと' not in follow
    first, second = row['memo'].rstrip('。').split('。')
    assert first.replace('私は', 'あなたは')[:-1] + 'くて、' in follow
    assert second.replace('自分自身', 'ご自身').replace('自分', 'ご自身').replace('私', 'あなた') + 'のですね。' in follow
    assert read_body(context, result.artifact.text).passed
    public = MeaningExperienceEngine().generate(req)
    assert public.artifact.text == result.artifact.text
    assert json.loads(json.dumps(asdict(public.question_decision))) == row['question_decision']
    assert public.question is None


@pytest.fixture(scope='module')
def unknown_object_context():
    from test_cmee_emlis_received_discourse import actual
    return actual(request=request('私は少し怖い。何が嫌なのか、自分でもまだよく分からない。'))


@pytest.mark.parametrize('old,new', [
    ('あなたは', '私は'), ('あなたは', '彼女は'), ('あなたは', ''),
    ('少し怖くて', 'とても怖くて'), ('少し怖くて', '少し寂しくて'),
    ('怖くて、', '怖いから、'), ('怖くて、', '怖いのに、'),
    ('怖くて、', '怖かったので、'), ('怖くて、', '怖くなくて、'),
    ('何が嫌なのか', '何が不安なのか'), ('何が嫌なのか', 'なぜ怖いのか'),
    ('何が嫌なのか、', ''), ('ご自身でも', '私でも'), ('ご自身でも', '友人でも'),
    ('ご自身でも', 'ご自身には'), ('ご自身でも', ''),
    ('まだよく', 'まだ'), ('まだよく', 'よく'), ('まだよく', ''),
    ('分からない', '分かった'), ('分からない', '分からなかった'),
    ('あなたは少し怖くて、', ''),
    ('何が嫌なのか、ご自身でもまだよく分からない', ''),
])
def test_unknown_object_independent_inverse_rejects_lost_or_changed_source(unknown_object_context, old, new):
    from test_cmee_emlis_detached_observation import read_body
    context = unknown_object_context
    artifact = context[0].artifact
    changed = artifact.reception.replace(old, new)
    assert changed != artifact.reception
    assert not read_body(context, artifact.text.replace(artifact.reception, changed)).passed


@pytest.mark.parametrize('ending', ['のです。', 'のだと受け取りました。'])
def test_unknown_object_independent_inverse_accepts_equivalent_receipt(unknown_object_context, ending):
    from test_cmee_emlis_received_discourse import inverse
    follow = unknown_object_context[0].artifact.reception.replace('のですね。', ending)
    assert inverse(unknown_object_context, follow, without_author=True).passed


@pytest.mark.parametrize('memo', [
    'なんだかしんどい。その理由は自分でもよくわからない。',
    'なんだかしんどい。なぜしんどいのか、自分でもよくわからない。',
    'なんだかしんどい。何が嫌なのか、友人にも分からない。',
    '友人はなんだかしんどい。何が嫌なのか、自分でもよくわからない。',
    'なんだかしんどい。何が嫌なのか、自分でもよくわからないと言った。',
    'なんだかしんどい。何が嫌なのか、自分でもよくわからないと思う。',
    'なんだかしんどい。何が嫌なのか、自分でもよくわからなかった。',
    'なんだかしんどい。何が嫌なのか、自分でもよくわからない？',
    'なんだかしんどい。もし何が嫌なのか、自分でもよくわからないなら休む。',
    '「なんだかしんどい。何が嫌なのか、自分でもよくわからない」と友人が言った。',
    '友人の話。なんだかしんどい。何が嫌なのか、自分でもよくわからない。',
    'なんだかしんどい。何が嫌なのか、自分でもよくわからない。眠い。',
    'なんだかしんどい？何が嫌なのか、自分でもよくわからない。',
    'なんだかしんどかった。何が嫌なのか、自分でもよくわからない。',
    '何が嫌なのか、自分でもよくわからない。',
])
def test_unknown_object_full_source_boundaries_do_not_borrow_new_grammar(memo):
    from emlis_ai_grounded_observation_plan import _source_unknown_object_group_from_resolver
    from emlis_ai_grounded_human_reception import _project_source_grounded_reception_move_realization
    p = prepare_emlis_meaning(request(memo))
    plan, resolver = build_updated_grounded_plan(p), p.thread.resolver()
    assert not _source_unknown_object_group_from_resolver(plan.nuclei, plan.relations, resolver)
    reception = plan.response_plan.human_reception_plan
    if reception:
        for move in reception.moves:
            # Already explicit references cannot bypass the complete field proof.
            concrete = replace(move, reference_mode='short_anchor_if_ambiguous')
            new_reception = replace(reception, moves=tuple(concrete if m == move else m for m in reception.moves))
            new_plan = replace(plan, response_plan=replace(plan.response_plan, human_reception_plan=new_reception))
            try:
                ir = _project_source_grounded_reception_move_realization(new_reception, concrete,
                    {n.nucleus_id: n for n in plan.nuclei}, resolver, plan=new_plan,
                    recovery_stage='full', clause_form='FINITE')
            except ValueError:
                continue
            assert not any(c.startswith('source-unknown-object:') for c in ir.nominalization_plan)
    # Exercise the ordinary public path too; no availability claim is made for
    # out-of-family sources whose existing result can be unavailable.
    result = MeaningExperienceEngine().generate(request(memo))
    if result.artifact:
        assert 'しんどくて、何が嫌なのか、ご自身でもよくわからないのですね' not in result.artifact.reception


@pytest.mark.parametrize('mutation', ['duplicate', 'slot', 'object', 'owner', 'profile', 'missing_source'])
def test_unknown_object_ir_and_rebuilt_plan_cannot_keep_invalid_pair(unknown_object_context, mutation):
    import emlis_ai_grounded_human_reception as hr
    from emlis_ai_grounded_observation_plan import _source_unknown_object_group_from_resolver
    _, plan, _, resolver, _ = unknown_object_context
    reception = plan.response_plan.human_reception_plan
    move, = reception.moves
    ir = hr._project_source_grounded_reception_move_realization(reception, move,
        {n.nucleus_id: n for n in plan.nuclei}, resolver, plan=plan, recovery_stage='full', clause_form='FINITE')
    marker = next(c for c in ir.nominalization_plan if c.startswith('source-unknown-object:'))
    slot = int(marker.split(':')[1]); unknown_slot = 1-slot
    if mutation == 'missing_source':
        for removed in (*move.target_nucleus_ids, *move.support_nucleus_ids):
            remaining = tuple(n for n in plan.nuclei if n.nucleus_id != removed)
            assert not _source_unknown_object_group_from_resolver(remaining, (), resolver)
        return
    if mutation == 'duplicate':
        changed = replace(ir, nominalization_plan=(*ir.nominalization_plan, marker))
    elif mutation == 'slot':
        changed = replace(ir, nominalization_plan=(ir.nominalization_plan[0], f'source-unknown-object:{unknown_slot}:{slot}'))
    elif mutation == 'profile':
        profiles = list(ir.semantic_profiles); profiles[unknown_slot] = replace(profiles[unknown_slot], modality='fact')
        changed = replace(ir, semantic_profiles=tuple(profiles))
    else:
        fragments = list(ir.semantic_fragments)
        fragments[unknown_slot] = fragments[unknown_slot].replace('何が嫌なのか', 'その理由') if mutation == 'object' else fragments[unknown_slot].replace('自分', '友人')
        changed = replace(ir, semantic_fragments=tuple(fragments))
    with pytest.raises(hr.GroundedHumanReceptionSurfaceError):
        hr._unknown_object_group_ir_text(changed)


@pytest.mark.parametrize('memo', [
    ' なんだかしんどい。何が嫌なのか、自分でもよくわからない。',
    '　なんだかしんどい。何が嫌なのか、自分でもよくわからない。',
    'なんだかしんどい。何が嫌なのか、自分でもよくわからない。 ',
    'なんだかしんどい。　何が嫌なのか、自分でもよくわからない。',
])
def test_unknown_object_raw_field_and_normalized_ledger_keep_same_body(memo):
    from test_cmee_emlis_received_discourse import actual
    from test_cmee_emlis_detached_observation import read_body
    p = prepare_emlis_meaning(request(memo))
    resolver = p.thread.resolver()
    first = next(s for s in resolver.resolve_many(resolver.span_ids) if s.source_field == 'memo')
    assert resolver.source_text_for_span_field(first.span_id) == memo
    context = actual(request=request(memo))
    assert context[0].artifact.reception == 'なんだかしんどくて、何が嫌なのか、ご自身でもよくわからないのですね。'
    assert read_body(context, context[0].artifact.text).passed
    public = MeaningExperienceEngine().generate(request(memo))
    assert public.artifact.text == context[0].artifact.text


@pytest.fixture(scope='module')
def single_unknown_context():
    from test_cmee_emlis_received_discourse import actual
    return actual(request=request('何が嫌なのか、自分でもまだよく分からない。'))


@pytest.mark.parametrize('case_index', range(10))
def test_single_unknown_object_preserves_saved_meaning_and_selected_openness(case_index):
    import hashlib
    import json
    from dataclasses import asdict
    from pathlib import Path
    from test_cmee_emlis_received_discourse import actual, inverse
    frozen = json.loads((Path(__file__).parent / 'fixtures' /
        'cmee_emlis_u325_single_unknown_checkpoint_v1.json').read_text())
    assert frozen['source_commit'] == '8df8bdb1d0076fe6c7895b7c423aa144182af4e6'
    row = frozen['cases'][case_index]
    req = request(row['memo'])
    req = replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=row['checkpoint']['checkpoint_id']))
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    selected = asdict(project_thread_meaning(prepared, plan).selected_reception)
    def digest(obj):
        return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assert json.loads(json.dumps(asdict(prepared.checkpoint))) == row['checkpoint']
    for name in ('nuclei', 'relations'):
        assert digest([asdict(n) for n in getattr(plan, name)]) == row[name + '_sha256']
    assert digest({k:v for k,v in selected.items() if k not in {'input_ref', 'grounding_ref'}}) == row['selected_content_sha256']
    assert selected['input_ref'] != row['selected_input_ref'] and selected['grounding_ref'] != row['grounding_ref']
    context = actual(request=req)
    result = MeaningExperienceEngine().generate(req)
    assert result.artifact and result.artifact.text == context[0].artifact.text
    follow = result.artifact.reception
    original = row['memo'].rstrip('。')
    recipient = original.replace('自分自身', 'ご自身').replace('自分', 'ご自身').replace('私', 'あなた')
    assert recipient in follow
    assert '結論を急がずに' in follow
    assert '小さくせずに' not in follow
    assert follow.count('まだ') == original.count('まだ')
    assert result.artifact.observation == row['body'].split('\n\nEmlisから：\n')[0].split('見えたこと：\n')[1]
    assert json.loads(json.dumps(asdict(result.question_decision))) == row['question_decision']
    assert result.question is None
    assert inverse(context, follow, without_author=True).passed


@pytest.mark.parametrize('old,new', [
    ('何が嫌なのか', '何が不安なのか'), ('何が嫌なのか', 'なぜ嫌なのか'),
    ('何が嫌なのか、', ''), ('ご自身でも', '私でも'), ('ご自身でも', '友人でも'),
    ('ご自身でも', 'ご自身には'), ('ご自身でも', ''),
    ('まだよく', 'まだ'), ('まだよく', 'よく'), ('まだよく', ''),
    ('分からない', '分かった'), ('分からない', '分からなかった'),
    ('分からない', '分からないと思う'), ('結論を急がずに、', ''),
    ('結論を急がずに', '結論を決めて'), ('のだと受け止めています', 'から苦しいのですね'),
])
def test_single_unknown_inverse_rejects_lost_scope_and_closed_uncertainty(single_unknown_context, old, new):
    from test_cmee_emlis_received_discourse import inverse
    context = single_unknown_context
    follow = context[0].artifact.reception
    changed = follow.replace(old, new)
    assert changed != follow
    assert not inverse(context, changed, without_author=True).passed


def test_single_unknown_inverse_keeps_existing_receipt_marker_contract(single_unknown_context):
    from test_cmee_emlis_received_discourse import inverse
    follow = single_unknown_context[0].artifact.reception.replace('受け止めています', '受け取っています')
    assert not inverse(single_unknown_context, follow, without_author=True).passed


@pytest.mark.parametrize('memo,action', [
    ('その理由は自分でもよくわからない。', ''),
    ('なぜ嫌なのか、自分でもよくわからない。', ''),
    ('何が嫌なのか、友人でもよくわからない。', ''),
    ('何が嫌なのか、自分でもよくわからなかった。', ''),
    ('何が嫌なのか、自分でもよくわからない？', ''),
    ('何が嫌なのか、自分でもよくわからないと言った。', ''),
    ('何が嫌なのか、自分でもよくわからないと思う。', ''),
    ('もし何が嫌なのか、自分でもよくわからないなら休む。', ''),
    ('「何が嫌なのか、自分でもよくわからない」と友人が言った。', ''),
    ('友人の話。何が嫌なのか、自分でもよくわからない。', ''),
    ('何が嫌なのか、自分でもよくわからない。机を片付けた。', ''),
    ('何が嫌なのか、自分でもよくわからない。', '机を片付けた。'),
])
def test_single_unknown_source_proof_excludes_other_owners_and_additional_material(memo, action):
    from emlis_ai_grounded_observation_plan import _source_unknown_object_group_from_resolver
    req = initial(memo, action)
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    assert not _source_unknown_object_group_from_resolver(plan.nuclei, plan.relations,
        prepared.thread.resolver(), include_single=True)


@pytest.mark.parametrize('prefix,suffix', [(' ', ''), ('　', ''), ('', ' '), ('', '　')])
def test_single_unknown_raw_field_whitespace_retains_full_object(prefix, suffix):
    from test_cmee_emlis_received_discourse import actual, inverse
    context = actual(request=request(prefix + '何が嫌なのか、自分でもよくわからない。' + suffix))
    assert '何が嫌なのか、ご自身でもよくわからない' in context[0].artifact.reception
    assert inverse(context, context[0].artifact.reception, without_author=True).passed


@pytest.mark.parametrize('change', ['duplicate', 'pair', 'foreign', 'tense', 'object', 'inactive'])
def test_single_unknown_ir_cannot_rebind_scope(single_unknown_context, change):
    import emlis_ai_grounded_human_reception as hr
    from emlis_ai_grounded_observation_plan import _source_unknown_object_group_from_resolver
    _, plan, _, resolver, _ = single_unknown_context
    reception = plan.response_plan.human_reception_plan
    move, = reception.moves
    index = {n.nucleus_id:n for n in plan.nuclei}
    if change == 'inactive':
        remaining = tuple(n for n in plan.nuclei if n.nucleus_id not in move.target_nucleus_ids)
        assert not _source_unknown_object_group_from_resolver(remaining, (), resolver, include_single=True)
        return
    ir = hr._project_source_grounded_reception_move_realization(reception, move, index, resolver,
        plan=plan, recovery_stage='full', clause_form='FINITE')
    if change == 'duplicate':
        changed = replace(ir, nominalization_plan=(*ir.nominalization_plan, ir.nominalization_plan[-1]))
    elif change == 'pair':
        changed = replace(ir, nominalization_plan=(ir.nominalization_plan[0], 'source-unknown-object:0:1'))
    elif change == 'foreign':
        changed = replace(ir, semantic_profiles=(replace(ir.semantic_profiles[0], actor_kind='OTHER'),))
    elif change == 'tense':
        changed = replace(ir, time_scope='past')
    else:
        changed = replace(ir, semantic_fragments=('その理由は分からない',))
    with pytest.raises(hr.GroundedHumanReceptionSurfaceError):
        hr._unknown_object_group_ir_text(changed)


@pytest.fixture(scope='module')
def unknown_action_baseline():
    import json
    from pathlib import Path
    return json.loads((Path(__file__).parent / 'fixtures' /
        'cmee_emlis_u326_unknown_action_checkpoint_v1.json').read_text())


def _unknown_action_request(memo, action, modern=True):
    req = initial(memo, action)
    return replace(req, execution_mode='EMLIS_APPLICATION',
        emlis_thread=replace(req.emlis_thread, capability_snapshot='Q3_FREE')) if modern else req


@pytest.fixture(scope='module')
def scalar_action_baseline():
    import json
    from pathlib import Path
    return json.loads((Path(__file__).parent / 'fixtures' /
        'cmee_emlis_u329_scalar_action_checkpoint_v1.json').read_text())


@pytest.mark.parametrize('modern', [False, True])
@pytest.mark.parametrize('case_index', range(20))
def test_scalar_unknown_and_action_retain_existing_two_duties(scalar_action_baseline, case_index, modern):
    from dataclasses import asdict
    import hashlib, json
    from test_cmee_emlis_received_discourse import actual, inverse
    from emlis_ai_grounded_observation_plan import _source_independent_unknown_object_from_resolver
    row = scalar_action_baseline['cases'][case_index]
    req = _unknown_action_request(row['memo'], row['action'], modern)
    p = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(p)
    resolver = p.thread.resolver()
    assert not _source_independent_unknown_object_from_resolver(plan.nuclei, plan.relations, resolver)
    group = _source_independent_unknown_object_from_resolver(plan.nuclei, plan.relations, resolver, allow_scalar=True)
    assert len(group) == 2
    nuclei_digest = hashlib.sha256(json.dumps([asdict(n) for n in plan.nuclei], ensure_ascii=False,
        sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assert nuclei_digest == row['nuclei_sha256']
    assert all(r.type == 'uncertain_connection' for r in plan.relations)
    moves = plan.response_plan.human_reception_plan.moves
    assert [m.reception_act for m in moves] == ['stay_with_current_burden', 'honor_concrete_effort']
    assert [m.target_nucleus_ids for m in moves] == [(n.nucleus_id,) for n in group]
    assert all(m.required and not m.support_nucleus_ids for m in moves)
    out = MeaningExperienceEngine().generate(req)
    assert out.artifact and out.body_state == 'FINAL' and out.question is None
    assert out.question_decision.disposition == 'END'
    assert row['memo'].rstrip('。') + 'こと' in out.artifact.reception
    assert row['action'].rstrip('。') + 'こと' in out.artifact.reception
    assert out.artifact.reception.count('まだ') == row['memo'].count('まだ')
    assert not any(word in out.artifact.reception for word in ('理由', '何が', 'そのため', '背景'))
    context = actual(request=req)
    assert out.artifact.text == context[0].artifact.text
    assert inverse(context, out.artifact.reception, without_author=True).passed
    if '片付けた' not in row['action']:
        assert out.artifact.text == row['body']


@pytest.mark.parametrize('case_index', range(20))
def test_u329_scalar_saved_meaning_and_body_are_not_relabelled(scalar_action_baseline, case_index):
    import json, hashlib
    from dataclasses import asdict
    row = scalar_action_baseline['cases'][case_index]
    assert scalar_action_baseline['source_commit'] == '6af573362ba2ff6f969e24018de80b359804080a'
    req = _unknown_action_request(row['memo'], row['action'])
    req = replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=row['checkpoint']['checkpoint_id']))
    restored = prepare_emlis_meaning(req)
    assert restored.legacy_unknown_object_action_scope == ('片付けた' in row['action'])
    assert json.loads(json.dumps(asdict(restored.checkpoint))) == row['checkpoint']
    plan = build_updated_grounded_plan(restored)
    def digest(value):
        return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
            separators=(',', ':')).encode()).hexdigest()
    assert digest([asdict(n) for n in plan.nuclei]) == row['nuclei_sha256']
    assert digest([asdict(r) for r in plan.relations]) == row['relations_sha256']
    assert digest(asdict(project_thread_meaning(restored, plan).selected_reception)) == row['selected_sha256']
    out = MeaningExperienceEngine().generate(req)
    assert out.artifact.text == row['body']
    assert json.loads(json.dumps(asdict(out.question_decision))) == row['question_decision']


@pytest.mark.parametrize('memo,action', [
    ('友人は分からない。', '机を片付けた。'),
    ('昨日は分からなかった。', '机を片付けた。'),
    ('「分からない」と聞いた。', '机を片付けた。'),
    ('分からない？', '机を片付けた。'),
    ('分からないので休む。', '机を片付けた。'),
    ('分からない。眠い。', '机を片付けた。'),
    ('分からない。', '友人が机を片付けた。'),
    ('分からない。', '机を片付けたい。'),
    ('分からない。', '机を片付けなかった。'),
    ('分からない。', '机を片付けるつもりだ。'),
    ('分からない。', '「机を片付けた」と聞いた。'),
    ('分からない。', '机を片付けた。資料を整理した。'),
    ('分からない。', '分かるために机を片付けた。'),
    ('分からない。', 'しかし机を片付けた。'),
])
def test_scalar_pair_proof_excludes_unproved_source(memo, action):
    from emlis_ai_grounded_observation_plan import _source_independent_unknown_object_from_resolver
    p = prepare_emlis_meaning(_unknown_action_request(memo, action))
    plan = build_updated_grounded_plan(p)
    assert not _source_independent_unknown_object_from_resolver(
        plan.nuclei, plan.relations, p.thread.resolver(), allow_scalar=True)


@pytest.mark.parametrize('change', [
    dict(retention='required'), dict(grounding_kind='user_stated_relation'),
    dict(type='cause_effect'), dict(type='contrast'),
    dict(source_relation_ids=('other.e1',)), dict(source_relation_ids=()),
    dict(source_meaning_arc_keys=('explicit:cause',)), dict(source_span_ids=('s1',)),
])
def test_scalar_pair_cannot_discard_differently_sourced_relation(change):
    from cocolon_meaning_experience_engine.emlis_question import original_meaning_plan
    from emlis_ai_grounded_observation_plan import _source_independent_unknown_object_from_resolver
    p = prepare_emlis_meaning(_unknown_action_request('今はまだよく分からない。', '机を片付けた。'))
    old = original_meaning_plan(p.thread, _legacy_unknown_object_action_scope=True)
    relation, = (r for r in old.relations if r.type == 'attempt_and_block')
    changed = tuple(replace(r, **change) if r == relation else r for r in old.relations)
    assert not _source_independent_unknown_object_from_resolver(
        old.nuclei, changed, p.thread.resolver(), allow_scalar=True)


@pytest.fixture(scope='module')
def scalar_action_context():
    from test_cmee_emlis_received_discourse import actual
    return actual(request=_unknown_action_request('今はまだよく分からない。', '机を片付けた。'))


@pytest.mark.parametrize('before,after', [
    ('まだ', ''), ('よく', ''), ('今は', '昨日は'),
    ('分からない', '分かった'), ('分からない', '何が嫌なのか分からない'),
    ('分からない', '友人が分からない'), ('机を片付けた', '机を片付けなかった'),
    ('机を片付けた', '部屋を片付けた'),
])
def test_scalar_pair_inverse_rejects_loss_or_invented_object(scalar_action_context, before, after):
    from test_cmee_emlis_received_discourse import inverse
    follow = scalar_action_context[0].artifact.reception
    changed = follow.replace(before, after)
    assert changed != follow
    assert not inverse(scalar_action_context, changed, without_author=True).passed


@pytest.mark.parametrize('modern', [False, True])
@pytest.mark.parametrize('case_index', range(20))
def test_independent_unknown_action_keeps_both_selected_duties(unknown_action_baseline, case_index, modern):
    from test_cmee_emlis_received_discourse import actual, inverse
    from emlis_ai_grounded_observation_plan import _source_independent_unknown_object_from_resolver
    row = unknown_action_baseline['cases'][case_index]
    req = _unknown_action_request(row['memo'], row['action'], modern)
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    group = _source_independent_unknown_object_from_resolver(plan.nuclei, plan.relations, prepared.thread.resolver())
    assert len(group) == 2
    moves = plan.response_plan.human_reception_plan.moves
    assert [m.reception_act for m in moves] == ['stay_with_current_burden', 'honor_concrete_effort']
    assert [m.target_nucleus_ids for m in moves] == [(n.nucleus_id,) for n in group]
    assert all(m.required and not m.support_nucleus_ids for m in moves)
    decisions = project_thread_meaning(prepared, plan).selected_reception.decisions
    assert len(decisions) == 2 and all(d.selected_contribution_refs for d in decisions)
    assert not set(decisions[0].selected_contribution_refs) & set(decisions[1].selected_contribution_refs)
    assert all((d.subjective_proposition.appraisal_content.dimension,
                d.subjective_proposition.appraisal_content.operation) == ('MATERIAL_WEIGHT','RECEIVE_AS_MATERIAL')
               for d in decisions)
    assert not any(r.type in {'wish_and_constraint','attempt_and_block'} for r in plan.relations)
    assert any(r.type == 'uncertain_connection' for r in plan.relations)
    context = actual(request=req)
    public = MeaningExperienceEngine().generate(req)
    assert public.artifact and public.artifact.text == context[0].artifact.text
    follow = public.artifact.reception
    recipient = row['memo'].rstrip('。').replace('自分自身','ご自身').replace('自分','ご自身').replace('私','あなた')
    assert follow.startswith(recipient + 'のですね。')
    assert row['action'].rstrip('。') in follow
    assert follow.count('まだ') == row['memo'].count('まだ')
    assert '結論を急がず' not in follow and '背景' not in follow
    assert public.question is None and public.question_decision.disposition == 'END'
    assert inverse(context, follow, without_author=True).passed


@pytest.mark.parametrize('case_index', range(20))
def test_unknown_action_old_checkpoint_is_restored_without_relabelling(unknown_action_baseline, case_index):
    import json, hashlib
    from dataclasses import asdict
    row = unknown_action_baseline['cases'][case_index]
    assert unknown_action_baseline['source_commit'] == '56fcaaec23a516de70fcc86f8f0caca94b86bc50'
    req = _unknown_action_request(row['memo'], row['action'])
    fresh = prepare_emlis_meaning(req)
    assert fresh.checkpoint.checkpoint_id != row['checkpoint']['checkpoint_id']
    req = replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=row['checkpoint']['checkpoint_id']))
    restored = prepare_emlis_meaning(req)
    assert restored.legacy_unknown_object_action_scope
    assert json.loads(json.dumps(asdict(restored.checkpoint))) == row['checkpoint']
    plan = build_updated_grounded_plan(restored)
    def digest(x):
        return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    assert digest([asdict(n) for n in plan.nuclei]) == row['nuclei_sha256']
    assert digest([asdict(r) for r in plan.relations]) == row['relations_sha256']
    assert digest(asdict(project_thread_meaning(restored, plan).selected_reception)) == row['selected_sha256']
    out = MeaningExperienceEngine().generate(req)
    assert out.artifact and out.artifact.text == row['body']
    assert json.loads(json.dumps(asdict(out.question_decision))) == row['question_decision']


@pytest.fixture(scope='module')
def independent_unknown_context():
    from test_cmee_emlis_received_discourse import actual
    return actual(request=_unknown_action_request('何が嫌なのか、自分でもまだよく分からない。','机を片付けた。'))


@pytest.mark.parametrize('old,new', [
    ('何が嫌なのか','なぜ嫌なのか'), ('何が嫌なのか','何が怖いのか'), ('何が嫌なのか、',''),
    ('ご自身でも','私でも'), ('ご自身でも','友人でも'), ('ご自身でも','ご自身には'),
    ('まだよく','よく'), ('まだよく','まだ'), ('分からない','分かった'),
    ('分からない','分からなかった'), ('のですね。','から、'), ('のですね。','のだと受け止めています。'),
    ('何が嫌なのか、ご自身でもまだよく分からないのですね。',''),
    ('机を片付けたことを大切に思っています。',''),
    ('机を片付けた','メモを書いた'), ('机を片付けた','机を片付けていない'),
    ('机を片付けた','机を片付けるつもりだ'), ('机を片付けた','友人が机を片付けた'),
])
def test_independent_unknown_inverse_rejects_loss_rebinding_and_false_link(independent_unknown_context, old, new):
    from test_cmee_emlis_received_discourse import inverse
    follow = independent_unknown_context[0].artifact.reception
    changed = follow.replace(old,new)
    assert changed != follow
    assert not inverse(independent_unknown_context, changed, without_author=True).passed


@pytest.mark.parametrize('memo,action', [
    ('その理由は自分でもよく分からない。','メモを書いた。'),
    ('なぜ嫌なのか、自分でもよく分からない。','メモを書いた。'),
    ('何が嫌なのか、友人でもよく分からない。','メモを書いた。'),
    ('何が嫌なのか、自分でもよく分からなかった。','メモを書いた。'),
    ('何が嫌なのか、自分でもよく分からない？','メモを書いた。'),
    ('何が嫌なのか、自分でもよく分からないと思う。','メモを書いた。'),
    ('「何が嫌なのか、自分でもよく分からない」と言った。','メモを書いた。'),
    ('友人の話。何が嫌なのか、自分でもよく分からない。','メモを書いた。'),
    ('なんだかしんどい。何が嫌なのか、自分でもよく分からない。','メモを書いた。'),
    ('何が嫌なのか、自分でもよく分からない。机を片付けた。',''),
    ('何が嫌なのか、自分でもよく分からない。','メモを書いた。机を片付けた。'),
    ('何が嫌なのか、自分でもよく分からない。','友人が机を片付けた。'),
    ('何が嫌なのか、自分でもよく分からない。','机を片付けていない。'),
    ('何が嫌なのか、自分でもよく分からない。','机を片付けるつもりだ。'),
    ('何が嫌なのか、自分でもよく分からない。','机を片付けたら休む。'),
    ('何が嫌なのか、自分でもよく分からない。','「机を片付けた」と友人が言った。'),
])
def test_independent_unknown_proof_does_not_expand_source_scope(memo,action):
    from emlis_ai_grounded_observation_plan import _source_independent_unknown_object_from_resolver
    p = prepare_emlis_meaning(_unknown_action_request(memo,action))
    plan = build_updated_grounded_plan(p)
    assert not _source_independent_unknown_object_from_resolver(plan.nuclei,plan.relations,p.thread.resolver())


@pytest.fixture(scope='module')
def same_field_unknown_baseline():
    import json
    from pathlib import Path
    return json.loads((Path(__file__).parent / 'fixtures' /
        'cmee_emlis_u327_same_field_unknown_action_checkpoint_v1.json').read_text())


@pytest.mark.parametrize('modern', [False, True])
@pytest.mark.parametrize('case_index', [0, 1, 4, 5, 8, 9, 12, 13])
def test_same_field_unknown_and_proved_action_reach_both_sections(same_field_unknown_baseline, case_index, modern):
    from test_cmee_emlis_received_discourse import actual, inverse
    from emlis_ai_grounded_observation_plan import _source_same_field_unknown_object_from_resolver
    row = same_field_unknown_baseline['cases'][case_index]
    assert row['body'] is None
    req = _unknown_action_request(row['memo'], '', modern)
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    unknown, action = _source_same_field_unknown_object_from_resolver(plan.nuclei, plan.relations, prepared.thread.resolver())
    assert unknown.source_fields == action.source_fields == ('memo',)
    assert unknown.semantic_frame.time_scope in {'present', 'current_input'}
    assert action.semantic_frame.time_scope == 'past'
    moves = plan.response_plan.human_reception_plan.moves
    assert [m.reception_act for m in moves] == ['stay_with_current_burden', 'honor_concrete_effort']
    assert [m.target_nucleus_ids for m in moves] == [(unknown.nucleus_id,), (action.nucleus_id,)]
    assert all(m.required and not m.support_nucleus_ids for m in moves)
    decisions = project_thread_meaning(prepared, plan).selected_reception.decisions
    assert len(decisions) == 2
    assert all((d.subjective_proposition.appraisal_content.dimension,
        d.subjective_proposition.appraisal_content.operation) == ('MATERIAL_WEIGHT', 'RECEIVE_AS_MATERIAL') for d in decisions)
    assert not set(decisions[0].selected_contribution_refs) & set(decisions[1].selected_contribution_refs)
    assert all(r.type == 'uncertain_connection' and r.retention != 'required' for r in plan.relations)
    context = actual(request=req)
    result = MeaningExperienceEngine().generate(req)
    assert result.artifact and result.artifact.text == context[0].artifact.text
    assert row['unknown'].rstrip('。') in result.artifact.observation
    assert row['action'].rstrip('。') in result.artifact.observation
    follow = result.artifact.reception
    recipient = row['unknown'].rstrip('。').replace('自分自身', 'ご自身').replace('自分', 'ご自身').replace('私', 'あなた')
    assert follow == recipient + 'のですね。メモを書いたことを見過ごさず、大切に受け止めています。'
    assert result.question is None and result.question_decision.disposition == 'END'
    assert inverse(context, follow, without_author=True).passed


@pytest.mark.parametrize('case_index', range(16))
def test_same_field_saved_checkpoint_retains_complete_old_meaning(same_field_unknown_baseline, case_index):
    import json, hashlib
    from dataclasses import asdict
    row = same_field_unknown_baseline['cases'][case_index]
    assert same_field_unknown_baseline['source_commit'] == 'd2cdc5d81d807f04999c48a263ef3647e6085087'
    req = _unknown_action_request(row['memo'], '')
    req = replace(req, emlis_thread=replace(req.emlis_thread, prepared_meaning_checkpoint_ref=row['checkpoint']['checkpoint_id']))
    restored = prepare_emlis_meaning(req)
    assert json.loads(json.dumps(asdict(restored.checkpoint))) == row['checkpoint']
    plan = build_updated_grounded_plan(restored)
    def digest(x):
        return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    assert digest([asdict(n) for n in plan.nuclei]) == row['nuclei_sha256']
    assert digest([asdict(r) for r in plan.relations]) == row['relations_sha256']
    try:
        selected = asdict(project_thread_meaning(restored, plan).selected_reception)
    except ValueError as exc:
        selected = {'error':str(exc)}
    assert digest(selected) == row['selected_sha256']
    result = MeaningExperienceEngine().generate(req)
    assert (result.artifact.text if result.artifact else None) == row['body']
    assert json.loads(json.dumps(asdict(result.question_decision) if result.question_decision else None)) == row['question_decision']


@pytest.mark.parametrize('memo, legacy_source', [(memo, False) for memo in [
    '何が嫌なのか、自分でもよく分からない。友人がメモを書いた。',
    '何が嫌なのか、自分でもよく分からない。メモを書いていない。',
    '何が嫌なのか、自分でもよく分からない。メモを書くつもりだ。',
    '何が嫌なのか、自分でもよく分からない。メモを書いたら休む。',
    '何が嫌なのか、自分でもよく分からない。メモを書いてもらった。',
    '何が嫌なのか、自分でもよく分からない。だからメモを書いた。',
    '何が嫌なのか、自分でもよく分からないが、メモを書いた。',
    '何が嫌なのか、自分でもよく分からない？メモを書いた。',
    '何が嫌なのか、自分でもよく分からない。メモを書いた？',
    '何が嫌なのか、友人にもよく分からない。メモを書いた。',
    '何が嫌なのか、自分でもよく分からなかった。メモを書いた。',
    '何が嫌なのか、自分でもよく分からないと思う。メモを書いた。',
    '「何が嫌なのか、自分でもよく分からない」と話した。メモを書いた。',
    '友人の話。何が嫌なのか、自分でもよく分からない。メモを書いた。',
    '何が嫌なのか、自分でもよく分からない。メモを書いた。資料を整理した。',
    'なぜ嫌なのか、自分でもよく分からない。メモを書いた。',
    '今はまだよく分からない。メモを書いた。',
]] + [
    ('何が嫌なのか、自分でもよく分からない。机を片付けた。', True),
    ('何が嫌なのか、自分でもよく分からない。資料を整理した。', True),
])
def test_same_field_pair_does_not_promote_unproved_sources(memo, legacy_source):
    from emlis_ai_grounded_observation_plan import _source_same_field_unknown_object_from_resolver
    p = prepare_emlis_meaning(_unknown_action_request(memo, ''))
    # The two pre-u329 lexical defaults remain unproved in their old plan.
    # Current finite-action recognition is tested independently below.
    from cocolon_meaning_experience_engine.emlis_question import original_meaning_plan
    plan = original_meaning_plan(p.thread, _legacy_unknown_object_action_scope=True) if legacy_source else build_updated_grounded_plan(p)
    assert not _source_same_field_unknown_object_from_resolver(plan.nuclei, plan.relations, p.thread.resolver())


@pytest.fixture(scope='module')
def same_field_unknown_context():
    from test_cmee_emlis_received_discourse import actual
    return actual(request=_unknown_action_request('何が嫌なのか、自分でもよく分からない。メモを書いた。', ''))


@pytest.mark.parametrize('before,after', [
    ('何が嫌なのか', 'なぜ嫌なのか'),
    ('ご自身でも', '友人にも'),
    ('よく分からない', 'よく分かる'),
    ('よく分からない', 'まだよく分からない'),
    ('よく分からない', 'よく分からなかった'),
    ('メモを書いた', 'メモを書いていない'),
    ('メモを書いた', '机を片付けた'),
    ('メモを書いたことを見過ごさず、大切に受け止めています。', ''),
    ('何が嫌なのか、ご自身でもよく分からないのですね。', ''),
    ('のですね。', 'のは、メモを書いたからですね。'),
])
def test_same_field_reader_rejects_changed_meaning_without_author(same_field_unknown_context, before, after):
    from test_cmee_emlis_received_discourse import inverse
    follow = same_field_unknown_context[0].artifact.reception
    assert before in follow
    assert not inverse(same_field_unknown_context, follow.replace(before, after), without_author=True).passed


@pytest.fixture(scope='module')
def same_field_action_baseline():
    import json
    from pathlib import Path
    return json.loads((Path(__file__).parent / 'fixtures' /
        'cmee_emlis_u328_same_field_action_checkpoint_v1.json').read_text())


@pytest.mark.parametrize('modern', [False, True])
@pytest.mark.parametrize('case_index', range(24))
def test_same_field_finite_action_replaces_lexical_default(same_field_action_baseline, case_index, modern):
    from cocolon_meaning_experience_engine.emlis_question import original_meaning_plan
    from emlis_ai_grounded_observation_plan import _source_same_field_unknown_object_from_resolver
    row = same_field_action_baseline['cases'][case_index]
    req = _unknown_action_request(row['memo'], '', modern)
    p = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(p)
    unknown, action = _source_same_field_unknown_object_from_resolver(plan.nuclei, plan.relations, p.thread.resolver())
    assert (action.kind, action.semantic_frame.predicate_kind, action.semantic_frame.polarity,
        action.semantic_frame.modality, action.semantic_frame.time_scope) == ('action', 'action', 'neutral', 'fact', 'past')
    assert 'operator:performed_action' in action.semantic_frame.attribute_codes
    assert 'semantic_role:current_change' not in action.semantic_frame.attribute_codes
    assert unknown.kind == unknown.semantic_frame.predicate_kind == 'uncertainty'
    assert unknown.semantic_frame.time_scope in {'present', 'current_input'}
    old = original_meaning_plan(p.thread, _legacy_unknown_object_action_scope=True)
    assert [(r.relation_id,r.from_nucleus_id,r.to_nucleus_id,r.source_span_ids,r.source_relation_ids,r.source_meaning_arc_keys)
        for r in plan.relations] == [(r.relation_id,r.from_nucleus_id,r.to_nucleus_id,r.source_span_ids,r.source_relation_ids,r.source_meaning_arc_keys)
        for r in old.relations]
    assert all(r.type == 'uncertain_connection' and r.grounding_kind == 'bounded_structural_inference'
        and r.retention != 'required' for r in plan.relations)
    assert p.checkpoint.checkpoint_id != row['checkpoint']['checkpoint_id']
    moves = plan.response_plan.human_reception_plan.moves
    assert [m.target_nucleus_ids for m in moves] == [(unknown.nucleus_id,), (action.nucleus_id,)]
    assert all(m.required and not m.support_nucleus_ids for m in moves)
    decisions = project_thread_meaning(p, plan).selected_reception.decisions
    assert len(decisions) == 2
    assert all((d.subjective_proposition.appraisal_content.dimension,
        d.subjective_proposition.appraisal_content.operation) == ('MATERIAL_WEIGHT','RECEIVE_AS_MATERIAL') for d in decisions)
    result = MeaningExperienceEngine().generate(req)
    assert result.artifact
    assert row['unknown'].rstrip('。') in result.artifact.observation
    assert row['action'].rstrip('。') in result.artifact.observation
    recipient = row['unknown'].rstrip('。').replace('自分自身','ご自身').replace('自分','ご自身').replace('私','あなた')
    assert recipient in result.artifact.reception
    assert row['action'].rstrip('。') + 'こと' in result.artifact.reception
    assert not any(x in result.artifact.text for x in ('という願い','という制約','を背景に'))
    assert result.question is None and result.question_decision.disposition == 'END'


@pytest.mark.parametrize('case_index', range(24))
def test_u328_same_field_saved_meaning_is_restored_in_full(same_field_action_baseline, case_index):
    import json, hashlib
    from dataclasses import asdict
    row = same_field_action_baseline['cases'][case_index]
    assert same_field_action_baseline['source_commit'] == 'f58e6ba96fded4befcec2df5cfd2f284e88705ea'
    req = _unknown_action_request(row['memo'], '')
    req = replace(req, emlis_thread=replace(req.emlis_thread, prepared_meaning_checkpoint_ref=row['checkpoint']['checkpoint_id']))
    restored = prepare_emlis_meaning(req)
    assert restored.legacy_unknown_object_action_scope
    assert json.loads(json.dumps(asdict(restored.checkpoint))) == row['checkpoint']
    plan = build_updated_grounded_plan(restored)
    def digest(x):
        return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    assert digest([asdict(n) for n in plan.nuclei]) == row['nuclei_sha256']
    assert digest([asdict(r) for r in plan.relations]) == row['relations_sha256']
    try:
        selected = asdict(project_thread_meaning(restored, plan).selected_reception)
    except ValueError as exc:
        selected = {'error':str(exc)}
    assert digest(selected) == row['selected_sha256']
    result = MeaningExperienceEngine().generate(req)
    assert (result.artifact.text if result.artifact else None) == row['body']
    assert json.loads(json.dumps(asdict(result.question_decision) if result.question_decision else None)) == row['question_decision']


@pytest.mark.parametrize('action', [
    '机を片付けたい。', '机を片付けていない。', '机を片付けなかった。',
    '机を片付けるつもりだ。', '机を片付けることにした。', '机を片付けたら休む。',
    '友人が机を片付けた。', '机を片付けてもらった。', '「机を片付けた」と聞いた。',
    'だから机を片付けた。', 'でも机を片付けた。', 'その後机を片付けた。',
    '机を片付けた？', '机を片付けた。資料を整理した。',
    '怒りを覚えた。', '失敗を恐れた。', '明日資料を整理した。',
    '資料を整理したと思う。', '資料を整理したらしい。', '資料を整理してくれた。',
    'しかし資料を整理した。', 'わかるために資料を整理した。', 'そこから資料を整理した。',
    '頼まれて資料を整理した。', 'それなのに資料を整理した。',
])
def test_same_field_action_correction_preserves_nonperformed_and_linked_sources(action):
    from cocolon_meaning_experience_engine.emlis_question import original_meaning_plan
    p = prepare_emlis_meaning(_unknown_action_request('何が嫌なのか、自分でもよくわからない。'+action, ''))
    current = build_updated_grounded_plan(p)
    old = original_meaning_plan(p.thread, _legacy_unknown_object_action_scope=True)
    assert current.nuclei == old.nuclei
    assert current.relations == old.relations


@pytest.mark.parametrize('mutation', ['extra_source','new_provenance','different_endpoint','extra_arc'])
def test_same_field_action_correction_cannot_relax_unproved_relation(mutation):
    from cocolon_meaning_experience_engine.emlis_question import original_meaning_plan
    from emlis_ai_grounded_observation_plan import _final_source_same_field_unknown_action
    p = prepare_emlis_meaning(_unknown_action_request('机を片付けた。何が嫌なのか、自分でもよくわからない。', ''))
    old = original_meaning_plan(p.thread, _legacy_unknown_object_action_scope=True)
    first = old.relations[0]
    changed = {
        'extra_source': replace(first, source_span_ids=(*first.source_span_ids,'unrelated')),
        'new_provenance': replace(first, source_relation_ids=('explicit_cause',)),
        'different_endpoint': replace(first, to_nucleus_id='unrelated'),
        'extra_arc': replace(first, source_meaning_arc_keys=(*first.source_meaning_arc_keys,'explicit_cause')),
    }[mutation]
    relations = (changed,*old.relations[1:])
    assert _final_source_same_field_unknown_action(old.nuclei,relations,p.thread.original.evidence_spans,
        p.thread.original.normalized_current_input) == (old.nuclei,relations)


@pytest.fixture(scope='module')
def finite_same_field_action_context():
    from test_cmee_emlis_received_discourse import actual
    return actual(request=_unknown_action_request('何が嫌なのか、自分でもよくわからない。机を片付けた。',''))


@pytest.mark.parametrize('before,after', [
    ('何が嫌なのか、ご自身でもよくわからないのですね。',''),
    ('机を片付けたことを見過ごさず、大切に受け止めています。',''),
    ('ご自身','友人'), ('何が嫌','何が不安'), ('わからない','わかっている'),
    ('よくわからない','分からない'), ('机を片付けた','机を片付けたい'),
    ('机を片付けた','机を片付けていない'), ('机を片付けた','資料を整理した'),
    ('のですね。','ので、'), ('机を片付けた','友人が机を片付けた'),
])
def test_same_field_finite_action_inverse_rejects_semantic_mutation(finite_same_field_action_context,before,after):
    from test_cmee_emlis_received_discourse import inverse
    follow = finite_same_field_action_context[0].artifact.reception
    assert before in follow
    assert not inverse(finite_same_field_action_context,follow.replace(before,after),without_author=True).passed
