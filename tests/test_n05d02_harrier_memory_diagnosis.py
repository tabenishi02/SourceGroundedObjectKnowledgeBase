import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "harrier_diagnosis",
    Path(__file__).resolve().parents[1] / "benchmark/tools/n05d02_harrier_memory_diagnosis.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_prefixes_preserve_whole_original_lines_and_choose_largest():
    text = "".join(f"line-{i}\n" for i in range(200))

    def counts(value):
        return len(value.splitlines()) * 100

    result = MODULE.prefixes(text, counts)
    for target, (prefix, tokens) in result.items():
        assert text.startswith(prefix) and prefix.endswith("\n")
        assert tokens <= target < tokens + 100


def test_prefix_selection_does_not_assume_token_counts_are_monotonic():
    text = "first\nsecond\nthird\n"
    counts = {"first\n": 2000, "first\nsecond\n": 3000, text: 2040}
    assert MODULE.prefixes(text, counts.__getitem__)[2048] == (text, 2040)


def test_missing_complete_line_prefix_is_blocked():
    with pytest.raises(ValueError):
        MODULE.prefixes("very long single line", lambda _: 20000)


def test_high_shared_memory_alone_is_not_nonviable():
    trials = [{"status": "PASS", "full": i >= 5, "peak_shared": 40 * 1024**3} for i in range(8)]
    assert MODULE.verdict(trials, True) == "VIABLE_FOR_FORMAL_RERUN"


@pytest.mark.parametrize("count", [0, 1, 2])
def test_fewer_than_three_full_trials_cannot_pass(count):
    assert MODULE.verdict([{"status": "PASS", "full": True}] * count, True) == "BLOCKED"


def test_resource_failure_cannot_be_hidden_by_successful_trials():
    trials = [{"status": "PASS", "full": True}] * 3 + [{"resource_failure": True}]
    assert MODULE.verdict(trials, True) == "NOT_VIABLE_REQUIRES_DESIGN_REMEDIATION"


def test_missing_monitoring_or_changed_source_cannot_pass():
    trials = [{"status": "PASS", "full": True}] * 3
    assert MODULE.verdict(trials, False) == "BLOCKED"
    assert MODULE.verdict(trials, True, source_unchanged=False) == "BLOCKED"
    trials[0] = {"status": "BLOCKED", "full": True}
    assert MODULE.verdict(trials, True) == "BLOCKED"


@pytest.mark.parametrize("mismatch", [False, True])
def test_preprocessing_verifies_token_ids_not_only_length(mismatch):
    from types import SimpleNamespace

    class Tokens:
        shape = [1, 2]

        def __getitem__(self, index):
            return self

        def tolist(self):
            return [1, 9] if mismatch else [1, 2]

    encoder = SimpleNamespace(
        default_prompt_name=None,
        preprocess=lambda texts: {"input_ids": Tokens()},
        tokenizer=lambda *args, **kwargs: {"input_ids": [1, 2]},
    )
    provider = SimpleNamespace(_encoder=encoder, document_instruction="")
    if mismatch:
        with pytest.raises(ValueError):
            MODULE.verify_preprocessed_input(provider, "original", 2)
    else:
        assert MODULE.verify_preprocessed_input(provider, "original", 2)["raw_token_ids_equal"]
