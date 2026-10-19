# OpenF1 API — Guia de Referência

> Resumo da documentação oficial: <https://openf1.org/docs/>

## 1. Visão geral

A OpenF1 é uma API **open source e não oficial**. Ela não tem vínculo com as empresas da Fórmula 1 e fornece dados de telemetria, cronometragem e sessões.

- **Base URL:** `https://api.openf1.org/v1/`
- **Versão:** `v1` (indicada no caminho da URL)
- **Método:** `GET` em todos os endpoints

## 2. Acesso e autenticação

| Tipo de dado | Acesso |
|---|---|
| Histórico (temporada 2023 em diante) | Gratuito e sem autenticação |
| Tempo real (ao vivo) | Requer assinatura paga (veja o tutorial *Streaming live data with OpenF1*) |

- A documentação não informa limites de requisição (rate limits).
- `meetings` e `sessions` são atualizados diariamente à meia-noite (UTC).

## 3. Formatos de resposta

- **JSON** é o padrão.
- **CSV** está disponível em qualquer endpoint: basta adicionar `csv=true` à query.

```
https://api.openf1.org/v1/laps?session_key=9161&driver_number=63&csv=true
```

## 4. Filtros e consultas

Os filtros são passados como parâmetros na query string e podem ser combinados com `&`.

| Recurso | Sintaxe | Exemplo |
|---|---|---|
| Igualdade | `campo=valor` | `driver_number=1` |
| Comparação | `>`, `<`, `>=`, `<=` | `speed>=315` |
| Intervalo | combine dois operadores | `interval>0&interval<0.005` |
| Múltiplos valores | repita o parâmetro | `driver_number=4&driver_number=81` |
| Mais recente | `latest` em `meeting_key` / `session_key` | `session_key=latest` |
| Strings com espaço | codifique na URL (`%20`) | `flag=BLACK%20AND%20WHITE` |
| Datas | `date>=`, `date<` | `date>=2023-01-01&date<2023-09-01` |

**Observações:**
- Campos do tipo **array** (por exemplo, `segments_sector_1`) **não podem ser filtrados**.
- Datas aceitam qualquer formato compatível com `dateutil.parser.parse` do Python, como `2021-09-10T14:30:20+00:00`, `2021-09-10` ou `10 September 2021`.

## 5. Conceitos-chave

- **Meeting:** um fim de semana de Grande Prêmio ou de testes. Identificado por `meeting_key`.
- **Session:** uma atividade de pista dentro do meeting (Practice, Qualifying, Sprint, Race...). Identificada por `session_key`.
- **Driver:** identificado por `driver_number`.

Para encontrar os dados de um piloto: busque o meeting, depois a session e, por fim, filtre os endpoints de dados por `session_key` e `driver_number`.

**Frequência de amostragem:**

| Endpoint | Frequência |
|---|---|
| `car_data`, `location` | ~3,7 Hz |
| `intervals` | ~a cada 4 segundos |
| `weather` | a cada 1 minuto |

## 6. Endpoints

### Tabela-resumo

| Endpoint | Descrição | Observações |
|---|---|---|
| `/car_data` | Telemetria do carro (velocidade, RPM, marcha, DRS...) | ~3,7 Hz |
| `/championship_drivers` | Classificação do campeonato de pilotos | **Beta**, só corridas |
| `/championship_teams` | Classificação do campeonato de construtores | **Beta**, só corridas |
| `/drivers` | Informações dos pilotos por sessão | — |
| `/intervals` | Diferença para o líder e para o carro à frente | Só corridas |
| `/laps` | Dados detalhados de cada volta | — |
| `/location` | Posição aproximada do carro na pista (x, y, z) | ~3,7 Hz |
| `/meetings` | Fins de semana de GP e testes | Atualizado diariamente |
| `/overtakes` | Ultrapassagens entre pilotos | Só corridas, pode estar incompleto |
| `/pit` | Passagens pelo pit lane | — |
| `/position` | Posição dos pilotos ao longo da sessão | — |
| `/race_control` | Bandeiras, safety car, incidentes, status | — |
| `/sessions` | Sessões de cada meeting | Atualizado diariamente |
| `/session_result` | Resultado final da sessão | Disponível minutos após o resultado oficial |
| `/starting_grid` | Grid de largada | Disponível minutos após o resultado oficial |
| `/stints` | Stints (períodos contínuos) e pneus | — |
| `/team_radio` | Rádios entre piloto e equipe (MP3) | Seleção parcial, quase vazio em 2026 |
| `/weather` | Condições climáticas da pista | A cada 1 minuto |

---

### 6.1 `/car_data`
Telemetria do carro a ~3,7 Hz.

| Campo | Descrição |
|---|---|
| `brake` | 100 = freio pressionado, 0 = não |
| `date` | Data/hora (UTC, ISO 8601) |
| `driver_number` | Número do piloto |
| `drs` | Status do DRS (ver [Tabelas de referência](#7-tabelas-de-referência)) |
| `n_gear` | Marcha (0 = neutro) |
| `rpm` | Rotações por minuto |
| `speed` | Velocidade (km/h) |
| `throttle` | Acelerador (%) |
| `meeting_key`, `session_key` | Chaves de referência |

```
https://api.openf1.org/v1/car_data?driver_number=55&session_key=9159&speed>=315
```

### 6.2 `/championship_drivers` (beta)
Classificação do campeonato de pilotos. Disponível só para sessões de corrida.

| Campo | Descrição |
|---|---|
| `driver_number` | Número do piloto |
| `points_start` / `points_current` | Pontos antes da sessão / atuais |
| `position_start` / `position_current` | Posição antes da sessão / atual |
| `meeting_key`, `session_key` | Chaves de referência |

```
https://api.openf1.org/v1/championship_drivers?session_key=9839&driver_number=4&driver_number=81
```

### 6.3 `/championship_teams` (beta)
Classificação do campeonato de construtores. Disponível só para sessões de corrida.

| Campo | Descrição |
|---|---|
| `team_name` | Nome da equipe |
| `points_start` / `points_current` | Pontos antes da sessão / atuais |
| `position_start` / `position_current` | Posição antes da sessão / atual |
| `meeting_key`, `session_key` | Chaves de referência |

```
https://api.openf1.org/v1/championship_teams?session_key=9839&team_name=McLaren
```

### 6.4 `/drivers`
Informações dos pilotos em cada sessão.

| Campo | Descrição |
|---|---|
| `driver_number` | Número do piloto |
| `broadcast_name` | Nome usado na transmissão (ex.: `M VERSTAPPEN`) |
| `first_name`, `last_name`, `full_name` | Nomes |
| `name_acronym` | Sigla de 3 letras (ex.: `VER`) |
| `team_name` | Equipe |
| `team_colour` | Cor da equipe (hex `RRGGBB`) |
| `headshot_url` | URL da foto do piloto |
| `country_code` | ⚠️ Depreciado (removido após 2026) |
| `meeting_key`, `session_key` | Chaves de referência |

```
https://api.openf1.org/v1/drivers?driver_number=1&session_key=9158
```

### 6.5 `/intervals`
Diferença de tempo entre os pilotos. Disponível só em corridas.

| Campo | Descrição |
|---|---|
| `date` | Data/hora |
| `driver_number` | Número do piloto |
| `gap_to_leader` | Diferença para o líder (s). `+1 LAP` se tomou volta e `null` para o líder |
| `interval` | Diferença para o carro à frente (s), com as mesmas convenções |
| `meeting_key`, `session_key` | Chaves de referência |

```
https://api.openf1.org/v1/intervals?session_key=9165&interval>0&interval<0.005
```

### 6.6 `/laps`
Dados detalhados de cada volta.

| Campo | Descrição |
|---|---|
| `lap_number` | Número da volta |
| `lap_duration` | Tempo total da volta (s) |
| `date_start` | Início aproximado da volta |
| `duration_sector_1/2/3` | Tempo de cada setor (s) |
| `segments_sector_1/2/3` | Status dos minissetores (array, ver [Tabelas de referência](#7-tabelas-de-referência)) |
| `i1_speed`, `i2_speed` | Velocidade nos pontos intermediários (km/h) |
| `st_speed` | Velocidade no speed trap (km/h) |
| `is_pit_out_lap` | Se é volta de saída dos boxes |
| `driver_number`, `meeting_key`, `session_key` | Chaves de referência |

```
https://api.openf1.org/v1/laps?session_key=9161&driver_number=63&lap_number=8
```

### 6.7 `/location`
Posição aproximada do carro na pista a ~3,7 Hz. Indica o progresso ao longo do traçado, mas não a posição lateral. A origem (0,0,0) é arbitrária.

| Campo | Descrição |
|---|---|
| `x`, `y`, `z` | Coordenadas |
| `date` | Data/hora |
| `driver_number`, `meeting_key`, `session_key` | Chaves de referência |

```
https://api.openf1.org/v1/location?session_key=9161&driver_number=81&date>2023-09-16T13:03:35.200&date<2023-09-16T13:03:35.800
```

### 6.8 `/meetings`
Fins de semana de Grande Prêmio ou de testes. Cada meeting contém várias sessões.

| Campo | Descrição |
|---|---|
| `meeting_key` | Identificador do meeting |
| `meeting_name`, `meeting_official_name` | Nome curto / oficial |
| `year` | Temporada |
| `date_start`, `date_end`, `gmt_offset` | Datas e fuso horário |
| `location`, `country_name`, `country_code`, `country_key`, `country_flag` | Local e país |
| `circuit_key`, `circuit_short_name` | Circuito |
| `circuit_type` | `Permanent`, `Temporary - Street` ou `Temporary - Road` |
| `circuit_image`, `circuit_info_url` | Imagem e JSON do circuito (MultiViewer) |
| `is_cancelled` | Se foi cancelado |

```
https://api.openf1.org/v1/meetings?year=2026&country_name=Singapore
```

### 6.9 `/overtakes`
Trocas de posição entre dois pilotos. Inclui mudanças causadas por pit stops e por punições pós-corrida. Disponível só em corridas e pode estar incompleto.

| Campo | Descrição |
|---|---|
| `overtaking_driver_number` | Piloto que ultrapassou |
| `overtaken_driver_number` | Piloto ultrapassado |
| `position` | Posição de quem ultrapassou, após a manobra |
| `date` | Data/hora |
| `meeting_key`, `session_key` | Chaves de referência |

```
https://api.openf1.org/v1/overtakes?session_key=9636&overtaking_driver_number=63&overtaken_driver_number=4&position=1
```

### 6.10 `/pit`
Passagens dos carros pelo pit lane.

| Campo | Descrição |
|---|---|
| `lap_number` | Volta da parada |
| `lane_duration` | Tempo total no pit lane (s) |
| `stop_duration` | Tempo parado (s). Disponível a partir do GP dos EUA de 2024 |
| `pit_duration` | ⚠️ Depreciado, igual a `lane_duration` (removido após 2026) |
| `date`, `driver_number`, `meeting_key`, `session_key` | Chaves de referência |

```
https://api.openf1.org/v1/pit?session_key=9877&stop_duration<2.3
```

### 6.11 `/position`
Posição dos pilotos ao longo da sessão: a posição inicial e cada mudança.

| Campo | Descrição |
|---|---|
| `position` | Posição (começa em 1) |
| `date`, `driver_number`, `meeting_key`, `session_key` | Chaves de referência |

```
https://api.openf1.org/v1/position?meeting_key=1217&driver_number=40&position<=3
```

### 6.12 `/race_control`
Mensagens da direção de prova: bandeiras, safety car, incidentes e status da sessão.

| Campo | Descrição |
|---|---|
| `category` | `SessionStatus`, `CarEvent`, `Drs`, `Flag`, `SafetyCar`... |
| `flag` | `GREEN`, `YELLOW`, `DOUBLE YELLOW`, `CHEQUERED`, `BLACK AND WHITE`... |
| `message` | Texto da mensagem |
| `scope` | `Track`, `Driver`, `Sector`... |
| `sector` | Setor afetado |
| `lap_number` | Volta (em corridas) |
| `qualifying_phase` | 1, 2 ou 3 (Q1/Q2/Q3) |
| `date`, `driver_number`, `meeting_key`, `session_key` | Chaves de referência |

```
https://api.openf1.org/v1/race_control?flag=BLACK%20AND%20WHITE&driver_number=1&date>=2023-01-01&date<2023-09-01
```

### 6.13 `/sessions`
Sessões de cada meeting (treinos, classificação, sprint, corrida...).

| Campo | Descrição |
|---|---|
| `session_key` | Identificador da sessão |
| `session_name` | Ex.: `Practice 1`, `Qualifying`, `Sprint Qualifying`, `Race` |
| `session_type` | Tipo da sessão |
| `date_start`, `date_end`, `gmt_offset` | Datas e fuso |
| `year`, `location`, `country_*`, `circuit_*` | Contexto |
| `is_cancelled` | Se foi cancelada |
| `meeting_key` | Meeting ao qual pertence |

```
https://api.openf1.org/v1/sessions?country_name=Belgium&session_name=Sprint%20Qualifying&year=2023
```

### 6.14 `/session_result`
Classificação final da sessão. Fica disponível alguns minutos após a publicação do resultado oficial.

| Campo | Descrição |
|---|---|
| `position` | Posição final |
| `duration` | Melhor volta (treino/quali) ou tempo total (corrida). Na classificação, um array com Q1–Q3 |
| `gap_to_leader` | Diferença (s), `+N LAP(S)` ou array Q1–Q3 |
| `number_of_laps` | Voltas completadas |
| `dnf`, `dns`, `dsq` | Abandonou / não largou / desclassificado |
| `driver_number`, `meeting_key`, `session_key` | Chaves de referência |

```
https://api.openf1.org/v1/session_result?session_key=7782&position<=3
```

### 6.15 `/starting_grid`
Grid de largada da corrida. Fica disponível alguns minutos após a publicação do resultado oficial.

| Campo | Descrição |
|---|---|
| `position` | Posição no grid |
| `lap_duration` | Tempo da volta de classificação (s) |
| `driver_number`, `meeting_key`, `session_key` | Chaves de referência |

```
https://api.openf1.org/v1/starting_grid?session_key=7783&position<=3
```

### 6.16 `/stints`
Períodos de pilotagem contínua de um piloto na sessão, com o pneu usado em cada um.

| Campo | Descrição |
|---|---|
| `stint_number` | Número do stint |
| `compound` | `SOFT`, `MEDIUM`, `HARD`, `INTERMEDIATE`, `WET`... |
| `lap_start`, `lap_end` | Voltas inicial e final |
| `tyre_age_at_start` | Idade do pneu no início (voltas) |
| `driver_number`, `meeting_key`, `session_key` | Chaves de referência |

```
https://api.openf1.org/v1/stints?session_key=9165&tyre_age_at_start>=3
```

### 6.17 `/team_radio`
Seleção de rádios entre piloto e equipe. Não é um registro completo, e a maioria dos eventos de 2026 não tem dados.

| Campo | Descrição |
|---|---|
| `recording_url` | URL do áudio (MP3) |
| `date`, `driver_number`, `meeting_key`, `session_key` | Chaves de referência |

```
https://api.openf1.org/v1/team_radio?session_key=9158&driver_number=11
```

### 6.18 `/weather`
Condições climáticas da pista, atualizadas a cada minuto.

| Campo | Descrição |
|---|---|
| `air_temperature` | Temperatura do ar (°C) |
| `track_temperature` | Temperatura da pista (°C) |
| `humidity` | Umidade (%) |
| `pressure` | Pressão (mbar) |
| `rainfall` | Indicador de chuva |
| `wind_direction` | Direção do vento (0–359°) |
| `wind_speed` | Velocidade do vento (m/s) |
| `date`, `meeting_key`, `session_key` | Chaves de referência |

```
https://api.openf1.org/v1/weather?meeting_key=1208&wind_direction>=130&track_temperature>=52
```

## 7. Tabelas de referência

### DRS (`car_data.drs`)

| Valor | Significado |
|---|---|
| 0, 1 | DRS desligado |
| 8 | Detectado, habilitado ao entrar na zona de ativação |
| 10, 12, 14 | DRS ligado |
| 2, 3, 9 | Desconhecido |

### Segmentos de volta (`laps.segments_sector_*`)

| Valor | Cor/Significado |
|---|---|
| 0 | Não disponível |
| 2048 | Amarelo |
| 2049 | Verde |
| 2051 | Roxo |
| 2064 | Pit lane |
| 2050, 2052, 2068 | Desconhecido |

> Os segmentos não estão disponíveis em corridas e podem não bater com as cores exibidas na TV.

## 8. Depreciações e limitações

- ⚠️ `drivers.country_code` e `pit.pit_duration` serão **removidos ao fim da temporada 2026**. Use `lane_duration` no lugar de `pit_duration`.
- `pit.stop_duration` só existe a partir do **GP dos EUA de 2024**.
- `overtakes` e `team_radio` podem ter **dados incompletos**.
- `championship_drivers` e `championship_teams` estão em **beta**.
- Endpoints disponíveis **só em corridas**: `championship_*`, `intervals` e `overtakes`.

## 9. Exemplo rápido em Python

```python
from urllib.request import urlopen
import json

BASE_URL = "https://api.openf1.org/v1"

# Sessão mais recente
with urlopen(f"{BASE_URL}/sessions?session_key=latest") as resp:
    sessions = json.load(resp)
session = sessions[0]
print(session["session_name"], session["location"], session["year"])

# Pilotos dessa sessão
with urlopen(f"{BASE_URL}/drivers?session_key={session['session_key']}") as resp:
    drivers = json.load(resp)
for d in drivers:
    print(d["driver_number"], d["name_acronym"], d["team_name"])
```

Com `pandas`, o formato CSV pode ser lido direto:

```python
import pandas as pd

df = pd.read_csv(
    "https://api.openf1.org/v1/laps?session_key=9161&driver_number=63&csv=true"
)
```

## 10. Links úteis

- Documentação oficial: <https://openf1.org/docs/>
- Streaming de dados ao vivo: <https://openf1.org/auth.html>
- Repositório e suporte (Discussions/Issues): <https://github.com/br-g/openf1>
