from math import exp


def zero_coupon_price(rate: float, maturity: float) -> float:
    if maturity < 0:
        raise ValueError("La maturite doit etre positive.")
    return exp(-rate * maturity)

