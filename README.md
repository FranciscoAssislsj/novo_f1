# Novo F1

Dashboard em Streamlit para explorar dados históricos de Fórmula 1 (2023+) da
[OpenF1 API](https://openf1.org), com cache local em Parquet.

Inclui calendário, resultados (classificação, grid x chegada e campeonato),
voltas e setores, estratégia (pneus, pit stops, posições e gaps), telemetria por
volta (velocidade, acelerador, freio, marcha e traçado), clima e direção de prova.

## Quickstart

```bash
pyenv install 3.14.2                     # versão de .python-version
poetry env use "$(pyenv which python)"   # cria .venv/ no projeto
poetry install

# (opcional) pré-carregar o cache de uma temporada
poetry run python -m novo_f1.main sync --year 2024

# subir o dashboard
poetry run python -m novo_f1.main dashboard
```

Os dados ficam em `data/raw/` (não versionado). A configuração é feita por
variáveis de ambiente (veja `.env.example`). Nenhuma é obrigatória.

## Desenvolvimento

```bash
poetry run ruff format . && poetry run ruff check . --fix
poetry run pytest                 # cobertura mínima de 50%, sem rede
poetry check --lock
poetry install --with docs && poetry run mkdocs serve
```

Os padrões do projeto estão em `.claude/SKILL.md`. A documentação completa está
em `docs/` (instalação, uso, arquitetura e referência).

> A OpenF1 é uma API não oficial, sem vínculo com as empresas da Fórmula 1.
