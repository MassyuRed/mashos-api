"""Opt-in quoted roots locate their own targets without changing source meaning."""
import asyncio
import copy
from dataclasses import replace
import hashlib
import json
import unittest
from unittest.mock import AsyncMock, patch
from uuid import UUID

import analysis_cumulative_service as service
from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler
from cocolon_meaning_experience_engine.cores.analysis import observed_route_realizer as author
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as admission
from cocolon_meaning_experience_engine.cores.analysis.source_adapter import freeze_analysis_sources
from test_analysis_cumulative import OWNER, source_snapshot


ACTION='私は模型を作った'
WISH='私は模型を作りたくない'
TEXT=ACTION+'。'+WISH+'。'


def unit(quote,kind=None,parent=None,role=None,qualifiers=()):
    return dict(quote=quote,node_kind=kind,parent_quote=parent,scope_role=role,
        qualifiers=[dict(kind=k,quote=q) for k,q in qualifiers])


def roots_with_targets():
    return [unit(ACTION,'ACTION_OR_NONACTION'),unit('模型',parent=ACTION,role='CONTENT_TARGET'),
        unit(WISH,'ATTENTION_OR_THOUGHT',qualifiers=[('NEGATION','作りたくない')]),
        unit('模型',parent=WISH,role='CONTENT_TARGET')]


def prepare(text=TEXT,units=None,*,profile='selected_material.v10',snapshot=None):
    snap=source_snapshot(1) if snapshot is None else copy.deepcopy(snapshot)
    if snapshot is None:snap['members'][0]['original'].update(memo=text,memo_action='')
    p=service.prepare_cumulative_category_units(OWNER,snap,prompt_version=profile)
    rows=units if snapshot is not None else [roots_with_targets() if units is None else units]
    packet=dict(fields=[dict(field=i,units=row) for i,row in enumerate(rows,1)])
    raw=admission.canonical(packet)
    response=admission.AnalysisModelQuotedParentUnitsResponse(p.request_ref,
        admission.digest(p.messages()),hashlib.sha256(raw.encode()).hexdigest(),'stop',raw)
    return snap,p,replace(p,response=response)


class ParentLocalContentTests(unittest.TestCase):
    def candidate(self,**kwargs):
        snap,p,value=prepare(**kwargs)
        artifact,counts=service.build_cumulative_quoted_parent_candidates(OWNER,snap,model_input=value)
        return snap,p,value,artifact,counts

    def reject(self,**kwargs):
        with self.assertRaises(admission.AnalysisSemanticError):self.candidate(**kwargs)

    def test_each_direct_root_binds_its_duplicate_target_to_exact_source_bytes(self):
        snap,p,value,candidate,_=self.candidate()
        raw=value.response.raw
        field,=candidate.graph.fields
        frozen=freeze_analysis_sources(p.request);source,=frozen.sources
        children=[u for u in field.units if u.scope_role=='CONTENT_TARGET']
        self.assertEqual([u.evidence.scalar_start for u in children],
            [TEXT.index('模型'),TEXT.rindex('模型')])
        for u in field.units:
            e=u.evidence
            self.assertEqual(field.complete_source_text[e.scalar_start:e.scalar_end],u.quote)
            self.assertEqual(source.envelope.raw_utf8[e.utf8_start:e.utf8_end].decode(),u.quote)
            self.assertEqual(e.field_sha256,hashlib.sha256(TEXT.encode()).hexdigest())
            self.assertEqual(e.literal_sha256,hashlib.sha256(u.quote.encode()).hexdigest())
        a,c=service.build_cumulative_map(OWNER,snap,model_input=value)
        self.assertEqual((c['mapped_count'],c['unparsed_count']),(1,0))
        self.assertEqual([(n.node_kind,n.modality,n.polarity) for n in a.graph.nodes],
            [('ACTION_OR_NONACTION','fact','positive'),('ATTENTION_OR_THOUGHT','wish','negative')])
        self.assertFalse(a.graph.edges)
        self.assertEqual(a.source_members,frozen.members)
        self.assertEqual(a.source_set_ref,frozen.source_set_ref)
        self.assertEqual(value.response.raw,raw)

    def test_forward_parent_and_unicode_prefix_preserve_absolute_qualifier_offsets(self):
        action='私は昨日の模型を作った';wish='私は昨日の模型を作りたくない'
        text='🙂。'+wish+'。'+action+'。'
        child=unit('昨日の模型',parent=action,role='CONTENT_TARGET',qualifiers=[('RELATIVE_TIME','昨日')])
        _,p,_,candidate,_=self.candidate(text=text,units=[child,
            unit(wish,'ATTENTION_OR_THOUGHT'),unit(action,'ACTION_OR_NONACTION')])
        field,=candidate.graph.fields;u=field.units[0]
        self.assertEqual(u.parent,3)
        start=text.rindex('昨日の模型')
        self.assertEqual((u.evidence.scalar_start,u.evidence.scalar_end),(start,start+5))
        qualifier,=u.qualifiers
        self.assertEqual((qualifier.evidence.scalar_start,qualifier.evidence.scalar_end),(start,start+2))
        source,=freeze_analysis_sources(p.request).sources
        for evidence,literal in [(u.evidence,u.quote),(qualifier.evidence,qualifier.quote)]:
            self.assertEqual(source.envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end].decode(),literal)
            self.assertEqual(evidence.utf8_start,evidence.field_utf8_start+len(text[:evidence.scalar_start].encode()))

    def test_previous_quoted_profiles_and_integer_parent_wire_keep_global_uniqueness(self):
        for profile in ['baseline.v1','selected_material.v4','selected_material.v9']:
            with self.subTest(profile=profile):self.reject(profile=profile)
        snap,_,_=prepare()
        p=service.prepare_cumulative_model_units(OWNER,snap)
        rows=roots_with_targets()
        old=[dict(quote=u['quote'],node_kind=u['node_kind'],parent=None if u['parent_quote'] is None else
            next(i for i,p in enumerate(rows,1) if p['quote']==u['parent_quote']),
            scope_role=u['scope_role'],qualifiers=u['qualifiers']) for u in rows]
        raw=admission.canonical(dict(fields=[dict(field=1,units=old)]))
        response=admission.AnalysisModelUnitsResponse(p.request_ref,admission.digest(p.messages()),
            hashlib.sha256(raw.encode()).hexdigest(),'stop',raw)
        with self.assertRaises(admission.AnalysisSemanticError):
            service.build_cumulative_unit_candidates(OWNER,snap,model_input=replace(p,response=response))

    def test_ambiguous_root_and_repeated_or_overlapping_target_inside_parent_are_rejected(self):
        cases=[(ACTION+'。'+ACTION+'。',[unit(ACTION,'ACTION_OR_NONACTION'),
            unit('模型',parent=ACTION,role='CONTENT_TARGET')]),
            ('模型の模型。',[unit('模型の模型','SCENE'),unit('模型',parent='模型の模型',role='CONTENT_TARGET')]),
            ('aaa。',[unit('aaa','SCENE'),unit('aa',parent='aaa',role='CONTENT_TARGET')])]
        for text,units in cases:
            with self.subTest(text=text):self.reject(text=text,units=units)

    def test_unique_target_outside_root_keeps_legacy_binding_but_ambiguous_or_foreign_targets_fail(self):
        _,_,_,candidate,_=self.candidate(text=ACTION+'。私は写真を見た。',
            units=[unit(ACTION,'ACTION_OR_NONACTION'),unit('写真',parent=ACTION,role='CONTENT_TARGET')])
        root,target=candidate.graph.fields[0].units
        self.assertGreater(target.evidence.scalar_start,root.evidence.scalar_end)
        self.reject(text=ACTION+'。私は写真を見た。私は写真を残した。',
            units=[unit(ACTION,'ACTION_OR_NONACTION'),unit('写真',parent=ACTION,role='CONTENT_TARGET')])
        self.reject(units=[unit(ACTION,'ACTION_OR_NONACTION'),
            unit('写真',parent=ACTION,role='CONTENT_TARGET')])
        snap=source_snapshot(1)
        snap['members'][0]['original'].update(memo=ACTION+'。',memo_action='私は写真を見た。')
        self.reject(snapshot=snap,units=[[unit(ACTION,'ACTION_OR_NONACTION'),
            unit('模型',parent='私は写真を見た',role='CONTENT_TARGET')],
            [unit('私は写真を見た','ACTION_OR_NONACTION')]])

    def test_nested_and_unknown_roots_do_not_gain_parent_local_search(self):
        self.reject(text='abc abc',units=[unit('abc abc','SCENE'),
            unit('abc ',parent='abc abc',role='CONTENT_TARGET'),
            unit('abc',parent='abc ',role='CONTENT_TARGET')])
        self.reject(text='模型は分からない。模型。',units=[unit('模型は分からない',role='WRITTEN_UNKNOWN'),
            unit('模型',parent='模型は分からない',role='CONTENT_TARGET')])

    def test_written_reason_keeps_its_own_global_quote_even_outside_parent(self):
        text='雨が降ったので、私は記録を残した。';root='私は記録を残した'
        _,_,_,candidate,_=self.candidate(text=text,units=[unit(root,'ACTION_OR_NONACTION'),
            unit('雨が降ったので',parent=root,role='WRITTEN_REASON')])
        field,=candidate.graph.fields;root,reason=field.units
        self.assertEqual(reason.parent,root.index)
        self.assertLess(reason.evidence.scalar_end,root.evidence.scalar_start)
        self.reject(units=[unit(ACTION,'ACTION_OR_NONACTION'),
            unit('模型',parent=ACTION,role='WRITTEN_REASON')])

    def test_qualifiers_cannot_borrow_parent_text_or_resolve_their_own_ambiguity(self):
        rows=roots_with_targets();rows[1]['qualifiers']=[dict(kind='EXPLICIT_ACTOR',quote='私')]
        self.reject(units=rows)
        text='模型の模型を作った。模型。'
        self.reject(text=text,units=[unit('模型の模型を作った','ACTION_OR_NONACTION'),
            unit('模型の模型',parent='模型の模型を作った',role='CONTENT_TARGET',
                qualifiers=[('WRITTEN_MODIFIER','模型')])])

    def test_cycle_depth_and_unknown_parent_guards_still_reject(self):
        cases=[([unit('a',parent='b',role='CONTENT_TARGET'),unit('b',parent='a',role='CONTENT_TARGET')],
            'analysis_model_units_parent_cycle'),
            ([unit('abcde','SCENE'),unit('abcd',parent='abcde',role='CONTENT_TARGET'),
                unit('abc',parent='abcd',role='CONTENT_TARGET'),unit('ab',parent='abc',role='CONTENT_TARGET')],
             'analysis_model_units_parent_depth'),
            ([unit('abcde','SCENE'),unit('a',parent='abcde',role='UNKNOWN_CONTENT')],
             'analysis_model_units_unknown_parent_invalid')]
        for rows,reason in cases:
            with self.subTest(reason=reason),self.assertRaisesRegex(admission.AnalysisSemanticError,reason):
                self.candidate(text='abcde',units=rows)

    def test_saved_candidate_rebinds_identical_absolute_ranges_without_regeneration(self):
        snap,_,value,a,c=self.candidate()
        raw=service.serialize_cumulative_quoted_parent_candidates(OWNER,snap,model_input=value,artifact=a,coverage=c)
        forbidden=AssertionError('saved candidate must not regenerate')
        with patch.object(compiler,'compile_analysis_unit_candidates',side_effect=forbidden),\
             patch.object(author,'realize_analysis_unit_candidates',side_effect=forbidden):
            restored,counts=service.reload_cumulative_quoted_parent_candidates(OWNER,snap,raw)
        self.assertEqual((restored.graph,counts),(a.graph,c))
        self.assertEqual(json.loads(raw)['state']['response']['raw'],value.response.raw)

    def test_v10_bare_role_and_decision_keep_global_object_bindings_graph_and_text(self):
        binder=admission._bind_model_unit_fields
        def legacy_binding(*args,**kwargs):
            kwargs['allow_parent_local_content_targets']=False
            return binder(*args,**kwargs)
        for negative in (False,True):
            with self.subTest(negative=negative):
                role='担当しなかった' if negative else '担当した'
                decision='決めなかった' if negative else '決めた'
                text='私は会合の進行を'+role+'。その後、私は分担を'+decision+'。'
                rows=[unit(role,'ROLE'),unit('会合の進行',parent=role,role='CONTENT_TARGET'),
                    unit(decision,'ACTION_OR_NONACTION'),unit('分担',parent=decision,role='CONTENT_TARGET')]
                snap,p,value,candidate,counts=self.candidate(text=text,units=rows)
                a,c=service.build_cumulative_map(OWNER,snap,model_input=value)
                self.assertIsNotNone(a)
                self.assertEqual((c['mapped_count'],c['unparsed_count']),(1,0))
                self.assertEqual(a.graph,compiler.compile_observed_graph(freeze_analysis_sources(p.request)))
                self.assertEqual(len(a.graph.edges),1)
                for parent,child in [(candidate.graph.fields[0].units[0],candidate.graph.fields[0].units[1]),
                        (candidate.graph.fields[0].units[2],candidate.graph.fields[0].units[3])]:
                    self.assertLess(child.evidence.scalar_end,parent.evidence.scalar_start)
                with patch.object(admission,'_bind_model_unit_fields',side_effect=legacy_binding):
                    old_candidate,old_counts=service.build_cumulative_quoted_parent_candidates(OWNER,snap,model_input=value)
                    old,old_c=service.build_cumulative_map(OWNER,snap,model_input=value)
                self.assertEqual((candidate.graph,counts),(old_candidate.graph,old_counts))
                self.assertEqual((a.graph,c),(old.graph,old_c))
                self.assertEqual(a.safe_text_projection(authenticated_owner_scope=OWNER)['text'],
                    old.safe_text_projection(authenticated_owner_scope=OWNER)['text'])

    def test_saved_v10_bare_predicates_restore_candidate_and_normal_map_without_generation(self):
        text='私は会合の進行を担当した。その後、私は分担を決めた。'
        rows=[unit('担当した','ROLE'),unit('会合の進行',parent='担当した',role='CONTENT_TARGET'),
            unit('決めた','ACTION_OR_NONACTION'),unit('分担',parent='決めた',role='CONTENT_TARGET')]
        snap,_,value,candidate,counts=self.candidate(text=text,units=rows)
        a,c=service.build_cumulative_map(OWNER,snap,model_input=value)
        saved=service.serialize_cumulative_quoted_parent_candidates(OWNER,snap,
            model_input=value,artifact=candidate,coverage=counts)
        forbidden=AssertionError('saved bare predicates must not regenerate')
        with patch.object(compiler,'compile_analysis_unit_candidates',side_effect=forbidden),\
             patch.object(author,'realize_analysis_unit_candidates',side_effect=forbidden):
            self.assertEqual(service.reload_cumulative_quoted_parent_candidates(OWNER,snap,saved),(candidate,counts))
        row=dict(id=str(UUID(a.artifact_id[9:])),source_profile=service.PROFILE,report_mode='standard',
            content_text=a.safe_text_projection(authenticated_owner_scope=OWNER)['text'],
            content_json=dict(report_mode='standard',watashiMap=a.safe_projection(authenticated_owner_scope=OWNER),map_context=c))
        expected=dict(items=[row],subscription_tier='free',matched=True,history_limit=2)
        with patch.object(service,'_rpc',AsyncMock(return_value=json.loads(admission.canonical(expected)))),\
             patch.object(compiler,'compile_observed_graph',side_effect=forbidden),\
             patch.object(compiler,'compile_model_observed_role_decision',side_effect=forbidden),\
             patch.object(author,'realize_observed_graph',side_effect=forbidden):
            self.assertEqual(asyncio.run(service.read_maps(OWNER,report_id=row['id'])),expected)

    def test_binding_fix_keeps_bad_past_wish_modifier_unread_in_its_own_record(self):
        snap=source_snapshot(2)
        snap['members'][0]['original'].update(memo='私は日記を書きたかった。',memo_action='')
        snap['members'][1]['original'].update(memo=TEXT,memo_action='')
        snap,p,value=prepare(snapshot=snap,units=[
            [unit('私は日記を書きたかった','ATTENTION_OR_THOUGHT',qualifiers=[('WRITTEN_MODIFIER','たかった')])],
            roots_with_targets()])
        candidate,_=service.build_cumulative_quoted_parent_candidates(OWNER,snap,model_input=value)
        self.assertEqual(len(candidate.graph.fields),2)
        a,c=service.build_cumulative_map(OWNER,snap,model_input=value)
        self.assertEqual((c['source_count'],c['mapped_count'],c['unparsed_count']),(2,1,1))
        self.assertEqual(len(a.graph.nodes),2)
        self.assertEqual({r for n in a.graph.nodes for r in n.record_refs},{snap['members'][1]['original']['id']})


if __name__=='__main__':unittest.main()
