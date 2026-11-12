"""Evaluation model prose through existing isolated SQL save/replay owners."""
import pytest

from test_cmee_piece_request_saved_pipeline import saved_piece_db, _run_saved_request
from test_b05_piece_model_saved_pipeline import _provider, _evidence


@pytest.mark.parametrize('tier', ('free', 'plus', 'premium'))
@pytest.mark.parametrize('case_id,memo,body', (
    ('focus-reason', '雨が続いているので、私が好きなのは、読書の時間です。',
     '雨が続いているので、私が好きなのは、読書の時間だ。'),
    ('focus-value-condition', '余裕があるなら、僕にとって大切なのは、一人で本を読む時間です。',
     '余裕があるなら、僕にとって大切なのは、一人で本を読む時間だ。'),
    ('focus-past-concession', '予定は決まっているけれど、わたしが少し苦手だったのは、朝食の時間です。',
     '予定は決まっているけれど、わたしが少し苦手だったのは、朝食の時間だ。'),
))
def test_source_focal_evaluation_register_survives_save_and_non_generated_reread(
        saved_piece_db, monkeypatch, tier, case_id, memo, body):
    from contextlib import ExitStack
    from unittest.mock import patch
    seen = _provider(monkeypatch, case_id, [body])
    record = dict(id=case_id,
        created_at=saved_piece_db.query('SELECT now()::text AS stamp')['rows'][0]['stamp'],
        memo=memo, memo_action='', category=['生活'], emotions=['平穏'],
        emotion_details=[dict(type='平穏', strength='weak')])
    with ExitStack() as stack:
        for owner in ('piece_v1c.realize_piece_artifact', 'piece_v1c._publicize_source_sentence',
                      'piece_v1c._evaluation_sentence', 'piece_refined.realize_refined_piece_artifact'):
            stack.enter_context(patch('cocolon_meaning_experience_engine.' + owner,
                                     side_effect=AssertionError('old author forbidden')))
        result = _run_saved_request(saved_piece_db, monkeypatch, record, tier=tier)
    assert result['detail']['piece_text'] == body
    assert result['source_unchanged'] and result['emlis_unchanged']
    assert result['quota_consumptions'] == 1
    _evidence(case_id + '-' + tier, result, seen)


@pytest.mark.parametrize('tier', ('free', 'plus', 'premium'))
@pytest.mark.parametrize('case_id,memo,body', (
    ('evaluation-focus', '私にとって大切なのは、一人で本を読む時間です。',
     '私にとって、一人で本を読む時間が大切だ。'),
    ('evaluation-past-modal', '僕にとって周りに合わせる時間が必要ではなかったかもしれません。',
     '僕にとって周りに合わせる時間が必要ではなかったかもしれない。'),
    ('action-evaluation-self-omission', '私は友人に予定を相談しました。私は読書が好きです。',
     '私は友人に予定を相談した。読書が好きだ。'),
))
def test_evaluation_receipt_stays_fixed_through_save_retry_and_new_owner_read(
        saved_piece_db, monkeypatch, tier, case_id, memo, body):
    seen = _provider(monkeypatch, case_id, [body])
    record = dict(id=case_id, created_at=saved_piece_db.query('SELECT now()::text AS stamp')['rows'][0]['stamp'],
        memo=memo, memo_action=None, category=['生活', '価値観'], emotions=['自己理解'],
        emotion_details=[dict(type='自己理解', strength='medium')])
    value = _run_saved_request(saved_piece_db, monkeypatch, record, tier=tier)
    assert value['detail']['piece_text'] == body != memo
    assert value['quota_consumptions'] == 1 and value['source_unchanged'] and value['emlis_unchanged']
    _evidence(case_id + '-' + tier, value, seen)


@pytest.mark.parametrize('tier', ('free', 'plus', 'premium'))
def test_original_focal_surface_can_be_saved_without_forcing_the_old_author_word_order(
        saved_piece_db, monkeypatch, tier):
    body='私が選びたいのは、版画です。'
    seen=_provider(monkeypatch,'focal-source-surface',[body])
    record=dict(id='focal-source-surface',
        created_at=saved_piece_db.query('SELECT now()::text AS stamp')['rows'][0]['stamp'],
        memo=body,memo_action=None,category=['趣味','価値観'],emotions=['自己理解'],
        emotion_details=[dict(type='自己理解',strength='medium')])
    value=_run_saved_request(saved_piece_db,monkeypatch,record,tier=tier)
    assert value['detail']['piece_text']==body
    assert value['quota_consumptions']==1 and value['source_unchanged'] and value['emlis_unchanged']
    _evidence('focal-source-surface-'+tier,value,seen)
