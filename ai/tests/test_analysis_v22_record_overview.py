from analysis_plan_source_choices import selected_record_overview


def fixture(rows):
    records = []
    fields = []
    nodes = []
    fixed = {}
    for i, (timestamp, actor_text) in enumerate(rows, 1):
        records.append(dict(record=i, recorded_at=timestamp))
        fields.append(dict(field=i, record=i, field_path='memo_action', text=actor_text,
                           source_role='ORIGINAL_INPUT'))
        nodes.append(dict(units=[dict(evidence=[dict(field=i, quote=actor_text)])]))
        fixed[f'n{i}.u1'] = [actor_text]
    return dict(records=records, fields=fields), nodes, fixed


def test_distinct_owners_and_repeated_labels_on_the_same_minute():
    cases = [('2026-01-01T08:00:00', text) for text in
             ['会場に連絡した。', '会場に連絡した。', '私は家で休んだ。', '友人は家で休んだ。']]
    m, n, f = fixture(cases)
    lines = selected_record_overview(m,n,f,'4件の記録を振り返って').splitlines()
    assert len(lines)==4 and lines[0]!=lines[1]
    assert lines[0].endswith('会場に連絡した。') and lines[1].endswith('会場に連絡した。')
    assert '本人' not in ''.join(lines) and lines[2:] == ['私は家で休んだ。', '友人は家で休んだ。']


def test_record_dates_keep_year_and_subject_and_do_not_publish_fragments():
    m,n,f = fixture([('2025-01-01T08:00:00','兄が「店へ行かなかった」と言った。'),
                     ('2026-01-01T08:00:00','私が店へ行った。')])
    heading = '2件の記録を振り返って'
    assert selected_record_overview(m,n,f,heading).splitlines() == [
        '2025/1/1 兄が「店へ行かなかった」と言った。','2026/1/1 私が店へ行った。']
    assert selected_record_overview(m,n,f,'家族に連絡した二日間') == ''
    m['fields'][1]['fragment_is_complete_field'] = False
    assert selected_record_overview(m,n,f,heading) == ''
    del m['fields'][1]['fragment_is_complete_field']
    f['n2.u1'] = ['店へ行った']
    assert selected_record_overview(m,n,f,heading) == ''


def test_repeated_identical_field_sentence_is_not_assigned_to_an_occurrence():
    m,n,f = fixture([('2026-02-01T08:00:00','手伝った。手伝った。'),
                     ('2026-02-02T08:00:00','手伝うかは決めていない。')])
    assert selected_record_overview(m,n,f,'2件の記録を振り返って') == ''
