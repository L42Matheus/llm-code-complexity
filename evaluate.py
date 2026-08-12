"""Executa o código gerado contra os testes do HumanEval, isolado em subprocesso.

Implementação própria do mesmo padrão usado pelo harness oficial do
HumanEval (Chen et al., 2021): concatena a solução com a função `check`
do próprio benchmark e roda `check(entry_point)` em um processo separado,
com timeout, para conter loops infinitos ou código malicioso acidental.
"""
import os
import subprocess
import sys
import tempfile

from config import EXEC_TIMEOUT_SECONDS
from fetch_problems import get_import_preamble

_HARNESS_TEMPLATE = """{preamble}

{completion}

{test}

check({entry_point})
"""


def run_test(problem: dict, completion: str, timeout: int = EXEC_TIMEOUT_SECONDS) -> dict:
    program = _HARNESS_TEMPLATE.format(
        preamble=get_import_preamble(problem["prompt"]),
        completion=completion,
        test=problem["test"],
        entry_point=problem["entry_point"],
    )
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(program)
        path = f.name
    try:
        result = subprocess.run(
            [sys.executable, path], capture_output=True, text=True, timeout=timeout
        )
        passed = result.returncode == 0
        return {"passed": passed, "error": None if passed else result.stderr[-1500:]}
    except subprocess.TimeoutExpired:
        return {"passed": False, "error": "timeout"}
    finally:
        os.unlink(path)


_HARNESS_PLUS_TEMPLATE = """{preamble}

{completion}

{canonical_renamed}

import math

def __values_equal__(a, b):
    try:
        if isinstance(a, float) or isinstance(b, float):
            return math.isclose(a, b, rel_tol=1e-6, abs_tol={atol!r} or 1e-6)
        return a == b
    except Exception:
        return False

_inputs = {inputs!r}
_failures = 0
_total = len(_inputs)
for _args in _inputs:
    try:
        _expected = __canonical_{entry_point}__(*_args)
    except Exception:
        _total -= 1
        continue
    try:
        _actual = {entry_point}(*_args)
    except Exception:
        _failures += 1
        continue
    if not __values_equal__(_actual, _expected):
        _failures += 1

if _failures > 0:
    raise AssertionError(f"{{_failures}}/{{_total}} EvalPlus test cases failed")
"""


def run_test_plus(problem: dict, completion: str, timeout: int = EXEC_TIMEOUT_SECONDS) -> dict:
    """Testa contra a suíte expandida do HumanEval+ (base_input + plus_input),
    comparando a saída do candidato com a da canonical_solution do próprio
    benchmark, em vez de usar apenas a função `check` original. Requer que
    `problem` venha de fetch_problems.fetch_humaneval_plus().

    Reimplementação própria e simplificada da lógica de checagem do EvalPlus
    (Liu et al., 2023): compara igualdade direta, com tolerância numérica
    para floats. Não reproduz o tratamento completo de estruturas aninhadas
    do checker oficial — suficiente para os fins deste piloto, mas deve ser
    revisado antes de uso em publicação final.
    """
    entry_point = problem["entry_point"]
    canonical_full = problem["prompt"] + problem["canonical_solution"]
    canonical_renamed = canonical_full.replace(
        f"def {entry_point}(", f"def __canonical_{entry_point}__(", 1
    )
    inputs = problem["base_input"] + problem["plus_input"]

    program = _HARNESS_PLUS_TEMPLATE.format(
        preamble=get_import_preamble(problem["prompt"]),
        completion=completion,
        canonical_renamed=canonical_renamed,
        entry_point=entry_point,
        inputs=inputs,
        atol=problem.get("atol", 0),
    )
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(program)
        path = f.name
    try:
        result = subprocess.run(
            [sys.executable, path], capture_output=True, text=True, timeout=timeout
        )
        passed = result.returncode == 0
        return {"passed": passed, "error": None if passed else result.stderr[-1500:]}
    except subprocess.TimeoutExpired:
        return {"passed": False, "error": "timeout"}
    finally:
        os.unlink(path)
