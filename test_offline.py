"""Teste offline do pipeline de métricas + análise, sem chamar nenhuma API.
Reaproveita os 8 arquivos do estudo piloto (Seção 4 do paper) para validar
que metrics.py e analyze.py funcionam de ponta a ponta antes de gastar
créditos de API de verdade.

Rode com: python3 test_offline.py
"""
import glob
import os

import pandas as pd

from metrics import compute_metrics

PILOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pilot_data")


def main():
    # No piloto manual (Seção 4 do paper), só uma combinação falhou nos
    # testes: p3_is_palindrome na condição minimal (não normalizava
    # caixa/espaços). Registrado aqui à mão porque este script só recalcula
    # métricas estáticas a partir dos arquivos — não roda o harness de teste.
    KNOWN_FAILURES = {("p3_is_palindrome", "minimal")}

    rows = []
    for condition in ["baseline", "minimal"]:
        for filepath in sorted(glob.glob(os.path.join(PILOT_DIR, condition, "*.py"))):
            task_id = os.path.basename(filepath).replace(".py", "")
            with open(filepath) as f:
                code = f.read()
            m = compute_metrics(code)
            passed = (task_id, condition) not in KNOWN_FAILURES
            rows.append({
                "task_id": task_id, "model": "pilot_manual", "condition": condition,
                "run_id": 1, "passed": passed, **m,
            })

    df = pd.DataFrame(rows)
    df.to_csv("test_offline_results.csv", index=False)
    print(df.to_string(index=False))

    from analyze import compare
    print("\n=== Comparação (estatística apenas descritiva, n pequeno) ===")
    for metric in ["cc", "mi", "loc", "cognitive"]:
        res = compare(df, "pilot_manual", metric=metric)
        print(f"{metric}: baseline={res['baseline_mean']:.2f}  minimal={res['minimal_mean']:.2f}  "
              f"p={res['p_value']:.4f}  A12={res['A12']:.3f}  (n={res['n']})")

    print("\n=== Mesma comparação, só pares onde as duas condições passaram ===")
    print("(deve excluir p3_is_palindrome, que falhou na condição minimal)")
    for metric in ["cc", "loc"]:
        res = compare(df, "pilot_manual", metric=metric, correct_only=True)
        print(f"{metric}: baseline={res['baseline_mean']:.2f}  minimal={res['minimal_mean']:.2f}  "
              f"n={res['n']} tarefas ({res['n_tasks_excluded']} excluída(s))")


if __name__ == "__main__":
    main()
