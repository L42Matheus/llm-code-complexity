"""Baixa o benchmark HumanEval (Chen et al., 2021) e amostra um subconjunto."""
import gzip
import json
import os
import random
import urllib.request

HUMANEVAL_URL = "https://raw.githubusercontent.com/openai/human-eval/master/data/HumanEval.jsonl.gz"
CACHE_PATH = os.path.join(os.path.dirname(__file__), "data", "HumanEval.jsonl.gz")


def fetch_humaneval(cache_path: str = CACHE_PATH):
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    if not os.path.exists(cache_path):
        urllib.request.urlretrieve(HUMANEVAL_URL, cache_path)
    problems = []
    with gzip.open(cache_path, "rt") as f:
        for line in f:
            line = line.strip()
            if line:
                problems.append(json.loads(line))
    return problems


def sample_problems(n: int = 20, seed: int = 42):
    problems = fetch_humaneval()
    random.Random(seed).shuffle(problems)
    return problems[:n]


def fetch_humaneval_plus():
    """Baixa o HumanEval+ (EvalPlus, Liu et al., 2023) via o pacote evalplus.
    Cada problema traz, além dos campos do HumanEval original, `base_input`
    (casos originais) e `plus_input` (centenas de casos adicionais gerados
    pelo EvalPlus), usados pelo harness de teste expandido em evaluate.py."""
    from evalplus.data import get_human_eval_plus

    problems_dict = get_human_eval_plus()
    return [problems_dict[tid] for tid in problems_dict]


def sample_problems_plus(n: int = 20, seed: int = 42):
    problems = fetch_humaneval_plus()
    random.Random(seed).shuffle(problems)
    return problems[:n]


def get_import_preamble(task_prompt: str) -> str:
    """Extrai as linhas de import que antecedem a assinatura da função no
    prompt original do HumanEval (ex.: 'from typing import List')."""
    lines = task_prompt.split("\n")
    preamble = []
    for line in lines:
        if line.strip().startswith("def ") or line.strip().startswith("class "):
            break
        preamble.append(line)
    return "\n".join(preamble)


if __name__ == "__main__":
    probs = sample_problems(n=5)
    for p in probs:
        print(p["task_id"], "-", p["entry_point"])
