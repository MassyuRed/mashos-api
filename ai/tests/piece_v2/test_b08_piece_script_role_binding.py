"""Whole written honorific identities in the disabled Piece publicizer.

All names and source sentences here are synthetic. Script changes do not grant
new relationships, authentication, public activation, or native acceptance.
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
    ('アキラさん', 'ミナさん', 'ユウさん'),
    ('田中アキラさん', '佐藤ミナさん', '鈴木ユウさん'),
    ('アキラ田中さん', 'ミナ佐藤さん', 'ユウ鈴木さん'),
    ('ジョージさん', 'メアリーさん', 'ジャンさん'),
)
CASES = (
    ('direct',
     '私は友人の{a}と落ち着いて話したい。{a}とはまだ会っていない。',
     '私は、友人と落ち着いて話したい。友人とはまだ会っていない。',
     {'a': '友人'}),
    ('chain',
     '私は私の友人の{a}の上司の{b}と話したい。{a}と{b}の都合はまだ分からない。',
     '私は、私の友人の上司と話したい。私の友人と私の友人の上司の都合はまだ分からない。',
     {'a': '私の友人', 'b': '私の友人の上司'}),
    ('late_owner',
     '私は{a}の上司の{b}と話したい。友人の{a}とはまだ会っていない。{b}の都合はまだ分からない。',
     '私は、友人の上司と話したい。友人とはまだ会っていない。友人の上司の都合はまだ分からない。',
     {'a': '友人', 'b': '友人の上司'}),
    ('three_links',
     '私は友人の{a}の上司の{b}の同僚の{c}と話したい。{c}とはまだ会っていない。',
     '私は、友人の上司の同僚と話したい。友人の上司の同僚とはまだ会っていない。',
     {'a': '友人', 'b': '友人の上司', 'c': '友人の上司の同僚'}),
    ('condition',
     '私は友人の{a}が来られるなら、{a}と話したい。まだ、会う日は決めていない。',
     '私は、友人が来られるなら、友人と話したい。まだ、会う日は決めていない。',
     {'a': '友人'}),
    ('concession',
     '友人の{a}は忙しいけれど、私は{a}と急いで話したくない。まだ、会う日は決めていない。',
     '友人は忙しいけれど、私は、友人と急いで話したくない。まだ、会う日は決めていない。',
     {'a': '友人'}),
    ('evaluation',
     '私にとって友人の{a}と話す時間が大切です。{a}と毎日会えるとは限らない。',
     '私にとって、友人と話す時間が大切です。友人と毎日会えるとは限らない。',
     {'a': '友人'}),
    ('focal',
     '私が大切にしたいのは、友人の{a}と話す時間です。{a}とはまだ会っていない。',
     '私は、友人と話す時間を大切にしたい。\n\n友人とはまだ会っていない。',
     {'a': '友人'}),
)


def outcome(text):
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-script-role', 'v1', text)
    out = MeaningExperienceEngine().generate(PieceGenerationRequest(
        'synthetic-script-role', source, source.owner_id,
        source.saved_input_id, source.source_version))
    return source, out


@pytest.mark.parametrize('names', NAMES, ids=['katakana', 'kanji_kana', 'kana_kanji', 'long_vowel'])
@pytest.mark.parametrize('case,template,expected,roles', CASES, ids=[x[0] for x in CASES])
def test_script_changes_preserve_written_relationships_and_canonical_meaning(names, case, template, expected, roles):
    named = dict(zip(('a', 'b', 'c'), names, strict=True))
    text = template.format(**named)
    source, out = outcome(text)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    assert out.artifact.piece_text == expected
    assert out.artifact.piece_text_hash == hashlib.sha256(expected.encode('utf-8')).hexdigest()
    meaning, plan = out.source_meaning, out.artifact_plan
    assert meaning.envelope.raw_utf8 == text.encode('utf-8')
    assert piece_public_role_aliases(meaning.role_bindings) == {named[key]: value for key, value in roles.items()}
    for binding in meaning.role_bindings:
        assert text[binding.source_start:binding.source_end] == binding.role + 'の' + binding.name
        assert binding.name not in out.artifact.piece_text
    for node, evidence in zip(meaning.graph.nodes, meaning.evidence, strict=True):
        assert text[evidence.scalar_start:evidence.scalar_end] == node.value
        assert text.encode('utf-8')[evidence.utf8_start:evidence.utf8_end].decode('utf-8') == node.value
    ids = [node for block in plan.block_node_ids for node in block]
    assert sorted(ids) == sorted(node.node_id for node in meaning.graph.nodes)
    assert len(ids) == len(meaning.graph.nodes)
    before = asdict(meaning), asdict(plan)
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id)
    assert candidate == out.artifact.as_candidate()
    assert (asdict(meaning), asdict(plan)) == before
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    assert candidate['production_enabled'] is False
    assert candidate['candidate_state'] == 'OFFLINE_NOT_ACCEPTED'


REJECT = (
    ('unbound', '私は{a}と落ち着いて話したい。まだ、会う日は決めていない。'),
    ('owner_unbound', '私は{a}の上司の{b}と話したい。まだ、会う日は決めていない。'),
    ('unknown_role', '私は友人の{a}と話したい。家族の{a}とはまだ会っていない。'),
    ('role_collision', '私は友人の{a}と友人の{b}に話を聞きたい。まだ、会う日は決めていない。'),
    ('identity_conflict', '私は友人の{a}と話したい。上司の{a}とはまだ会っていない。'),
    ('name_as_material', '私は友人の{a}という名前を書きたい。まだ、書く日は決めていない。'),
    ('cycle', '私は{a}の上司の{b}と話したい。{b}の同僚の{a}とはまだ会っていない。'),
)


@pytest.mark.parametrize('names', NAMES, ids=['katakana', 'kanji_kana', 'kana_kanji', 'long_vowel'])
@pytest.mark.parametrize('case,template', REJECT, ids=[x[0] for x in REJECT])
def test_script_changes_do_not_infer_or_erase_unresolved_identity(names, case, template):
    _, out = outcome(template.format(**dict(zip(('a', 'b', 'c'), names, strict=True))))
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.artifact is None
    assert out.as_body_free()['record_effect'] == out.as_body_free()['quota_effect'] == 0


@pytest.mark.parametrize('short,long', [
    ('アキラさん', 'ミアキラさん'),
    ('アキラさん', '山田アキラさん'),
    ('田中さん', 'アキラ田中さん'),
])
def test_whole_names_never_become_a_known_suffix(short, long):
    _, out = outcome(f'私は友人の{short}と話したい。{long}とはまだ会っていない。')
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.artifact is None
    _, out = outcome(f'私は友人の{short}と上司の{long}に話を聞きたい。{short}と{long}は別々の部署で働いている。')
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    assert out.artifact.piece_text == '私は、友人と上司に話を聞きたい。友人と上司は別々の部署で働いている。'


def test_ordinary_hiragana_san_is_not_a_named_person():
    _, out = outcome('私が大切にしたいのは、たくさん本を読む時間です。まだ、読む本は決めていない。')
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    assert out.artifact.piece_text == '私は、たくさん本を読む時間を大切にしたい。\n\nまだ、読む本は決めていない。'
    assert out.source_meaning.role_bindings == ()


# A name used as the material of a statement cannot be replaced by its role.
# Horizontal layout is source text, not permission to turn a label into a
# person reference. These are whole-engine probes, not regex-only assertions.
MATERIAL_NAMES = ('田中さん', 'アキラさん', 'あいさん', 'Jean・Lucさん')
HORIZONTAL_GAPS = ('', ' ', '\t', '\u3000', '、 ', '\u3000，\t')


@pytest.mark.parametrize('name', MATERIAL_NAMES)
@pytest.mark.parametrize('label', ('名前', '名字', '姓', '呼び名', '氏名'))
@pytest.mark.parametrize('gap', HORIZONTAL_GAPS)
def test_written_identity_label_never_becomes_a_relationship(name, label, gap):
    text = f'私は友人の{name}について話したい。{label}は{gap}{name}。'
    _, out = outcome(text)
    assert out.status == EngineStatus.UNAVAILABLE
    # An unpunctuated hiragana mention may already be refused by the older
    # whole-name boundary, before the material guard is reached.
    assert out.reason_codes in (('public_identity_is_material',), ('public_role_binding_missing',))
    assert out.artifact is None
    assert out.as_body_free()['record_effect'] == out.as_body_free()['quota_effect'] == 0
    assert text not in str(out.as_body_free())


@pytest.mark.parametrize('name', MATERIAL_NAMES)
@pytest.mark.parametrize('suffix', ('という名前を確かめたい', 'と言う名前を確かめたい',
                                  'っていう名前を確かめたい', 'と呼ぶ名前を確かめたい',
                                  'と書く名前を確かめたい', 'と読む名前を確かめたい',
                                  'と名付けたい', 'と名づけたい',
                                  'と名付けたいです', 'と名づけたくないです'))
@pytest.mark.parametrize('gap', ('', ' ', '\t', '\u3000'))
def test_identity_material_operator_never_becomes_a_relationship(name, suffix, gap):
    text = f'私は友人の{name}{gap}{suffix}。まだ、確認する日は決めていない。'
    _, out = outcome(text)
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.reason_codes in (('public_identity_is_material',), ('public_role_binding_missing',))
    assert out.artifact is None


@pytest.mark.parametrize('name', ('皆さん', '父さん', '母さん', '兄さん', '姉さん', '爺さん', '婆さん',
                                '叔父さん', '伯父さん', '叔母さん', '伯母さん', '旦那さん', '嫁さん', '娘さん',
                                'みなさん', 'とうさん', 'かあさん'))
@pytest.mark.parametrize('following', ('まだ、会う日は決めていない。', '{name}とはまだ会っていない。'))
def test_collective_and_kinship_are_not_singular_named_friends(name, following):
    text = f'私は友人の{name}と話したい。' + following.format(name=name)
    _, out = outcome(text)
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.reason_codes == ('public_role_binding_ambiguous',)
    assert out.artifact is None


@pytest.mark.parametrize('name', MATERIAL_NAMES)
@pytest.mark.parametrize('gap', (' ', '\t', '\u3000'))
def test_horizontal_layout_does_not_reject_an_ordinary_person_reference(name, gap):
    text = f'私は友人の{name}{gap}の名前を確認したい。{name}とはまだ会っていない。'
    source, out = outcome(text)
    expected = f'私は、友人{gap}の名前を確認したい。友人とはまだ会っていない。'
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    assert out.artifact.piece_text == expected
    assert out.source_meaning.envelope.raw_utf8 == text.encode('utf-8')
    for node, evidence in zip(out.source_meaning.graph.nodes, out.source_meaning.evidence, strict=True):
        assert text[evidence.scalar_start:evidence.scalar_end] == node.value
        assert text.encode('utf-8')[evidence.utf8_start:evidence.utf8_end].decode('utf-8') == node.value
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id)
    assert candidate == out.artifact.as_candidate()


@pytest.mark.parametrize('name', ('皆川さん', '母里さん', '父石さん', '兄田さん', '姉崎さん', '大母さん'))
def test_nonidentity_spellings_do_not_reject_parts_of_a_whole_person_name(name):
    _, out = outcome(f'私は友人の{name}と話したい。{name}とはまだ会っていない。')
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    assert out.artifact.piece_text == '私は、友人と話したい。友人とはまだ会っていない。'


@pytest.mark.parametrize('spelling', ('名付け', '名づけ'))
@pytest.mark.parametrize('ending', ('たい', 'たくない', 'たいです', 'たくないです',
                                  'ました', 'ませんでした', 'ます', 'た', 'る', 'ない'))
def test_finite_naming_does_not_change_the_written_name_into_a_role(spelling, ending):
    _, out = outcome(f'私は人形を友人の田中さんと{spelling}{ending}。まだ、用意はできていない。')
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.reason_codes == ('public_identity_is_material',)
    assert out.artifact is None


@pytest.mark.parametrize('name', MATERIAL_NAMES)
@pytest.mark.parametrize('topic', ('名付けについて話したい', '名づけについて話したい',
                                 '名付けの候補を考えたい', '名づけには参加したい'))
def test_naming_as_a_conversation_topic_keeps_the_person_reference(name, topic):
    _, out = outcome(f'私は友人の{name}と{topic}。{name}とはまだ会っていない。')
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    assert out.artifact.piece_text == f'私は、友人と{topic}。友人とはまだ会っていない。'


@pytest.mark.parametrize('name', MATERIAL_NAMES)
@pytest.mark.parametrize('label', ('名前', '名字', '姓', '呼び名', '氏名'))
@pytest.mark.parametrize('gap', (' ', '\t', '\u3000'))
def test_identity_label_layout_before_the_particle_does_not_change_its_value(name, label, gap):
    _, out = outcome(f'私は友人の{name}について話したい。{label}{gap}は {name}。')
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.reason_codes == ('public_identity_is_material',)
    assert out.artifact is None
