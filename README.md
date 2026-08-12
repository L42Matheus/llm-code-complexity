# Toolkit do experimento — complexidade ciclomática vs. prompt minimalista

Implementa o desenho experimental da Seção 3 do paper: gera soluções em duas
condições (prompt padrão vs. prompt minimalista) para uma amostra do
benchmark HumanEval, testa a corretude de cada solução e mede complexidade
ciclomática, Índice de Manutenibilidade e LOC com o Radon.

## 1. Instalar dependências

```bash
pip install -r requirements.txt
```

## 2. Configurar chaves de API

Rode com os modelos que já tiver acesso — não precisa dos três de uma vez.

```bash
export ANTHROPIC_API_KEY="sua-chave"          # para o modelo "claude"
export OPENAI_API_KEY="sua-chave"             # para o modelo "gpt4o"
export OPEN_MODEL_API_KEY="sua-chave"         # para o modelo aberto
export OPEN_MODEL_BASE_URL="https://api.together.xyz/v1"   # ou outro provedor OpenAI-compatible
export OPEN_MODEL_NAME="meta-llama/Llama-3.3-70B-Instruct-Turbo"
```

`OPEN_MODEL_*` funciona com qualquer provedor que exponha uma API
compatível com a da OpenAI (Together AI, Fireworks, Groq, um servidor vLLM
local, etc.) — só trocar `OPEN_MODEL_BASE_URL`.

## 3. Testar sem gastar créditos de API (opcional, mas recomendado primeiro)

```bash
python3 test_offline.py
```

Isso reaproveita as 8 soluções do estudo piloto manual (já incluídas no
paper) só para confirmar que `metrics.py` e `analyze.py` funcionam antes de
gastar créditos de verdade. Já foi rodado e validado — reproduz exatamente
os números da Seção 4 do paper (CC baseline 6,38 / minimal 1,88 etc.), e
já calcula Wilcoxon + A12 mesmo com n pequeno (útil para conferir a mecânica
do teste, não para tirar conclusões).

## 4. Rodar o experimento de verdade

```bash
python3 run_pipeline.py --n 164 --runs 5 --models claude
```

- `--n`: quantos problemas do HumanEval amostrar (o benchmark completo tem
  164). Comece pequeno (`--n 3`) para validar, depois escale.
- `--runs`: repetições por problema × condição (recomendado 3-10, já que a
  saída do LLM varia entre chamadas mesmo com temperatura baixa — sem isso
  você não separa efeito real de ruído estocástico).
- `--models`: quais dos três modelos configurados usar (`claude`, `gpt4o`,
  `open_model`). Pode rodar só `claude` primeiro e adicionar os outros depois
  — os CSVs de diferentes rodadas usam o mesmo esquema de colunas.
- `--dataset`: **`humaneval_plus` é o padrão e o recomendado.** Usa a suíte
  expandida do EvalPlus/HumanEval+ (Liu et al., 2023) — até ~1.000 casos de
  teste por problema, em vez dos ~8 originais. Isso é importante para a tese
  central deste trabalho: sem uma suíte robusta, uma solução minimalista
  incompleta pode "parecer correta" só porque a suíte original não cobre o
  caso de borda que ela deixou de tratar (foi exatamente o que aconteceu no
  problema de palíndromo do piloto manual). Use `--dataset humaneval` apenas
  se quiser rodar mais rápido em um teste exploratório.
- `--seed`: fixa a amostragem para reprodutibilidade.

Isso grava `results.csv`, uma linha por problema × modelo × condição × run,
com: `task_id`, `model` (chave lógica), `model_full` (string exata do
modelo, ex. `claude-sonnet-5`), `condition`, `run_id`, `passed`, `cc`, `mi`,
`loc`, `cognitive` (complexidade cognitiva, Campbell 2018), `tokens_in`,
`tokens_out`, `latency_s`, `cost_usd`. O CSV já fica no formato certo para
usar como artefato de replicação do paper.

## 5. Ver o resumo estatístico

```bash
python3 summarize.py
```

Imprime a taxa de aprovação, o custo total estimado e, para cada métrica de
complexidade (CC, MI, LOC, complexidade cognitiva) e também para
`tokens_out` (tokens de saída por geração — a resposta empírica à pergunta
"o prompt minimalista também reduz o custo de geração, ou só reduz CC sem
mexer em tokens?"), duas comparações: **geral** (todas as soluções) e
**restrita a soluções corretas nas duas condições** — essa segunda é a que importa de verdade, porque evita que uma
solução minimalista que falhou o teste (por ter cortado tratamento
necessário) seja contada como "redução de complexidade" legítima. Com
múltiplas repetições (`--runs > 1`), a comparação é sempre pareada por
tarefa (média entre runs), não por execução individual.

## Estimando custo antes de rodar

`run_pipeline.py` já imprime o custo estimado (`cost_usd`) linha a linha e o
acumulado ao final, usando os preços em `PRICING_PER_MTOK_USD` em
`config.py` — **confira se esses valores ainda estão corretos** antes de
rodar em escala (preços de API mudam; veja o comentário no próprio
`config.py` com os links oficiais). Para dimensionar antes de começar: 164
problemas × 2 condições × 5 repetições × 1 modelo = 1.640 chamadas.

## Limitações conhecidas

- O harness de execução (`evaluate.py`) reconstrói o mesmo padrão do
  harness oficial do HumanEval, mas roda em subprocesso com timeout — não
  é um sandbox completo. Não rode contra modelos/prompts não confiáveis.
- `run_test_plus` (usado por padrão) é uma reimplementação própria e
  simplificada da lógica de checagem do EvalPlus: compara igualdade direta
  entre a saída do candidato e a da `canonical_solution`, com tolerância
  numérica para floats. Não reproduz o tratamento completo de estruturas
  aninhadas do checker oficial do EvalPlus — validado contra a solução
  canônica (passa) e uma solução quebrada (falha corretamente), mas vale
  revisar antes de reportar como métrica final em publicação.
- `MAX_TOKENS=1024` pode truncar soluções muito longas em alguns problemas
  do HumanEval mais complexos; ajuste em `config.py` se notar erros de
  sintaxe por corte no meio do código.
- Complexidade cognitiva (Campbell, 2018), citada no paper como métrica
  complementar recomendada, não está incluída aqui — precisaria do pacote
  `cognitive-complexity` à parte.
