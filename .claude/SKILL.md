---
name: python-project-standards
description: Padrões obrigatórios de arquitetura, dependências (Pyenv + Poetry), qualidade (Ruff), testes (Pytest, cobertura ≥ 50%) e documentação (MkDocs Material) para criar ou modificar código Python neste projeto.
---

# SKILL.md — Padrões de Desenvolvimento Python

Guia operacional para agentes de IA e desenvolvedores. Siga estas instruções sempre que criar, alterar ou manter código neste repositório.

**Convenção deste documento**

- **OBRIGATÓRIO** — regra que não pode ser violada.
- **RECOMENDADO** — boa prática; desvios devem ser justificados.

**Referência do projeto**

| Item | Valor |
|---|---|
| Nome do projeto (distribuição) | `novo-f1` |
| Pacote importável | `novo_f1` (em `src/novo_f1/`) |
| Python | 3.14 (definido em `.python-version`) |
| Ferramentas | pyenv (pyenv-win no Windows), Poetry 2.x, Ruff, Pytest + pytest-cov, MkDocs Material |

> Em outro projeto, substitua `novo_f1` pelo nome do pacote correspondente.

---

## 1. Fluxo rápido para agentes de IA

Execute nesta ordem em toda tarefa que altere código:

```bash
# 0. Entender o contexto
git status
# leia a estrutura de src/novo_f1/ e tests/ antes de criar arquivos

# 1. Garantir o ambiente
pyenv version                 # deve bater com .python-version
poetry install                # sincroniza dependências com poetry.lock

# 2. Implementar a alteração + testes

# 3. Validar (todos devem passar)
poetry run ruff format .
poetry run ruff check . --fix
poetry run ruff format --check .
poetry run ruff check .
poetry run pytest
poetry check --lock
poetry run mkdocs build --strict   # se a documentação foi alterada
```

Se algum comando não puder ser executado (ferramenta ausente, sem rede, etc.), **informe explicitamente** qual verificação não foi feita e por quê. Nunca declare a tarefa concluída sem essa informação.

---

## 2. Estrutura e arquitetura

### Regras OBRIGATÓRIAS

- Usar **src layout**: todo código-fonte fica em `src/novo_f1/`.
- Todo diretório de pacote contém `__init__.py`.
- Testes ficam em `tests/`, **nunca** dentro de `src/`.
- Separar responsabilidades em módulos (ingestão, transformação, configuração, utilitários).
- Não duplicar lógica: antes de escrever uma função, procure se já existe algo equivalente (`grep`/busca no editor).
- Usar type hints em todas as funções e métodos públicos.
- Nomes descritivos: `snake_case` para módulos, funções e variáveis; `PascalCase` para classes; `UPPER_SNAKE_CASE` para constantes.
- Não criar arquivos monolíticos: se um módulo passar de ~300 linhas ou acumular responsabilidades distintas, divida-o.

### RECOMENDADO

- Aplicar DRY, KISS e SOLID quando trouxerem ganho real — não criar abstrações "para o futuro".
- Funções pequenas, puras sempre que possível (entrada → saída, sem efeitos colaterais), o que facilita testes.
- Isolar I/O (HTTP, disco, banco) em camadas finas, separadas das regras de negócio.
- Criar apenas os módulos necessários; a estrutura abaixo é referência, não obrigação.

### Estrutura de referência

```text
novo_f1/
├── .github/
│   └── workflows/
│       └── ci.yml
├── .venv/                    # criado pelo Poetry, NÃO versionado
├── docs/
│   └── index.md
├── src/
│   └── novo_f1/
│       ├── __init__.py
│       ├── main.py           # ponto de entrada / orquestração
│       ├── config/           # settings, leitura de variáveis de ambiente
│       ├── ingestion/        # clientes de API, leitura de fontes
│       ├── transformation/   # regras de negócio, limpeza, agregações
│       └── utils/            # funções genéricas reutilizáveis
├── tests/
│   ├── conftest.py           # fixtures compartilhadas
│   └── unit/
│       ├── test_ingestion.py
│       └── test_transformation.py
├── .env.example
├── .gitignore
├── .python-version
├── poetry.toml               # config local do Poetry (virtualenvs.in-project)
├── pyproject.toml
├── poetry.lock
├── mkdocs.yml
├── README.md
└── SKILL.md
```

### Exemplo de módulo bem estruturado

```python
# src/novo_f1/transformation/laps.py
"""Regras de transformação de dados de voltas."""

from collections.abc import Iterable


def fastest_lap(lap_durations: Iterable[float | None]) -> float | None:
    """Retorna a menor duração de volta válida, ou None se não houver."""
    valid = [duration for duration in lap_durations if duration is not None]
    return min(valid, default=None)
```

---

## 3. Versão do Python com Pyenv

### Regras OBRIGATÓRIAS

- O `pyenv` é a ferramenta oficial para versões do Python (no Windows, `pyenv-win`).
- O arquivo `.python-version` deve existir na raiz e ser versionado.
- A versão do `.python-version` deve satisfazer `requires-python` do `pyproject.toml` (atualmente `>=3.14`).
- Não depender do Python global do sistema para rodar o projeto.

### Comandos

```bash
# Listar versões disponíveis para instalação
pyenv install --list

# Instalar a versão do projeto
pyenv install 3.14.2

# Fixar a versão no diretório do projeto (cria/atualiza .python-version)
pyenv local 3.14.2

# Verificar a versão ativa e o executável
pyenv version
python --version
pyenv which python
```

> Se `python --version` não corresponder ao `.python-version`, rode `pyenv rehash` e reabra o terminal.

---

## 4. Dependências e ambiente virtual com Poetry

### Regras OBRIGATÓRIAS

- Usar **somente** o Poetry para criar o ambiente virtual e gerenciar dependências.
- **Nunca** usar `pip install` (nem dentro da `.venv`).
- **Nunca** instalar dependências do projeto no Python global.
- O ambiente virtual fica em `.venv/` na raiz do projeto.
- Separar dependências de produção (`[project].dependencies`) das de desenvolvimento (grupo `dev`) e documentação (grupo `docs`).
- `pyproject.toml` e `poetry.lock` devem ser commitados juntos sempre que uma dependência mudar.
- Executar ferramentas do projeto via `poetry run <comando>` (ou com o ambiente ativado).
- Não editar `poetry.lock` manualmente.

### Configuração inicial (uma vez por máquina/clone)

```bash
# Criar a .venv dentro do projeto (grava em poetry.toml, só para este projeto)
poetry config virtualenvs.in-project true --local

# Apontar o Poetry para o Python do pyenv
poetry env use "$(pyenv which python)"      # Bash
# poetry env use (pyenv which python)       # PowerShell

# Instalar dependências (produção + dev + docs)
poetry install --with docs

# Conferir o ambiente
poetry env info
```

### Comandos do dia a dia

```bash
# Dependência de produção
poetry add httpx

# Dependências de desenvolvimento
poetry add --group dev ruff pytest pytest-cov pytest-mock

# Dependências de documentação (grupo opcional)
poetry add --group docs mkdocs-material "mkdocstrings[python]"

# Remover dependência
poetry remove httpx
poetry remove --group dev pytest-mock

# Atualizar
poetry show --outdated
poetry update httpx           # uma dependência
poetry update                 # todas, dentro das restrições

# Sincronizar o ambiente exatamente com o lock (remove pacotes extras)
poetry sync --with docs

# Validar pyproject.toml e consistência do lock
poetry check --lock

# Executar comandos no ambiente
poetry run python -m novo_f1.main
poetry run pytest

# Ativar o ambiente no shell atual (Poetry 2.x; `poetry shell` não existe mais por padrão)
poetry env activate           # imprime o comando de ativação a ser executado
```

### Grupo opcional no `pyproject.toml`

Para que `docs` só seja instalado com `--with docs`:

```toml
[tool.poetry.group.docs]
optional = true
```

---

## 5. Qualidade de código com Ruff

### Regras OBRIGATÓRIAS

- Ruff é a única ferramenta de lint, formatação e ordenação de imports (não usar black, isort ou flake8 em paralelo).
- Configuração centralizada no `pyproject.toml`.
- `ruff check` e `ruff format --check` devem passar sem erros antes de concluir qualquer tarefa.
- Não desabilitar regras sem justificativa técnica. Quando inevitável, usar `# noqa: <CÓDIGO>` na linha específica, com comentário explicando o motivo — nunca `# noqa` genérico.

### Configuração (`pyproject.toml`)

```toml
[tool.ruff]
line-length = 88
target-version = "py314"
src = ["src", "tests"]

[tool.ruff.lint]
select = [
    "E",    # pycodestyle (erros)
    "W",    # pycodestyle (avisos)
    "F",    # pyflakes
    "I",    # isort (ordenação de imports)
    "N",    # pep8-naming
    "UP",   # pyupgrade
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "SIM",  # flake8-simplify
    "PT",   # flake8-pytest-style
    "RUF",  # regras específicas do Ruff
]

[tool.ruff.lint.isort]
known-first-party = ["novo_f1"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
docstring-code-format = true
```

### Comandos

```bash
# Verificar
poetry run ruff check .
poetry run ruff format --check .

# Corrigir automaticamente
poetry run ruff check . --fix
poetry run ruff format .

# Apenas organizar imports
poetry run ruff check . --select I --fix

# Ver explicação de uma regra
poetry run ruff rule B006
```

---

## 6. Testes automatizados com Pytest

### Regras OBRIGATÓRIAS

- Usar `pytest` para todos os testes; testes em `tests/` (unitários em `tests/unit/`).
- Nomenclatura: arquivos `test_*.py`, funções `test_*`, classes `Test*` (sem `__init__`).
- Toda função/componente com regra de negócio deve ter testes unitários.
- Ao alterar uma funcionalidade, criar ou atualizar os testes correspondentes no mesmo commit.
- Testes **não** podem acessar APIs externas, bancos de produção ou usar credenciais reais — usar mocks/fixtures.
- **Cobertura mínima: 50%** do código em `src/novo_f1/`. A suíte deve **falhar** abaixo disso.
- Não reduzir `fail_under` nem adicionar exclusões de cobertura para "passar" no limite.

### RECOMENDADO

- Um arquivo de teste por módulo (`transformation/laps.py` → `tests/unit/test_laps.py`).
- Padrão Arrange–Act–Assert; um comportamento por teste.
- `@pytest.mark.parametrize` para cobrir vários casos sem duplicar código.
- Fixtures compartilhadas em `tests/conftest.py`.
- Testar casos de borda: listas vazias, `None`, valores inválidos, erros HTTP.

### Configuração (`pyproject.toml`)

```toml
[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
addopts = [
    "-ra",
    "--strict-markers",
    "--cov=novo_f1",
    "--cov-report=term-missing",
]

[tool.coverage.run]
source = ["novo_f1"]
branch = true

[tool.coverage.report]
fail_under = 50
show_missing = true
skip_empty = true
exclude_also = [
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

> O pacote é instalado em modo editável pelo `poetry install`, por isso `--cov=novo_f1` funciona sem ajustar `PYTHONPATH`.

### Exemplo: fixture + parametrize

```python
# tests/conftest.py
import pytest


@pytest.fixture
def sample_laps() -> list[dict[str, float | None]]:
    return [
        {"lap_number": 1, "lap_duration": 95.2},
        {"lap_number": 2, "lap_duration": 93.8},
        {"lap_number": 3, "lap_duration": None},
    ]
```

```python
# tests/unit/test_laps.py
import pytest

from novo_f1.transformation.laps import fastest_lap


def test_fastest_lap_returns_minimum(sample_laps):
    durations = [lap["lap_duration"] for lap in sample_laps]

    assert fastest_lap(durations) == 93.8


@pytest.mark.parametrize(
    ("durations", "expected"),
    [
        ([], None),
        ([None, None], None),
        ([90.0], 90.0),
    ],
)
def test_fastest_lap_edge_cases(durations, expected):
    assert fastest_lap(durations) == expected
```

### Exemplo: mock de dependência externa (pytest-mock)

```python
# src/novo_f1/ingestion/client.py
import httpx

BASE_URL = "https://api.openf1.org/v1"


def fetch_sessions(year: int) -> list[dict]:
    response = httpx.get(f"{BASE_URL}/sessions", params={"year": year}, timeout=30)
    response.raise_for_status()
    return response.json()
```

```python
# tests/unit/test_client.py
import httpx
import pytest

from novo_f1.ingestion import client


def test_fetch_sessions_returns_json(mocker):
    fake_response = mocker.Mock(spec=httpx.Response)
    fake_response.json.return_value = [{"session_key": 9161}]
    mock_get = mocker.patch.object(client.httpx, "get", return_value=fake_response)

    result = client.fetch_sessions(2023)

    assert result == [{"session_key": 9161}]
    mock_get.assert_called_once()


def test_fetch_sessions_propagates_http_error(mocker):
    fake_response = mocker.Mock(spec=httpx.Response)
    fake_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "erro", request=mocker.Mock(), response=mocker.Mock()
    )
    mocker.patch.object(client.httpx, "get", return_value=fake_response)

    with pytest.raises(httpx.HTTPStatusError):
        client.fetch_sessions(2023)
```

### Comandos

```bash
poetry run pytest                              # suíte completa + cobertura
poetry run pytest tests/unit/test_laps.py      # um arquivo
poetry run pytest -k fastest_lap               # por nome
poetry run pytest -x                           # parar no primeiro erro
poetry run pytest --cov-report=html            # relatório em htmlcov/ (não versionar)
```

---

## 7. Documentação com MkDocs Material

### Regras OBRIGATÓRIAS

- Documentação em `docs/`, configurada por `mkdocs.yml` na raiz, tema `material`.
- Documentar: visão geral, instalação, configuração (variáveis de ambiente), execução, arquitetura/módulos e fluxos principais.
- Atualizar a documentação no mesmo commit sempre que uma mudança alterar comportamento, configuração, comandos ou interfaces públicas.
- `mkdocs build --strict` deve passar sem avisos.
- Outro desenvolvedor deve conseguir instalar e rodar o projeto apenas lendo `README.md` + `docs/`.

### RECOMENDADO

- Docstrings no estilo Google em funções públicas, renderizadas com `mkdocstrings`.
- Diagramas de fluxo com Mermaid (suportado pelo Material via `pymdownx.superfences`).

### Estrutura sugerida

```text
docs/
├── index.md            # visão geral e objetivo
├── installation.md     # pyenv, Poetry, poetry install
├── usage.md            # como executar, exemplos
├── architecture.md     # módulos, fluxo de dados
└── reference.md        # API gerada via mkdocstrings
```

### `mkdocs.yml` de referência

```yaml
site_name: Novo F1
repo_url: https://github.com/<usuario>/novo_f1

theme:
  name: material
  language: pt-BR
  features:
    - navigation.sections
    - content.code.copy
  palette:
    - scheme: default
      toggle:
        icon: material/brightness-7
        name: Modo escuro
    - scheme: slate
      toggle:
        icon: material/brightness-4
        name: Modo claro

nav:
  - Início: index.md
  - Instalação: installation.md
  - Uso: usage.md
  - Arquitetura: architecture.md
  - Referência: reference.md

markdown_extensions:
  - admonition
  - tables
  - toc:
      permalink: true
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:pymdownx.superfences.fence_code_format

plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          paths: [src]
```

`docs/reference.md`:

```markdown
# Referência da API

::: novo_f1.transformation.laps
```

### Comandos

```bash
poetry install --with docs
poetry run mkdocs serve            # servidor local em http://127.0.0.1:8000
poetry run mkdocs build --strict   # gera site/ e falha em avisos
```

---

## 8. Git e segurança

### Regras OBRIGATÓRIAS

- **Nunca** commitar senhas, tokens, chaves de API ou credenciais — nem em código, testes, docs ou exemplos.
- Configurações sensíveis vêm de variáveis de ambiente (lidas em `src/novo_f1/config/`).
- `.env` nunca é versionado; `.env.example` é versionado, apenas com nomes de variáveis e valores fictícios.
- Versionar: `pyproject.toml`, `poetry.lock`, `poetry.toml`, `.python-version`, `mkdocs.yml`, `docs/`, `.env.example`.
- Não versionar: `.venv/`, caches, `htmlcov/`, `.coverage`, `site/`, `.env`.
- Antes de commitar, revisar `git diff --staged` em busca de segredos.

### `.gitignore` mínimo

```gitignore
# Ambiente
.venv/
.env
.env.*
!.env.example

# Python
__pycache__/
*.py[cod]
*.egg-info/
build/
dist/

# Ferramentas
.pytest_cache/
.ruff_cache/
.coverage
.coverage.*
htmlcov/
coverage.xml

# Documentação gerada
site/

# IDE / SO
.vscode/
.idea/
.DS_Store
Thumbs.db
```

### Exemplo de configuração via ambiente

```python
# src/novo_f1/config/settings.py
import os

API_BASE_URL = os.getenv("OPENF1_BASE_URL", "https://api.openf1.org/v1")
API_TOKEN = os.getenv("OPENF1_API_TOKEN")  # nunca escrever o valor no código
```

```dotenv
# .env.example
OPENF1_BASE_URL=https://api.openf1.org/v1
OPENF1_API_TOKEN=
```

### CI recomendado (`.github/workflows/ci.yml`)

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version-file: ".python-version"

      - name: Instalar Poetry
        run: pipx install poetry

      - name: Instalar dependências
        run: |
          poetry config virtualenvs.in-project true
          poetry install --with docs

      - name: Validar lock
        run: poetry check --lock

      - name: Ruff (lint)
        run: poetry run ruff check .

      - name: Ruff (formatação)
        run: poetry run ruff format --check .

      - name: Testes + cobertura
        run: poetry run pytest

      - name: Documentação
        run: poetry run mkdocs build --strict
```

> No CI, o `actions/setup-python` substitui o pyenv lendo o mesmo `.python-version`, mantendo a versão consistente.

---

## 9. Regras obrigatórias para agentes de IA

1. **Explorar antes de criar**: listar `src/novo_f1/` e `tests/` e ler os módulos relacionados antes de criar arquivos. Reutilizar código existente.
2. **Respeitar a arquitetura**: código novo apenas em `src/novo_f1/<módulo>/`; testes em `tests/`.
3. **Dependências só via Poetry**: `poetry add` / `poetry add --group dev` / `poetry remove`. Proibido `pip install`. Não adicionar dependência sem necessidade clara.
4. **Respeitar o Python do projeto**: não alterar `.python-version` nem `requires-python` sem pedido explícito.
5. **Ruff limpo**: rodar `ruff format` e `ruff check --fix`; corrigir manualmente o que restar.
6. **Testes**: criar/atualizar testes unitários para toda funcionalidade criada ou alterada.
7. **Cobertura ≥ 50%**: nunca reduzir `fail_under` nem excluir arquivos para atingir a meta.
8. **Documentação**: atualizar `docs/` e `README.md` quando comportamento, comandos ou configuração mudarem.
9. **Segurança**: nunca inserir credenciais; usar variáveis de ambiente e atualizar `.env.example` quando surgir variável nova.
10. **Verificar antes de concluir**: executar o fluxo da seção 1.
11. **Transparência**: relatar explicitamente qualquer verificação não executada ou que falhou, com a saída do erro.
12. **Escopo mínimo**: não reformatar, renomear ou alterar arquivos não relacionados à tarefa.

### Proibições

- `pip install ...` em qualquer contexto do projeto.
- Commitar `.venv/`, `.env`, `htmlcov/`, `site/` ou caches.
- `# noqa` sem código de regra e justificativa.
- Testes que fazem chamadas HTTP reais ou dependem de credenciais.
- Diminuir o limite de cobertura ou usar `pragma: no cover` para contornar a meta.
- Declarar sucesso sem ter executado as verificações.

---

## 10. Checklist de validação final

Uma tarefa só está **concluída** quando todos os itens forem verdadeiros:

- [ ] Código novo/alterado está em `src/novo_f1/`, em módulo coerente com sua responsabilidade.
- [ ] Funções públicas têm type hints e nomes descritivos; não há lógica duplicada.
- [ ] Dependências adicionadas via Poetry; `pyproject.toml` e `poetry.lock` atualizados juntos.
- [ ] `poetry check --lock` passa.
- [ ] `poetry run ruff check .` sem erros.
- [ ] `poetry run ruff format --check .` sem arquivos a reformatar.
- [ ] `poetry run pytest` passa com cobertura ≥ 50%.
- [ ] Testes cobrem a funcionalidade alterada, sem acesso a serviços externos reais.
- [ ] Documentação (`docs/`, `README.md`) atualizada se houve mudança de comportamento/uso.
- [ ] `poetry run mkdocs build --strict` passa (se a documentação foi alterada).
- [ ] Nenhum segredo, `.env` ou artefato local incluído no diff.
- [ ] Verificações não executadas foram informadas explicitamente.
