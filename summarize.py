"""Lê results.csv (gerado por run_pipeline.py) e imprime a comparação
baseline vs. minimal por modelo, com Wilcoxon + A12 — geral e restrita a
soluções corretas em ambas as condições."""
import argparse

import pandas as pd

from analyze import compare


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default="results.csv")
    args = ap.parse_args()

    df = pd.read_csv(args.path)
    n_runs = df.groupby(["task_id", "model", "condition"]).size().max()

    print(f"=== {len(df)} linhas | até {n_runs} repetição(ões) por tarefa/condição ===\n")

    print("=== Taxa de aprovação (média de 'passed', entre runs) ===")
    print(df.groupby(["model", "condition"])["passed"].mean().unstack())

    if "cost_usd" in df.columns:
        print(f"\nCusto total estimado: ${df['cost_usd'].sum():.4f}")
        print(f"Tempo médio por chamada: {df['latency_s'].mean():.2f}s" if "latency_s" in df.columns else "")

    for metric in ["cc", "mi", "loc", "cognitive", "tokens_out"]:
        if metric not in df.columns:
            continue
        print(f"\n=== {metric.upper()} (todas as soluções) ===")
        for model in sorted(df["model"].unique()):
            res = compare(df, model, metric=metric)
            print(f"{model:12s} baseline={res['baseline_mean']:.2f}  minimal={res['minimal_mean']:.2f}  "
                  f"p={res['p_value']:.4f}  A12={res['A12']:.3f}  (n={res['n']})")

        print(f"--- {metric.upper()} (só execuções pareadas em que as duas condições passaram) ---")
        for model in sorted(df["model"].unique()):
            res = compare(df, model, metric=metric, correct_only=True)
            print(f"{model:12s} baseline={res['baseline_mean']:.2f}  minimal={res['minimal_mean']:.2f}  "
                  f"p={res['p_value']:.4f}  A12={res['A12']:.3f}  "
                  f"(n={res['n']} tarefas, {res['n_valid_runs']} execuções válidas, "
                  f"{res['n_tasks_excluded']} tarefas sem par excluídas)")


if __name__ == "__main__":
    main()
