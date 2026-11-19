"""Projection removes only identical source-backed pieces in the same node and record."""
from copy import deepcopy

import pytest

from cocolon_meaning_experience_engine.cores.analysis.intent_compiler import _node_unique_fixed_facts

def unit(*roots, mode='RECORDED'):
    return dict(evidence=[dict(field=f,quote=q) for f,q in roots], fact=''.join(q for f,q in roots), source_mode=mode)

def test_repeated_bound_phrase_preserves_other_parts_and_all_input_units():
    a,b,c=((1,'机を整えた。'),(2,'紙を折った。'),(1,'窓を開けた。'))
    units=[unit(a,b),unit(a,c)]
    source=deepcopy(units)
    selected=[(a[1],b[1]),(a[1],c[1])]
    assert _node_unique_fixed_facts(units,selected,{1:1,2:1})==[a[1]+b[1],c[1]]
    assert units==source
    assert _node_unique_fixed_facts(units,[selected[0],False],{1:1,2:1})==[u['fact'] for u in units]
    assert _node_unique_fixed_facts(units,selected,{1:1,2:2})==[u['fact'] for u in units]
    assert _node_unique_fixed_facts(units,selected,{1:1})==[u['fact'] for u in units]

@pytest.mark.parametrize('field,quote,phrase,mode', [
    (2,'窓を開けた。紙を折った。','紙を折った。','RECORDED'),
    (1,'机を整えた。紙を折った。','紙を折った。','RECORDED'),
    (1,'窓を開けた。紙を折った。','窓を開けた。','RECORDED'),
    (1,'窓を開けた。紙を折った。','紙を折った。','PERSON_JUDGMENT'),
])
def test_keep_different_field_root_choice_or_mode(field,quote,phrase,mode):
    units=[unit((1,'窓を開けた。紙を折った。')),unit((field,quote),mode=mode)]
    values=[('紙を折った。',),(phrase,)]
    for row,parts in zip(units,values,strict=True):
        row['fact']=''.join(parts)
    assert _node_unique_fixed_facts(units,values,{1:1,2:1})==[u['fact'] for u in units]
