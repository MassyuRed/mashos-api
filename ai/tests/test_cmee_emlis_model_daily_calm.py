"""Approved finite daily family; synthetic semantics, no GPU/model calls.

Old snapshots/messages are executable pre-change captures, not new expectations
derived from the modified owners. PostgreSQL cases use the existing real SQL.
"""
import copy
from dataclasses import asdict, replace
import itertools
import json
from pathlib import Path

import pytest

from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
from cocolon_meaning_experience_engine.contracts import GenerationRequest, EngineStatus
from cocolon_meaning_experience_engine.source_kernel import freeze_text_source
from cocolon_meaning_experience_engine.emlis_thread_contracts import EmlisThreadInputV1
from cocolon_meaning_experience_engine.emlis_semantic_admission import (
    MODEL_PROFILE, SemanticInput, SemanticNotAdopted, prepare_model_snapshot,
    restore_model_snapshot, _model_semantic_ref,
)
from cocolon_meaning_experience_engine.model_candidate_source import build_model_messages
from cocolon_meaning_experience_engine.preparation import prepare_emlis, receive_candidate
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from emlis_ai_grounded_observation_gate import evaluate_emlis_model_surface_inverse
from emlis_thread_service import EmlisThreadService
from test_emlis_q2_application import db, case, run


FIXTURE = json.loads((Path(__file__).parent / "fixtures/cmee_emlis_model_daily_calm_v1.json").read_text())


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def daily_request(food="うどん", warm="あったかいもの", particle="", degree="ちょっと"):
    raw = dict(FIXTURE["daily_mapping"]["original"])
    raw["memo_action"] = f"帰ってから、{food}を作って食べた。"
    raw["memo"] = f"{warm}{particle}食べたら、{degree}落ち着いた。"
    req = GenerationRequest("daily-synthetic-request", build_emlis_current_input_bundle(raw), raw["id"])
    source = freeze_text_source(req)
    return replace(req, emlis_thread=EmlisThreadInputV1("daily-synthetic-thread", source.envelope.envelope_id))


def daily_packet(req):
    """Rebind the frozen teacher, never copy a model result or production parser."""
    raw = req.current_input_bundle.raw_current_input
    sid = prepare_emlis(req).payload()["sources"][0]["source_id"]
    food = "雑炊" if "雑炊" in raw["memo_action"] else "うどん"
    warm = "温かいもの" if "温かいもの" in raw["memo"] else "あったかいもの"
    degree = "少し" if "少し" in raw["memo"] else "ちょっと"
    particle = "を" if warm + "を食べた" in raw["memo"] else ""
    def visit(value):
        if isinstance(value, dict):
            return {k: visit(v) for k, v in value.items()}
        if isinstance(value, list):
            return [visit(v) for v in value]
        if isinstance(value, str):
            return value.replace("FT-UDON-O", sid).replace("うどん", food).replace(
                "あったかいもの食べた", warm + particle + "食べた").replace("あったかいもの", warm).replace("ちょっと", degree)
        return value
    packet = visit(FIXTURE["daily_mapping"]["packet"])
    for e in packet["evidence"]:
        e["start"] = raw[e["field_path"]].index(e["quote"])
        e["end"] = e["start"] + len(e["quote"])
    return packet


def semantic(req, packet):
    material = prepare_emlis(req)
    receipt = receive_candidate(material, request_id=material.request_id,
        raw_output=canonical(packet), finish_reason="stop", provider="synthetic-not-model")
    return SemanticInput("FRESH_CANDIDATE", receipt, semantic_profile=MODEL_PROFILE)


def prepared_daily(req=None, packet=None):
    req = req or daily_request()
    packet = packet or daily_packet(req)
    return req, prepare_model_snapshot(req, semantic(req, packet))


def outcome(req, prepared):
    resumed = replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=prepared.checkpoint.checkpoint_id))
    return MeaningExperienceEngine().generate(resumed, semantic_input=SemanticInput(
        "RESUME_ADOPTED", snapshot_json=prepared.semantic_snapshot, semantic_profile=MODEL_PROFILE))


@pytest.mark.parametrize("stage", ["initial", "corrected"])
def test_old_chair_prechange_complete_snapshot_outcome_and_messages_are_identical(stage):
    from test_cmee_emlis_model_proposal import initial_result, corrected_result
    req, prepared, out = initial_result() if stage == "initial" else corrected_result()
    p = json.loads(prepared.semantic_snapshot)
    prior = canonical(p["prior_snapshot"]) if p["prior_snapshot"] else None
    actual = {key: getattr(prepared, key) for key in (
        "semantic_snapshot", "meaning_json", "native_bindings_json", "surface_proposal_json", "question_proposal_json")}
    actual.update(outcome=asdict(out), messages=build_model_messages(req, prior))
    assert json.loads(canonical(actual)) == FIXTURE["chair_baseline"][stage]
    assert p["admission_version"] == p["adapter_version"] == "1"
    assert "family" not in p["native_bindings"]


@pytest.mark.parametrize("food,warm,particle,degree", list(itertools.product(
    ("うどん", "雑炊"), ("あったかいもの", "温かいもの"), ("", "を"), ("ちょっと", "少し"))))
def test_daily_preserves_all_five_roles_four_links_degree_selections_and_no_question(food, warm, particle, degree):
    req = daily_request(food, warm, particle, degree)
    _, prepared = prepared_daily(req)
    p = json.loads(prepared.semantic_snapshot)
    native = p["native_bindings"]
    assert p["admission_version"] == p["adapter_version"] == "2"
    assert native["family"] == "DAILY_CALM_V1" and native["stage"] == "INITIAL"
    assert len(native["roles"]) == 5 and len(native["written_links"]) == 4
    assert native["roles"]["slight_calm"]["text"] == degree + "落ち着いた"
    raw = req.current_input_bundle.raw_current_input
    assert native["preserved_selections"] == {k: raw[k] for k in ("category", "emotions", "emotion_details", "is_secret")}
    assert len(native["source_slices"]) == 8
    for e in native["source_slices"]:
        assert raw[e["field_path"]][e["start"]:e["end"]] == e["quote"]
    result = outcome(req, prepared)
    assert result.status is EngineStatus.GENERATED and result.body_state == "FINAL", result.reason_codes
    assert result.question is None and result.artifact.update_note is None
    assert result.artifact.observation == f"帰ってから、{food}を作って食べたのですね。"
    assert result.artifact.reception == f"{warm}を食べて、少し落ち着けてよかったです。"
    assert restore_model_snapshot(req, prepared.semantic_snapshot) == prepared


@pytest.mark.parametrize("index,mutation", [(0,"reverse"),(1,"remove"),(2,"reverse"),(3,"reverse"),(3,"cause")])
def test_daily_relationships_require_both_return_scopes_written_te_and_noncausal_tara(index, mutation):
    req = daily_request(); packet = daily_packet(req)
    r = packet["candidate"]["relations"][index]
    if mutation == "reverse":
        r["from_claim_id"], r["to_claim_id"] = r["to_claim_id"], r["from_claim_id"]
    elif mutation == "remove":
        packet["candidate"]["relations"].pop(index)
    else:
        r["type"] = "OBJECTIVE_CAUSE"
    with pytest.raises(SemanticNotAdopted):
        prepare_model_snapshot(req, semantic(req, packet))


@pytest.mark.parametrize("field,extra", [("memo", "お腹が空いていた。"), ("memo", "だから元気になった。"),
    ("memo_action", "友人は"), ("memo_action", "今日は")])
def test_daily_rejects_extra_full_source_while_candidate_quotes_and_ids_still_match(field, extra):
    req = daily_request(); raw = dict(req.current_input_bundle.raw_current_input)
    raw[field] += extra
    req = replace(req, current_input_bundle=build_emlis_current_input_bundle(raw), emlis_thread=None)
    source = freeze_text_source(req)
    req = replace(req, emlis_thread=EmlisThreadInputV1("daily-synthetic-thread",source.envelope.envelope_id))
    with pytest.raises(SemanticNotAdopted, match="source_out_of_scope"):
        prepare_model_snapshot(req, semantic(req, daily_packet(req)))


@pytest.mark.parametrize("key,value", [("unknowns",[{"unknown_id":"why"}]), ("updates",[{}]),
    ("question_proposal",{}), ("update_note","理由を確認します。")])
def test_daily_cannot_create_gap_question_or_update(key, value):
    req = daily_request(); packet=daily_packet(req)
    target=packet["candidate"]["surface_proposal"] if key=="update_note" else packet["candidate"]
    target[key]=value
    with pytest.raises(SemanticNotAdopted):
        prepare_model_snapshot(req, semantic(req, packet))


@pytest.mark.parametrize("mutation", ["degree", "subject", "polarity", "merge_eating", "remove_return", "remove_cook"])
def test_daily_claim_coverage_does_not_accept_only_valid_quotes_and_references(mutation):
    req=daily_request(); packet=daily_packet(req)
    cs=packet["candidate"]["claims"]
    if mutation=="degree":
        cs[4]["predicate"]["surface"]="落ち着いた"
    elif mutation=="subject":
        cs[4]["subject"]["binding"]="SELF"
    elif mutation=="polarity":
        cs[4]["polarity"]["value"]="NEGATED"
    elif mutation=="merge_eating":
        packet["candidate"]["relations"][3]["from_claim_id"]="eat"
    else:
        cs.pop(0 if mutation=="remove_return" else 1)
    with pytest.raises(SemanticNotAdopted):
        prepare_model_snapshot(req,semantic(req,packet))


@pytest.mark.parametrize("section,text", [
    ("observation","うどんを作って食べたのですね。"),
    ("observation","帰ってから、うどんを食べたのですね。"),
    ("observation","うどんを作ってから帰って食べたのですね。"),
    ("observation","帰ってから、雑炊を作って食べたのですね。"),
    ("reception","あったかいものを食べて、落ち着けてよかったです。"),
    ("reception","あったかいものを食べて、すっかり落ち着けてよかったです。"),
    ("reception","温かいうどんを食べて、少し落ち着けてよかったです。"),
    ("reception","お腹が空いていたので、食べて落ち着いたのですね。"),
    ("reception","落ち着きたくて、あったかいものを食べたのですね。"),
    ("reception","温かい食事には、心を落ち着ける効果があります。"),
    ("reception","あったかいものを食べて、少し落ち着けてよかったです。大丈夫です。"),
    ("reception","あったかいものを食べて、少し落ち着けてよかったです？"),
])
def test_independent_daily_reader_rejects_changed_words_with_unchanged_valid_refs(section, text):
    req=daily_request(); packet=daily_packet(req)
    packet["candidate"]["surface_proposal"][section]=text
    _,prepared=prepared_daily(req,packet)
    with pytest.raises(ValueError, match="model_surface_"):
        evaluate_emlis_model_surface_inverse(proposal=json.loads(prepared.surface_proposal_json),
            meaning_packet=json.loads(prepared.meaning_json), native_bindings=json.loads(prepared.native_bindings_json))
    result=outcome(req,prepared)
    assert result.artifact is None and result.meaning_checkpoint==prepared.checkpoint


@pytest.mark.parametrize("section,field,index", [(0,"relation_refs",0),(0,"relation_refs",1),
    (0,"relation_refs",2),(1,"relation_refs",0),(0,"claim_refs",0),(1,"claim_refs",1)])
def test_independent_daily_reader_requires_complete_section_binding(section,field,index):
    _,prepared=prepared_daily(); proposal=json.loads(prepared.surface_proposal_json)
    proposal["bindings"][section][field].pop(index)
    with pytest.raises(ValueError,match="binding_or_coverage"):
        evaluate_emlis_model_surface_inverse(proposal=proposal,meaning_packet=json.loads(prepared.meaning_json),
            native_bindings=json.loads(prepared.native_bindings_json))


def test_daily_saved_version_is_derived_from_source_even_with_a_recomputed_hash():
    req,prepared=prepared_daily(); p=json.loads(prepared.semantic_snapshot)
    p["admission_version"]=p["adapter_version"]="1"
    p["snapshot_ref"]=_model_semantic_ref(p)
    with pytest.raises(SemanticNotAdopted,match="snapshot_binding_invalid"):
        restore_model_snapshot(req,canonical(p))


def test_daily_messages_describe_the_new_shape_but_preserve_complete_source():
    req=daily_request("雑炊","温かいもの","を","少し")
    messages=build_model_messages(req); p=json.loads(messages[1]["content"])
    assert p["output_spec"]["shape"]["candidate"]["unknowns"]==[]
    assert "Daily initial only" in p["output_spec"]["meaning"]
    assert "solo" not in p["output_spec"]["meaning"]
    assert p["material"]["sources"][0]["text_fields"]["memo"]==req.current_input_bundle.raw_current_input["memo"]
    assert [m["role"] for m in messages]==["system","user"]


@pytest.mark.parametrize("variant", [False,True])
def test_daily_real_sql_saved_reads_use_no_generation_and_leave_events_unchanged(case,db,variant):
    user,parent,_=case
    proto=daily_request("雑炊","温かいもの","を","少し") if variant else daily_request()
    raw=proto.current_input_bundle.raw_current_input
    db.query("update public.emotions set memo=$1,memo_action=$2,category=array['生活'],emotions=array['平穏','喜び'],emotion_details=$3 where id=$4",
        [raw["memo"],raw["memo_action"],json.dumps(raw["emotion_details"],ensure_ascii=False),parent])
    calls=[]
    def source(req,prior):
        assert prior is None
        calls.append(req.request_id)
        return semantic(req,daily_packet(req)).receipt
    service=EmlisThreadService(semantic_profile=MODEL_PROFILE,offline_candidate_source=source,offline_model_attempt_seconds=180)
    completed=run(service.start(user,parent))
    assert completed["state"]=="COMPLETED" and completed["body_state"]=="FINAL",completed
    assert completed["issued_count"]==0 and completed["pending_question"] is None
    before=run(service.store.read(user,input_id=parent))
    assert len([e for e in before["events"] if e["kind"]=="MEANING_UPDATE"])==1
    assert len([e for e in before["events"] if e["kind"]=="OBSERVATION"])==1
    class NoGeneration:
        def __getattr__(self,_name):
            raise AssertionError("saved daily read requested generation")
    reader=EmlisThreadService(engine=NoGeneration())
    assert run(reader.get(user,parent))=={**completed,"can_write":False}
    assert run(reader.start(user,parent))=={**completed,"can_write":False}
    after=run(service.store.read(user,input_id=parent))
    # SQL returns a fresh server clock on every read; persisted values do not change.
    assert {k:v for k,v in after.items() if k!="now"}=={k:v for k,v in before.items() if k!="now"}
    assert len(calls)==1
