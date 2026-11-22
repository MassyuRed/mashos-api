"""Multiple independent user supplements, corrections and their source roots."""
from dataclasses import replace

import pytest

from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.cores.analysis.source_adapter import AnalysisSupplement, commitment, freeze_analysis_sources
from test_cmee_analysis_v1d_vertical import OWNER, record, request


def answered(original, *texts):
    return replace(original, supplements=tuple(AnalysisSupplement('answer-'+str(i), OWNER,
        original.saved_record_ref, original.saved_record_version, text, commitment(text))
        for i, text in enumerate(texts)))


@pytest.mark.parametrize('texts', [
    ('私は資料を調べた。', '私は仕事を続けたい。'),
    ('私は資料を調べた。', '私は仕事を続けたい。', '私は記録を残した。'),
])
def test_independent_answers_keep_every_source_and_visible_claim(texts):
    original=record(memo='私は考えをノートに書いた。')
    value=request(answered(original,*texts))
    result=MeaningExperienceEngine().generate(value)
    assert result.status == EngineStatus.GENERATED, result.reason_codes
    assert len(freeze_analysis_sources(value).sources)==len(texts)+1
    labels=[n.visible_label for n in result.artifact.graph.nodes]
    for text in texts: assert text.rstrip('。') in labels
    assert '私は考えをノートに書いた' in labels
    result.artifact.safe_projection(authenticated_owner_scope=OWNER)


@pytest.mark.parametrize('texts', [
    ('私は仕事を続けたい。','私は仕事を続けたくない。'),
    ('「私は資料を見た」ではなく「私は資料を調べた」です。',
     '「私は資料を見た」ではなく「私は記録を残した」です。'),
    ('私は仕事を続けたい。','「私は仕事を続けたい」ではなく「私は資料を調べた」です。'),
])
def test_unresolved_opposition_or_ambiguous_correction_never_becomes_current_map(texts):
    result=MeaningExperienceEngine().generate(request(answered(record(memo='私は資料を見た。'),*texts)))
    assert result.artifact is None
    assert result.status != EngineStatus.GENERATED


def test_correction_then_independent_answer_preserves_updated_original_and_all_roots():
    original=record(memo='私は資料を見た。')
    value=request(answered(original,'「私は資料を見た」ではなく「私は資料を調べた」です。','私は仕事を続けたい。'))
    result=MeaningExperienceEngine().generate(value)
    assert result.status == EngineStatus.GENERATED, result.reason_codes
    labels=[n.visible_label for n in result.artifact.graph.nodes]
    assert '私は資料を見た' not in labels
    assert '私は資料を調べた' in labels and '私は仕事を続けたい' in labels
    assert len(freeze_analysis_sources(value).sources)==3


def test_later_answer_cannot_contradict_the_replacement_claim():
    value=request(answered(record(memo='私は仕事を続けたい。'),
        '「私は仕事を続けたい」ではなく「私は仕事を続けたくない」です。','私は仕事を続けたい。'))
    assert MeaningExperienceEngine().generate(value).artifact is None


def test_later_replacement_cannot_contradict_an_earlier_answer():
    value=request(answered(record(memo='私は資料を見た。'),
        '私は仕事を続けたい。','「私は資料を見た」ではなく「私は仕事を続けたくない」です。'))
    assert MeaningExperienceEngine().generate(value).artifact is None


def test_replacements_of_different_original_clauses_cannot_silently_conflict():
    value=request(answered(record(memo='私は資料を見た。私は記録を残した。'),
        '「私は資料を見た」ではなく「私は仕事を続けたい」です。',
        '「私は記録を残した」ではなく「私は仕事を続けたくない」です。'))
    assert MeaningExperienceEngine().generate(value).artifact is None


def test_repeated_source_identity_and_above_three_answers_remain_invalid():
    original=record(memo='私は資料を見た。')
    two=answered(original,'私は記録を残した。','私は仕事を続けたい。')
    duplicate=replace(two,supplements=(two.supplements[0],replace(two.supplements[1],source_id=two.supplements[0].source_id)))
    assert MeaningExperienceEngine().generate(request(duplicate)).artifact is None
    assert MeaningExperienceEngine().generate(request(answered(original,*(['私は記録を残した。']*4)))).artifact is None
