"""Source-written Latin honorific identities in the disabled Piece candidate.

Synthetic inputs exercise ASCII/fullwidth Latin and existing Han/kana/dot name
forms. Case and width are distinct identities. This is role/name binding, not
general PII recognition, public safety admission, or a new role vocabulary.
"""
from dataclasses import asdict
import hashlib

import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_source import piece_public_role_aliases
from cocolon_meaning_experience_engine.piece_v1c import PieceGenerationRequest
from piece_v2_contract import validate_piece_text_binding
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate


CASES = (
    ('ascii_direct',
     '私は友人のAliceさんと落ち着いて話したい。Aliceさんの都合はまだ分からない。',
     '私は、友人と落ち着いて話したい。友人の都合はまだ分からない。',
     {'Aliceさん': '友人'}),
    ('fullwidth_direct',
     '私は友人のＡｌｉｃｅさんと落ち着いて話したい。Ａｌｉｃｅさんの都合はまだ分からない。',
     '私は、友人と落ち着いて話したい。友人の都合はまだ分からない。',
     {'Ａｌｉｃｅさん': '友人'}),
    ('han_ascii_whole_name',
     '私は友人の山田Aliceさんと落ち着いて話したい。山田Aliceさんの都合はまだ分からない。',
     '私は、友人と落ち着いて話したい。友人の都合はまだ分からない。',
     {'山田Aliceさん': '友人'}),
    ('kana_mixed_width_whole_name',
     '私は友人のアリスＡliceさんと落ち着いて話したい。アリスＡliceさんの都合はまだ分からない。',
     '私は、友人と落ち着いて話したい。友人の都合はまだ分からない。',
     {'アリスＡliceさん': '友人'}),
    ('joined_latin_name',
     '私は友人のJean・Lucさんと落ち着いて話したい。Jean・Lucさんの都合はまだ分からない。',
     '私は、友人と落ち着いて話したい。友人の都合はまだ分からない。',
     {'Jean・Lucさん': '友人'}),
    ('owned_relationship_chain',
     '私は私の友人のAliceさんの上司のＢｏｂさんと話したい。AliceさんとＢｏｂさんの都合はまだ分からない。',
     '私は、私の友人の上司と話したい。私の友人と私の友人の上司の都合はまだ分からない。',
     {'Aliceさん': '私の友人', 'Ｂｏｂさん': '私の友人の上司'}),
    ('owner_bound_later',
     '私はAliceさんの上司のBobさんと話したい。友人のAliceさんとはまだ会っていない。Bobさんの都合はまだ分からない。',
     '私は、友人の上司と話したい。友人とはまだ会っていない。友人の上司の都合はまだ分からない。',
     {'Aliceさん': '友人', 'Bobさん': '友人の上司'}),
    ('conditional_negative_and_reservation',
     '私は友人のAliceさんが来られるなら、Aliceさんと急いで話したくない。まだ、会う日は決めていない。',
     '私は、友人が来られるなら、友人と急いで話したくない。まだ、会う日は決めていない。',
     {'Aliceさん': '友人'}),
    ('personal_evaluation_and_uncertainty',
     '私にとって友人のAliceさんと話す時間が大切です。Aliceさんと毎日会えるとは限らない。',
     '私にとって、友人と話す時間が大切です。友人と毎日会えるとは限らない。',
     {'Aliceさん': '友人'}),
    ('focal_expression',
     '私が大切にしたいのは、友人のAliceさんと話す時間です。Aliceさんとはまだ会っていない。',
     '私は、友人と話す時間を大切にしたい。\n\n友人とはまだ会っていない。',
     {'Aliceさん': '友人'}),
    ('case_distinguishes_people',
     '私は友人のAliceさんと上司のaliceさんに話を聞きたい。Aliceさんとaliceさんは別々の部署で働いている。',
     '私は、友人と上司に話を聞きたい。友人と上司は別々の部署で働いている。',
     {'Aliceさん': '友人', 'aliceさん': '上司'}),
    ('width_distinguishes_people',
     '私は友人のAliceさんと上司のＡｌｉｃｅさんに話を聞きたい。AliceさんとＡｌｉｃｅさんは別々の部署で働いている。',
     '私は、友人と上司に話を聞きたい。友人と上司は別々の部署で働いている。',
     {'Aliceさん': '友人', 'Ａｌｉｃｅさん': '上司'}),
)


def outcome(text):
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-latin-role', 'v1', text)
    out = MeaningExperienceEngine().generate(PieceGenerationRequest(
        'synthetic-latin-role', source, source.owner_id,
        source.saved_input_id, source.source_version))
    return source, out


def assert_source_and_candidate(source, out, expected, aliases):
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    text, raw = source.original_text, source.original_text.encode('utf-8')
    meaning, plan, artifact = out.source_meaning, out.artifact_plan, out.artifact
    assert artifact.piece_text == expected
    assert artifact.piece_text_hash == hashlib.sha256(expected.encode('utf-8')).hexdigest()
    assert validate_piece_text_binding(artifact.content_payload(), expected,
        artifact.piece_text_hash) == expected
    assert meaning.envelope.raw_utf8 == raw
    assert meaning.envelope.raw_sha256 == hashlib.sha256(raw).hexdigest()
    assert piece_public_role_aliases(meaning.role_bindings) == aliases
    for binding in meaning.role_bindings:
        assert text[binding.source_start:binding.source_end] == binding.role+'の'+binding.name
        assert binding.name not in expected
    for node, evidence in zip(meaning.graph.nodes, meaning.evidence, strict=True):
        assert text[evidence.scalar_start:evidence.scalar_end] == node.value
        literal = raw[evidence.utf8_start:evidence.utf8_end]
        assert literal.decode('utf-8') == node.value
        assert evidence.literal_sha256 == hashlib.sha256(literal).hexdigest()
        assert evidence.field_sha256 == hashlib.sha256(raw).hexdigest()
    covered = [node for block in plan.block_node_ids for node in block]
    assert sorted(covered) == sorted(node.node_id for node in meaning.graph.nodes)
    assert len(covered) == len(meaning.graph.nodes)
    before = asdict(meaning), asdict(plan)
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id)
    assert candidate == artifact.as_candidate()
    assert (asdict(meaning), asdict(plan)) == before
    assert source.original_text == text
    assert candidate['candidate_state'] == 'OFFLINE_NOT_ACCEPTED'
    assert candidate['production_enabled'] is False
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    assert 'safety_state' not in candidate


@pytest.mark.parametrize('name,text,expected,aliases', CASES, ids=[case[0] for case in CASES])
def test_written_latin_identity_is_abstracted_without_changing_its_relationship(name, text, expected, aliases):
    source, out = outcome(text)
    assert_source_and_candidate(source, out, expected, aliases)


REJECT = (
    ('unbound_name', '私はAliceさんと落ち着いて話したい。まだ、会う日は決めていない。'),
    ('unbound_owner', '私はAliceさんの上司のBobさんと話したい。まだ、会う日は決めていない。'),
    ('unknown_role', '私は友人のAliceさんと話したい。家族のAliceさんとはまだ会っていない。'),
    ('two_people_same_role', '私は友人のAliceさんと友人のBobさんに話を聞きたい。まだ、会う日は決めていない。'),
    ('conflicting_roles', '私は友人のAliceさんと話したい。上司のAliceさんとはまだ会っていない。'),
    ('cyclic_owners', '私はAliceさんの上司のBobさんと話したい。Bobさんの同僚のAliceさんとはまだ会っていない。'),
    ('name_is_written_material', '私は友人のAliceさんという名前を書きたい。まだ、書く日は決めていない。'),
    ('name_is_later_subject', '私は友人のＡｌｉｃｅさんと話したい。呼び名はＡｌｉｃｅさん。'),
    ('known_suffix_is_not_whole_name', '私は友人のAliceさんと話したい。MaryAliceさんとはまだ会っていない。'),
    ('accented_prefix_is_not_a_bound_suffix', '私は友人のAliceさんと話したい。ÉAliceさんとはまだ会っていない。'),
    ('combining_prefix_is_not_a_bound_suffix', '私は友人のAliceさんと話したい。Jo\u0301Aliceさんとはまだ会っていない。'),
    ('numeric_prefix_is_not_a_bound_suffix', '私は友人のAliceさんと話したい。1Aliceさんとはまだ会っていない。'),
    ('hyphen_join_is_not_a_bound_suffix', '私は友人のLucさんと話したい。Jean-Lucさんとはまだ会っていない。'),
    ('apostrophe_join_is_not_a_bound_suffix', "私は友人のConnorさんと話したい。O'Connorさんとはまだ会っていない。"),
    ('curly_apostrophe_join_is_not_a_bound_suffix', '私は友人のConnorさんと話したい。O’Connorさんとはまだ会っていない。'),
    ('fullwidth_hyphen_join_is_not_a_bound_suffix', '私は友人のLucさんと話したい。Jean－Lucさんとはまだ会っていない。'),
    ('case_is_not_an_alias', '私は友人のAliceさんと話したい。aliceさんとはまだ会っていない。'),
    ('width_is_not_an_alias', '私は友人のAliceさんと話したい。Ａｌｉｃｅさんとはまだ会っていない。'),
    ('malformed_dot_does_not_expose_bound_suffix', '私は友人のLucさんと話したい。上司のJean・・Lucさんとはまだ会っていない。'),
)


@pytest.mark.parametrize('name,text', REJECT, ids=[case[0] for case in REJECT])
def test_unresolved_or_meaning_bearing_latin_identity_has_no_candidate(name, text):
    _, out = outcome(text)
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.artifact is None
    body_free = out.as_body_free()
    assert body_free['record_effect'] == body_free['quota_effect'] == 0
    assert body_free['production_enabled'] is False
    assert text not in str(body_free)


@pytest.mark.parametrize('text,expected', [
    ('私が大切にしたいのは、たくさん本を読む時間です。まだ、読む本は決めていない。',
     '私は、たくさん本を読む時間を大切にしたい。\n\nまだ、読む本は決めていない。'),
    ('私はみなさんの考えを落ち着いて聞きたい。まだ、会う日は決めていない。',
     '私は、みなさんの考えを落ち着いて聞きたい。まだ、会う日は決めていない。'),
])
def test_ordinary_hiragana_words_are_not_newly_classified_as_people(text, expected):
    source, out = outcome(text)
    assert_source_and_candidate(source, out, expected, {})
