"""Acquire only the sanctioned synthetic inputs exported by the local PGlite case.

Run from the exact source checkout with its production Python imports available.
This program needs neither pytest nor Node. It calls configured model endpoints only, without database access.
"""
import argparse
import asyncio
from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path
import time

from analysis_model_source import (
    analysis_model_prompt_version, application_analysis_model_source, semantic_analysis_input_fits,
)
from analysis_semantic_map import prepare_semantic_map
from api_deep_insight import _generate_candidate, natural_reply_provider_settings
from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import SEMANTIC_MAP_OCCURRENCE_V24_PROFILE
from cocolon_meaning_experience_engine.deep_insight_question import generate_question, prepare_question_material


def digest(value):
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


async def records(cases):
    name = natural_reply_provider_settings()['model']
    assert '4b' in name.casefold(), 'expected the configured natural 4B route'
    outcomes = {}
    for key, material in cases.items():
        prepared, sources = prepare_question_material(material, lane='records', theme=None)
        calls = []

        async def generate(system, model_input):
            started = time.monotonic()
            result = await _generate_candidate(system, model_input)
            calls.append(dict(system_sha256=sha256(system.encode()).hexdigest(), input_sha256=digest(model_input),
                              raw=result, seconds=round(time.monotonic() - started, 3)))
            return result

        outcome = await generate_question(prepared, sources, material=material, generate=generate)
        outcomes[key] = dict(result=asdict(outcome), calls=calls)
    return {'model': name, 'records': outcomes}


async def analysis(packet):
    source = application_analysis_model_source()
    profile = analysis_model_prompt_version(source)
    assert profile == SEMANTIC_MAP_OCCURRENCE_V24_PROFILE, 'expected the configured real v24 Analysis Map route'
    prepared = prepare_semantic_map(packet['owner'], packet['snapshot'], prompt_version=profile)
    assert prepared.request_ref == packet['request_ref']
    assert digest(json.loads(prepared.material_json)) == packet['material_sha256']
    assert semantic_analysis_input_fits(prepared), 'the synthetic case must fit the normal single-map request'
    started = time.monotonic()
    response = await source(prepared)
    return {'analysis_profile': profile, 'seconds': round(time.monotonic() - started, 3), 'response': asdict(response)}


async def capture(packet):
    assert packet['synthetic'] is True
    if packet['kind'] == 'records':
        result = await records(packet['cases'])
    elif packet['kind'] == 'map':
        result = await analysis(packet)
    else:
        raise ValueError('unknown synthetic capture kind')
    return {'kind': packet['kind'], 'input_sha256': digest(packet), **result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('refusing to overwrite existing capture')
    packet = json.loads(args.input.read_text(encoding='utf-8'))
    result = asyncio.run(capture(packet))
    with args.output.open('x', encoding='utf-8') as target:
        os.chmod(args.output, 0o600)
        json.dump(result, target, ensure_ascii=False, separators=(',', ':'))
        target.write('\n')
    print(result['kind'], result['input_sha256'], args.output.name)


if __name__ == '__main__':
    main()
