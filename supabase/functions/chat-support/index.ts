import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

interface ChatRequest {
  user_id: string;
  user_name: string;
  user_email: string;
  user_plan: string;
  user_backtests_used: number;
  user_backtests_limit: number;
  category: string;
  message: string;
  conversation_history: Array<{ role: "user" | "assistant"; content: string }>;
}

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: CORS_HEADERS });
  }

  if (req.method !== "POST") {
    return new Response("Method Not Allowed", { status: 405, headers: CORS_HEADERS });
  }

  // Validar sessão
  const authHeader = req.headers.get("Authorization");
  if (!authHeader) {
    return new Response(JSON.stringify({ error: "Não autorizado" }), {
      status: 401, headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
    });
  }

  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_ANON_KEY")!,
    { global: { headers: { Authorization: authHeader } } }
  );

  const { data: { user }, error: authError } = await supabase.auth.getUser();
  if (authError || !user) {
    return new Response(JSON.stringify({ error: "Sessão inválida" }), {
      status: 401, headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
    });
  }

  let body: ChatRequest;
  try {
    body = await req.json() as ChatRequest;
  } catch {
    return new Response(JSON.stringify({ error: "Payload inválido" }), {
      status: 400, headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
    });
  }

  // Validar que o user_id do payload corresponde à sessão
  if (body.user_id !== user.id) {
    return new Response(JSON.stringify({ error: "user_id não corresponde à sessão" }), {
      status: 403, headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
    });
  }

  const systemPrompt = `Você é o assistente de suporte do Backtest Pro, produto da alphaQuant.

CONTEXTO DO USUÁRIO ATUAL
Nome: ${body.user_name}
Email: ${body.user_email}
Plano: ${body.user_plan}
Backtests utilizados: ${body.user_backtests_used} de ${body.user_backtests_limit}
Categoria do atendimento: ${body.category}

SOBRE O PRODUTO
O Backtest Pro é uma plataforma web que permite traders de varejo testarem estratégias
de análise técnica usando dados históricos reais, sem precisar programar.

Como funciona:
- O usuário configura uma estratégia através de um wizard de 5 passos:
  Mercado > Condições > Gatilho > Risco > Gestão
- Cada passo apresenta opções visuais — sem código, sem instalação
- O usuário define o período específico que deseja testar (dentro dos 5 anos disponíveis)
- O sistema roda o backtest e retorna o resultado completo

URL do produto: https://www.backtestpro.com.br

ATIVOS SUPORTADOS
- WIN (mini índice), WDO (mini dólar), IND (índice cheio), DOL (dólar cheio)
- Todas as ações disponíveis na B3

PLANOS E PREÇOS
Free trial: 5 backtests gratuitos (todos salvos automaticamente)

Starter:  100 backtests/mês | 20 estratégias salvas
  Mensal: R$109,90 (cobrança avulsa, não recorrente)
  Semestral: R$599,40 | Anual: R$1.044,00
  (semestral e anual: pagamento à vista ou parcelado em até 12x com juros do gateway)

Advanced: 150 backtests/mês | 40 estratégias salvas
  Mensal: R$139,90 (cobrança avulsa, não recorrente)
  Semestral: R$779,40 | Anual: R$1.318,80
  (semestral e anual: pagamento à vista ou parcelado em até 12x com juros do gateway)

Elite: 200 backtests/mês | 60 estratégias salvas
  Mensal: R$159,90 (cobrança avulsa, não recorrente)
  Semestral: R$899,40 | Anual: R$1.558,80
  (semestral e anual: pagamento à vista ou parcelado em até 12x com juros do gateway)

Pagamento: Pix (principal) ou cartão de crédito.

INDICADORES E RECURSOS DISPONÍVEIS
Osciladores: RSI/IFR, Estocástico, CCI, Williams %R, MACD
Tendência: SMA, EMA, Bandas de Bollinger, VWAP, SAR Parabólico, ADX, HiLo
Volume: Volume, OBV
Smart Money Concepts: FVG, BoS, CHoCH, Order Block, Liquidity Sweep
Fibonacci: retrações automáticas com gatilho configurável
Padrões de preço: Gap e outros padrões gráficos
Estratégias famosas pré-configuradas: modelos prontos baseados em estratégias
  consagradas de análise técnica

GLOSSÁRIO DE MÉTRICAS
Taxa de acerto: % de operações que fecharam no lucro. 40% pode ser excelente
  se o ganho médio for maior que a perda média — depende do risco/retorno.
Profit Factor: total ganho / total perdido. Acima de 1.0 = lucrativo.
  Acima de 1.5 = sólido. Abaixo de 1.0 = deficitário.
Drawdown: maior queda do capital desde o pico. Mede o pior momento da estratégia.
Curva de equity: gráfico que mostra a evolução do capital ao longo do tempo.

COMO SE COMPORTAR
- Tom: direto, sem rodeios, sem linguagem de guru
- Respostas curtas — máximo 5 linhas por resposta
- Nunca usar o termo "setup" — usar sempre "estratégia"
- Nunca revelar qual tecnologia roda os backtests por baixo
- Nunca prometer resultado — backtest mostra o passado, não garante o futuro
- Nunca dizer "usuário monta a estratégia" — dizer "usuário configura a estratégia"

PROTOCOLO — BACKTEST TRAVADO OU COM ERRO
Executar os passos em ordem. Só escalonar após todos falharem.

Passo 1: Perguntar se apareceu mensagem de erro ou se ficou rodando sem retornar.
Passo 2 (timeout): Orientar a fechar a aba, acessar novamente e verificar o histórico.
  Se o resultado estiver salvo: era problema de exibição, resolvido.
Passo 3: Teste em aba anônima (Ctrl+Shift+N Chrome / Ctrl+Shift+P Firefox).
  Se funcionar na aba anônima: limpar cache do browser normal.
Passo 4: Simplificar a estratégia removendo uma condição por vez.
Passo 5: Escalonar apenas se todos os passos anteriores falharem.

QUANDO ESCALONAR IMEDIATAMENTE (sem protocolo)
- Pagamento realizado mas acesso não liberado
- Solicitação de reembolso ou estorno
- Usuário claramente insatisfeito e escalando o tom
- Qualquer dúvida jurídica ou contratual
- Problema técnico persistente após todos os passos do protocolo

IMPORTANTE: Quando decidir escalonar, incluir exatamente a string [ESCALONAR]
no final da sua resposta. O sistema detecta essa string e aciona o fluxo de
coleta do WhatsApp automaticamente. Não mencionar isso ao usuário.`;

  const anthropicKey = Deno.env.get("ANTHROPIC_API_KEY");
  if (!anthropicKey) {
    return new Response(JSON.stringify({ error: "Serviço temporariamente indisponível" }), {
      status: 503, headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
    });
  }

  const messages = [
    ...body.conversation_history,
    { role: "user" as const, content: body.message },
  ];

  const claudeRes = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": anthropicKey,
      "anthropic-version": "2023-06-01",
    },
    body: JSON.stringify({
      model: "claude-haiku-4-5-20251001",
      max_tokens: 512,
      system: systemPrompt,
      messages,
    }),
  });

  if (!claudeRes.ok) {
    const errText = await claudeRes.text();
    console.error("[chat-support] Erro Claude API:", claudeRes.status, errText);
    return new Response(JSON.stringify({ error: "Erro ao processar sua mensagem. Tente novamente." }), {
      status: 502, headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
    });
  }

  const claudeData = await claudeRes.json();
  const rawReply: string = claudeData.content?.[0]?.text ?? "";

  const shouldEscalate = rawReply.includes("[ESCALONAR]");
  const cleanReply = rawReply.replace("[ESCALONAR]", "").trim();

  return new Response(
    JSON.stringify({ message: cleanReply, escalate: shouldEscalate }),
    { status: 200, headers: { ...CORS_HEADERS, "Content-Type": "application/json" } }
  );
});
