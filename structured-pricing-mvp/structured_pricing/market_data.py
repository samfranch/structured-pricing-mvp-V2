from dataclasses import dataclass
from math import log, sqrt


@dataclass(frozen=True)
class MarketSnapshot:
    ticker: str
    spot: float
    annualized_volatility: float


def fetch_market_snapshot(ticker: str, lookback_days: int = 252) -> MarketSnapshot:
    if lookback_days < 30:
        raise ValueError("Utilisez au moins 30 jours pour estimer la volatilite.")

    try:
        import yfinance as yf
    except ImportError as exc:
        raise ImportError(
            "Le package yfinance est requis. Installez les dependances via requirements.txt."
        ) from exc

    symbol = ticker.strip().upper()
    if not symbol:
        raise ValueError("Le ticker ne peut pas etre vide.")

    data = yf.Ticker(symbol)
    history = data.history(period=f"{lookback_days + 5}d")
    if history.empty or "Close" not in history:
        raise ValueError(f"Aucune donnee recuperee pour {symbol}.")

    closes = [float(v) for v in history["Close"].dropna().tolist()]
    if len(closes) < 30:
        raise ValueError(f"Pas assez de donnees historiques pour {symbol}.")

    spot = closes[-1]
    log_returns = [log(closes[i] / closes[i - 1]) for i in range(1, len(closes)) if closes[i - 1] > 0]
    if len(log_returns) < 20:
        raise ValueError(f"Impossible d'estimer la volatilite pour {symbol}.")

    mean_ret = sum(log_returns) / len(log_returns)
    variance = sum((r - mean_ret) ** 2 for r in log_returns) / (len(log_returns) - 1)
    annualized_volatility = sqrt(variance) * sqrt(252.0)

    return MarketSnapshot(ticker=symbol, spot=spot, annualized_volatility=annualized_volatility)

