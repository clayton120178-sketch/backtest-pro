"""
BacktestPro - Parser de Resultado do MT5 Strategy Tester

O MT5 gera um arquivo XML quando configurado com Report= no .ini.
O XML contem metricas do backtest e lista de trades.

Formato XML do MT5 Strategy Tester:
<Strategy_Tester_Report>
  <Summary>
    <TotalNetProfit>1234.56</TotalNetProfit>
    <GrossProfit>5000.00</GrossProfit>
    <GrossLoss>-3765.44</GrossLoss>
    <ProfitFactor>1.33</ProfitFactor>
    <ExpectedPayoff>12.35</ExpectedPayoff>
    <MaximalDrawdownMoney>500.00</MaximalDrawdownMoney>
    <MaximalDrawdownPercent>5.00</MaximalDrawdownPercent>
    <TotalTrades>100</TotalTrades>
    <WinTrades>60</WinTrades>
    <LossTrades>40</LossTrades>
    <RecoveryFactor>2.47</RecoveryFactor>
    <SharpeRatio>0.85</SharpeRatio>
    ...
  </Summary>
  <Trades>
    <Trade>
      <OpenTime>2024.01.15 09:30:00</OpenTime>
      <CloseTime>2024.01.15 10:15:00</CloseTime>
      <Type>buy</Type>
      <Volume>0.10</Volume>
      <OpenPrice>126500</OpenPrice>
      <ClosePrice>126700</ClosePrice>
      <StopLoss>126300</StopLoss>
      <TakeProfit>126900</TakeProfit>
      <Profit>200.00</Profit>
      <Commission>0.00</Commission>
      <Swap>0.00</Swap>
      ...
    </Trade>
  </Trades>
</Strategy_Tester_Report>

NOTA: O formato exato pode variar entre versoes do MT5.
O parser tenta ser tolerante a variacoes de tag names.
"""

import logging
import os
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# TAG ALIASES: O MT5 pode usar nomes diferentes dependendo da versao/idioma
# ============================================================================

SUMMARY_TAG_MAP = {
    # Lucro
    "total_net_profit":     ["TotalNetProfit", "NetProfit", "Profit"],
    "gross_profit":         ["GrossProfit"],
    "gross_loss":           ["GrossLoss"],
    "profit_factor":        ["ProfitFactor"],
    "expected_payoff":      ["ExpectedPayoff", "Payoff"],

    # Drawdown
    "max_drawdown_money":   ["MaximalDrawdownMoney", "MaxDrawdownMoney", "MaxDrawdown"],
    "max_drawdown_pct":     ["MaximalDrawdownPercent", "MaxDrawdownPercent", "MaxDrawdown%"],
    "relative_drawdown_pct":["RelativeDrawdownPercent", "RelDrawdown%"],

    # Trades
    "total_trades":         ["TotalTrades", "Trades"],
    "win_trades":           ["WinTrades", "ProfitTrades", "WinningTrades"],
    "loss_trades":          ["LossTrades", "LossingTrades", "LosingTrades"],

    # Ratios
    "recovery_factor":      ["RecoveryFactor"],
    "sharpe_ratio":         ["SharpeRatio"],

    # Posicoes
    "short_trades":         ["ShortTrades", "ShortPositions"],
    "long_trades":          ["LongTrades", "LongPositions"],
    "short_won":            ["ShortWon", "ShortTradesWon"],
    "long_won":             ["LongWon", "LongTradesWon"],

    # Consecutivos
    "max_consecutive_wins": ["MaxConsecutiveWins", "ConsecutiveWins"],
    "max_consecutive_losses":["MaxConsecutiveLosses", "ConsecutiveLosses"],

    # Deposito
    "initial_deposit":      ["InitialDeposit", "Deposit"],
}

TRADE_TAG_MAP = {
    "open_time":    ["OpenTime", "Time"],
    "close_time":   ["CloseTime"],
    "type":         ["Type", "Direction"],
    "volume":       ["Volume", "Lots"],
    "open_price":   ["OpenPrice", "Price"],
    "close_price":  ["ClosePrice"],
    "stop_loss":    ["StopLoss", "SL"],
    "take_profit":  ["TakeProfit", "TP"],
    "profit":       ["Profit"],
    "commission":   ["Commission"],
    "swap":         ["Swap"],
    "comment":      ["Comment"],
    "magic":        ["MagicNumber", "Magic"],
}


def _find_tag_value(element: ET.Element, aliases: List[str], default: str = "0") -> str:
    """Busca valor de uma tag tentando varios nomes possiveis."""
    for alias in aliases:
        # Busca case-insensitive
        for child in element:
            if child.tag.lower() == alias.lower():
                return child.text or default
    return default


def _safe_float(value: str, default: float = 0.0) -> float:
    """Converte string para float, tolerando formatacao diversa."""
    try:
        # Remove espacos e substitui virgula por ponto
        cleaned = value.strip().replace(",", ".").replace(" ", "")
        return float(cleaned)
    except (ValueError, AttributeError):
        return default


def _safe_int(value: str, default: int = 0) -> int:
    """Converte string para int."""
    try:
        return int(float(value.strip().replace(",", ".").replace(" ", "")))
    except (ValueError, AttributeError):
        return default


# ============================================================================
# PARSER PRINCIPAL
# ============================================================================

def parse_xml_report(xml_path: str) -> Optional[Dict[str, Any]]:
    """
    Parseia o XML de resultado do MT5 Strategy Tester.

    Args:
        xml_path: Caminho absoluto do arquivo .xml

    Returns:
        Dict com metricas e trades, ou None se falhar.
        Formato:
        {
            "metrics": {
                "total_trades": int,
                "win_trades": int,
                "loss_trades": int,
                "win_rate": float,          # percentual 0-100
                "total_net_profit": float,
                "gross_profit": float,
                "gross_loss": float,
                "profit_factor": float,
                "expected_payoff": float,
                "max_drawdown_money": float,
                "max_drawdown_pct": float,
                "recovery_factor": float,
                "sharpe_ratio": float,
                "initial_deposit": float,
            },
            "trades": [
                {
                    "open_time": str,
                    "close_time": str,
                    "type": str,            # "buy" ou "sell"
                    "volume": float,
                    "open_price": float,
                    "close_price": float,
                    "profit": float,
                    "commission": float,
                    "swap": float,
                },
                ...
            ],
            "equity_curve": [float, ...],   # Curva de equity (saldo acumulado)
        }
    """
    if not os.path.exists(xml_path):
        logger.error(f"Arquivo XML nao encontrado: {xml_path}")
        return None

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        logger.error(f"Erro ao parsear XML: {e}")
        return None

    # Buscar elemento Summary (pode estar em varios niveis)
    summary = root.find(".//Summary")
    if summary is None:
        # Tentar no root direto (alguns formatos colocam metricas no root)
        summary = root

    # Extrair metricas
    metrics = {}
    for metric_name, aliases in SUMMARY_TAG_MAP.items():
        raw = _find_tag_value(summary, aliases)
        if metric_name in ("total_trades", "win_trades", "loss_trades",
                           "short_trades", "long_trades", "short_won", "long_won",
                           "max_consecutive_wins", "max_consecutive_losses"):
            metrics[metric_name] = _safe_int(raw)
        else:
            metrics[metric_name] = _safe_float(raw)

    # Calcular win_rate
    total = metrics.get("total_trades", 0)
    wins = metrics.get("win_trades", 0)
    metrics["win_rate"] = (wins / total * 100) if total > 0 else 0.0

    # Calcular payoff (avg win / avg loss)
    losses = metrics.get("loss_trades", 0)
    gross_profit = metrics.get("gross_profit", 0)
    gross_loss = abs(metrics.get("gross_loss", 0))
    avg_win = (gross_profit / wins) if wins > 0 else 0
    avg_loss = (gross_loss / losses) if losses > 0 else 0
    metrics["payoff"] = (avg_win / avg_loss) if avg_loss > 0 else 0.0

    # Extrair trades
    trades = []
    trades_element = root.find(".//Trades")
    if trades_element is None:
        trades_element = root.find(".//Orders")

    if trades_element is not None:
        for trade_el in trades_element:
            trade = {}
            for field_name, aliases in TRADE_TAG_MAP.items():
                raw = _find_tag_value(trade_el, aliases)
                if field_name in ("volume", "open_price", "close_price",
                                  "stop_loss", "take_profit", "profit",
                                  "commission", "swap"):
                    trade[field_name] = _safe_float(raw)
                else:
                    trade[field_name] = raw
            trades.append(trade)

    # Construir curva de equity
    equity_curve = []
    deposit = metrics.get("initial_deposit", 10000)
    running = deposit
    for t in trades:
        profit = t.get("profit", 0) + t.get("commission", 0) + t.get("swap", 0)
        running += profit
        equity_curve.append(round(running, 2))

    return {
        "metrics": metrics,
        "trades": trades,
        "equity_curve": equity_curve,
    }


def parse_html_report(html_path: str) -> Optional[Dict[str, Any]]:
    """
    Fallback: parseia o HTML de resultado do MT5.
    O MT5 tambem gera .htm com tabelas de metricas.

    Este parser e mais simples e extrai apenas as metricas principais
    via regex, sem dependencia de parser HTML completo.
    """
    import re

    if not os.path.exists(html_path):
        logger.error(f"Arquivo HTML nao encontrado: {html_path}")
        return None

    try:
        with open(html_path, "r", encoding="utf-16-le", errors="replace") as f:
            content = f.read()
    except Exception:
        try:
            with open(html_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Erro ao ler HTML: {e}")
            return None

    def extract_metric(label, text, default=0.0):
        """Extrai valor da celula seguinte ao label no HTML do MT5.
        Formato: <td>Label:</td><td><b>value</b></td>"""
        pattern = re.escape(label) + r'.*?</td>\s*<td[^>]*>\s*(?:<b>)?\s*([-\d.,\s]+)'
        m = re.search(pattern, text, re.S | re.IGNORECASE)
        if m:
            # MT5 usa espaco como separador de milhar (ex: "-9 861.00")
            raw = m.group(1).replace('\xa0', '').replace(' ', '').replace(',', '.')
            return _safe_float(raw)
        return default

    def extract_metric_pct(label, text, default=0.0):
        """Extrai percentual entre parenteses, ex: '1 234.56 (12.34%)'"""
        pattern = re.escape(label) + r'.*?</td>\s*<td[^>]*>\s*(?:<b>)?.*?\(([-\d.,\s]+)%\)'
        m = re.search(pattern, text, re.S | re.IGNORECASE)
        if m:
            raw = m.group(1).replace('\xa0', '').replace(' ', '').replace(',', '.')
            return _safe_float(raw)
        return default

    total_trades = int(extract_metric("Total Trades:", content))
    profit_trades_pct = extract_metric_pct("Profit Trades", content)
    win_trades = round(total_trades * profit_trades_pct / 100) if total_trades > 0 else 0

    metrics = {
        "total_net_profit": extract_metric("Total Net Profit:", content),
        "gross_profit": extract_metric("Gross Profit:", content),
        "gross_loss": extract_metric("Gross Loss:", content),
        "profit_factor": extract_metric("Profit Factor:", content),
        "total_trades": total_trades,
        "max_drawdown_money": extract_metric("Equity Drawdown Maximal:", content),
        "max_drawdown_pct": extract_metric_pct("Equity Drawdown Maximal:", content),
        "recovery_factor": extract_metric("Recovery Factor:", content),
        "sharpe_ratio": extract_metric("Sharpe Ratio:", content),
        "win_trades": win_trades,
        "loss_trades": total_trades - win_trades,
        "win_rate": profit_trades_pct,
    }

    # Extrair trades da tabela de deals (se disponivel)
    trades = _extract_html_trades(content)

    return {
        "metrics": metrics,
        "trades": trades,
        "equity_curve": [],
    }


def _extract_html_trades(content: str) -> list:
    """Extrai lista de trades da tabela de deals do HTML do MT5."""
    import re
    trades = []

    # Procurar a secao de Deals
    deals_match = re.search(r'<b>Deals</b>.*?<tr[^>]*>.*?Deal.*?</tr>(.*?)(?:<tr>\s*<td[^>]*colspan|</table>)', content, re.S | re.IGNORECASE)
    if not deals_match:
        return trades

    deals_html = deals_match.group(1)
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', deals_html, re.S)

    for row in rows:
        cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.S)
        if len(cells) < 10:
            continue
        # Limpar tags e espacos
        cells = [re.sub(r'<[^>]+>', '', c).replace('\xa0', '').strip() for c in cells]
        try:
            profit_str = cells[-2].replace(' ', '').replace(',', '.') if len(cells) > 2 else '0'
            profit = float(profit_str) if profit_str else 0.0
            trades.append({
                "time": cells[0] if cells[0] else "",
                "type": cells[2] if len(cells) > 2 else "",
                "volume": cells[4] if len(cells) > 4 else "",
                "price": cells[5] if len(cells) > 5 else "",
                "profit": profit,
                "commission": 0.0,
                "swap": 0.0,
            })
        except (ValueError, IndexError):
            continue

    return trades


# ============================================================================
# LOCALIZADOR DE ARQUIVO DE RESULTADO
# ============================================================================

def find_report_file(
    report_name: str,
    mt5_data_dir: str = "",
) -> Optional[str]:
    """
    Localiza o arquivo de resultado do backtest.

    O MT5 salva o report em:
    - <MT5_DATA>/Tester/<report_name>  (XML)
    - <MT5_DATA>/Tester/<ea_name>.htm  (HTML)

    Args:
        report_name: Nome do arquivo (ex: "BP_WINJ25_M5_abc12345_20260330.xml")
        mt5_data_dir: Diretorio base do MT5 data

    Returns:
        Caminho absoluto do arquivo, ou None
    """
    if not mt5_data_dir:
        appdata = os.getenv("APPDATA", "")
        mt5_guid = "84064CA60B86A0341461272DFBBA7B87"
        mt5_data_dir = os.path.join(appdata, "MetaQuotes", "Terminal", mt5_guid)

    # MT5 pode salvar reports em Tester/ ou na raiz do terminal
    search_dirs = [
        os.path.join(mt5_data_dir, "Tester"),
        mt5_data_dir,
    ]

    base = os.path.splitext(report_name)[0]
    # Se o nome ja termina com .xml, o MT5 pode gerar .xml.htm
    if report_name.endswith(".xml"):
        base_noxml = report_name[:-4]  # remove .xml
        extensions = [".xml", ".xml.htm", ".xml.html", ".htm", ".html"]
    else:
        base_noxml = base
        extensions = [".xml", ".xml.htm", ".htm", ".html"]

    for search_dir in search_dirs:
        if not os.path.isdir(search_dir):
            continue

        # Tentar nome exato
        exact = os.path.join(search_dir, report_name)
        if os.path.exists(exact):
            return exact

        # Tentar com extensoes alternativas
        for ext in extensions:
            path = os.path.join(search_dir, base_noxml + ext)
            if os.path.exists(path):
                return path

        # Buscar arquivos que comecam com o base name
        try:
            for fname in os.listdir(search_dir):
                if fname.startswith(base_noxml) and not fname.endswith(".png"):
                    return os.path.join(search_dir, fname)
        except OSError:
            continue

    logger.warning(f"Report nao encontrado: {report_name} em {[d for d in search_dirs]}")
    return None


# ============================================================================
# FUNCAO PRINCIPAL: Localizar + Parsear
# ============================================================================

def get_backtest_result(
    report_name: str,
    mt5_data_dir: str = "",
) -> Optional[Dict[str, Any]]:
    """
    Localiza e parseia o resultado do backtest.

    Args:
        report_name: Nome do arquivo de report
        mt5_data_dir: Diretorio base MT5 (opcional)

    Returns:
        Dict com metricas, trades e equity_curve, ou None
    """
    path = find_report_file(report_name, mt5_data_dir)
    if not path:
        return None

    if path.endswith((".htm", ".html", ".xml.htm", ".xml.html")):
        return parse_html_report(path)
    elif path.endswith(".xml"):
        return parse_xml_report(path)
    else:
        logger.error(f"Formato de report nao suportado: {path}")
        return None


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    if len(sys.argv) < 2:
        print("Uso: python result_parser.py <report.xml|report.htm>")
        sys.exit(1)

    path = sys.argv[1]

    if path.endswith(".xml"):
        result = parse_xml_report(path)
    else:
        result = parse_html_report(path)

    if result:
        print("\n=== METRICAS ===")
        for k, v in result["metrics"].items():
            print(f"  {k}: {v}")
        print(f"\n=== TRADES: {len(result['trades'])} ===")
        for t in result["trades"][:5]:
            print(f"  {t.get('type','?')} {t.get('volume',0)} @ {t.get('open_price',0)} -> {t.get('close_price',0)} = {t.get('profit',0)}")
        if len(result["trades"]) > 5:
            print(f"  ... e mais {len(result['trades'])-5} trades")
    else:
        print("Falha ao parsear resultado.")
