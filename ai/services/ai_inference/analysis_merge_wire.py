"""A lossless transport view of v24 history MERGE inputs. Model outputs retain the v24 schema."""
from __future__ import annotations

import hashlib
import json


LEGACY_VERSION = 'cocolon.analysis.merge_wire.v1'
VERSION = 'cocolon.analysis.merge_wire.v2'
VERSIONS = (LEGACY_VERSION, VERSION)
PROFILE = 'semantic_map.node_local.v4.occurrence.v24'
MODEL_SCHEMA = 'cocolon.analysis.semantic_map.node_local.model.v4'
WIRE_FIELDS = {'merge_wire_version', 'merge_original_messages_sha256'}
INSTRUCTION = ('\nMERGEのleaf_source_indexは[欄番号,元の開始位置,終了位置,選べる原文句（ある場合）]です。'
    '引用の内容は指定したfieldsの同じ原文範囲です。開始を含み、終了は含みません。'
    'field_manifestのsource_rowsは[欄番号,source_columnsの0起点の番号]の場合、'
    '表示している完全な原欄と同じです。元の各葉から届いた範囲と、本人が入力した原文の区別は変わりません。')

RECORD_GUIDANCE = ('\n記録ごとの項目を並べられる場合、先頭の項目は記録の順に作ります。'
    '各項目は対応する原記録の本人の欄から始め、その記録の根拠で説明します。'
    '12記録を超える場合、各記録の原欄を選べない場合、または訂正などの独立した項目が収まらない場合は、'
    'この順序に固定せず、原文に沿って項目を構成します。'
    '複数の記録に基づく比較では、どの記録のどの条件・時点の話かを別々のunitで示します。'
    '別項目の関連はRELATIONSで具体的な根拠を一つずつ選びます。別の対象や未確認事項を同じ出来事として扱いません。')


def instruction(version):
    require(version in VERSIONS)
    return INSTRUCTION + (RECORD_GUIDANCE if version == VERSION else '')


def require(ok):
    if not ok:
        raise ValueError('analysis_merge_wire_invalid')


def compact_json(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def messages_digest(messages):
    return digest(json.dumps(messages, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False))


def eligible(material):
    return (isinstance(material, dict) and material.get('author_profile') == PROFILE
            and material.get('model_schema') == MODEL_SCHEMA
            and (material.get('history_stage') or {}).get('kind') == 'MERGE'
            and material.get('author_phase') in ('PLAN', 'NODES', 'RELATIONS'))


def is_compact(messages):
    material = json.loads(messages[1]['content'])
    if not isinstance(material, dict) or not WIRE_FIELDS.intersection(material):
        return False
    require(WIRE_FIELDS.issubset(material) and eligible(material)
            and material['merge_wire_version'] in VERSIONS)
    return True


def displayed_fields(material):
    """Some PLAN fields carry the same ordered text as annotated passages."""
    fields = {}
    for field in material['fields']:
        number = field['field']
        require(type(number) is int and number not in fields)
        if 'text' in field:
            require('passages' not in field and type(field['text']) is str)
            fields[number] = field
        else:
            parts = []
            for passage in field['passages']:
                if isinstance(passage, str):
                    parts.append(passage)
                else:
                    parts.extend(piece if isinstance(piece, str) else piece[0] for piece in passage)
            fields[number] = dict(field, text=''.join(parts))
    return fields


def source_slice(fields, field_number, lo, hi):
    require(type(field_number) is int and type(lo) is int and type(hi) is int and lo < hi)
    field = fields[field_number]
    start, end = field['fragment_scalar_range']
    require(start <= lo < hi <= end and end - start == len(field['text']))
    return field['text'][lo-start:hi-start]


def pack_index(index, fields):
    result = []
    for row in index:
        if tuple(row) not in (('field', 'quote', 'scalar_range'), ('field', 'quote', 'scalar_range', 'choice')):
            result.append(row)
            continue
        lo, hi = row['scalar_range']
        require(source_slice(fields, row['field'], lo, hi) == row['quote'])
        entry = [row['field'], lo, hi]
        if 'choice' in row:
            entry.append(row['choice'])
        result.append(entry)
    return result


def unpack_index(index, fields):
    result = []
    for row in index:
        if type(row) is dict:
            result.append(row)
        else:
            require(type(row) is list and len(row) in (3, 4))
            number, lo, hi = row[:3]
            entry = dict(field=number, quote=source_slice(fields, number, lo, hi), scalar_range=[lo, hi])
            if len(row) == 4:
                entry['choice'] = row[3]
            result.append(entry)
    return result


def manifest_row(field, columns):
    require(field.get('fragment_is_complete_field') is True
            and field.get('fragment_scalar_range') == [0, len(field['text'])])
    values = dict(field, scalar_length=len(field['text']), text_sha256=digest(field['text']))
    return {name: values[name] for name in columns}


def pack_manifest(manifest, fields):
    columns, rows = [], []
    for row in manifest:
        field = fields.get(row['field'])
        names = list(row)
        if (field and field.get('fragment_is_complete_field') is True
                and all(k in field or k in ('text_sha256', 'scalar_length') for k in names)
                and compact_json(manifest_row(field, names)) == compact_json(row)):
            if names not in columns:
                columns.append(names)
            rows.append([row['field'], columns.index(names)])
        else:
            # A fragment or absent field cannot reconstruct the full-field hash.
            rows.append(row)
    return dict(source_columns=columns, source_rows=rows)


def unpack_manifest(manifest, fields):
    require(type(manifest) is dict and set(manifest) == {'source_columns', 'source_rows'})
    columns = manifest['source_columns']
    result = []
    for row in manifest['source_rows']:
        if type(row) is dict:
            result.append(row)
            continue
        require(type(row) is list and len(row) == 2)
        number, layout = row
        require(type(number) is int and type(layout) is int and 0 <= layout < len(columns))
        result.append(manifest_row(fields[number], columns[layout]))
    return result


def prepare_messages(messages, *, version=VERSION):
    material = json.loads(messages[1]['content'])
    if isinstance(material, dict):
        require(not WIRE_FIELDS.intersection(material))
    if not eligible(material):
        return messages
    require(compact_json(material) == messages[1]['content'])
    fields = displayed_fields(material)
    material['leaf_source_index'] = pack_index(material['leaf_source_index'], fields)
    material['field_manifest'] = pack_manifest(material['field_manifest'], fields)
    material['merge_wire_version'] = version
    material['merge_original_messages_sha256'] = messages_digest(messages)
    return [dict(messages[0], content=messages[0]['content'] + instruction(version)),
            dict(messages[1], content=compact_json(material))]


def legacy_messages(messages):
    try:
        material = json.loads(messages[1]['content'])
        require(eligible(material))
        version = material.pop('merge_wire_version', None)
        suffix = instruction(version)
        binding = material.pop('merge_original_messages_sha256')
        require(messages[0]['content'].endswith(suffix))
        fields = displayed_fields(material)
        material['leaf_source_index'] = unpack_index(material['leaf_source_index'], fields)
        material['field_manifest'] = unpack_manifest(material['field_manifest'], fields)
        result = [dict(messages[0], content=messages[0]['content'][:-len(suffix)]),
                  dict(messages[1], content=compact_json(material))]
        require(messages_digest(result) == binding)
        # Ensure the sender used the canonical representation, including the menu layout.
        require(prepare_messages(result, version=version) == messages)
        return result
    except (KeyError, TypeError, IndexError) as exc:
        raise ValueError('analysis_merge_wire_invalid') from exc
