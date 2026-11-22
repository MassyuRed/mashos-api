"""A fact may quote the author's notation, but a wire key is never a fact of its own."""
import json

import pytest

from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_node_local_native_profile import accepts, advance, probe
from test_analysis_occurrence_v16_fact_content import example


SOURCE = '私は図面を提出した。担当者は預かったと知らせてくれた。'
PROFILE = core.SEMANTIC_MAP_OCCURRENCE_V18_PROFILE


@pytest.mark.parametrize('source,value,admitted', [
    (SOURCE, ",'e3/私は図面を提出した。','e3/私は図面を提", False),
    (SOURCE, "本文に続く 'e2/私は図面を提出した。", False),
    (SOURCE, 'e1/担当者は預かった。', False),
    (SOURCE, '確認後にe1/担当者は預かった。', False),
    ('stage3/fileに記録した。端末を閉じた。', "'e3/記録した。", False),
    (SOURCE, '担当者から受領の連絡があった。', True),
    (SOURCE, '@0', True), (SOURCE, '@1', True), (SOURCE, '@2', True),
    ('記録に e2/ の文字がある。標識を確認した。', '標識には e2/ とある。', True),
    ('route3/fileへの変更を記した。端末を閉じた。', 'route3/fileを参照した。', True),
])
def test_wire_key_requires_the_assigned_source(source, value, admitted):
    prepared, plan, raw, parts, messages = example(source, profile=PROFILE)
    key, = parts
    parts[key] = value
    assert accepts(raw, messages) == admitted
    if admitted:
        core.admit_semantic_node_local_v4_nodes_response(prepared, plan, raw)
    else:
        with pytest.raises(core.AnalysisSemanticMapError):
            core.admit_semantic_node_local_v4_nodes_response(prepared, plan, raw)


@pytest.mark.parametrize('profile,allowed', [(PROFILE,False),(core.SEMANTIC_MAP_OCCURRENCE_V17_PROFILE,True)])
def test_direct_and_escaped_slash_at_the_first_unbound_key(profile, allowed):
    prepared, plan, raw, parts, messages = example(SOURCE,profile=profile)
    key, = parts
    prefix = json.dumps(raw,ensure_ascii=False,separators=(',',':')).split(json.dumps(key,ensure_ascii=False)+':',1)[0]
    prefix += json.dumps(key,ensure_ascii=False)+':"' + ",'e3"
    alphabet=''.join(dict.fromkeys(prefix+SOURCE+"e2/\\u002fF担当者'+@"))
    parser=probe.semantic_json_parser(messages,alphabet)
    state=advance(parser,prefix)
    assert state is not None
    for escape,last in [('', '/'), (r'\u002','f'), ('\\','/')]:
        tail=advance(state,escape)
        assert tail is not None
        assert (last in tail.get_allowed_characters()) == allowed
