"""Chama os modelos configurados, extrai o código e devolve metadados
(tokens de entrada/saída, latência) para rastreabilidade e custo."""
import os
import re
import time

from config import MODELS, TEMPERATURE, MAX_TOKENS
from prompts import build_prompt

_CODE_BLOCK_RE = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)


def extract_code(text: str) -> str:
    match = _CODE_BLOCK_RE.search(text)
    return match.group(1).strip() if match else text.strip()


def _call_anthropic(cfg, prompt):
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ[cfg["api_key_env"]])
    resp = client.messages.create(
        model=cfg["model"],
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(block.text for block in resp.content if block.type == "text")
    return text, resp.usage.input_tokens, resp.usage.output_tokens


def _call_openai_compatible(cfg, prompt):
    from openai import OpenAI

    client = OpenAI(api_key=os.environ[cfg["api_key_env"]], base_url=cfg.get("base_url"))
    resp = client.chat.completions.create(
        model=cfg["model"],
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    text = resp.choices[0].message.content
    usage = resp.usage
    # Provedores OpenAI-compatible nem sempre preenchem `usage` (alguns
    # proxies omitem) — usa 0 nesse caso em vez de quebrar o pipeline.
    tokens_in = getattr(usage, "prompt_tokens", 0) or 0
    tokens_out = getattr(usage, "completion_tokens", 0) or 0
    return text, tokens_in, tokens_out


def generate(model_key: str, task_prompt: str, condition: str) -> dict:
    """Retorna dict com: code, model (string exata usada), tokens_in,
    tokens_out, latency_s."""
    if model_key not in MODELS:
        raise ValueError(f"Modelo desconhecido: {model_key!r}. Configurados: {list(MODELS)}")
    cfg = MODELS[model_key]
    if cfg["api_key_env"] not in os.environ:
        raise RuntimeError(
            f"Variável de ambiente {cfg['api_key_env']} não definida "
            f"(necessária para o modelo '{model_key}')."
        )
    prompt = build_prompt(task_prompt, condition)

    start = time.monotonic()
    if cfg["provider"] == "anthropic":
        raw, tokens_in, tokens_out = _call_anthropic(cfg, prompt)
    elif cfg["provider"] == "openai":
        raw, tokens_in, tokens_out = _call_openai_compatible(cfg, prompt)
    else:
        raise ValueError(f"Provider desconhecido: {cfg['provider']!r}")
    latency_s = time.monotonic() - start

    return {
        "code": extract_code(raw),
        "model_full": cfg["model"],
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "latency_s": round(latency_s, 3),
    }
