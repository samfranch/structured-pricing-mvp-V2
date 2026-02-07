from math import erf, exp, log, sqrt


def _validate_inputs(spot: float, strike: float, volatility: float, maturity: float) -> None:
    if spot <= 0:
        raise ValueError("Le spot doit etre strictement positif.")
    if strike <= 0:
        raise ValueError("Le strike doit etre strictement positif.")
    if volatility <= 0:
        raise ValueError("La volatilite doit etre strictement positive.")
    if maturity <= 0:
        raise ValueError("La maturite doit etre strictement positive.")


def normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + erf(x / sqrt(2.0)))


def compute_d1_d2(
    spot: float,
    strike: float,
    rate: float,
    volatility: float,
    maturity: float,
) -> tuple[float, float]:
    _validate_inputs(spot, strike, volatility, maturity)
    vol_sqrt_t = volatility * sqrt(maturity)
    d1 = (log(spot / strike) + (rate + 0.5 * volatility * volatility) * maturity) / vol_sqrt_t
    d2 = d1 - vol_sqrt_t
    return d1, d2


def price_call_bs(
    spot: float,
    strike: float,
    rate: float,
    volatility: float,
    maturity: float,
) -> float:
    d1, d2 = compute_d1_d2(spot, strike, rate, volatility, maturity)
    return spot * normal_cdf(d1) - strike * exp(-rate * maturity) * normal_cdf(d2)


def price_put_bs(
    spot: float,
    strike: float,
    rate: float,
    volatility: float,
    maturity: float,
) -> float:
    d1, d2 = compute_d1_d2(spot, strike, rate, volatility, maturity)
    return strike * exp(-rate * maturity) * normal_cdf(-d2) - spot * normal_cdf(-d1)


def price_digital_call_bs(
    spot: float,
    strike: float,
    rate: float,
    volatility: float,
    maturity: float,
    payoff: float = 1.0,
) -> float:
    _, d2 = compute_d1_d2(spot, strike, rate, volatility, maturity)
    return payoff * exp(-rate * maturity) * normal_cdf(d2)

