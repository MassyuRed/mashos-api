"""A history MERGE may reuse displayed source scalars but must recover the exact v24 request."""
import json

import pytest

import analysis_merge_wire as wire


def fixture(phase='PLAN'):
    # The same sentence in two different source fields cannot identify its author.
    first = '朝、試した。🪴まだ決めていない。'
    visible = 'まだ決めていない。'
    start = first.index(visible)
    second = dict(field=2, field_path='memo', record=2, source_role='ORIGINAL_INPUT',
                  text=visible, fragment_scalar_range=[21, 21 + len(visible)], fragment_is_complete_field=False)
    first_field = dict(field=1, field_path='memo_action', record=1, source_role='ORIGINAL_INPUT',
                       text=first, fragment_scalar_range=[0, len(first)], fragment_is_complete_field=True)
    manifest = [dict(field=1, field_path='memo_action', record=1, source_role='ORIGINAL_INPUT',
                     scalar_length=len(first), text_sha256=wire.digest(first)),
                dict(field=2, scalar_length=100, text_sha256=wire.digest('the full source is not present')),
                dict(field=7, scalar_length=90, text_sha256=wire.digest('an omitted source'))]
    citations = [dict(field=1, quote=visible, scalar_range=[start, len(first)], choice=['決めていない']),
                 dict(field=2, quote=visible, scalar_range=second['fragment_scalar_range']),
                 dict(field=1, quote=first[:start], scalar_range=[0, start])]
    material = dict(model_schema=wire.MODEL_SCHEMA, author_profile=wire.PROFILE, author_phase=phase,
                    history_stage=dict(kind='MERGE'), fields=[first_field, second],
                    field_manifest=manifest, leaf_source_index=citations,
                    leaf_receipts=[dict(leaf_request_ref='old leaf id', response_sha256='old response')],
                    omitted_ranges=[dict(field=7, reason='not presented')])
    return [dict(role='system', content='原文の範囲を確認'), dict(role='user', content=wire.compact_json(material))]


@pytest.mark.parametrize('phase', ['PLAN', 'NODES', 'RELATIONS'])
def test_all_merge_phases_preserve_exact_citations_fragment_hashes_and_original_bytes(phase):
    original = fixture(phase)
    wire_messages = wire.prepare_messages(original)
    material = json.loads(wire_messages[1]['content'])
    legacy = json.loads(original[1]['content'])
    assert wire.legacy_messages(wire_messages) == original
    assert material['leaf_source_index'][0] == [1, *legacy['leaf_source_index'][0]['scalar_range'], ['決めていない']]
    assert material['leaf_source_index'][1][:2] == [2, 21]
    assert material['field_manifest']['source_rows'][1:] == legacy['field_manifest'][1:]
    for key in ('fields', 'leaf_receipts', 'omitted_ranges'):
        assert material[key] == legacy[key]


@pytest.mark.parametrize('mutation', ['other_scope', 'range', 'boolean_field', 'original_text', 'extra_layout'])
def test_modified_source_scope_or_noncanonical_compression_rejected(mutation):
    wire_messages = wire.prepare_messages(fixture())
    material = json.loads(wire_messages[1]['content'])
    if mutation == 'other_scope':
        material['history_stage']['kind'] = 'LEAF'
    elif mutation == 'range':
        material['leaf_source_index'][0][1] -= 1
    elif mutation == 'boolean_field':
        material['leaf_source_index'][0][0] = True
    elif mutation == 'original_text':
        material['fields'][1]['text'] = 'もう確かめた。'
    else:
        material['field_manifest']['source_columns'].append(['field'])
    wire_messages[1]['content'] = wire.compact_json(material)
    with pytest.raises(ValueError, match='analysis_merge_wire_invalid'):
        wire.legacy_messages(wire_messages)


def test_sliced_text_and_supported_passage_markup_have_identical_scalar_coordinates():
    original = fixture()
    material = json.loads(original[1]['content'])
    field = material['fields'][0]
    text = field.pop('text')
    field['passages'] = [text[:3], [[text[3:7], 'original wording'], text[7:]]]
    original[1]['content'] = wire.compact_json(material)
    assert wire.legacy_messages(wire.prepare_messages(original)) == original


def test_unrelated_models_and_current_leaf_or_whole_return_original_message_objects():
    for kind, profile in [('LEAF', wire.PROFILE), ('WHOLE', wire.PROFILE), ('MERGE', 'older')]:
        original = fixture()
        material = json.loads(original[1]['content'])
        material['author_profile'] = profile
        material['history_stage']['kind'] = kind
        original[1]['content'] = wire.compact_json(material)
        assert wire.prepare_messages(original) is original


def test_only_reconstructible_manifest_metadata_is_condensed():
    original = fixture()
    material = json.loads(original[1]['content'])
    manifest = material['field_manifest']
    manifest[0]['supplement'] = 'retained historical annotation'
    original[1]['content'] = wire.compact_json(material)
    wire_messages = wire.prepare_messages(original)
    visible_manifest = json.loads(wire_messages[1]['content'])['field_manifest']['source_rows']
    assert visible_manifest == manifest
    assert wire.legacy_messages(wire_messages) == original


@pytest.mark.parametrize('kind', ['MERGE', 'LEAF', 'WHOLE'])
@pytest.mark.parametrize('marker', sorted(wire.WIRE_FIELDS))
def test_reserved_wire_fields_cannot_be_used_independently_or_as_legacy_input(kind, marker):
    original = fixture()
    material = json.loads(original[1]['content'])
    material['history_stage']['kind'] = kind
    material[marker] = wire.VERSION if marker == 'merge_wire_version' else '1' * 64
    original[1]['content'] = wire.compact_json(material)
    for operation in (wire.is_compact, wire.prepare_messages, wire.legacy_messages):
        with pytest.raises(ValueError, match='analysis_merge_wire_invalid'):
            operation(original)


def test_native_constraint_reader_restores_only_the_versioned_merge_input():
    from test_emlis_natural_reply_probe_http import probe

    original = fixture()
    actual_wire = wire.prepare_messages(original)
    assert actual_wire != original
    assert probe._semantic_constraint_messages(actual_wire) == original

    whole = fixture()
    material = json.loads(whole[1]['content'])
    del material['history_stage']
    whole[1]['content'] = wire.compact_json(material)
    assert probe._semantic_constraint_messages(whole) is whole

    for key, value in [('merge_original_messages_sha256', 'a' * 64), ('merge_wire_version', wire.VERSION)]:
        malformed = [whole[0], dict(whole[1], content=wire.compact_json({**material, key: value}))]
        with pytest.raises(ValueError, match='analysis_merge_wire_invalid'):
            probe._semantic_constraint_messages(malformed)
