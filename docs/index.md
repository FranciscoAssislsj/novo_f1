# Novo F1

Dashboard em **Streamlit** para explorar os dados históricos de Fórmula 1 da
[OpenF1 API](https://openf1.org) (temporadas de 2023 em diante, gratuitas e sem
autenticação). Os dados baixados ficam em **cache local em Parquet**, então cada
sessão é buscada na API uma única vez.

!!! note "Fonte de dados"
    A OpenF1 é uma API **open source e não oficial**, sem vínculo com as
    empresas da Fórmula 1. Dados ao vivo exigem assinatura e estão fora do
    escopo deste projeto.

## O que o dashboard mostra

| Página | Conteúdo |
|---|---|
| Calendário | Linha do tempo da temporada, sprints, cancelamentos e sessões de cada GP |
| Resultados | Classificação (Q1–Q3 na classificação), grid x chegada e campeonato (beta) |
| Voltas | Tempos por volta dos pilotos escolhidos, melhores setores e ritmo por stint |
| Estratégia | Gantt de pneus, pit stops, posições por volta, gap para o líder e ultrapassagens |
| Telemetria | Velocidade/acelerador/freio/marcha da volta, traçado x/y, clima e direção de prova |

A barra lateral (temporada → Grande Prêmio → sessão → pilotos) é comum a todas
as páginas.

## Próximos passos

- [Instalação](installation.md): pyenv, Poetry e dependências.
- [Uso](usage.md): `sync`, `dashboard` e variáveis de ambiente.
- [Arquitetura](architecture.md): camadas e fluxo de dados.
- [Referência](reference.md): API dos módulos.
