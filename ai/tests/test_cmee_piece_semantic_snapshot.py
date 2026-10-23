"""P4 actual sole writer, author-free review and private replay. No live DB/API."""
from dataclasses import asdict, replace
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_v1c import (
    PieceGenerationRequest, compile_piece_artifact_plan, realize_piece_artifact,
)
from cocolon_meaning_experience_engine.preparation import prepare_piece, receive_candidate
import cocolon_meaning_experience_engine.piece_semantic_admission as sem
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_content_policy import validate_piece_semantic_preservation, validate_source_meaning_preservation
from piece_v2_contract import canonical_json_bytes

FIXTURE=json.loads((Path(__file__).parent/'fixtures/cmee_piece_semantic_snapshot_v1.json').read_text())


def context(*,tier='free',packet=None,original=None,owner='synthetic-piece-owner',stage='normal_observation',requested=None):
    original=deepcopy(FIXTURE['original'] if original is None else original)
    source=PieceSourceSnapshot(owner,original['id'],FIXTURE['source_version'],
        '\n\n'.join(original[k] for k in ('memo','memo_action') if original[k]),
        source_stage=stage,saved_original_json=canonical_json_bytes(original))
    request=PieceGenerationRequest('p4-synthetic',source,owner,source.saved_input_id,
        source.source_version,tier=tier,requested_format=requested)
    prepared=prepare_piece(source,expected_owner_id=owner,tier=tier)
    raw=sem.canonical(FIXTURE['packet'] if packet is None else packet)
    receipt=receive_candidate(prepared,request_id=prepared.request_id,raw_output=raw,finish_reason='stop')
    return request,sem.PieceSemanticInputV1(prepared,receipt)


def generated(**kwargs):
    request,input=context(**kwargs)
    result=MeaningExperienceEngine().generate(request,semantic_input=input)
    assert result.status.value=='GENERATED',result.reason_codes
    return request,input,result


def test_six_claims_five_sentences_and_selections_reach_actual_author():
    request,input,result=generated()
    assert input.prepared.request_id==FIXTURE['p1_request_ref']
    assert input.receipt.adoption_state=='NOT_ADOPTED'
    assert len(result.snapshot.claim_bindings)==6
    assert len({b.node_ref for b in result.snapshot.claim_bindings})==5
    assert len(result.snapshot.relation_bindings)==2
    assert result.artifact.piece_text==request.source.original_text
    assert 'でも自分の仕事が残って、帰るのが遅くなった。' in result.artifact.piece_text
    assert '不安' not in result.artifact.piece_text and '弱い' not in result.artifact.piece_text
    assert [(s.label,s.strength,s.alias_refs,s.coverage_state) for s in result.snapshot.source_selections]==[
        ('喜び','weak',('emotions:0','emotion_details:0'),'SOURCE_SELECTION_RETAINED_NOT_TEXTUALIZED'),
        ('不安','weak',('emotions:1','emotion_details:1'),'SOURCE_SELECTION_RETAINED_NOT_TEXTUALIZED')]
    assert result.artifact.meaning_contract_version==sem.MEANING_VERSION
    assert not hasattr(result.artifact,'content_payload')
    assert all('助かった' not in repr(o) for o in (result,result.snapshot,result.plan,result.artifact))


@pytest.mark.parametrize('tier',['free','plus','premium'])
def test_existing_tiers_and_only_eligible_format(tier):
    request,input,result=generated(tier=tier)
    validate_source_meaning_preservation(result.snapshot,result.plan,result.artifact)
    assert result.artifact.eligible_formats==('short_essay',)


@pytest.mark.parametrize('requested',['quote','declaration','missing'])
def test_profile_cannot_grant_unqualified_format(requested):
    request,input=context(tier='premium',requested=requested)
    assert MeaningExperienceEngine().generate(request,semantic_input=input).artifact is None


@pytest.mark.parametrize('mutation',[
    'polarity','subject','time','modality','negation_scope','report_scope','argument',
    'cause','relation_endpoint','missing_claim','missing_relation','duplicate_claim',
    'extra_field','unknown','conflict','update','unused_evidence','quote','bool_index',
])
def test_correct_quotes_do_not_admit_wrong_meaning(mutation):
    packet=deepcopy(FIXTURE['packet']); c=packet['candidate']
    if mutation=='polarity':c['claims'][3]['polarity']['value']='AFFIRMED'
    if mutation=='subject':c['claims'][1]['subject']['source_entity']='自分'
    if mutation=='time':c['claims'][0]['about_time']['kind']='WRITTEN_CURRENT_EVALUATION'
    if mutation=='modality':c['claims'][4]['modality']['value']='ASSERTED_AS_WRITTEN'
    if mutation=='negation_scope':c['claims'][3]['polarity']['scope_refs']=['p.help']
    if mutation=='report_scope':c['claims'][0]['qualifiers']=[]
    if mutation=='argument':c['claims'][4]['predicate']['arguments'][0]['text']='次回の余裕'
    if mutation=='cause':c['relations'][1]['type']='CAUSE'
    if mutation=='relation_endpoint':c['relations'][0]['to_claim_id']='p.help'
    if mutation=='missing_claim':c['claims'].pop()
    if mutation=='missing_relation':c['relations'].pop()
    if mutation=='duplicate_claim':c['claims'][1]['claim_id']=c['claims'][0]['claim_id']
    if mutation=='extra_field':c['claims'][0]['score']=1
    if mutation=='unknown':c['unknowns']=[{'description':'原因不明'}]
    if mutation=='conflict':c['conflicts']=[{}]
    if mutation=='update':c['updates']=[{}]
    if mutation=='unused_evidence':packet['evidence'].append(deepcopy(packet['evidence'][0]))
    if mutation=='quote':packet['evidence'][0]['quote']='助かった'
    if mutation=='bool_index':c['claims'][0]['evidence_indexes']=[True]
    request,input=context(packet=packet)
    result=MeaningExperienceEngine().generate(request,semantic_input=input)
    assert result.artifact is None and result.snapshot is None
    assert result.decision in ('REJECTED','UNSUPPORTED')


@pytest.mark.parametrize('field',['emotions','emotion_details'])
def test_full_selection_source_changes_cannot_reuse_old_prepared(field):
    request,input=context(); original=deepcopy(FIXTURE['original'])
    original[field]=list(reversed(original[field]))
    changed,_=context(original=original)
    assert MeaningExperienceEngine().generate(changed,semantic_input=input).decision=='REJECTED'


@pytest.mark.parametrize('mutation',['duplicate','mismatch','strength','extra','missing_label','invalid_label'])
def test_selection_shape_and_aliases_are_not_ignored(mutation):
    original=deepcopy(FIXTURE['original'])
    if mutation=='duplicate':original['emotions']=['喜び','喜び']
    if mutation=='mismatch':original['emotion_details'].reverse()
    if mutation=='strength':original['emotion_details'][0]['strength']='maximum'
    if mutation=='extra':original['emotion_details'][0]['why']='不明'
    if mutation=='missing_label':original['emotion_details'][0].pop('type')
    if mutation=='invalid_label':original['emotions'][0]='信頼'
    request,input=context(original=original)
    assert MeaningExperienceEngine().generate(request,semantic_input=input).decision=='REJECTED'


@pytest.mark.parametrize('mutation',['expected_owner','expected_id','expected_version','mode','profile','receipt'])
def test_request_and_receipt_are_rebound(mutation):
    request,input=context()
    if mutation=='expected_owner':request=replace(request,expected_owner_id='other')
    if mutation=='expected_id':request=replace(request,expected_saved_input_id='other')
    if mutation=='expected_version':request=replace(request,expected_source_version='other')
    if mutation=='mode':request=replace(request,execution_mode='EMLIS_APPLICATION')
    if mutation=='profile':input=replace(input,semantic_profile='emlis_candidate_snapshot.v2')
    if mutation=='receipt':input=replace(input,receipt=replace(input.receipt,candidate_json='{}'))
    assert MeaningExperienceEngine().generate(request,semantic_input=input).decision=='REJECTED'


@pytest.mark.parametrize('finish',['timeout','length','error','unknown'])
def test_candidate_failure_dominates_well_formed_packet(finish):
    request,input=context()
    receipt=receive_candidate(input.prepared,request_id=input.prepared.request_id,
        raw_output=input.receipt.raw_output,finish_reason=finish)
    result=MeaningExperienceEngine().generate(request,semantic_input=replace(input,receipt=receipt))
    assert result.decision=='HOLD' and result.snapshot is None


def test_author_free_review_does_not_replay_compiler_or_author():
    request,input,result=generated()
    with patch('cocolon_meaning_experience_engine.piece_v1c.compile_piece_artifact_plan',side_effect=AssertionError('compiler')), \
         patch('cocolon_meaning_experience_engine.piece_v1c.realize_piece_artifact',side_effect=AssertionError('author')):
        validate_piece_semantic_preservation(result.snapshot,result.plan,result.artifact,tier='free',requested_format=None)


@pytest.mark.parametrize('mutation',['negation','current','cause','anxiety','degree','drop','duplicate','order','trace','selection','namespace','plan'])
def test_rehashed_artifact_mutations_are_rejected(mutation):
    request,input,result=generated(); artifact=result.artifact; plan=result.plan
    blocks=list(artifact.body_blocks)
    if mutation=='negation':blocks[0]=blocks[0].replace('わけではない','わけだ')
    if mutation=='current':blocks[0]=blocks[0].replace('うれしかった','うれしい')
    if mutation=='cause':blocks[0]=blocks[0].replace('残って、','残ったから、')
    if mutation=='anxiety':blocks[0]+='不安もあった。'
    if mutation=='degree':blocks[0]=blocks[0].replace('うれしかった','少しうれしかった')
    if mutation=='drop':blocks[0]=blocks[0].replace('手伝ったことを後悔しているわけではない。','')
    if mutation=='duplicate':blocks[0]+='帰るのが遅くなった。'
    if mutation=='order':blocks.reverse()
    text='\n\n'.join(blocks)
    artifact=replace(artifact,body_blocks=tuple(blocks),piece_text=text,piece_text_hash=hashlib.sha256(text.encode()).hexdigest())
    if mutation=='trace':artifact=replace(artifact,claim_realizations=artifact.claim_realizations[:-1])
    if mutation=='selection':artifact=replace(artifact,retained_selection_refs=())
    if mutation=='namespace':artifact=replace(artifact,meaning_contract_version='piece.content_meaning.v1')
    if mutation=='plan':plan=replace(plan,selection_duties=())
    with pytest.raises(ValueError):
        validate_piece_semantic_preservation(result.snapshot,plan,artifact,tier='free',requested_format=None)


@pytest.mark.parametrize('stage',['meaning','plan','complete'])
def test_interrupted_replay_never_reacquires_or_readopts(stage):
    request,input,result=generated()
    plan=result.plan if stage!='meaning' else None
    artifact=result.artifact if stage=='complete' else None
    raw=sem.serialize_piece_semantic_state(request,result.snapshot,plan,artifact)
    with patch.object(sem,'admit_piece_semantic_snapshot',side_effect=AssertionError('readopt')), \
         patch.object(sem,'receive_candidate',side_effect=AssertionError('reacquire')):
        if stage=='complete':
            with patch('cocolon_meaning_experience_engine.piece_v1c.realize_piece_artifact',side_effect=AssertionError('reauthor')), \
                 patch('cocolon_meaning_experience_engine.piece_v1c.compile_piece_artifact_plan',side_effect=AssertionError('recompile')):
                restored=sem.resume_piece_semantic(request,raw)
        else:restored=sem.resume_piece_semantic(request,raw)
    assert restored==result
    assert sem.serialize_piece_semantic_state(request,restored.snapshot,restored.plan,restored.artifact)==sem.serialize_piece_semantic_state(request,result.snapshot,result.plan,result.artifact)


@pytest.mark.parametrize('mutation',['owner','id','version','stage','tier','request','selection','claim','snapshot_hash','unknown_version','extra_state'])
def test_saved_state_cannot_transfer_or_rehash_new_meaning(mutation):
    request,input,result=generated()
    raw=sem.serialize_piece_semantic_state(request,result.snapshot,result.plan,result.artifact)
    state=json.loads(raw)
    if mutation=='owner':request,_=context(owner='another-owner')
    if mutation=='id':request=replace(request,expected_saved_input_id='other-record')
    if mutation=='version':request=replace(request,expected_source_version='other-version')
    if mutation=='stage':request,_=context(stage='pre_question_observation')
    if mutation=='tier':request=replace(request,tier='premium')
    if mutation=='request':request=replace(request,request_id='different-operation')
    if mutation=='selection':state['snapshot']['source_selections'][0]['strength']='strong'
    if mutation=='claim':
        packet=json.loads(state['snapshot']['candidate_packet']);packet['candidate']['claims'][3]['polarity']['value']='AFFIRMED'
        state['snapshot']['candidate_packet']=sem.canonical(packet)
    if mutation=='snapshot_hash':state['snapshot']['snapshot_ref']='piece-snapshot:'+'0'*64
    if mutation=='unknown_version':state['snapshot']['adapter_version']=2
    if mutation=='extra_state':state['injected']='new'
    if mutation in ('selection','claim'):
        pre=deepcopy(state['snapshot']);pre.pop('snapshot_ref');state['snapshot']['snapshot_ref']='piece-snapshot:'+sem.digest(pre)
    with pytest.raises(ValueError):sem.load_piece_semantic_state(request,sem.canonical(state))


def test_same_p1_identity_does_not_grant_saved_owner_transfer():
    request,input,result=generated(); other,other_input=context(owner='other-owner')
    assert input.prepared.request_id==other_input.prepared.request_id
    raw=json.loads(sem.serialize_piece_semantic_state(request,result.snapshot,result.plan,result.artifact))
    raw['request_binding']['owner_id']='other-owner'
    with pytest.raises(ValueError):sem.load_piece_semantic_state(other,sem.canonical(raw))


def test_regular_b8_keeps_its_existing_selection_refusal():
    request,input=context()
    with pytest.raises(ValueError,match='saved_emotion_meaning_not_yet_supported'):
        generate_piece_candidate(request.source,authenticated_owner_id=request.expected_owner_id)


@pytest.mark.parametrize('mutation',['admission_bool','adapter_bool','selection_bool','selection_rehash','binding_rehash'])
def test_direct_snapshot_strict_types_and_rehashed_bindings(mutation):
    request,input,result=generated();snapshot=result.snapshot
    if mutation=='admission_bool':snapshot=replace(snapshot,admission_version=True)
    if mutation=='adapter_bool':snapshot=replace(snapshot,adapter_version=True)
    if mutation=='selection_bool':snapshot=replace(snapshot,source_selections=(snapshot.source_selections[0],replace(snapshot.source_selections[1],selection_index=True)))
    if mutation=='selection_rehash':snapshot=replace(snapshot,source_selections=(replace(snapshot.source_selections[0],strength='strong'),snapshot.source_selections[1]))
    if mutation=='binding_rehash':snapshot=replace(snapshot,claim_bindings=(replace(snapshot.claim_bindings[0],node_ref='invented'),*snapshot.claim_bindings[1:]))
    if mutation.endswith('rehash'):
        payload=sem._snapshot_payload(snapshot);payload.pop('snapshot_ref')
        snapshot=replace(snapshot,snapshot_ref='piece-snapshot:'+sem.digest(payload))
    with pytest.raises(ValueError):compile_piece_artifact_plan(snapshot)


def test_body_failure_keeps_adopted_snapshot_for_explicit_replay():
    request,input=context()
    with patch('cocolon_meaning_experience_engine.piece_v1c.realize_piece_artifact',side_effect=ValueError('private-body-failure')):
        result=MeaningExperienceEngine().generate(request,semantic_input=input)
    assert result.decision=='ADOPTED_PROVISIONAL' and result.artifact is None
    assert result.snapshot is not None and result.request_ref==input.prepared.request_id
    assert result.reason_codes==('piece_semantic_body_unavailable',)
    restored=sem.resume_piece_semantic(request,sem.serialize_piece_semantic_state(request,result.snapshot))
    assert restored.artifact is not None and restored.snapshot==result.snapshot


def test_unsupported_retains_valid_material_request_ref():
    request,input=context();original=deepcopy(FIXTURE['original']);original['memo']='今日は休んだ。'
    packet=deepcopy(FIXTURE['packet'])
    packet['evidence']=[dict(source_id=original['id'],field_path='memo',start=0,end=len(original['memo']),quote=original['memo'])]
    request,input=context(original=original,packet=packet)
    result=MeaningExperienceEngine().generate(request,semantic_input=input)
    assert result.decision=='UNSUPPORTED' and result.request_ref==input.prepared.request_id


def test_forged_overflow_metadata_is_a_stable_rejection():
    request,input=context();metadata=json.loads(input.receipt.metadata_json)
    metadata['elapsed_seconds']=10**309
    input=replace(input,receipt=replace(input.receipt,metadata_json=sem.canonical(metadata)))
    result=MeaningExperienceEngine().generate(request,semantic_input=input)
    assert result.decision=='REJECTED' and result.request_ref==input.prepared.request_id


def test_actual_interruption_after_private_meaning_save(tmp_path):
    request,input=context()
    with patch('cocolon_meaning_experience_engine.piece_v1c.realize_piece_artifact',side_effect=ValueError('interrupted')):
        meaning=sem.admit_piece_semantic_snapshot(request,input).snapshot
        saved=tmp_path/'private-piece.json'
        saved.write_text(sem.serialize_piece_semantic_state(request,meaning))
        with pytest.raises(ValueError,match='interrupted'):
            sem.resume_piece_semantic(request,saved.read_text())
    with patch.object(sem,'admit_piece_semantic_snapshot',side_effect=AssertionError('readopt')), \
         patch.object(sem,'receive_candidate',side_effect=AssertionError('reacquire')):
        restored=sem.resume_piece_semantic(request,saved.read_text())
    assert restored.snapshot==meaning and restored.artifact is not None
