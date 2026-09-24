"""Gera (e desta vez SALVA o código) os pares baseline/minimal para um
conjunto fixo de task_id do HumanEval+, e já escreve direto no formato
esperado por data/pairs.json do survey (llm-code-complexity-survey).

Criado para o subconjunto curado do survey de especialistas: o
run_pipeline.py original só persiste métricas (results.csv), não o texto
do código gerado, então os 90 pares reportados no artigo não podem ser
recuperados — este script gera os task_id escolhidos de novo, salvando o
código desta vez.

Uso:
    export ANTHROPIC_API_KEY=...
    python3 generate_curated.py --out pairs_curated.json
"""
import argparse
import json

from config import PRICING_PER_MTOK_USD
from evaluate import run_test_plus
from fetch_problems import fetch_humaneval_plus
from generate_solutions import generate
from metrics import compute_metrics

DEFAULT_TASK_IDS = [
    # discordantes (prioridade máxima — só um lado passou na coleta original)
    "HumanEval/127",
    "HumanEval/96",
    "HumanEval/125",
    # maior redução de CC (ambos passaram)
    "HumanEval/126",
    "HumanEval/31",
    "HumanEval/61",
    "HumanEval/130",
    "HumanEval/18",
    "HumanEval/19",
    # neutros / Δ CC pequeno (ambos passaram)
    "HumanEval/104",
    "HumanEval/42",
    "HumanEval/145",
]


def estimate_cost(tokens_in: int, tokens_out: int) -> float:
    rates = PRICING_PER_MTOK_USD["claude"]
    return (tokens_in / 1_000_000) * rates["input"] + (tokens_out / 1_000_000) * rates["output"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task-ids", nargs="+", default=DEFAULT_TASK_IDS)
    ap.add_argument("--out", default="pairs_curated.json")
    args = ap.parse_args()

    all_problems = fetch_humaneval_plus()
    by_id = {p["task_id"]: p for p in all_problems}

    missing = [t for t in args.task_ids if t not in by_id]
    if missing:
        raise SystemExit(f"task_id não encontrados no HumanEval+: {missing}")

    pairs = []
    running_cost = 0.0
    for order, task_id in enumerate(args.task_ids, start=1):
        problem = by_id[task_id]
        row = {"task_id": task_id, "display_order": order, "problem_statement": problem["prompt"]}
        for condition, key in (("baseline", "code_baseline"), ("minimal", "code_minimal")):
            gen = generate("claude", problem["prompt"], condition)
            test_result = run_test_plus(problem, gen["code"])
            m = compute_metrics(gen["code"])
            cost = estimate_cost(gen["tokens_in"], gen["tokens_out"])
            running_cost += cost
            row[key] = gen["code"]
            row[f"_{condition}_meta"] = {
                "passed": test_result["passed"],
                "cc": m["cc"],
                "loc": m["loc"],
                "cost_usd": round(cost, 6),
            }
            print(
                f"{task_id:15s} {condition:9s} passed={test_result['passed']!s:5s} "
                f"cc={m['cc']} cost=${cost:.5f} (acum. ${running_cost:.4f})"
            )
        pairs.append(row)

    with open(args.out, "w") as f:
        json.dump(pairs, f, indent=2)
    print(f"\n{len(pairs)} pares salvos em {args.out}. Custo estimado total: ${running_cost:.4f}")
    print(
        "Os campos _baseline_meta/_minimal_meta são só para conferência manual "
        "(pass/fail, CC) — remova-os (ou ignore) ao copiar para "
        "data/pairs.json do survey, que só usa task_id/display_order/"
        "problem_statement/code_baseline/code_minimal."
    )


if __name__ == "__main__":
    main()
