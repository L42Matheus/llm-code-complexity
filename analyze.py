"""Comparação estatística baseline vs. minimal (Seção 3.5 do paper).

O pareamento é feito no nível de execução (task_id + run_id), não só de
tarefa: baseline e minimal de execuções diferentes nunca são comparados
entre si, mesmo quando agregados depois. Isso evita o viés de seleção de
"melhor run de cada lado" ao filtrar por corretude.
"""
import pandas as pd
from scipy.stats import wilcoxon


def vda(treatment, control) -> float:
    """Vargha-Delaney A12: probabilidade de um valor de 'treatment' ser
    maior que um valor de 'control', amostrado aleatoriamente. A12 < 0.5
    indica que 'treatment' tende a ser menor que 'control'
    (Vargha e Delaney, 2000)."""
    treatment = list(treatment)
    control = list(control)
    m, n = len(treatment), len(control)
    ranks = pd.Series(treatment + control).rank().values
    r_treatment = ranks[:m].sum()
    return (r_treatment / m - (m + 1) / 2) / n


def _paired_by_run(df: pd.DataFrame, model: str, metric: str, correct_only: bool):
    """Faz o merge baseline x minimal no nível de (task_id, run_id) —
    a mesma execução em ambas as condições — e só então agrega por
    tarefa. Retorna (pivot_por_tarefa, n_execucoes_validas, n_tarefas_sem_par)."""
    sub = df[df["model"] == model]
    cols = ["task_id", "run_id", "passed", metric]
    baseline = sub[sub["condition"] == "baseline"][cols]
    minimal = sub[sub["condition"] == "minimal"][cols]

    merged = baseline.merge(
        minimal, on=["task_id", "run_id"], suffixes=("_baseline", "_minimal")
    )
    all_task_ids = set(sub["task_id"].unique())

    if correct_only:
        merged = merged[merged["passed_baseline"] & merged["passed_minimal"]]

    n_valid_runs = len(merged)
    tasks_with_pair = set(merged["task_id"].unique())
    n_tasks_no_pair = len(all_task_ids - tasks_with_pair)

    # agrega por tarefa: MEDIANA entre as execuções válidas (mais robusta a
    # uma execução atípica do que a média, dado n pequeno de repetições)
    agg = (
        merged.groupby("task_id")[[f"{metric}_baseline", f"{metric}_minimal"]]
        .median()
        .dropna()
        .rename(columns={f"{metric}_baseline": "baseline", f"{metric}_minimal": "minimal"})
    )
    return agg, n_valid_runs, n_tasks_no_pair


def compare(df: pd.DataFrame, model: str, metric: str = "cc", correct_only: bool = False) -> dict:
    """Compara baseline vs. minimal para um modelo e uma métrica.

    correct_only=True restringe aos PARES DE EXECUÇÃO (mesma task_id +
    run_id) em que a solução passou nos testes nas DUAS condições — não
    apenas "alguma execução passou de cada lado" (isso seria viés de
    seleção: ver discussão de pareamento). Tarefas sem nenhuma execução
    em que ambas as condições passaram são excluídas e contadas em
    'n_tasks_excluded'.
    """
    pivot, n_valid_runs, n_tasks_excluded = _paired_by_run(df, model, metric, correct_only)

    out = {
        "model": model,
        "metric": metric,
        "correct_only": correct_only,
        "n": len(pivot),
        "n_valid_runs": n_valid_runs,
        "n_tasks_excluded": n_tasks_excluded,
        "baseline_mean": pivot["baseline"].mean() if len(pivot) else float("nan"),
        "minimal_mean": pivot["minimal"].mean() if len(pivot) else float("nan"),
    }
    if len(pivot) >= 2 and not (pivot["minimal"] == pivot["baseline"]).all():
        try:
            stat, p = wilcoxon(pivot["minimal"], pivot["baseline"])
            out["p_value"] = p
        except ValueError:
            out["p_value"] = float("nan")
        out["A12"] = vda(pivot["minimal"], pivot["baseline"])
    else:
        out["p_value"] = float("nan")
        out["A12"] = float("nan")
    return out


def pass_rate_by_task(df: pd.DataFrame, model: str) -> pd.DataFrame:
    """Taxa de aprovação por tarefa x condição, média entre runs — útil
    para checar se a corretude é estável ou varia entre execuções."""
    sub = df[df["model"] == model]
    return sub.groupby(["task_id", "condition"])["passed"].mean().unstack()
