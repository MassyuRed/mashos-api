"""Synthetic source-to-Piece cases; no private review inputs or fixture dispatch."""
import hashlib
import pytest
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate


def generate(text, **kwargs):
    return generate_piece_candidate(PieceSourceSnapshot('owner', 'saved', 'v1', text),
                                    authenticated_owner_id='owner', **kwargs)


CONTEXTS = (
    ('予定を詰めると、一人で過ごす時間が足りなくなる。',
     '人と会う時間も私には大切だ。',
     '自分の調子に合わせて、無理のない予定を選びたい'),
    ('すぐに決めると、気持ちが追いつかないことがある。',
     '迷う時間も私には必要だ。',
     '速さだけで答えを決めず、自分で納得できる選び方を続けたい'),
    ('長く歩くと、疲れてしまうこともある。',
     '新しい景色を見る楽しさも残っている。',
     '体調に余裕があるときに、知らない道も歩いてみたい'),
    ('今はまだ、考えが変わるかもしれない。',
     '人の意見を聞かないわけではない。',
     '迷いを隠して、決まった答えのようには話したくない'),
)


@pytest.mark.parametrize('context,qualification,wish', CONTEXTS)
@pytest.mark.parametrize('speaker', ['私', '僕', 'わたし'])
def test_source_owned_expression_precedes_complete_context(context, qualification, wish, speaker):
    source = context + qualification + speaker + 'は' + wish + '。'
    result = generate(source)
    expected = speaker + 'は、' + wish + '。\n\n' + context + qualification
    assert result['piece_text'] == expected
    assert result['content_payload']['body_blocks'] == [expected.split('\n\n')[0], context + qualification]
    assert result['piece_text_hash'] == hashlib.sha256(expected.encode()).hexdigest()
    assert result['eligible_formats'] == ['short_essay']
    assert result['format_type'] == 'short_essay'
    assert not result['production_enabled']
    assert result['record_effect'] == result['quota_effect'] == 0


def test_repeated_context_is_not_lost_to_shared_summary_deduplication():
    context = '人と会う時間も私には大切だ。'
    result = generate(context * 2 + '私は、無理のない予定を選びたい。')
    assert result['piece_text'] == '私は、無理のない予定を選びたい。\n\n' + context * 2


def test_complete_condition_and_uncertainty_stay_inside_the_original_wish():
    text = ('気持ちが変わることもある。答えを急がない時間も必要だ。'
            '私は迷っている間は、まだ一つの答えに決めたくない。')
    assert generate(text)['piece_text'] == (
        '私は、迷っている間は、まだ一つの答えに決めたくない。\n\n'
        '気持ちが変わることもある。答えを急がない時間も必要だ。')


@pytest.mark.parametrize('text', [
    '私は、自分の歩幅で進みたい。',
    '朝はゆっくり歩いた。友人は自分の歩幅で進みたい。',
    '朝はゆっくり歩いた。私は友人が自分の歩幅で進みたいと言っていた。',
    '朝はゆっくり歩いた。私は自分の歩幅で進みたい？',
    '朝はゆっくり歩いた。私は自分の歩幅で進みたいのだろうか。',
    '朝はゆっくり歩いた。私はそれを続けたい。',
    '朝はゆっくり歩いた。私はその時間を大切にしたい。',
    '朝はゆっくり歩いた。だから、私は自分の歩幅で進みたい。',
    '朝はゆっくり歩いた。私は、だから自分の歩幅で進みたい。',
    '朝はゆっくり歩いた。でも、遠くまでは歩かなかった。私は自分の歩幅で進みたい。',
    '朝はゆっくり歩いた。その時は疲れていなかった。私は自分の歩幅で進みたい。',
    '朝はゆっくり歩いた。私は今は答えがわからない。',
    '朝はゆっくり歩いた。私は自分の歩幅で進みたい。まだ迷っている。',
    '朝はゆっくり歩いた。私は、自分の歩幅で進みたいと言われたい。',
])
def test_unsupported_or_reference_dependent_discourse_is_not_promoted(text):
    with pytest.raises(ValueError):
        generate(text)


@pytest.mark.parametrize('kwargs', [{'tier': 'free', 'requested_format': 'short_essay'},
                                   {'tier': 'premium', 'requested_format': 'declaration'},
                                   {'tier': 'premium', 'requested_format': 'quote'}])
def test_expression_does_not_bypass_existing_format_or_tier_contract(kwargs):
    with pytest.raises(ValueError):
        generate('迷う時間も私には必要だ。私は自分のペースで答えを選びたい。', **kwargs)


def test_source_owner_and_stage_are_checked_before_the_new_expression_path():
    text = '迷う時間も私には必要だ。私は自分のペースで答えを選びたい。'
    with pytest.raises(ValueError):
        generate_piece_candidate(PieceSourceSnapshot('other', 'saved', 'v1', text),
                                 authenticated_owner_id='owner')
    with pytest.raises(ValueError):
        generate_piece_candidate(PieceSourceSnapshot('owner', 'saved', 'v1', text,
                                                     source_stage='refined_observation'),
                                 authenticated_owner_id='owner')
