"""Templates de prompt para as duas condições do experimento (Seção 3.1 do paper)."""

_INSTRUCTION = (
    "Complete the following Python function. Return ONLY the full function "
    "code inside a single ```python code block, with no explanation before "
    "or after."
)

_MINIMAL_INSTRUCTION = (
    "Write the simplest, most direct implementation that satisfies the "
    "specification below. Do not add exception handling, type validation, "
    "or checks for edge cases that are not explicitly mentioned in the "
    "docstring. Include only the logic strictly necessary to solve the "
    "described problem."
)


def build_prompt(task_prompt: str, condition: str) -> str:
    if condition == "baseline":
        return f"{_INSTRUCTION}\n\n{task_prompt}"
    if condition == "minimal":
        return f"{_INSTRUCTION}\n\n{_MINIMAL_INSTRUCTION}\n\n{task_prompt}"
    raise ValueError(f"Condição desconhecida: {condition!r} (use 'baseline' ou 'minimal')")
