"""Railway web app for the LLM code-complexity experiment.

The CLI toolkit stays in the repository root. This app imports those modules
and exposes them through a small FastAPI UI.
"""
import csv
import math
import os
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Dict, Literal

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from analyze import compare
from config import MODELS, PRICING_PER_MTOK_USD
from evaluate import run_test, run_test_plus
from fetch_problems import sample_problems, sample_problems_plus
from generate_solutions import generate
from metrics import compute_metrics


APP_DIR = Path(__file__).resolve().parent
RESULTS_DIR = APP_DIR / "web_results"
STATIC_DIR = APP_DIR / "web_static"
AUTH_TOKEN_ENV = "EXPERIMENT_WEB_TOKEN"

app = FastAPI(title="LLM Code Complexity Experiment")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

_jobs: Dict[str, dict] = {}
_jobs_lock = threading.Lock()


class JobRequest(BaseModel):
    model: str = Field(default="claude")
    dataset: Literal["humaneval", "humaneval_plus"] = "humaneval_plus"
    n: int = Field(default=10, ge=1, le=164)
    runs: int = Field(default=1, ge=1, le=10)
    seed: int = 42


def _json_number(value):
    if value is None:
        return None
    try:
        if pd.isna(value) or math.isnan(float(value)):
            return None
    except (TypeError, ValueError):
        return value
    return value


def _estimate_cost(model_key: str, tokens_in: int, tokens_out: int) -> float:
    rates = PRICING_PER_MTOK_USD.get(model_key, {"input": 0.0, "output": 0.0})
    return (tokens_in / 1_000_000) * rates["input"] + (tokens_out / 1_000_000) * rates["output"]


def _configured_models():
    out = []
    for key, cfg in MODELS.items():
        api_key_env = cfg["api_key_env"]
        out.append(
            {
                "key": key,
                "provider": cfg["provider"],
                "model": cfg["model"],
                "api_key_env": api_key_env,
                "configured": bool(os.environ.get(api_key_env)),
            }
        )
    return out


def _build_summary(rows):
    if not rows:
        return None

    df = pd.DataFrame(rows)
    pass_rate_df = df.groupby(["model", "condition"])["passed"].mean().unstack()
    pass_rate = {
        model: {condition: _json_number(value) for condition, value in row.items()}
        for model, row in pass_rate_df.to_dict(orient="index").items()
    }

    comparisons = []
    for metric in ["cc", "mi", "loc", "cognitive", "tokens_out"]:
        if metric not in df.columns:
            continue
        for model in sorted(df["model"].unique()):
            res = compare(df, model, metric=metric, correct_only=True)
            comparisons.append(
                {
                    "metric": metric,
                    "model": model,
                    "baseline_mean": _json_number(res["baseline_mean"]),
                    "minimal_mean": _json_number(res["minimal_mean"]),
                    "p_value": _json_number(res["p_value"]),
                    "A12": _json_number(res["A12"]),
                    "n": int(res["n"]),
                    "n_valid_runs": int(res["n_valid_runs"]),
                    "n_tasks_excluded": int(res["n_tasks_excluded"]),
                }
            )

    return {
        "rows": int(len(df)),
        "tasks": int(df["task_id"].nunique()),
        "calls": int(len(df)),
        "cost_usd": round(float(df["cost_usd"].sum()), 6) if "cost_usd" in df else 0.0,
        "avg_latency_s": round(float(df["latency_s"].mean()), 3) if "latency_s" in df else None,
        "pass_rate": pass_rate,
        "comparisons": comparisons,
    }


def _set_job(job_id: str, **updates):
    with _jobs_lock:
        job = _jobs[job_id]
        job.update(updates)
        job["updated_at"] = time.time()


def _append_event(job_id: str, event: dict):
    with _jobs_lock:
        job = _jobs[job_id]
        job["events"].append(event)
        job["updated_at"] = time.time()


def _append_row(job_id: str, row: dict):
    with _jobs_lock:
        job = _jobs[job_id]
        job["rows"].append(row)
        job["completed_calls"] = len(job["rows"])
        job["running_cost_usd"] = round(job["running_cost_usd"] + row["cost_usd"], 6)
        job["updated_at"] = time.time()


def _write_csv(job_id: str, rows):
    RESULTS_DIR.mkdir(exist_ok=True)
    path = RESULTS_DIR / f"{job_id}.csv"
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return path


def _run_job(job_id: str, req: JobRequest):
    started = time.time()
    try:
        if req.model not in MODELS:
            raise ValueError(f"Modelo desconhecido: {req.model}")
        cfg = MODELS[req.model]
        if not os.environ.get(cfg["api_key_env"]):
            raise RuntimeError(f"Variavel {cfg['api_key_env']} nao configurada no servidor.")

        _set_job(job_id, status="running", started_at=started)
        if req.dataset == "humaneval_plus":
            problems = sample_problems_plus(n=req.n, seed=req.seed)
            test_fn = run_test_plus
        else:
            problems = sample_problems(n=req.n, seed=req.seed)
            test_fn = run_test

        total_calls = len(problems) * 2 * req.runs
        _set_job(job_id, total_calls=total_calls)

        for problem in problems:
            for condition in ["baseline", "minimal"]:
                for run_id in range(1, req.runs + 1):
                    event_base = {
                        "task_id": problem["task_id"],
                        "model": req.model,
                        "condition": condition,
                        "run_id": run_id,
                    }
                    try:
                        gen = generate(req.model, problem["prompt"], condition)
                        test_result = test_fn(problem, gen["code"])
                        metrics = compute_metrics(gen["code"])
                        cost = round(_estimate_cost(req.model, gen["tokens_in"], gen["tokens_out"]), 6)
                        row = {
                            "task_id": problem["task_id"],
                            "model": req.model,
                            "model_full": gen["model_full"],
                            "condition": condition,
                            "run_id": run_id,
                            "passed": test_result["passed"],
                            "cc": metrics["cc"],
                            "mi": metrics["mi"],
                            "loc": metrics["loc"],
                            "cognitive": metrics["cognitive"],
                            "tokens_in": gen["tokens_in"],
                            "tokens_out": gen["tokens_out"],
                            "latency_s": gen["latency_s"],
                            "cost_usd": cost,
                        }
                        _append_row(job_id, row)
                        _append_event(job_id, {**event_base, "status": "ok", **row})
                    except Exception as exc:
                        _append_event(job_id, {**event_base, "status": "error", "error": str(exc)})

        with _jobs_lock:
            rows = list(_jobs[job_id]["rows"])

        if not rows:
            raise RuntimeError("Nenhum resultado gerado. Confira chave de API, modelo e logs.")

        csv_path = _write_csv(job_id, rows)
        _set_job(
            job_id,
            status="complete",
            finished_at=time.time(),
            csv_path=str(csv_path),
            summary=_build_summary(rows),
        )
    except Exception as exc:
        _set_job(job_id, status="failed", finished_at=time.time(), error=str(exc))


@app.get("/", response_class=HTMLResponse)
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/api/config")
def api_config():
    return {
        "models": _configured_models(),
        "datasets": ["humaneval_plus", "humaneval"],
        "auth_required": bool(os.environ.get(AUTH_TOKEN_ENV)),
        "defaults": {"model": "claude", "dataset": "humaneval_plus", "n": 10, "runs": 1, "seed": 42},
    }


@app.post("/api/jobs")
def create_job(req: JobRequest, x_experiment_token: str = Header(default="")):
    expected_token = os.environ.get(AUTH_TOKEN_ENV)
    if expected_token and x_experiment_token != expected_token:
        raise HTTPException(status_code=401, detail="Token invalido.")
    if req.model not in MODELS:
        raise HTTPException(status_code=400, detail="Modelo invalido.")
    job_id = uuid.uuid4().hex[:12]
    now = time.time()
    with _jobs_lock:
        _jobs[job_id] = {
            "id": job_id,
            "status": "queued",
            "request": req.model_dump(),
            "created_at": now,
            "updated_at": now,
            "total_calls": req.n * 2 * req.runs,
            "completed_calls": 0,
            "running_cost_usd": 0.0,
            "rows": [],
            "events": [],
            "summary": None,
            "error": None,
            "csv_path": None,
        }
    threading.Thread(target=_run_job, args=(job_id, req), daemon=True).start()
    return {"job_id": job_id}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    with _jobs_lock:
        job = _jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job nao encontrado.")
        events = job["events"][-100:]
        return {
            "id": job["id"],
            "status": job["status"],
            "request": job["request"],
            "created_at": job["created_at"],
            "updated_at": job["updated_at"],
            "total_calls": job["total_calls"],
            "completed_calls": job["completed_calls"],
            "running_cost_usd": job["running_cost_usd"],
            "events": events,
            "summary": job["summary"],
            "error": job["error"],
            "has_csv": bool(job["csv_path"]),
        }


@app.get("/api/jobs/{job_id}/csv")
def download_csv(job_id: str):
    with _jobs_lock:
        job = _jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job nao encontrado.")
        csv_path = job.get("csv_path")
    if not csv_path or not Path(csv_path).exists():
        raise HTTPException(status_code=404, detail="CSV ainda nao disponivel.")
    return FileResponse(csv_path, media_type="text/csv", filename=f"{job_id}_results.csv")
