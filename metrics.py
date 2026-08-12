"""Métricas de complexidade: McCabe/Radon (cc, mi, loc) e complexidade
cognitiva (Campbell, 2018) via o pacote `cognitive-complexity`."""
import ast

from radon.complexity import cc_visit
from radon.metrics import mi_visit
from radon.raw import analyze as raw_analyze

try:
    from cognitive_complexity.api import get_cognitive_complexity
    _HAS_COGNITIVE = True
except ImportError:
    _HAS_COGNITIVE = False


def _compute_cognitive(code: str):
    if not _HAS_COGNITIVE:
        return None
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None
    total = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            total += get_cognitive_complexity(node)
    return total


def compute_metrics(code: str) -> dict:
    result = {"cc": None, "mi": None, "loc": None, "cognitive": None}
    try:
        blocks = cc_visit(code)
        result["cc"] = sum(b.complexity for b in blocks) if blocks else 1
    except Exception:
        pass
    try:
        result["mi"] = mi_visit(code, multi=True)
    except Exception:
        pass
    try:
        result["loc"] = raw_analyze(code).loc
    except Exception:
        pass
    result["cognitive"] = _compute_cognitive(code)
    return result
