"""Reversible private transport for v24 history MERGE. Saved receipts retain the bytes received."""
from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from datetime import date
from itertools import combinations


LEGACY_VERSION = 'cocolon.analysis.merge_wire.v1'
RECORD_VERSION = 'cocolon.analysis.merge_wire.v2'
OUTPUT_VERSION = 'cocolon.analysis.merge_wire.v3'
SOURCE_TITLE_VERSION = 'cocolon.analysis.merge_wire.v4'
COMPARISON_VERSION = 'cocolon.analysis.merge_wire.v5'
PAIRED_VERSION = 'cocolon.analysis.merge_wire.v6'
DECISION_VERSION = 'cocolon.analysis.merge_wire.v7'
REQUEST_SUBJECT_VERSION = 'cocolon.analysis.merge_wire.v8'
REQUEST_PROGRESS_VERSION = 'cocolon.analysis.merge_wire.v9'
JUDGMENT_VERSION = 'cocolon.analysis.merge_wire.v10'
VERSION = JUDGMENT_VERSION
REQUEST_PROGRESS_VERSIONS = (REQUEST_PROGRESS_VERSION, JUDGMENT_VERSION)
REQUEST_SUBJECT_VERSIONS = (REQUEST_SUBJECT_VERSION, *REQUEST_PROGRESS_VERSIONS)
DECISION_VERSIONS = (DECISION_VERSION, *REQUEST_SUBJECT_VERSIONS)
PAIRED_VERSIONS = (PAIRED_VERSION, *DECISION_VERSIONS)
COMPARISON_VERSIONS = (COMPARISON_VERSION, *PAIRED_VERSIONS)
TITLE_VERSIONS = (SOURCE_TITLE_VERSION, *COMPARISON_VERSIONS)
OUTPUT_VERSIONS = (OUTPUT_VERSION, *TITLE_VERSIONS)
VERSIONS = (LEGACY_VERSION, RECORD_VERSION, *OUTPUT_VERSIONS)
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


RESPONSE_GUIDANCE = {
    'PLAN': ('\n今回のMERGEの応答は {"h":"source_choices_sha256の値","n":[項目,…]} です。'
        '項目は単位の配列、単位は根拠の配列、一つの根拠は[原文の短い符号,欄番号]です。'
        '符号 ~先頭…末尾 はその範囲と完全に同じ原文を指します。'
        '記録ごとに本人の行動欄と経過の末尾を読み、最初の予定・検討と、実行したこと、'
        '見送ったこと、未確認のことを時点・対象とともに選びます。別の出来事には別の単位を使います。'
        '事実に必要な根拠を選び、同じ内容の繰り返しを避けます。'),
    'NODES': ('\n今回のMERGEの応答は {"h":"plan_sha256の値","n":[項目,…]} です。'
        '入力のplanの各単位の数値は、evidence_parts_by_unitに示した根拠の個数です。'
        '同じ項目・単位順で、項目は[単位の配列,node_kind,perspective,title,meaning]、'
        '単位は[source_mode,根拠順のfact値の配列,留保の配列]、留保は[原文の符号,欄番号]です。'
        '根拠名は順序で決まり、符号 ~先頭…末尾 は完全な原文を指します。'
        '未確認は確認済みに変えず、他の出来事や別人の発言を本人の行動にしません。'
        '別々の根拠にある出来事を同時とせず、後の記録や返答で判明したことを前の時点の確定事項にしません。'),
    'RELATIONS': ('\n各単位でfactが0なら、同じ単位のevidenceを順番に読み、各引用をそのままつないだ本文です。'
        'fact_part_overridesに同じn番号.u番号.e番号がある箇所だけ、その本文片を引用に代えて読みます。'
        'qualification_candidatesの[n,u,k]は番号nの項目、u番目の単位のunknownsのk番目と同じ留保です。'
        'unknownsとqualification_candidatesの留保は、それぞれの原文と時点を確認します。'
        '返すqualification_reviewは候補順の配列です。STATED、EARLIER、DUPLICATEは文字列で、'
        'OPENは[0]で候補の原文全体、許可された別の原文範囲なら[引用符号]で選びます。'),
}


def instruction(version, phase):
    require(version in VERSIONS)
    guidance = INSTRUCTION
    if version in (RECORD_VERSION, *OUTPUT_VERSIONS):
        guidance += RECORD_GUIDANCE
    if version in OUTPUT_VERSIONS:
        guidance += ('\n原欄はfieldsに全文があります。根拠・留保の引用値が[開始,終了,読取り句]なら、'
            '対応する欄のその範囲の全文です。読取り句は両端の手掛かりで、途中の否定や条件を含む元の範囲を読みます。'
            '未読範囲の圧縮表示ではstartから各lengthsの長さだけ進み、次までの間隔は1、'
            'gapsにある番号だけ指定間隔です。')
        guidance += RESPONSE_GUIDANCE[phase]
    if version in TITLE_VERSIONS and phase == 'NODES':
        guidance += (' この項目の見出しは、選んだ根拠にある一文を条件・主体・留保ごと残して選びます。'
            '文の一部を切り出して別の事実にはしません。選べる一文がないときは記録を指す見出しを使います。')
    if version in TITLE_VERSIONS and phase == 'PLAN':
        guidance += (' 行動欄の「話した・聞いた・伝えた・確認した」だけで、誰が何を望み、'
            '何を話したかが分からない場面では、同じ記録の思考欄全文から話者と発言内容が一緒に分かる原文を選びます。'
            '葉の引用以外の原文も選べます。別の日に同じ対象への判断が変わった場合は、'
            'それぞれの日の判断と、その時に分かっていた条件を各記録の単位に残します。')
    if version in TITLE_VERSIONS and phase == 'RELATIONS' and version != JUDGMENT_VERSION:
        guidance += (' 線を選ぶ前に、同じ対象が再び出た日の単位を突き合わせます。'
            '両方の原引用から、どの条件で何を選び、後にどの条件で何を選んだか説明できる組は、'
            'その二つの単位を選び、具体的な条件と行動を線の文にします。'
            '対象の一致や条件差を両端で確かめられず、他にも説明できる関係がなければedges=[]です。')
    if version in COMPARISON_VERSIONS and phase == 'PLAN':
        guidance += (' memo_context_choicesは、行動の要約にない発言の内容・実行時点・確かめた結果を照合するための'
            '[思考欄番号,同じ欄で選べる原文の候補]です。該当する項目でいずれかを原文のまま含む根拠を選びます。'
            '誰が話したか、意向と実行、予定と実際の順序は原文で確かめます。候補自体は意味の判定ではありません。')
    if version == COMPARISON_VERSION and phase == 'RELATIONS':
        guidance += (' comparison_candidatesがある時は、qualification_reviewの次に、その順でcomparisonsを答えます。'
            'wordingは同じ綴りで、同じ物や理由の証拠ではありません。左右の原引用を実際に読み、'
            '同じ対象について条件と行動の違いを説明できる時は["COMPARE",自分で書いた具体的な比較文,relation_kind]。'
            '異なる対象は"DIFFERENT_SUBJECT"、共通性や違いの根拠が足りない時は"INSUFFICIENT_EVIDENCE"です。'
            '同じ綴りだけで対象や主体が同じと決めず、否定・希望・未確認を残します。別記録でも同日や時間順が不明なら、別日や時系列変化を断定しません。'
            '比較を選んだ組はそのまま線になるので、次のedgesはほかに原文から説明できる関係だけにします。')
    if version in PAIRED_VERSIONS and phase == 'NODES':
        guidance += (' 同じ記録の原欄はそれぞれ原文順に読みます。見出しには最初に表示する原文か'
                     '記録を示す見出しを選び、後の出来事を先に見せません。')
    if version in PAIRED_VERSIONS and phase == 'PLAN':
        guidance += (' 同じ思考欄に複数の行があれば、それぞれ別の発言・条件・訂正です。'
            '各行から少なくとも一候補を原文のまま含めます。一つの引用で複数行を満たせます。')
    if version == JUDGMENT_VERSION and phase == 'RELATIONS':
        return guidance + (' comparison_candidatesごとに左右の記録日、sentencesの各原文とsubject_witnessを読みます。'
            '依頼物とrecipient（宛先）が一致しても、発言した人・伝えた人・自分で確かめたことは別々に扱います。'
            '各組のjudgment_choicesから、両方の文に沿う一行をそのままcomparisonsの同じ位置に書きます。'
            '形は[判断,対象,左の文番号,接続語,右の文番号]です。判断の条件や選択の違いは「対照」、'
            '同じ依頼物を同じ宛先へ頼む提案とその後の連絡・応答は「同じ依頼の経過」です。'
            '両日から対象や案件の違いを読み取れるときは「別件」、対応を判断する材料が足りないときは「材料不足」。'
            '進行を選んでも、本人が送信したことや納品までを意味しません。別題の否定や返事の有無も含め原文どおり残します。'
            '判断した組はedgesへ重ねません。ほかに説明できる関係は両端の原文を選んで書き、なければedgesは空配列です。')
    if version in PAIRED_VERSIONS and phase == 'RELATIONS':
        difference = '判断の対象が違う場合は' if version in REQUEST_SUBJECT_VERSIONS else '別の物や判断なら'
        guidance += (' comparison_candidatesは対象を照合するための原文です。subjectとsubject_witnessの'
            f'記録・主体・対象・条件を左右で確認します。{difference}"DIFFERENT_SUBJECT"、'
            '不足なら"INSUFFICIENT_EVIDENCE"を選びます。両資料から同じ対象への判断差を説明できる時だけ、'
            'comparisonsに["COMPARE",subject,左のsentencesの1始まり番号,"一方、"または"別の記録では、",右の番号]。'
            'あなたが選んだ左の一文・接続語・右の一文がその順で一本の比較文になります。'
            '別記録を別日と決めず、留保や伝聞を保ちます。同じ候補の組はedgesに重ねません。別の記録間の線も、指定した両端の原引用に固有の内容を左右から一つずつ文に残します。')
    if version in REQUEST_SUBJECT_VERSIONS and phase == 'RELATIONS':
        guidance += (' subject_witness.kind が requested_object の組では、subject は依頼された物、'
            'recipient は依頼先です。left と right は依頼物と依頼先を照合した各記録の原文です。'
            '誰が提案し、誰が依頼し、誰がその連絡に応えたかを両端の sentences と一緒に読みます。'
            '同じ物についての提案と後日の連絡は話者や行動が違っても比較できます。'
            '未送信と送信未確認、依頼と納品は区別します。物が違う時は DIFFERENT_SUBJECT、'
            '同じ物か確認できない時は INSUFFICIENT_EVIDENCE を選びます。')
    if version in REQUEST_PROGRESS_VERSIONS and phase == 'RELATIONS':
        guidance += (' request_progress_choices は同じ物の依頼がどこまで進んだかを二つの記録でたどる選択肢です。'
            '提案した時の未確認と、後の記録で受け取った連絡や本人の返答は、判断が対照的でなくても結べます。'
            '左右の原文を読み、同じ依頼の段階なら、comparisonsのその位置に対応するFOLLOW_REQUESTの配列を選びます。'
            '判断や条件の違いを比べる場合はCOMPAREを選びます。別の案件にはDIFFERENT_SUBJECT、'
            '同じ依頼か判断できないときはINSUFFICIENT_EVIDENCEを使います。'
            '連絡を受けたことから、自分で送信や受領を確認したとは書きません。')
    return guidance


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


def _range_lengths(material, *, unpack=False):
    for row in (material.get('source_duties') or {}).get('unassessed_source_ranges', ()):
        ranges = row['ranges']
        if unpack:
            if type(ranges) is not dict:
                continue
            require(set(ranges) == {'start', 'lengths', 'gaps'})
            start, lengths, gaps = ranges['start'], ranges['lengths'], ranges['gaps']
            require(type(start) is int and start >= 0 and type(lengths) is list and lengths
                    and type(gaps) is list)
            gap_at = {}
            for pair in gaps:
                require(type(pair) is list and len(pair) == 2)
                index, gap = pair
                require(type(index) is int and 1 <= index < len(lengths) and index not in gap_at
                        and type(gap) is int and gap >= 0 and gap != 1)
                gap_at[index] = gap
            expanded = []
            for i, length in enumerate(lengths):
                require(type(length) is int and length > 0)
                expanded.append([start, start + length])
                start += length + gap_at.get(i + 1, 1)
            row['ranges'] = expanded
        elif (type(ranges) is list and len(ranges) >= 4
                and all(type(pair) is list and len(pair) == 2 and all(type(n) is int for n in pair)
                        and 0 <= pair[0] < pair[1] for pair in ranges)
                and all(prev[1] <= nxt[0] for prev, nxt in zip(ranges, ranges[1:]))):
            packed = dict(start=ranges[0][0], lengths=[hi-lo for lo, hi in ranges],
                gaps=[[i, right[0]-left[1]] for i, (left, right) in enumerate(zip(ranges, ranges[1:]), 1)
                      if right[0]-left[1] != 1])
            if len(compact_json(packed)) < len(compact_json(ranges)):
                row['ranges'] = packed


def _source_spelling(row, fields, field_key, quote_key, *, unpack):
    field = fields.get(row.get(field_key))
    if not field or quote_key not in row:
        return
    quote = row[quote_key]
    if unpack and type(quote) is list:
        require(len(quote) == 3)
        start, end, cue = quote
        literal = source_slice(fields, row[field_key], start, end)
        require(cue == literal[:4] + '…' + literal[-4:])
        row[quote_key] = literal
    elif not unpack and type(quote) is str and len(quote) > 12:
        span = field.get('fragment_scalar_range')
        if type(span) is not list or len(span) != 2:
            return
        start = field['text'].find(quote)
        if start >= 0 and start == field['text'].rfind(quote):
            begin = span[0] + start
            packed = [begin, begin + len(quote), quote[:4] + '…' + quote[-4:]]
            if len(compact_json(packed).encode()) < len(compact_json(quote).encode()):
                row[quote_key] = packed


def _visible_sources(material, fields, *, unpack=False):
    """Preserve every source/qualification, including duplicates with different field owners."""
    if material['author_phase'] == 'NODES':
        for entries in material.get('evidence_parts_by_unit', {}).values():
            for root in entries.values():
                _source_spelling(root, fields, 'field', 'quote', unpack=unpack)
        return
    if material['author_phase'] != 'RELATIONS':
        return
    registry = material.get('candidate_nodes', ())
    candidates = material.get('qualification_candidates', {})
    by_indices, by_source = {}, {}
    for n, node in enumerate(registry, 1):
        for u, unit in enumerate(node['units'], 1):
            for root in unit['evidence']:
                _source_spelling(root, fields, 'field', 'quote', unpack=unpack)
            for k, source in enumerate(unit.get('unknowns', ()), 1):
                if unpack:
                    _source_spelling(source, fields, 'source_field', 'source_quote', unpack=True)
                ref = (n, u, k)
                by_indices[ref] = source
                by_source.setdefault(compact_json(source), ref)
                if not unpack:
                    _source_spelling(source, fields, 'source_field', 'source_quote', unpack=False)
    for key, candidate in candidates.items():
        if unpack and type(candidate) is list:
            require(len(candidate) == 3 and all(type(i) is int for i in candidate))
            ref = tuple(candidate)
            require(ref in by_indices)
            candidates[key] = dict(by_indices[ref])
        elif not unpack and (ref := by_source.get(compact_json(candidate))) is not None:
            candidates[key] = list(ref)
        elif type(candidate) is dict:
            _source_spelling(candidate, fields, 'source_field', 'source_quote', unpack=unpack)


def _node_plan_references(material, *, unpack=False):
    """Keep exactly one visible copy of every selected quote and its fact references."""
    if material['author_phase'] != 'NODES' or 'plan' not in material or 'evidence_parts_by_unit' not in material:
        return
    parts = material['evidence_parts_by_unit']
    for node in material['plan']['nodes']:
        for u, unit in enumerate(node['units'], 1):
            entries = parts.get(f"{node['node_id']}.u{u}", {})
            sources = [dict(field=entries[f'e{i}']['field'], quote=entries[f'e{i}']['quote'])
                       for i in range(1, len(entries) + 1)]
            evidence = unit['evidence']
            if unpack and type(evidence) is int:
                require(evidence == len(sources) and 1 <= evidence <= 4)
                unit['evidence'] = sources
            elif not unpack and evidence == sources and sources:
                unit['evidence'] = len(sources)


def _relation_fact_references(material, *, unpack=False):
    """The ordered roots and explicit overrides already carry the author's entire unit fact."""
    if material['author_phase'] != 'RELATIONS' or 'fact_part_overrides' not in material:
        return
    overrides = material['fact_part_overrides']
    for node in material.get('candidate_nodes', ()):
        for index, unit in enumerate(node['units'], 1):
            ref = f"{node['node_id']}.u{index}"
            fact = ''.join(overrides.get(f'{ref}.e{i}', root['quote'])
                           for i, root in enumerate(unit['evidence'], 1))
            if unpack and type(unit['fact']) is int:
                require(unit['fact'] == 0 and bool(fact))
                unit['fact'] = fact
            elif not unpack and fact and unit['fact'] == fact:
                unit['fact'] = 0


def _memo_context_menu(material, fields, choice_module, *, version):
    if not material.get('records'):
        return []
    if choice_module is None:
        import analysis_plan_source_choices as choice_module
    source = dict(material, fields=list(fields.values()))
    owners = choice_module.record_plan_owners(source, merge_anchors=True)
    rows = choice_module.merge_action_sources(source, owners, context_sources=True,
                                              distinct_context_sources=version in PAIRED_VERSIONS,
                                              speaker_context_sources=choice_module.uses_speaker_context(version),
                                              attributed_context_sources=choice_module.uses_attributed_context(version))
    return [[row.memo_field, list(group)] for row in rows.values() for group in row.context_groups if group]


# Recurring spelling is a retrieval cue, never a determination that events
# have the same object, actor, conditions, or outcome.
COMPARISON_SKIPS = ('DIFFERENT_SUBJECT', 'INSUFFICIENT_EVIDENCE')
JUDGMENT_CODES = {'対照': 'COMPARE', '同じ依頼の経過': 'FOLLOW_REQUEST',
                  '別件': 'DIFFERENT_SUBJECT', '材料不足': 'INSUFFICIENT_EVIDENCE'}


def comparison_candidates(material):
    if material['author_phase'] != 'RELATIONS' or material.get('map_corrections'):
        return []
    fields = displayed_fields(material)
    by_record = defaultdict(set)
    units = []
    word = re.compile(r'[一-鿿々ァ-ヺー]{2,}|[A-Za-z][A-Za-z0-9-]{2,}')
    for node in material.get('candidate_nodes', []):
        roots = [root for unit in node['units'] for root in unit['evidence']]
        owners = {fields.get(root['field'], {}).get('record') for root in roots}
        if len(owners) != 1 or None in owners:
            continue
        record, = owners
        if any(fields[root['field']].get('source_role') != 'ORIGINAL_INPUT' for root in roots):
            continue
        for index, unit in enumerate(node['units'], 1):
            for root in unit['evidence']:
                field, quote = fields[root['field']], root['quote']
                if (field.get('supplement') is not None or field.get('fragment_is_complete_field') is not True
                        or field.get('field_path') not in ('memo', 'memo_action')
                        or not 2 <= len(quote) <= 160 or quote not in field['text']):
                    continue
                terms = {t for t in word.findall(quote) if 2 <= len(t) <= 32}
                if terms:
                    others = [r['quote'] for r in unit['evidence'] if r is not root]
                    used_cues = {cue for text in others for cue in (text[:16], text[-16:])}
                    cue = next((c for c in (quote[:16], quote[-16:]) if c not in used_cues), None)
                    if cue is None:
                        continue
                    by_record[record].update(terms)
                    units.append((record, node['node_id'], index, root['field'], quote,
                                  field['field_path'] == 'memo_action', cue, terms))
    owners = defaultdict(set)
    for record, terms in by_record.items():
        for term in terms:
            owners[term].add(record)
    pairs = {}
    for left, right in combinations(units, 2):
        if left[0] == right[0] or left[1] == right[1] or left[4] == right[4]:
            continue
        terms = sorted(t for t in left[-1] & right[-1] if len(owners[t]) == 2)
        if not terms:
            continue
        # Require two independent recurring terms for a short commonplace word.
        if len(terms) == 1 and len(terms[0]) < 3:
            continue
        key = (left[1], right[1])
        score = (len(terms), int(left[5])+int(right[5]), sum(min(len(t), 8) for t in terms))
        if key not in pairs or score > pairs[key][0]:
            def endpoint(entry):
                return dict(node=entry[1], unit=f'{entry[1]}.u{entry[2]}', record=entry[0],
                            field=entry[3], quote=entry[4], cue=entry[6])
            pairs[key] = (score, dict(left=endpoint(left), right=endpoint(right), wording=terms[:4]))
    # Bound both the context cost and the number of mandatory author decisions.
    return [pair for _, pair in sorted(pairs.values(), key=lambda item: item[0], reverse=True)[:2]]


# In v6 a lexical overlap can propose reading two passages. A selectable comparison
# needs a recurring subject with a source witness and complete sentences on both ends.
_SUBJECT_WORD = re.compile(r'[一-鿿々ァ-ヺー]{2,}|[A-Za-z][A-Za-z0-9-]{2,}')
_REFERS_BACK = re.compile(r'^(?:前に|前から)|以前|前回|先日|この前|もう一度|引き続き|再び|再度|前述|previously|again', re.I)
_COMPARISON_JOINERS = ('一方、', '別の記録では、')


def _subject_words(text):
    return {w for w in _SUBJECT_WORD.findall(text) if len(w) <= 32}


def _overlap_words(text):
    words = _subject_words(text)
    return words | {w[i:i+2] for w in words if not w.isascii() for i in range(len(w)-1)}


def _label_binds_source(label, origins, peers):
    for quote in origins:
        # Two independent content words, or one distinctive, predicate-bearing
        # source phrase, can ground free prose. A single pasted subject cannot.
        distinctive = {w for w in _subject_words(quote) if w in label and all(w not in p for p in peers)}
        if len(distinctive) >= 2:
            return True
        for run in re.findall(r'[一-鿿々ぁ-ゖァ-ヺー]{8,}',quote):
            for index in range(len(run)-7):
                part = run[index:index+8]
                if (part in label and not any(part in p for p in peers)
                        and re.search(r'[一-鿿々ァ-ヺー]',part)
                        and re.search(r'した|った|いた|えた|めた|けた|れた|ない|なく|せず|ている|られる|たい',part)):
                    return True
        if len(quote)>=4 and quote in label and not any(quote in p for p in peers):
            # A genuinely short complete source sentence still belongs to its author.
            if re.search(r'[。！？.!?]$',quote) and any(w in quote for w in distinctive):
                return True
    return False


def _comparison_record_roots(material, choice_module):
    fields = displayed_fields(material)
    original = {number: f for number, f in fields.items()
        if f.get('source_role') == 'ORIGINAL_INPUT' and f.get('supplement') is None
        and f.get('fragment_is_complete_field') is True and f.get('field_path') in ('memo', 'memo_action')}
    sentences = {i: choice_module._sentences(f['text'], original_for_overview=True) for i, f in original.items()}
    record_sentences = defaultdict(list)
    for number, lines in sentences.items():
        record_sentences[original[number]['record']].extend((number, s, _subject_words(s)) for s in lines
            if 4 <= len(s) <= 160)
    roots = []
    for node in material.get('candidate_nodes', []):
        evidence = [r for u in node['units'] for r in u['evidence']]
        if not evidence or any(r['field'] not in original for r in evidence):
            continue
        owners = {original[r['field']]['record'] for r in evidence}
        if len(owners) != 1:
            continue
        record, = owners
        seen = set()
        for i, unit in enumerate(node['units'], 1):
            for r in unit['evidence']:
                number, quote = r['field'], r['quote']
                if (number, quote) in seen or not 4 <= len(quote) <= 160 or original[number]['text'].count(quote) != 1:
                    continue
                other = {cue for root in unit['evidence'] if root is not r
                         for cue in (root['quote'][:16], root['quote'][-16:])}
                cue = next((s for s in (quote[:16], quote[-16:]) if s not in other), None)
                lines = [s for s in sentences[number] if s in quote and 4 <= len(s) <= 74]
                if cue is None or not lines:
                    continue
                seen.add((number, quote))
                ep = dict(node=node['node_id'], unit=f"{node['node_id']}.u{i}", record=record,
                          field=number, quote=quote, cue=cue, sentences=lines)
                words = _subject_words(quote)
                proofs = {}
                for field, sentence, nearby in record_sentences[record]:
                    # An explicit backward reference names the subject; repeating a transaction verb alone cannot do so.
                    clauses = [c for c in re.split('[、,]',sentence) if _REFERS_BACK.search(c)]
                    if clauses:
                        for w in words & nearby:
                            if re.search(re.escape(w) + r'(?:し[たてなま]|する|せず)', quote):
                                continue
                            if any(w in clause and abs(clause.index(w)-_REFERS_BACK.search(clause).start())<=20 for clause in clauses):
                                proofs.setdefault(w, dict(kind='reference',field=field,quote=sentence))
                    # A missing subject spelling needs its own complete reinforcing sentence joined to the selected
                    # passage by a distinctive content word, e.g. the name of a document or item.
                    if any(len(w) >= 3 and w in sentence for w in words) and sentence not in quote:
                        for w in nearby - words:
                            if re.search(re.escape(w) + r'(?:へ|を|の|が|は|に)', sentence):
                                proofs.setdefault(w,dict(kind='companion',field=field,quote=sentence))
                roots.append((ep, words, _overlap_words(quote), proofs, original[number]['field_path']=='memo_action'))
    return roots


# The same noun may name a participant or a background condition. Compare
# decisions only when both source sentences concern the recurring object or
# independently express the same action. Source text is never synthesized.
_NOMINAL_ACTION = re.compile(r'([一-鿿々]{2,})(?:した|しな|しました|せず|する|を(?:提案|決定|依頼|予定|断念))')


def _candidate_actions(sentence):
    return {term for noun in _NOMINAL_ACTION.findall(sentence)
            for term in (noun, noun[-2:])}


def _request_objects(sentence, actions):
    """Return complete noun modifiers of the requested action, without its recipient."""
    objects = set()
    for action in actions:
        for mention in re.finditer(re.escape(action), sentence):
            noun = re.search(r'([一-鿿々ァ-ヺー]{2,})(?:の)?$', sentence[:mention.start()])
            if noun:
                objects.add(noun[1])
    return objects


def _recurring_object_witness(first_objects, second_objects, endpoints, subject, originals):
    # An object absent from a selected sentence may be grounded in its full
    # original record. Keep the actual wording (including particles) visible.
    for side, objs, ep in (('left', second_objects, endpoints[0]), ('right', first_objects, endpoints[1])):
        for obj in sorted(objs, key=lambda w: (-len(w), w)):
            for number, first, context in originals.get(ep['record'], ()):
                if (subject in context and obj in context.replace('の', '')
                        and (subject in first or obj in first.replace('の', ''))):
                    return dict(side=side, field=number, quote=context, object=obj)
    return None


_REQUEST_VERB = r'(?:依頼|頼[みむんまめも]|申請|発注|注文|照会|問[い合])'
_REQUEST_REFERENCE = r'(?:その|この|同じ)(?:依頼|申請|発注|注文|照会)'


def _request_context(originals, record, obj, recipient):
    """Read the request and its recipient in one clause or an explicit continuation."""
    recipient_to = re.escape(recipient) + r'(?:へ|に)'
    object_name = r'(?:の)?'.join(map(re.escape, obj))
    target = object_name + r'(?:の|を|も|について)?'
    verb = r'(?:もう一度|改めて|直接)?' + _REQUEST_VERB
    requested = re.compile(target + verb)
    addressed = re.compile(r'(?:' + recipient_to + r'(?:の)?' + target + '|' + target + recipient_to + ')' + verb)
    continued = re.compile(_REQUEST_REFERENCE + r'(?:を|は)?' + recipient_to + r'(?:送|伝|渡|' + _REQUEST_VERB + ')')
    for field, first, span in originals.get(record, ()):
        if addressed.search(first):
            return dict(field=field, quote=first)
        following = span[len(first):]
        if requested.search(first) and '\n\n' not in following and continued.search(following):
            return dict(field=field, quote=span)
    return None


def _requested_subject(left_objects, right_objects, endpoints, recipient, originals):
    """A shared addressee qualifies only when both records actually request the same item."""
    def names_item(obj, terms, witness):
        # A common final character in e.g. two document names cannot identify a document.
        # A more general name can be bound by a literal modifier and its noun head in the record.
        for term in terms:
            if term == obj or (len(term) >= 2 and obj.endswith(term)):
                return True
            for split in range(1, len(obj)):
                modifier, head = obj[:split], obj[split:]
                if term.startswith(head) and modifier + 'の' + head in witness['quote']:
                    return True
        return False

    for obj in sorted(left_objects | right_objects, key=lambda word: (-len(word), word)):
        left, right = (_request_context(originals, ep['record'], obj, recipient) for ep in endpoints)
        if left and right and names_item(obj, left_objects, left) and names_item(obj, right_objects, right):
            return dict(object=obj, kind='requested_object', recipient=recipient, left=left, right=right)
    return None


def _decision_endpoints(row, originals, *, named_requests=False):
    subject = row['subject']
    endpoints = row['left'], row['right']
    direct_object = tuple(subject + suffix for suffix in ('を', 'について', 'に対し'))
    recipient = tuple(subject + suffix for suffix in ('へ', 'に'))
    candidates = []
    for first in endpoints[0]['sentences']:
        for second in endpoints[1]['sentences']:
            direct = [any(term in s for term in direct_object) for s in (first, second)]
            if row['subject_witness']['kind'] == 'same_phrase':
                if all(direct):
                    candidates.append((first, second, None))
                continue
            shared = _overlap_words(first) & _overlap_words(second)
            actions = {a for a in (_candidate_actions(first) | _candidate_actions(second)) & shared
                       if a not in subject}
            if not actions:
                continue
            bound_actions = {action for action in actions if any(
                re.search(re.escape(term) + r'[^、。をが]{0,12}' + re.escape(action), sentence)
                for sentence in (first, second) for term in direct_object)}
            if bound_actions:
                explicit_objects = {m[1] for action in bound_actions for sentence in (first, second)
                                    for m in re.finditer(r'([一-鿿々ァ-ヺー]{2,})を' + re.escape(action), sentence)}
                if explicit_objects <= {subject}:
                    candidates.append((first, second, None))
            elif any(term in s for term in recipient for s in (first, second)):
                left_objects, right_objects = (_request_objects(s, actions) for s in (first, second))
                if not left_objects or not right_objects:
                    continue
                witness_for = _requested_subject if named_requests else _recurring_object_witness
                witness = witness_for(left_objects, right_objects, endpoints, subject, originals)
                if witness:
                    candidates.append((first, second, witness))
    # Keep the authorized pairings, including when two unrelated operations
    # occur in the same selected passage. Sentence numbers refer to the exact
    # source sentences shown in this request.
    if not candidates:
        return None
    if named_requests and any(w for _, _, w in candidates):
        topics = {w['object'] for _, _, w in candidates if w}
        if len(topics) != 1:
            return None
        candidates = [(first, second, w) for first, second, w in candidates if w]
    left = list(dict.fromkeys(first for first, _, _ in candidates))
    right = list(dict.fromkeys(second for _, second, _ in candidates))
    result = dict(row, left=dict(row['left'], sentences=left), right=dict(row['right'], sentences=right),
                  decision_pairs=[[left.index(first) + 1, right.index(second) + 1]
                                  for first, second, _ in candidates])
    witnesses = [w for _, _, w in candidates if w]
    if witnesses and named_requests:
        # One pair of original passages supports the shared object for every offered sentence pair.
        witness = dict(witnesses[0])
        result['subject'] = witness.pop('object')
        result['subject_witness'] = witness
    elif witnesses:
        result['object_witnesses'] = list({compact_json(w): w for w in witnesses}.values())
    return result


def _comparison_originals(material, choice_module):
    originals = defaultdict(list)
    for number, field in displayed_fields(material).items():
        if (field.get('source_role') != 'ORIGINAL_INPUT' or field.get('supplement') is not None
                or field.get('fragment_is_complete_field') is not True
                or field.get('field_path') not in ('memo', 'memo_action')):
            continue
        sentences = choice_module._sentences(field['text'], original_for_overview=True)
        cursor = 0
        previous = None
        for sentence in sentences:
            start = field['text'].find(sentence, cursor)
            if start < 0:
                continue
            end = start + len(sentence)
            if len(sentence) <= 160:
                originals[field['record']].append((number, sentence, sentence))
            if previous is not None:
                prior_start, prior_end, prior_sentence = previous
                if end-prior_start <= 160 and not field['text'][prior_end:start].strip():
                    originals[field['record']].append((number, prior_sentence, field['text'][prior_start:end]))
            previous = start, end, sentence
            cursor = end
    return originals


# Require the selected predicate to finish its own clause. A proposed request
# may still be unsent, and receiving news need not mean the author replied.
_STATED_CLAUSE = r'(?=$|[。．.!！]|[、,](?!\s*と(?:仮定|想定))|(?:が|けれど(?:も)?|ものの)(?:[、,]|(?=[一-鿿々])))'
_DID = r'(?:した|しました|し(?=[、,]))'
_REQUEST_INITIATED = re.compile(
    r'(?:(?:依頼|申請|発注|注文|照会|問い合わせ|申込)(?:を|することを)?'
    r'(?:(?:提案|打診|検討|相談|予定)(?:を)?' + _DID + r'|したい)'
    r'|(?:頼み|申し込み)たい(?:と(?:提案|相談)' + _DID + r')?)' + _STATED_CLAUSE)
_REQUEST_UPDATE = re.compile(
    r'(?:連絡|回答|返事|返答|知らせ|報告)(?:が(?:あった|ありました|来た|来ました|届いた|届きました|(?:あり|届き)(?=[、,]))'
    r'|を(?:受け(?:取った|取りました|た|ました)|聞いた|聞きました|読んだ|読みました|返した|返しました|(?:受け|受け取り|聞き|読み|返し)(?=[、,]))'
    r'|に(?:(?:返事|回答|返答)(?:を)?' + _DID + r'|応え(?:た|ました|(?=[、,]))))' + _STATED_CLAUSE)
_DIFFERENT_REQUEST = re.compile(r'別件|別の(?:依頼|案件|申請|注文|見積り)|無関係な')


def _request_progress_options(row, days):
    """Offer an authored trace only between dated records with supported request and update passages."""
    witness = row['subject_witness']
    if witness['kind'] != 'requested_object':
        return []
    left_day, right_day = (days.get(row[side]['record']) for side in ('left', 'right'))
    if left_day is None or right_day is None or left_day >= right_day:
        return []
    if any(_DIFFERENT_REQUEST.search(witness[side]['quote']) for side in ('left', 'right')):
        return []
    options = []
    # Reuse the same source-bound, distinct sentences that qualify for a comparison.
    pairs = dict.fromkeys((action[2], action[4]) for action, _ in paired_decisions(row))
    for li, ri in pairs:
        first, second = row['left']['sentences'][li - 1], row['right']['sentences'][ri - 1]
        if (_REQUEST_INITIATED.search(first) and _REQUEST_UPDATE.search(second)
                and not any(_DIFFERENT_REQUEST.search(sentence) for sentence in (first, second))
                and len(first + '後の記録では、' + second) <= 80):
            options.append(['FOLLOW_REQUEST', row['subject'], li, '後の記録では、', ri])
    return options


def _record_days(material):
    days = {}
    for field in material.get('records', ()):
        try:
            days[field['record']] = date.fromisoformat(field['recorded_at'][:10])
        except (KeyError, TypeError, ValueError):
            continue
    return days


def paired_comparison_candidates(material, choice_module, *, limit=2, decision_sources=False, named_requests=False, request_progress=False):
    if material['author_phase'] != 'RELATIONS' or material.get('map_corrections'):
        return []
    if choice_module is None:
        import analysis_plan_source_choices as choice_module
    originals = _comparison_originals(material, choice_module) if decision_sources else {}
    days = _record_days(material) if request_progress else {}
    roots = _comparison_record_roots(material, choice_module)
    owners = defaultdict(set)
    for ep, _, terms, _, _ in roots:
        for term in terms:
            owners[term].add(ep['record'])
    pairs = {}
    for left, right in combinations(roots, 2):
        a, aw, at, ap, action_a = left
        b, bw, bt, bp, action_b = right
        if a['record'] == b['record'] or a['quote'] == b['quote']:
            continue
        overlap = {t for t in at & bt if len(owners[t]) <= 3}
        if not overlap:
            continue
        anchors = []
        for ep, direct, proof, other_words, side in ((a, aw, ap, bw, 'left'), (b, bw, bp, aw, 'right')):
            for word in sorted(proof.keys() & other_words):
                witness = proof[word]
                other = b if side == 'left' else a
                if re.search(re.escape(word) + r'(?:し[たてなま]|する|せず)', other['quote']):
                    continue
                if witness['kind']=='companion' and (word in direct or word in overlap):
                    continue
                if witness['kind']=='reference' and word not in overlap:
                    continue
                anchors.append((2 if witness['kind']=='reference' else 1,word,side,witness))
        for phrase in sorted(set(re.findall(r'[一-鿿々ァ-ヺー]{2,}の[一-鿿々ァ-ヺー]{2,}|[A-Za-z]+[-0-9][A-Za-z0-9-]*', a['quote']))):
            if phrase in b['quote']:
                anchors.append((3,phrase,'right',dict(kind='same_phrase',field=b['field'],quote=b['quote'])))
        for strength, word, side, witness in anchors:
            if not any(len(x)+len(y)+3 <= 80 for x in a['sentences'] for y in b['sentences']):
                continue
            row = dict(left=a,right=b,subject=word,subject_witness=dict(side=side,**witness),wording=sorted(overlap))
            if decision_sources:
                row = _decision_endpoints(row, originals, named_requests=named_requests)
                if row is None:
                    continue
            if request_progress:
                progress = _request_progress_options(row, days)
                if progress:
                    row['request_progress_choices'] = progress
            allowed = paired_decisions(row)
            if not allowed:
                continue
            # Prioritize specific recurring subjects over transaction words and complete action passages over mentions.
            score = (strength, int(action_a)+int(action_b), sum(len(t) for t in (aw&bw) if t in overlap),
                     sum(word in ep['quote'] for ep in (a,b)),len(word))
            key = (a['node'],b['node'])
            if key not in pairs or score>pairs[key][0]:
                pairs[key]=(score,row)
    return [row for _,row in sorted(pairs.values(),key=lambda item:item[0],reverse=True)[:limit]]


def paired_decisions(candidate):
    left, right = candidate['left'],candidate['right']
    topic = candidate['subject']
    relevant = (topic,*candidate['wording'])
    progress = candidate.get('request_progress_choices', ())
    if 'judgment_choices' in candidate:
        progress = [['FOLLOW_REQUEST', *choice[1:]] for choice in candidate['judgment_choices'] if choice[0] == '同じ依頼の経過']
    options = [(action, left['sentences'][action[2] - 1] + action[3] + right['sentences'][action[4] - 1])
               for action in progress]
    for li, first in enumerate(left['sentences'],1):
        for ri, second in enumerate(right['sentences'],1):
            if 'decision_pairs' in candidate and [li, ri] not in candidate['decision_pairs']:
                continue
            if (first in second or second in first or not (topic in first or topic in second)
                    or not any(t in first and t in second for t in relevant)):
                continue
            # Each selected sentence must contribute source wording absent from the other endpoint.
            if first in right['quote'] or second in left['quote']:
                continue
            for join in _COMPARISON_JOINERS:
                label = first + join + second
                if len(label) <= 80:
                    options.append((['COMPARE',topic,li,join,ri],label))
    return options


def _judgment_candidate(row, days):
    # Every answer names the same subject and an authorized pair of original sentences.
    # Choosing to omit a line retains the exact material the author has reviewed.
    decisions = [action for action, _ in paired_decisions(row)]
    names = {code: text for text, code in JUDGMENT_CODES.items()}
    choices = [[names[action[0]], *action[1:]] for action in decisions]
    pairs = dict.fromkeys((action[2], action[4]) for action in decisions)
    choices.extend([names[code], row['subject'], li, '線なし', ri]
                   for li, ri in pairs for code in COMPARISON_SKIPS)
    result = dict(row, judgment_choices=choices)
    result.pop('request_progress_choices', None)
    for side in ('left', 'right'):
        ep = row[side]
        day = days.get(ep['record'])
        result[side] = dict(ep, recorded_on=day.isoformat() if day is not None else None)
    return result


def comparison_endpoints(candidate):
    left, right = candidate['left'], candidate['right']
    return {'from': left['node'], 'to': right['node'], 'from_unit': left['unit'], 'to_unit': right['unit'],
            'from_source': left['cue'], 'to_source': right['cue']}


def _comparison_source_pair(edge):
    return tuple((edge.get(side), edge.get(side + '_unit'), edge.get(side + '_source'))
                 for side in ('from', 'to'))


def _comparison_sources(candidate, decision):
    # Root identity keeps overlapping quotations from widening the chosen sentence.
    return tuple((endpoint['field'], endpoint['quote'], endpoint['sentences'][position - 1])
                 for endpoint, position in ((candidate['left'], decision[2]), (candidate['right'], decision[4])))


def prepare_messages(messages, *, version=VERSION, choice_module=None):
    material = json.loads(messages[1]['content'])
    if isinstance(material, dict):
        require(not WIRE_FIELDS.intersection(material) and not {'comparison_candidates', 'memo_context_choices'}.intersection(material))
    if not eligible(material):
        return messages
    require(compact_json(material) == messages[1]['content'])
    comparisons = (paired_comparison_candidates(material, choice_module, decision_sources=version in DECISION_VERSIONS,
                                                named_requests=version in REQUEST_SUBJECT_VERSIONS,
                                                request_progress=version in REQUEST_PROGRESS_VERSIONS) if version in PAIRED_VERSIONS
                   else comparison_candidates(material) if version == COMPARISON_VERSION else [])
    fields = displayed_fields(material)
    if version in COMPARISON_VERSIONS and material['author_phase'] == 'PLAN':
        menu = _memo_context_menu(material, fields, choice_module, version=version)
        if menu:
            material['memo_context_choices'] = menu
    material['leaf_source_index'] = pack_index(material['leaf_source_index'], fields)
    material['field_manifest'] = pack_manifest(material['field_manifest'], fields)
    if version in OUTPUT_VERSIONS:
        _node_plan_references(material)
        _relation_fact_references(material)
        _visible_sources(material, fields)
        _range_lengths(material)
    if comparisons:
        if version == JUDGMENT_VERSION:
            days = _record_days(material)
            comparisons = [_judgment_candidate(row, days) for row in comparisons]
        material['comparison_candidates'] = comparisons
    material['merge_wire_version'] = version
    material['merge_original_messages_sha256'] = messages_digest(messages)
    return [dict(messages[0], content=messages[0]['content'] + instruction(version, material['author_phase'])),
            dict(messages[1], content=compact_json(material))]


def legacy_messages(messages, *, choice_module=None):
    try:
        material = json.loads(messages[1]['content'])
        require(eligible(material))
        version = material.pop('merge_wire_version', None)
        suffix = instruction(version, material['author_phase'])
        binding = material.pop('merge_original_messages_sha256')
        if version in COMPARISON_VERSIONS:
            material.pop('comparison_candidates', None)  # Canonical round-trip below checks the whole table.
        require(messages[0]['content'].endswith(suffix))
        if version in COMPARISON_VERSIONS and material['author_phase'] == 'PLAN':
            material.pop('memo_context_choices', None)
        fields = displayed_fields(material)
        material['leaf_source_index'] = unpack_index(material['leaf_source_index'], fields)
        material['field_manifest'] = unpack_manifest(material['field_manifest'], fields)
        if version in OUTPUT_VERSIONS:
            _range_lengths(material, unpack=True)
            _visible_sources(material, fields, unpack=True)
            _node_plan_references(material, unpack=True)
            _relation_fact_references(material, unpack=True)
        result = [dict(messages[0], content=messages[0]['content'][:-len(suffix)]),
                  dict(messages[1], content=compact_json(material))]
        require(messages_digest(result) == binding)
        # Ensure the sender used the canonical representation, including the menu layout.
        require(prepare_messages(result, version=version, choice_module=choice_module) == messages)
        return result
    except (KeyError, TypeError, IndexError) as exc:
        raise ValueError('analysis_merge_wire_invalid') from exc


def _quote_codes(literals):
    """Visible beginnings and endings identify one complete source value in this request."""
    from collections import Counter

    literals = set(literals)
    # An original tilde is escaped, so even literal text resembling a code is unambiguous.
    result = {s: ('~' + s if s.startswith('~') else s) for s in literals}
    longer = [s for s in literals if len(s) > 8]
    pending = set(longer)
    for width in (2, 3, 4, 6, 8, 12):
        if not pending:
            break
        codes = {s: '~' + s[:width] + '…' + s[-width:] for s in pending}
        counts = Counter(codes.values())
        for source, code in codes.items():
            if counts[code] == 1 and len(code) < len(source) and not code.startswith('~~'):
                result[source] = code
                pending.remove(source)
    require(len(set(result.values())) == len(result))
    return result


class ResponseCodec:
    """Project only deterministic positions. Every authored choice remains in the raw receipt."""
    def __init__(self, material, choice_module, fact_key, *, comparisons=(), paired=False, decision_sources=False, named_requests=False, request_progress=False):
        self._decision_sources = decision_sources
        self._named_requests = named_requests
        self._request_progress = request_progress
        self.paired_material = material if paired and material['author_phase'] == 'RELATIONS' else None
        self._comparison_source_module = choice_module
        self._extra_comparisons = None
        self._owners = {}
        self._unit_evidence = {}
        if self.paired_material is not None:
            fields = displayed_fields(material)
            for node in material.get('candidate_nodes',[]):
                for index,unit in enumerate(node['units'],1):
                    self._unit_evidence[(node['node_id'],f"{node['node_id']}.u{index}")] = tuple(r['quote'] for r in unit['evidence'])
                self._owners[node['node_id']] = {fields.get(r['field'],{}).get('record')
                    for u in node['units'] for r in u['evidence']}
        self.paired = paired
        self.paired_choices = [paired_decisions(c) for c in comparisons] if paired else []
        self.comparisons = comparisons
        self.judgments = [row['judgment_choices'] for row in comparisons if 'judgment_choices' in row]
        self.comparison_endpoints = tuple(comparison_endpoints(c) for c in comparisons)
        pairs = tuple(_comparison_source_pair(edge) for edge in self.comparison_endpoints)
        self._reserved_source_pairs = pairs + tuple(pair[::-1] for pair in pairs)
        self.comparison_skips = COMPARISON_SKIPS
        self.phase = material['author_phase']
        self.primary_structure_reading = material.get('primary_structure_reading') in ('karen.v1', 'karen.v2')
        self.plan_units = ()
        self.qualification_items = ()
        if self.phase == 'PLAN':
            _, aliases, allowed = choice_module.restore_view(material)
            assigned = {(field, quote) for (field, _), quote in aliases.items()}
            literals = {quote for field, texts in allowed.items() for quote in texts
                        if (field, quote) not in assigned}
            literals.update(alias for _, alias in aliases)
            self.binding = material['source_choices_sha256']
        elif self.phase == 'NODES':
            plan = material['plan']
            self.binding = messages_digest(['analysis.node-facts.v1', 'NODES', material['fact_source_request_ref'], plan])
            self.plan_units = tuple(tuple(tuple(fact_key(unit['evidence'], i)
                for i in range(len(unit['evidence']))) for unit in node['units']) for node in plan['nodes'])
            literals = set()
            for node in plan['nodes']:
                for unit in node['units']:
                    for root in unit['evidence']:
                        quote = root['quote']
                        literals.add(quote)
                        # Shorten common bound qualifications. Other valid original literals
                        # retain their complete spelling and pass through the same admission.
                        _, parts = choice_module.choices_for_field(dict(text=quote, source_role='ORIGINAL_INPUT'))
                        literals.update(parts)
        elif self.phase == 'RELATIONS':
            self.binding = messages_digest(material['candidate_nodes'])
            candidates = material['qualification_candidates']
            # Request serialization can place q10 before q2. The authored NODES
            # registry numbers qualifications by node, unit and unknown ordinal.
            numbered = sorted(candidates, key=lambda ref: int(ref.partition('/')[0][1:]))
            require(all(ref.startswith(f'q{i}/') for i, ref in enumerate(numbered, 1)))
            self.qualification_items = tuple((ref, candidates[ref]['source_quote']) for ref in numbered)
            literals = set()
            for _, source in self.qualification_items:
                _, parts = choice_module.choices_for_field(dict(text=source, source_role='ORIGINAL_INPUT'))
                literals.update(parts)
                literals.add(source)
        else:
            raise ValueError('analysis_merge_wire_phase_invalid')
        self._codes = _quote_codes(literals)
        self.quotes = {code: quote for quote, code in self._codes.items()}

    def quote_code(self, quote):
        require(type(quote) is str)
        return self._codes.get(quote, '~' + quote if quote.startswith('~') else quote)

    def _quote(self, code):
        require(type(code) is str)
        if code in self.quotes:
            return self.quotes[code]
        require(self.phase in ('NODES', 'RELATIONS'))
        original = code[1:] if code.startswith('~~') else code
        require(self.quote_code(original) == code)
        return original

    def _root(self, pair, *, qualification=False):
        require(type(pair) is list and len(pair) == 2 and type(pair[1]) is int)
        q, field = self._quote(pair[0]), pair[1]
        return dict(source_quote=q, source_field=field) if qualification else dict(quote=q, field=field)

    @staticmethod
    def paired_kind(action):
        return 'SHARED_MEANING' if action[0] == 'FOLLOW_REQUEST' else 'CONTEXT_CONTRAST'

    def _extra_pair_choices(self, endpoint_key):
        if self._extra_comparisons is None:
            # Unoffered supported pairs remain available through the ordinary edge array.
            # The two explicit author decisions may not be contradicted or duplicated here.
            offered = {frozenset((row['left']['node'],row['right']['node'])) for row in self.comparisons}
            self._extra_comparisons = {}
            extra = paired_comparison_candidates(self.paired_material, self._comparison_source_module, limit=None,
                decision_sources=self._decision_sources, named_requests=self._named_requests, request_progress=self._request_progress)
            for row in extra:
                if frozenset((row['left']['node'],row['right']['node'])) in offered:
                    continue
                reverse = dict(row, left=row['right'], right=row['left'])
                if 'decision_pairs' in row:
                    reverse['decision_pairs'] = [[right, left] for left, right in row['decision_pairs']]
                if row.get('request_progress_choices'):
                    reverse['request_progress_choices'] = [[action, subject, ri, '先の記録では、', li]
                        for action, subject, li, _, ri in row['request_progress_choices']]
                for candidate in (row, reverse):
                    key = tuple(comparison_endpoints(candidate).values())
                    choices = {
                        (self.paired_kind(decision), label): _comparison_sources(candidate, decision) if self._decision_sources else None
                        for decision, label in paired_decisions(candidate)}
                    self._extra_comparisons[key] = (choices, candidate['subject_witness']['kind'] == 'requested_object')
        return self._extra_comparisons.get(endpoint_key, ({}, False))

    def free_comparisons_allowed(self, edges, *, comparison_sources=None):
        if self.paired_material is None:
            return True
        for edge in edges:
            if any(type(edge.get(key)) is not str for key in ('from','to','label')):
                return False
            # The explicit decision owns these exact source choices in either direction.
            if self._request_progress and _comparison_source_pair(edge) in self._reserved_source_pairs:
                return False
            l = self._owners.get(edge.get('from'),set())
            r = self._owners.get(edge.get('to'),set())
            if not l or not r or l & r or None in l or None in r:
                continue
            kind = edge.get('relation_kind')
            label = edge['label']
            progress_label = (self._request_progress and kind == 'SHARED_MEANING'
                              and any(join in label for join in ('後の記録では、', '先の記録では、')))
            if kind == 'CONTEXT_CONTRAST' or progress_label:
                key = tuple(edge.get(k) for k in ('from','to','from_unit','to_unit','from_source','to_source'))
                if not all(type(x) is str for x in key):
                    return False
                choices, named_request = self._extra_pair_choices(key)
                # Other freely authored relations still use the ordinary two-source check below.
                if kind == 'CONTEXT_CONTRAST' or named_request:
                    if (kind, label) not in choices:
                        return False
                    if self._decision_sources and comparison_sources is not None:
                        comparison_sources[(edge['from_unit'], edge['to_unit'], label)] = choices[(kind, label)]
                    continue
            # Every additional cross-record relation must identify something
            # distinctive from the selected quotation at each endpoint. The
            # author still chooses the relation kind and writes the full label.
            sources = []
            for side in ('from','to'):
                unit, cue = edge.get(side+'_unit'), edge.get(side+'_source')
                if not isinstance(unit,str) or not isinstance(cue,str):
                    return False
                quotes = self._unit_evidence.get((edge[side],unit),())
                sources.append(tuple(q for q in quotes if cue in (q[:16],q[-16:])))
            if not all(_label_binds_source(label,origins,sources[1-side]) for side,origins in enumerate(sources)):
                return False
        return True

    def _relation_values(self, value, *, unpack, comparison_decisions=None, comparison_sources=None):
        keys = {'schema_version', 'nodes_sha256', 'qualification_review', 'edges', 'overview'}
        if self.primary_structure_reading and type(value) is dict and 'primary_structures' in value:
            keys.add('primary_structures')
        if self.comparisons and unpack:
            keys.add('comparisons')
        require(type(value) is dict and set(value) == keys and value['nodes_sha256'] == self.binding
                and value['schema_version'] == MODEL_SCHEMA + '.relations')
        source = value['qualification_review']
        closed = ('STATED', 'EARLIER', 'DUPLICATE')
        if unpack:
            require(type(source) is list and len(source) == len(self.qualification_items))
            review = {}
            for (key, original), choice in zip(self.qualification_items, source, strict=True):
                if type(choice) is str:
                    require(choice in closed)
                    review[key] = dict(status=choice)
                else:
                    require(type(choice) is list and len(choice) == 1)
                    ref = choice[0]
                    if type(ref) is int:
                        require(ref == 0)
                        quote = original
                    else:
                        quote = self._quote(ref)
                        require(quote != original)
                    review[key] = dict(status='OPEN', source_quote=quote)
        else:
            require(type(source) is dict and set(source) == {key for key, _ in self.qualification_items})
            review = []
            for key, original in self.qualification_items:
                item = source[key]
                require(type(item) is dict)
                if set(item) == {'status', 'source_quote'} and item['status'] == 'OPEN':
                    quote = item['source_quote']
                    review.append([0 if quote == original else self.quote_code(quote)])
                else:
                    require(set(item) == {'status'} and item['status'] in closed)
                    review.append(item['status'])
        edges = value['edges']
        if self.paired and unpack:
            require(type(edges) is list and all(type(edge) is dict for edge in edges)
                    and self.free_comparisons_allowed(edges, comparison_sources=comparison_sources))
        result = dict(schema_version=value['schema_version'], nodes_sha256=self.binding, qualification_review=review)
        if comparison_decisions is not None:
            require(not unpack and self.comparisons and type(comparison_decisions) is list
                    and len(comparison_decisions) == len(self.comparisons))
        if self.comparisons:
            require(type(edges) is list)
            bindings = self.comparison_endpoints
            if unpack:
                decisions = value['comparisons']
                require(type(decisions) is list and len(decisions) == len(bindings))
                authored = []
                for index,(decision,endpoints) in enumerate(zip(decisions, bindings, strict=True)):
                    if type(decision) is str:
                        require(decision in COMPARISON_SKIPS)
                    elif self.paired:
                        label = next((label for action,label in self.paired_choices[index]
                                      if compact_json(action)==compact_json(decision)),None)
                        require(label is not None)
                        authored.append(dict(endpoints,label=label,relation_kind=self.paired_kind(decision)))
                        if self._decision_sources and comparison_sources is not None:
                            key = (endpoints['from_unit'], endpoints['to_unit'], label)
                            comparison_sources[key] = _comparison_sources(self.comparisons[index], decision)
                    else:
                        require(type(decision) is list and len(decision) == 3 and decision[0] == 'COMPARE')
                        authored.append(dict(endpoints, label=decision[1], relation_kind=decision[2]))
                # A skipped or already authored pair cannot be reintroduced
                # with exactly those same source choices in the free array.
                for edge in edges:
                    require(type(edge) is dict and _comparison_source_pair(edge) not in self._reserved_source_pairs)
                edges = authored + edges
            else:
                result['comparisons'] = []
                edges = list(edges)
                for index, endpoints in enumerate(bindings):
                    if edges and all(edges[0].get(k) == v for k, v in endpoints.items()):
                        edge = edges.pop(0)
                        if self.paired:
                            action = next((a for a,label in self.paired_choices[index] if edge['label']==label
                                           and edge['relation_kind']==self.paired_kind(a)),None)
                            require(action is not None)
                            result['comparisons'].append(action)
                        else:
                            result['comparisons'].append(['COMPARE', edge['label'], edge['relation_kind']])
                    else:
                        skip = 'INSUFFICIENT_EVIDENCE' if comparison_decisions is None else comparison_decisions[index]
                        require(type(skip) is str and skip in COMPARISON_SKIPS)
                        result['comparisons'].append(skip)
                if comparison_decisions is not None:
                    require(result['comparisons'] == comparison_decisions)
        result.update(edges=edges, overview=value['overview'])
        if 'primary_structures' in value:
            result['primary_structures'] = value['primary_structures']
        return result

    def judgment_decision(self, index, choice):
        # JSON scalar types matter here: true is not sentence one.
        require(any(compact_json(item) == compact_json(choice) for item in self.judgments[index]))
        code = JUDGMENT_CODES[choice[0]]
        return code if code in COMPARISON_SKIPS else [code, *choice[1:]]

    def decode(self, raw, *, comparison_sources=None):
        if self.phase == 'RELATIONS':
            if self.judgments:
                decisions = raw.get('comparisons') if type(raw) is dict else None
                require(type(decisions) is list and len(decisions) == len(self.judgments))
                raw = dict(raw, comparisons=[self.judgment_decision(i, choice) for i, choice in enumerate(decisions)])
            return self._relation_values(raw, unpack=True, comparison_sources=comparison_sources)
        require(type(raw) is dict and set(raw) == {'h', 'n'} and raw['h'] == self.binding
                and type(raw['n']) is list)
        version = MODEL_SCHEMA + '.' + self.phase.lower()
        if self.phase == 'PLAN':
            nodes = []
            require(1 <= len(raw['n']) <= 12)
            for n, row in enumerate(raw['n'], 1):
                require(type(row) is list and 1 <= len(row) <= 2)
                units = []
                for unit in row:
                    require(type(unit) is list and 1 <= len(unit) <= 4)
                    units.append(dict(evidence=[self._root(pair) for pair in unit]))
                nodes.append(dict(node_id=f'n{n}', units=units))
            return dict(schema_version=version, source_choices_sha256=self.binding, nodes=nodes)
        require(len(raw['n']) == len(self.plan_units))
        nodes = {}
        for n, (row, layout) in enumerate(zip(raw['n'], self.plan_units, strict=True), 1):
            require(type(row) is list and len(row) == 5 and type(row[0]) is list and len(row[0]) == len(layout))
            entries, kind, perspective, title, meaning = row
            units = {}
            for u, (entry, keys) in enumerate(zip(entries, layout, strict=True), 1):
                require(type(entry) is list and len(entry) == 3)
                mode, parts, unknowns = entry
                require(type(parts) is list and len(parts) == len(keys) and type(unknowns) is list
                        and len(unknowns) <= 2)
                units[f'u{u}'] = dict(evidence_ref=f'n{n}.u{u}', source_mode=mode,
                    fact_parts=dict(zip(keys, parts, strict=True)),
                    unknowns=[self._root(pair, qualification=True) for pair in unknowns])
            nodes[f'n{n}'] = dict(units=units, node_kind=kind, perspective=perspective, title=title, meaning=meaning)
        return dict(schema_version=version, plan_sha256=self.binding, nodes=nodes)

    def encode(self, value, *, comparison_decisions=None):
        """Inverse, used to check that no model selection is lost in a physical response."""
        if self.phase == 'RELATIONS':
            selected = comparison_decisions
            if self.judgments and selected is not None:
                require(type(selected) is list and len(selected) == len(self.judgments))
                selected = [self.judgment_decision(i, choice) for i, choice in enumerate(selected)]
            raw = self._relation_values(value, unpack=False, comparison_decisions=selected)
            if self.judgments:
                raw['comparisons'] = comparison_decisions if comparison_decisions is not None else [
                    next(choice for choice in self.judgments[i] if self.judgment_decision(i, choice) == decision)
                    for i, decision in enumerate(raw['comparisons'])]
            require(messages_digest(self.decode(raw)) == messages_digest(value))
            return raw
        require(comparison_decisions is None)
        if self.phase == 'PLAN':
            rows = [[[[self.quote_code(root['quote']), root['field']] for root in unit['evidence']]
                      for unit in node['units']] for node in value['nodes']]
        else:
            rows = []
            for n, layout in enumerate(self.plan_units, 1):
                node = value['nodes'][f'n{n}']
                entries = []
                for u, keys in enumerate(layout, 1):
                    unit = node['units'][f'u{u}']
                    entries.append([unit['source_mode'], [unit['fact_parts'][k] for k in keys],
                        [[self.quote_code(q['source_quote']), q['source_field']] for q in unit['unknowns']]])
                rows.append([entries, node['node_kind'], node['perspective'], node['title'], node['meaning']])
        raw = dict(h=self.binding, n=rows)
        # Canonical JSON also distinguishes booleans from identically valued integers.
        require(messages_digest(self.decode(raw)) == messages_digest(value))
        return raw


def response_codec(messages, *, choice_module=None, fact_key=None):
    """Construct a request-local v3 output view after checking the logical message binding."""
    if not is_compact(messages):
        return None
    material = json.loads(messages[1]['content'])
    if material['merge_wire_version'] not in OUTPUT_VERSIONS:
        return None
    logical = json.loads(legacy_messages(messages, choice_module=choice_module)[1]['content'])
    if choice_module is None:
        import analysis_plan_source_choices as choice_module
    if logical['author_phase'] == 'NODES' and fact_key is None:
        from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import _semantic_fact_part_key
        fact_key = _semantic_fact_part_key
    comparisons = material.get('comparison_candidates', ()) if material['merge_wire_version'] in COMPARISON_VERSIONS else ()
    return ResponseCodec(logical, choice_module, fact_key, comparisons=comparisons,
                         paired=material['merge_wire_version'] in PAIRED_VERSIONS,
                         decision_sources=material['merge_wire_version'] in DECISION_VERSIONS,
                         named_requests=material['merge_wire_version'] in REQUEST_SUBJECT_VERSIONS,
                         request_progress=material['merge_wire_version'] in REQUEST_PROGRESS_VERSIONS)
