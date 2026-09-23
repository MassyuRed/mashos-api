"""Whole source-written halfwidth and middle-dot names in disabled Piece.

Synthetic inputs only. Width/spelling is identity, not a normalization hint.
Relationships and owner chains still require the same original-source proof.
"""
from dataclasses import asdict
import hashlib

import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_source import piece_public_role_aliases
from cocolon_meaning_experience_engine.piece_v1c import PieceGenerationRequest
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate


NAMES = (
    ('ｱｷﾗさん', 'ﾐﾅさん', 'ﾕｳさん'),
    ('ｼﾞｮｰｼﾞさん', 'ﾒｱﾘｰさん', 'ｼﾞｬﾝさん'),
    ('ジャン・リュックさん', 'メアリー・アンさん', 'ジャン・マリーさん'),
    ('ｼﾞｬﾝ･リュックさん', 'ﾒｱﾘｰ・ｱﾝさん', '田中･ﾕｳさん'),
)
CASES = (
    ('direct', '私は友人の{a}と落ち着いて話したい。{a}とはまだ会っていない。',
     '私は、友人と落ち着いて話したい。友人とはまだ会っていない。', {'a': '友人'}),
    ('chain', '私は私の友人の{a}の上司の{b}と話したい。{a}と{b}の都合はまだ分からない。',
     '私は、私の友人の上司と話したい。私の友人と私の友人の上司の都合はまだ分からない。',
     {'a': '私の友人', 'b': '私の友人の上司'}),
    ('late_owner', '私は{a}の上司の{b}と話したい。友人の{a}とはまだ会っていない。{b}の都合はまだ分からない。',
     '私は、友人の上司と話したい。友人とはまだ会っていない。友人の上司の都合はまだ分からない。',
     {'a': '友人', 'b': '友人の上司'}),
    ('three_links', '私は友人の{a}の上司の{b}の同僚の{c}と話したい。{c}とはまだ会っていない。',
     '私は、友人の上司の同僚と話したい。友人の上司の同僚とはまだ会っていない。',
     {'a': '友人', 'b': '友人の上司', 'c': '友人の上司の同僚'}),
    ('condition', '私は友人の{a}が来られるなら、{a}と話したい。まだ、会う日は決めていない。',
     '私は、友人が来られるなら、友人と話したい。まだ、会う日は決めていない。', {'a': '友人'}),
    ('concession', '友人の{a}は忙しいけれど、私は{a}と急いで話したくない。まだ、会う日は決めていない。',
     '友人は忙しいけれど、私は、友人と急いで話したくない。まだ、会う日は決めていない。', {'a': '友人'}),
    ('evaluation', '私にとって友人の{a}と話す時間が大切です。{a}と毎日会えるとは限らない。',
     '私にとって、友人と話す時間が大切です。友人と毎日会えるとは限らない。', {'a': '友人'}),
    ('focal', '私が大切にしたいのは、友人の{a}と話す時間です。{a}とはまだ会っていない。',
     '私は、友人と話す時間を大切にしたい。\n\n友人とはまだ会っていない。', {'a': '友人'}),
)


def outcome(text):
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-joined-kana', 'v1', text)
    result = MeaningExperienceEngine().generate(PieceGenerationRequest(
        'synthetic-joined-kana', source, source.owner_id,
        source.saved_input_id, source.source_version))
    return source, result


@pytest.mark.parametrize('names', NAMES, ids=['halfwidth', 'voiced', 'joined', 'mixed'])
@pytest.mark.parametrize('case,template,expected,roles', CASES, ids=[c[0] for c in CASES])
def test_complete_names_preserve_role_graph_source_coordinates_and_body(names, case, template, expected, roles):
    named = dict(zip(('a', 'b', 'c'), names, strict=True))
    text = template.format(**named)
    source, out = outcome(text)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    assert out.artifact.piece_text == expected
    assert out.artifact.piece_text_hash == hashlib.sha256(expected.encode('utf-8')).hexdigest()
    meaning, plan = out.source_meaning, out.artifact_plan
    assert meaning.envelope.raw_utf8 == text.encode('utf-8')
    assert piece_public_role_aliases(meaning.role_bindings) == {named[k]: v for k, v in roles.items()}
    for binding in meaning.role_bindings:
        assert text[binding.source_start:binding.source_end] == binding.role + 'の' + binding.name
        assert binding.name not in out.artifact.piece_text
    for node, evidence in zip(meaning.graph.nodes, meaning.evidence, strict=True):
        assert text[evidence.scalar_start:evidence.scalar_end] == node.value
        assert text.encode('utf-8')[evidence.utf8_start:evidence.utf8_end].decode('utf-8') == node.value
    ordered = [node for block in plan.block_node_ids for node in block]
    assert sorted(ordered) == sorted(node.node_id for node in meaning.graph.nodes)
    assert len(ordered) == len(meaning.graph.nodes)
    frozen = asdict(meaning), asdict(plan)
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id)
    assert candidate == out.artifact.as_candidate()
    assert (asdict(meaning), asdict(plan)) == frozen
    assert candidate['candidate_state'] == 'OFFLINE_NOT_ACCEPTED'
    assert candidate['production_enabled'] is False
    assert candidate['record_effect'] == candidate['quota_effect'] == 0


REJECT = (
    ('unbound', '私は{a}と落ち着いて話したい。まだ、会う日は決めていない。'),
    ('unbound_owner', '私は{a}の上司の{b}と話したい。まだ、会う日は決めていない。'),
    ('unsupported_role', '私は友人の{a}と話したい。家族の{a}とはまだ会っていない。'),
    ('role_collision', '私は友人の{a}と友人の{b}に話を聞きたい。まだ、会う日は決めていない。'),
    ('name_collision', '私は友人の{a}と話したい。上司の{a}とはまだ会っていない。'),
    ('name_as_material', '私は友人の{a}という名前を書きたい。まだ、書く日は決めていない。'),
    ('owner_cycle', '私は{a}の上司の{b}と話したい。{b}の同僚の{a}とはまだ会っていない。'),
)


@pytest.mark.parametrize('names', NAMES, ids=['halfwidth', 'voiced', 'joined', 'mixed'])
@pytest.mark.parametrize('case,template', REJECT, ids=[c[0] for c in REJECT])
def test_same_explicit_role_requirements_apply_to_all_name_forms(names, case, template):
    _, out = outcome(template.format(**dict(zip(('a', 'b', 'c'), names, strict=True))))
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.artifact is None
    assert out.as_body_free()['record_effect'] == out.as_body_free()['quota_effect'] == 0


@pytest.mark.parametrize('short,long', [
    ('リュックさん', 'ジャン・リュックさん'),
    ('ﾘｭｯｸさん', 'ｼﾞｬﾝ･ﾘｭｯｸさん'),
    ('リュックさん', 'ｼﾞｬﾝ･リュックさん'),
    ('ｱｷﾗさん', '山田ｱｷﾗさん'),
    ('ミナさん', 'ﾅミナさん'),
])
def test_suffix_is_not_the_identity_of_a_longer_name(short, long):
    _, out = outcome(f'私は友人の{short}と話したい。{long}とはまだ会っていない。')
    assert out.status == EngineStatus.UNAVAILABLE
    _, out = outcome(f'私は友人の{short}と上司の{long}に話を聞きたい。{short}と{long}は別々の部署で働いている。')
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    assert out.artifact.piece_text == '私は、友人と上司に話を聞きたい。友人と上司は別々の部署で働いている。'


@pytest.mark.parametrize('first,second', [
    ('ｱｷﾗさん', 'アキラさん'),
    ('ジャン･リュックさん', 'ジャン・リュックさん'),
    ('ｼﾞｮｰｼﾞさん', 'ジョージさん'),
])
def test_width_and_separator_variants_are_not_inferred_to_be_the_same_person(first, second):
    _, out = outcome(f'私は友人の{first}と話したい。{second}とはまだ会っていない。')
    assert out.status == EngineStatus.UNAVAILABLE
    text = f'私は友人の{first}と上司の{second}に話を聞きたい。{first}と{second}は別々の部署で働いている。'
    _, out = outcome(text)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    assert piece_public_role_aliases(out.source_meaning.role_bindings) == {first: '友人', second: '上司'}
    assert out.source_meaning.envelope.raw_utf8 == text.encode('utf-8')
    assert out.artifact.piece_text == '私は、友人と上司に話を聞きたい。友人と上司は別々の部署で働いている。'


@pytest.mark.parametrize('malformed', ['・リュックさん', 'ジャン・・リュックさん', 'ジャン・さん',
                                       '･ﾘｭｯｸさん', 'ｼﾞｬﾝ･･ﾘｭｯｸさん', 'ｼﾞｬﾝ･さん'])
def test_incomplete_joined_tokens_are_not_truncated_to_a_known_suffix(malformed):
    _, out = outcome(f'私は友人のリュックさんと話したい。上司の{malformed}とはまだ会っていない。')
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.artifact is None


@pytest.mark.parametrize('delimiter', ['、', 'と', '・', '･'])
def test_source_delimiters_do_not_join_two_distinct_named_people(delimiter):
    text = f'私は友人のｱｷﾗさんと上司のジャン・リュックさんに話を聞きたい。ｱｷﾗさん{delimiter}ジャン・リュックさんの都合はまだ分からない。'
    _, out = outcome(text)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    assert out.artifact.piece_text == f'私は、友人と上司に話を聞きたい。友人{delimiter}上司の都合はまだ分からない。'


@pytest.mark.parametrize('delimiter', ['・', '･'])
def test_middle_dot_after_closed_honorific_separates_role_phrases(delimiter):
    text = f'私は友人のｱｷﾗさん{delimiter}上司のジャン・リュックさんと話したい。ｱｷﾗさん{delimiter}ジャン・リュックさんにはまだ会っていない。'
    _, out = outcome(text)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    assert out.artifact.piece_text == f'私は、友人{delimiter}上司と話したい。友人{delimiter}上司にはまだ会っていない。'
