"""Provider-independent failure classification for bounded extraction."""


class OutputBudgetExceeded(ValueError):
    pass


def is_output_budget(error):
    return isinstance(error, OutputBudgetExceeded) or str(error) in {
        "LLM output reached token budget",
        "LLM output truncated; increase CPC_LLM_MAX_TOKENS",
    }
