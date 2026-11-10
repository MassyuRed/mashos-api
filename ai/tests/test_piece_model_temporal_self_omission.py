"""Same-author ellipsis inside an anchored time-scoped model evaluation."""
import pytest

from test_cmee_piece_finite_request_reuse import source
from test_piece_model_narrator_voice import SPEAKERS, evaluate


def original(speaker='私'):
    return f'以前は、{speaker}は一人の食事が苦手でした。今は、{speaker}は一人の食事が好きです。'


@pytest.mark.parametrize('speaker', SPEAKERS)
def test_bound_adjacent_narrator_may_be_omitted_after_exact_time_prefix(speaker):
    body = f'以前は、{speaker}は一人の食事が苦手だった。今は、一人の食事が好きだ。'
    out = evaluate(source(original(speaker), field='memo'), [body])
    assert out.artifact is not None, out.reason_codes
    assert out.artifact.body_blocks == (body,)


@pytest.mark.parametrize('body', [
    '以前は、一人の食事が苦手だった。今は、一人の食事が好きだ。',
    '以前は、私は一人の食事が苦手だった。一人の食事が好きだ。',
    '今は、私は一人の食事が苦手だった。以前は、一人の食事が好きだ。',
    '以前は、私は一人の食事が苦手だ。今は、一人の食事が好きだ。',
    '以前は、私は一人の食事が苦手だった。今は、一人の食事が好きだった。',
    '以前は、私は一人の食事が苦手だった。今は、一人の食事が好きではない。',
    '以前は、私は一人の食事が苦手だった。今は、一人の食事が好きかもしれない。',
    '以前は、私は一人の食事が苦手だった。今は、食事が好きだ。',
    '以前は、私は一人の食事が苦手だった。今は、僕は一人の食事が好きだ。',
    '今は、一人の食事が好きだ。以前は、私は一人の食事が苦手だった。',
    '以前は、私は一人の食事が苦手だった。今は、一人の食事が好きだ。だから安心した。',
])
def test_ellipsis_does_not_drop_or_change_time_narrator_target_or_evaluation(body):
    assert evaluate(source(original(), field='memo'), [body]).artifact is None


@pytest.mark.parametrize('speaker', [s for s in SPEAKERS if s != '私'])
def test_different_written_narrators_cannot_be_unified_by_ellipsis(speaker):
    saved = source(f'以前は、私は一人の食事が苦手でした。今は、{speaker}は一人の食事が好きです。', field='memo')
    assert evaluate(saved, [f'以前は、私は一人の食事が苦手だった。今は、{speaker}は一人の食事が好きだ。']).artifact
    assert evaluate(saved, ['以前は、私は一人の食事が苦手だった。今は、一人の食事が好きだ。']).artifact is None


@pytest.mark.parametrize('gap', ['昨日は雨が降った。', '友人が戻ってきた。'])
def test_intervening_context_cannot_supply_a_continuing_author(gap):
    saved = source(original().replace('。今', '。' + gap + '今'), field='memo')
    body = '以前は、私は一人の食事が苦手だった。' + gap + '今は、一人の食事が好きだ。'
    assert evaluate(saved, [body]).artifact is None


@pytest.mark.parametrize('gap', ['\n', '\r\n', '\n\n'])
def test_written_paragraph_boundary_cannot_supply_the_narrator(gap):
    saved = source(original().replace('。今', '。' + gap + '今'), field='memo')
    assert evaluate(saved, ['以前は、私は一人の食事が苦手だった。',
                           '今は、一人の食事が好きだ。']).artifact is None


def test_fields_do_not_supply_each_others_temporal_narrator():
    saved = source('以前は、私は一人の食事が苦手でした。', field='memo',
                   other='今は、私は一人の食事が好きです。')
    assert evaluate(saved, ['以前は、私は一人の食事が苦手だった。',
                           '今は、一人の食事が好きだ。']).artifact is None


def test_explicit_value_viewpoint_remains_required():
    saved = source('以前は、私にとって一人の食事が大切でした。今は、私にとって一人の食事が必要です。', field='memo')
    assert evaluate(saved, ['以前は、私にとって一人の食事が大切だった。今は、一人の食事が必要だ。']).artifact is None
