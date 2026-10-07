"""Public synthetic contact/target-boundary regressions; no real user material."""
import hashlib

import pytest
from piece_v2_contract import PieceContractError, validate_piece_text_binding
from piece_v2_content_policy import check_existing_detectors
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate


@pytest.mark.parametrize('contact', [
    'sample@example.test', 'Sample@EXAMPLE.TEST', 'name+tag@example.test',
])
def test_email_adjacent_to_japanese_is_not_emitted(contact):
    from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
    text = f'私が大切にしたいのは、連絡先を{contact}にしておくことです。'
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-source', '1', text)
    with pytest.raises(PieceContractError):
        generate_piece_candidate(source, authenticated_owner_id='synthetic-owner')


_CONTACT_CASES = [
    pytest.param('https://example.test/path', 'existing_safety_detector', id='https-adjacent'),
    pytest.param('http://example.test', 'existing_safety_detector', id='http-adjacent'),
    pytest.param('www.example.test', 'existing_safety_detector', id='www-adjacent'),
    pytest.param('@sample_account', 'existing_safety_detector', id='handle-adjacent'),
    pytest.param('ｈｔｔｐｓ：／／ｅｘａｍｐｌｅ．ｔｅｓｔ', 'existing_safety_detector', id='fullwidth-url'),
    pytest.param('ｎａｍｅ＠ｅｘａｍｐｌｅ．ｔｅｓｔ', 'existing_safety_detector', id='fullwidth-mail'),
    pytest.param('＠ｓａｍｐｌｅ＿ａｃｃｏｕｎｔ', 'existing_safety_detector', id='fullwidth-handle'),
    pytest.param('ｐａｓｓｗｏｒｄ＝ｓｙｎｔｈｅｔｉｃ', 'credential_like_material', id='fullwidth-credential'),
    pytest.param('０８０－１２３４－５６７８', 'existing_safety_detector', id='fullwidth-phone'),
    pytest.param('ＬＩＮＥ　ＩＤ：ｓａｍｐｌｅ＿ｉｄ', 'existing_safety_detector', id='fullwidth-line'),
]


@pytest.mark.parametrize('contact, reason', _CONTACT_CASES)
def test_policy_rejects_adjacent_and_fullwidth_contact(contact, reason):
    text = f'連絡先は{contact}です。'
    with pytest.raises(PieceContractError) as error:
        check_existing_detectors(text)
    assert error.value.code == 'PIECE_CONTENT_UNAVAILABLE'
    assert error.value.detail == reason
    assert str(error.value) == f'PIECE_CONTENT_UNAVAILABLE:{reason}'
    assert contact not in str(error.value)


@pytest.mark.parametrize('text', [
    '私は、ＡＢＣの読書時間を大切にしたい。',
    '私は家族👩\u200d👩\u200d👧\u200d👦との時間を大切にしたい。',
    '私はcafe\u0301で過ごす時間を大切にしたい。',
    '私は①つずつ自分の考えを確かめたい。',
    '私にとって、電話で話す時間は大切です。',
    '私はメールより手紙を書く時間を大切にしたい。',
    '私は人と話すことが好きではない。',
])
def test_policy_detection_view_does_not_rewrite_visible_unicode(text):
    before = text.encode('utf-8')
    digest = hashlib.sha256(before).hexdigest()
    assert check_existing_detectors(text) is None
    assert text.encode('utf-8') == before
    assert hashlib.sha256(text.encode('utf-8')).hexdigest() == digest


@pytest.mark.parametrize('text, reason', [
    ('私\u200bは読書が好きです。', 'hidden_control'),
    ('私は\u202e読書が好きです。', 'hidden_control'),
    ('私は\ud800読書が好きです。', 'malformed_unicode'),
])
def test_policy_existing_unicode_rejections_keep_body_free_reason(text, reason):
    with pytest.raises(PieceContractError) as error:
        check_existing_detectors(text)
    assert error.value.detail == reason
    assert str(error.value) == f'PIECE_CONTENT_UNAVAILABLE:{reason}'


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
@pytest.mark.parametrize('contact, reason', _CONTACT_CASES)
def test_engine_rejects_source_contact_before_candidate_admission(tier, contact, reason):
    from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
    text = f'私が大切にしたいのは、連絡先を{contact}にしておくことです。'
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-source', '1', text)
    with pytest.raises(PieceContractError) as error:
        generate_piece_candidate(source, authenticated_owner_id='synthetic-owner', tier=tier)
    # An unrelated grammar/import error is not contact-safety evidence.
    assert error.value.code == 'PIECE_CONTENT_UNAVAILABLE'
    assert error.value.detail == reason


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
@pytest.mark.parametrize('contact, reason', _CONTACT_CASES)
def test_engine_rechecks_contact_after_format_realization(monkeypatch, tier, contact, reason):
    from cocolon_meaning_experience_engine import piece_v1c
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-source', '1',
        '私が大切にしたいのは、自分の気持ちを丁寧に見つめる時間です。')
    # Only the realized output is contaminated; source admission is still real.
    original_validate = piece_v1c.validate_candidate_text
    def contaminate(payload):
        original_validate(payload)
        return f'私は自分の時間を大切にしたい。連絡先は{contact}です。'
    monkeypatch.setattr(piece_v1c, 'validate_candidate_text', contaminate)
    with pytest.raises(PieceContractError) as error:
        generate_piece_candidate(source, authenticated_owner_id='synthetic-owner', tier=tier)
    assert error.value.code == 'PIECE_CONTENT_UNAVAILABLE'
    assert error.value.detail == reason


# PCE-4: name abstraction cannot verify an allegation about its remaining role.
_ROLE_ASSERTIONS = (
    '友人は詐欺師です。',
    '私の友人の上司は犯罪者だった。',
    '上司が泥棒でした。',
    '同僚は、嘘つきだ。',
    '先輩はうそつきである。',
    '後輩は　詐欺師　です。',
)

_NAMED_ASSERTIONS = (
    ('focal-fraud',
     '私が大切にしたいのは、友人のAliceさんと話す時間です。Aliceさんは詐欺師です。'),
    ('direct-lie',
     '私は友人のAliceさんと落ち着いて話したい。Aliceさんは嘘つきだ。'),
    ('negative-state-crime',
     '私は上司のBobさんとの時間を大切にしていない。Bobさんは犯罪者だった。'),
    ('owned-role-theft',
     '私は私の友人のAliceさんの上司のBobさんと話したい。Bobさんは泥棒でした。'),
    ('fullwidth-name',
     '私は友人のＡｌｉｃｅさんと落ち着いて話したい。Ａｌｉｃｅさんは詐欺師である。'),
)


def assert_private_rejection(call):
    with pytest.raises(PieceContractError) as error:
        call()
    # A different parser/import/shape failure is not this regression's proof.
    assert str(error.value) == 'PIECE_CONTENT_UNAVAILABLE:existing_safety_detector'


@pytest.mark.parametrize('text', _ROLE_ASSERTIONS)
def test_direct_role_assertion_is_not_verified_by_removing_a_name(text):
    assert_private_rejection(lambda: check_existing_detectors(text))


@pytest.mark.parametrize('tier', ('free', 'plus', 'premium'))
@pytest.mark.parametrize('case,text', _NAMED_ASSERTIONS,
                         ids=[case[0] for case in _NAMED_ASSERTIONS])
def test_real_cmee_does_not_emit_the_assertion_after_named_role_abstraction(case, text, tier):
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-assertion', 'v1', text)
    before = hashlib.sha256(text.encode('utf-8')).hexdigest()
    assert_private_rejection(lambda: generate_piece_candidate(
        source, authenticated_owner_id=source.owner_id, tier=tier))
    assert source.original_text == text
    assert hashlib.sha256(source.original_text.encode('utf-8')).hexdigest() == before


@pytest.mark.parametrize('tier,requested_format', (
    ('free', None), ('plus', None), ('premium', 'short_essay'),
    ('premium', 'quote'), ('premium', 'declaration'),
))
@pytest.mark.parametrize('tail', ('友人は詐欺師です。', '私の友人の上司は泥棒だった。'))
def test_final_format_cannot_reinject_an_assertive_role_accusation(monkeypatch, tier, requested_format, tail):
    from cocolon_meaning_experience_engine import piece_v1c
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-clean-source', 'v1',
        '私が大切にしたいのは、自分の気持ちを丁寧に見つめる時間です。')
    original_validate = piece_v1c.validate_candidate_text

    def contaminated_output(payload):
        original_validate(payload)
        return '私は、自分の気持ちを丁寧に見つめる時間を大切にしたい。' + tail

    monkeypatch.setattr(piece_v1c, 'validate_candidate_text', contaminated_output)
    assert_private_rejection(lambda: generate_piece_candidate(
        source, authenticated_owner_id=source.owner_id,
        tier=tier, requested_format=requested_format))


@pytest.mark.parametrize('text', (
    '友人は詐欺師ではない。',
    '友人は詐欺師ではありません。',
    '友人は詐欺師ではなかった。',
    '友人は詐欺師かもしれない。',
    '友人は詐欺師とは限らない。',
    '友人は詐欺師だと思っていたが、違っていた。',
    '友人は詐欺師だったという話は事実ではない。',
    '友人が詐欺師なら、私は距離を置きたい。',
    '私は詐欺師を扱った本を読みたい。',
    '私は友人に怒りを感じています。',
    '友人は詐欺師という言葉が苦手です。',
))
def test_words_alone_do_not_turn_negation_or_uncertainty_into_an_assertion(text):
    # This is only a non-match control for the bounded detector, NOT public
    # admission of uncertain allegations, quoted claims or every possible risk.
    original = text.encode('utf-8')
    assert check_existing_detectors(text) is None
    assert text.encode('utf-8') == original


@pytest.mark.parametrize('tier', ('free', 'plus', 'premium'))
@pytest.mark.parametrize('text,expected', (
    ('私は友人のAliceさんと落ち着いて話したい。Aliceさんの都合はまだ分からない。',
     '私は、友人と落ち着いて話したい。友人の都合はまだ分からない。'),
    ('私は友人のAliceさんが来られるなら、Aliceさんと急いで話したくない。まだ、会う日は決めていない。',
     '私は、友人が来られるなら、友人と急いで話したくない。まだ、会う日は決めていない。'),
))
def test_benign_relationship_and_owner_reservation_keep_the_same_actual_body(tier, text, expected):
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-benign-role', 'v1', text)
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id, tier=tier)
    assert candidate['piece_text'] == expected
    assert validate_piece_text_binding(candidate['content_payload'], expected,
        candidate['piece_text_hash']) == expected
    assert source.original_text == text
    assert candidate['candidate_state'] == 'OFFLINE_NOT_ACCEPTED'
    assert 'safety_state' not in candidate
    assert candidate['production_enabled'] is False
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
