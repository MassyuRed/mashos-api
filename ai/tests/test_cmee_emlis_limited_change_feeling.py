"""Finite observations keep the complete past episode and independent material.

All inputs extend existing public synthetic examples. Historical expectations
and the shared echo-quality threshold remain unchanged.
"""
from dataclasses import replace
from unittest.mock import patch

import pytest

from test_cmee_emlis_q3_thread import ACTION_CHANGE_CONTRAST_MEMO, begin
from test_cmee_emlis_q1_thread import initial
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from emlis_ai_grounded_observation_gate import evaluate_grounded_surface_body_inverse
import emlis_ai_grounded_sentence_surface as surface
import emlis_ai_grounded_observation_gate as gate
import emlis_ai_grounded_observation_plan as plan_owner
from cocolon_meaning_experience_engine.source_kernel import freeze_text_source
from emlis_ai_evidence_ledger_service import EvidenceLedgerResolutionError


def _polite_change_plan(memo, *, source_override=None):
    source = freeze_text_source(initial(memo))
    normalized = dict(source.normalized_current_input)
    if source_override is not None:
        normalized['memo'] = source_override
    return plan_owner.build_final_stage1_grounded_observation_plan(
        normalized, evidence_spans=source.evidence_spans)


def _action_change_relations(plan):
    return tuple(r for r in plan.relations if r.source_relation_ids == (
        'typed_projection:perfective_action_before_bounded_change',))


@pytest.mark.parametrize('form,plain', [(form, plain)
    for plain, polite in [('安心しなかった', '安心しませんでした'),
        ('落ち着かなかった', '落ち着きませんでした'),
        ('嬉しくなかった', '嬉しくありませんでした'), ('うれしくなかった', 'うれしくありませんでした')]
    for form in (plain, plain + 'です', polite)])
@pytest.mark.parametrize('action,visible', [('私は資料を調べた後、', '資料を調べた後、'),
    ('それから俺は資料を調べてから、', 'それから資料を調べてから、')])
def test_negative_compound_feeling_keeps_negation_and_never_supports_it(form, plain, action, visible):
    import cocolon_meaning_experience_engine.emlis_stage1_response as response
    from test_cmee_emlis_received_discourse import inverse
    from test_cmee_emlis_detached_observation import read_body
    memo = action + '私は、' + form + '。その後、私は記録を残した。'
    plan = _polite_change_plan(memo)
    relation, = _action_change_relations(plan)
    change = next(n for n in plan.nuclei if n.nucleus_id == relation.to_nucleus_id)
    assert change.semantic_frame.polarity == 'negative'
    assert 'operator:negation' in change.semantic_frame.attribute_codes
    assert 'operator:positive_change' not in change.semantic_frame.attribute_codes
    attempts = []
    def capture(**kwargs):
        verdict = evaluate_grounded_surface_body_inverse(**kwargs)
        attempts.append((kwargs, verdict))
        return verdict
    with patch.object(response, 'evaluate_grounded_surface_body_inverse', capture):
        result = MeaningExperienceEngine().generate(initial(memo))
    assert result.artifact is not None, result.reason_codes
    assert visible + plain + 'のですね。' in result.artifact.reception
    actual = next(kwargs for kwargs, verdict in reversed(attempts)
        if verdict.passed and kwargs['body'] == result.artifact.text.encode())
    assert {k['sentence_plan'].recovery_stage for k, _ in attempts} >= {'full', 'optional_removed', 'integrated', 'hedged'}
    for kwargs, _ in attempts:
        assert '支えている' not in kwargs['body'].decode()
        assert '大切に思っています' not in kwargs['body'].decode()
        assert '変化' not in kwargs['body'].decode()
        assert 'つながっています' not in kwargs['body'].decode()
    context = (result, actual['plan'], actual['sentence_plan'], actual['resolver'], actual['selected_subjective_input'])
    assert inverse(context, result.artifact.reception, without_author=True).passed
    assert read_body(context, result.artifact.text).passed
    episode = result.artifact.observation
    for wrong in (episode.replace('とあります。', 'という変化へつながっています。'),
            episode.replace('」後、', '」ので、').replace('」から、', '」ので、'),
            episode.replace(form, '安心した'), episode.replace(form, ''),
            episode.replace('私は、' + form, '友人は、' + form)):
        assert wrong != episode
        assert not read_body(context, result.artifact.text.replace(episode, wrong, 1)).passed
    for wrong in (result.artifact.reception.replace('から、', 'ので、').replace('後、', 'ので、'),
            '友人が' + result.artifact.reception, result.artifact.reception.replace(plain, '安心した'),
            result.artifact.reception.replace(plain, ''),
            result.artifact.reception.replace('のですね', 'ことを支えています')):
        assert not inverse(context, wrong, without_author=True).passed


@pytest.mark.parametrize('form', ['安心しなかった', '落ち着きませんでした', '嬉しくなかったです', 'うれしくありませんでした'])
@pytest.mark.parametrize('before,action,subject,after', [
    ('', '友人は資料を調べた後、', '', ''), ('', '資料を調べた後、', '', ''),
    ('', '私は資料を調べなかった後、', '', ''), ('', '私は資料を調べたら、', '', ''),
    ('', '私は資料を調べた後、', '友人は', ''), ('', '私は資料を調べた後、', '少し', ''),
    ('', '私は資料を調べた後、', '', 'か。'), ('', '私は資料を調べた後、', '', '？'),
    ('', '私は資料を調べた後、', '', 'かもしれない。'),
    ('「', '私は資料を調べた後、', '', '」。'),
    ('夢を見た。', '私は資料を調べた後、', '', ''),
    ('友人が言っていた。', '私は資料を調べた後、', '', ''),
    ('', '私は資料を調べた後、', '', '。と友人が言った。'),
    ('', '私は資料を調べた後、', '', '。と私は思う。'),
    ('', '私は資料を調べた後、', '', '。のは嘘だった。'),
    ('', '私は資料を調べた後、', '', '\nわけではない。')])
def test_negative_compound_feeling_keeps_unproved_host_pending(form, before, action, subject, after):
    memo = before + action + subject + form + after
    assert not _action_change_relations(_polite_change_plan(memo))


def test_negative_compound_short_echo_keeps_quality_gate_closed():
    import cocolon_meaning_experience_engine.emlis_stage1_response as response
    reports = []
    evaluate = response.evaluate_grounded_observation_gate
    def capture(**kwargs):
        report = evaluate(**kwargs)
        reports.append((kwargs['surface_result'].text, report))
        return report
    with patch.object(response, 'evaluate_grounded_observation_gate', capture):
        result = MeaningExperienceEngine().generate(initial('私は資料を調べた後、安心しなかった。'))
    assert result.artifact is None
    assert result.reason_codes == ('stage1_no_hard_valid_realization',)
    assert any('observation_surface_only_echo' in report.rejection_reasons
        and report.text_semantic_retention_gate == 'passed'
        and report.required_coverage_gate == 'passed' for _, report in reports)
    assert reports and all('変化' not in text and '支えている' not in text for text, _ in reports)
    assert any('「私は資料を調べた」後、「安心しなかった」とあります。' in text for text, _ in reports)


@pytest.mark.parametrize('feeling', ['落ち着きました', '嬉しかったです', 'うれしかったです'])
@pytest.mark.parametrize('prefix', ['', '私は資料を調べた。', '私は会議を担当した。私は資料を調べた。私は記録を残した。'])
def test_polite_standalone_feelings_have_bound_positive_shared_witness(feeling, prefix):
    plan = _polite_change_plan(prefix + '私は、' + feeling + '。')
    node = [n for n in plan.nuclei if n.source_fields == ('memo',)][-1]
    frame = node.semantic_frame
    assert (node.kind, frame.predicate_kind, frame.polarity, frame.modality) == (
        'reaction', 'feeling', 'positive', 'feeling')
    assert {'operator:feeling', 'operator:positive_change', 'semantic_role:current_change'} <= set(frame.attribute_codes)
    assert not _action_change_relations(plan)
    # The global positive keyword rule is intentionally unchanged.
    assert plan_owner._POSITIVE_CHANGE_RE.search('落ち着きました') is None


@pytest.mark.parametrize('memo', [
    '落ち着きました。', '友人は落ち着きました。', '私は少し落ち着きました。',
    '私は落ち着きましたか。', '私は落ち着きました？', '私は落ち着きましたと聞いた。',
    '私は落ち着きました。とは言えない。', '私は落ち着きました\nわけではない。',
    '私は落ち着きました。と思う。', '「私は落ち着きました」。',
    '夢を見た。私は落ち着きました。', '友人の話です。私は落ち着きました。',
    '友人は言った。私は落ち着きました。',
])
def test_polite_standalone_feeling_does_not_borrow_unasserted_or_foreign_scope(memo):
    plan = _polite_change_plan(memo)
    assert not any('operator:positive_change' in n.semantic_frame.attribute_codes for n in plan.nuclei)


@pytest.mark.parametrize('feeling,plain', [('落ち着きました', '落ち着いた'),
    ('嬉しかったです', '嬉しかった'), ('うれしかったです', 'うれしかった')])
@pytest.mark.parametrize('action,visible', [('私は資料を調べた後、', '資料を調べた後、'),
    ('俺は、資料を調べてから、', '資料を調べてから、')])
@pytest.mark.parametrize('subject', ['', '私は、'])
@pytest.mark.parametrize('following', ['', 'その後、私は記録を残した。',
    'その後、私は記録を残さなかった。', '散歩していた猫を眺めた。その後、私は記録を残した。'])
def test_polite_feeling_compound_retains_sequence_without_causal_support(feeling, plain, action, visible, subject, following):
    import cocolon_meaning_experience_engine.emlis_stage1_response as response
    from test_cmee_emlis_received_discourse import inverse
    memo = action + subject + feeling + '。' + following
    relation, = _action_change_relations(_polite_change_plan(memo))
    assert relation.retention == 'required'
    attempts = []
    def capture(**kwargs):
        verdict = evaluate_grounded_surface_body_inverse(**kwargs)
        attempts.append((kwargs, verdict))
        return verdict
    with patch.object(response, 'evaluate_grounded_surface_body_inverse', capture):
        result = MeaningExperienceEngine().generate(initial(memo))
    assert result.artifact is not None, result.reason_codes
    assert (visible + plain + 'のですね。') in result.artifact.reception
    actual = next(kwargs for kwargs, verdict in reversed(attempts)
                  if verdict.passed and kwargs['body'] == result.artifact.text.encode())
    assert {k['sentence_plan'].recovery_stage for k, _ in attempts} >= {'full', 'optional_removed', 'integrated', 'hedged'}
    for kwargs, _ in attempts:
        assert '支えている' not in kwargs['body'].decode()
        assert '大切に思っています' not in kwargs['body'].decode()
    context = (result, actual['plan'], actual['sentence_plan'], actual['resolver'],
               actual['selected_subjective_input'])
    assert inverse(context, result.artifact.reception, without_author=True).passed
    for changed in (result.artifact.reception.replace('から、', 'ので、').replace('後、', 'ので、'),
                    '友人が' + result.artifact.reception,
                    result.artifact.reception.replace(plain, '不安だった'),
                    result.artifact.reception.replace(plain, ''),
                    result.artifact.reception.replace('のですね', 'ことを支えています')):
        assert not inverse(context, changed, without_author=True).passed


def test_polite_standalone_feeling_requires_unchanged_complete_source():
    memo = '私は落ち着きました。'
    with pytest.raises(EvidenceLedgerResolutionError, match='source_slice_mismatch'):
        _polite_change_plan(memo, source_override='友人は' + memo)
    plan = _polite_change_plan(memo, source_override=memo[:-1] + '？')
    assert not any('operator:positive_change' in n.semantic_frame.attribute_codes for n in plan.nuclei)


@pytest.mark.parametrize('feeling', ['落ち着きました', '嬉しかったです', 'うれしかったです'])
@pytest.mark.parametrize('prefix,suffix', [('友人が言っていた。', ''),
    ('', 'と私は思う。'), ('', 'なんて嘘だった。')])
def test_polite_compound_does_not_detach_report_cognition_or_retraction(feeling, prefix, suffix):
    memo = prefix + '私は資料を調べた後、' + feeling + '。' + suffix
    assert not _action_change_relations(_polite_change_plan(memo))


def test_polite_nominal_change_keeps_self_word_as_original_argument():
    result = MeaningExperienceEngine().generate(initial('私は資料を調べた後、自分は減りました。'))
    assert result.artifact is not None, result.reason_codes
    assert result.artifact.reception == '資料を調べた後、自分は減ったのですね。'


@pytest.mark.parametrize('change', ['不安が減りました', '気持ちメモが増えました', '資料が戻りました'])
@pytest.mark.parametrize('action', ['私は資料を調べた後、', '僕は記録を残してから、',
    '私は、資料を調べた後、', '僕は，　記録を残してから、', 'わたしは、 資料を調べてから、'])
def test_polite_nominal_changes_have_neutral_source_bound_final_witness(action, change):
    memo = action + change + '。'
    plan = _polite_change_plan(memo)
    relation, = _action_change_relations(plan)
    nodes = {n.nucleus_id: n for n in plan.nuclei}
    first, second = nodes[relation.from_nucleus_id], nodes[relation.to_nucleus_id]
    assert (first.kind, second.kind) == ('action', 'change')
    assert (relation.grounding_kind, relation.retention) == ('user_stated_relation', 'required')
    assert second.semantic_frame.polarity == 'neutral'
    assert second.semantic_frame.time_scope == 'past'
    assert 'operator:positive_change' not in second.semantic_frame.attribute_codes
    for node, fragment in ((first, action.split('後')[0] if '後' in action else action[:-3]),
                           (second, change)):
        code, = (c for c in node.semantic_frame.attribute_codes
                 if c.startswith('source_fragment_scalar_range:'))
        start, end = map(int, code.split(':')[1:])
        assert memo[start:end] == fragment
        assert 'source_fragment_scalar_source:normalized_raw_text' in node.semantic_frame.attribute_codes
    # The old builder is not reached through the new final-only projector.
    source = freeze_text_source(initial(memo))
    with patch.object(plan_owner, '_typed_nucleus_projections_for_span', side_effect=AssertionError('final owner')):
        plan_owner.build_grounded_observation_plan(source.normalized_current_input,
            evidence_spans=source.evidence_spans)


@pytest.mark.parametrize('memo', [
    '私は資料を調べた後、不安が減りました？',
    '私は資料を調べた後、不安が減りましたか。',
    '私は資料を調べた後、不安が減りましたと聞いた。',
    '私は資料を調べた後、不安が減りましたなら。',
    '私は資料を調べなかった後、不安が減りました。',
    '私は資料を調べたら、不安が減りました。',
    '私は資料を調べた後、友人の不安が減りました。',
    '私は資料を調べた後、何が戻りました。',
    '私は資料を調べた後、気持ち来週メモが増えました。',
    '友人は資料を調べた後、不安が減りました。',
    '私は友人が資料を調べた後、不安が減りました。',
    '資料を調べた後、不安が減りました。',
    '「私は資料を調べた後、不安が減りました」と友人が言った。',
    '友人の話です。私は資料を調べた後、不安が減りました。',
    '友人は言った。私は資料を調べた後、不安が減りました。',
    '私は資料を調べた後、不安が減りました。と聞いた。',
    '友人から聞いた内容です。私は資料を調べた後、不安が減りました。',
    '私は、、資料を調べてから、不安が減りました。',
    '私は、\t資料を調べてから、不安が減りました。',
    '私は、\n資料を調べてから、不安が減りました。',
    '私は、明日資料を調べてから、不安が減りました。',
    '友人は、資料を調べてから、不安が減りました。',
    '私は、資料を調べてから、不安が減りましたと聞いた。',
    '私は、資料を調べてから、不安が減りました？',
    '「私は、資料を調べてから、不安が減りました」と友人が言った。',
])
def test_polite_nominal_changes_do_not_borrow_foreign_or_unasserted_scope(memo):
    assert not _action_change_relations(_polite_change_plan(memo))


def test_polite_nominal_changes_require_original_source_and_keep_independent_sentences():
    memo = '私は資料を調べた後、不安が減りました。'
    assert not _action_change_relations(_polite_change_plan(memo, source_override=memo[:-1] + '？'))
    with pytest.raises(EvidenceLedgerResolutionError, match='source_slice_mismatch'):
        _polite_change_plan(memo, source_override='友人は' + memo)
    assert len(_action_change_relations(_polite_change_plan('私は仕事を続けたい。' + memo))) == 1


@pytest.mark.parametrize('change,plain', [('資料が減りました', '資料が減った'),
    ('気持ちメモが増えました', '気持ちメモが増えた'), ('資料が戻りました', '資料が戻った')])
@pytest.mark.parametrize('action,visible', [('私は資料を調べた後、', '資料を調べた後、'),
    ('僕は記録を残してから、', '記録を残してから、'),
    ('私は、資料を調べた後、', '資料を調べた後、'),
    ('僕は，　記録を残してから、', '記録を残してから、'),
    ('わたしは、 資料を調べてから、', '資料を調べてから、')])
def test_polite_changes_reach_emlis_without_causal_or_value_appraisal(action, visible, change, plain):
    import cocolon_meaning_experience_engine.emlis_stage1_response as response
    from test_cmee_emlis_received_discourse import inverse
    attempts = []
    def capture(**kwargs):
        verdict = evaluate_grounded_surface_body_inverse(**kwargs)
        attempts.append((kwargs, verdict))
        return verdict
    with patch.object(response, 'evaluate_grounded_surface_body_inverse', capture):
        result = MeaningExperienceEngine().generate(initial(action + change + '。'))
    assert result.artifact is not None, result.reason_codes
    assert result.artifact.reception == visible + plain + 'のですね。'
    actual = next(kwargs for kwargs, verdict in reversed(attempts)
                  if verdict.passed and kwargs['body'] == result.artifact.text.encode())
    assert {k['sentence_plan'].recovery_stage for k, _ in attempts} >= {'full', 'optional_removed', 'integrated', 'hedged'}
    for kwargs, _ in attempts:
        assert '支えている' not in kwargs['body'].decode()
        assert '大切に思っています' not in kwargs['body'].decode()
    context = (result, actual['plan'], actual['sentence_plan'], actual['resolver'],
               actual['selected_subjective_input'])
    # Disable author replay through the existing independent-reader helper;
    # the source/meaning checks must reject even a replay agreeing with a lie.
    assert inverse(context, result.artifact.reception, without_author=True).passed
    for changed in (result.artifact.reception.replace('から、', 'ので、').replace('後、', 'ので、'),
                    '、' + result.artifact.reception,
                    '友人が' + result.artifact.reception,
                    result.artifact.reception.replace(plain, '不安が増えた'),
                    result.artifact.reception.replace(plain, ''),
                    result.artifact.reception.replace('のですね', 'ことを大切に思っています')):
        assert not inverse(context, changed, without_author=True).passed


@pytest.mark.parametrize('change', ['不安が減りました', '不安が増えました'])
@pytest.mark.parametrize('action', ['私は資料を調べた後、', '私は、資料を調べてから、'])
def test_emlis_existing_unbound_feeling_scope_is_not_relaxed(change, action):
    result = MeaningExperienceEngine().generate(initial(action + change + '。'))
    assert result.artifact is None
    assert result.reason_codes == ('current_experiencer_or_time_scope_unsupported',)


@pytest.mark.parametrize('q3', [False, True])
@pytest.mark.parametrize('action', ['', 'お茶を飲んだ。'])
@pytest.mark.parametrize('unfinished', ['', 'まだ配置は見つかっていない。'])
def test_original_initial_route_provides_a_body_without_relaxing_quality(q3, action, unfinished):
    result = MeaningExperienceEngine().generate(
        (begin if q3 else initial)(ACTION_CHANGE_CONTRAST_MEMO + unfinished, action))
    assert result.artifact is not None, result.reason_codes
    if not q3 and (action or unfinished):
        assert 'うれしかったのは、机の上が広くなったことなのですね。' in result.artifact.observation
        assert '窓辺の鉢を棚へ移したら、' in result.artifact.observation
        assert 'いつも見ていた葉が遠くなって、手元に緑がないという寂しさも残っている' in result.artifact.observation
    for separate in (action, unfinished):
        if separate:
            assert separate.rstrip('。') in result.artifact.observation


def _limited_context(memo=ACTION_CHANGE_CONTRAST_MEMO):
    observed = []
    def capture(**kwargs):
        verdict = evaluate_grounded_surface_body_inverse(**kwargs)
        if verdict.passed:
            observed.append(kwargs)
        return verdict
    with patch.object(gate, 'evaluate_grounded_surface_body_inverse', capture):
        result = MeaningExperienceEngine().generate(initial(
            memo + 'まだ配置は見つかっていない。', '明日、棚を動かす。'))
    assert result.artifact is not None, result.reason_codes
    assert 'ことなのですね。' in result.artifact.observation
    actual = next(row for row in reversed(observed)
                  if row['body'] == result.artifact.text.encode())
    assert actual['sentence_plan'].lines[0].binding.line_role == 'limited_scope'
    return result, actual['plan'], actual['sentence_plan'], actual['resolver'], actual['selected_subjective_input']


def _read(context, observation, plan_override=None):
    result, plan, sentence, resolver, selected = context
    with patch.object(surface, '_limited_action_change_feeling_sentences', side_effect=AssertionError('author')), \
         patch.object(surface, '_shared_observation_change_relation', side_effect=AssertionError('eligibility')), \
         patch.object(surface, '_render_final_stage1_limited_scope', side_effect=AssertionError('renderer')):
        return evaluate_grounded_surface_body_inverse(
            body=result.artifact.text.replace(result.artifact.observation, observation).encode(),
            plan=plan_override or plan, sentence_plan=sentence, resolver=resolver,
            selected_subjective_input=selected)


@pytest.mark.parametrize('memo', [
    ACTION_CHANGE_CONTRAST_MEMO,
    ACTION_CHANGE_CONTRAST_MEMO.replace('窓辺の鉢を棚', '窓際の鉢を台'),
    ACTION_CHANGE_CONTRAST_MEMO.replace('机の上が広く', '作業台の上が広く'),
    ACTION_CHANGE_CONTRAST_MEMO.replace('広くなってうれしかった', '思っていたより広くなってとてもうれしかった'),
    ACTION_CHANGE_CONTRAST_MEMO.replace('広くなってうれしかった', '明るくなって嬉しかった'),
])
def test_complete_source_episode_and_degree_survive_independent_reading(memo):
    context = _limited_context(memo)
    verdict = _read(context, context[0].artifact.observation)
    assert verdict.passed, verdict.failure_codes


@pytest.fixture(scope='module')
def context():
    return _limited_context()


@pytest.mark.parametrize('old,new', [
    ('移したら、', '移したから、'), ('移したら、', '移したあと、'),
    ('移したら、', '移さなかったら、'), ('うれしかったのは、', 'うれしいのは、'),
    ('うれしかったのは、', 'うれしくなかったのは、'), ('のは、', 'のも、'),
    ('広くなったこと', '広くなること'), ('机の上が広くなったこと', '広くなったこと'),
    ('うれしかったのは、', '弟がうれしかったのは、'),
    ('一方で、', 'なので、'), ('一方で、', 'その結果、'),
    ('いつも見ていた葉が遠くなって、', ''), ('寂しさも残っている', '寂しさは残っていない'),
    ('なって、', 'なったので、'), ('ないという寂しさ', 'あるという寂しさ'),
    ('ないという寂しさ', 'ないことでの寂しさ'),
    ('寂しさも残っている', '寂しさも残っていた'),
    ('まだ配置は見つかっていない', '配置は見つかった'),
    ('明日、棚を動かす', '今日、棚を動かした'),
    ('という、これからの行動', 'という行動'),
    ('ことなのですね。', 'ことなのですね。相手も喜んでいました。'),
])
def test_changed_actual_meaning_is_rejected_without_author(context, old, new):
    original = context[0].artifact.observation
    changed = original.replace(old, new, 1)
    assert changed != original
    assert not _read(context, changed).passed


@pytest.mark.parametrize('operation', ['remove_action', 'remove_burden', 'remove_unfinished',
                                     'remove_future', 'swap', 'duplicate', 'quote'])
def test_missing_reordered_or_quoted_clauses_do_not_count_as_finite_evidence(context, operation):
    original = context[0].artifact.observation
    rows = original.split('。')
    if operation == 'remove_action': rows[0] = rows[0].replace('窓辺の鉢を棚へ移したら、', '')
    elif operation == 'remove_burden': rows[1] = ''
    elif operation == 'remove_unfinished': rows = [r for r in rows if 'まだ配置' not in r]
    elif operation == 'remove_future': rows = [r for r in rows if '明日、棚' not in r]
    elif operation == 'swap': rows[0], rows[1] = rows[1], rows[0]
    elif operation == 'duplicate': rows.insert(1, rows[0])
    elif operation == 'quote': rows[0] = '「' + rows[0] + '」'
    changed = '。'.join(rows)
    assert changed != original
    assert not _read(context, changed).passed


@pytest.mark.parametrize('field,value', [('actor', 'other_person'), ('time_scope', 'future'),
                                       ('polarity', 'negative'), ('modality', 'possibility')])
def test_changed_source_scope_cannot_borrow_a_valid_finite_body(context, field, value):
    result, plan, sentence, resolver, selected = context
    support = next(r for r in plan.relations if r.type == 'action_supports_change'
                   and r.relation_id in sentence.lines[0].binding.relation_ids)
    assert getattr(next(n for n in plan.nuclei if n.nucleus_id == support.to_nucleus_id).semantic_frame, field) != value
    nuclei = tuple(replace(n, semantic_frame=replace(n.semantic_frame, **{field: value}))
                   if n.nucleus_id == support.to_nucleus_id else n for n in plan.nuclei)
    assert not _read(context, result.artifact.observation, replace(plan, nuclei=nuclei)).passed



@pytest.mark.parametrize('marker', ['その後、', 'それから、', 'その後', 'それから'])
@pytest.mark.parametrize('action,visible', [('私は資料を調べた後、', '資料を調べた後、'),
    ('僕は、資料を調べてから、', '資料を調べてから、')])
@pytest.mark.parametrize('ending,plain', [('落ち着きました', '落ち着いた'),
    ('私は、嬉しかったです', '嬉しかった'), ('うれしかったです', 'うれしかった'),
    ('疑問が減りました', '疑問が減った'), ('気持ちメモが増えました', '気持ちメモが増えた'),
    ('資料が戻りました', '資料が戻った'),
    ('落ち着いた', '落ち着いた'), ('私は、嬉しかった', '嬉しかった'),
    ('うれしかった', 'うれしかった'), ('疑問が減った', '疑問が減った'),
    ('気持ちメモが増えた', '気持ちメモが増えた'), ('資料が戻った', '資料が戻った'),
    ('自分が戻った', '自分が戻った')])
def test_prefixed_polite_episode_keeps_marker_without_first_person_or_support(marker, action, visible, ending, plain):
    import cocolon_meaning_experience_engine.emlis_stage1_response as response
    from test_cmee_emlis_received_discourse import inverse
    memo = marker + action + ending + '。'
    relation, = _action_change_relations(_polite_change_plan(memo))
    assert relation.retention == 'required'
    attempts = []
    def capture(**kwargs):
        verdict = evaluate_grounded_surface_body_inverse(**kwargs)
        attempts.append((kwargs, verdict))
        return verdict
    with patch.object(response, 'evaluate_grounded_surface_body_inverse', capture):
        result = MeaningExperienceEngine().generate(initial(memo))
    assert result.artifact is not None, result.reason_codes
    body = result.artifact.reception
    assert body == marker + visible + plain + 'のですね。'
    actual = next(kwargs for kwargs, verdict in reversed(attempts)
                  if verdict.passed and kwargs['body'] == result.artifact.text.encode())
    assert {k['sentence_plan'].recovery_stage for k, _ in attempts} >= {'full', 'optional_removed', 'integrated', 'hedged'}
    for kwargs, _ in attempts:
        assert '支えている' not in kwargs['body'].decode()
        assert '大切に思っています' not in kwargs['body'].decode()
    context = (result, actual['plan'], actual['sentence_plan'], actual['resolver'], actual['selected_subjective_input'])
    assert inverse(context, body, without_author=True).passed
    for changed in (body.replace(marker, '', 1), body.replace(marker, '翌日、', 1),
                    body.replace(marker, 'それから、' if marker == 'その後、' else 'その後、', 1),
                    body.replace(marker, marker + '友人が', 1),
                    body.replace('から、', 'ので、').replace('後、', 'ので、'),
                    body.replace(plain, ''), body.replace('のですね', 'ことが支えています')):
        assert changed != body
        assert not inverse(context, changed, without_author=True).passed


@pytest.mark.parametrize('ending', ['落ち着きました', '資料が戻りました', '落ち着いた', '資料が戻った'])
@pytest.mark.parametrize('prefix,action,suffix', [
    ('その後昨日、', '私は資料を調べた後、', ''),
    ('それからその後、', '私は資料を調べた後、', ''),
    ('その後、', '友人は資料を調べた後、', ''),
    ('その後、', '資料を調べた後、', ''),
    ('その後、', '私は何を調べた後、', ''),
    ('その後、', '私は資料を調べなかった後、', ''),
    ('「その後、', '私は資料を調べた後、', '」と聞いた'),
    ('友人は言った。その後、', '私は資料を調べた後、', ''),
    ('夢を見た。その後、', '私は資料を調べた後、', ''),
    ('その後、', '私は資料を調べた後、', 'か'),
    ('その後、', '私は資料を調べた後、', 'と聞いた'),
    ('友人が言っていた。その後、', '私は資料を調べた後、', ''),
    ('その後、', '私は資料を調べた後、', '。と私は思う'),
    ('その後、', '私は資料を調べた後、', '。なんて嘘だった'),
])
@pytest.mark.parametrize('unpunctuated', [False, True])
def test_prefixed_polite_episode_requires_complete_self_source(prefix, action, suffix, ending, unpunctuated):
    if unpunctuated:
        prefix = prefix.replace('その後、', 'それから').replace('それから、', 'それから')
    assert not _action_change_relations(_polite_change_plan(prefix + action + ending + suffix + '。'))


@pytest.mark.parametrize('ending', ['落ち着いた', '嬉しかった', '疑問が減った', '資料が戻った'])
def test_unpunctuated_plain_compound_has_source_proven_sequence(ending):
    plan = _polite_change_plan('それから私は資料を調べた後、' + ending + '。')
    relation, = _action_change_relations(plan)
    result = next(n for n in plan.nuclei if n.nucleus_id == relation.to_nucleus_id)
    assert 'semantic_role:source_proven_plain_sequence' in result.semantic_frame.attribute_codes


@pytest.mark.parametrize('ending', ['落ち着いた', '私は、嬉しかった', '疑問が減った', '自分が戻った'])
@pytest.mark.parametrize('following', ['その後、私は記録を残した。', 'その後、私は記録を残さなかった。'])
def test_plain_prefixed_episode_with_following_action_keeps_noncausal_reception(ending, following):
    memo = 'それから私は資料を調べてから、' + ending + '。' + following
    result = MeaningExperienceEngine().generate(initial(memo))
    assert result.artifact is not None, result.reason_codes
    body = result.artifact.reception
    assert ('それから資料を調べてから、' + ending.replace('私は、', '') + 'のですね。') in body
    assert '支えて' not in body and '大切に思っています' not in body
