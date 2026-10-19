# Instalação

## Pré-requisitos

- [pyenv](https://github.com/pyenv/pyenv) (no Windows, [pyenv-win](https://github.com/pyenv-win/pyenv-win))
- [Poetry](https://python-poetry.org) 2.x
- Git

## Passo a passo

```bash
git clone <url-do-repositório> novo_f1
cd novo_f1

# 1. Python do projeto (lido de .python-version)
pyenv install 3.14.2
pyenv version            # deve mostrar 3.14.2

# 2. Ambiente virtual em .venv/ (poetry.toml já define in-project = true)
poetry env use "$(pyenv which python)"      # Bash
# poetry env use (pyenv which python)       # PowerShell

# 3. Dependências (produção + dev; docs é opcional)
poetry install
poetry install --with docs   # para gerar a documentação
```

!!! warning "Nunca use `pip install`"
    Todas as dependências são gerenciadas pelo Poetry (`poetry add`,
    `poetry add --group dev`, `poetry remove`).

!!! tip "`VIRTUAL_ENV` herdado do shell"
    Se a variável `VIRTUAL_ENV` estiver definida no seu terminal (apontando
    para outro Python), o Poetry vai usá-la em vez de criar a `.venv` do
    projeto. Remova-a antes (`unset VIRTUAL_ENV` no Bash ou
    `Remove-Item Env:VIRTUAL_ENV` no PowerShell) e confira com
    `poetry env info -p`.

## Configuração

Copie o exemplo e ajuste, se necessário. Todos os valores têm padrão, então o
arquivo é opcional:

```bash
cp .env.example .env
```

As variáveis são lidas do ambiente do processo (veja [Uso](usage.md#variaveis-de-ambiente)).
O `.env` **não** é carregado automaticamente. Exporte as variáveis no shell ou
use a integração de `.env` do seu editor.

## Verificação

```bash
poetry run ruff check .
poetry run ruff format --check .
poetry run pytest            # cobertura mínima de 50%
poetry check --lock
poetry run mkdocs build --strict
```
