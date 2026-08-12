"""Pipeline principal: gera soluções (com repetições), testa contra o
HumanEval+ e mede complexidade + custo.

Uso:
    export ANTHROPIC_API_KEY=...
    python3 run_pipeline.py --n 20 --runs 5 --models claude
"""
import argparse
import csv

from config import MODELS, PRICING_PER_MTOK_USD
from evaluate import run_test, run_test_plus
from fetch_problems import sample_problems, sample_problems_plus
from generate_solutions import generate
from metrics import compute_metrics


def estimate_cost(model_key: str, tokens_in: int, tokens_out: int) -> float:
    rates = PRICING_PER_MTOK_USD.get(model_key, {"input": 0.0, "output": 0.0})
    return (tokens_in / 1_000_000) * rates["input"] + (tokens_out / 1_000_000) * rates["output"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20, help="quantidade de problemas do HumanEval a amostrar (máx. 164)")
    ap.add_argument("--runs", type=int, default=1, help="repetições por problema x condição x modelo (recomendado 3-10, já que a saída do LLM varia)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--models", nargs="+", default=list(MODELS.keys()), choices=list(MODELS.keys()))
    ap.add_argument("--dataset", default="humaneval_plus", choices=["humaneval", "humaneval_plus"],
                     help="humaneval_plus (padrão, recomendado) usa a suíte expandida do EvalPlus/HumanEval+ "
                          "(Liu et al., 2023) — importante para não confundir 'complexidade desnecessária' "
                          "com solução incompleta que passa só por insuficiência de testes. "
                          "humaneval usa a suíte original, mais rápida mas mais fraca.")
    ap.add_argument("--out", default="results.csv")
    args = ap.parse_args()

    if args.dataset == "humaneval_plus":
        problems = sample_problems_plus(n=args.n, seed=args.seed)
        test_fn = run_test_plus
    else:
        problems = sample_problems(n=args.n, seed=args.seed)
        test_fn = run_test

    total_calls = len(problems) * len(args.models) * 2 * args.runs
    print(f"{len(problems)} problemas ({args.dataset}), {len(args.models)} modelo(s), {args.runs} repetição(ões) "
          f"= {total_calls} chamadas de API.\n")

    rows = []
    running_cost = 0.0
    for problem in problems:
        for model_key in args.models:
            for condition in ["baseline", "minimal"]:
                for run_id in range(1, args.runs + 1):
                    try:
                        gen = generate(model_key, problem["prompt"], condition)
                    except Exception as e:
                        print(f"[ERRO geração] {problem['task_id']} {model_key} {condition} run{run_id}: {e}")
                        continue
                    test_result = test_fn(problem, gen["code"])
                    m = compute_metrics(gen["code"])
                    cost = estimate_cost(model_key, gen["tokens_in"], gen["tokens_out"])
                    running_cost += cost
                    row = {
                        "task_id": problem["task_id"],
                        "model": model_key,
                        "model_full": gen["model_full"],
                        "condition": condition,
                        "run_id": run_id,
                        "passed": test_result["passed"],
                        "cc": m["cc"],
                        "mi": m["mi"],
                        "loc": m["loc"],
                        "cognitive": m["cognitive"],
                        "tokens_in": gen["tokens_in"],
                        "tokens_out": gen["tokens_out"],
                        "latency_s": gen["latency_s"],
                        "cost_usd": round(cost, 6),
                    }
                    rows.append(row)
                    print(f"{problem['task_id']:15s} {model_key:10s} {condition:9s} run{run_id} "
                          f"passed={str(row['passed']):5s} cc={row['cc']} cost=${cost:.5f} "
                          f"(acum. ${running_cost:.4f})")

    if not rows:
        print("Nenhum resultado gerado — confira as chaves de API.")
        return

    with open(args.out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n{len(rows)} linhas salvas em {args.out}. Custo estimado total: ${running_cost:.4f}")
    print("Rode `python3 summarize.py` para ver a comparação estatística.")


if __name__ == "__main__":
    main()
