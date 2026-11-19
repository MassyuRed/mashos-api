"""An authored multirecord title must be composed of complete grounded propositions."""
import pytest

import analysis_plan_source_choices as source
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_node_local_native_profile import accepts
from test_analysis_v16_source_title_endings import prepare
from test_analysis_v18_overview_source_coverage import relation


def original_material(notes):
    fields = [dict(field=i, record=i, text=q, field_path='memo_action', source_role='ORIGINAL_INPUT')
              for i, q in enumerate(notes, 1)]
    return (dict(fields=fields, records=[dict(record=i, recorded_at=f'2026-01-{i:02}T09:00:00Z')
                                         for i in range(1, len(notes) + 1)]),
            [dict(units=[dict(evidence=[dict(field=i, quote=q)])]) for i, q in enumerate(notes, 1)])


def admissible(notes, proposal):
    return source._source_composed_title(proposal, *original_material(notes))


@pytest.mark.parametrize('positive,negative', [
    ('工房の鍵を預けた日と、郵便局で封筒を開けた日', '工房で封筒を開けた日と、郵便局の鍵'),
    ('預けた工房の鍵と、郵便局で開けた封筒', '預けた工房の鍵と、弟が郵便局で開けた封筒'),
    ('工房の鍵を預けた。郵便局で封筒を開けた。', '工房の鍵を預けた。郵便局で封筒を開けなかった。'),
    ('工房の鍵を預けた日から郵便局で封筒を開けた日まで', '郵便局で封筒を開けた日から工房の鍵を預けた日まで'),
    ('工房の鍵を預けた日と、郵便局で開けた封筒', '工房の鍵を預けた日と、工房からの郵便局への封筒の転送'),
    ('工房の鍵を預けた日と、郵便局で開けた封筒', '工房の鍵を預けた日と、郵便局での開会まで'),
])
def test_every_character_has_one_grounded_argument_and_predicate(positive, negative):
    notes = ('工房の鍵を預けた。', '郵便局で封筒を開けた。')
    assert admissible(notes, positive)
    assert not admissible(notes, negative)


def test_report_and_question_keep_their_original_scope():
    lost = '港から列車が止まったと通知が届いた。'
    question = '受付番号を確認した？'
    assert admissible((lost, question), lost + question)
    assert not admissible((lost, question), lost + '受付番号を確認した。')
    assert not admissible((lost, question), '列車が止まった。' + question)
    reported = '職員は「受付番号を確認した？」と言った。'
    tentative = '受付番号を確認したかは聞いていない。'
    assert not admissible((lost, reported), lost + '受付番号を確認した。')
    assert not admissible((lost, tentative), lost + '受付番号を確認した。')


def test_source_preserving_paraphrases_and_compound_actions_keep_participants():
    notes = ('倉庫に空箱を預けた。', '支所から設備の点検が終わったと通知が来た。')
    assert admissible(notes, '倉庫に預けた空箱と、支所から通知を受けた設備の点検')
    assert not admissible(notes, '倉庫に預けた空箱と、本所から通知を受けた設備の点検')
    actions = ('図面を保存し、担当者へ寸法を伝えた。', '作業日誌を確認した。')
    assert admissible(actions, '図面の保存から作業日誌の確認まで')
    assert not admissible(actions, '図面の保存から作業日誌の取消まで')
    assert not admissible(actions, '図面を保存した日と、担当者が作業日誌を確認した日')


def test_only_complete_selected_source_sentences_count_even_in_history():
    first, extra, second = '港へ地図を送った。', '海岸を測った。', '山道を記録した。'
    material, nodes = original_material((first + extra, second))
    material['fields'][0]['fragment_is_complete_field'] = False
    nodes[0]['units'][0]['evidence'][0]['quote'] = first
    assert source._source_composed_title(first + second, material, nodes)
    assert not source._source_composed_title(extra + second, material, nodes)
    material['fields'][0]['source_role'] = 'SUPPLEMENTAL_ANSWER'
    assert not source._source_composed_title(first + second, material, nodes)


@pytest.mark.parametrize('proposal,expected', [
    ('製本室に預けた荷札と、支所から通知を受けた設備の点検', True),
    ('製本室に荷札を預けた。支所から設備の点検が終わったと通知が来た。', True),
    ('製本室で点検した荷札と、支所から届いた通知', False),
    ('製本室に預けた荷札と、支所での設備の検査開始', False),
    ('製本室に預けた荷札と、支所から設備の点検が終わっていないと通知が来た。', False),
])
def test_native_and_admission_share_the_proof_and_older_saved_decisions(proposal, expected):
    notes = ('製本室に荷札を預けた。', '支所から設備の点検が終わったと通知が来た。')
    for version in (core.SEMANTIC_MAP_OCCURRENCE_V22_PROFILE, core.SEMANTIC_MAP_OCCURRENCE_V23_PROFILE):
        p, plan, nodes = prepare(notes, version)
        packet, messages = relation(p, plan, nodes, ['n1', 'n2'], proposal)
        packet['overview'] = dict(node_refs=['n1', 'n2'], title_proposal=proposal, title=proposal)
        valid = version == core.SEMANTIC_MAP_OCCURRENCE_V22_PROFILE or expected
        assert accepts(packet, messages) is valid
        if valid:
            assert core.semantic_node_local_v4_relations(p, plan, nodes, packet)['overview']['title'] == proposal
        else:
            with pytest.raises(core.AnalysisSemanticMapError, match='overview_title_unbound'):
                core.semantic_node_local_v4_relations(p, plan, nodes, packet)
        packet['overview']['title'] = '2件の記録を振り返って'
        assert accepts(packet, messages)
        assert core.semantic_node_local_v4_relations(p, plan, nodes, packet)['overview']['title'] == packet['overview']['title']
