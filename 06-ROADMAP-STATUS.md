# BACKTEST PRO — Roadmap e Status Atual

## STATUS ATUAL (Março 2026)

### Concluído ✅
- Definição completa do produto e posicionamento
- Decisão arquitetural: EA universal parametrizado (sem geração de código)
- Especificação detalhada da interface UX (wizard de 5 passos)
- Design system definido (paleta, tipografia, componentes)
- Protótipo visual construído (originalmente React/JSX, convertido para HTML estático)
- Frontend versionado no GitHub e deployado na Vercel
- **URL de produção: https://backtestpro-app.vercel.app**
- Arquivo principal: `index.html` (HTML + CSS + JS inline, single-file)
- Modelo de negócio definido (2 tiers, cobranças avulsas)
- Gateway de pagamento escolhido (Mercado Pago, Pix como método principal)
- Banco de dados escolhido (Supabase: Postgres + Auth)
- **Workflow Git definido:** branch `dev` criada, fluxo `feature → dev → main` estabelecido (ver `07-GIT-WORKFLOW.md`)

### Próximos passos imediatos 🔄
- Configurar Supabase (criar tabelas, configurar auth)
- Integrar autenticação no frontend
- Integrar Mercado Pago para cobranças
- Implementar controle de acesso (verificar assinatura ativa)
- Implementar lógica de free trial (3 backtests grátis)
- Construir o EA Universal em MQL5
- Definir infra para MT5 headless (servidor)
- Conectar frontend → backend → MT5

---

## ROADMAP DE PRODUTO

### V1 — MVP
**Objetivo:** Produto funcional mínimo que um cliente pode usar para testar um setup.

**Escopo:**
- Wizard de 5 passos completo
- Indicadores essenciais: RSI, SMA, EMA, MACD, Bollinger, Volume
- Ativos: Mini Índice (WIN), Mini Dólar (WDO)
- Timeframes: 1min, 5min, 15min, 60min, Diário
- Stop: fixo, candle de sinal
- Alvo: fixo, múltiplo do risco
- Gestão: trailing stop, parcial básica
- Resultado: curva de equity, métricas essenciais, drawdown
- Autenticação e controle de acesso
- Pagamento via Mercado Pago (Pix + cartão)
- Free trial: 3 backtests

### V2 — Expansão
- Mais indicadores (Estocástico, CCI, Williams, SAR, VWAP, OBV)
- Mais ativos (Índice Cheio, Dólar Cheio)
- Saída por condição (indicador)
- Stop por N candles
- Filtro de horário refinado
- Histórico de backtests salvos na conta do usuário
- Compartilhamento de resultado (imagem para redes sociais)
- Exportação de relatório PDF (tier Pro)

### V3 — Otimização (Tier Pro)
- Otimização de parâmetros (testa variações automaticamente)
- Teste de robustez / Walk Forward simplificado
- Aviso de overfitting
- Comparação lado a lado de variações
- Dashboard do usuário com histórico

### V4 — Integração com Fábrica
- "Quer rodar essa estratégia ao vivo?" → gera EA a partir da configuração validada
- Funil completo Backtest Pro → Fábrica de Estratégias

---

## DEPENDÊNCIAS TÉCNICAS CRÍTICAS

1. **MT5 Headless no servidor** — Sem isso, não há backtest real. Precisa definir: VPS com Windows? Docker? Licenciamento MetaQuotes? Isso é o gargalo técnico principal.

2. **EA Universal** — Precisa ser construído sobre as bibliotecas MQL5 existentes. É o motor do produto. Sem ele, o frontend é só uma casca bonita.

3. **Dados históricos** — Precisam estar pré-carregados e atualizados no servidor. Mini índice e mini dólar, pelo menos 5 anos de dados em múltiplos timeframes.

4. **API intermediária** — Algo entre o frontend (Vercel) e o MT5 precisa receber o JSON de configuração, enviar pro MT5, aguardar o resultado, e devolver pro frontend. Pode ser uma API simples em Node.js rodando no mesmo servidor do MT5, ou Supabase Edge Functions.
