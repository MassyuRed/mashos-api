"""Both privileged legacy Piece RPCs reject the public database roles."""
from uuid import uuid4

import pytest

from test_piece_public_alias_transactions import alias_db


@pytest.mark.parametrize('role', ['anon', 'authenticated'])
@pytest.mark.parametrize('function', ['piece_increment_legacy_metric', 'piece_apply_legacy_reaction'])
def test_legacy_piece_rpc_denies_public_role_before_any_effect(alias_db, role, function):
    before = alias_db.query('select count(*)::int as n from public.mymodel_qna_metrics')
    if function == 'piece_increment_legacy_metric':
        result = alias_db.query('select public.piece_increment_legacy_metric($1,$2,$3,$4)',
                                ['synthetic-role-test', 'reflection:synthetic', 'views', 1], role)
    else:
        source, owner, viewer = (str(uuid4()) for _ in range(3))
        result = alias_db.query('select public.piece_apply_legacy_reaction($1,$2,$3,$4,$5,$6,$7)',
             [source, owner, viewer, 'reflection:'+source, 'synthetic-role-test', 'resonate', None], role)
    assert result['code'] == '42501', result
    assert alias_db.query('select count(*)::int as n from public.mymodel_qna_metrics') == before
    assert alias_db.query('select count(*)::int as n from public.mymodel_qna_resonances')['rows'] == [{'n': 0}]
    assert alias_db.query('select count(*)::int as n from public.mymodel_qna_echoes')['rows'] == [{'n': 0}]
