"""The isolated records-answer source for a future explicit Piece selection."""

from hashlib import sha256
import json
from uuid import uuid4

import pytest

from test_analysis_deep_insight_handoff import RECEIVED_MAP_MIGRATIONS
from test_analysis_interpretation_correction_sources import sql_script
from test_emlis_q3_application import qdb


MIGRATION = '20261128060550_piece_deep_insight_source_binding.sql'
RECORD = '会議の前に手順を確認しました。'
QUESTION = '会議の前に手順を確認するとき、どこを重視しますか？'
ANSWER = '私は、途中で参加する人にも分かりやすい順番を大切にしたいです。'


@pytest.fixture(scope='module')
def piece_db(qdb):
    for migration in (*RECEIVED_MAP_MIGRATIONS, '20261121134000_deep_insight_grounded_questions.sql', MIGRATION):
        sql_script(qdb, migration)
    assert 'code' not in qdb.query('alter table public.emotions add column is_secret boolean not null default false')
    return qdb


@pytest.fixture
def selection(piece_db):
    owner, reader, parent, unrelated = (str(uuid4()) for _ in range(4))
    assert 'code' not in piece_db.query('insert into auth.users values($1),($2)', [owner, reader])
    assert 'code' not in piece_db.query("insert into public.profiles values($1,'premium'),($2,'premium')", [owner, reader])
    assert 'code' not in piece_db.query("""insert into public.emotions(id,user_id,created_at,memo,memo_action,category,emotions,emotion_details)
      values($1,$2,(now()-interval '500 days') at time zone 'UTC',$3,'',array['仕事'],array['平穏'],
        '[{"type":"平穏","strength":"medium"}]'), ($4,$2,(now()-interval '500 days') at time zone 'UTC',$3,'',
        array['仕事'],array['平穏'],'[{"type":"平穏","strength":"medium"}]')""", [parent, owner, RECORD, unrelated])
    context = value(piece_db, 'select public.deep_insight_candidate_context($1) as v', owner)
    day = value(piece_db, 'select public.deep_insight_state($1) as v', owner)['day']
    original = next(row for row in context['material']['records'] if row['id'] == parent)
    span = RECORD.removesuffix('。')
    receipt = dict(policy_version='deep-insight.v2', lane='records', focus='VALUE', source_id=parent,
        source_version=original['source_version'], field='thought', start=0, end=len(span),
        literal_sha256=sha256(span.encode()).hexdigest(), condition_key=None, target_key='a' * 64)
    issued = value(piece_db, "select public.deep_insight_issue_grounded($1,$2,'records',null,$3,$4,$5,$6,$7) as v",
        owner, day, QUESTION, 'deep-insight-target-' + receipt['target_key'],'test-question',context['guard'],json.dumps(receipt))
    assert issued['status'] == 'issued'
    question = issued['question']['id']
    saved = value(piece_db, 'select public.deep_insight_answer($1,$2,$3) as v', owner, question, ANSWER)
    assert saved['inserted'] is True
    return owner, reader, parent, question, unrelated


def value(db, sql, *parameters, role='service_role'):
    result = db.query(sql, list(parameters), role)
    assert 'code' not in result, result
    return result['rows'][0]['v']


def read(db, owner, original, question, commitment=None, *, role='service_role'):
    return value(db, 'select public.piece_deep_insight_source_binding($1,$2,$3,$4) as v',
        owner, original, question, commitment, role=role)


def test_explicit_record_answer_keeps_original_and_question_context_separate(piece_db, selection):
    owner, reader, parent, question, unrelated = selection
    selected = read(piece_db, owner, parent, question)
    assert selected['source_version'] == 'piece.deep_insight_answer.v1'
    assert selected['original']['memo'] == RECORD and selected['original']['id'] == parent
    assert selected['answer_id'] == question and selected['answer_text'] == ANSWER
    assert selected['ai_question_context'] == QUESTION and len(selected['commitment']) == 71
    assert read(piece_db, owner, parent, question, selected['commitment']) == selected
    assert read(piece_db, owner, parent, question, 'sha256:' + 'f' * 64) is None
    assert read(piece_db, owner, unrelated, question) is None
    assert read(piece_db, reader, parent, question) is None
    assert read(piece_db, owner, parent, None) is None


@pytest.mark.parametrize('change', ['secret', 'owner-access', 'old-tier', 'edited', 'deleted', 'proof',
    'wrong-role', 'theme', 'unanswered', 'future-answer'])
def test_changed_or_ineligible_draft_source_cannot_be_reused(piece_db, selection, change):
    owner, _, original, question, _ = selection
    old = read(piece_db, owner, original, question)
    statements = {
        'secret': ('update public.emotions set is_secret=true where id=$1', original),
        'owner-access': ('delete from public.profiles where id=$1', owner),
        'old-tier': ("update public.profiles set subscription_tier='plus' where id=$1", owner),
        'edited': ("update public.emotions set memo=memo||'更新' where id=$1", original),
        'deleted': ('delete from public.emotions where id=$1', original),
        'proof': ("update public.deep_insight_questions set grounding_receipt=grounding_receipt-'literal_sha256' where id=$1", question),
        'wrong-role': ("""update public.deep_insight_questions set grounding_receipt=jsonb_set(grounding_receipt,
            '{field}','"answer"'::jsonb) where id=$1""", question),
        'theme': ("update public.deep_insight_questions set lane='theme',theme='仕事・学び' where id=$1", question),
        'unanswered': ('update public.deep_insight_questions set answer_text=null,answered_at=null where id=$1', question),
        'future-answer': ("update public.deep_insight_questions set answered_at=now()+interval '1 day' where id=$1", question),
    }
    sql, row = statements[change]
    assert 'code' not in piece_db.query(sql, [row])
    assert read(piece_db, owner, original, question, old['commitment']) is None


def test_source_binding_is_unavailable_to_direct_application_roles(piece_db, selection):
    owner, _, original, question, _ = selection
    for role in ('anon', 'authenticated'):
        result = piece_db.query('select public.piece_deep_insight_source_binding($1,$2,$3) as v',
            [owner, original, question], role)
        assert result.get('code') == '42501'
