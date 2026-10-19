# Uso

O CLI tem dois comandos: `sync` (pré-carrega o cache) e `dashboard` (sobe o
Streamlit).

## Pré-carregar o cache: `sync`

```bash
# Temporada inteira (só sessões já encerradas e não canceladas)
poetry run python -m novo_f1.main sync --year 2024

# Uma sessão específica
poetry run python -m novo_f1.main sync --year 2024 --session-key 9590
```

Para cada sessão, o `sync` baixa `drivers`, `session_result`, `laps`, `stints`,
`pit` e `position`, e `starting_grid` nas classificações (a OpenF1 associa o grid
à classificação que o definiu, não à corrida). Antes disso, carrega
`meetings` e `sessions` da temporada. A **telemetria não é pré-carregada**: ela
é buscada sob demanda pelo dashboard, uma volta por vez.

Ao final, o comando mostra o total de linhas por endpoint e de requisições HTTP.
Se você rodar o `sync` de novo para uma temporada passada, tudo vem do Parquet:
só os endpoints que vieram vazios (por exemplo, `pit` em uma sessão sem paradas)
são consultados de novo. Erros de uma sessão não
interrompem as demais: eles são listados no fim e o comando sai com código 1.

## Dashboard

```bash
poetry run python -m novo_f1.main dashboard
```

O comando abre o Streamlit (por padrão em <http://localhost:8501>). O `sync`
prévio é opcional, já que o dashboard busca e grava no cache o que faltar.

1. Na barra lateral, escolha a **temporada**, o **Grande Prêmio** (o mais recente
   vem selecionado), a **sessão** (a corrida, por padrão) e os **pilotos** (os
   três primeiros da classificação, por padrão).
2. Navegue pelas páginas no menu lateral.
3. Na página **Telemetria**, até 2 pilotos são comparados na volta mais rápida
   de cada um ou na mesma volta.

!!! info "Avisos exibidos na interface"
    - `intervals`, `overtakes` e `championship_*` existem **só em corridas**
      (Race e Sprint). Nas outras sessões, essas seções mostram um aviso e a API
      não é chamada.
    - `championship_*` está em **beta**. `overtakes` e `team_radio` podem ter
      **dados incompletos**.
    - `stop_duration` (tempo parado no pit) só existe a partir do GP dos EUA
      de 2024.

## Cache local

```text
data/raw/<endpoint>/year=<ano>/session_key=<k>.parquet           # por sessão
data/raw/<meetings|sessions>/year=<ano>/all.parquet              # calendário
data/raw/<car_data|location>/year=<ano>/session_key=<k>_driver=<d>_lap=<n>.parquet
```

- **Histórico é imutável**: se o arquivo existe, a API não é chamada.
- `meetings` e `sessions` do **ano corrente** expiram após `CALENDAR_TTL_HOURS`
  (24h por padrão), porque a OpenF1 os atualiza à meia-noite (UTC).
- **Respostas vazias não são gravadas**, para que dados publicados depois
  (por exemplo, o resultado oficial) sejam buscados de novo.
- Para limpar o cache, apague a pasta `data/` (ou só o arquivo desejado).

## Variáveis de ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `OPENF1_BASE_URL` | `https://api.openf1.org/v1` | URL base da API |
| `OPENF1_API_TOKEN` | *(vazio)* | Token opcional, enviado como `Authorization: Bearer` só se definido. O histórico não exige token |
| `DATA_DIR` | `data` | Diretório raiz do cache em Parquet |
| `REQUEST_TIMEOUT` | `30` | Timeout de cada requisição (s) |
| `MAX_RETRIES` | `3` | Novas tentativas em 429, 5xx e erros de rede |
| `MIN_REQUEST_INTERVAL` | `0.35` | Intervalo mínimo entre requisições (s) |
| `BACKOFF_FACTOR` | `1.0` | Base do backoff exponencial (s): 1, 2, 4… (respeita `Retry-After`) |
| `CALENDAR_TTL_HOURS` | `24` | Validade do calendário do ano corrente (h) |

!!! danger "Segredos"
    Nunca escreva o token em código, testes ou documentação. Use o `.env`
    (não versionado) ou o ambiente.
