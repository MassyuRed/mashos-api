"""The private reference contract preserves source and prior parser isolation."""
from copy import deepcopy
import json
import pytest
from test_emlis_natural_reply_probe_http import probe


def plan():
    return dict(schema_version=probe.EVENT_PLAN_SCHEMA, events=[
        dict(evidence=[dict(quote='私は便を予約しなかった。',field=1)],event_id='e1',
             fact='本人は便を予約しませんでした。',unknowns=[]),
        dict(evidence=[dict(quote='翌日、私は窓口で便を予約した。',field=2)],event_id='e2',
             fact='翌日、本人は窓口で便を予約しました。',unknowns=[])],
        readings=[dict(reading_id='r1',event_refs=['e1','e2'],meaning='予約の状態が前後で変わっています。')],
        nodes=[dict(node_id='n1',node_kind='CHOICE_OUTPUT',perspective='SELF',title='予約の前後',
                    event_refs=['e1','e2'],reading_refs=['r1'])],edges=[],
        overview=dict(title='予約の前後',event_refs=['e1','e2'],reading_refs=['r1']))


def messages():
    return [dict(role='system',content='synthetic'), dict(role='user',content=json.dumps(dict(
        model_schema=probe.EVENT_PLAN_SCHEMA,fields=[dict(field=1,record=1,text='私は便を予約しなかった。'),
        dict(field=2,record=2,text='翌日、私は窓口で便を予約した。')]),ensure_ascii=False))]


def accepts(packet, *, escaped=False):
    pytest.importorskip('lmformatenforcer')
    raw=json.dumps(packet,ensure_ascii=escaped,separators=(',',':'))
    alphabet=''.join(dict.fromkeys(raw+json.dumps(plan(),ensure_ascii=False)+'P '))
    parser=probe.semantic_json_parser(messages(),alphabet)
    try:
        for char in raw:
            if char not in parser.get_allowed_characters():
                return False
            parser=parser.add_character(char)
        return parser.can_end()
    except ValueError:
        return False


def test_reference_plan_decoder_accepts_bound_earlier_and_later_events():
    assert accepts(plan())


@pytest.mark.parametrize('mutation', ['forward_event','forward_reading','duplicate_id',
    'missing_record','changed_quote','wrong_field','missing_event','self_edge'])
def test_reference_plan_decoder_rejects_unbound_selection(mutation):
    p=plan()
    if mutation=='forward_event': p['readings'][0]['event_refs']=['e3']
    elif mutation=='forward_reading': p['nodes'][0]['reading_refs']=['r2']
    elif mutation=='duplicate_id': p['events'][1]['event_id']='e1'
    elif mutation=='missing_record': p['events']=p['events'][:1]
    elif mutation=='changed_quote': p['events'][0]['evidence'][0]['quote']='私は便を予約した。'
    elif mutation=='wrong_field': p['events'][0]['evidence'][0]['field']=2
    elif mutation=='missing_event': p['nodes'][0]['event_refs']=['e3']
    elif mutation=='self_edge': p['edges']=[dict(**{'from':'n1','to':'n1'},
        relation_kind='CONTEXT_CONTRAST',label='比較',event_refs=['e1'],reading_refs=[])]
    assert not accepts(p)


def test_private_schema_leaves_legacy_and_if_schema_selection_unchanged():
    m=messages(); original=deepcopy(m); material=json.loads(m[1]['content'])
    del material['model_schema'];m[1]['content']=json.dumps(material,ensure_ascii=False)
    before=probe.semantic_output_schema(m)
    assert probe.semantic_output_schema(original)['properties']['schema_version']['enum']==[probe.EVENT_PLAN_SCHEMA]
    assert probe.semantic_output_schema(m)==before
    assert before['properties']['schema_version']['enum']==['cocolon.analysis.semantic_map.model.v2']
