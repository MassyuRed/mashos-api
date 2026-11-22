"""Active original ranges reach the semantic author without invented sources.

Synthetic model packets are new to these exact materials, never rebound raw.
"""
import copy
from dataclasses import replace
import hashlib
import json

import pytest
from test_analysis_interpretation_correction_sources import corrected
from test_analysis_saved_period import snapshot, OWNER, NOW, START, END
from emlis_thread_service import _request
import analysis_cumulative_service as cumulative
import analysis_semantic_map as semantic
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as admission
from cocolon_meaning_experience_engine.cores.analysis.source_adapter import freeze_analysis_sources
from test_analysis_semantic_map import response

MEMO = '私は考えをノートに書いた。私は仕事を続けたい。私は資料を読んだ。'
REVISE = '「私は仕事を続けたい」ではなく「私は家族を守りたい」です。'
WITHDRAW = '「私は仕事を続けたい」は取り消します。'


def saved_update(explanation=REVISE, *, memo=MEMO, action='私は日程を決めた。'):
    saved = corrected(explanation)
    saved['original'].update(memo=memo, memo_action=action)
    saved['thread']['source_snapshot'] = copy.deepcopy(saved['original'])
    ref = _request(saved, include_context=False, analysis_source_only=True).emlis_thread.original_source_ref
    saved['events'][-1]['payload']['source']['original_source_ref'] = ref
    return saved


def source_snapshot(saved=None):
    return dict(tier='plus', now=NOW, period_start=START, period_end=END,
        members=[saved_update() if saved is None else saved, snapshot(2)],
        guard='analysis-db-cumulative-v1:'+'a'*64)


def prepare(saved=None, *, profile=admission.SEMANTIC_MAP_SOURCE_DUTIES_PROFILE):
    snap = source_snapshot(saved)
    request = cumulative._cumulative_model_request(OWNER, snap)
    return admission.prepare_analysis_semantic_map(request, snap, prompt_version=profile)


def packet(prepared, field, quote, *, label='家族を守りたい'):
    return dict(schema_version=semantic.MODEL_SCHEMA,
        overview=dict(title='記録に書かれたこと', summary='本人が残した有効な記述を見ています。'),
        nodes=[dict(node_id='n1', node_kind='CHOICE_OUTPUT', title=label,
            summary=label+'と書かれています。', explanation='本人の記録を考える材料にします。',
            perspective='SELF', unknowns=[], evidence=[dict(field=field,quote=quote)])], edges=[])


@pytest.mark.parametrize('profile',[admission.SEMANTIC_MAP_PROFILE,admission.SEMANTIC_MAP_SOURCE_DUTIES_PROFILE])
@pytest.mark.parametrize('explanation',[REVISE,WITHDRAW])
def test_active_ranges_keep_both_fields_and_unrelated_records_without_old_claim(profile,explanation):
    saved = saved_update(explanation)
    before = copy.deepcopy(saved)
    prepared = prepare(saved, profile=profile)
    material = json.loads(prepared.material_json)
    assert len(prepared.request.members) == 2
    assert json.loads(prepared.exclusion_reasons_json) == {}
    first = [f for f in material['fields'] if f['record']==1]
    texts = [f['text'] for f in first]
    assert texts[:3] == ['私は考えをノートに書いた。','私は資料を読んだ。','私は日程を決めた。']
    assert all('私は仕事を続けたい' not in text for text in texts)
    assert len(first) == (4 if explanation==REVISE else 3)
    if explanation==REVISE:
        assert first[-1]['text'] == '私は家族を守りたい'
        assert first[-1]['source_role'] == 'USER_INTERPRETATION_CORRECTION'
        assert first[-1]['source_recorded_at'] == NOW
    assert prepared.frozen == freeze_analysis_sources(prepared.request)
    assert saved == before
    for _,text,_,base in prepared.fields:
        source = next(s for s in prepared.frozen.sources if s.envelope.envelope_id==base.source_envelope_id)
        raw = source.envelope.raw_utf8
        assert raw[base.utf8_start:base.utf8_end].decode()==text
        field = raw[base.field_utf8_start:base.field_utf8_end].decode()
        assert field[base.scalar_start:base.scalar_end]==text
        assert base.field_sha256==hashlib.sha256(field.encode()).hexdigest()


def test_replacement_evidence_and_source_duties_use_absolute_original_utf8_offsets():
    prepared = prepare()
    material = json.loads(prepared.material_json)
    field = next(f for f in material['fields'] if f['text']=='私は家族を守りたい')
    artifact, coverage = semantic.build_semantic_map(prepared,response(prepared,
        packet(prepared,field['field'],'私は家族を守りたい')))
    assert artifact and coverage['mapped_count']==1 and coverage['processed_count']==2
    private = artifact.private_evidence()
    roots = private['graph']['nodes'][0]['evidence_refs']
    root = next(r for r in roots if r['literal_sha256']==hashlib.sha256('私は家族を守りたい'.encode()).hexdigest())
    raw = next(s.envelope.raw_utf8 for s in prepared.frozen.sources
        if s.envelope.envelope_id==root['source_envelope_id'])
    assert raw[root['utf8_start']:root['utf8_end']].decode()=='私は家族を守りたい'
    original = raw[root['field_utf8_start']:root['field_utf8_end']].decode()
    assert root['scalar_start']==REVISE.index('私は家族を守りたい')>0
    assert original[root['scalar_start']:root['scalar_end']]=='私は家族を守りたい'
    for claim in json.loads(prepared.source_duties_json)['claims']:
        root = __import__('cocolon_meaning_experience_engine.cores.analysis.intent_compiler',fromlist=['_semantic_map_duty_root'])._semantic_map_duty_root(prepared,claim)
        raw = next(s.envelope.raw_utf8 for s in prepared.frozen.sources if s.envelope.envelope_id==root['source_envelope_id'])
        assert raw[root['utf8_start']:root['utf8_end']].decode()==claim['quote']


@pytest.mark.parametrize('quote',['私は仕事を続けたい','私は考えをノートに書いた。私は資料を読んだ。','AI_TARGET_NOT_USER_EVIDENCE'])
def test_removed_cross_fragment_and_ai_target_quotes_are_rejected(quote):
    prepared = prepare()
    with pytest.raises(semantic.SemanticMapError,match='analysis_semantic_evidence_unbound'):
        semantic.build_semantic_map(prepared,response(prepared,packet(prepared,1,quote)))


def test_equal_surviving_ranges_get_separate_field_identities_and_duties():
    saved = saved_update(WITHDRAW,memo='私は考えをノートに書いた。私は仕事を続けたい。私は考えをノートに書いた。',action='')
    prepared = prepare(saved)
    fields = [f for f in prepared.fields if f[2]==saved['original']['id']]
    assert len(fields)==2 and fields[0][1]==fields[1][1]=='私は考えをノートに書いた。'
    assert fields[0][3].source_span_id!=fields[1][3].source_span_id
    duties=json.loads(prepared.source_duties_json)
    assert {c['field'] for c in duties['claims'] if c['record']==1}=={fields[0][0],fields[1][0]}


def test_unknown_explanation_still_pending_without_resurrecting_original():
    prepared = prepare(saved_update('今はまだ決められません。'))
    assert len(prepared.request.members)==1
    assert json.loads(prepared.exclusion_reasons_json)=={'analysis_interpretation_correction_pending':1}


def test_withdrawal_only_material_also_warns_against_joining_separate_ranges():
    prepared=prepare(saved_update(WITHDRAW))
    assert prepared.active_source_updates
    assert '離れた有効部分' in prepared.messages()[0]['content']


def test_entirely_withdrawn_record_has_no_model_field_but_other_record_survives():
    prepared=prepare(saved_update(WITHDRAW,memo='私は仕事を続けたい。',action=''))
    assert len(prepared.request.members)==1
    assert json.loads(prepared.exclusion_reasons_json)=={'analysis_semantic_text_empty':1}
    assert all(f[2]==snapshot(2)['original']['id'] for f in prepared.fields)
