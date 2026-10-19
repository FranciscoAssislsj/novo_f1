# Plano de criação do projeto `novo_f1`

## Contexto

O repositório `novo_f1` tem apenas o esqueleto: `pyproject.toml` sem dependências, `src/novo_f1/__init__.py` e `tests/__init__.py` vazios. Ainda não existem `.python-version`, `.gitignore`, `README.md`, `docs/` nem CI.

**Objetivo:** criar um **dashboard visual em Streamlit** para explorar os dados históricos da **OpenF1 API** (temporadas de 2023 em diante, gratuitas e sem autenticação). A referência da API está em `doc_api.md`.
- Os dados extraídos ficam em **cache local em Parquet**.
- O escopo do MVP cobre os quatro grupos de dados: calendário, pilotos e resultados, voltas e estratégia, telemetria e contexto.
- O código segue os padrões obrigatórios de `SKILL.md`: pyenv, Poetry, Ruff, Pytest com cobertura ≥ 50% e MkDocs Material.

## Decisões de arquitetura

- **Camadas isoladas:** `ingestion` (HTTP) → `storage` (Parquet) → `transformation` (regras puras com pandas) → `dashboard` (Streamlit e Plotly).
- **Páginas finas:** as páginas do Streamlit só chamam serviços e builders de gráficos. A lógica fica em funções puras, que podem ser testadas, e isso garante a cobertura de 50%.
- **Cache imutável:** o histórico não muda. Se o arquivo Parquet de um `endpoint + session_key` já existe, ele é lido do disco e a API não é chamada. `meetings` e `sessions` do ano corrente expiram em 24h, porque a API os atualiza à meia-noite (UTC).
- **Telemetria sob demanda:** `car_data` e `location` (~3,7 Hz) nunca são baixados em massa. A busca é por `session_key + driver_number` e pela janela de tempo da volta (`date>=início` e `date<início da próxima`).
- **Filtros com operadores:** o `httpx` codifica `>=` dentro de `params`. Por isso, um utilitário monta a query string manualmente, aceitando repetição de parâmetros e `%20`.
- **Resiliência:** a API não documenta rate limit. O cliente terá timeout, retry com backoff exponencial em 429/5xx e um intervalo mínimo entre requisições, todos configuráveis.
- **Endpoints só de corrida** (`intervals`, `overtakes`, `championship_*`): ficam em uma constante e não são chamados em sessões que não são corrida.

## Dependências (via Poetry, nunca pip)

| Grupo | Pacotes |
|---|---|
| produção | `httpx`, `pandas`, `pyarrow`, `streamlit`, `plotly` |
| dev | `ruff`, `pytest`, `pytest-cov`, `pytest-mock` |
| docs (opcional) | `mkdocs-material`, `mkdocstrings[python]` |

> ⚠️ Python 3.14: confirmar no `poetry add` se há wheels de `pyarrow`, `pandas` e `streamlit`. Se não houver, avisar o usuário antes de qualquer mudança no `.python-version` (regra 4 do SKILL).

## Estrutura alvo

```text
src/novo_f1/
├── __init__.py
├── main.py                    # CLI: `sync` (pré-carrega cache) e `dashboard` (sobe o Streamlit)
├── config/settings.py         # OPENF1_BASE_URL, OPENF1_API_TOKEN, DATA_DIR, REQUEST_TIMEOUT, MAX_RETRIES
├── utils/query.py             # build_query(): filtros com operadores, valores repetidos, encoding
├── ingestion/
│   ├── client.py              # OpenF1Client.get(endpoint, filters) com retry/backoff
│   └── endpoints.py           # fetch_meetings, fetch_sessions, fetch_drivers, fetch_laps, ...
├── storage/
│   └── parquet_store.py       # caminho data/raw/<endpoint>/year=<y>/session_key=<k>.parquet; save/load/exists/expired
├── services/
│   └── repository.py          # "cache-or-fetch": devolve DataFrame do disco ou da API e grava
├── transformation/
│   ├── calendar.py            # meetings/sessions → calendário da temporada
│   ├── results.py             # session_result + drivers + starting_grid (+ cores das equipes) → classificação; campeonato
│   ├── laps.py                # volta mais rápida, melhores setores, ritmo por stint, limpeza de pit-out laps
│   ├── strategy.py            # stints + pit → linha do tempo de pneus, resumo de paradas (lane/stop duration)
│   ├── positions.py           # position/intervals → evolução de posições e gaps
│   ├── telemetry.py           # janela de tempo da volta, merge car_data×location, decodificação DRS
│   └── context.py             # weather e race_control (bandeiras, SC) → séries e eventos por volta
└── dashboard/
    ├── app.py                 # entrada do Streamlit + seletor ano → meeting → sessão (session_state)
    ├── data.py                # wrappers @st.cache_data em cima de services.repository
    ├── charts.py              # builders Plotly puros (recebem DataFrame e devolvem Figure)
    └── pages/
        ├── 1_Calendario.py
        ├── 2_Resultados.py    # classificação, grid × chegada, campeonato
        ├── 3_Voltas.py        # tempos por volta, comparação de pilotos, setores
        ├── 4_Estrategia.py    # stints/pneus, pit stops, posições ao longo da corrida
        └── 5_Telemetria.py    # velocidade/acelerador/freio/marcha por volta, traçado (x,y), clima, race control
tests/
├── conftest.py                # fixtures com payloads JSON reduzidos de cada endpoint
├── fixtures/*.json
└── unit/test_query.py, test_client.py, test_parquet_store.py, test_repository.py,
         test_laps.py, test_strategy.py, test_results.py, test_telemetry.py, test_charts.py, ...
```

Também na raiz: `.python-version`, `.gitignore` (o mínimo do SKILL + `data/`), `.env.example`, `poetry.toml`, `mkdocs.yml`, `README.md`, `docs/` e `.github/workflows/ci.yml`.

## Fases de implementação

### Fase 0 — Fundação do ambiente
1. `pyenv local 3.14.x` → cria o `.python-version`.
2. `poetry config virtualenvs.in-project true --local` e `poetry env use (pyenv which python)`.
3. Adicionar as dependências por grupo com `poetry add`. O grupo `docs` fica como `optional = true`.
4. No `pyproject.toml`: blocos `[tool.ruff]`, `[tool.pytest.ini_options]` e `[tool.coverage]` copiados do SKILL (`fail_under = 50`). Preencher `description`.
5. Criar `.gitignore`, `.env.example`, `README.md` inicial e um commit de base.

**Pronto quando:** `poetry install`, `poetry check --lock` e `ruff check` passam.

### Fase 1 — Ingestão e cache
1. `config/settings.py`, lendo o ambiente com `os.getenv` (padrão do SKILL §8).
2. `utils/query.py` → `build_query()` com testes parametrizados (`=`, `>=`, `<`, intervalo, repetição, espaços, `latest`).
3. `ingestion/client.py` → `OpenF1Client`: monta a URL, faz retry em 429/5xx, `raise_for_status` e devolve `list[dict]`. Envia o token só se `OPENF1_API_TOKEN` existir.
4. `ingestion/endpoints.py` → uma função fina por endpoint (todos os 18 da tabela de `doc_api.md`), com a constante `RACE_ONLY_ENDPOINTS`.
5. `storage/parquet_store.py` e `services/repository.py` (cache-or-fetch, TTL para meetings/sessions).
6. `main.py sync --year 2025 [--session-key N]` pré-carrega o calendário, os pilotos, os resultados, as voltas e a estratégia. A telemetria não entra.

**Testes:** HTTP mockado com `pytest-mock`, Parquet em `tmp_path` e nenhuma chamada real.

### Fase 2 — Transformações
Implementar os módulos de `transformation/`, todos como funções puras `DataFrame → DataFrame/valor`. Cobrir os casos de borda:
- `lap_duration` nulo e pit-out laps;
- `gap_to_leader` como `"+1 LAP"` ou `null`;
- `session_result.duration` como array em sessões de classificação;
- `stop_duration` ausente antes do GP dos EUA de 2024;
- DRS conforme a tabela de referência;
- campos depreciados: usar `lane_duration` e não `pit_duration`, e ignorar `country_code`.

### Fase 3 — Dashboard Streamlit
1. `dashboard/app.py` com a barra lateral de seleção (ano → meeting → sessão → pilotos), guardada em `st.session_state`.
2. `dashboard/charts.py` com os builders Plotly: barras de classificação, linha de tempos de volta, Gantt de stints por composto, linha de posições, telemetria multi-eixo e traçado x/y colorido por velocidade.
3. As cinco páginas, cada uma usando `data.py`, `transformation` e `charts`. Endpoints só de corrida aparecem com aviso em outras sessões. `team_radio` e `overtakes` levam um aviso de "dados incompletos".
4. `main.py dashboard` → `streamlit run src/novo_f1/dashboard/app.py`.

**Testes:** testes unitários dos builders (tipo e número de traces). Opcionalmente, um smoke test com `streamlit.testing.v1.AppTest` e o repositório mockado.

### Fase 4 — Documentação e CI
1. `mkdocs.yml` (modelo do SKILL §7) e as páginas `docs/index.md`, `installation.md`, `usage.md` (sync, dashboard, variáveis de ambiente), `architecture.md` (diagrama Mermaid do fluxo API → Parquet → transformação → Streamlit) e `reference.md` (mkdocstrings).
2. `.github/workflows/ci.yml` conforme o SKILL §8.
3. `README.md` com o quickstart.

## Riscos e limitações conhecidas
- A API não tem rate limit documentado. Mitigação: backoff e o cache em Parquet.
- `overtakes` e `team_radio` são incompletos, e `championship_*` está em beta. A interface sinaliza isso.
- O volume de telemetria é alto. Ela só é buscada sob demanda, por volta.
- Dados ao vivo exigem assinatura e ficam **fora do escopo**. O token é só opcional na configuração.

## Verificação (ao fim de cada fase)

```bash
poetry run ruff format . && poetry run ruff check . --fix
poetry run ruff format --check . && poetry run ruff check .
poetry run pytest                      # cobertura ≥ 50%, sem rede
poetry check --lock
poetry run mkdocs build --strict       # fase 4 / quando docs mudarem
```

**Teste ponta a ponta manual** (exige rede):
1. `poetry run python -m novo_f1.main sync --year 2024` → conferir os arquivos em `data/raw/`.
2. `poetry run python -m novo_f1.main dashboard` → navegar pelas cinco páginas com uma corrida (ex.: Singapura 2024).
3. Rodar o sync de novo e confirmar que as respostas vêm do cache, sem novas requisições.

Qualquer verificação que não for executada deve ser relatada explicitamente.
