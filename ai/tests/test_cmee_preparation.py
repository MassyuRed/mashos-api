"""Synthetic source and candidate boundaries; no model, service, DB or generation.

These tests establish P1 material/receipt behavior only. A located quotation
does not establish that its candidate interpretation is correct or adopted.
"""
from copy import deepcopy
from dataclasses import replace
import json
import unittest

from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
from piece_v2_contract import canonical_json_bytes
from piece_v2_generation import PieceSourceSnapshot
from cocolon_meaning_experience_engine.contracts import GenerationRequest
from cocolon_meaning_experience_engine.source_kernel import freeze_text_source
from cocolon_meaning_experience_engine.emlis_thread_contracts import (
    EmlisQuestionControlV1, EmlisThreadInputV1, SupplementalAnswerSource,
)
from cocolon_meaning_experience_engine.emlis_thread_source import admit_emlis_thread
from cocolon_meaning_experience_engine.emlis_question import original_meaning_plan, question_candidate
from cocolon_meaning_experience_engine.emlis_thread_history import OwnedHistorySourceV1
from cocolon_meaning_experience_engine.cores.analysis.source_adapter import (
    AnalysisObservedMapRequest, AnalysisSavedRecord, AnalysisSupplement,
    canonical_bytes, commitment,
)
from cocolon_meaning_experience_engine.preparation import (
    prepare_emlis, prepare_piece, prepare_analysis, receive_candidate,
)


OWNER = "synthetic-preparation-owner"


def original(record_id="prep-original", *, memo=None, created_at=None):
    return {
        "id": record_id,
        "created_at": created_at or "2026-10-21T16:30:00+09:00",
        "memo": memo or "うれしかったけど、どこがうれしかったかはまだ曖昧。",
        "memo_action": "打合せで後輩に説明を任せて、最後まで聞いた。",
        "category": ["仕事"], "emotions": ["喜び"],
        "emotion_details": [{"type": "喜び", "strength": "medium"}],
    }


def emlis_request(raw=None):
    raw = deepcopy(raw or original())
    request = GenerationRequest("synthetic-preparation", current_input_bundle=
        build_emlis_current_input_bundle(raw), expected_source_record_id=raw["id"])
    admitted = freeze_text_source(request)
    return replace(request, emlis_thread=EmlisThreadInputV1(
        "synthetic-preparation-thread", admitted.envelope.envelope_id,
        capability_snapshot="Q3_FREE",
        question_control_context=EmlisQuestionControlV1(question_limit=1)))


def piece_source(raw=None):
    raw = deepcopy(raw or original("prep-piece"))
    view = "\n\n".join(raw[key] for key in ("memo", "memo_action")
                         if raw[key] is not None and raw[key].strip())
    return PieceSourceSnapshot(OWNER, raw["id"], "emlis.current_input_bundle.v1",
        view, saved_original_json=canonical_json_bytes(raw))


def native_answer_request(record_id="prep-native-answer-original"):
    """Issue an actual native synthetic question; no C0 probe or fake pending."""
    request = emlis_request(original(record_id, memo="褒められたのに、嬉しくなかった。"))
    admitted = admit_emlis_thread(request)
    decision, question = question_candidate(admitted, original_meaning_plan(admitted),
                                           parent_request_id=request.request_id)
    if question is None or decision.disposition != "ASK":
        raise AssertionError("Synthetic source no longer issues its native question")
    thread = request.emlis_thread
    answer = SupplementalAnswerSource(record_id + "-answer", thread.thread_id,
        question.question_id, 1, thread.original_source_ref,
        "期待されているように感じて、その時は重かったです。", "2026-10-21T08:00:00Z")
    control = EmlisQuestionControlV1(pending_question=question,
        asked_target_refs=(question.decision.target_ref,), issued_count=1,
        issued_questions=(question,), question_limit=1)
    return replace(request, emlis_thread=replace(thread, answers=(answer,),
        current_round=1, question_control_context=control)), question


def analysis_record(raw, *, supplements=()):
    return AnalysisSavedRecord(OWNER, raw["id"], commitment(raw),
        canonical_bytes(raw).decode("utf-8"), supplements=supplements)


def analysis_request(*records):
    return AnalysisObservedMapRequest("synthetic-preparation-analysis", OWNER,
        "2026-10-21T00:00:00+09:00", "2026-10-22T00:00:00+09:00", tuple(records))


def candidate_for(request, *, source_id=None, field="memo", start=0, end=None):
    source = request.payload()["sources"][0]
    text = source["text_fields"][field]
    end = len(text) if end is None else end
    return {"candidate": {"meaning": "A provisional reading, not a source fact."},
        "evidence": [{"source_id": source_id or source["source_id"],
            "field_path": field, "start": start, "end": end,
            "quote": text[start:end]}]}


class PreparationSourceTests(unittest.TestCase):
    def test_stopped_control_has_no_question_budget(self):
        request = emlis_request()
        request = replace(request, emlis_thread=replace(request.emlis_thread,
            question_control_context=EmlisQuestionControlV1(stop=True)))
        control = prepare_emlis(request).payload()["control"]
        self.assertTrue(control["stop"])
        self.assertEqual(control["actual_question_budget_remaining"], 0)

    def test_emlis_keeps_original_fields_and_actual_question_state(self):
        raw = original()
        prepared = prepare_emlis(emlis_request(raw))
        payload = prepared.payload()
        self.assertEqual(payload["sources"][0]["original"], raw)
        self.assertEqual(payload["sources"][0]["text_fields"],
                         {key: raw[key] for key in ("memo", "memo_action")})
        self.assertIsNone(payload["control"]["pending_question"])
        self.assertEqual(payload["control"]["issued_count"], 0)
        self.assertEqual(payload["tier"], "free")
        self.assertEqual(payload["task"], "EMLIS_INITIAL_MATERIAL")
        self.assertEqual(payload["adoption_state"], "NOT_ADOPTED")

    def test_material_is_detached_from_original_and_payload_nested_mutation(self):
        request = emlis_request()
        prepared = prepare_emlis(request)
        before, identity = prepared.payload(), prepared.request_id
        request.current_input_bundle.raw_current_input["category"].append("生活")
        detached = prepared.payload()
        detached["sources"][0]["original"]["emotion_details"][0]["type"] = "怒り"
        self.assertEqual(prepared.payload(), before)
        self.assertEqual(prepared.request_id, identity)

    def test_same_material_identity_and_changed_original_are_distinct(self):
        first = prepare_emlis(emlis_request())
        self.assertEqual(first.request_id, prepare_emlis(emlis_request()).request_id)
        other = prepare_emlis(emlis_request(original(memo="今日は少し嬉しかった。")))
        self.assertNotEqual(first.request_id, other.request_id)

    def test_supplement_probe_keeps_no_pending_and_is_not_a_thread_answer(self):
        request = emlis_request()
        probe = dict(source_id="prep-probe", source_role="SUPPLEMENTAL_ANSWER",
            parent_record_id="prep-original", text="理由はまだわかりません。")
        payload = prepare_emlis(request, supplemental_probe=probe).payload()
        self.assertEqual(len(request.emlis_thread.answers), 0)
        self.assertEqual(payload["sources"][1]["role"], "SUPPLEMENTAL_PROBE")
        self.assertFalse(payload["sources"][1]["thread_answer_admitted"])
        self.assertIsNone(payload["sources"][1]["envelope_id"])
        self.assertIsNone(payload["control"]["pending_question"])
        self.assertEqual(payload["control"]["actual_update_status"],
                         "N_A_NO_ACTUAL_PENDING_QUESTION")

    def test_generated_role_or_wrong_parent_cannot_be_a_supplement_probe(self):
        probe = dict(source_id="prep-probe", source_role="SUPPLEMENTAL_ANSWER",
            parent_record_id="prep-original", text="本人の補足です。")
        for change in ({"source_role": "GENERATED_OBSERVATION"},
                       {"parent_record_id": "another-record"},
                       {"source_id": "prep-original"}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                prepare_emlis(emlis_request(), supplemental_probe=dict(probe, **change))

    def test_native_answer_is_a_separate_source_and_question_is_control_only(self):
        request, question = native_answer_request()
        payload = prepare_emlis(request).payload()
        source = payload["sources"][1]
        answer = request.emlis_thread.answers[0]
        self.assertEqual(payload["task"], "EMLIS_ANSWER_MATERIAL")
        self.assertEqual(source["role"], "SUPPLEMENTAL_ANSWER")
        self.assertEqual(source["source_id"], answer.answer_id)
        self.assertEqual(source["text_fields"], {"answer_text_private": answer.answer_text_private})
        self.assertEqual(source["parent_record_id"], request.expected_source_record_id)
        self.assertEqual(source["recorded_at"], answer.recorded_at)
        self.assertIsNotNone(source["envelope_id"])
        self.assertTrue(source["evidence"])
        self.assertEqual({row["field_path"] for row in source["evidence"]},
                         {"answer_text_private"})
        self.assertEqual(payload["control"]["pending_question"]["prompt_private"],
                         question.prompt_private)
        self.assertFalse(any(question.question_id == row["source_id"] for row in payload["sources"]))
        self.assertFalse(any("prompt_private" in row["text_fields"] for row in payload["sources"]))
        invalid = candidate_for(prepare_emlis(request))
        invalid["evidence"][0].update(source_id=answer.answer_id,
            field_path="prompt_private", start=0, end=len(question.prompt_private),
            quote=question.prompt_private)
        prepared = prepare_emlis(request)
        receipt = receive_candidate(prepared, request_id=prepared.request_id,
            raw_output=json.dumps(invalid, ensure_ascii=False), finish_reason="stop")
        self.assertEqual(receipt.status, "INVALID_EVIDENCE")

    def test_plus_and_premium_history_keep_original_and_answer_sources_separate(self):
        past_request, _ = native_answer_request("prep-past")
        history = OwnedHistorySourceV1(past_request, "2026-10-21T07:30:00Z",
                                       ("prep-past", "source-version", 1))
        current = emlis_request(original("prep-current"))
        for capability, tier in (("Q3_PLUS", "plus"), ("Q3_PREMIUM", "premium")):
            request = replace(current, emlis_thread=replace(current.emlis_thread,
                capability_snapshot=capability, admitted_history=(history,)))
            with self.subTest(capability=capability):
                payload = prepare_emlis(request).payload()
                self.assertEqual(payload["tier"], tier)
                self.assertEqual([row["role"] for row in payload["sources"]],
                    ["ORIGINAL_INPUT", "HISTORY_ORIGINAL_INPUT", "HISTORY_SUPPLEMENTAL_ANSWER"])
                self.assertEqual(payload["sources"][1]["original"],
                                 past_request.current_input_bundle.raw_current_input)
                self.assertEqual(payload["sources"][2]["text_fields"],
                    {"answer_text_private": past_request.emlis_thread.answers[0].answer_text_private})
                group = payload["control"]["history_groups"][0]
                self.assertEqual(group["source_guard"], list(history.source_guard))
                self.assertEqual(group["source_ids"], ["prep-past", "prep-past-answer"])
                self.assertNotEqual(payload["sources"][0]["envelope_id"],
                                    payload["sources"][1]["envelope_id"])

    def test_free_cannot_include_even_a_native_owned_history_source(self):
        past = emlis_request(original("prep-past"))
        history = OwnedHistorySourceV1(past, "2026-10-20T07:30:00Z",
                                       ("prep-past", "source-version", 1))
        current = emlis_request()
        request = replace(current, emlis_thread=replace(current.emlis_thread,
            admitted_history=(history,)))
        with self.assertRaises(ValueError):
            prepare_emlis(request)

    def test_piece_preserves_incomplete_raw_text_without_finite_meaning_admission(self):
        raw = original("prep-piece", memo="まだ言葉にできないけれど")
        source = piece_source(raw)
        payload = prepare_piece(source, expected_owner_id=OWNER, tier="free").payload()
        self.assertEqual(payload["sources"][0]["original"], raw)
        self.assertEqual(payload["sources"][0]["text_fields"]["memo"], raw["memo"])
        self.assertEqual(payload["control"]["original_text_view"], source.original_text)
        self.assertEqual(payload["core"], "piece")
        self.assertTrue(payload["task"])

    def test_piece_rejects_owner_version_view_and_generated_source(self):
        source = piece_source()
        changes = ({"owner_id": "other-owner"}, {"source_version": "other-version"},
                   {"original_text": "generated replacement"},
                   {"source_role": "generated_observation"},
                   {"source_stage": "refined_observation"})
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                prepare_piece(replace(source, **change), expected_owner_id=OWNER, tier="free")

    def test_analysis_preserves_period_and_excludes_exact_end_record(self):
        inside = original("prep-inside")
        end = original("prep-at-end", created_at="2026-10-22T00:00:00+09:00")
        payload = prepare_analysis(analysis_request(analysis_record(inside),
            analysis_record(end)), tier="plus").payload()
        self.assertEqual([source["source_id"] for source in payload["sources"]], [inside["id"]])
        self.assertEqual(payload["sources"][0]["original"], inside)
        self.assertEqual(payload["period"], {"start": "2026-10-20T15:00:00+00:00",
                                             "end_exclusive": "2026-10-21T15:00:00+00:00"})
        self.assertEqual({row["inclusion_status"] for row in payload["control"]["members"]},
                         {"INCLUDED", "EXCLUDED"})
        self.assertTrue(payload["task"])

    def test_analysis_keeps_supplement_separate_and_unknown_record_time(self):
        raw = original("prep-analysis")
        text = "先ほどの説明を訂正します。"
        supplement = AnalysisSupplement("prep-answer", OWNER, raw["id"], commitment(raw),
            text, commitment(text))
        payload = prepare_analysis(analysis_request(analysis_record(raw,
            supplements=(supplement,))), tier="plus").payload()
        source = payload["sources"][1]
        self.assertEqual(source["role"], "SUPPLEMENTAL_ANSWER")
        self.assertEqual(source["text_fields"], {"answer_text_private": text})
        self.assertEqual(source["parent_record_id"], raw["id"])
        self.assertIsNone(source["recorded_at"])

    def test_analysis_retains_native_owner_version_and_supplement_limit_rejections(self):
        raw = original("prep-analysis")
        record = analysis_record(raw)
        text = "本人の補足です。"
        answer = AnalysisSupplement("answer-1", OWNER, raw["id"], commitment(raw),
            text, commitment(text))
        bad_records = (replace(record, owner_scope="someone-else"),
                       replace(record, saved_record_version="changed"),
                       replace(record, supplements=(answer, replace(answer, source_id="answer-2"))))
        for bad in bad_records:
            with self.subTest(record=bad), self.assertRaises(ValueError):
                prepare_analysis(analysis_request(bad), tier="plus")


class CandidateReceiptTests(unittest.TestCase):
    def setUp(self):
        self.request = prepare_emlis(emlis_request())

    def receive(self, value, **changes):
        args = dict(request_id=self.request.request_id,
                    raw_output=json.dumps(value, ensure_ascii=False), finish_reason="stop")
        args.update(changes)
        return receive_candidate(self.request, **args)

    def test_located_candidate_is_retained_but_never_adopted(self):
        candidate = candidate_for(self.request)
        receipt = self.receive(candidate)
        self.assertEqual(receipt.status, "CANDIDATE_UNREVIEWED")
        self.assertEqual(json.loads(receipt.candidate_json), candidate)
        self.assertEqual(receipt.adoption_state, "NOT_ADOPTED")
        metadata = json.loads(receipt.metadata_json)
        for field in ("provider", "model", "revision", "usage", "elapsed_seconds"):
            self.assertIsNone(metadata[field])
        self.assertEqual(metadata["evidence_check"], "LOCATION_ONLY_NOT_SEMANTIC_ADMISSION")

    def test_request_mismatch_and_forged_snapshot_identity_are_rejected(self):
        args = dict(raw_output="{}", finish_reason="stop")
        with self.assertRaises(ValueError):
            receive_candidate(self.request, request_id="another-request", **args)
        forged = replace(self.request, private_json=self.request.private_json + " ")
        with self.assertRaises(ValueError):
            receive_candidate(forged, request_id=forged.request_id, **args)

    def test_empty_invalid_format_and_unknown_finish_remain_distinct(self):
        cases = (("", "stop", "EMPTY"), (None, "stop", "EMPTY"),
                 ("not json", "stop", "INVALID_FORMAT"),
                 ('{"candidate":{},"evidence":[]}', "stop", "INVALID_FORMAT"),
                 ("{}", None, "UNKNOWN_FINISH"))
        for raw, finish, expected in cases:
            with self.subTest(raw=raw, finish=finish):
                receipt = self.receive({}, raw_output=raw, finish_reason=finish)
                self.assertEqual(receipt.status, expected)
                self.assertEqual(receipt.raw_output, raw)
                self.assertEqual(receipt.adoption_state, "NOT_ADOPTED")

    def test_timeout_token_limit_and_provider_error_dominate_parse_success(self):
        for finish, expected in (("timeout", "TIMEOUT"), ("length", "TOKEN_LIMIT"),
                                 ("error", "PROVIDER_ERROR")):
            with self.subTest(finish=finish):
                receipt = self.receive(candidate_for(self.request), finish_reason=finish)
                self.assertEqual(receipt.status, expected)
                self.assertIsNotNone(receipt.candidate_json)
                self.assertEqual(receipt.adoption_state, "NOT_ADOPTED")

    def test_wrong_source_field_offsets_and_quote_are_invalid_evidence(self):
        changes = ({"source_id": "generated-artifact"}, {"field_path": "reception"},
                   {"start": -1}, {"end": 10000}, {"start": True},
                   {"quote": "本人の原文にない意味"})
        for change in changes:
            candidate = candidate_for(self.request)
            candidate["evidence"][0].update(change)
            with self.subTest(change=change):
                receipt = self.receive(candidate)
                self.assertEqual(receipt.status, "INVALID_EVIDENCE")
                self.assertEqual(receipt.adoption_state, "NOT_ADOPTED")

    def test_unicode_scalar_quote_can_be_located_without_rewriting_original(self):
        prepared = prepare_emlis(emlis_request(original(memo="今日は😊で嬉しかった。")))
        candidate = candidate_for(prepared, start=3, end=4)
        self.assertEqual(candidate["evidence"][0]["quote"], "😊")
        receipt = receive_candidate(prepared, request_id=prepared.request_id,
            raw_output=json.dumps(candidate, ensure_ascii=False), finish_reason="stop")
        self.assertEqual(receipt.status, "CANDIDATE_UNREVIEWED")

    def test_duplicate_keys_nonfinite_values_and_numeric_overflow_preserve_raw_failure(self):
        raws = ('{"candidate":{"x":1,"x":2},"evidence":[]}',
                '{"candidate":{"x":NaN},"evidence":[]}',
                '{"candidate":{"x":1e309},"evidence":[]}',
                json.dumps(candidate_for(self.request)).replace('"meaning":', '"n":1e309,"meaning":'))
        for raw in raws:
            with self.subTest(raw=raw):
                receipt = self.receive({}, raw_output=raw)
                self.assertEqual(receipt.status, "INVALID_FORMAT")
                self.assertEqual(receipt.raw_output, raw)

    def test_reported_metadata_is_kept_and_invalid_usage_is_rejected(self):
        usage = {"input_tokens": 12, "output_tokens": 8, "cached_tokens": None}
        receipt = self.receive(candidate_for(self.request), provider="stub", model="fixed",
                               usage=usage, elapsed_seconds=0.25)
        metadata = json.loads(receipt.metadata_json)
        self.assertEqual(metadata["usage"], usage)
        self.assertEqual(metadata["elapsed_seconds"], 0.25)
        for changes in ({"usage": {"input_tokens": True}},
                        {"usage": {"output_tokens": -1}},
                        {"elapsed_seconds": float("inf")}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.receive(candidate_for(self.request), **changes)


if __name__ == "__main__":
    unittest.main()
