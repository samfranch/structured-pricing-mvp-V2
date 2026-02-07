from dataclasses import dataclass


@dataclass(frozen=True)
class MarketParams:
    spot: float
    rate: float
    volatility: float


@dataclass(frozen=True)
class OptionParams:
    strike: float
    maturity: float


@dataclass(frozen=True)
class AutocallParams:
    strike_call: float
    strike_put: float
    maturity: float
    coupon_rate: float

