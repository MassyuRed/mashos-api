"""A history merge keeps the whole short original action without assigning its meaning."""
from dataclasses import replace
import hashlib
import json

import pytest

import analysis_merge_wire as wire
import analysis_plan_source_choices as choices
import analysis_semantic_map as maps
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_cumulative import OWNER, source_snapshot
from test_analysis_node_local_native_profile import accepts
from test_analysis_occurrence_v17_record_owners import packet


OPENING = '午前、家族から寸法を調べてほしいと言われた。'
OUTCOME = '家族は業者へ問い合わせたと私に知らせた。'
NONACTION = '私は家具を注文しなかった。'
UNCONFIRMED = '図は届いておらず、費用は分からない。'
WISH = '夕方、私は次の店も見たいと思った。'
ACTION = OUTCOME + NONACTION + UNCONFIRMED + WISH
MEMO = OPENING + ''.join(f'{i}枚目の写真に広い机を見つけて、紙の余白へ大きさを控えた。' for i in range(8))


def stage_with_action():
    snap = source_snapshot(1)
    snap['members'][0]['original'].update(memo=MEMO, memo_action=ACTION)
    parent = maps.prepare_semantic_map(OWNER, snap, prompt_version=wire.PROFILE)
    stage = core.prepare_semantic_leaf(parent, (parent.frozen.members[0].saved_record_ref,))
    material = json.loads(stage.material_json)
    material['history_stage']['kind'] = 'MERGE'
    material.update(leaf_source_index=[], field_manifest=[], omitted_ranges=[], leaf_receipts=[])
    for field in material['fields']:
        field['fragment_scalar_range'] = [0, len(field['text'])]
        field['fragment_is_complete_field'] = True
        material['field_manifest'].append({**{k: field.get(k) for k in ('field', 'record', 'source_role', 'field_path', 'supplement')},
            'scalar_length': len(field['text']), 'text_sha256': hashlib.sha256(field['text'].encode()).hexdigest()})
    return replace(stage, kind='MERGE', material_json=core.semantic_map_canonical(material))


def test_keeps_reported_action_nonaction_unconfirmed_and_wish_verbatim():
    stage = stage_with_action()
    material = json.loads(stage.material_json)
    fields = {f['field_path']: f for f in material['fields']}
    memo, act = fields['memo']['field'], fields['memo_action']['field']
    next_memo_sentence = choices.choices_for_field(fields['memo'])[0][1]
    anchors = dict(merge_anchors=True, merge_action_sources=True)
    legal = [[[(memo, OPENING), (memo, next_memo_sentence),
                (act, OUTCOME + NONACTION)], [(act, UNCONFIRMED), (act, WISH)]]]
    admitted = core.admit_semantic_node_local_v4_plan_response(stage, packet(stage,legal), **anchors)
    refs = [q for u in admitted['nodes'][0]['units'] for q in u['evidence']]
    assert ''.join(q['quote'] for q in refs if q['field']==act)==ACTION
    current = core.semantic_node_local_v4_wire_messages(stage)
    codec = wire.response_codec(current)
    assert accepts(codec.encode(packet(stage, legal)), current)
    for missing in range(4):
        retained=[(act,q) for i,q in enumerate((OUTCOME, NONACTION, UNCONFIRMED, WISH)) if i!=missing]
        raw = packet(stage, [[[(memo,OPENING),*retained]]])
        assert core.admit_semantic_node_local_v4_plan_response(stage, raw, merge_anchors=True)
        with pytest.raises(core.AnalysisSemanticMapError, match='action_source_missing'):
            core.admit_semantic_node_local_v4_plan_response(stage, raw, **anchors)
        assert not accepts(codec.encode(raw), current)


@pytest.mark.parametrize('change', ['no_action', 'long_action', 'partial', 'updated', 'supplement', 'correction', 'unchanged_field_digest', 'unowned_omitted', 'leaf'])
def test_does_not_impose_incomplete_superseded_or_unavailable_source(change):
    material = json.loads(stage_with_action().material_json)
    action = next(f for f in material['fields'] if f['field_path']=='memo_action')
    if change=='no_action':
        material['fields'].remove(action)
    elif change=='long_action':
        action['text']=MEMO
        action['fragment_scalar_range']=[0,len(MEMO)]
        item=next(e for e in material['field_manifest'] if e['field']==action['field']); item['text_sha256']=hashlib.sha256(MEMO.encode()).hexdigest()
    elif change=='partial':
        action['fragment_is_complete_field']=False
    elif change=='updated':
        material['emlis_source_materials']=[dict(record=1,source_updates=['later'])]
    elif change=='supplement':
        material['fields'].append({**action,'field':12,'source_role':'SUPPLEMENTAL_ANSWER'})
    elif change=='correction':
        material['fields'].append({**action,'field':13,'record':None,'source_role':'USER_ANALYSIS_MAP_CORRECTION'})
    elif change=='unchanged_field_digest':
        action['text']=action['text'].replace('家具','番地')
    elif change=='unowned_omitted':
        material['field_manifest'].append(dict(field=14,record=None,field_path='map_correction',source_role='USER_ANALYSIS_MAP_CORRECTION'))
    elif change=='leaf':
        material['history_stage']['kind']='LEAF'
    owners=choices.record_plan_owners(material,merge_anchors=True)
    assert choices.merge_action_sources(material,owners)=={}
