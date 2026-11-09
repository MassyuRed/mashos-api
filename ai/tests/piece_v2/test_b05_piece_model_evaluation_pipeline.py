"""Evaluation model prose through existing isolated SQL save/replay owners."""
import pytest

from test_cmee_piece_request_saved_pipeline import saved_piece_db, _run_saved_request
from test_b05_piece_model_saved_pipeline import _provider, _evidence


@pytest.mark.parametrize('tier', ('free', 'plus', 'premium'))
@pytest.mark.parametrize('case_id,memo,body', (
    ('evaluation-focus', '私にとって大切なのは、一人で本を読む時間です。',
     '私にとって、一人で本を読む時間が大切だ。'),
    ('evaluation-past-modal', '僕にとって周りに合わせる時間が必要ではなかったかもしれません。',
     '僕にとって周りに合わせる時間が必要ではなかったかもしれない。'),
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
