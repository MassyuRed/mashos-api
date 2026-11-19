"""Private inference server for the existing local Qwen3.5-4B cache.

The default remains the bounded personal connection probe.  The explicit
--analysis-service mode serves the ordinary Analysis route until stopped,
with its own output/context/time budgets. No training, downloads, provider
fallback, or automatic request retry occur in either mode.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager, nullcontext
from functools import lru_cache
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.metadata import version
import json
import logging
import os
from pathlib import Path
import re
import signal
import threading
import time

MODEL = "Qwen/Qwen3.5-4B"
REVISION = "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"
FIT38_WEIGHTS = "ad8b89e8974df9bfe7e804b8f67bbaac59e6cbb37042c3254fb58ffb64230d0a"
FIT38_CONFIG = "ef4b1aef621fb4e234ce6a05601efb62a987c3cf5d40f3995ca1b72200bab145"
PINS = {"transformers": "5.19.0", "peft": "0.21.2", "accelerate": "1.15.0", "safetensors": "0.8.0"}
SEMANTIC_FORMAT_SOURCE = '817f944fcc8851917c40300a47f62d1defc3ffc3'
PIECE_CANDIDATE_FORMAT = 'piece.field_slots.v1'
EVENT_PLAN_SCHEMA = 'cocolon.analysis.semantic_map.event_plan.model.v1'
EVENT_PLAN_V2_SCHEMA = 'cocolon.analysis.semantic_map.event_plan.model.v2'
EVENT_PLAN_V2_MODEL = 'cocolon-qwen3.5-4b-analysis-event-plan-v2'
EVENT_PLAN_V2_BASE_MODEL = 'cocolon-qwen3.5-4b-analysis-event-plan-v2-base-851bf6e'
NODE_LOCAL_V3_SCHEMA = 'cocolon.analysis.semantic_map.node_local.model.v3'
NODE_LOCAL_V4_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4'
NODE_LOCAL_V4_BOUND_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-bound-roots'
NODE_LOCAL_V4_BOUND_PROFILE = 'semantic_map.node_local.v4.bound_roots.v1'
OCCURRENCE_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v1'
OCCURRENCE_PROFILE = 'semantic_map.node_local.v4.occurrence.v1'
OCCURRENCE_V2_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v2'
OCCURRENCE_V2_PROFILE = 'semantic_map.node_local.v4.occurrence.v2'
OCCURRENCE_V3_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v3'
OCCURRENCE_V4_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v4'
OCCURRENCE_V5_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v5'
OCCURRENCE_V6_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v6'
OCCURRENCE_V7_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v7'
OCCURRENCE_V8_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v8'
OCCURRENCE_V9_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v9'
OCCURRENCE_V10_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v10'
OCCURRENCE_V11_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v11'
OCCURRENCE_V12_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v12'
OCCURRENCE_V13_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v13'
OCCURRENCE_V14_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v14'
OCCURRENCE_V15_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v15'
OCCURRENCE_V16_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v16'
OCCURRENCE_V17_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v17'
OCCURRENCE_V18_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v18'
OCCURRENCE_V19_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v19'
OCCURRENCE_V20_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v20'
OCCURRENCE_V21_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v21'
OCCURRENCE_V22_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v22'
OCCURRENCE_V23_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v23'
OCCURRENCE_V24_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-occurrence-v24'
OCCURRENCE_V3_PROFILE = 'semantic_map.node_local.v4.occurrence.v3'
OCCURRENCE_V4_PROFILE = 'semantic_map.node_local.v4.occurrence.v4'
OCCURRENCE_V5_PROFILE = 'semantic_map.node_local.v4.occurrence.v5'
OCCURRENCE_V6_PROFILE = 'semantic_map.node_local.v4.occurrence.v6'
OCCURRENCE_V7_PROFILE = 'semantic_map.node_local.v4.occurrence.v7'
OCCURRENCE_V8_PROFILE = 'semantic_map.node_local.v4.occurrence.v8'
OCCURRENCE_V9_PROFILE = 'semantic_map.node_local.v4.occurrence.v9'
OCCURRENCE_V10_PROFILE = 'semantic_map.node_local.v4.occurrence.v10'
OCCURRENCE_V11_PROFILE = 'semantic_map.node_local.v4.occurrence.v11'
OCCURRENCE_V12_PROFILE = 'semantic_map.node_local.v4.occurrence.v12'
OCCURRENCE_V13_PROFILE = 'semantic_map.node_local.v4.occurrence.v13'
OCCURRENCE_V14_PROFILE = 'semantic_map.node_local.v4.occurrence.v14'
OCCURRENCE_V15_PROFILE = 'semantic_map.node_local.v4.occurrence.v15'
OCCURRENCE_V16_PROFILE = 'semantic_map.node_local.v4.occurrence.v16'
OCCURRENCE_V17_PROFILE = 'semantic_map.node_local.v4.occurrence.v17'
OCCURRENCE_V18_PROFILE = 'semantic_map.node_local.v4.occurrence.v18'
OCCURRENCE_V19_PROFILE = 'semantic_map.node_local.v4.occurrence.v19'
OCCURRENCE_V20_PROFILE = 'semantic_map.node_local.v4.occurrence.v20'
OCCURRENCE_V21_PROFILE = 'semantic_map.node_local.v4.occurrence.v21'
OCCURRENCE_V22_PROFILE = 'semantic_map.node_local.v4.occurrence.v22'
OCCURRENCE_V23_PROFILE = 'semantic_map.node_local.v4.occurrence.v23'
OCCURRENCE_V24_PROFILE = 'semantic_map.node_local.v4.occurrence.v24'
FACT_PROSE_PROFILES = frozenset({OCCURRENCE_V16_PROFILE, OCCURRENCE_V17_PROFILE, OCCURRENCE_V18_PROFILE, OCCURRENCE_V19_PROFILE, OCCURRENCE_V20_PROFILE, OCCURRENCE_V21_PROFILE, OCCURRENCE_V22_PROFILE, OCCURRENCE_V23_PROFILE, OCCURRENCE_V24_PROFILE})
VISIBLE_SOURCE_PROFILES = frozenset({OCCURRENCE_V14_PROFILE, OCCURRENCE_V15_PROFILE, OCCURRENCE_V16_PROFILE, OCCURRENCE_V17_PROFILE, OCCURRENCE_V18_PROFILE, OCCURRENCE_V19_PROFILE, OCCURRENCE_V20_PROFILE, OCCURRENCE_V21_PROFILE, OCCURRENCE_V22_PROFILE, OCCURRENCE_V23_PROFILE, OCCURRENCE_V24_PROFILE})
CONTENT_PLAN_PROFILES = frozenset({OCCURRENCE_V13_PROFILE, *VISIBLE_SOURCE_PROFILES})
FACT_REFERENCE_PROFILES = frozenset({OCCURRENCE_V12_PROFILE, *CONTENT_PLAN_PROFILES})
SOURCE_CUED_PROFILES = frozenset({OCCURRENCE_V9_PROFILE, OCCURRENCE_V10_PROFILE, OCCURRENCE_V11_PROFILE, *FACT_REFERENCE_PROFILES})
OCCURRENCE_PROFILES = frozenset({OCCURRENCE_PROFILE, OCCURRENCE_V2_PROFILE, OCCURRENCE_V3_PROFILE, OCCURRENCE_V4_PROFILE, OCCURRENCE_V5_PROFILE, OCCURRENCE_V6_PROFILE, OCCURRENCE_V7_PROFILE, OCCURRENCE_V8_PROFILE, *SOURCE_CUED_PROFILES})
NODE_LOCAL_V4_BOUND_V2_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v4-bound-roots-v2'
NODE_LOCAL_V4_BOUND_V2_PROFILE = 'semantic_map.node_local.v4.bound_roots.v2'
NODE_LOCAL_V4_SCHEMA = 'cocolon.analysis.semantic_map.node_local.model.v4'
NODE_LOCAL_V4_PHASES = ('PLAN', 'NODES', 'RELATIONS')
NODE_LOCAL_V3_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v3'
NODE_LOCAL_V3_BASE_MODEL = 'cocolon-qwen3.5-4b-analysis-node-local-v3-base-851bf6e'

IF_CANDIDATE_SCHEMA = 'cocolon.analysis.if-candidates.model.v1'
PIECE_ADAPTER_NAME = 'piece'
EVENT_PLAN_ADAPTER_NAME = 'event_plan'


class SourcePrivateConstraintLog(logging.Filter):
    """Upstream error paths must never print decoded prompts or prefixes."""
    def filter(self, record):
        if 'lmformatenforcer' in Path(record.pathname).parts:
            record.msg = 'analysis_generation_constraint_internal_error'
            record.args = ()
            record.exc_info = record.exc_text = record.stack_info = None
        return True


def generation_stage(stage):
    print('analysis_generation_stage=' + stage + ' monotonic=' + str(round(time.monotonic(), 3)), flush=True)


def generation_failure(exc):
    """Locate a serving failure without logging source, prefixes or messages."""
    generation_stage('failed_' + type(exc).__name__)
    trace = exc.__traceback__
    while trace is not None:
        generation_stage('failure_location_' + trace.tb_frame.f_code.co_name + '_' + str(trace.tb_lineno))
        trace = trace.tb_next


# Match the fixed, ordered v4 NODES envelope, including JSON whitespace.
_OCCURRENCE_NODES_OPEN = re.compile(
    r'\s*\{\s*"schema_version"\s*:\s*"[^"]+"\s*,\s*"plan_sha256"\s*:\s*"[0-9a-f]{64}"\s*,\s*"nodes"\s*:\s*\{')
_OCCURRENCE_NODE_OPEN = re.compile(r'\s*(?:,\s*)?"n[1-9][0-9]*"\s*:\s*\{')
_OCCURRENCE_NODE_KEYS = tuple(re.compile(r'\s*' + ('' if name=='units' else r',\s*') +
    '"' + name + r'"\s*:\s*') for name in ('units','node_kind','perspective','title','meaning'))
_OCCURRENCE_ESCAPE = re.compile(r'\\(?:u[0-9A-Fa-f]{4}|["\\/bfnrt])')


def _semantic_source_cues(quote):
    # Keep a verbatim, bounded beginning or ending next to the prose it grounds.
    # The complete selected quote remains in the input and in the saved PLAN.
    return tuple(dict.fromkeys((quote[:16], quote[-16:])))


def _semantic_fact_part_key(evidence, index):
    # Put a short piece of this source immediately before its authored value.
    # Prefer a span that distinguishes siblings with the same opening words.
    quote = evidence[index]['quote']
    others = [root['quote'] for i, root in enumerate(evidence) if i != index]
    width = min(8, len(quote))
    cue = quote[:width]
    for start in range(len(quote) - width + 1):
        span = quote[start:start + width]
        if all(span not in other for other in others):
            cue = span
            break
    return f'e{index + 1}/{cue}'


def _occurrence_visible_signature(units, title, meaning, fact_sources=None):
    # Use the compiler's projection order. Comparison alone ignores trailing
    # horizontal padding and repeated terminal Japanese full stops. Every
    # original string remains untouched, including quotations and questions.
    def comparison(text):
        return '\n'.join(re.sub(r'。(?:[ \t\u3000]*。)+$', '。', line.rstrip(' \t\u3000')) for line in text.split('\n'))
    title, meaning = comparison(title), comparison(meaning)
    facts = []
    for i in range(1, len(units)+1):
        unit = units['u' + str(i)]
        if 'fact_parts' in unit:
            parts = unit['fact_parts']
            fact = ''.join((fact_sources or {}).get((unit.get('evidence_ref'), key, parts[key]), str(parts[key]))
                           for key in sorted(parts))
        else:
            fact = unit['fact']
        facts.append(comparison(fact))
    repeated = meaning in facts or meaning in ('\n'.join(facts), ''.join(facts))
    parts = facts + ([meaning] if meaning and not repeated else [])
    body = '\n'.join(dict.fromkeys(line for part in parts for line in part.split('\n')))
    return title, meaning or facts[0], body


def _occurrence_duplicate_prefix(wire, fact_sources=None):
    """Reject an irrevocably duplicate public node before its token is emitted."""
    opener = _OCCURRENCE_NODES_OPEN.match(wire)
    if opener is None:
        return False
    position = opener.end()
    decoder = json.JSONDecoder()
    seen = set()
    while node := _OCCURRENCE_NODE_OPEN.match(wire,position):
        position = node.end()
        values = []
        for key in _OCCURRENCE_NODE_KEYS:
            prop = key.match(wire,position)
            if prop is None:
                return False
            position = prop.end()
            try:
                value, position = decoder.raw_decode(wire,position)
            except json.JSONDecodeError:
                # LMFE gives an unfinished meaning at its 240-character limit
                # only a closing quote. Prevent that dead end one token earlier.
                if len(values)==4 and seen and wire[position:position+1]=='"':
                    encoded = wire[position+1:]
                    if len(encoded)>=240 and len(_OCCURRENCE_ESCAPE.sub('x',encoded))>=240:
                        try:
                            value = json.loads(wire[position:]+'"')
                        except json.JSONDecodeError:
                            return False
                        return _occurrence_visible_signature(values[0],values[3],value,fact_sources) in seen
                return False
            values.append(value)
        identity = _occurrence_visible_signature(values[0],values[3],values[4],fact_sources)
        if identity in seen:
            return True
        seen.add(identity)
        while position<len(wire) and wire[position] in ' \r\t\n':
            position += 1
        if wire[position:position+1]!='}':
            return False
        position += 1
    return False


def _semantic_wire_fact_sources(messages):
    messages = _semantic_constraint_messages(messages)
    material = json.loads(messages[1]['content'])
    if material.get('author_profile') not in FACT_REFERENCE_PROFILES:
        return None
    schema = semantic_output_schema(messages)['properties']['nodes']['properties']
    sources = {}
    for node in material['plan']['nodes']:
        nid = node['node_id']
        for i, unit in enumerate(node['units'], 1):
            uid = f'u{i}'
            parts = schema[nid]['properties']['units']['properties'][uid]['properties']['fact_parts']['properties']
            for j, root in enumerate(unit['evidence']):
                key = _semantic_fact_part_key(unit['evidence'], j)
                if parts[key].get('type') == 'integer' and 'enum' in parts[key]:
                    sources[(f'{nid}.{uid}', key, parts[key]['enum'][0])] = root['quote']
                for ref, sentence in parts[key].get('x-fact-sentences', {}).items():
                    sources[(f'{nid}.{uid}', key, ref)] = sentence
    return sources


def _occurrence_greedy_node_filter(tokenizer, prompt_tokens, fact_sources=None, visible_filter=None, compact_prefix=None):
    """Filter actual greedy choices after the pinned LMFE prefix mask."""
    def choose(input_ids, scores):
        if len(scores)!=1 or len(input_ids)!=1:
            raise ValueError('occurrence_single_greedy_sequence_required')
        accepted = input_ids[0][prompt_tokens:].tolist()
        while True:
            if visible_filter is not None:
                scores = visible_filter(input_ids, scores)
            picked = int(scores[0].argmax().item())
            if float(scores[0,picked])==float('-inf'):
                raise ValueError('occurrence_no_distinct_node_continuation')
            if compact_prefix is None:
                wire = tokenizer.decode([*accepted,picked],skip_special_tokens=False,
                    clean_up_tokenization_spaces=False)
            else:
                enforcer = compact_prefix.token_enforcer
                state = enforcer.prefix_states[tuple(accepted)]
                parser = state.parser
                if parser.can_end():
                    return scores
                for char in _semantic_token_suffix(enforcer, state, picked):
                    if char not in parser.get_allowed_characters():
                        break
                    parser = parser.add_character(char)
                else:
                    if not _occurrence_duplicate_prefix(parser.projected_prefix(), fact_sources):
                        return scores
                scores[0,picked] = float('-inf')
                continue
            if not _occurrence_duplicate_prefix(wire, fact_sources):
                return scores
            scores[0,picked] = float('-inf')
    return choose


def _semantic_prefix_input(sent, prompt_tokens):
    # A fresh pinned enforcer treats its first input as the parser root. For a
    # single greedy MERGE the prompt is fixed, so every branch is identified by
    # its full generated token history, including the initial empty history.
    return sent[prompt_tokens:] if prompt_tokens else sent


def _semantic_token_suffix(enforcer, state, token):
    if token in enforcer.tokenizer_tree.new_word_tokens:
        return enforcer.tokenizer_tree.tokens_to_strs[token]
    prior = state.current_word_tokens
    return enforcer.decoder(prior + [token])[len(enforcer.decoder(prior)):]


def _occurrence_greedy_relation_filter(prefix, *, prompt_tokens=0):
    """Validate a greedy token against the exact title rule before it is emitted."""
    enforcer = prefix.token_enforcer
    enforcer.root_parser.context.guard_endpoint_label_tokens = True
    def choose(input_ids, scores):
        if len(scores) != 1 or len(input_ids) != 1:
            raise ValueError('occurrence_single_greedy_sequence_required')
        history = _semantic_prefix_input(input_ids[0], prompt_tokens)
        state = enforcer.prefix_states[tuple(history.tolist())]
        stack = getattr(state.parser, 'object_stack', ())
        if not stack or not getattr(stack[-1], 'guarded_shortcut', False):
            return scores
        while True:
            token = int(scores[0].argmax().item())
            if float(scores[0,token]) == float('-inf'):
                raise ValueError('occurrence_no_distinct_edge_label_continuation')
            # Decode the same incremental spelling as the pinned token enforcer,
            # including multi-character tokens and context-dependent token joins.
            suffix = _semantic_token_suffix(enforcer, state, token)
            parser = state.parser
            for char in suffix:
                if char not in parser.get_allowed_characters():
                    break
                parser = parser.add_character(char)
            else:
                return scores
            scores[0,token] = float('-inf')
    return choose


def semantic_free_text_tokens(prefix, batch, sent, blocked, invalid_json_tokens=frozenset()):
    """Exclude raw-control/blank loops only from generated prose, not quotes."""
    allowed = prefix(batch, sent)
    # Source quote candidates contain no raw controls. JSON layout can be
    # compact. Empty decoder entries otherwise enter LMFE's root trie and are
    # allowed at every state without advancing the parser.
    state = prefix.token_enforcer.prefix_states[tuple(sent.tolist())].parser
    key = state.shortcut_key()
    excluded = invalid_json_tokens
    if isinstance(key, tuple) and key[0] == 'json_freetext':
        excluded = invalid_json_tokens | blocked
    allowed = [token for token in allowed if token not in excluded]
    if not allowed:
        raise ValueError('semantic_free_text_tokens_unavailable')
    return allowed


def _if_output_schema(material):
    """Constrain only the versioned IF protocol; the IF owner admits meaning."""
    if (set(material) != {'model_schema', 'base_map_kind', 'branch_point_ref', 'anchors',
            'fields', 'requested_candidate_count', 'constraints_confirmed'}
            or material['model_schema'] != IF_CANDIDATE_SCHEMA
            or material['base_map_kind'] != 'DERIVED_AI_MAP_ANCHOR'
            or type(material['branch_point_ref']) is not str or not material['branch_point_ref']
            or type(material['requested_candidate_count']) is not int
            or not 1 <= material['requested_candidate_count'] <= 3
            or type(material['constraints_confirmed']) is not bool
            or type(material['anchors']) is not list or not material['anchors']
            or type(material['fields']) is not list or not material['fields']):
        raise ValueError('if_material_invalid')
    anchors = []
    for anchor in material['anchors']:
        if (type(anchor) is not dict or set(anchor) != {'node_ref', 'visible_label'}
                or any(type(anchor[k]) is not str or not anchor[k] for k in anchor)):
            raise ValueError('if_material_invalid')
        anchors.append(anchor['node_ref'])
    if len(set(anchors)) != len(anchors):
        raise ValueError('if_material_invalid')
    fields = []
    for index, field in enumerate(material['fields'], 1):
        if (type(field) is not dict or set(field) != {'field', 'source_role', 'purpose', 'text'}
                or type(field['field']) is not int or field['field'] != index
                or field['source_role'] != 'SIMULATION_SESSION_MATERIAL'
                or field['purpose'] not in {'BRANCH_INTENT', 'CONSTRAINT', 'PERSON_ALTERNATIVE'}
                or (field['purpose'] == 'BRANCH_INTENT') != (index == 1)
                or type(field['text']) is not str or not field['text'].strip()):
            raise ValueError('if_material_invalid')
        fields.append(index)

    def text(maximum=1000):
        return dict(type='string', minLength=1, maxLength=maximum)

    def obj(properties):
        return dict(type='object', properties=properties, required=list(properties), additionalProperties=False)

    def array(items, minimum=0, maximum=None):
        result = dict(type='array', items=items, minItems=minimum)
        if maximum is not None:
            result['maxItems'] = maximum
        return result

    refs = array(dict(type='integer', enum=fields), maximum=len(fields))
    def quoted(value):
        return dict(type='string', enum=[value])

    def node_variant(origin, body, anchor, sources, reasons):
        return obj(dict(node_id=text(100), step_kind=text(100),
            origin=dict(type='string', enum=[origin]), text=body,
            anchor_ref=anchor, source_refs=sources, unknown_reasons=reasons))

    empty = array(dict(type='integer', enum=fields), maximum=0)
    variants = [node_variant('OBSERVED_ANCHOR', quoted(anchor['visible_label']),
        dict(type='string', enum=[anchor['node_ref']]), empty, array(text(200)))
        for anchor in material['anchors']]
    alternatives = [field for field in material['fields'] if field['purpose'] == 'PERSON_ALTERNATIVE']
    if (len(alternatives) != material['requested_candidate_count']
            or len({field['text'] for field in alternatives}) != material['requested_candidate_count']):
        alternatives = []
    choice_fields = alternatives or [field for field in material['fields']
        if field['purpose'] == 'PERSON_ALTERNATIVE']
    variants += [node_variant('USER_CHOICE', quoted(field['text']), dict(type='null'),
        array(dict(type='integer', enum=[field['field']]), 1, 1), array(text(200)))
        for field in choice_fields]
    if not alternatives:
        variants.append(node_variant('SIMULATED_EXTENSION', text(), dict(type='null'), refs, array(text(200), maximum=0)))
    variants.append(node_variant('UNKNOWN', text(), dict(type='null'), empty, array(text(200), 1)))
    node = dict(oneOf=variants)
    edge = obj({'edge_id': text(100), 'from': text(100), 'to': text(100),
        'condition_refs': array(text(100), maximum=12)})
    condition = obj(dict(condition_id=text(100), text=text(), source_refs=refs))
    label = dict(type='string', enum=[field['text'] for field in alternatives]) if alternatives else text()
    scenario = obj(dict(scenario_id=text(100), label=label, nodes=array(node, 1, 24),
        edges=array(edge, 1, 48), required_conditions=array(condition, maximum=12),
        frictions=array(text(), maximum=12), unmodelled_factors=array(text(), 1, 12)))
    # Keep authored conditions visible in every candidate. Additional uncertain
    # requirements remain model-authored UNKNOWN/frictions/factors, never a
    # silently omitted or reworded person constraint.
    constraints = [field for field in material['fields'] if field['purpose'] == 'CONSTRAINT']
    def object_tuple(items):
        return dict(type='array', prefixItems=items, items=False,
            minItems=len(items), maxItems=len(items))
    if constraints:
        scenario['properties']['required_conditions'] = object_tuple([
            obj(dict(condition_id=quoted('constraint_' + str(i)), text=quoted(field['text']),
                source_refs=array(dict(type='integer', enum=[field['field']]), 1, 1)))
            for i, field in enumerate(constraints, 1)])

    def fixed_node(node_id, kind, origin, body, anchor, sources, reasons):
        value = node_variant(origin, body, anchor, sources, reasons)
        value['properties'].update(node_id=quoted(node_id), step_kind=quoted(kind))
        return value

    anchor_nodes = [fixed_node('anchor_' + str(i), 'BASE_MAP_ANCHOR',
        'OBSERVED_ANCHOR', quoted(anchor['visible_label']), quoted(anchor['node_ref']),
        empty, array(text(200), maximum=0))
        for i, anchor in enumerate(material['anchors'], 1)]
    def fixed_edge(edge_id, start, end):
        return obj({'edge_id': quoted(edge_id), 'from': quoted(start), 'to': quoted(end),
            'condition_refs': array(text(100), maximum=12)})

    edges = [fixed_edge('anchor_' + str(i) + '_to_choice', 'anchor_' + str(i), 'choice')
        for i in range(1, len(anchor_nodes) + 1)]
    edges.append(fixed_edge('choice_to_unknown', 'choice', 'unknown'))
    unknown = fixed_node('unknown', 'UNKNOWN_AFTERMATH', 'UNKNOWN', text(),
        dict(type='null'), empty, array(text(200), 1))
    if alternatives:
        # Complete person-authored options retain their exact source slots.
        scenarios = []
        for field in alternatives:
            choice = fixed_node('choice', 'POSSIBLE_CHOICE', 'USER_CHOICE',
                quoted(field['text']), dict(type='null'),
                array(dict(type='integer', enum=[field['field']]), 1, 1), array(text(200), maximum=0))
            properties = dict(scenario['properties'], label=quoted(field['text']),
                nodes=object_tuple(anchor_nodes + [choice, unknown]), edges=object_tuple(edges))
            scenarios.append(obj(properties))
        scenario = dict(oneOf=scenarios)
    else:
        # Standard RN supplies an intent, not a completed list of choices.
        # Proposal content remains generated. Intent is not a person option. A partial option can still
        # be quoted as USER_CHOICE; constraints cannot become that choice.
        choices = [fixed_node('choice', 'POSSIBLE_CHOICE', 'USER_CHOICE',
            quoted(field['text']), dict(type='null'),
            array(dict(type='integer', enum=[field['field']]), 1, 1), array(text(200), maximum=0))
            for field in choice_fields]
        choices.append(fixed_node('choice', 'POSSIBLE_CHOICE', 'SIMULATED_EXTENSION',
            text(), dict(type='null'), refs, array(text(200), maximum=0)))
        scenario['properties'].update(nodes=object_tuple(anchor_nodes + [dict(oneOf=choices), unknown]),
            edges=object_tuple(edges))
    clarification = obj(dict(reason_code=dict(type='string', enum=[
        'BRANCH_INTENT_UNCLEAR', 'CONSTRAINT_UNCLEAR', 'ALTERNATIVES_UNCLEAR']), prompt=text(300)))
    return obj(dict(schema_version=dict(type='string', enum=[IF_CANDIDATE_SCHEMA]),
        scenarios=array(scenario, maximum=material['requested_candidate_count']),
        clarification=dict(anyOf=[dict(type='null'), clarification])))


def _semantic_sentence_quotes(original, *, qualification_tails=False):
    """Additional unique sentences; never rewrite or replace the full source.

    Keep paired Japanese quotations intact. Ambiguous quotation boundaries or
    JSON enum escape characters yield no new sentence spanning that boundary.
    ASCII periods are deliberately not sentence boundaries (URLs/decimals).
    """
    pairs = {'「': '」', '『': '』'}
    if qualification_tails:
        pairs.update({'“': '”', '‘': '’', '"': '"', "'": "'", '`': '`', '（': '）', '(': ')',
            '【': '】', '〈': '〉', '《': '》', '[': ']', '{': '}'})
    escaped = False
    stack, candidates = [], []
    starts = [] if qualification_tails else [0]
    terminal = '。！？!?'
    for index, char in enumerate(original):
        if qualification_tails and stack and stack[-1] in ('"', "'", '`'):
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == stack[-1]:
                stack.pop()
            continue
        if stack and char == stack[-1]:
            stack.pop()
        elif char in pairs:
            stack.append(pairs[char])
        elif char in pairs.values():
            return []
        elif qualification_tails and not stack and char in '、，':
            starts.append(index + 1)
        elif not stack and (char in terminal or char in '\r\n'):
            if char in terminal and index + 1 < len(original) and original[index + 1] in terminal:
                continue
            candidates.extend(original[start:index + 1].strip() for start in starts
                if not qualification_tails or index + 1 - start <= 240)
            starts = [] if qualification_tails else [index + 1]
    if stack:
        return []
    candidates.extend(original[start:].strip() for start in starts
        if not qualification_tails or len(original) - start <= 240)
    if qualification_tails:
        # Keep the completing predicate, with exactly one location in the
        # original field. The stage later checks containment in its chosen root.
        return [span for span in candidates if 0 < len(span) <= 240
            and original.find(span) == original.rfind(span)
            and not re.search(r'["\\\x00-\x1f]', span)]
    return [span for span in candidates if span and len(span) <= 4000
        and original.count(span) == 1 and not re.search(r'["\\\x00-\x1f]', span)]


def _semantic_event_plan_schema(pairs, *, leaf=False):
    """One authored fact, reference selections for every display surface."""
    def text(n):
        return dict(type='string', minLength=1, maxLength=n)
    def obj(props):
        return dict(type='object', properties=props, required=list(props), additionalProperties=False)
    def refs(prefix, minimum, maximum):
        return dict(type='array', items=dict(type='string', enum=[prefix + str(i) for i in range(1,25)]),
            minItems=minimum, maxItems=maximum)
    event = obj(dict(evidence=dict(type='array', items=dict(oneOf=pairs), minItems=1, maxItems=4),
        event_id=dict(type='string', enum=['e'+str(i) for i in range(1,25)]),
        fact=text(160), unknowns=dict(type='array', items=text(240), maxItems=4)))
    reading = obj(dict(reading_id=dict(type='string', enum=['r'+str(i) for i in range(1,25)]),
        event_refs=refs('e',1,4), meaning=text(240)))
    node = obj(dict(node_id=dict(type='string', enum=['n'+str(i) for i in range(1,25)]),
        node_kind=dict(type='string', enum=['SELF_POSITION','TARGET_MEANING','CHOICE_OUTPUT','STATE_CONTEXT']),
        perspective=dict(type='string', enum=['SELF','OBSERVED_INTERACTION']), title=text(80),
        event_refs=refs('e',1,4), reading_refs=refs('r',0,4)))
    edge = obj({'from':dict(type='string',enum=['n'+str(i) for i in range(1,25)]),
        'to':dict(type='string',enum=['n'+str(i) for i in range(1,25)]),
        'relation_kind':dict(type='string',enum=['SELF_OUTSIDE_GAP','CRITERION_EXPRESSION','CONTEXT_CONTRAST','SHARED_MEANING']),
        'label':text(80), 'event_refs':refs('e',1,6), 'reading_refs':refs('r',0,4)})
    return obj(dict(schema_version=dict(type='string',enum=[EVENT_PLAN_SCHEMA]),
        events=dict(type='array',items=event,minItems=1,maxItems=24),
        readings=dict(type='array',items=reading,maxItems=24),
        nodes=dict(type='array',items=node,minItems=1,maxItems=24),
        edges=dict(type='array',items=edge,maxItems=0 if leaf else 48),
        overview=obj(dict(title=text(80),event_refs=refs('e',1,24),reading_refs=refs('r',0,8)))))


def _semantic_event_plan_v2_schema(pairs, unknown_pairs, *, leaf=False):
    """Select source-qualified authored units without redeclaring their roots."""
    def text(n):
        return dict(type='string', minLength=1, maxLength=n)
    def obj(props):
        return dict(type='object', properties=props, required=list(props), additionalProperties=False)
    def refs(prefixes, minimum, maximum):
        return dict(type='array', items=dict(type='string',
            enum=[prefix + str(i) for prefix in prefixes for i in range(1,25)]),
            minItems=minimum, maxItems=maximum)
    unknowns = (dict(type='array', items=dict(oneOf=unknown_pairs), maxItems=4)
        if unknown_pairs else dict(type='array', items=dict(type='object'), maxItems=0))
    event = obj(dict(evidence=dict(type='array', items=dict(oneOf=pairs), minItems=1, maxItems=4),
        event_id=dict(type='string', enum=['e'+str(i) for i in range(1,25)]),
        source_mode=dict(type='string', enum=['RECORDED','PERSON_JUDGMENT','PERSON_WISH','DECIDED_PLAN']),
        fact=text(160), unknowns=unknowns))
    reading = obj(dict(reading_id=dict(type='string', enum=['r'+str(i) for i in range(1,25)]),
        event_refs=refs('e',1,4), meaning=text(240)))
    node = obj(dict(node_id=dict(type='string', enum=['n'+str(i) for i in range(1,25)]),
        node_kind=dict(type='string', enum=['SELF_POSITION','TARGET_MEANING','CHOICE_OUTPUT','STATE_CONTEXT']),
        perspective=dict(type='string', enum=['SELF','OBSERVED_INTERACTION']), title=text(80),
        unit_refs=refs('er',1,4)))
    edge = obj({'from':dict(type='string', enum=['n'+str(i) for i in range(1,25)]),
        'to':dict(type='string', enum=['n'+str(i) for i in range(1,25)]),
        'relation_kind':dict(type='string', enum=['SELF_OUTSIDE_GAP','CRITERION_EXPRESSION','CONTEXT_CONTRAST','SHARED_MEANING']),
        'label':text(80), 'unit_refs':refs('er',1,6)})
    return obj(dict(schema_version=dict(type='string',enum=[EVENT_PLAN_V2_SCHEMA]),
        events=dict(type='array',items=event,minItems=1,maxItems=24),
        readings=dict(type='array',items=reading,maxItems=24),
        nodes=dict(type='array',items=node,minItems=1,maxItems=24),
        edges=dict(type='array',items=edge,maxItems=0 if leaf else 48),
        overview=obj(dict(title=text(80),unit_refs=refs('er',1,32)))))


def _semantic_node_local_v3_schema(pairs, unknown_pairs, *, leaf=False):
    """Author facts inside their node; only node positions cross-reference."""
    def text(maximum, minimum=1):
        return dict(type='string', minLength=minimum, maxLength=maximum)
    def obj(props):
        return dict(type='object', properties=props, required=list(props), additionalProperties=False)
    node_ref = dict(type='string', enum=['n' + str(i) for i in range(1, 13)])
    unknowns = (dict(type='array', items=dict(oneOf=unknown_pairs), maxItems=2)
        if unknown_pairs else dict(type='array', items=dict(type='object'), maxItems=0))
    unit = obj(dict(evidence=dict(type='array', items=dict(oneOf=pairs), minItems=1, maxItems=4),
        source_mode=dict(type='string', enum=['RECORDED', 'PERSON_JUDGMENT', 'PERSON_WISH', 'DECIDED_PLAN']),
        fact=text(160), unknowns=unknowns))
    node = obj(dict(units=dict(type='array', items=unit, minItems=1, maxItems=2),
        node_kind=dict(type='string', enum=['SELF_POSITION', 'TARGET_MEANING', 'CHOICE_OUTPUT', 'STATE_CONTEXT']),
        perspective=dict(type='string', enum=['SELF', 'OBSERVED_INTERACTION']),
        title=text(80), meaning=text(240, 0)))
    edge = obj({'from': node_ref, 'to': node_ref,
        'relation_kind': dict(type='string', enum=['SELF_OUTSIDE_GAP', 'CRITERION_EXPRESSION', 'CONTEXT_CONTRAST', 'SHARED_MEANING']),
        'label': text(80)})
    return obj(dict(schema_version=dict(type='string', enum=[NODE_LOCAL_V3_SCHEMA]),
        nodes=dict(type='array', items=node, minItems=1, maxItems=12),
        edges=dict(type='array', items=edge, maxItems=0 if leaf else 48),
        overview=obj(dict(title=text(80), node_refs=dict(type='array', items=node_ref, minItems=1, maxItems=8)))))


def _semantic_recorded_actions(material):
    """Index complete positive, past SELF facts that the existing source reader proved."""
    fields = {field['field']: field for field in material['fields']}
    actions = set()
    for claim in material.get('source_duties', {}).get('claims', ()):
        reading = claim['reading']
        field = fields.get(claim['field'])
        if (field is None or reading.get('actor') != 'SELF' or reading.get('modality') != 'fact'
                or reading.get('polarity') != 'positive' or reading.get('time') != 'past'
                or any(reading.get(key) for key in ('possible_content', 'dependent', 'sequence'))):
            continue
        offset = field.get('fragment_scalar_range', [0])[0]
        start, end = (position - offset for position in claim['span'])
        if 0 <= start < end <= len(field['text']):
            actions.add((field['field'], field['text'][start:end]))
    return actions


def _semantic_literal_handles(quote):
    # A whole numeric handle is valid prose if this root contains it. Do
    # not license a different numeric handle from a substring of an email.
    return set(re.findall(r'(?<![A-Za-z0-9_.%+@-])@[1-9][0-9]*(?![A-Za-z0-9_@-])', quote))


def _semantic_display_sentences(material):
    """Only standalone, unique, complete sentences are eligible for literal display."""
    choices = {}
    for field in material['fields']:
        if field.get('fragment_is_complete_field') is False:
            continue
        source = field['text']
        # The shared sentence reader handles Japanese quotation brackets. For
        # other enclosures keep authored prose: an apparent stop may be nested.
        if any(char in source for char in '（）()［］[]【】〈〉《》｛｝{}“”‘’"\'`'):
            continue
        choices[field['field']] = {value for value in _semantic_sentence_quotes(source)
            if value.endswith(('。', '！', '？', '!', '?')) and '\n' not in value and '\r' not in value}
    return choices


def _semantic_relation_fact_parts(material):
    """Recover exactly the per-root fact text retained by the preceding NODES receipt."""
    error = 'semantic_relation_fact_parts_unbound'
    if ('evidence_parts_by_unit' in material or type(material.get('fact_part_overrides')) is not dict
            or material.get('author_profile') not in FACT_REFERENCE_PROFILES or material.get('author_phase') != 'RELATIONS'):
        raise ValueError(error)
    overrides = dict(material['fact_part_overrides'])
    parts = {}
    for node in material['candidate_nodes']:
        for i, unit in enumerate(node['units'], 1):
            ref = f"{node['node_id']}.u{i}"
            entries = {}
            for j, root in enumerate(unit['evidence'], 1):
                key = f'e{j}'
                path = ref + '.' + key
                part = root['quote']
                if path in overrides:
                    part = overrides.pop(path)
                    if type(part) is not str or not part.strip() or part == root['quote']:
                        raise ValueError(error)
                entries[key] = dict(field=root['field'], quote=root['quote'], fact_part=part)
            if ''.join(e['fact_part'] for e in entries.values()) != unit['fact']:
                raise ValueError(error)
            parts[ref] = entries
    digest = hashlib.sha256(json.dumps(parts, ensure_ascii=False, sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    if overrides or material.get('evidence_parts_sha256') != digest:
        raise ValueError(error)
    return parts


def _semantic_node_local_v4_schema(material, pairs, unknown_pairs, *, leaf=False, record_owners=(), bound_titles=False):
    """Three private author shapes; no text repair or semantic certification."""
    from copy import deepcopy
    def obj(props):
        return dict(type='object', properties=props, required=list(props), additionalProperties=False)
    def text(maximum, minimum=1):
        return dict(type='string', minLength=minimum, maxLength=maximum)
    def signature(value):
        return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
            separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    def root(phase, props):
        return obj(dict(schema_version=dict(type='string',
            enum=[NODE_LOCAL_V4_SCHEMA + '.' + phase.lower()]), **props))
    phase = material.get('author_phase')
    author_profile = material.get('author_profile')
    if author_profile not in (None, NODE_LOCAL_V4_BOUND_PROFILE, NODE_LOCAL_V4_BOUND_V2_PROFILE, *OCCURRENCE_PROFILES):
        raise ValueError('semantic_v4_profile_invalid')
    bound = author_profile in {NODE_LOCAL_V4_BOUND_PROFILE, NODE_LOCAL_V4_BOUND_V2_PROFILE, *OCCURRENCE_PROFILES}
    if phase == 'PLAN':
        unit = obj(dict(evidence=dict(type='array', items=dict(oneOf=pairs), minItems=1, maxItems=4)))
        node = obj(dict(node_id=dict(type='string', enum=['n' + str(i) for i in range(1, 13)]),
            units=dict(type='array', items=unit, minItems=1, maxItems=2)))
        props = {}
        if author_profile in {OCCURRENCE_V11_PROFILE, *FACT_REFERENCE_PROFILES}:
            scope = material.get('source_choices_sha256')
            if type(scope) is not str or not re.fullmatch(r'[0-9a-f]{64}', scope):
                raise ValueError('semantic_plan_choice_scope_invalid')
            props['source_choices_sha256'] = dict(type='string', enum=[scope])
        props['nodes'] = dict(type='array', items=node, minItems=max(1, len(record_owners)), maxItems=12)
        return root(phase, props)
    if phase == 'RELATIONS' and author_profile in {OCCURRENCE_V8_PROFILE, *SOURCE_CUED_PROFILES}:
        # The model sees one ordered copy of the evidence. Reconstruct the
        # PLAN used by the schema without re-expanding the tokenizer input.
        registry = material.get('candidate_nodes')
        if ('plan' in material or 'relation_units' in material or type(registry) is not list
                or not 1 <= len(registry) <= 12):
            raise ValueError('semantic_v8_compact_registry_invalid')
        try:
            planned_nodes = [
                dict(node_id=node['node_id'], units=[dict(evidence=unit['evidence']) for unit in node['units']])
                for node in registry]
        except (TypeError, KeyError) as exc:
            raise ValueError('semantic_v8_compact_registry_invalid') from exc
        plan = dict(schema_version=NODE_LOCAL_V4_SCHEMA + '.plan', nodes=planned_nodes)
        if signature(plan) != material.get('plan_sha256'):
            raise ValueError('semantic_v8_compact_plan_unbound')
    else:
        plan = material.get('plan')
    if (phase not in {'NODES', 'RELATIONS'} or type(plan) is not dict
            or plan.get('schema_version') != NODE_LOCAL_V4_SCHEMA + '.plan'
            or type(plan.get('nodes')) is not list or not 1 <= len(plan['nodes']) <= 12):
        raise ValueError('semantic_v4_plan_invalid')
    ids, node_properties = [], {}
    source_runs = (_semantic_choice_module().source_closer_runs
        if author_profile in VISIBLE_SOURCE_PROFILES and phase == 'NODES' else None)
    options = {(p['properties']['field']['enum'][0], quote)
        for p in pairs for quote in p['properties']['quote']['enum']}
    display_sentences = _semantic_display_sentences(material) if author_profile in {OCCURRENCE_V11_PROFILE, *FACT_REFERENCE_PROFILES} else {}
    fact_ordinal = 0
    for i, node in enumerate(plan['nodes'], 1):
        if (type(node) is not dict or set(node) != {'node_id', 'units'}
                or node['node_id'] != 'n' + str(i) or type(node['units']) is not list
                or not 1 <= len(node['units']) <= 2):
            raise ValueError('semantic_v4_node_invalid')
        ids.append(node['node_id'])
        units = {}
        titles = []
        for j, unit in enumerate(node['units'], 1):
            if (type(unit) is not dict or set(unit) != {'evidence'}
                    or type(unit['evidence']) is not list or not 1 <= len(unit['evidence']) <= 4):
                raise ValueError('semantic_v4_unit_invalid')
            roots = []
            for pair in unit['evidence']:
                if (type(pair) is not dict or set(pair) != {'field', 'quote'}
                        or type(pair['field']) is not int or type(pair['quote']) is not str
                        or (pair['field'], pair['quote']) not in options
                        or pair in roots):
                    raise ValueError('semantic_v4_root_invalid')
                roots.append(pair)
                quote = pair['quote']
                if len(quote) <= 80 and quote in display_sentences.get(pair['field'], ()):
                    titles.append(quote)
            qualifications = []
            for part in unknown_pairs:
                number = part['properties']['source_field']['enum'][0]
                quotes = [q for q in part['properties']['source_quote']['enum']
                    if any(p['field'] == number and p['quote'].count(q) == 1 for p in roots)]
                if quotes:
                    part = deepcopy(part)
                    part['properties']['source_quote']['enum'] = quotes
                    qualifications.append(part)
            unknowns = (dict(type='array', items=dict(oneOf=qualifications), maxItems=2)
                if qualifications else dict(type='array', items=dict(type='object'), maxItems=0))
            properties = dict(source_mode=dict(type='string', enum=[
                'RECORDED', 'PERSON_JUDGMENT', 'PERSON_WISH', 'DECIDED_PLAN']),
                fact=text(160), unknowns=unknowns)
            if author_profile in {OCCURRENCE_V6_PROFILE, OCCURRENCE_V7_PROFILE, OCCURRENCE_V8_PROFILE, *SOURCE_CUED_PROFILES}:
                lengths = [len(root['quote']) for root in roots]
                count = len(lengths)
                total = sum(lengths)
                if total <= 160:
                    extra, remainder = divmod(160 - total, count)
                    limits = [length + extra + (i < remainder) for i, length in enumerate(lengths)]
                else:
                    # Reserve a character per root, then apportion the rest
                    # by largest remainder. The PLAN order breaks exact ties.
                    shares = [divmod((160 - count) * (length - 1), total - count) for length in lengths]
                    limits = [1 + whole for whole, _ in shares]
                    order = sorted(range(count), key=lambda i: -shares[i][1])
                    for i in order[:160-sum(limits)]:
                        limits[i] += 1
                parts = {'e' + str(index): text(limit) for index, limit in enumerate(limits, 1)}
                if author_profile in SOURCE_CUED_PROFILES:
                    parts = {_semantic_fact_part_key(roots, index): text(limit)
                             for index, limit in enumerate(limits)}
                if display_sentences or author_profile in FACT_PROSE_PROFILES:
                    for (key, part), source in zip(parts.items(), roots, strict=True):
                        fact_ordinal += 1
                        quote = source['quote']
                        if author_profile in {OCCURRENCE_V20_PROFILE, OCCURRENCE_V21_PROFILE, OCCURRENCE_V22_PROFILE, OCCURRENCE_V23_PROFILE, OCCURRENCE_V24_PROFILE}:
                            choices = _semantic_choice_module().source_fact_ranges(quote)
                            parts[key] = (dict(type='string', enum=list(choices), **{'x-fact-sentences': choices})
                                          if choices else dict(type='integer', enum=[fact_ordinal]))
                            continue
                        if len(quote) <= part['maxLength'] and quote in display_sentences.get(source['field'], ()):
                            parts[key] = (dict(type='integer', enum=[fact_ordinal])
                                if author_profile in FACT_REFERENCE_PROFILES else dict(type='string', enum=[quote]))
                        elif author_profile in FACT_REFERENCE_PROFILES:
                            handles = _semantic_literal_handles(quote)
                            if author_profile in FACT_PROSE_PROFILES:
                                handles = _semantic_choice_module().literal_fact_handles(quote)
                                choices = _semantic_choice_module().fact_sentence_choices(
                                    quote, display_sentences.get(source['field'], ()), part['maxLength'])
                                if author_profile in {OCCURRENCE_V19_PROFILE, OCCURRENCE_V20_PROFILE, OCCURRENCE_V21_PROFILE, OCCURRENCE_V22_PROFILE, OCCURRENCE_V23_PROFILE, OCCURRENCE_V24_PROFILE} and '@0' in choices:
                                    parts[key] = dict(type='string', enum=list(choices), **{'x-fact-sentences': choices})
                                    continue
                                if author_profile in {OCCURRENCE_V19_PROFILE, OCCURRENCE_V20_PROFILE, OCCURRENCE_V21_PROFILE, OCCURRENCE_V22_PROFILE, OCCURRENCE_V23_PROFILE, OCCURRENCE_V24_PROFILE}:
                                    part['x-source-bound-members'] = True
                                if choices:
                                    part['x-fact-sentences'] = choices
                                part['x-fact-source'] = quote
                                if author_profile in {OCCURRENCE_V18_PROFILE, OCCURRENCE_V19_PROFILE, OCCURRENCE_V20_PROFILE, OCCURRENCE_V21_PROFILE, OCCURRENCE_V22_PROFILE, OCCURRENCE_V23_PROFILE, OCCURRENCE_V24_PROFILE}:
                                    part['x-source-bound-keys'] = True
                                handles.update(choices)
                            part['description'] = 'source-at-ids:' + ','.join(sorted(handles))
                properties = dict(source_mode=properties['source_mode'], fact_parts=obj(parts), unknowns=unknowns)
            if author_profile in {OCCURRENCE_V5_PROFILE, OCCURRENCE_V6_PROFILE, OCCURRENCE_V7_PROFILE, OCCURRENCE_V8_PROFILE, *SOURCE_CUED_PROFILES}:
                # The plan digest identifies the roots of this unit. Each
                # reference binds its complete list, including order and field.
                binding = dict(type='string', enum=[f"{node['node_id']}.u{j}"])
                properties = dict(evidence_ref=binding, **properties)
            elif bound:
                assigned = {'e' + str(k): obj(dict(
                    source_quote=dict(type='string', enum=[p['quote']]),
                    source_field=dict(type='integer', enum=[p['field']])))
                    for k, p in enumerate(roots, 1)}
                properties = dict(assigned_evidence=obj(assigned), **properties)
            units['u' + str(j)] = obj(properties)
        title = dict(type='string', enum=list(dict.fromkeys(titles))) if titles else text(80)
        if author_profile in CONTENT_PLAN_PROFILES and phase == 'NODES':
            forbidden = _semantic_choice_module().one_sided_source_titles(material, node['units'],
                compare_end_marks=author_profile in FACT_PROSE_PROFILES)
            if forbidden is not None:
                title = text(80)
                if forbidden:
                    title['not'] = dict(enum=forbidden)
        fresh_leaf = (author_profile == OCCURRENCE_V24_PROFILE and phase == 'NODES'
                      and _semantic_choice_module().single_original_leaf(material))
        if (bound_titles or fresh_leaf) and phase == 'NODES':
            title_choices = _semantic_choice_module().source_node_titles(material, node['units'], title.get('enum', ()))
            title = dict(type='string', enum=title_choices)
        meaning = text(240, 0)
        if author_profile in {OCCURRENCE_V20_PROFILE, OCCURRENCE_V21_PROFILE, OCCURRENCE_V22_PROFILE, OCCURRENCE_V23_PROFILE, OCCURRENCE_V24_PROFILE} and phase == 'NODES':
            choices = _semantic_choice_module().paired_node_meanings(
                material['fields'], node['units'], display_sentences)
            if fresh_leaf and not choices:
                choices = _semantic_choice_module().leaf_meanings(material['fields'], node['units'], display_sentences)
            if choices:
                meaning = dict(type='string', enum=choices)
        node_properties[node['node_id']] = obj(dict(units=obj(units),
            node_kind=dict(type='string', enum=['SELF_POSITION', 'TARGET_MEANING', 'CHOICE_OUTPUT', 'STATE_CONTEXT']),
            perspective=dict(type='string', enum=['SELF', 'OBSERVED_INTERACTION']),
            title=title, meaning=meaning))
        if source_runs is not None:
            properties = node_properties[node['node_id']]['properties']
            runs = source_runs(root['quote'] for unit in node['units'] for root in unit['evidence'])
            for name in ('title', 'meaning'):
                if 'enum' not in properties[name]:
                    properties[name]['x-source-closers'] = runs
            for index, unit in enumerate(node['units'], 1):
                props = units[f'u{index}']['properties']['fact_parts']['properties']
                for prop, evidence in zip(props.values(), unit['evidence'], strict=True):
                    if 'enum' not in prop:
                        prop['x-source-closers'] = source_runs([evidence['quote']])
    if phase == 'NODES':
        digest = signature(plan)
        if author_profile in FACT_REFERENCE_PROFILES:
            request = material.get('fact_source_request_ref')
            if type(request) is not str or not request:
                raise ValueError('semantic_node_fact_scope_unbound')
            digest = signature(['analysis.node-facts.v1', 'NODES', request, plan])
        return root(phase, dict(plan_sha256=dict(type='string', enum=[digest]),
            nodes=obj(node_properties)))
    registry = material.get('candidate_nodes')
    if (type(registry) is not list or len(registry) != len(ids)
            or any(type(n) is not dict for n in registry)
            or [n.get('node_id') for n in registry] != ids):
        raise ValueError('semantic_v4_registry_invalid')
    for planned, candidate in zip(plan['nodes'], registry, strict=True):
        if (set(candidate) != {'node_id', 'units', 'node_kind', 'perspective', 'title', 'meaning'}
                or type(candidate['units']) is not list
                or len(candidate['units']) != len(planned['units'])
                or candidate['node_kind'] not in ['SELF_POSITION', 'TARGET_MEANING', 'CHOICE_OUTPUT', 'STATE_CONTEXT']
                or candidate['perspective'] not in ['SELF', 'OBSERVED_INTERACTION']
                or type(candidate['title']) is not str or not 1 <= len(candidate['title']) <= 80
                or type(candidate['meaning']) is not str or len(candidate['meaning']) > 240):
            raise ValueError('semantic_v4_registry_invalid')
        for roots, unit in zip(planned['units'], candidate['units'], strict=True):
            if (type(unit) is not dict or set(unit) != {'evidence', 'source_mode', 'fact', 'unknowns'}
                    or unit['evidence'] != roots['evidence']
                    or unit['source_mode'] not in ['RECORDED', 'PERSON_JUDGMENT', 'PERSON_WISH', 'DECIDED_PLAN']
                    or type(unit['fact']) is not str or not 1 <= len(unit['fact']) <= (
                        160 * len(roots['evidence']) if author_profile in {OCCURRENCE_V20_PROFILE, OCCURRENCE_V21_PROFILE, OCCURRENCE_V22_PROFILE, OCCURRENCE_V23_PROFILE, OCCURRENCE_V24_PROFILE} else 160)
                    or type(unit['unknowns']) is not list or len(unit['unknowns']) > 2):
                raise ValueError('semantic_v4_registry_invalid')
            seen = set()
            for unknown in unit['unknowns']:
                if (type(unknown) is not dict or set(unknown) != {'source_quote', 'source_field'}
                        or type(unknown['source_field']) is not int
                        or type(unknown['source_quote']) is not str
                        or not 1 <= len(unknown['source_quote']) <= 240):
                    raise ValueError('semantic_v4_registry_invalid')
                pair = unknown['source_field'], unknown['source_quote']
                if (pair in seen or not any(r['field'] == pair[0]
                        and r['quote'].count(pair[1]) == 1 for r in roots['evidence'])):
                    raise ValueError('semantic_v4_registry_invalid')
                seen.add(pair)
    if 'fact_part_overrides' in material or 'evidence_parts_sha256' in material:
        _semantic_relation_fact_parts(material)
    elif author_profile in FACT_REFERENCE_PROFILES and 'evidence_parts_by_unit' not in material:
        raise ValueError('semantic_relation_fact_parts_unbound')
    ref = dict(type='string', enum=ids)
    endpoints = {'from': ref, 'to': ref}
    if author_profile in {OCCURRENCE_V6_PROFILE, OCCURRENCE_V7_PROFILE, OCCURRENCE_V8_PROFILE, *SOURCE_CUED_PROFILES}:
        unit_ref = dict(type='string', enum=[f"{n['node_id']}.u{i}"
            for n in registry for i in range(1, len(n['units']) + 1)])
        endpoints.update(from_unit=unit_ref, to_unit=unit_ref)
    if author_profile in SOURCE_CUED_PROFILES:
        cues = list(dict.fromkeys(cue for node in registry for unit in node['units']
                    for root_evidence in unit['evidence'] for cue in _semantic_source_cues(root_evidence['quote'])))
        source = dict(type='string', enum=cues)
        endpoints.update(from_source=source, to_source=source)
    edge = obj(dict(**endpoints, label=text(80), relation_kind=dict(type='string', enum=[
        'SELF_OUTSIDE_GAP', 'CRITERION_EXPRESSION', 'CONTEXT_CONTRAST', 'SHARED_MEANING'])))
    whole = (_semantic_choice_module().WholeMapTitle(material, registry)
             if author_profile in {OCCURRENCE_V20_PROFILE, OCCURRENCE_V21_PROFILE, OCCURRENCE_V22_PROFILE, OCCURRENCE_V23_PROFILE, OCCURRENCE_V24_PROFILE} else None)
    full_scope = whole is not None and whole.count >= 2
    overview = dict(title=text(80), node_refs=dict(type='array', items=ref,
        minItems=len(ids) if full_scope else 1, maxItems=len(ids) if full_scope else min(8, len(ids))))
    if author_profile in {NODE_LOCAL_V4_BOUND_V2_PROFILE, *OCCURRENCE_PROFILES}:
        overview = dict(node_refs=overview['node_refs'], title=overview['title'])
    if full_scope and author_profile in {OCCURRENCE_V21_PROFILE, OCCURRENCE_V22_PROFILE, OCCURRENCE_V23_PROFILE, OCCURRENCE_V24_PROFILE}:
        overview = dict(node_refs=overview['node_refs'], title_proposal=text(80, 0), title=text(80))
    properties = dict(nodes_sha256=dict(type='string', enum=[signature(registry)]))
    if author_profile in {OCCURRENCE_V7_PROFILE, OCCURRENCE_V8_PROFILE, *SOURCE_CUED_PROFILES}:
        # Keep the same order as the original NODES receipt, even when the
        # request serializer sorts dictionary keys (n10 precedes n2 there).
        candidates = {f"{n['node_id']}.u{i}.q{j}": candidate
            for n in registry for i, unit in enumerate(n['units'], 1)
            for j, candidate in enumerate(unit['unknowns'], 1)}
        if author_profile in {OCCURRENCE_V11_PROFILE, *FACT_REFERENCE_PROFILES}:
            candidates = {f"q{i}/{candidate['source_quote'][-8:]}": candidate
                          for i, candidate in enumerate(candidates.values(), 1)}
        if material.get('qualification_candidates') != candidates:
            raise ValueError('semantic_v7_qualification_registry_unbound')
        originals = {f['field']: f['text'] for f in material['fields']}
        review = {}
        closed = obj(dict(status=dict(type='string', enum=['STATED', 'EARLIER', 'DUPLICATE'])))
        stated = _semantic_recorded_actions(material) if author_profile in {OCCURRENCE_V11_PROFILE, *FACT_REFERENCE_PROFILES} else set()
        if author_profile in {OCCURRENCE_V17_PROFILE, OCCURRENCE_V18_PROFILE, OCCURRENCE_V19_PROFILE, OCCURRENCE_V20_PROFILE, OCCURRENCE_V21_PROFILE, OCCURRENCE_V22_PROFILE, OCCURRENCE_V23_PROFILE, OCCURRENCE_V24_PROFILE}:
            stated.update(_semantic_choice_module().recorded_non_actions(material))
        for ref, candidate in candidates.items():
            source = originals[candidate['source_field']]
            quote = candidate['source_quote']
            options = list(dict.fromkeys(q for q in [quote, *_semantic_sentence_quotes(quote),
                *_semantic_sentence_quotes(quote, qualification_tails=True)]
                if 0 <= quote.find(q) == quote.rfind(q) and 0 <= source.find(q) == source.rfind(q)))
            if quote not in options:
                raise ValueError('semantic_v7_qualification_quote_unbound')
            options = [q for q in options if (candidate['source_field'], q.rstrip('。．.')) not in stated]
            if not options:
                review[ref] = closed
                continue
            opened = obj(dict(status=dict(type='string', enum=['OPEN']),
                source_quote=dict(type='string', enum=options)))
            review[ref] = dict(oneOf=[closed, opened])
        properties['qualification_review'] = obj(review)
    properties.update(edges=dict(type='array', items=edge, maxItems=0 if leaf else 48), overview=obj(overview))
    return root(phase, properties)


def _semantic_choice_module():
    # The private inference server is also used as a standalone script. Only
    # this profile needs its matching source contract from the same release.
    from importlib.util import module_from_spec, spec_from_file_location
    path = Path(__file__).resolve().parents[1] / 'services/ai_inference/analysis_plan_source_choices.py'
    spec = spec_from_file_location('cocolon_plan_source_choices', path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _semantic_plan_choice_view(material):
    return _semantic_choice_module().restore_view(material)


@lru_cache(maxsize=1)
def _semantic_merge_wire_module():
    from importlib.util import module_from_spec, spec_from_file_location
    path = Path(__file__).resolve().parents[1] / 'services/ai_inference/analysis_merge_wire.py'
    spec = spec_from_file_location('cocolon_analysis_merge_wire', path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _semantic_merge_prefix_offset(profile, material, messages, prompt_tokens):
    if (profile == 'event_plan' and isinstance(material, dict)
            and 'merge_wire_version' in material
            and _semantic_merge_wire_module().is_compact(messages)):
        return prompt_tokens
    return 0


def _semantic_merge_tuple_output(messages):
    material = json.loads(messages[1]['content'])
    return (isinstance(material, dict) and 'merge_wire_version' in material
            and material['merge_wire_version'] in _semantic_merge_wire_module().OUTPUT_VERSIONS)


def _merge_record_anchors(messages):
    material = json.loads(messages[1]['content'])
    if not isinstance(material, dict) or 'merge_wire_version' not in material:
        return False
    wire = _semantic_merge_wire_module()
    return material['merge_wire_version'] in (wire.RECORD_VERSION, *wire.OUTPUT_VERSIONS)


def _semantic_constraint_messages(messages):
    """Check the original source bindings while the model reads the compact request."""
    material = json.loads(messages[1]['content'])
    if isinstance(material, dict) and (
            'merge_wire_version' in material or 'merge_original_messages_sha256' in material):
        return _semantic_merge_wire_module().legacy_messages(messages)
    return messages


def semantic_output_schema(messages):
    """Constrain protocol and source quotes; meanings remain model-generated."""
    if (type(messages) is not list or len(messages) != 2
            or messages[1].get('role') != 'user'):
        raise ValueError('semantic_material_invalid')
    wire_version = json.loads(messages[1]['content']).get('merge_wire_version')
    bound_titles = wire_version is not None and wire_version == _semantic_merge_wire_module().VERSION
    merge_anchors = _merge_record_anchors(messages)
    messages = _semantic_constraint_messages(messages)
    material = json.loads(messages[1]['content'])
    if type(material) is dict and material.get('model_schema') == IF_CANDIDATE_SCHEMA:
        return _if_output_schema(material)
    if material.get('author_profile') in {OCCURRENCE_V11_PROFILE, *FACT_REFERENCE_PROFILES} and material.get('author_phase') == 'PLAN':
        original, choices, allowed = _semantic_plan_choice_view(material)
        inverse = {}
        for (field, key), quote in choices.items():
            inverse.setdefault((field, quote), []).append(key)
        pairs = []
        for f in original['fields']:
            number = f['field']
            quotes = [key for q in sorted(allowed[number]) for key in inverse.get((number, q), [q])]
            if quotes:
                pairs.append(dict(type='object', properties=dict(quote=dict(type='string', enum=quotes),
                    field=dict(type='integer', enum=[number])), required=['quote', 'field'], additionalProperties=False))
        if not pairs:
            raise ValueError('semantic_quotes_unavailable')
        owners = _semantic_choice_module().record_plan_owners(original,
            {field for field, options in allowed.items() if options}, merge_anchors=merge_anchors)
        return _semantic_node_local_v4_schema(material, pairs, [], record_owners=owners)
    fields = material.get('fields')
    if type(fields) is not list or not fields:
        raise ValueError('semantic_fields_invalid')
    stage = material.get('history_stage', {}).get('kind')
    history, leaf = stage in {'LEAF', 'MERGE'}, stage == 'LEAF'
    pairs, seen, unknown_pairs = [], set(), []
    event_v2 = material.get('model_schema') == EVENT_PLAN_V2_SCHEMA
    node_local = material.get('model_schema') in {NODE_LOCAL_V3_SCHEMA, NODE_LOCAL_V4_SCHEMA}
    source_qualified = event_v2 or node_local
    quoted_records, correction_fields = set(), 0
    full_actions = ({field: text for field, text, _ in _semantic_choice_module().compact_action_pairs(material).values()}
                    if material.get('author_profile') in {OCCURRENCE_V18_PROFILE, OCCURRENCE_V19_PROFILE, OCCURRENCE_V20_PROFILE, OCCURRENCE_V21_PROFILE, OCCURRENCE_V22_PROFILE, OCCURRENCE_V23_PROFILE, OCCURRENCE_V24_PROFILE} else {})
    for field in fields:
        number, original = field.get('field'), field.get('text')
        if type(number) is not int or number < 1 or number in seen or type(original) is not str:
            raise ValueError('semantic_field_invalid')
        seen.add(number)
        # Long fields stay complete in messages. Offer real, unique spans
        # within the existing quote budget rather than changing any source.
        # Upstream enum parsing does not round-trip every JSON escape. Select
        # literal spans between those characters, without altering material.
        fragments = re.findall(r'[^"\\\x00-\x1f]+', original)
        spans = [fragment[start:start + 4000].strip() for fragment in fragments
            for start in range(0, len(fragment), 2000)]
        # A map correction requires its complete explanation at admission.
        # Other fields can quote a unique sentence inside a long paragraph.
        if field.get('source_role') != 'USER_ANALYSIS_MAP_CORRECTION':
            sentences = _semantic_sentence_quotes(original)
            short = [span for span in sentences if len(span) <= 160] if leaf else []
            # Only the private leaf reading is compact. Its complete input is
            # unchanged, and fields without a short sentence keep old options.
            spans = short if short else spans + sentences
            if source_qualified:
                # Reuse sentence boundaries rather than asking for whole
                # paragraphs repeatedly. Full source remains in messages.
                compact = [span for span in sentences if len(span) <= 240]
                spans = compact if compact else spans
        if source_qualified:
            sentences = _semantic_sentence_quotes(original)
            qualifications = list(sentences)
            for left, right in zip(sentences, sentences[1:]):
                start = original.index(left)
                end = original.index(right) + len(right)
                qualifications.append(original[start:end])
            qualifications = list(dict.fromkeys(span for span in qualifications
                if 0 < len(span) <= 240 and original.count(span) == 1
                and not re.search(r'["\\\x00-\x1f]', span)))
            if field.get('source_role') != 'USER_ANALYSIS_MAP_CORRECTION':
                # A qualification that retains its antecedent must also be
                # selectable as one enclosing event root, not two fragments.
                spans = list(dict.fromkeys(spans + qualifications))
            if (material.get('author_profile') in {OCCURRENCE_V4_PROFILE, OCCURRENCE_V5_PROFILE, OCCURRENCE_V6_PROFILE, OCCURRENCE_V7_PROFILE, OCCURRENCE_V8_PROFILE, *SOURCE_CUED_PROFILES}
                    and material.get('author_phase') == 'NODES'):
                # Add only possible unknowns. PLAN/assigned_evidence keeps the
                # full root containing the known context and its qualification.
                qualifications = list(dict.fromkeys(qualifications
                    + _semantic_sentence_quotes(original, qualification_tails=True)))
            if qualifications:
                unknown_pairs.append(dict(type='object', properties=dict(
                    source_quote=dict(type='string',enum=qualifications),
                    source_field=dict(type='integer',enum=[number])),
                    required=['source_quote','source_field'],additionalProperties=False))
        if number in full_actions:
            spans.append(full_actions[number])
        spans = list(dict.fromkeys(span for span in spans if span and original.count(span) == 1
            and not re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', span)))
        if spans:
            pairs.append(dict(type='object', properties=dict(quote=dict(type='string', enum=spans),
                field=dict(type='integer', enum=[number])), required=['quote', 'field'], additionalProperties=False))
            if type(field.get('record')) is int and field['record'] > 0:
                quoted_records.add(field['record'])
            if field.get('source_role') == 'USER_ANALYSIS_MAP_CORRECTION':
                correction_fields += 1
    if not pairs:
        raise ValueError('semantic_quotes_unavailable')
    if material.get('model_schema') == EVENT_PLAN_SCHEMA:
        return _semantic_event_plan_schema(pairs, leaf=leaf)
    if event_v2:
        return _semantic_event_plan_v2_schema(pairs, unknown_pairs, leaf=leaf)
    if material.get('model_schema') == NODE_LOCAL_V4_SCHEMA:
        return _semantic_node_local_v4_schema(material, pairs, unknown_pairs, leaf=leaf, bound_titles=bound_titles)
    if node_local:
        return _semantic_node_local_v3_schema(pairs, unknown_pairs, leaf=leaf)
    def text(maximum):
        return dict(type='string', minLength=1, maxLength=maximum)
    def obj(properties):
        return dict(type='object', properties=properties, required=list(properties), additionalProperties=False)
    # Keep enough slots for every original-record anchor and every mandatory
    # whole correction, with two roots per leaf node. This is not final layout.
    node_limit = (min(24, max(2, len(quoted_records),
        (len(quoted_records) + correction_fields + 1) // 2)) if leaf else 24)
    title_limit = 36 if leaf else 60 if history else 80
    node_ids = ['n' + str(i) for i in range(1, 25)]
    node = obj(dict(node_id=dict(type='string', enum=node_ids),
        node_kind=dict(type='string', enum=['SELF_POSITION', 'TARGET_MEANING', 'CHOICE_OUTPUT', 'STATE_CONTEXT']),
        title=text(title_limit), summary=text(100 if leaf else 160 if history else 400),
        explanation=text(240 if leaf else 420 if history else 3000),
        perspective=dict(type='string', enum=['SELF', 'OBSERVED_INTERACTION']),
        unknowns=dict(type='array', items=text(160 if leaf else 240 if history else 500), maxItems=4),
        evidence=dict(type='array', items=dict(oneOf=pairs), minItems=1, maxItems=2 if leaf else 4)))
    # Select a real source before interpreting it. Receiver keys and the
    # full source text stay unchanged; this is private decoding order.
    properties = node['properties']
    node = obj(dict(evidence=properties['evidence'], **{
        key: value for key, value in properties.items() if key != 'evidence'}))
    edge = obj({'from': dict(type='string', enum=node_ids), 'to': dict(type='string', enum=node_ids),
        'relation_kind': dict(type='string', enum=['SELF_OUTSIDE_GAP', 'CRITERION_EXPRESSION', 'CONTEXT_CONTRAST', 'SHARED_MEANING']),
        'label': text(60 if history else 80), 'explanation': text(360 if history else 1800)})
    properties = dict(schema_version=dict(type='string', enum=['cocolon.analysis.semantic_map.model.v2']),
        overview=obj(dict(title=text(title_limit), summary=text(160 if leaf else 480 if history else 2000))),
        nodes=dict(type='array', items=node, minItems=1, maxItems=node_limit),
        edges=dict(type='array', items=edge, maxItems=0 if leaf else 48))
    # A summary can condition on the completed meanings and relations.
    # All receiver keys, source options and profile capacities stay unchanged.
    properties = {key: properties[key] for key in ('schema_version', 'nodes', 'edges', 'overview')}
    return obj(properties)


def _if_json_schema_parser(schema, config):
    """Keep exact JSON-escaped source quotes inside the existing IF grammar.

    The pinned upstream parser compares decoded enum strings to raw JSON
    characters. Isolate its namespace so this correction cannot change the
    ordinary Analysis or Piece parsers. No generated text is rewritten.
    """
    import importlib.util
    from lmformatenforcer import jsonschemaparser as upstream
    from lmformatenforcer.characterlevelparser import StringParser, UnionParser

    spec = importlib.util.spec_from_file_location('lmformatenforcer._cocolon_if_jsonschema', upstream.__file__)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    alphabet = frozenset(config.alphabet)

    def enum_literal(value):
        raw = json.dumps(value, ensure_ascii=False)
        return ''.join(char if char != '\ufffd' and (ord(char) < 128 or char in alphabet)
            else json.dumps(char, ensure_ascii=True)[1:-1] for char in raw)

    class ExactJsonEnum(module.StringParsingState):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.exact = (UnionParser([StringParser(enum_literal(value))
                for value in self.allowed_strings]) if self.allowed_strings
                and self.require_opening_quote and self.require_closing_quote else None)
            self.raw_prefix = ''

        def _clone(self):
            result = type(self)(self.root, self.allowed_strings, self.require_opening_quote,
                self.require_closing_quote, self.min_length, self.max_length, self.pattern, self.regex_parser)
            for key in ('parsed_string', 'seen_opening_quote', 'seen_closing_quote', 'exact', 'raw_prefix'):
                setattr(result, key, getattr(self, key))
            return result

        def add_character(self, char):
            if self.exact is None:
                return super().add_character(char)
            if (not self.seen_opening_quote or self.seen_closing_quote) and char in module.WHITESPACE_CHARACTERS:
                return self
            result = self._clone()
            result.exact = self.exact.add_character(char)
            result.raw_prefix += char
            result.seen_opening_quote = True
            result.seen_closing_quote = result.exact.can_end()
            result.parsed_string = json.loads(result.raw_prefix) if result.seen_closing_quote else result.raw_prefix[1:]
            return result

        def get_allowed_characters(self):
            if self.exact is None:
                return super().get_allowed_characters()
            if self.seen_closing_quote:
                return module.WHITESPACE_CHARACTERS
            return self.exact.get_allowed_characters() + (module.WHITESPACE_CHARACTERS if not self.seen_opening_quote else '')

    def is_object_slot(item):
        return item.type == 'object' or bool(item.oneOf) and all(
            part.type == 'object' for part in item.oneOf)

    class EmptyAwareList(module.ListParsingState):
        def add_character(self, char):
            if isinstance(self.list_member_type, list):
                # Only IF's fixed prefixItems object tuples use this path;
                # nested values keep upstream behavior.
                if not self.list_member_type or any(not is_object_slot(item) for item in self.list_member_type):
                    raise ValueError('if_object_tuple_invalid')
                result = module.PrimitiveParsingState.add_character(self, char)
                if char == '[':
                    result.seen_list_opener = True
                    result.root.context.active_parser.object_stack.append(
                        module.get_parser(result.root, result.list_member_type[0]))
                elif char == ',' and not result.seen_list_closer:
                    result.num_items_seen += 1
                    result.root.context.active_parser.object_stack.append(
                        module.get_parser(result.root, result.list_member_type[result.num_items_seen]))
                elif char == ']':
                    result.seen_list_closer = True
                return result
            if char == '[' and self.max_items == 0 and not self.seen_list_opener:
                # Upstream otherwise pushes an item parser even for maxItems=0.
                result = self._clone()
                result.parsed_string += char
                result.seen_list_opener = True
                return result
            return super().add_character(char)

    module.StringParsingState = ExactJsonEnum
    module.ListParsingState = EmptyAwareList
    generic_get_parser = module.get_parser
    def if_get_parser(root, value):
        prefix = value.extras.get('prefixItems') if value.type == 'array' else None
        if prefix is not None:
            if (type(prefix) is not list or not prefix
                    or value.minItems != len(prefix) or value.maxItems != len(prefix)):
                raise ValueError('if_object_tuple_invalid')
            members = [module.JsonSchemaObject(**item) for item in prefix]
            if any(not is_object_slot(item) for item in members):
                raise ValueError('if_object_tuple_invalid')
            return EmptyAwareList(root, members, len(members), len(members))
        return generic_get_parser(root, value)
    module.get_parser = if_get_parser
    return module.JsonSchemaParser(schema, config=config)


@lru_cache(maxsize=512)
def _fact_escape_examples(start, end, *, numeric=False):
    """ASCII controls syntax. Other scalars affect a fact as a word, space, or symbol."""
    ascii_values = list(range(start, min(end, 127) + 1))
    examples = {}
    for code in range(max(start, 128), end + 1):
        char = chr(code)
        kind = ((char.isalpha(), char.isdigit(), char.isalnum(), char.isspace()) if numeric
                else (char.isalnum(), char.isspace()))
        examples.setdefault(kind, code)
        if len(examples) == (5 if numeric else 3):
            break
    return tuple(ascii_values + list(examples.values()))


def _semantic_unique_json_schema_parser(schema, config, *, record_fields=None, bound_node_ids=(),
                                        unique_qualifications=False, endpoint_nodes=(), unique_allocations=False,
                                        plan_source_texts=None, plan_choice_quotes=None, overview_sources=None, protect_visible=False,
                                        compare_title_end_marks=False, record_owners=(), compact_pairs=(), reading_regions=(), required_sources=None, merge_anchors=False, action_sources=()):
    """Bind graph references and unique source/quote pairs while decoding.

    The pinned parser does not enforce JSON Schema uniqueItems. Use an isolated
    namespace, as for IF, so evidence selection stays immutable across decoder
    branches and cannot change ordinary Piece/IF or the installed library.
    """
    import importlib.util
    from copy import deepcopy
    from lmformatenforcer import jsonschemaparser as upstream
    spec = importlib.util.spec_from_file_location(
        'lmformatenforcer._cocolon_semantic_unique_jsonschema', upstream.__file__)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    from copy import copy
    from lmformatenforcer.characterlevelparser import StringParser, UnionParser
    alphabet = frozenset(config.alphabet)
    record_fields = dict(record_fields or {})
    required_records = frozenset(record_fields.values())
    paired_check = _semantic_choice_module().paired_original_root if compact_pairs else None
    marker = schema.get('properties', {}).get('schema_version', {}).get('enum')
    plan_only = marker == [NODE_LOCAL_V4_SCHEMA + '.plan']
    relations_only = marker == [NODE_LOCAL_V4_SCHEMA + '.relations']
    node_local = marker == [NODE_LOCAL_V3_SCHEMA] or plan_only or relations_only
    plan_choice_quotes = plan_choice_quotes or {}
    def evidence_pair_key(field, quote):
        return field, plan_choice_quotes.get((field, quote), quote)

    if unique_allocations:
        units_schema = schema['properties']['nodes']['items']['properties']['units']
        roots_schema = units_schema['items']['properties']['evidence']
        plan_roots = tuple(dict.fromkeys(evidence_pair_key(part['properties']['field']['enum'][0], quote)
            for part in roots_schema['items']['oneOf'] for quote in part['properties']['quote']['enum']))
        if plan_source_texts is not None:
            # A short quote and an extended quote from the same start identify the same lead.
            lead_positions = {(field, quote): (field, plan_source_texts[field].index(quote))
                              for field, quote in plan_roots}

    missing_sources_in = _semantic_choice_module().missing_plan_sources if required_sources else None

    def uncovered_sources(graph):
        return missing_sources_in(required_sources, (*graph.previous_allocations, graph.plan_allocation))

    def can_add_root(allocation, previous):
        # Search only while a prefix could finish as an already completed node.
        # One distinct complete allocation is enough, even if every root is shared.
        roots = allocation[-1]
        return len(roots) < roots_schema['maxItems'] and any(
            can_finish(allocation[:-1] + (roots + (pair,),), previous)
            for pair in plan_roots if pair not in roots)

    def can_close_unit(allocation, previous):
        return (allocation not in previous or len(allocation) < units_schema['maxItems']
            and can_add_root(allocation + ((),), previous))

    def can_finish(allocation, previous):
        if plan_source_texts is not None and len(allocation) == 1 and len(allocation[0]) == 1:
            lead = lead_positions[allocation[0][0]]
            return all(lead != lead_positions[node[0][0]] for node in previous)
        return can_close_unit(allocation, previous) or can_add_root(allocation, previous)

    endpoint_titles = {node['node_id']: node['title'] for node in endpoint_nodes}
    cue_edges = relations_only and 'from_source' in schema['properties']['edges']['items']['properties']
    unit_cues = {f"{node['node_id']}.u{i}": list(dict.fromkeys(cue for root in unit['evidence']
                 for cue in _semantic_source_cues(root['quote'])))
                 for node in endpoint_nodes for i, unit in enumerate(node['units'], 1)} if cue_edges else {}
    closer_rules = _semantic_choice_module() if protect_visible else None
    label_alphabet = ''.join(c for c in config.alphabet if ord(c) >= 32 and c not in '"\\')

    def enum_literal(value):
        raw = json.dumps(value, ensure_ascii=False)
        return ''.join(char if char != '\ufffd' and (ord(char) < 128 or char in alphabet)
            else json.dumps(char, ensure_ascii=True)[1:-1] for char in raw)

    class ExactJsonEnum(module.StringParsingState):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.exact = (UnionParser([StringParser(enum_literal(value))
                for value in self.allowed_strings]) if self.allowed_strings
                and self.require_opening_quote and self.require_closing_quote else None)
            self.raw_prefix = ''

        def _clone(self):
            # Enum branches and string states are immutable across transitions.
            return copy(self)

        def add_character(self, char):
            if self.exact is None:
                return super().add_character(char)
            if (not self.seen_opening_quote or self.seen_closing_quote) and char in module.WHITESPACE_CHARACTERS:
                return self
            result = self._clone()
            result.exact = self.exact.add_character(char)
            result.raw_prefix += char
            result.seen_opening_quote = True
            result.seen_closing_quote = result.exact.can_end()
            result.parsed_string = json.loads(result.raw_prefix) if result.seen_closing_quote else result.raw_prefix[1:]
            return result

        def get_allowed_characters(self):
            if self.exact is None:
                return super().get_allowed_characters()
            if self.seen_closing_quote:
                return module.WHITESPACE_CHARACTERS
            return self.exact.get_allowed_characters() + (module.WHITESPACE_CHARACTERS if not self.seen_opening_quote else '')

    module.StringParsingState = ExactJsonEnum

    class EndpointLabel(module.PrimitiveParsingState):
        """Keep both endpoint titles out of this label, including JSON escape spellings."""
        def __init__(self, root, titles, maximum):
            super().__init__(root)
            self.titles = titles
            self.maximum = maximum
            self.minimum = 1
            self.source_runs = None
            self.opened = self.closed = False
            self.raw = self.text = self.escape = ''

        def can_end(self):
            return self.closed

        def bound(self, text):
            return self.source_runs is None or closer_rules.visible_closers_bound(text, self.source_runs)

        def forbidden(self, text):
            return text in self.titles

        def still_guarded(self, text):
            return any(title.startswith(text) for title in self.titles)

        def final_content(self, text, alphabet):
            for title in self.titles:
                if len(title) == self.maximum and title[:-1] == text:
                    alphabet = alphabet.replace(title[-1], '')
            return alphabet

        @property
        def guarded_shortcut(self):
            return (self.opened and not self.closed and not self.escape
                    and len(self.text) < self.maximum and not (self.text and '\ud800' <= self.text[-1] <= '\udbff')
                    and getattr(self.root.context, 'guard_endpoint_label_tokens', False))

        def get_allowed_characters(self):
            if self.closed:
                return ''
            if not self.opened:
                return '"' + module.WHITESPACE_CHARACTERS
            if self.escape:
                if self.escape == '\\':
                    choices = '"\\/bfnrtu'
                else:
                    choices = '0123456789abcdefABCDEF'
                # A high surrogate at the length limit only has room for its
                # low surrogate. Prefixes of that second escape stay viable.
                if self.text and '\ud800' <= self.text[-1] <= '\udbff' and len(self.text) == self.maximum:
                    if self.escape == '\\':
                        return 'u'
                    if self.escape == '\\u':
                        return 'dD'
                    if len(self.escape) == 3:
                        return 'cCdDeEfF'
                if self.escape == '\\' or len(self.escape) == 5:
                    for char in choices:
                        if self.escape == '\\' and char == 'u':
                            continue
                        decoded = json.loads('"' + self.raw + char + '"')
                        if (len(decoded) > self.maximum or len(decoded) == self.maximum and self.forbidden(decoded)
                                or decoded[-1:] in ('}', ']') and not self.bound(decoded)):
                            choices = choices.replace(char, '')
                return choices
            chars = '"' if len(self.text) >= self.minimum and not self.forbidden(self.text) else ''
            if len(self.text) < self.maximum:
                content = label_alphabet
                if self.source_runs is not None:
                    for closer in '}]':
                        if not self.bound(self.text + closer):
                            content = content.replace(closer, '')
                if len(self.text) + 1 == self.maximum:
                    content = self.final_content(self.text, content)
                chars += content + '\\'
            elif self.text and '\ud800' <= self.text[-1] <= '\udbff':
                chars += '\\'
            return chars

        def add_character(self, char):
            result = copy(self)
            if not result.opened:
                result.opened = char == '"'
                return result
            if not result.escape and char == '"':
                result.closed = True
                return result
            result.raw += char
            if result.escape:
                result.escape += char
                if result.escape.startswith('\\u') and len(result.escape) < 6:
                    return result
                result.escape = ''
            elif char == '\\':
                result.escape = char
                return result
            result.text = json.loads('"' + result.raw + '"')
            if result.source_runs is not None or result.still_guarded(result.text):
                return result
            if result.text and '\ud800' <= result.text[-1] <= '\udbff':
                return result
            # Further characters cannot turn a different prefix into a title.
            # Only here may the ordinary LMFE free-text shortcut resume.
            ordinary = module.StringParsingState(result.root, [], True, True, 1, result.maximum)
            ordinary.seen_opening_quote = True
            ordinary.parsed_string = result.text
            return ordinary

    class SourceTitle(EndpointLabel):
        """Compare a multi-record title to one-record evidence through its ending."""
        def forbidden(self, text):
            return closer_rules.source_title_key(text) in self.titles

        def still_guarded(self, text):
            return self.forbidden(text) or super().still_guarded(text)

        def final_content(self, text, alphabet):
            if self.forbidden(text):
                alphabet = alphabet.translate(dict.fromkeys(map(ord, closer_rules.TITLE_END_MARKS)))
            # A nonseparator can match a normalized title only as its final character.
            for title in self.titles:
                if title[:-1] == text:
                    alphabet = alphabet.replace(title[-1], '')
            return alphabet

    class OverviewTitle(SourceTitle):
        def __init__(self, root, titles, maximum, phrases):
            super().__init__(root, titles, maximum)
            self.phrases = phrases

        def forbidden(self, text):
            return super().forbidden(text) or self.phrases.omits_record(text)

        def final_content(self, text, alphabet):
            alphabet = super().final_content(text, alphabet)
            for char in self.phrases.end_chars:
                if char in alphabet and self.phrases.omits_record(text + char):
                    alphabet = alphabet.replace(char, '')
            return alphabet

    class GroundedOverview(OverviewTitle):
        def __init__(self, root, titles, maximum, phrases, scope):
            super().__init__(root, titles, maximum, phrases)
            self.scope = scope
            self.required_tail = None

        def forbidden(self, text):
            return (text != self.scope.neutral
                    and (not self.scope.accepts(text) or super().forbidden(text)))

        def get_allowed_characters(self):
            if self.required_tail is not None:
                return self.required_tail.get_allowed_characters()
            return super().get_allowed_characters()

        def add_character(self, char):
            if self.required_tail is not None:
                result = copy(self)
                result.required_tail = self.required_tail.add_character(char)
                result.closed = result.required_tail.can_end()
                return result
            result = super().add_character(char)
            if not result.opened or result.closed or result.escape:
                return result
            tail = result.scope.completion(result.text)
            reserve = 1 if result.text or not tail else 2
            if tail is not None and len(result.text) + len(tail) + reserve <= result.maximum:
                return result
            # Reserve a complete source-supported path before the 80-character
            # title fills up. A neutral heading remains available even when two
            # originals have no independently identifiable words.
            choices = []
            if tail is not None and len(result.text) + len(tail) <= result.maximum:
                choices.append(tail)
            if result.scope.neutral.startswith(result.text):
                choices.append(result.scope.neutral[len(result.text):])
            if not choices:
                raise ValueError('semantic_overview_title_continuation_unavailable')
            result.required_tail = UnionParser([StringParser(enum_literal(value)[1:]) for value in choices])
            return result

    class OverviewProposal(EndpointLabel):
        """Retain the decoded private proposal for the following final title choice."""
        def still_guarded(self, text):
            return True

        def add_character(self, char):
            result = super().add_character(char)
            if result.closed:
                stack = result.root.context.active_parser.object_stack
                overview = stack[-2].clone()
                overview.title_proposal = result.text
                stack[-2] = overview
            return result

    class FactProse(EndpointLabel):
        """Only intercept a whole unmatched numeric handle. Ordinary prose stays free."""
        assigned_source = None
        source_bound_keys = False
        source_bound_members = False

        def forbidden(self, text):
            value = text.strip()
            if self.assigned_source is not None:
                if re.fullmatch(r'@[0-9]+', value):
                    if value in closer_rules.literal_fact_handles(self.assigned_source):
                        return False
                    return text != value or value not in self.titles
                return (not closer_rules.source_fact_text(text, self.assigned_source)
                        or self.source_bound_keys and not closer_rules.source_fact_keys_bound(text, self.assigned_source)
                        or self.source_bound_members and not (closer_rules.source_fact_members_bound(text, self.assigned_source)
                            and closer_rules.source_fact_numeric_bound(text, self.assigned_source)))
            return re.fullmatch(r'@[1-9][0-9]*', value) is not None and value not in self.titles

        def bound(self, text):
            if self.source_bound_members and closer_rules.fact_starts_with_member(text):
                return any(not self.forbidden(text + tail[:i])
                           for tail in closer_rules.fact_member_suffixes(text, self.assigned_source, self.maximum)
                           for i in range(len(tail) + 1))
            return (super().bound(text) and (self.assigned_source is None or not text.endswith('>')
                    or closer_rules.source_markup_bound(text, self.assigned_source))
                    and (not self.source_bound_keys or not text.endswith('/')
                         or closer_rules.source_fact_keys_bound(text, self.assigned_source))
                    and (not self.source_bound_members or closer_rules.source_fact_members_bound(text, self.assigned_source)))

        def get_allowed_characters(self):
            if self.assigned_source is None or not self.opened or self.closed:
                return super().get_allowed_characters()
            high = bool(self.text and 0xd800 <= ord(self.text[-1]) <= 0xdbff)
            if high and not self.escape:
                return '\\'
            if high and self.escape == '\\':
                return 'u'
            quoted_member = self.source_bound_members and closer_rules.fact_starts_with_member(self.text)
            if self.escape.startswith('\\u') and (quoted_member or high or self.escape[2:3].lower() == 'd'
                                                       or len(self.text) + 1 == self.maximum):
                # Keep an escape prefix only if a completed scalar can still end
                # the field at its limit. A surrogate pair consumes one scalar.
                digits = self.escape[2:]
                return ''.join(c for c in '0123456789abcdefABCDEF'
                               if self.escape_can_finish(digits + c, high))
            allowed = super().get_allowed_characters()
            if self.escape and len(self.escape) == 5:
                return ''.join(c for c in allowed if self.bound(json.loads('"' + self.raw + c + '"')))
            if self.source_bound_keys and self.escape in ('', '\\') and '/' in allowed and not self.bound(self.text + '/'):
                allowed = allowed.replace('/', '')
            if not self.escape and '>' in allowed and not self.bound(self.text + '>'):
                allowed = allowed.replace('>', '')
            if self.source_bound_members:
                if not self.escape:
                    if quoted_member:
                        # The prefix is now a source quotation. Keep only actual next
                        # characters; closing the JSON string is handled by forbidden().
                        subsequent = {tail[0] for tail in closer_rules.fact_member_suffixes(
                            self.text, self.assigned_source, self.maximum) if tail}
                        viable = {c for c in subsequent if self.bound(self.text + c)}
                        if viable:
                            viable.add('\\')
                        viable.add('"')  # The closing delimiter was checked by forbidden().
                        allowed = ''.join(c for c in allowed if c in viable)
                    else:
                        for c in "':{[}]":
                            if c in allowed and not self.bound(self.text + c):
                                allowed = allowed.replace(c, '')
                elif self.escape == '\\':
                    escaped = {'"': '"', '/': '/', '\\': '\\', 'b': '\b', 'f': '\f', 'n': '\n', 'r': '\r', 't': '\t'}
                    allowed = ''.join(c for c in allowed if c == 'u' or self.bound(self.text + escaped[c]))
            return allowed

        def escape_can_finish(self, digits, high):
            lo = int(digits.ljust(4, '0'), 16)
            hi = int(digits.ljust(4, 'f'), 16)
            base = self.text[:-1] if high else self.text
            if high:
                offset = 0x10000 + (ord(self.text[-1]) - 0xd800) * 1024 - 0xdc00
                intervals = [(max(lo, 0xdc00) + offset, min(hi, 0xdfff) + offset)]
            else:
                # Test directly encoded scalars before supplementary planes.
                first, last = max(lo, 0xd800), min(hi, 0xdbff)
                intervals = [(lo, min(hi, 0xd7ff)), (max(lo, 0xe000), hi),
                             (0x10000 + (first-0xd800)*1024, 0x10000 + (last-0xd800+1)*1024-1)]
            for start, end in intervals:
                if end < start:
                    continue
                # Literal source characters can also complete a source-supported
                # tag or symbol. Other non-ASCII characters of one class are
                # equivalent for this upper-bound check.
                samples = _fact_escape_examples(start, end, numeric=self.source_bound_members)
                source = (ord(c) for c in self.assigned_source if start <= ord(c) <= end)
                for code in (*samples, *source):
                    value = base + chr(code)
                    if self.bound(value) and (len(value) < self.maximum or not self.forbidden(value)):
                        return True
            return False

        def still_guarded(self, text):
            value = text.strip()
            return not value or value == '@' or re.fullmatch(r'@[1-9][0-9]*', value) is not None

        def final_content(self, text, alphabet):
            return ''.join(c for c in alphabet if not self.forbidden(text + c))

    if endpoint_titles or protect_visible:
        ordinary_shortcut = module.JsonSchemaParser.shortcut_key
        def shortcut(parser):
            current = parser.object_stack[-1] if parser.object_stack else None
            if isinstance(current, EndpointLabel) and current.guarded_shortcut:
                return ('json_freetext', len(current.text), current.minimum, current.maximum)
            return ordinary_shortcut(parser)
        module.JsonSchemaParser.shortcut_key = shortcut

    def evidence_pair(value):
        props = value.properties or {}
        return (value.type == 'object' and set(props) == {'field', 'quote'}
            and props['field'].type == 'integer' and len(props['field'].enum or []) == 1
            and props['quote'].type == 'string' and bool(props['quote'].enum))

    def qualification_pair(value):
        props = value.properties or {}
        return (unique_qualifications and value.type == 'object'
            and set(props) == {'source_field', 'source_quote'}
            and props['source_field'].type == 'integer' and len(props['source_field'].enum or []) == 1
            and props['source_quote'].type == 'string' and bool(props['source_quote'].enum))

    def node_type(value):
        props = value.properties or {}
        return value.type == 'object' and (('node_id' in props and (
            'evidence' in props or 'event_refs' in props or 'unit_refs' in props))
            or node_local and set(props) == {'units', 'node_kind', 'perspective', 'title', 'meaning'}
            or plan_only and set(props) == {'node_id', 'units'})

    def local_unit_type(value):
        return node_local and value.type == 'object' and (
            set(value.properties or {}) == {'evidence', 'source_mode', 'fact', 'unknowns'}
            or plan_only and set(value.properties or {}) == {'evidence'})

    def event_type(value):
        return value.type == 'object' and 'event_id' in (value.properties or {})

    def reading_type(value):
        return value.type == 'object' and 'reading_id' in (value.properties or {})

    def graph_type(value):
        props = value.properties or {}
        return value.type == 'object' and (
            'nodes' in props and 'edges' in props or plan_only and 'nodes' in props
            or relations_only and {'edges', 'overview'} <= set(props))

    def edge_type(value):
        props = value.properties or {}
        return value.type == 'object' and (set(props) in ({
            'from', 'to', 'relation_kind', 'label', 'explanation'},
            {'from','to','relation_kind','label','event_refs','reading_refs'},
            {'from','to','relation_kind','label','unit_refs'})
            or node_local and set(props) in ({'from', 'to', 'relation_kind', 'label'},
                {'from', 'to', 'from_unit', 'to_unit', 'relation_kind', 'label'},
                {'from', 'to', 'from_unit', 'to_unit', 'from_source', 'to_source', 'relation_kind', 'label'}))

    def graph_state(active):
        for index, value in enumerate(active.object_stack):
            if isinstance(value, EvidenceObject) and graph_type(value.schema_object):
                return index, value
        raise ValueError('semantic_graph_unbound')

    def edge_key(start, end, kind):
        return min(start, end), max(start, end), kind

    def remaining_edges(graph, *, start=None, end=None):
        kinds = schema['properties']['edges']['items']['properties']['relation_kind']['enum']
        for left in graph.generated_node_ids:
            if start is not None and left != start:
                continue
            for right in graph.generated_node_ids:
                if left == right or end is not None and right != end:
                    continue
                for kind in kinds:
                    if edge_key(left, right, kind) not in graph.generated_edge_keys:
                        yield left, right, kind

    class UniqueEvidenceList(module.ListParsingState):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            parts = self.list_member_type.oneOf
            self.is_evidence = bool(parts) and all(evidence_pair(p) for p in parts)
            self.is_qualification = bool(parts) and all(qualification_pair(p) for p in parts)
            self.field_key, self.quote_key = ('source_field', 'source_quote') if self.is_qualification else ('field', 'quote')
            self.is_units = local_unit_type(self.list_member_type)
            self.is_nodes = node_type(self.list_member_type)
            self.is_events = event_type(self.list_member_type)
            self.is_readings = reading_type(self.list_member_type)
            self.is_edges = edge_type(self.list_member_type)
            self.is_node_refs = (node_local and self.list_member_type.type == 'string'
                and bool(self.list_member_type.enum) and all(re.fullmatch(r'n[1-9][0-9]*', value)
                    for value in self.list_member_type.enum))
            self.used_pairs = frozenset()
            self.used_node_refs = frozenset()

        def _clone(self):
            result = super()._clone()
            result.used_pairs = self.used_pairs
            result.used_node_refs = self.used_node_refs
            return result

        def future_root_capacity(self, *, after_item=False):
            # Count only still-selectable evidence roots in this branch. Closing
            # a list may discard slots, so reserve coverage before that choice,
            # while source selection can still choose a missing record.
            active = self.root.context.active_parser
            _, graph = graph_state(active)
            node = schema['properties']['nodes']
            units = node['items']['properties']['units']
            evidence = units['items']['properties']['evidence']
            future_nodes = node['maxItems'] - len(graph.generated_node_ids) - 1
            capacity = future_nodes * units['maxItems'] * evidence['maxItems']
            if self.is_evidence:
                parent = next(value for value in reversed(active.object_stack)
                    if isinstance(value, UniqueEvidenceList) and value.is_units)
                capacity += (units['maxItems'] - parent.num_items_seen - 1) * evidence['maxItems']
                if after_item:
                    capacity += self.max_items - self.num_items_seen - 1
            return capacity

        def owner_fields(self, graph):
            index = len(graph.generated_node_ids)
            if not self.is_evidence:
                return None
            if index < len(record_owners):
                original, local = record_owners[index]
                return original if graph.plan_allocation == ((),) else local
            if merge_anchors and record_owners and graph.plan_allocation and graph.plan_allocation[-1]:
                first_field = graph.plan_allocation[-1][0][0]
                origin = record_fields.get(first_field, -first_field)
                return {field for field in plan_source_texts if record_fields.get(field, -field) == origin}
            return None

        def remaining_type(self):
            remaining = []
            owner_fields = pair = region = None
            action = None
            preceding = ()
            missing_sources = {}
            missing = frozenset()
            previous = frozenset()
            if unique_allocations:
                _, graph = graph_state(self.root.context.active_parser)
                allocation, previous = graph.plan_allocation, graph.previous_allocations
                owner_fields = self.owner_fields(graph)
                index = len(graph.generated_node_ids)
                if self.is_evidence and index < len(action_sources):
                    action = action_sources[index]
                    if action:
                        missing_action = action.missing(root for unit in allocation for root in unit)
                        future_units = units_schema['maxItems'] - len(allocation)
                        action_slots = (future_units + 1) * roots_schema['maxItems'] - len(allocation[-1]) - 1
                if required_sources and self.is_evidence and index >= len(record_owners):
                    outstanding = uncovered_sources(graph)
                    if len(outstanding) > self.future_root_capacity(after_item=True):
                        missing_sources = outstanding
                if self.is_evidence and index < len(compact_pairs):
                    pair = compact_pairs[index]
                    preceding = tuple(root for unit in allocation for root in unit)
                if self.is_evidence and index < len(reading_regions):
                    region = reading_regions[index]
                    if region:
                        missing_regions = region.missing(allocation)
                        # The second and last unit cannot rely on another unit to finish its record.
                        remaining_slots = self.max_items - len(allocation[-1]) - 1 if len(allocation) == 2 else 4
            if node_local and required_records and owner_fields is None:
                _, graph = graph_state(self.root.context.active_parser)
                uncovered = required_records - graph.covered_records
                if len(uncovered) > self.future_root_capacity(after_item=True):
                    missing = uncovered
            for part in self.list_member_type.oneOf:
                field = part.properties[self.field_key].enum[0]
                if owner_fields is not None and field not in owner_fields:
                    continue
                if missing and record_fields.get(field) not in missing:
                    continue
                quotes = [q for q in part.properties[self.quote_key].enum if evidence_pair_key(field, q) not in self.used_pairs]
                if missing_sources:
                    quotes = [q for q in quotes if field in missing_sources
                              and missing_sources[field] in evidence_pair_key(field, q)[1]]
                if pair:
                    quotes = [q for q in quotes if paired_check(pair, preceding, *evidence_pair_key(field, q))]
                if action and missing_action:
                    quotes = [q for q in quotes if action.minimum_roots[
                        missing_action & ~action.coverage(*evidence_pair_key(field, q))] <= action_slots]
                if region:
                    def fits(q):
                        f, quote = evidence_pair_key(field, q)
                        added = region.coverage.get(quote, 0) if f == region.field else 0
                        return (region.can_reuse(allocation[:-1], allocation[-1], f, quote)
                                and region.adds_text(allocation[-1], f, quote)
                                and region.minimum_roots[missing_regions & ~added] <= remaining_slots)
                    quotes = [q for q in quotes if fits(q)]
                if previous:
                    quotes = [q for q in quotes if can_finish(
                        allocation[:-1] + (allocation[-1] + (evidence_pair_key(field, q),),), previous)]
                if quotes:
                    part = deepcopy(part)
                    part.properties[self.quote_key].enum = quotes
                    remaining.append(part)
            result = deepcopy(self.list_member_type)
            result.oneOf = remaining
            return result if remaining else None

        def get_allowed_control_characters(self):
            chars = super().get_allowed_control_characters()
            if unique_allocations and self.seen_list_opener and not self.seen_list_closer and (',' in chars or ']' in chars):
                _, graph = graph_state(self.root.context.active_parser)
                allocation, previous = graph.plan_allocation, graph.previous_allocations
                if previous:
                    if self.is_nodes and ',' in chars and not can_add_root(((),), previous):
                        chars = chars.replace(',', '')
                    if self.is_units and allocation:
                        if allocation in previous:
                            chars = chars.replace(']', '')
                        if ',' in chars and not can_add_root(allocation + ((),), previous):
                            chars = chars.replace(',', '')
                    if self.is_evidence and allocation:
                        if not can_close_unit(allocation, previous):
                            chars = chars.replace(']', '')
                        if ',' in chars and not can_add_root(allocation, previous):
                            chars = chars.replace(',', '')
            if required_sources and ']' in chars and (self.is_nodes or self.is_units or self.is_evidence):
                _, graph = graph_state(self.root.context.active_parser)
                if self.is_nodes:
                    if uncovered_sources(graph):
                        chars = chars.replace(']', '')
                elif (len(graph.generated_node_ids) >= len(record_owners)
                        and len(uncovered_sources(graph)) > self.future_root_capacity()):
                    chars = chars.replace(']', '')
            if reading_regions and (self.is_units or self.is_evidence) and (']' in chars or ',' in chars):
                _, graph = graph_state(self.root.context.active_parser)
                index = len(graph.generated_node_ids)
                region = reading_regions[index] if index < len(reading_regions) else None
                if region:
                    allocation = graph.plan_allocation
                    if (self.is_units or len(allocation) == 2) and region.missing(allocation):
                        chars = chars.replace(']', '')
                    if self.is_evidence and ',' in chars and self.remaining_type() is None:
                        chars = chars.replace(',', '')
            if compact_pairs and self.is_units and ']' in chars:
                _, graph = graph_state(self.root.context.active_parser)
                index = len(graph.generated_node_ids)
                pair = compact_pairs[index] if index < len(compact_pairs) else None
                roots = tuple(root for unit in graph.plan_allocation for root in unit)
                if pair and len(roots) == 1 and roots[0][0] == pair[0]:
                    chars = chars.replace(']', '')
            if action_sources and ']' in chars and (self.is_evidence or self.is_units):
                _, graph = graph_state(self.root.context.active_parser)
                index = len(graph.generated_node_ids)
                action = action_sources[index] if index < len(action_sources) else None
                allocation = graph.plan_allocation
                if action:
                    missing = action.missing(root for unit in allocation for root in unit)
                    future_units = 0 if self.is_units else units_schema['maxItems'] - len(allocation)
                    if action.minimum_roots[missing] > future_units * roots_schema['maxItems']:
                        chars = chars.replace(']', '')
            if record_owners and self.is_evidence and ',' in chars:
                _, graph = graph_state(self.root.context.active_parser)
                owned = self.owner_fields(graph)
                if owned is not None and not any(pair[0] in owned and pair not in self.used_pairs for pair in plan_roots):
                    chars = chars.replace(',', '')
            if (self.is_evidence or self.is_qualification) and not any(
                    evidence_pair_key(part.properties[self.field_key].enum[0], q) not in self.used_pairs
                    for part in self.list_member_type.oneOf for q in part.properties[self.quote_key].enum):
                chars = chars.replace(',', '')
            if node_local and required_records and (self.is_evidence or self.is_units):
                _, graph = graph_state(self.root.context.active_parser)
                if (len(graph.generated_node_ids) >= len(record_owners)
                        and len(required_records - graph.covered_records) > self.future_root_capacity()):
                    chars = chars.replace(']', '')
            if self.is_nodes or self.is_events:
                _, graph = graph_state(self.root.context.active_parser)
                if (self.is_events or 'events' not in schema['properties']) and required_records - graph.covered_records:
                    chars = chars.replace(']', '')
                if not node_local:
                    generated = graph.generated_event_ids if self.is_events else graph.generated_node_ids
                    key = 'event_id' if self.is_events else 'node_id'
                    if not any(value not in generated
                            for value in self.list_member_type.properties[key].enum):
                        chars = chars.replace(',', '')
            if self.is_edges:
                _, graph = graph_state(self.root.context.active_parser)
                if not any(remaining_edges(graph)):
                    chars = chars.replace(',', '')
            return chars

        def add_character(self, char):
            if char == '[' and self.max_items == 0 and not self.seen_list_opener:
                # Upstream otherwise pushes an item parser for an empty array.
                result = self._clone()
                result.parsed_string += char
                result.seen_list_opener = True
                return result
            result = super().add_character(char)
            if unique_allocations and self.is_evidence and char == '[' and not self.seen_list_opener:
                active = result.root.context.active_parser
                index, graph = graph_state(active)
                graph = graph.clone()
                graph.plan_allocation += ((),)
                active.object_stack[index] = graph
            if (self.is_evidence and node_local and (required_records or unique_allocations)
                    and char == '[' and not self.seen_list_opener):
                remaining = result.remaining_type()
                if remaining is None:
                    raise ValueError('semantic_evidence_options_exhausted')
                result.root.context.active_parser.object_stack[-1] = module.get_parser(result.root, remaining)
            if (self.is_evidence and not node_local and required_records
                    and char == '[' and not self.seen_list_opener):
                active = result.root.context.active_parser
                _, graph = graph_state(active)
                remaining_records = required_records - graph.covered_records
                if remaining_records:
                    value = deepcopy(self.list_member_type)
                    value.oneOf = [part for part in value.oneOf
                        if record_fields.get(part.properties['field'].enum[0]) in remaining_records]
                    active.object_stack[-1] = module.get_parser(result.root, value)
            if (self.is_evidence or self.is_qualification) and char == ',' and not result.seen_list_closer:
                remaining = result.remaining_type()
                if remaining is None:
                    raise ValueError('semantic_evidence_options_exhausted')
                result.root.context.active_parser.object_stack[-1] = module.get_parser(result.root, remaining)
            if self.is_node_refs and char in ',]' and not self.seen_list_closer:
                active = result.root.context.active_parser
                selected = active.last_parsed_string
                if selected not in self.list_member_type.enum or selected in self.used_node_refs:
                    raise ValueError('semantic_node_reference_unbound')
                result.used_node_refs = self.used_node_refs | {selected}
                if overview_sources and char == ']':
                    index, graph = graph_state(active)
                    graph = graph.clone()
                    graph.selected_overview_refs = result.used_node_refs
                    active.object_stack[index] = graph
                if char == ',':
                    remaining = deepcopy(self.list_member_type)
                    remaining.enum = [value for value in remaining.enum if value not in result.used_node_refs]
                    if not remaining.enum:
                        raise ValueError('semantic_node_reference_options_exhausted')
                    active.object_stack[-1] = module.get_parser(result.root, remaining)
            return result

    class EvidenceObject(module.ObjectParsingState):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.generated_node_ids = tuple(bound_node_ids) if graph_type(self.schema_object) else ()
            self.generated_event_ids = ()
            self.generated_reading_ids = ()
            self.selected_plan_id = None
            self.generated_edge_keys = frozenset()
            self.covered_records = frozenset()
            self.selected_overview_refs = frozenset()
            self.title_proposal = None
            self.previous_allocations = frozenset()
            self.plan_allocation = ()
            self.selected_node_id = self.selected_from = None
            self.selected_to = self.selected_relation_kind = None
            self.selected_from_unit = self.selected_to_unit = None
            self.selected_quote = None
            self.selected_event_roots = ()

        def clone(self):
            result = super().clone()
            result.generated_node_ids = self.generated_node_ids
            result.generated_event_ids = self.generated_event_ids
            result.generated_reading_ids = self.generated_reading_ids
            result.selected_plan_id = self.selected_plan_id
            result.generated_edge_keys = self.generated_edge_keys
            result.covered_records = self.covered_records
            result.selected_overview_refs = self.selected_overview_refs
            result.title_proposal = self.title_proposal
            result.previous_allocations = self.previous_allocations
            result.plan_allocation = self.plan_allocation
            result.selected_node_id = self.selected_node_id
            result.selected_from = self.selected_from
            result.selected_to = self.selected_to
            result.selected_from_unit = self.selected_from_unit
            result.selected_to_unit = self.selected_to_unit
            result.selected_relation_kind = self.selected_relation_kind
            result.selected_quote = self.selected_quote
            result.selected_event_roots = self.selected_event_roots
            return result

        def add_character(self, char):
            prior_key = self.current_key
            result = super().add_character(char)
            active = result.root.context.active_parser
            if char in ',}' and self.current_stage in (
                    module.ObjectParsingStage.PARSING_VALUE,
                    module.ObjectParsingStage.PARSING_SEPARATOR_OR_END):
                if (event_type(result.schema_object) and prior_key == 'event_id'
                        or reading_type(result.schema_object) and prior_key == 'reading_id'):
                    result.selected_plan_id = active.last_parsed_string
                if node_type(result.schema_object) and prior_key == 'node_id':
                    result.selected_node_id = active.last_parsed_string
                if edge_type(result.schema_object) and prior_key == 'from':
                    result.selected_from = active.last_parsed_string
                if edge_type(result.schema_object) and prior_key == 'to':
                    result.selected_to = active.last_parsed_string
                if unit_cues and edge_type(result.schema_object) and prior_key in {'from_unit', 'to_unit'}:
                    setattr(result, 'selected_' + prior_key, active.last_parsed_string)
                if edge_type(result.schema_object) and prior_key == 'relation_kind':
                    result.selected_relation_kind = active.last_parsed_string
                if (evidence_pair(result.schema_object) and prior_key == 'quote'
                        or qualification_pair(result.schema_object) and prior_key == 'source_quote'):
                    result.selected_quote = active.last_parsed_string
            if char == ':' and result.current_stage == module.ObjectParsingStage.PARSING_VALUE:
                key = result.current_key
                value = None
                if ((event_type(result.schema_object) and key == 'event_id')
                        or (reading_type(result.schema_object) and key == 'reading_id')):
                    _, graph = graph_state(active)
                    generated = graph.generated_event_ids if key == 'event_id' else graph.generated_reading_ids
                    value = deepcopy(result.schema_object.properties[key])
                    value.enum = [('e' if key == 'event_id' else 'r') + str(len(generated)+1)]
                elif key in {'event_refs', 'reading_refs', 'unit_refs'} and 'events' in schema['properties']:
                    _, graph = graph_state(active)
                    value = deepcopy(result.schema_object.properties[key])
                    available = (graph.generated_event_ids if key == 'event_refs' else
                        graph.generated_reading_ids if key == 'reading_refs' else
                        graph.generated_event_ids + graph.generated_reading_ids)
                    if not available:
                        value.minItems = value.maxItems = 0
                    else:
                        value.items.enum = list(available)
                elif node_local and key == 'node_refs':
                    _, graph = graph_state(active)
                    value = deepcopy(result.schema_object.properties[key])
                    value.items.enum = list(graph.generated_node_ids)
                    value.maxItems = min(value.maxItems, len(graph.generated_node_ids))
                elif ((event_type(result.schema_object) or local_unit_type(result.schema_object))
                        and key == 'unknowns' and (node_local
                            or schema['properties']['schema_version'].get('enum') == [EVENT_PLAN_V2_SCHEMA])):
                    value = deepcopy(result.schema_object.properties[key])
                    options = []
                    for part in value.items.oneOf or []:
                        number = part.properties['source_field'].enum[0]
                        quotes = [quote for quote in part.properties['source_quote'].enum
                            if any(field == number and original.count(quote) == 1
                                for field, original in result.selected_event_roots)]
                        if quotes:
                            part = deepcopy(part)
                            part.properties['source_quote'].enum = quotes
                            options.append(part)
                    if options:
                        value.items.oneOf = options
                    else:
                        value.minItems = value.maxItems = 0
                elif node_type(result.schema_object) and key == 'node_id':
                    _, graph = graph_state(active)
                    value = deepcopy(result.schema_object.properties[key])
                    next_id = 'n' + str(len(graph.generated_node_ids) + 1)
                    value.enum = [next_id] if next_id in value.enum else []
                    if not value.enum:
                        raise ValueError('semantic_node_ids_exhausted')
                elif graph_type(result.schema_object) and key == 'edges':
                    value = deepcopy(result.schema_object.properties[key])
                    ids = list(result.generated_node_ids)
                    if len(ids) < 2:
                        value.minItems = value.maxItems = 0
                    else:
                        value.items.properties['from'].enum = ids
                        value.items.properties['to'].enum = ids
                elif edge_type(result.schema_object) and key in {'from', 'to', 'relation_kind'}:
                    _, graph = graph_state(active)
                    value = deepcopy(result.schema_object.properties[key])
                    options = tuple(remaining_edges(graph,
                        start=result.selected_from if key != 'from' else None,
                        end=result.selected_to if key == 'relation_kind' else None))
                    position = {'from': 0, 'to': 1, 'relation_kind': 2}[key]
                    available = {option[position] for option in options}
                    value.enum = [item for item in value.enum if item in available]
                    if not value.enum:
                        raise ValueError('semantic_edge_options_exhausted')
                elif endpoint_titles and edge_type(result.schema_object) and key in {'from_unit','to_unit'}:
                    endpoint = result.selected_from if key == 'from_unit' else result.selected_to
                    value = deepcopy(result.schema_object.properties[key])
                    value.enum = [ref for ref in value.enum if ref.partition('.')[0] == endpoint]
                    if not value.enum:
                        raise ValueError('semantic_edge_unit_unbound')
                elif unit_cues and edge_type(result.schema_object) and key in {'from_source', 'to_source'}:
                    unit_ref = result.selected_from_unit if key == 'from_source' else result.selected_to_unit
                    value = deepcopy(result.schema_object.properties[key])
                    value.enum = unit_cues[unit_ref]
                elif (key in result.schema_object.properties and
                        (result.schema_object.properties[key].description or '').startswith('source-at-ids:')):
                    part = result.schema_object.properties[key]
                    handles = part.description.removeprefix('source-at-ids:').split(',')
                    fact = FactProse(result.root, handles, part.maxLength)
                    fact.assigned_source = part.extras.get('x-fact-source')
                    fact.source_bound_keys = bool(part.extras.get('x-source-bound-keys'))
                    fact.source_bound_members = bool(part.extras.get('x-source-bound-members'))
                    active.object_stack[-1] = fact
                elif key == 'title_proposal':
                    proposal = OverviewProposal(result.root, (), result.schema_object.properties[key].maxLength)
                    proposal.minimum = 0
                    active.object_stack[-1] = proposal
                elif key == 'title' and 'title_proposal' in result.schema_object.properties:
                    scope = closer_rules.WholeMapTitle(overview_sources, endpoint_nodes)
                    value = deepcopy(result.schema_object.properties[key])
                    value.enum = scope.authored_choices(result.title_proposal, overview_sources, endpoint_nodes)
                elif key == 'title':
                    forbidden = result.schema_object.properties[key].extras.get('not', {}).get('enum', ())
                    phrases = None
                    if overview_sources and set(result.schema_object.properties) == {'node_refs', 'title'}:
                        _, graph = graph_state(active)
                        units = [unit for node in endpoint_nodes if node['node_id'] in graph.selected_overview_refs
                                 for unit in node['units']]
                        forbidden = _semantic_choice_module().one_sided_source_titles(overview_sources, units,
                            compare_end_marks=compare_title_end_marks)
                        if (overview_sources.get('author_profile') in {OCCURRENCE_V18_PROFILE, OCCURRENCE_V19_PROFILE, OCCURRENCE_V20_PROFILE, OCCURRENCE_V21_PROFILE, OCCURRENCE_V22_PROFILE, OCCURRENCE_V23_PROFILE, OCCURRENCE_V24_PROFILE}
                                and len(graph.selected_overview_refs) > 1):
                            phrases = closer_rules.OverviewSourcePhrases(overview_sources, units, restricted_titles=forbidden,
                                include_original_fields=overview_sources.get('author_profile') in {OCCURRENCE_V19_PROFILE, OCCURRENCE_V20_PROFILE, OCCURRENCE_V21_PROFILE, OCCURRENCE_V22_PROFILE, OCCURRENCE_V23_PROFILE, OCCURRENCE_V24_PROFILE})
                            forbidden = phrases.restricted_titles
                    if phrases is not None and phrases.required:
                        if overview_sources.get('author_profile') in {OCCURRENCE_V20_PROFILE, OCCURRENCE_V21_PROFILE, OCCURRENCE_V22_PROFILE, OCCURRENCE_V23_PROFILE, OCCURRENCE_V24_PROFILE}:
                            scope = closer_rules.WholeMapTitle(overview_sources, endpoint_nodes)
                            active.object_stack[-1] = GroundedOverview(result.root, forbidden or (),
                                result.schema_object.properties[key].maxLength, phrases, scope)
                        else:
                            active.object_stack[-1] = OverviewTitle(result.root, forbidden or (),
                                result.schema_object.properties[key].maxLength, phrases)
                    elif forbidden:
                        label_type = SourceTitle if compare_title_end_marks else EndpointLabel
                        active.object_stack[-1] = label_type(result.root, forbidden,
                            result.schema_object.properties[key].maxLength)
                elif endpoint_titles and edge_type(result.schema_object) and key == 'label':
                    titles = (endpoint_titles[result.selected_from], endpoint_titles[result.selected_to])
                    active.object_stack[-1] = EndpointLabel(result.root, titles,
                        result.schema_object.properties[key].maxLength)
                if value is not None:
                    active.object_stack[-1] = module.get_parser(result.root, value)
                if protect_visible and key in result.schema_object.properties:
                    prop = result.schema_object.properties[key]
                    runs = prop.extras.get('x-source-closers')
                    if key == 'title' and set(result.schema_object.properties) == {'node_refs', 'title'}:
                        _, graph = graph_state(active)
                        runs = closer_rules.source_closer_runs(root['quote'] for node in endpoint_nodes
                            if node['node_id'] in graph.selected_overview_refs for unit in node['units'] for root in unit['evidence'])
                    elif key == 'label' and edge_type(result.schema_object):
                        refs = (result.selected_from_unit, result.selected_to_unit)
                        runs = closer_rules.source_closer_runs(root['quote'] for node in endpoint_nodes
                            for i, unit in enumerate(node['units'], 1) if f"{node['node_id']}.u{i}" in refs for root in unit['evidence'])
                    if runs is not None:
                        inner = active.object_stack[-1]
                        if not isinstance(inner, EndpointLabel):
                            inner = EndpointLabel(result.root, (), prop.maxLength)
                            active.object_stack[-1] = inner
                        inner.source_runs = runs
                        inner.minimum = prop.minLength or 0
            if char == '}' and result.can_end() and (event_type(result.schema_object) or reading_type(result.schema_object)):
                index, graph = graph_state(active)
                graph = graph.clone()
                attr = 'generated_event_ids' if event_type(result.schema_object) else 'generated_reading_ids'
                generated = getattr(graph, attr)
                if result.selected_plan_id is None or result.selected_plan_id in generated:
                    raise ValueError('semantic_plan_id_unbound')
                setattr(graph, attr, generated + (result.selected_plan_id,))
                active.object_stack[index] = graph
            if char == '}' and result.can_end() and node_type(result.schema_object):
                index, graph = graph_state(active)
                graph = graph.clone()
                if node_local and not plan_only:
                    result.selected_node_id = 'n' + str(len(graph.generated_node_ids) + 1)
                if result.selected_node_id is None or result.selected_node_id in graph.generated_node_ids:
                    raise ValueError('semantic_node_id_unbound')
                graph.generated_node_ids += (result.selected_node_id,)
                if unique_allocations:
                    graph.previous_allocations = graph.previous_allocations | {graph.plan_allocation}
                    graph.plan_allocation = ()
                active.object_stack[index] = graph
            if char == '}' and result.can_end() and edge_type(result.schema_object):
                index, graph = graph_state(active)
                if any(value is None for value in (result.selected_from,
                        result.selected_to, result.selected_relation_kind)):
                    raise ValueError('semantic_edge_unbound')
                key = edge_key(result.selected_from, result.selected_to, result.selected_relation_kind)
                if key in graph.generated_edge_keys:
                    raise ValueError('semantic_edge_duplicate')
                graph = graph.clone()
                graph.generated_edge_keys = graph.generated_edge_keys | {key}
                active.object_stack[index] = graph
            if char == '}' and result.can_end() and qualification_pair(result.schema_object):
                # Assigned evidence has the same object shape, but only a
                # qualification array consumes this choice. Scoping the set to
                # its array preserves identical quotations in other units.
                for index in range(len(active.object_stack) - 1, -1, -1):
                    parent = active.object_stack[index]
                    if isinstance(parent, UniqueEvidenceList) and parent.is_qualification:
                        pair = (result.schema_object.properties['source_field'].enum[0], result.selected_quote)
                        if result.selected_quote is None or pair in parent.used_pairs:
                            raise ValueError('semantic_qualification_unbound')
                        parent = parent._clone()
                        parent.used_pairs = parent.used_pairs | {pair}
                        active.object_stack[index] = parent
                        break
            if char == '}' and result.can_end() and evidence_pair(result.schema_object):
                if result.selected_quote is None:
                    raise ValueError('semantic_evidence_quote_unbound')
                pair = evidence_pair_key(result.schema_object.properties['field'].enum[0], result.selected_quote)
                if unique_allocations:
                    index, graph = graph_state(active)
                    graph = graph.clone()
                    units = graph.plan_allocation
                    graph.plan_allocation = units[:-1] + (units[-1] + (pair,),)
                    active.object_stack[index] = graph
                if node_local or schema.get('properties', {}).get('schema_version', {}).get('enum') == [EVENT_PLAN_V2_SCHEMA]:
                    for index in range(len(active.object_stack) - 1, -1, -1):
                        parent = active.object_stack[index]
                        if isinstance(parent, EvidenceObject) and (
                                event_type(parent.schema_object) or local_unit_type(parent.schema_object)):
                            parent = parent.clone()
                            parent.selected_event_roots += (pair,)
                            active.object_stack[index] = parent
                            break
                record = record_fields.get(pair[0])
                if record is not None:
                    index, graph = graph_state(active)
                    graph = graph.clone()
                    graph.covered_records = graph.covered_records | {record}
                    active.object_stack[index] = graph
                for index in range(len(active.object_stack) - 1, -1, -1):
                    parent = active.object_stack[index]
                    if isinstance(parent, UniqueEvidenceList) and parent.is_evidence:
                        parent = parent._clone()
                        parent.used_pairs = parent.used_pairs | {pair}
                        active.object_stack[index] = parent
                        break
                else:
                    raise ValueError('semantic_evidence_array_unbound')
            return result

    module.ListParsingState = UniqueEvidenceList
    module.ObjectParsingState = EvidenceObject
    return module.JsonSchemaParser(schema, config=config)


def semantic_json_parser(messages, alphabet):
    logical = _semantic_logical_json_parser(messages, alphabet)
    if not _semantic_merge_tuple_output(messages):
        return logical
    codec = _semantic_merge_wire_module().response_codec(messages,
        choice_module=_semantic_choice_module(), fact_key=_semantic_fact_part_key)
    if codec is None:
        return logical
    from importlib.util import module_from_spec, spec_from_file_location
    path = Path(__file__).resolve().parents[1] / 'services/ai_inference/analysis_merge_response_parser.py'
    spec = spec_from_file_location('cocolon_merge_response_parser', path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.response_parser(logical, codec)


def _semantic_logical_json_parser(messages, alphabet):
    merge_action_sources_enabled = _semantic_merge_tuple_output(messages)
    from lmformatenforcer import CharacterLevelParserConfig, JsonSchemaParser
    # LMFE snapshots alphabet_without_quotes while constructing its context.
    # Updating parser.config later leaves that initial snapshot unchanged.
    merge_anchors = _merge_record_anchors(messages)
    schema = semantic_output_schema(messages)
    messages = _semantic_constraint_messages(messages)
    config = CharacterLevelParserConfig(alphabet=alphabet)
    if schema['properties']['schema_version'].get('enum') == [IF_CANDIDATE_SCHEMA]:
        config.force_json_field_order = True
        return _if_json_schema_parser(schema, config)
    # Every map selects a real source before its meaning. Record IDs bind
    # coverage only; they never substitute for evidence field IDs.
    config.force_json_field_order = True
    material = json.loads(messages[1]['content'])
    if material.get('model_schema') == NODE_LOCAL_V4_SCHEMA and material.get('author_phase') != 'PLAN':
        ids = tuple(n['node_id'] for n in material.get('candidate_nodes', ()))
        return _semantic_unique_json_schema_parser(schema, config, bound_node_ids=ids,
            protect_visible=material.get('author_profile') in VISIBLE_SOURCE_PROFILES,
            compare_title_end_marks=material.get('author_profile') in FACT_PROSE_PROFILES,
            overview_sources=material if material.get('author_phase') == 'RELATIONS'
                and material.get('author_profile') in CONTENT_PLAN_PROFILES else None,
            endpoint_nodes=material['candidate_nodes'] if material.get('author_phase') == 'RELATIONS'
                and material.get('author_profile') in {OCCURRENCE_V6_PROFILE, OCCURRENCE_V7_PROFILE, OCCURRENCE_V8_PROFILE, *SOURCE_CUED_PROFILES} else (),
            unique_qualifications=material.get('author_phase') == 'NODES'
                and material.get('author_profile') in OCCURRENCE_PROFILES)
    anchor_key = 'events' if 'events' in schema['properties'] else 'nodes'
    node_local = schema['properties']['schema_version'].get('enum') in (
        [NODE_LOCAL_V3_SCHEMA], [NODE_LOCAL_V4_SCHEMA + '.plan'])
    item = schema['properties'][anchor_key]['items']['properties']
    evidence = item['units']['items']['properties']['evidence'] if node_local else item['evidence']
    quoted_fields = {part['properties']['field']['enum'][0] for part in evidence['items']['oneOf']}
    records = {field['field']: field['record'] for field in material['fields']
        if field['field'] in quoted_fields and type(field.get('record')) is int and field['record'] > 0}
    # Native output has at most 24 meaning nodes. Larger source sets retain the
    # existing explicitly partial coverage rather than becoming a new refusal.
    if len(set(records.values())) > 24:
        records = {}
    distinct_leads = material.get('author_profile') in {OCCURRENCE_V10_PROFILE, OCCURRENCE_V11_PROFILE, *FACT_REFERENCE_PROFILES} and material.get('author_phase') == 'PLAN'
    choices = None
    owners = pairs = regions = actions = ()
    required_sources = None
    if distinct_leads and material.get('author_profile') in {OCCURRENCE_V11_PROFILE, *FACT_REFERENCE_PROFILES}:
        material, choices, _ = _semantic_plan_choice_view(material)
        owners = _semantic_choice_module().record_plan_owners(material, quoted_fields, merge_anchors=merge_anchors)
        if owners:
            required_sources = _semantic_choice_module().whole_plan_sources(material, owners)
            by_record = _semantic_choice_module().compact_action_pairs(material)
            if by_record:
                pairs = tuple(by_record.get(r['record']) for r in material['records'])
            choice_rules = _semantic_choice_module()
            if merge_action_sources_enabled:
                by_record_action = choice_rules.merge_action_sources(material, owners)
                if by_record_action:
                    actions = tuple(by_record_action.get(row['record']) for row in material['records'])
            by_region = choice_rules.owner_source_regions(material, owners, choice_rules.plan_reading_regions(material, by_record), required_sources)
            if by_region:
                regions = tuple(by_region.get(row['record']) for row in material['records'])
            # Map corrections have no original record, even for a one-record
            # dependency cohort. Reserve free evidence slots for their own text.
            records.update({f['field']: -f['field'] for f in material['fields']
                if f['source_role'] == 'USER_ANALYSIS_MAP_CORRECTION' and f['field'] in quoted_fields})
    return _semantic_unique_json_schema_parser(schema, config, record_fields=records, record_owners=owners, merge_anchors=merge_anchors, compact_pairs=pairs, reading_regions=regions, required_sources=required_sources, plan_choice_quotes=choices, action_sources=actions,
        plan_source_texts={f['field']: f['text'] for f in material['fields']} if distinct_leads else None,
        unique_allocations=material.get('author_profile') in SOURCE_CUED_PROFILES
            and material.get('author_phase') == 'PLAN')


def piece_output_schema(messages):
    """Constrain named transport slots, without constraining their meaning."""
    if (type(messages) is not list or len(messages) != 2
            or any(type(message) is not dict for message in messages)
            or [message.get('role') for message in messages] != ['system', 'user']
            or type(messages[1].get('content')) is not str):
        raise ValueError('piece_material_invalid')
    material = json.loads(messages[1]['content'])
    if (type(material) is not dict or material.get('core') != 'piece'
            or material.get('task') != 'PIECE_MODEL_BODY'
            or type(material.get('control')) is not dict):
        raise ValueError('piece_material_invalid')
    slots = material['control'].get('field_slots')
    if (type(slots) is not dict or not 1 <= len(slots) <= 3
            or any(not re.fullmatch(r'(?:memo|memo_action|answer_text_private)_[0-2]', key)
                   or type(value) is not dict for key, value in slots.items())
            or {int(key.rsplit('_', 1)[1]) for key in slots} != set(range(len(slots)))):
        raise ValueError('piece_slots_invalid')
    # This is private decoding order only. The receiver still projects back to
    # the frozen partition order. Decode the separate answer before originals;
    # this does not certify source separation inside either generated value.
    ordered_keys = sorted(slots, key=lambda key: (
        not key.startswith('answer_text_private_'), int(key.rsplit('_', 1)[1])))
    properties = {key: dict(type='string', minLength=1) for key in ordered_keys}
    fields = dict(type='object', properties=properties, required=list(properties), additionalProperties=False)
    return dict(type='object', properties=dict(field_blocks=fields), required=['field_blocks'],
                additionalProperties=False)


def piece_json_parser(messages, alphabet):
    from lmformatenforcer import CharacterLevelParserConfig, JsonSchemaParser
    return JsonSchemaParser(piece_output_schema(messages),
        config=CharacterLevelParserConfig(alphabet=alphabet, force_json_field_order=True))


def _correction_target_context_messages_valid(messages):
    """Admit only a complete, locator-bound AI target context, never arbitrary history."""
    try:
        if (type(messages) is not list or len(messages) != 3
                or any(type(row) is not dict or set(row) != {'role', 'content'} for row in messages)
                or [row['role'] for row in messages] != ['system', 'assistant', 'user']
                or any(type(row['content']) is not str or not row['content'] for row in messages)):
            return False
        context = json.loads(messages[1]['content'])
        material = json.loads(messages[2]['content'])
        if (type(context) is not dict or set(context) != {'ai_interpretation_targets'}
                or type(context['ai_interpretation_targets']) is not list
                or not context['ai_interpretation_targets'] or type(material) is not dict):
            return False
        targets = context['ai_interpretation_targets']
        histories = material.get('past_user_records', [])
        if type(histories) is not list or any(type(row) is not dict for row in histories):
            return False
        records = [('', material.get('current_input_id'), material)]
        records.extend((f'past_user_records[{index}].', row.get('input_id'), row)
                       for index, row in enumerate(histories))
        target_fields = {'source_role', 'context_ref', 'parent_input_id', 'correction_source_path',
                         'correction_id', 'target_event_id', 'target_ai_interpretation'}
        count = 0
        for prefix, parent_id, record in records:
            corrections = record.get('interpretation_corrections', [])
            if type(corrections) is not list:
                return False
            for index, correction in enumerate(corrections):
                if (type(correction) is not dict or count >= len(targets)
                        or correction.get('source_role') != 'USER_INTERPRETATION_CORRECTION'
                        or 'target_ai_interpretation' in correction
                        or type(parent_id) is not str or not parent_id.strip()):
                    return False
                target = targets[count]
                reference = f'ai_interpretation_targets[{count}]'
                if (type(target) is not dict or set(target) != target_fields
                        or any(type(value) is not str or not value.strip() for value in target.values())
                        or target['source_role'] != 'AI_INTERPRETATION_TARGET'
                        or target['context_ref'] != reference
                        or correction.get('target_ai_context_ref') != reference
                        or target['parent_input_id'] != parent_id
                        or target['correction_source_path'] != prefix + f'interpretation_corrections[{index}]'
                        or any(target[key] != correction.get(key) for key in ('correction_id', 'target_event_id'))):
                    return False
                count += 1
        return count == len(targets)
    except (ValueError, TypeError, KeyError):
        return False


def make_handler(generate, *, api_key, model_name, deadline, max_requests,
                 max_new_tokens=2048, request_seconds=23, max_request_bytes=65536,
                 natural_reply=None, natural_queue_seconds=210, piece_revision=None,
                 correction_target_context=False, event_plan_model=None):
    if (type(correction_target_context) is not bool
            or correction_target_context and not natural_reply):
        raise ValueError('correction_target_context_configuration_invalid')
    if piece_revision is not None and (type(piece_revision) is not str
            or not re.fullmatch(r'piece-lora:[0-9a-f]{64}', piece_revision)):
        raise ValueError('piece_adapter_revision_invalid')
    if event_plan_model is not None and (type(event_plan_model) is not str
            or not event_plan_model.strip() or event_plan_model == model_name
            or natural_reply and event_plan_model == natural_reply['model_name']):
        raise ValueError('event_plan_model_configuration_invalid')
    lock = threading.Lock()
    served = 0

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Never log request headers, source, or generated text.

        def reply(self, status, body):
            encoded = json.dumps(body, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            try:
                self.wfile.write(encoded)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def do_GET(self):
            if self.path != "/healthz":
                return self.reply(404, {"error": "not_found"})
            return self.reply(200 if time.monotonic() < deadline else 503,
                              {"status": "ok" if time.monotonic() < deadline else "stopping"})

        def do_POST(self):
            nonlocal served
            authorization = self.headers.get("Authorization", "")
            natural = bool(natural_reply and hmac.compare_digest(authorization, "Bearer " + natural_reply["api_key"]))
            if not natural and not hmac.compare_digest(authorization, "Bearer " + api_key):
                return self.reply(401, {"error": "unauthorized"})
            selected_model = natural_reply["model_name"] if natural else model_name
            selected_tokens = 2048 if natural else max_new_tokens
            selected_seconds = 23 if natural else request_seconds
            selected_bytes = 65536 if natural else max_request_bytes
            if self.path != "/v1/chat/completions":
                return self.reply(404, {"error": "not_found"})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= selected_bytes or self.headers.get("Transfer-Encoding"):
                    raise ValueError
                self.connection.settimeout(5)
                request = json.loads(self.rfile.read(length))
                messages = request["messages"]
                piece = 'candidate_format' in request
                event_plan = bool(not natural and event_plan_model is not None
                    and request.get('model') == event_plan_model)
                event_plan_base = event_plan and event_plan_model in {
                    EVENT_PLAN_V2_BASE_MODEL, NODE_LOCAL_V3_BASE_MODEL}
                if event_plan:
                    selected_model = event_plan_model
                staged = event_plan and event_plan_model in {NODE_LOCAL_V4_MODEL, NODE_LOCAL_V4_BOUND_MODEL, NODE_LOCAL_V4_BOUND_V2_MODEL, OCCURRENCE_MODEL, OCCURRENCE_V2_MODEL, OCCURRENCE_V3_MODEL, OCCURRENCE_V4_MODEL, OCCURRENCE_V5_MODEL, OCCURRENCE_V6_MODEL, OCCURRENCE_V7_MODEL, OCCURRENCE_V8_MODEL, OCCURRENCE_V9_MODEL, OCCURRENCE_V10_MODEL, OCCURRENCE_V11_MODEL, OCCURRENCE_V12_MODEL, OCCURRENCE_V13_MODEL, OCCURRENCE_V14_MODEL, OCCURRENCE_V15_MODEL, OCCURRENCE_V16_MODEL, OCCURRENCE_V17_MODEL, OCCURRENCE_V18_MODEL, OCCURRENCE_V19_MODEL, OCCURRENCE_V20_MODEL, OCCURRENCE_V21_MODEL, OCCURRENCE_V22_MODEL, OCCURRENCE_V23_MODEL, OCCURRENCE_V24_MODEL}
                if staged:
                    material = json.loads(messages[1]['content'])
                    if material.get('author_phase') not in NODE_LOCAL_V4_PHASES:
                        raise ValueError
                    selected_tokens = request.get('max_tokens')
                    if type(selected_tokens) is not int or not 1 <= selected_tokens <= min(4096, max_new_tokens):
                        raise ValueError
                    seconds = request.get('generation_seconds')
                    if type(seconds) not in (int, float) or not 0 < seconds <= 210:
                        raise ValueError
                    selected_seconds = min(selected_seconds, seconds)
                ordinary_messages = (isinstance(messages, list) and len(messages) == 2
                    and [m["role"] for m in messages] == ["system", "user"]
                    and all(isinstance(m["content"], str) and m["content"] for m in messages))
                correction_messages = (correction_target_context and natural and not piece
                    and _correction_target_context_messages_valid(messages))
                if (request.get("model") != selected_model or request.get("stream") is not False
                        or type(request.get("max_tokens")) is not int
                        or request["max_tokens"] != selected_tokens or request.get("temperature") != 0
                        or request.get("chat_template_kwargs") != {"enable_thinking": False}
                        or not (ordinary_messages or correction_messages)):
                    raise ValueError
                if not natural:
                    try:
                        material = json.loads(messages[1]['content'])
                    except (ValueError, TypeError):
                        material = None
                    marker = material.get('model_schema') if type(material) is dict else None
                    expected_marker = (NODE_LOCAL_V4_SCHEMA if event_plan_model in {NODE_LOCAL_V4_MODEL, NODE_LOCAL_V4_BOUND_MODEL, NODE_LOCAL_V4_BOUND_V2_MODEL, OCCURRENCE_MODEL, OCCURRENCE_V2_MODEL, OCCURRENCE_V3_MODEL, OCCURRENCE_V4_MODEL, OCCURRENCE_V5_MODEL, OCCURRENCE_V6_MODEL, OCCURRENCE_V7_MODEL, OCCURRENCE_V8_MODEL, OCCURRENCE_V9_MODEL, OCCURRENCE_V10_MODEL, OCCURRENCE_V11_MODEL, OCCURRENCE_V12_MODEL, OCCURRENCE_V13_MODEL, OCCURRENCE_V14_MODEL, OCCURRENCE_V15_MODEL, OCCURRENCE_V16_MODEL, OCCURRENCE_V17_MODEL, OCCURRENCE_V18_MODEL, OCCURRENCE_V19_MODEL, OCCURRENCE_V20_MODEL, OCCURRENCE_V21_MODEL, OCCURRENCE_V22_MODEL, OCCURRENCE_V23_MODEL, OCCURRENCE_V24_MODEL}
                        else NODE_LOCAL_V3_SCHEMA if event_plan_model in {
                            NODE_LOCAL_V3_MODEL, NODE_LOCAL_V3_BASE_MODEL}
                        else EVENT_PLAN_V2_SCHEMA if event_plan_model in {
                            EVENT_PLAN_V2_MODEL, EVENT_PLAN_V2_BASE_MODEL} else EVENT_PLAN_SCHEMA)
                    if (event_plan and marker != expected_marker
                            or not event_plan and marker in {EVENT_PLAN_SCHEMA, EVENT_PLAN_V2_SCHEMA,
                                NODE_LOCAL_V3_SCHEMA, NODE_LOCAL_V4_SCHEMA}):
                        raise ValueError
                    if staged:
                        expected_profile = (OCCURRENCE_V24_PROFILE if event_plan_model == OCCURRENCE_V24_MODEL
                            else OCCURRENCE_V23_PROFILE if event_plan_model == OCCURRENCE_V23_MODEL
                            else OCCURRENCE_V22_PROFILE if event_plan_model == OCCURRENCE_V22_MODEL
                            else OCCURRENCE_V21_PROFILE if event_plan_model == OCCURRENCE_V21_MODEL
                            else OCCURRENCE_V20_PROFILE if event_plan_model == OCCURRENCE_V20_MODEL
                            else OCCURRENCE_V19_PROFILE if event_plan_model == OCCURRENCE_V19_MODEL
                            else OCCURRENCE_V18_PROFILE if event_plan_model == OCCURRENCE_V18_MODEL
                            else OCCURRENCE_V17_PROFILE if event_plan_model == OCCURRENCE_V17_MODEL
                            else OCCURRENCE_V16_PROFILE if event_plan_model == OCCURRENCE_V16_MODEL
                            else OCCURRENCE_V15_PROFILE if event_plan_model == OCCURRENCE_V15_MODEL
                            else OCCURRENCE_V14_PROFILE if event_plan_model == OCCURRENCE_V14_MODEL
                            else OCCURRENCE_V13_PROFILE if event_plan_model == OCCURRENCE_V13_MODEL
                            else OCCURRENCE_V12_PROFILE if event_plan_model == OCCURRENCE_V12_MODEL
                            else OCCURRENCE_V11_PROFILE if event_plan_model == OCCURRENCE_V11_MODEL
                            else OCCURRENCE_V10_PROFILE if event_plan_model == OCCURRENCE_V10_MODEL
                            else OCCURRENCE_V9_PROFILE if event_plan_model == OCCURRENCE_V9_MODEL
                            else OCCURRENCE_V8_PROFILE if event_plan_model == OCCURRENCE_V8_MODEL
                            else OCCURRENCE_V7_PROFILE if event_plan_model == OCCURRENCE_V7_MODEL
                            else OCCURRENCE_V6_PROFILE if event_plan_model == OCCURRENCE_V6_MODEL
                            else OCCURRENCE_V5_PROFILE if event_plan_model == OCCURRENCE_V5_MODEL
                            else OCCURRENCE_V4_PROFILE if event_plan_model == OCCURRENCE_V4_MODEL
                            else OCCURRENCE_V3_PROFILE if event_plan_model == OCCURRENCE_V3_MODEL
                            else OCCURRENCE_V2_PROFILE if event_plan_model == OCCURRENCE_V2_MODEL
                            else OCCURRENCE_PROFILE if event_plan_model == OCCURRENCE_MODEL
                            else NODE_LOCAL_V4_BOUND_V2_PROFILE
                            if event_plan_model == NODE_LOCAL_V4_BOUND_V2_MODEL else NODE_LOCAL_V4_BOUND_PROFILE
                            if event_plan_model == NODE_LOCAL_V4_BOUND_MODEL else None)
                        if material.get('author_profile') != expected_profile:
                            raise ValueError
                        semantic_output_schema(messages)
                if piece:
                    if not natural or request['candidate_format'] != PIECE_CANDIDATE_FORMAT:
                        raise ValueError
                    piece_output_schema(messages)
            except Exception:
                return self.reply(400, {"error": "request_invalid"})
            admitted = lock.acquire(timeout=natural_queue_seconds) if natural else lock.acquire(blocking=False)
            if not admitted:
                return self.reply(429, {"error": "busy"})
            try:
                if (max_requests and served >= max_requests) or time.monotonic() >= deadline:
                    return self.reply(429, {"error": "probe_limit"})
                served += 1
                if not max_requests:
                    generation_stage('admitted')
                end = min(deadline, time.monotonic() + selected_seconds)
                generated = (generate(messages, end, profile='event_plan', output_tokens=selected_tokens)
                                if staged else generate(messages, end, profile="piece" if piece else "natural")
                                if natural else generate(messages, end,
                                    profile='event_plan_base' if event_plan_base else 'event_plan')
                                if event_plan else generate(messages, end))
                if staged:
                    text, finish, usage = generated
                    if (type(usage) is not dict or type(usage.get('completion_tokens')) is not int
                            or not 1 <= usage['completion_tokens'] <= selected_tokens):
                        raise ValueError('semantic_phase_usage_invalid')
                else:
                    text, finish = generated
                if finish not in {"stop", "length"} or not isinstance(text, str):
                    raise ValueError
                status, body = 200, {"model": selected_model, "choices": [{
                    "index": 0, "finish_reason": finish,
                    "message": {"role": "assistant", "content": text}}]}
                if piece:
                    body['candidate_format'] = PIECE_CANDIDATE_FORMAT
                    if piece_revision is not None:
                        body['revision'] = piece_revision
                if staged:
                    body['usage'] = usage
            except Exception as exc:
                if staged or not max_requests:
                    generation_failure(exc)
                status, body = 503, {"error": "generation_unavailable"}
            finally:
                lock.release()
            return self.reply(status, body)
    return Handler


def adapter_identity(adapter, weights_sha256=None, config_sha256=None):
    """Verify an explicitly selected saved candidate; never select a new one."""
    if weights_sha256 is None and config_sha256 is None:
        weights_sha256, config_sha256 = FIT38_WEIGHTS, FIT38_CONFIG
    elif (not adapter or not isinstance(weights_sha256, str) or not isinstance(config_sha256, str)
          or not re.fullmatch(r'[0-9a-f]{64}', weights_sha256)
          or not re.fullmatch(r'[0-9a-f]{64}', config_sha256)):
        raise ValueError('adapter_identity_configuration_invalid')
    if not adapter:
        return None
    path = Path(adapter)
    for name, digest in (("adapter_model.safetensors", weights_sha256), ("adapter_config.json", config_sha256)):
        if hashlib.sha256((path / name).read_bytes()).hexdigest() != digest:
            raise ValueError('saved_adapter_identity_changed')
    return weights_sha256, config_sha256


@contextmanager
def base_inference_context(model):
    try:
        with model.disable_adapter():
            yield
    finally:
        # PEFT re-enabling its adapter can also re-enable LoRA gradients.
        # Restore the serving invariant on both successful and failed forwards.
        model.eval()
        model.requires_grad_(False)


@contextmanager
def piece_inference_context(model, process_stop, *, adapter_name=PIECE_ADAPTER_NAME):
    """Use only the separately loaded Piece adapter, then restore Analysis."""
    previous = model.active_adapter
    if previous != 'default':
        raise ValueError('piece_adapter_state_invalid')
    try:
        model.set_adapter(adapter_name, inference_mode=True)
        model.eval()
        model.requires_grad_(False)
        yield
    finally:
        try:
            model.set_adapter(previous, inference_mode=True)
            model.eval()
            model.requires_grad_(False)
        except BaseException:
            # A failed restoration must not serve Analysis with Piece weights.
            process_stop.set()
            raise


def load_piece_adapter(model, path, *, weights_sha256, config_sha256,
                       analysis_config, analysis_weights, adapter_name=PIECE_ADAPTER_NAME):
    """Load an opt-in independent LoRA; never replace or combine adapters."""
    from peft import PeftConfig, get_peft_model_state_dict
    from safetensors.torch import load_file
    import torch
    identity = adapter_identity(path, weights_sha256, config_sha256)
    config = PeftConfig.from_pretrained(path, local_files_only=True)
    expected_config, selected_config = analysis_config.to_dict(), config.to_dict()
    # The fresh Piece training uses the current adapter's structural config,
    # not its learned tensors. Only train/inference mode may differ on disk.
    for value in (expected_config, selected_config):
        value.pop('inference_mode', None)
    if selected_config != expected_config:
        raise ValueError('piece_adapter_scope_changed')
    expected = load_file(Path(path) / 'adapter_model.safetensors')
    if (set(expected) != set(analysis_weights) or len(expected) != 112
            or sum(t.numel() for t in expected.values()) != 3833856
            or any(expected[key].shape != analysis_weights[key].shape for key in expected)):
        raise ValueError('piece_adapter_saved_weights_scope_changed')
    model.load_adapter(path, adapter_name=adapter_name,
                       is_trainable=False, local_files_only=True)
    actual = get_peft_model_state_dict(model, adapter_name=adapter_name)
    original = get_peft_model_state_dict(model)
    if (set(actual) != set(expected) or len(actual) != 112
            or sum(t.numel() for t in actual.values()) != 3833856
            or any(not torch.equal(actual[k].detach().cpu(), expected[k]) for k in expected)
            or set(original) != set(analysis_weights)
            or any(not torch.equal(original[k].detach().cpu(), analysis_weights[k])
                   for k in analysis_weights)):
        raise ValueError('piece_adapter_loaded_weights_changed')
    model.set_adapter('default', inference_mode=True)
    adapter_identity(path, *identity)


def load_generator(adapter, process_stop, *, weights_sha256=None, config_sha256=None,
                   max_new_tokens=2048, context_tokens=8192, semantic_json=False,
                   piece_adapter=None, piece_weights_sha256=None, piece_config_sha256=None,
                   event_plan_adapter=None, event_plan_weights_sha256=None, event_plan_config_sha256=None):
    if (type(max_new_tokens) is not int or type(context_tokens) is not int
            or not 1 <= max_new_tokens < context_tokens <= 32768):
        raise ValueError("model_token_budget_invalid")
    if os.environ.get("HF_HUB_OFFLINE") != "1" or os.environ.get("TRANSFORMERS_OFFLINE") != "1":
        raise ValueError("offline_cache_required")
    if {name: version(name) for name in PINS} != PINS:
        raise ValueError("model_dependency_changed")
    selected_identity = adapter_identity(adapter, weights_sha256, config_sha256)
    if (piece_adapter is not None or piece_weights_sha256 is not None
            or piece_config_sha256 is not None):
        if (not adapter or not piece_adapter or not semantic_json
                or piece_weights_sha256 is None or piece_config_sha256 is None):
            raise ValueError('piece_adapter_configuration_invalid')
        if (Path(piece_adapter).resolve() == Path(adapter).resolve()
                or piece_weights_sha256 == selected_identity[0]):
            raise ValueError('piece_adapter_must_be_separate')
        adapter_identity(piece_adapter, piece_weights_sha256, piece_config_sha256)
    if any(value is not None for value in (event_plan_adapter, event_plan_weights_sha256, event_plan_config_sha256)):
        if (not adapter or not event_plan_adapter or not semantic_json
                or event_plan_weights_sha256 is None or event_plan_config_sha256 is None):
            raise ValueError('event_plan_adapter_configuration_invalid')
        if (Path(event_plan_adapter).resolve() == Path(adapter).resolve()
                or event_plan_weights_sha256 == selected_identity[0]):
            raise ValueError('event_plan_adapter_must_be_separate')
        adapter_identity(event_plan_adapter, event_plan_weights_sha256, event_plan_config_sha256)
    import torch
    from transformers import AutoTokenizer, Qwen3_5ForConditionalGeneration, StoppingCriteria, StoppingCriteriaList
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise ValueError("single_cuda_device_required")
    tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=REVISION,
        local_files_only=True, trust_remote_code=False)
    model = Qwen3_5ForConditionalGeneration.from_pretrained(MODEL, revision=REVISION,
        dtype=torch.bfloat16, device_map={"": 0}, attn_implementation="sdpa",
        local_files_only=True, trust_remote_code=False)
    if adapter:
        path = Path(adapter)
        from peft import PeftConfig, PeftModel, get_peft_model_state_dict
        from peft.tuners.tuners_utils import check_target_module_exists
        from safetensors.torch import load_file
        config = PeftConfig.from_pretrained(path, local_files_only=True)
        if sum(bool(check_target_module_exists(config, name)) for name, _ in model.named_modules()) != 56:
            raise ValueError("fit38_target_scope_changed")
        expected = load_file(path / "adapter_model.safetensors")
        model = PeftModel.from_pretrained(model, path, is_trainable=False, local_files_only=True)
        actual = get_peft_model_state_dict(model)
        if (set(actual) != set(expected) or len(actual) != 112
                or sum(t.numel() for t in actual.values()) != 3833856
                or any(not torch.equal(actual[k].detach().cpu(), expected[k]) for k in expected)):
            raise ValueError("fit38_loaded_weights_changed")
        if piece_adapter is not None:
            load_piece_adapter(model, piece_adapter,
                weights_sha256=piece_weights_sha256, config_sha256=piece_config_sha256,
                analysis_config=config, analysis_weights=expected)
        if event_plan_adapter is not None:
            load_piece_adapter(model, event_plan_adapter,
                weights_sha256=event_plan_weights_sha256, config_sha256=event_plan_config_sha256,
                analysis_config=config, analysis_weights=expected, adapter_name=EVENT_PLAN_ADAPTER_NAME)
    model.eval()
    model.requires_grad_(False)
    if model.training or any(p.requires_grad for p in model.parameters()):
        raise ValueError("nontraining_model_required")
    if selected_identity:
        adapter_identity(adapter, *selected_identity)
    tokenizer_data = None
    blocked_free_text = set()
    invalid_json_tokens = set()
    unsupported_unicode_tokens = set()
    if semantic_json:
        private_log_filter = SourcePrivateConstraintLog()
        logging.getLogger().addFilter(private_log_filter)
        for handler in logging.getLogger().handlers:
            handler.addFilter(private_log_filter)
        from lmformatenforcer.integrations.transformers import build_token_enforcer_tokenizer_data
        distribution = __import__('importlib.metadata', fromlist=['distribution']).distribution('lm-format-enforcer')
        origin = json.loads(distribution.read_text('direct_url.json') or '{}')
        if origin.get('vcs_info', {}).get('commit_id') != SEMANTIC_FORMAT_SOURCE:
            raise ValueError('semantic_format_source_changed')
        tokenizer_data = build_token_enforcer_tokenizer_data(tokenizer,
            vocab_size=min(len(tokenizer), model.get_output_embeddings().weight.shape[0]))
        blocked_free_text = {token for token, decoded, _ in tokenizer_data.regular_tokens
            if not decoded.strip() or any(ord(char) < 32 for char in decoded)}
        invalid_json_tokens = {token for token, decoded, _ in tokenizer_data.regular_tokens
            if not decoded or any(ord(char) < 32 for char in decoded)}
        # LMFE's prose shortcut can admit partial UTF-8 or interior characters
        # outside its parser alphabet. Its incremental decoder cannot roll back
        # a replacement character when later bytes complete it. Keep these
        # token spellings out of Analysis/IF; JSON Unicode escapes retain the
        # same decoded text, including exact source quotes.
        tokenizer_alphabet = frozenset(tokenizer_data.tokenizer_alphabet)
        unsupported_unicode_tokens = {token for token, decoded, _ in tokenizer_data.regular_tokens
            if '\ufffd' in decoded or any(char not in tokenizer_alphabet for char in decoded)}

    class Deadline(StoppingCriteria):
        def __init__(self, end):
            self.end, self.expired = end, False

        def __call__(self, input_ids, scores, **kwargs):
            self.expired = process_stop.is_set() or time.monotonic() >= self.end
            return self.expired

    def generate(messages, end, *, profile=None, output_tokens=None):
        if (piece_adapter is not None or event_plan_adapter is not None) and process_stop.is_set():
            raise ValueError('generation_stopping')
        if profile not in (None, "natural", "piece", "event_plan", "event_plan_base"):
            raise ValueError("generation_profile_invalid")
        if profile == "piece" and (not semantic_json or tokenizer_data is None):
            raise ValueError("piece_constraint_unavailable")
        if profile in ('event_plan', 'event_plan_base') and (event_plan_adapter is None or not semantic_json or tokenizer_data is None):
            raise ValueError('event_plan_adapter_unavailable')
        use_semantic_json = semantic_json and profile != "natural"
        base_profile = profile in ("natural", "piece")
        output_budget = 2048 if base_profile else max_new_tokens
        if output_tokens is not None:
            material = json.loads(messages[1]['content'])
            if (profile != 'event_plan' or material.get('model_schema') != NODE_LOCAL_V4_SCHEMA
                    or type(output_tokens) is not int
                    or material.get('author_phase') not in NODE_LOCAL_V4_PHASES
                    or not 1 <= output_tokens <= min(4096, max_new_tokens)):
                raise ValueError('semantic_phase_budget_invalid')
            output_budget = output_tokens
        context_budget = 8192 if base_profile else context_tokens
        # Preserve the base identity previously connected for natural replies.
        # The analysis adapter stays loaded; its state is restored on context exit.
        adapter_context = (piece_inference_context(model, process_stop, adapter_name=EVENT_PLAN_ADAPTER_NAME)
            if profile == 'event_plan' else piece_inference_context(model, process_stop)
            if profile == 'piece' and piece_adapter is not None else
            base_inference_context(model) if (base_profile or profile == 'event_plan_base') and adapter else nullcontext())
        if use_semantic_json:
            generation_stage('tokenize')
        encoded = tokenizer.apply_chat_template(messages, enable_thinking=False,
            add_generation_prompt=True, tokenize=True, return_dict=True,
            return_tensors="pt", truncation=False)
        count = encoded["input_ids"].shape[-1]
        if count + output_budget > context_budget or time.monotonic() >= end:
            raise ValueError("context_or_deadline_exceeded")
        encoded = {k: v.to(model.device) for k, v in encoded.items()}
        stopping = Deadline(end)
        format_options = {}
        if use_semantic_json:
            generation_stage('constraint')
            from lmformatenforcer.integrations.transformers import build_transformers_prefix_allowed_tokens_fn
            allowed_prefix = build_transformers_prefix_allowed_tokens_fn(
                tokenizer_data, (piece_json_parser if profile == "piece" else semantic_json_parser)(
                    messages, tokenizer_data.tokenizer_alphabet))
            if profile != 'piece':
                # The pinned integration replaces parser.config. Restore the
                # Analysis/IF order before the first token is explored.
                allowed_prefix.token_enforcer.root_parser.config.force_json_field_order = True
            profile_invalid_json_tokens = (invalid_json_tokens if profile == 'piece' else
                invalid_json_tokens | unsupported_unicode_tokens)
            material = json.loads(messages[1]['content']) if profile == 'event_plan' else None
            prefix_offset = _semantic_merge_prefix_offset(profile, material, messages, count)
            previous_allowed = None
            def private_prefix(batch, sent):
                nonlocal previous_allowed
                if prefix_offset and batch != 0:
                    raise ValueError('semantic_merge_single_greedy_sequence_required')
                progress = len(sent) - count
                measured = progress % 128 == 0
                if measured:
                    generation_stage('prefix_enter_' + str(progress))
                if progress and int(sent[-1]) in profile_invalid_json_tokens:
                    raise ValueError('semantic_nontext_token_generated')
                if progress and previous_allowed is not None and int(sent[-1]) not in previous_allowed:
                    generation_stage('prefix_constraint_violation')
                    raise ValueError('semantic_prefix_constraint_violation')
                history = _semantic_prefix_input(sent, prefix_offset)
                allowed = semantic_free_text_tokens(allowed_prefix, batch, history,
                    set() if profile == "piece" else blocked_free_text, profile_invalid_json_tokens)
                previous_allowed = allowed
                if measured:
                    parser = allowed_prefix.token_enforcer.prefix_states[tuple(history.tolist())].parser
                    key = parser.shortcut_key()
                    mode = 'free' if isinstance(key, tuple) and key[0] == 'json_freetext' else 'other'
                    generation_stage('prefix_exit_' + str(progress) + '_' + type(parser).__name__
                        + '_' + mode + '_allowed_' + str(len(allowed)))
                return allowed
            if profile == 'event_plan':
                if material.get('author_profile') in {OCCURRENCE_V2_PROFILE, OCCURRENCE_V3_PROFILE, OCCURRENCE_V4_PROFILE, OCCURRENCE_V5_PROFILE, OCCURRENCE_V6_PROFILE, OCCURRENCE_V7_PROFILE, OCCURRENCE_V8_PROFILE, *SOURCE_CUED_PROFILES} and material.get('author_phase')=='NODES':
                    visible_filter = (_occurrence_greedy_relation_filter(allowed_prefix, prompt_tokens=prefix_offset)
                        if material.get('author_profile') in VISIBLE_SOURCE_PROFILES else None)
                    compact_prefix = allowed_prefix if _semantic_merge_tuple_output(messages) else None
                    format_options['logits_processor']=[_occurrence_greedy_node_filter(tokenizer,count,
                        _semantic_wire_fact_sources(messages),visible_filter,compact_prefix)]
                elif material.get('author_profile') in {OCCURRENCE_V6_PROFILE, OCCURRENCE_V7_PROFILE, OCCURRENCE_V8_PROFILE, *SOURCE_CUED_PROFILES} and material.get('author_phase') == 'RELATIONS':
                    format_options['logits_processor']=[_occurrence_greedy_relation_filter(allowed_prefix, prompt_tokens=prefix_offset)]
            format_options['prefix_allowed_tokens_fn'] = private_prefix
            format_options['eos_token_id'] = tokenizer_data.eos_token_id
            generation_stage('decode')
        with adapter_context, torch.inference_mode():
            result = model.generate(**encoded, max_new_tokens=output_budget, do_sample=False,
                num_beams=1, use_cache=True, stopping_criteria=StoppingCriteriaList([stopping]), **format_options)
        tokens = result[0, count:]
        eos = tokenizer_data.eos_token_id if use_semantic_json else model.generation_config.eos_token_id
        eos = eos if isinstance(eos, list) else [eos]
        finish = "stop" if len(tokens) and int(tokens[-1]) in eos and not stopping.expired else "length"
        if use_semantic_json:
            generation_stage('complete_' + finish)
            special = set(tokenizer.all_special_ids) | {token for token, value in tokenizer.added_tokens_decoder.items() if value.special}
            generation_stage('special_count_' + str(sum(int(token) in special for token in tokens)))
        text = tokenizer.decode(tokens, skip_special_tokens=True, clean_up_tokenization_spaces=False)
        if output_tokens is not None:
            return text, finish, dict(prompt_tokens=count, completion_tokens=len(tokens), total_tokens=count + len(tokens))
        return text, finish
    return generate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter")
    parser.add_argument("--adapter-weights-sha256")
    parser.add_argument("--adapter-config-sha256")
    parser.add_argument('--event-plan-model')
    parser.add_argument('--event-plan-adapter')
    parser.add_argument('--event-plan-adapter-weights-sha256')
    parser.add_argument('--event-plan-adapter-config-sha256')
    parser.add_argument('--piece-adapter')
    parser.add_argument('--piece-adapter-weights-sha256')
    parser.add_argument('--piece-adapter-config-sha256')
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--max-requests", type=int)
    parser.add_argument("--seconds", type=int)
    parser.add_argument("--analysis-service", action="store_true",
                        help="Serve ordinary Analysis until SIGTERM/SIGINT; no probe-count expiry.")
    parser.add_argument('--natural-reply-model', help='Also serve the existing base natural-reply profile with its separate API key.')
    parser.add_argument('--natural-reply-correction-target-context', action='store_true',
                        help='Admit locator-bound AI correction context for the shared natural profile only.')
    parser.add_argument('--semantic-json', action='store_true', help='Constrain Analysis JSON/source-quote pairs and explicit Piece field slots during generation.')
    parser.add_argument("--max-new-tokens", type=int)
    parser.add_argument("--context-tokens", type=int)
    parser.add_argument("--request-seconds", type=int)
    args = parser.parse_args()
    if args.natural_reply_model and not args.analysis_service:
        parser.error('shared natural reply requires explicit analysis service mode')
    if args.natural_reply_correction_target_context and not args.natural_reply_model:
        parser.error('AI correction context requires the shared natural reply profile')
    natural_reply = None
    if args.natural_reply_model:
        natural_key = os.environ.get("EMLIS_NATURAL_REPLY_API_KEY", "")
        if len(natural_key) < 24 or natural_key == os.environ.get("COCOLON_ANALYSIS_MODEL_API_KEY", ""):
            parser.error('shared natural reply requires its separate existing private key')
        natural_reply = {"api_key": natural_key, "model_name": args.natural_reply_model}
    if args.semantic_json and not args.analysis_service:
        parser.error('semantic JSON generation requires explicit analysis service mode')
    if args.analysis_service:
        if args.max_requests is not None or args.seconds is not None:
            parser.error("analysis service and bounded probe lifetime are separate modes")
        max_new_tokens = 4096 if args.max_new_tokens is None else args.max_new_tokens
        context_tokens = 16384 if args.context_tokens is None else args.context_tokens
        request_seconds = 210 if args.request_seconds is None else args.request_seconds
        if (not 1 <= max_new_tokens <= 8192 or not max_new_tokens < context_tokens <= 32768
                or not 1 <= request_seconds <= 210):
            parser.error("analysis service limits invalid")
        if args.adapter and (args.adapter_weights_sha256 is None or args.adapter_config_sha256 is None):
            parser.error("analysis service requires explicit identity for any selected adapter")
    else:
        if (args.max_requests is None or args.seconds is None
                or not 1 <= args.max_requests <= 18 or not 1 <= args.seconds <= 1800):
            parser.error("bounded probe limits required")
        if any(value is not None for value in (args.max_new_tokens, args.context_tokens, args.request_seconds)):
            parser.error("custom inference budgets require explicit analysis service mode")
        max_new_tokens, context_tokens, request_seconds = 2048, 8192, 23
    if args.adapter_weights_sha256 is not None or args.adapter_config_sha256 is not None:
        if (not args.adapter or not re.fullmatch(r'[0-9a-f]{64}', args.adapter_weights_sha256 or '')
                or not re.fullmatch(r'[0-9a-f]{64}', args.adapter_config_sha256 or '')):
            parser.error('an adapter and both SHA256 values are required together')
    piece_options = {}
    if any(value is not None for value in (args.piece_adapter,
            args.piece_adapter_weights_sha256, args.piece_adapter_config_sha256)):
        if (not args.analysis_service or not args.natural_reply_model or not args.semantic_json
                or not args.adapter or not args.piece_adapter
                or not re.fullmatch(r'[0-9a-f]{64}', args.piece_adapter_weights_sha256 or '')
                or not re.fullmatch(r'[0-9a-f]{64}', args.piece_adapter_config_sha256 or '')):
            parser.error('Piece adapter requires the shared constrained service and both SHA256 values')
        piece_options = dict(piece_adapter=args.piece_adapter,
            piece_weights_sha256=args.piece_adapter_weights_sha256,
            piece_config_sha256=args.piece_adapter_config_sha256)
    event_plan_options = {}
    if any(value is not None for value in (args.event_plan_model, args.event_plan_adapter,
            args.event_plan_adapter_weights_sha256, args.event_plan_adapter_config_sha256)):
        if (not args.analysis_service or not args.semantic_json or not args.adapter
                or not args.event_plan_model or args.event_plan_model == args.model_name
                or args.event_plan_model == args.natural_reply_model or not args.event_plan_adapter
                or not re.fullmatch(r'[0-9a-f]{64}', args.event_plan_adapter_weights_sha256 or '')
                or not re.fullmatch(r'[0-9a-f]{64}', args.event_plan_adapter_config_sha256 or '')):
            parser.error('Event plan requires its separate model alias, constrained adapter and both SHA256 values')
        event_plan_options = dict(event_plan_adapter=args.event_plan_adapter,
            event_plan_weights_sha256=args.event_plan_adapter_weights_sha256,
            event_plan_config_sha256=args.event_plan_adapter_config_sha256)
    key = (os.environ.get("COCOLON_ANALYSIS_MODEL_API_KEY", "") if args.analysis_service
           else os.environ.get("EMLIS_NATURAL_REPLY_API_KEY", ""))
    if len(key) < 24:
        parser.error("a private API key of at least 24 characters is required")
    stop = threading.Event()
    deadline = float("inf") if args.analysis_service else time.monotonic() + args.seconds
    # Hard process bound also covers model loading and a blocked GPU forward.
    # No model or adapter is ever being written when this process terminates.
    if not args.analysis_service:
        signal.signal(signal.SIGALRM, signal.SIG_DFL)
        signal.setitimer(signal.ITIMER_REAL, args.seconds)
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    identity_options = (dict(weights_sha256=args.adapter_weights_sha256,
                             config_sha256=args.adapter_config_sha256)
                        if args.adapter_weights_sha256 is not None else {})
    runtime_options = (dict(max_new_tokens=max_new_tokens, context_tokens=context_tokens)
                       if args.analysis_service else {})
    if args.semantic_json:
        runtime_options['semantic_json'] = True
    generator = load_generator(args.adapter, stop, **identity_options, **runtime_options, **piece_options, **event_plan_options)
    server = ThreadingHTTPServer(("0.0.0.0", args.port), make_handler(generator,
        api_key=key, model_name=args.model_name, deadline=deadline,
        max_requests=0 if args.analysis_service else args.max_requests,
        max_new_tokens=max_new_tokens, request_seconds=request_seconds,
        max_request_bytes=262144 if args.analysis_service else 65536,
        natural_reply=natural_reply, event_plan_model=args.event_plan_model,
        correction_target_context=args.natural_reply_correction_target_context,
        piece_revision='piece-lora:' + args.piece_adapter_weights_sha256 if piece_options else None))
    server.timeout = 1
    try:
        while not stop.is_set() and time.monotonic() < deadline:
            server.handle_request()
    finally:
        stop.set()
        server.server_close()


if __name__ == "__main__":
    main()
