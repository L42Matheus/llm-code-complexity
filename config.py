"""
Configuração dos modelos usados no experimento.

Cada modelo lê sua chave de API de uma variável de ambiente — nunca coloque
chaves diretamente neste arquivo. Ajuste os nomes de modelo conforme
disponibilidade/preço no momento em que for rodar.
"""
import os

MODELS = {
    # Modelo proprietário de fronteira (Anthropic)
    "claude": {
        "provider": "anthropic",
        "model": os.environ.get("CLAUDE_MODEL", "claude-sonnet-5"),
        "api_key_env": "ANTHROPIC_API_KEY",
    },
    # Modelo proprietário de fronteira (OpenAI) — segundo ponto de comparação
    "gpt4o": {
        "provider": "openai",
        "model": os.environ.get("OPENAI_MODEL", "gpt-4o"),
        "api_key_env": "OPENAI_API_KEY",
        "base_url": None,  # usa o endpoint padrão da OpenAI
    },
    # Modelo aberto, servido via qualquer provedor com API compatível com
    # OpenAI (Together AI, Fireworks, Groq, vLLM local, etc.)
    "open_model": {
        "provider": "openai",
        "model": os.environ.get("OPEN_MODEL_NAME", "meta-llama/Llama-3.3-70B-Instruct-Turbo"),
        "api_key_env": "OPEN_MODEL_API_KEY",
        "base_url": os.environ.get("OPEN_MODEL_BASE_URL", "https://api.together.xyz/v1"),
    },
}

# Preço por milhão de tokens (USD), usado só para a coluna `cost_usd` do
# results.csv — é uma ESTIMATIVA para orçar o experimento, não um substituto
# do dashboard de billing oficial. Confira o valor atual antes de rodar em
# escala: platform.claude.com/docs/en/about-claude/pricing (Anthropic) e
# platform.openai.com/docs/pricing (OpenAI). Preço do open_model varia demais
# por provedor — ajuste manualmente se quiser custo estimado para ele também.
PRICING_PER_MTOK_USD = {
    "claude": {"input": 2.00, "output": 10.00},   # Claude Sonnet 5, conferido em ago/2026
    "gpt4o": {"input": 2.50, "output": 10.00},     # GPT-4o, pode ter mudado — confira
    "open_model": {"input": 0.0, "output": 0.0},   # defina manualmente conforme seu provedor
}

TEMPERATURE = 0.2
MAX_TOKENS = 1024
EXEC_TIMEOUT_SECONDS = 10
