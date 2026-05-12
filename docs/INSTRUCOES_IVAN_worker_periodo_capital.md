# Instruções para o Worker — Período e Capital Dinâmicos
**Backtest Pro · alphaQuant**

---

## O que mudou no frontend

O frontend agora envia dois novos campos no JSON de configuração do backtest. Antes, período e capital eram valores fixos hardcoded no backend. A partir de agora, o usuário escolhe ambos na tela de confirmação antes de rodar.

O payload que chega na Edge Function `submit-backtest` e é gravado na coluna `config` da tabela `backtests` passou a incluir:

```json
{
  "cfg": {
    "...outros campos existentes...",

    "backtest_period": {
      "date_from": "2022-03-15",
      "date_to":   "2026-05-12"
    },
    "initial_capital": 25000,
    "capital_currency": "R$"
  }
}
```

Esses três campos são sempre enviados. Nunca chegam `null` ou ausentes — o frontend já garante isso com validação antes de submeter.

---

## Formatos exatos

| Campo | Tipo | Formato | Exemplo |
|---|---|---|---|
| `backtest_period.date_from` | string | ISO 8601 `YYYY-MM-DD` | `"2022-03-15"` |
| `backtest_period.date_to` | string | ISO 8601 `YYYY-MM-DD` | `"2026-05-12"` |
| `initial_capital` | number | float, sem formatação | `25000` ou `25000.0` |
| `capital_currency` | string | símbolo da moeda | `"R$"`, `"USD"`, `"EUR"`, `"GBP"`, `"JPY"`, `"AUD"`, `"HKD"` |

**Observação sobre `capital_currency`:** a moeda varia conforme o ativo selecionado. Ativos brasileiros (WIN, WDO, ações B3, ETFs B3) sempre enviam `"R$"`. Forex e ações americanas enviam `"USD"`. Índices internacionais podem enviar `"EUR"`, `"GBP"`, `"JPY"`, `"AUD"` ou `"HKD"` dependendo do país do índice.

---

## O que precisa mudar no worker

O problema é que atualmente `pipeline.run()` recebe o `frontend_cfg` mas **ignora** os campos de período e capital que vêm dele. Esses valores são passados como parâmetros fixos na instância do `BacktestPipeline`, e dentro de `build_backtest_json` o capital também está hardcoded em `10000.0`.

São três mudanças, todas cirúrgicas.

---

### Mudança 1 — `cfg_to_json.py` · função `build_backtest_json`

**Situação atual:** `from_date`, `to_date` e `deposit` são parâmetros da função com defaults fixos. O campo `from_date` default é `"2019.01.02"` (hardcoded). `deposit` default é `10000`.

**O que fazer:** ler os valores diretamente do `cfg` quando presentes, convertendo o formato ISO `YYYY-MM-DD` para o formato MT5 `YYYY.MM.DD`.

```python
# Substitua a lógica de from_date / to_date / deposit dentro de build_backtest_json:

# Período: ler do cfg se disponível, senão usar parâmetros/defaults
backtest_period = cfg.get("backtest_period", {})

if backtest_period.get("date_from"):
    # Converter ISO (YYYY-MM-DD) para MT5 (YYYY.MM.DD)
    from_date = backtest_period["date_from"].replace("-", ".")
else:
    # Manter o parâmetro recebido (ou o default da função)
    pass  # from_date já está definido pelo parâmetro

if backtest_period.get("date_to"):
    to_date = backtest_period["date_to"].replace("-", ".")
else:
    if to_date is None:
        to_date = datetime.now().strftime("%Y.%m.%d")

# Capital: ler do cfg se disponível
if cfg.get("initial_capital") is not None:
    deposit = int(cfg["initial_capital"])
# else: manter o parâmetro recebido (ou o default da função)
```

**Também nesta função:** `InpInitialAlloc` está hardcoded em `10000.0` dentro de `convert_cfg_to_ea_params`. Precisa receber o valor do usuário:

```python
# Linha atual (~linha 344):
params["InpInitialAlloc"] = 10000.0

# Substituir por (o deposit já estará disponível no escopo de build_backtest_json):
params["InpInitialAlloc"] = float(deposit)
```

Para isso funcionar, `convert_cfg_to_ea_params` precisa receber `deposit` como parâmetro, ou `build_backtest_json` deve sobrescrever `InpInitialAlloc` após chamar `convert_cfg_to_ea_params`. A segunda opção é mais simples:

```python
# Em build_backtest_json, após chamar convert_cfg_to_ea_params(cfg):
ea_params = convert_cfg_to_ea_params(cfg)
ea_params["InpInitialAlloc"] = float(deposit)  # sobrescreve o hardcoded
```

---

### Mudança 2 — `cfg_to_json.py` · função `build_backtest_json` · moeda

**Situação atual:** a moeda é determinada pelo campo `market` do cfg:

```python
market = cfg.get("market", "local")
currency = "BRL" if market == "local" else "USD"
```

**O problema:** isso não funciona para índices internacionais como DE40 (EUR), UK100 (GBP), JP225 (JPY), etc. O frontend agora envia `capital_currency` diretamente, eliminando a ambiguidade.

**O que fazer:**

```python
# Substituir a lógica de currency por:
capital_currency = cfg.get("capital_currency", None)

if capital_currency:
    # Mapear símbolo do frontend para código ISO 4217 que o MT5 aceita
    currency_map = {
        "R$":  "BRL",
        "USD": "USD",
        "EUR": "EUR",
        "GBP": "GBP",
        "JPY": "JPY",
        "AUD": "AUD",
        "HKD": "HKD",
    }
    currency = currency_map.get(capital_currency, "USD")
else:
    # Fallback para lógica anterior (compatibilidade com configs antigas sem o campo)
    market = cfg.get("market", "local")
    currency = "BRL" if market == "local" else "USD"
```

---

### Mudança 3 — `worker.py` · instanciação do `BacktestPipeline`

**Situação atual:** o worker cria o pipeline com valores fixos:

```python
self.pipeline = BacktestPipeline(
    use_cache=True,
    timeout=MAX_BACKTEST_TIMEOUT,
)
```

E em `process_job`, chama:

```python
result = self.pipeline.run(frontend_cfg)
```

**Depois das mudanças 1 e 2**, `build_backtest_json` vai ler período e capital diretamente do `frontend_cfg`, então o worker não precisa mudar — desde que `frontend_cfg` seja o `cfg` do payload (que já inclui os novos campos).

Confirmar que `frontend_cfg` em `process_job` é exatamente `bt.get("config", {})`, ou seja, o objeto `cfg` gravado pelo frontend. Se sim, nenhuma mudança adicional é necessária no `worker.py`.

---

## Validação defensiva no backend

O frontend já valida antes de submeter, mas adicionar defesa aqui custa pouco:

```python
from datetime import date, timedelta

def validate_backtest_period(cfg: dict):
    period = cfg.get("backtest_period", {})
    date_from_str = period.get("date_from")
    date_to_str   = period.get("date_to")

    if not date_from_str or not date_to_str:
        return  # sem os campos, deixar o comportamento padrão/antigo funcionar

    date_from = date.fromisoformat(date_from_str)
    date_to   = date.fromisoformat(date_to_str)
    today     = date.today()
    min_date  = today - timedelta(days=5 * 366)

    assert date_from >= min_date, f"date_from excede limite de 5 anos: {date_from}"
    assert date_to   <= today,    f"date_to é futuro: {date_to}"
    assert date_from  < date_to,  "date_from deve ser anterior a date_to"
    assert (date_to - date_from).days >= 30, "período mínimo é 30 dias"
```

Chamar antes de `build_backtest_json` em `pipeline.py`.

---

## Checksum de cache

O checksum já inclui `from_date`, `to_date` e `deposit` na chave de cache — então backtests com período ou capital diferente são tratados como jobs distintos. Nenhuma mudança necessária em `compute_checksum`.

---

## Resumo das mudanças

| Arquivo | O que muda |
|---|---|
| `cfg_to_json.py` · `build_backtest_json` | Ler `backtest_period.date_from/to` do cfg e converter para formato MT5 |
| `cfg_to_json.py` · `build_backtest_json` | Ler `initial_capital` do cfg como `deposit` |
| `cfg_to_json.py` · `build_backtest_json` | Sobrescrever `InpInitialAlloc` nos ea_params com o valor real |
| `cfg_to_json.py` · `build_backtest_json` | Ler `capital_currency` do cfg para determinar `currency` com mapa completo |
| `worker.py` | Sem mudança, desde que `frontend_cfg = bt["config"]` já contenha os novos campos |
| `pipeline.py` | Sem mudança estrutural — validação defensiva opcional |

---

*Backtest Pro · alphaQuant · Maio 2026*
