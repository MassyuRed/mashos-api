"""CPU-only assistant mask and refusal boundaries; never load/forward a model."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


spec = importlib.util.spec_from_file_location('piece_adapter_training',
    Path(__file__).parents[1] / 'tools/training/train_piece_model_adapter.py')
trainer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trainer)


def row(number=0):
    material = dict(core='piece', task='PIECE_MODEL_BODY', control={'field_slots': {
        'memo_0': {'literal': '独立した架空原文' + str(number) + '。'}}})
    return dict(id='SYNTHETIC' + str(number), messages=[
        dict(role='system', content='合成の指示'),
        dict(role='user', content=json.dumps(material, ensure_ascii=False))],
        assistant_target=json.dumps({'field_blocks': {'memo_0': '独立した架空編集文。'}}, ensure_ascii=False))


class Tokenizer:
    def __init__(self, *, prefix_changed=False, eos_changed=False, tail=None):
        self.prefix_changed, self.eos_changed = prefix_changed, eos_changed
        self.tail = tail or [20, 21, 22, 90, 10]
        self.calls = []
    def apply_chat_template(self, messages, **kwargs):
        self.calls.append((deepcopy(messages), kwargs))
        prefix = [1, 2, 3]
        if messages[-1]['role'] != 'assistant':
            return prefix
        self.target = messages[-1]['content']
        return ([99] + prefix[1:] if self.prefix_changed else prefix) + self.tail
    def decode(self, tokens, **kwargs):
        assert tokens == self.tail
        assert kwargs == dict(skip_special_tokens=False, clean_up_tokenization_spaces=False)
        return self.target + ('<|im_end|>' if self.eos_changed else '<|im_end|>\n')


def test_entire_assistant_and_eos_are_supervised_after_fully_masked_prompt():
    tokenizer, selected = Tokenizer(), row()
    before = deepcopy(selected)
    encoded = trainer.encode_training(tokenizer, selected)
    assert encoded['input_ids'] == [1, 2, 3, 20, 21, 22, 90, 10]
    assert encoded['labels'] == [-100, -100, -100, 20, 21, 22, 90, 10]
    # First output is predicted at the final prompt logit; every target and
    # the EOS/newline remain aligned, with exactly one unused final logit.
    assert encoded['loss_start'] == 2 and encoded['logits_positions'] == 6
    assert encoded['labels'][encoded['loss_start'] + 1:] == [20, 21, 22, 90, 10]
    assert len(encoded['input_ids'][-encoded['logits_positions']:-1]) == 5
    assert encoded['prompt_tokens'] == 3 and encoded['target_tokens'] == 5
    assert selected == before
    assert all(call[1]['truncation'] is False and call[1]['enable_thinking'] is False for call in tokenizer.calls)
    assert tokenizer.calls[0][1]['add_generation_prompt'] is True
    assert tokenizer.calls[1][1]['add_generation_prompt'] is False


@pytest.mark.parametrize('tokenizer,error', [(Tokenizer(prefix_changed=True), 'prefix_changed'),
    (Tokenizer(eos_changed=True), 'eos_tail_changed')])
def test_template_or_eos_drift_refuses_instead_of_training_a_partial_target(tokenizer, error):
    with pytest.raises(ValueError, match=error):
        trainer.encode_training(tokenizer, row())


def test_exact_context_boundary_is_allowed_and_overflow_never_truncates():
    assert trainer.encode_training(Tokenizer(), row(), context_tokens=8, output_tokens=5)['target_tokens'] == 5
    with pytest.raises(ValueError, match='context_or_target_exceeded'):
        trainer.encode_training(Tokenizer(), row(), context_tokens=7, output_tokens=5)
    with pytest.raises(ValueError, match='context_or_target_exceeded'):
        trainer.encode_training(Tokenizer(), row(), context_tokens=8, output_tokens=4)


def packet():
    return dict(all_fictional=True, rows=[row(number) for number in range(24)])


def test_exact_24_distinct_source_texts_are_required_without_reading_holdout_targets():
    selected = packet(); before = deepcopy(selected)
    assert trainer.validate_rows(selected) is selected['rows']
    assert selected == before
    duplicate = deepcopy(selected)
    duplicate['rows'][1]['messages'] = deepcopy(duplicate['rows'][0]['messages'])
    with pytest.raises(ValueError, match='source_text_missing_or_duplicate'):
        trainer.validate_rows(duplicate)
    with pytest.raises(ValueError, match='exact_24'):
        trainer.validate_rows({**selected, 'rows': selected['rows'][:-1]})
    with pytest.raises(ValueError, match='fictional_data_required'):
        trainer.validate_rows({**selected, 'all_fictional': False})


@pytest.mark.parametrize('count', (36, 48))
def test_complement_rows_are_explicit_and_keep_default24_and_all_teacher_validation(count):
    selected = dict(all_fictional=True, rows=[row(number) for number in range(count)])
    before = deepcopy(selected)
    with pytest.raises(ValueError, match='exact_24'):
        trainer.validate_rows(selected)
    assert trainer.validate_rows(selected, expected_rows=count) is selected['rows']
    assert selected == before
    with pytest.raises(ValueError, match=f'exact_{count}'):
        trainer.validate_rows(packet(), expected_rows=count)
    duplicate = deepcopy(selected)
    duplicate['rows'][-1]['messages'] = deepcopy(duplicate['rows'][0]['messages'])
    with pytest.raises(ValueError, match='source_text_missing_or_duplicate'):
        trainer.validate_rows(duplicate, expected_rows=count)
    bad_target = deepcopy(selected)
    bad_target['rows'][-1]['assistant_target'] = '{"field_blocks":{"memo_1":"wrong slot"}}'
    with pytest.raises(ValueError, match='assistant_target_shape_invalid'):
        trainer.validate_rows(bad_target, expected_rows=count)


@pytest.mark.parametrize('count,updates', ((36, 72), (48, 96)))
def test_complement_updates_need_explicit_rows_and_still_have_a_fixed_two_pass_limit(tmp_path, count, updates):
    options = dict(output=tmp_path / 'new', max_seconds=480, updates=updates,
                   learning_rate=1e-4, seed=20261109)
    with pytest.raises(ValueError, match='updates_invalid'):
        trainer.validate_settings(**options)
    trainer.validate_settings(**options, training_rows=count)
    with pytest.raises(ValueError, match='updates_invalid'):
        trainer.validate_settings(**{**options, 'updates': updates + 1}, training_rows=count)
    with pytest.raises(ValueError, match='max_seconds_invalid'):
        trainer.validate_settings(**{**options, 'max_seconds': 481}, training_rows=count)
    for invalid_count in (True, 25, 37, 49):
        with pytest.raises(ValueError, match='training_rows_invalid'):
            trainer.validate_settings(**options, training_rows=invalid_count)


def test_cli_preserves_default24_and_requires_an_explicit_supported_row_count(monkeypatch, tmp_path):
    captured = []
    monkeypatch.setattr(trainer, 'run', captured.append)
    base = ['trainer', '--data', str(tmp_path / 'data.json'), '--scope-config',
            str(tmp_path / 'adapter_config.json'), '--output', str(tmp_path / 'output')]
    for count in (None, 36, 48):
        monkeypatch.setattr(sys, 'argv', base + ([] if count is None else ['--training-rows', str(count)]))
        trainer.main()
        assert captured[-1].training_rows == (24 if count is None else count)
        assert captured[-1].updates == 48 and captured[-1].max_seconds == 480
    monkeypatch.setattr(sys, 'argv', base + ['--training-rows', '49'])
    with pytest.raises(SystemExit):
        trainer.main()
    assert len(captured) == 3


@pytest.mark.parametrize('target', [
    '{"field_blocks":{"memo_0":"a","memo_0":"b"}}',
    '{"field_blocks":{"memo_0":"a"},"extra":1}',
    '{"body_blocks":["a"]}', '{"field_blocks":{"memo_1":"a"}}',
    '{"field_blocks":{"memo_0":""}}', '{"field_blocks":{"memo_0":"a\\nb"}}',
])
def test_bad_teacher_target_is_rejected_before_model_loading(target):
    selected = packet(); selected['rows'][0]['assistant_target'] = target
    with pytest.raises(ValueError):
        trainer.validate_rows(selected)


def scope():
    return dict(peft_type='LORA', task_type='CAUSAL_LM', base_model_name_or_path=trainer.MODEL,
        r=8, lora_alpha=16, lora_dropout=0., bias='none', init_lora_weights=True,
        target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj'] + [
            str(layer) + '.mlp.' + projection for layer in range(3, 32, 4)
            for projection in ('gate_proj', 'up_proj', 'down_proj')])


@pytest.mark.parametrize('change', [dict(r=16), dict(lora_dropout=.05), dict(init_lora_weights=False),
    dict(modules_to_save=['lm_head']), dict(rank_pattern={'q_proj': 16}), dict(target_modules=['q_proj'])])
def test_only_the_existing_architectural_scope_can_initialize_a_fresh_adapter(change):
    trainer.validate_scope(scope())
    with pytest.raises(ValueError, match='scope_'):
        trainer.validate_scope({**scope(), **change})


def test_existing_partial_or_complete_output_is_never_resumed(tmp_path):
    options = dict(output=tmp_path / 'new', max_seconds=480, updates=48, learning_rate=1e-4, seed=20261109)
    trainer.validate_settings(**options)
    options['output'].mkdir()
    with pytest.raises(ValueError, match='output_already_exists_no_resume'):
        trainer.validate_settings(**options)


@pytest.mark.parametrize('change', [dict(max_seconds=481), dict(max_seconds=True), dict(updates=49),
    dict(updates=0), dict(learning_rate=float('nan')), dict(learning_rate=0.), dict(learning_rate=1e-3)])
def test_process_and_update_budgets_fail_before_allocating_a_model(tmp_path, change):
    options = dict(output=tmp_path / 'new', max_seconds=480, updates=48, learning_rate=1e-4, seed=20261109)
    with pytest.raises(ValueError):
        trainer.validate_settings(**{**options, **change})


def test_portable_trainer_imports_its_adjacent_server_before_an_older_parent_copy(tmp_path):
    directory = tmp_path / 'portable'; directory.mkdir()
    copied = directory / 'trainer.py'
    copied.write_bytes(Path(trainer.__file__).read_bytes())
    for root, label in ((tmp_path, 'OLD_PARENT'), (directory, 'ADJACENT_PINNED')):
        (root / 'serve_emlis_natural_reply.py').write_text(
            'MODEL=' + repr(label) + '\nREVISION="synthetic"\nPINS={}\ndef piece_output_schema(messages): pass\n')
    result = subprocess.run([sys.executable, '-B', '-c',
        'import runpy,sys;print(runpy.run_path(sys.argv[1],run_name="import_only")["MODEL"])', str(copied)],
        check=True, capture_output=True, text=True)
    assert result.stdout.strip() == 'ADJACENT_PINNED'
