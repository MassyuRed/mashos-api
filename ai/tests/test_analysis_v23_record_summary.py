import pytest

from analysis_plan_source_choices import repeated_record_node_dates, selected_record_overview
from test_analysis_v22_record_overview import fixture


def test_authored_heading_keeps_both_original_actions_in_time_order():
    material,nodes,facts=fixture([
        ('2026-07-02T10:00:00','妹は連絡を待つと答えた。'),
        ('2026-07-01T10:00:00','私は面談を申し込んだ。')])
    heading='面談を申し込んだ日と連絡を待つ妹'
    assert selected_record_overview(material,nodes,facts,heading)==''
    assert selected_record_overview(material,nodes,facts,heading,include_authored_titles=True).splitlines()==[
        '7/1 私は面談を申し込んだ。','7/2 妹は連絡を待つと答えた。']
    material['fields'][1]['fragment_is_complete_field']=False
    assert selected_record_overview(material,nodes,facts,heading,include_authored_titles=True)==''


def test_duplicate_names_and_same_clock_keep_disjoint_record_labels():
    material,nodes,facts=fixture([('2026-02-02T10:30:00','名簿を開いた。')]*2)
    lines=selected_record_overview(material,nodes,facts,'同じ時刻に開いた二つの名簿',include_authored_titles=True).splitlines()
    assert len(lines)==2 and lines[0]!=lines[1] and all(line.endswith('名簿を開いた。') for line in lines)
    assert repeated_record_node_dates(material,nodes)=={}
    mixed={'units':nodes[0]['units']+nodes[1]['units']}
    material['fields'].append(dict(field=3,record=1,source_role='SUPPLEMENT'))
    extra={'units':[{'evidence':[{'field':1},{'field':3}]}]}
    bound=repeated_record_node_dates(material,[nodes[0],nodes[1],nodes[0],mixed,extra])
    assert set(bound)=={0,1,2} and bound[0]==bound[2] and bound[0]!=bound[1]
    assert set(repeated_record_node_dates(material,[nodes[0],mixed,nodes[0],extra]))=={0,2}


@pytest.fixture
def merged_corrections():
    quote = '私は不安だった。'
    stamp = '2026-11-24T00:12:00Z'
    material = {
        'history_stage': {'kind': 'MERGE'},
        'records': [{'record': i, 'recorded_at': stamp} for i in range(1, 5)],
        'fields': [{'field': i, 'record': i, 'source_role': 'USER_INTERPRETATION_CORRECTION',
                    'field_path': 'memo', 'source_recorded_at': stamp, 'text': quote,
                    'fragment_is_complete_field': True} for i in range(1, 5)],
    }
    nodes = [{'meaning': '', 'units': [{'evidence': [{'field': i, 'quote': quote}]} for i in group]}
             for group in ((1, 2), (3, 4))]
    return material, nodes


def test_history_merge_dates_each_complete_correction_by_its_own_record(merged_corrections):
    material, nodes = merged_corrections
    assert repeated_record_node_dates(material, nodes, include_corrections=True) == {
        0: '記録1（11月24日 09:12）・記録2（11月24日 09:12）への訂正',
        1: '記録3（11月24日 09:12）・記録4（11月24日 09:12）への訂正',
    }
    assert repeated_record_node_dates(material, nodes) == {}


@pytest.mark.parametrize('change', ['fragment', 'mixed_source', 'shared_record', 'meaning', 'quote'])
def test_history_merge_cannot_date_unverified_or_authored_repetition(merged_corrections, change):
    material, nodes = merged_corrections
    field = material['fields'][-1]
    if change == 'fragment':
        field['fragment_is_complete_field'] = False
    elif change == 'mixed_source':
        field['source_role'] = 'ORIGINAL_INPUT'
    elif change == 'shared_record':
        field['record'] = 2
    elif change == 'meaning':
        nodes[1]['meaning'] = 'そう感じた理由がある。'
    else:
        nodes[1]['units'][1]['evidence'][0]['quote'] = '不安だった'
    assert repeated_record_node_dates(material, nodes, include_corrections=True) == {}
