from .black_scholes import price_digital_call_bs, price_put_bs
from .bonds import zero_coupon_price


def price_autocall_simplified(
    spot: float,
    strike_call: float,
    strike_put: float,
    rate: float,
    volatility: float,
    maturity: float,
    coupon_rate: float,
    nominal: float = 100.0,
) -> float:
    if nominal <= 0:
        raise ValueError("Le nominal doit etre strictement positif.")
    if coupon_rate < 0:
        raise ValueError("Le coupon doit etre positif ou nul.")

    zc_value = nominal * zero_coupon_price(rate, maturity)
    digital_call_value = price_digital_call_bs(
        spot=spot,
        strike=strike_call,
        rate=rate,
        volatility=volatility,
        maturity=maturity,
        payoff=nominal * coupon_rate,
    )
    put_sold_cost = price_put_bs(
        spot=spot,
        strike=strike_put,
        rate=rate,
        volatility=volatility,
        maturity=maturity,
    )
    return zc_value + digital_call_value - put_sold_cost

