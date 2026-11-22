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


def stage_with_action(memo_text=MEMO, action_text=ACTION, leaf_quotes=()):
    snap = source_snapshot(1)
    snap['members'][0]['original'].update(memo=memo_text, memo_action=action_text)
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
        if field['field_path'] == 'memo':
            for quote in leaf_quotes:
                start = field['text'].index(quote)
                material['leaf_source_index'].append(dict(field=field['field'], quote=quote,
                    scalar_range=[start, start + len(quote)]))
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


def test_single_leaf_descriptions_only_use_complete_selected_thought_sentences():
    earlier = '場所の条件を先にメモした。'
    later = '店で試すと、角度を変えれば届くと分かった。'
    action = '試した商品を購入した。'
    fields = [dict(field=1, record=1, source_role='ORIGINAL_INPUT', field_path='memo', text=earlier + later),
              dict(field=2, record=1, source_role='ORIGINAL_INPUT', field_path='memo_action', text=action)]
    material = dict(history_stage=dict(kind='LEAF'), fields=fields)
    assert choices.single_original_leaf(material)
    selected = [dict(evidence=[dict(field=1, quote=later), dict(field=2, quote=action)])]
    sentences = {1: {earlier, later}, 2: {action}}
    assert choices.leaf_meanings(fields, selected, sentences) == ['', later]
    assert not choices.single_original_leaf(dict(material, history_stage=dict(kind='MERGE')))
    for change in (dict(source_role='PERSON_SUPPLEMENT'), dict(fragment_is_complete_field=False), dict(record=2)):
        assert not choices.single_original_leaf(dict(material, fields=[fields[0], dict(fields[1], **change)]))


def test_context_selection_is_source_bound_native_and_saved_v4_replays_unchanged():
    topic = '教室では、講師が組み立てた時計の説明をした。'
    other = 'その日の雲は灰色だった。'
    action = '席に着いて時計の説明を聞いた。'
    stage = stage_with_action(other + topic + MEMO, action)
    messages = core.semantic_node_local_v4_wire_messages(stage)
    old = core.semantic_node_local_v4_wire_messages(stage, wire_version=wire.SOURCE_TITLE_VERSION)
    assert wire.legacy_messages(messages) == wire.legacy_messages(old)
    assert 'memo_context_choices' not in json.loads(old[1]['content'])
    assert json.loads(messages[1]['content'])['memo_context_choices'] == [[1, [topic]]]
    for quote, expected in ((topic, True), (other, False)):
        raw = packet(stage, [[[(1, quote), (2, action)]]])
        assert core.admit_semantic_node_local_v4_plan_response(stage, raw,
            merge_anchors=True, merge_action_sources=True)
        assert accepts(wire.response_codec(old).encode(raw), old)
        assert accepts(wire.response_codec(messages).encode(raw), messages) is expected
        if expected:
            admitted = core.admit_semantic_node_local_v4_plan_response(stage, raw,
                merge_anchors=True, merge_action_sources=True, context_sources=True)
            assert admitted['nodes'][0]['units'][0]['evidence'][0]['quote'] == topic
        else:
            with pytest.raises(core.AnalysisSemanticMapError, match='action_source_missing'):
                core.admit_semantic_node_local_v4_plan_response(stage, raw,
                    merge_anchors=True, merge_action_sources=True, context_sources=True)
    material = json.loads(messages[1]['content'])
    material['memo_context_choices'][0][1] = [other]
    with pytest.raises(ValueError, match='analysis_merge_wire_invalid'):
        wire.legacy_messages([messages[0], dict(messages[1], content=wire.compact_json(material))])


def test_named_context_keeps_subordinate_subject_and_leaves_ambiguous_readings_open():
    action = '係員と荷物を相談し、希望を伝えた。'
    wish = '入口に戻ると、係員は客が休める場所を増やしたいと言った。'
    alternate = '係員は客が席で待てるようにしたいと話した。'
    other_person = '隣人は行列を短くしたいと言った。'
    guess = '係員は客を案内したいと言ったのかもしれない。'
    negated = '係員は受付を閉じたいとは言わなかった。'
    embedded = '同僚は「係員は先へ進みたい」と言った。'
    question = '係員が休みたいと言ったのだろうか。'
    lines = (wish, alternate, other_person, guess, negated, embedded, question)
    stage = stage_with_action(''.join(lines) + MEMO, action)
    m = json.loads(stage.material_json)
    sources = choices.merge_action_sources(m, choices.record_plan_owners(m, merge_anchors=True), context_sources=True)
    selected = sources[1]
    assert selected.memo_choices == (wish, alternate)
    for quote in lines:
        assert bool(selected.coverage(1, quote)) == (quote in (wish, alternate))
    # A long fact can be legally shortened to a source range in NODES. It
    # cannot carry this obligation since the chosen passage might disappear.
    assert not selected.coverage(1, wish + '狭かった。' * 40)


def test_timing_uses_same_recipient_and_action_and_trial_uses_leaf_pair():
    timed = '準備を終えてから車掌へ短い報告を送り、番号を控えた。'
    wrong_recipient = '食事を終えてから駅員へ報告した。'
    wrong_action = '食事を終えてから車掌へ挨拶した。'
    trial = '手元で小さな鍵を試した。押す向きを変えると奥まで入った。'
    unseen = '窓辺で予備の鍵を試した。鍵を回すと扉が開いた。'
    scheduled = '来週にも別の道具を試したい。置く位置を変えると収まるだろう。'
    action = '車掌へ報告した。道具の条件を確認して番号を保管した。'
    stage = stage_with_action(timed + wrong_recipient + wrong_action + trial + unseen + scheduled + MEMO,
                              action, (trial, scheduled))
    m = json.loads(stage.material_json)
    owners = choices.record_plan_owners(m, merge_anchors=True)
    assert choices.merge_action_sources(m, owners, context_sources=True)[1].memo_choices == (timed, trial)
    m['leaf_source_index'] = []
    assert choices.merge_action_sources(m, owners, context_sources=True)[1].memo_choices == (timed,)
    m['emlis_source_materials'] = [dict(record=1, conflicts=['訂正待ち'])]
    assert not choices.merge_action_sources(m, owners, context_sources=True)


def test_context_preserves_reported_words_including_their_conditions():
    said = '私は、日程が変わるなら説明会を二回に分けたいと述べた。'
    report = '打合せで自分の意見を述べた。'
    contact = '当直の職員に電話した。'
    reply = '日曜なら手伝えるとの返事だった。'
    asked = '職員の意向を尋ねて、日曜の集合にした。'

    def selected(action, memo, leaf_quotes=()):
        simple, allowed = choices.choices_for_field(dict(text=memo, source_role='ORIGINAL_INPUT'))
        return choices._reported_content_choices(action, simple, allowed, leaf_quotes)

    assert selected(report, said, (said,)) == {said}
    assert not selected(report, said)
    assert not selected('明日、自分の意見を述べたい。', said, (said,))
    assert selected(asked, contact + reply) == {contact + reply}
    assert not selected(asked, '当直の医師に電話した。' + reply)
    assert not selected(asked, contact + 'その日は出先で応答がなかった。' + reply)
    assert not selected(asked, contact + '日曜に来られるかまでは分からない。')
