"""An actual saved Emlis ADD leaves the original eligible for explicit Piece use."""

from hashlib import sha256
import json
import pytest

from cocolon_meaning_experience_engine.piece_semantic_admission import (
    PieceModelInputV1, prepare_piece_model_request, receive_piece_model_candidate,
)
from cocolon_meaning_experience_engine.piece_v1c import PieceGenerationRequest
from piece_v2_source_adapter import (eligible_deep_insight_history_source, piece_deep_insight_handoff_from_binding,
                                     project_saved_deep_insight_source)
from piece_v2_generation import generate_piece_candidate
from test_b05_deep_insight_lifecycle import (
    corrected_db, effective_fence_db, mixed_fence_db, natural_refined_db, piece_db,
    recovered_natural_db, refined_pipeline_db, revised_frame_db, saved_piece_db,
)
from test_b05_natural_refined_saved_pipeline import _prepare_natural
from test_b05_effective_round_sql_fence import _apply
from test_piece_deep_insight_http_lifecycle import linked_db
from test_piece_deep_insight_source_binding import read, value


ANSWER = '私は、自分の気持ちを大切にしたい。'


@pytest.fixture(scope='module')
def preserved_original_db(linked_db):
    _apply(linked_db, '20261128072900_piece_deep_insight_preserved_original.sql')
    return linked_db


@pytest.mark.parametrize('emlis_answer,eligible', [
    ('私は安心しました。', True),
    ('その時は重かった。', False),
])
def test_current_emlis_add_requires_the_original_to_be_independently_active(
        preserved_original_db, monkeypatch, emlis_answer, eligible):
    db = preserved_original_db
    state, _, _ = _prepare_natural(db, monkeypatch, case_id='deep-insight-original-after-certified-add',
        first_answer=emlis_answer)
    owner, source = state['owner'], state['source_id']
    original = state['original']['memo']
    context = value(db, 'select public.deep_insight_candidate_context($1) as v', owner)
    day = value(db, 'select public.deep_insight_state($1) as v', owner)['day']
    record, = [row for row in context['material']['records'] if row['id'] == source]
    receipt = dict(policy_version='deep-insight.v2', lane='records', focus='CONDITION',
        source_id=source, source_version=record['source_version'], field='thought',
        start=0, end=len(original), literal_sha256=sha256(original.encode()).hexdigest(),
        condition_key='d' * 64, target_key='a' * 64)
    issued = value(db, "select public.deep_insight_issue_grounded($1,$2,'records',null,$3,$4,$5,$6,$7) as v",
        owner, day, '褒められた直後に、受け止め方が変わるのはどんなときですか？',
        'deep-insight-target-' + receipt['target_key'], 'deep-insight-current-original',
        context['guard'], json.dumps(receipt))
    assert issued['status'] == 'issued'
    question = issued['question']['id']
    saved = value(db, 'select public.deep_insight_answer($1,$2,$3) as v', owner, question, ANSWER)
    assert saved['inserted']

    def links():
        return value(db, 'select public.deep_insight_piece_history_links($1,ARRAY[$2::uuid]) as v', owner, question)

    selected = read(db, owner, source, question)
    if not eligible:
        assert selected is None and links() == {}
        return
    assert selected is not None
    assert links()[question] == selected['original']
    assert eligible_deep_insight_history_source(owner, question, ANSWER, selected['answered_at'],
        links()[question]) == source
    handoff = piece_deep_insight_handoff_from_binding(owner, source, question, selected)
    projected = project_saved_deep_insight_source(handoff)
    prepared = prepare_piece_model_request(PieceGenerationRequest('synthetic-piece-active-original',
        projected, owner, source, handoff.original.source_input_version))
    assert [s['source_id'] for s in prepared.payload()['sources']] == [source, question]
    assert state['answer_text'] not in prepared.private_json
    receipt = receive_piece_model_candidate(prepared, finish_reason='stop',
        raw_output=json.dumps({'body_blocks': [original, ANSWER]}, ensure_ascii=False))
    candidate = generate_piece_candidate(projected, authenticated_owner_id=owner,
        model_candidate=PieceModelInputV1(prepared, receipt))
    assert candidate['content_payload']['body_blocks'] == [original, ANSWER]

    # A mismatched private source receipt cannot prove the preserved original.
    changed = db.query("""update public.emlis_input_threads
        set data=jsonb_set(data,'{analysis_material,source_prefix_ref}','"stale"'::jsonb)
        where original_emotion_id=$1""", [source])
    assert 'code' not in changed, changed
    assert read(db, owner, source, question, selected['commitment']) is None
    assert links() == {}
