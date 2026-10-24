"""Synthetic repair/reuse proposals; no provider or product-quality claims."""
import copy
import json
from dataclasses import asdict, replace

import pytest

from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
from cocolon_meaning_experience_engine.contracts import GenerationRequest
from cocolon_meaning_experience_engine.source_kernel import freeze_text_source
from cocolon_meaning_experience_engine.emlis_thread_contracts import (
    EmlisThreadInputV1, EmlisQuestionControlV1, SupplementalAnswerSource)
from cocolon_meaning_experience_engine.preparation import prepare_emlis, receive_candidate
from cocolon_meaning_experience_engine.emlis_semantic_admission import (
    MODEL_PROFILE, MODEL_SCHEMA, MODEL_CHECKPOINT_SCHEMA, MODEL_CANDIDATE_SCHEMA,
    SemanticInput, SemanticNotAdopted, ModelPreparedMeaning, prepare_model_snapshot,
    restore_model_snapshot, model_question, model_prior_for_messages,
    prepare_snapshot_meaning)


def initial_model_request(object_text="ぐらついていた椅子", *, record="model-synthetic"):
    raw = dict(id=record, created_at="2026-10-24T00:00:00Z",
        memo="全部一人で直せたことが、うれしかった。",
        memo_action=f"{object_text}を修理して、また座れるようになった。",
        category=["生活"], emotions=["喜び"],
        emotion_details=[dict(type="喜び", strength="medium")], is_secret=False)
    req = GenerationRequest("model-synthetic-request",build_emlis_current_input_bundle(raw),record)
    source = freeze_text_source(req)
    return replace(req,emlis_thread=EmlisThreadInputV1("model-synthetic-thread",source.envelope.envelope_id))


def _ev(sid,field,text,quote):
    start = text.index(quote)
    return dict(source_id=sid,field_path=field,start=start,end=start+len(quote),quote=quote)


def model_packet(req, prior=None):
    """Hand-authored synthetic model-shaped data, never a model output."""
    raw = req.current_input_bundle.raw_current_input
    sid,memo,action = raw["id"],raw["memo"],raw["memo_action"]
    event,result = action.rstrip("。").split("、")
    ev = [_ev(sid,"memo_action",action,event),_ev(sid,"memo_action",action,result),
        _ev(sid,"memo",memo,"うれしかった"),_ev(sid,"memo",memo,"全部一人で直せたこと"),
        _ev(sid,"memo_action",action,"して、"),_ev(sid,"memo",memo,memo.rstrip("。"))]
    def claim(cid,kind,index):
        return dict(claim_id=cid,kind=kind,text=ev[index]["quote"],
            subject=dict(binding="OMITTED",source_entity=None,evidence_indexes=[]),
            predicate=dict(surface=ev[index]["quote"],arguments=[]),
            polarity=dict(value="AFFIRMED",scope_refs=[cid],evidence_indexes=[index]),
            modality=dict(value="ASSERTED_AS_WRITTEN",evidence_indexes=[index]),
            about_time=dict(kind="WRITTEN_PAST_UNRESOLVED_OCCASION",expression=None,
                anchor_source_id=ev[index]["source_id"],evidence_indexes=[index]),
            qualifiers=[],evidence_indexes=[index])
    def relation(rid,kind,left,right,index):
        return dict(relation_id=rid,type=kind,from_claim_id=left,to_claim_id=right,
            polarity="AFFIRMED",scope_refs=[rid],qualifiers=[],evidence_indexes=[index])
    claims = [claim("repair","EVENT",0),claim("usable_again","ACTION_RESULT",1),claim("joy","STATE",2)]
    relations = [relation("repair_and_result","SOURCE_WRITTEN_TE_LINK","repair","usable_again",4)]
    updates=[]
    if prior is None:
        claims.append(claim("solo_appraisal_object","USER_APPRAISAL_OBJECT",3))
        relations.append(relation("joy_ground","USER_STATED_JOY_GROUND","solo_appraisal_object","joy",5))
        unknowns=[dict(unknown_id="personal_significance",kind="NOT_STATED",
            target_claim_refs=["solo_appraisal_object","joy"],description="詳しい本人の意味づけは未記載。",evidence_indexes=[3,2])]
        proposal=dict(text="「全部一人で直せたこと」がなぜ嬉しかったのですか？",
            target_unknown_ref="personal_significance",focus="PERSONAL_JOY_SIGNIFICANCE",claim_refs=["solo_appraisal_object","joy"])
        surface=dict(observation="椅子を修理して、また座れるようになったのですね。",
            reception="全部一人で直せたことが、うれしかったのですね。",update_note=None,
            bindings=[dict(section="observation",claim_refs=["repair","usable_again"],relation_refs=["repair_and_result"]),
                dict(section="reception",claim_refs=["solo_appraisal_object","joy"],relation_refs=["joy_ground"])])
    else:
        a=req.emlis_thread.answers[0];text=a.answer_text_private;aid=a.answer_id
        for quote in ["さっき「全部一人で」と書いたのは訂正します","友人に手順を教えてもらって",
            "一緒に直しました","捨てずにまた使えるようになったからです","一人でできたからではなく",
            "うれしかったのも、一人でできたからではなく、捨てずにまた使えるようになったからです"]:
            ev.append(_ev(aid,"answer_text_private",text,quote))
        claims.extend([claim("friend_guidance","EVENT",7),claim("joint_repair","EVENT",8),
            claim("reuse_appraisal_object","USER_APPRAISAL_OBJECT",9)])
        relations.append(relation("joy_ground_revised","USER_STATED_JOY_GROUND","reuse_appraisal_object","joy",11))
        for op,kind,target,replacements,indexes in [
            ("REVISE","CLAIM","solo_appraisal_object",["friend_guidance","joint_repair"],[6,7,8]),
            ("REVISE","RELATION","joy_ground",["joy_ground_revised"],[10,11]),
            ("INVALIDATE_GAP","UNKNOWN","personal_significance",[],[6,11])]:
            updates.append(dict(operation=op,target_kind=kind,target_ref=target,replacement_refs=replacements,
                evidence_indexes=indexes,prior_snapshot_ref=prior.checkpoint.snapshot_ref))
        unknowns=[];proposal=None
        surface=dict(observation="友人に手順を教わり、一緒に椅子を直したのですね。",
            reception="捨てずにまた使えるようになったことが、うれしかったのですね。",
            update_note="共同修理と、また使えることへの喜びへ訂正しました。",
            bindings=[dict(section="observation",claim_refs=["friend_guidance","joint_repair"],relation_refs=[]),
                dict(section="reception",claim_refs=["reuse_appraisal_object","joy"],relation_refs=["joy_ground_revised"]),
                dict(section="update_note",claim_refs=["friend_guidance","joint_repair","reuse_appraisal_object"],
                    relation_refs=["joy_ground_revised"],update_refs=[0,1,2])])
    return dict(candidate=dict(schema_version=MODEL_CANDIDATE_SCHEMA,core="emlis",claims=claims,
        relations=relations,unknowns=unknowns,conflicts=[],updates=updates,
        surface_proposal=surface,question_proposal=proposal),evidence=ev)


def model_semantic(req,packet=None,prior=None,**metadata):
    material=prepare_emlis(req)
    receipt=receive_candidate(material,request_id=material.request_id,
        raw_output=json.dumps(packet or model_packet(req,prior),ensure_ascii=False),finish_reason="stop",**metadata)
    return SemanticInput("FRESH_CANDIDATE",receipt,
        prior_snapshot_json=prior.semantic_snapshot if prior else None,semantic_profile=MODEL_PROFILE)


def model_answer(req,prepared,text=None):
    _,q=model_question(prepared,parent_request_id=req.request_id)
    assert q is not None
    text=text or ("さっき「全部一人で」と書いたのは訂正します。途中で友人に手順を教えてもらって、一緒に直しました。\n\n"
        "うれしかったのも、一人でできたからではなく、捨てずにまた使えるようになったからです。")
    answer=SupplementalAnswerSource("model-synthetic-answer",req.emlis_thread.thread_id,q.question_id,1,
        req.emlis_thread.original_source_ref,text,"2026-10-24T01:00:00Z")
    return replace(req,emlis_thread=replace(req.emlis_thread,answers=(answer,),current_round=1,
        question_control_context=EmlisQuestionControlV1(q,(q.decision.target_ref,),1)))


def test_model_initial_source_roles_cases_and_selection_are_retained():
    req=initial_model_request();p=prepare_model_snapshot(req,model_semantic(req))
    assert type(p) is ModelPreparedMeaning
    assert p.checkpoint.semantic_schema_version==MODEL_CHECKPOINT_SCHEMA
    snapshot=json.loads(p.semantic_snapshot);native=json.loads(p.native_bindings_json)
    assert snapshot["schema_version"]==MODEL_SCHEMA
    assert native["roles"]["repair"]["text"]=="ぐらついていた椅子を修理して"
    assert native["case_arguments"][0]["text"]=="ぐらついていた椅子"
    assert native["case_arguments"][0]["written_role"]=="を"
    assert native["preserved_selections"]["emotion_details"]==[{"type":"喜び","strength":"medium"}]
    assert p.checkpoint.answer_update is None
    assert prepare_snapshot_meaning(req,model_semantic(req))==p


def test_model_surface_wording_and_provider_metadata_do_not_change_meaning_identity():
    req=initial_model_request();packet=model_packet(req)
    first=prepare_model_snapshot(req,model_semantic(req,packet))
    packet["candidate"]["surface_proposal"]["reception"]="一人で直せた喜びがあったのですね。"
    second=prepare_model_snapshot(req,model_semantic(req,packet,provider="synthetic",elapsed_seconds=1))
    assert first.checkpoint.snapshot_ref==second.checkpoint.snapshot_ref
    assert first.checkpoint.checkpoint_id==second.checkpoint.checkpoint_id
    assert json.loads(first.semantic_snapshot)["proposal_ref"]!=json.loads(second.semantic_snapshot)["proposal_ref"]
    assert first.semantic_snapshot!=second.semantic_snapshot


def test_model_gap_description_is_not_adopted_as_person_stated_knowledge():
    req=initial_model_request();packet=model_packet(req)
    first=prepare_model_snapshot(req,model_semantic(req,packet))
    packet["candidate"]["unknowns"][0]["description"]="モデル自身による未検証の説明文。"
    second=prepare_model_snapshot(req,model_semantic(req,packet))
    assert first.checkpoint.snapshot_ref==second.checkpoint.snapshot_ref
    assert json.loads(second.meaning_json)["candidate"]["unknowns"][0]["description"]=="詳しい本人の意味づけは未記載。"
    assert json.loads(second.semantic_snapshot)["packet"]["candidate"]["unknowns"][0]["description"]=="モデル自身による未検証の説明文。"
    # Different targets are not repaired by canonicalizing the description.
    packet["candidate"]["unknowns"][0]["target_claim_refs"]=["repair","joy"]
    with pytest.raises(SemanticNotAdopted):prepare_model_snapshot(req,model_semantic(req,packet))


def test_model_snapshot_replay_rebinds_source_without_provider_or_new_adoption():
    req=initial_model_request();p=prepare_model_snapshot(req,model_semantic(req))
    assert restore_model_snapshot(req,p.semantic_snapshot)==p
    changed=initial_model_request(record="different-source")
    with pytest.raises(SemanticNotAdopted):restore_model_snapshot(changed,p.semantic_snapshot)
    modified=json.loads(p.semantic_snapshot);modified["native_bindings"]["roles"]["joy"]["text"]="悲しかった"
    with pytest.raises(SemanticNotAdopted):restore_model_snapshot(req,json.dumps(modified,ensure_ascii=False,sort_keys=True,separators=(",",":")))


@pytest.mark.parametrize("mutation",["polarity","time","subject","relation_direction","relation_cause","missing_result","person_unknown"])
def test_model_valid_locations_do_not_adopt_wrong_meaning(mutation):
    req=initial_model_request();packet=model_packet(req);c=packet["candidate"]
    if mutation=="polarity":c["claims"][2]["polarity"]["value"]="NEGATED"
    if mutation=="time":c["claims"][2]["about_time"]["kind"]="ANSWER_TIME"
    if mutation=="subject":c["claims"][2]["subject"]={"binding":"EXPLICIT","source_entity":"友人","evidence_indexes":[0]}
    if mutation=="relation_direction":c["relations"][1]["from_claim_id"],c["relations"][1]["to_claim_id"]="joy","solo_appraisal_object"
    if mutation=="relation_cause":c["relations"][0]["type"]="OBJECTIVE_CAUSE"
    if mutation=="missing_result":c["claims"].pop(1)
    if mutation=="person_unknown":c["unknowns"][0]["kind"]="PERSON_STATED"
    with pytest.raises(SemanticNotAdopted):prepare_model_snapshot(req,model_semantic(req,packet))


def test_model_source_family_reads_novel_object_instead_of_fixture_lookup():
    req=initial_model_request("壊れていた長椅子")
    p=prepare_model_snapshot(req,model_semantic(req))
    assert json.loads(p.native_bindings_json)["case_arguments"][0]["text"]=="壊れていた長椅子"


@pytest.mark.parametrize("object_text",[
    "古い椅子を壊して新しい椅子", "古い椅子を捨てて新しい椅子",
    "椅子に座って古い棚", "同僚と話して古い椅子", "友人が直した椅子",
    "古い椅子を壊して壊れていた長椅子",
])
def test_model_added_action_cannot_be_swallowed_by_patient_slot(object_text):
    req=initial_model_request(object_text)
    # The model proposal quotes the whole apparent patient and has matching
    # locations. Independent source grammar must still reject its lost action.
    with pytest.raises(SemanticNotAdopted) as rejected:
        prepare_model_snapshot(req,model_semantic(req))
    assert rejected.value.decision=="UNSUPPORTED"
    assert rejected.value.reason_code=="model_repair_reuse_source_out_of_scope"
    assert req.current_input_bundle.raw_current_input["memo_action"].startswith(object_text)


@pytest.mark.parametrize("object_text",["ぐらついていた椅子","壊れていた長椅子","緩んでいた棚","古い机","新しいテーブル"])
def test_model_single_state_modifier_and_unlisted_noun_remain_supported(object_text):
    req=initial_model_request(object_text)
    prepared=prepare_model_snapshot(req,model_semantic(req))
    assert json.loads(prepared.native_bindings_json)["case_arguments"][0]["text"]==object_text


def test_model_added_action_cannot_be_swallowed_by_participant_slot():
    req=initial_model_request();first=prepare_model_snapshot(req,model_semantic(req))
    text=("さっき「全部一人で」と書いたのは訂正します。途中で友人を訪ねて同僚に手順を教えてもらって、一緒に直しました。\n\n"
          "うれしかったのも、一人でできたからではなく、捨てずにまた使えるようになったからです。")
    answered=model_answer(req,first,text)
    packet=model_packet(model_answer(req,first),first)
    # Bind the claim to the full participant clause instead of relying on a
    # quote mismatch. The independent nominal-slot boundary is what rejects it.
    quote="友人を訪ねて同僚に手順を教えてもらって"
    for index,old in enumerate(packet["evidence"]):
        if old["field_path"]=="answer_text_private":
            packet["evidence"][index]=_ev(old["source_id"],old["field_path"],text,
                quote if index==7 else old["quote"])
    packet["candidate"]["claims"][3]["text"]=quote
    packet["candidate"]["claims"][3]["predicate"]["surface"]=quote
    with pytest.raises(SemanticNotAdopted) as rejected:
        prepare_model_snapshot(answered,model_semantic(answered,packet,first))
    assert rejected.value.decision=="UNSUPPORTED"
    assert rejected.value.reason_code=="model_correction_source_out_of_scope"


def test_model_unknown_added_clause_and_other_person_are_unsupported():
    for obj in ("友人が直した椅子","もし壊れていた椅子"):
        req=initial_model_request(obj)
        with pytest.raises(SemanticNotAdopted):prepare_model_snapshot(req,model_semantic(req))


def test_model_actual_question_answer_and_three_prior_updates_replay():
    req=initial_model_request();first=prepare_model_snapshot(req,model_semantic(req))
    decision,q=model_question(first,parent_request_id=req.request_id)
    assert decision.disposition=="ASK" and q.answer_limit==1
    second_req=model_answer(req,first);packet=model_packet(second_req,first)
    second=prepare_model_snapshot(second_req,model_semantic(second_req,packet,first))
    assert second.checkpoint.answer_update.disposition=="RESOLVED"
    assert len(second.checkpoint.answer_update.updates)==3
    assert second.checkpoint.inactive_claim_refs==("solo_appraisal_object","joy_ground","personal_significance")
    native=json.loads(second.native_bindings_json)
    assert native["stage"]=="AFTER_CORRECTION"
    assert "solo_appraisal_object" not in native["roles"]
    assert [r["text"] for r in native["case_arguments"]]==["ぐらついていた椅子","友人","手順"]
    assert native["source_negations"][1]["quote"]=="捨てずに"
    assert model_question(second,parent_request_id=req.request_id)[1] is None
    assert restore_model_snapshot(second_req,second.semantic_snapshot)==second
    prior=model_prior_for_messages(second_req,first.semantic_snapshot)
    assert prior["snapshot_ref"]==first.checkpoint.snapshot_ref
    assert "surface_proposal" not in prior["meaning_packet"]["candidate"]
    assert "question_proposal" not in prior["meaning_packet"]["candidate"]


@pytest.mark.parametrize("mutation",["stale_prior","unaffected","old_reason","gap","wrong_question"])
def test_model_answer_rejects_update_and_pending_mismatches(mutation):
    req=initial_model_request();first=prepare_model_snapshot(req,model_semantic(req))
    answered=model_answer(req,first);packet=model_packet(answered,first)
    if mutation=="stale_prior":packet["candidate"]["updates"][0]["prior_snapshot_ref"]="fabricated"
    if mutation=="unaffected":packet["candidate"]["claims"][0]["claim_id"]="changed-id"
    if mutation=="old_reason":packet["candidate"]["relations"][1]["from_claim_id"]="joint_repair"
    if mutation=="gap":packet["candidate"]["updates"].pop()
    if mutation=="wrong_question":
        control=answered.emlis_thread.question_control_context
        altered=replace(control.pending_question,prompt_private="別の問い")
        answered=replace(answered,emlis_thread=replace(answered.emlis_thread,
            question_control_context=replace(control,pending_question=altered)))
    with pytest.raises(SemanticNotAdopted):prepare_model_snapshot(answered,model_semantic(answered,packet,first))


def test_model_saved_packet_cannot_be_replaced_by_old_completed_json_or_unknown_profile():
    req=initial_model_request();packet=model_packet(req)
    packet["candidate"]["schema_version"]="cocolon.cmee.semantic_mapping_proposal.v1"
    with pytest.raises(SemanticNotAdopted):prepare_model_snapshot(req,model_semantic(req,packet))
    semantic=model_semantic(req)
    with pytest.raises(SemanticNotAdopted):prepare_model_snapshot(req,replace(semantic,semantic_profile="other"))


def test_model_prior_helper_rejects_foreign_source_before_messages():
    req=initial_model_request();p=prepare_model_snapshot(req,model_semantic(req))
    assert model_prior_for_messages(req,None) is None
    with pytest.raises(SemanticNotAdopted):model_prior_for_messages(req,p.semantic_snapshot)
    foreign=initial_model_request(record="foreign-original")
    fp=prepare_model_snapshot(foreign,model_semantic(foreign))
    answered=model_answer(req,p)
    with pytest.raises(SemanticNotAdopted):model_prior_for_messages(answered,fp.semantic_snapshot)
