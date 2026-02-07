import math
import random
from typing import Callable


def _simulate_from_normals(
    spot: float,
    rate: float,
    volatility: float,
    maturity: float,
    normals: list[float],
) -> float:
    n_steps = len(normals)
    if n_steps == 0:
        return spot
    dt = maturity / n_steps
    drift = (rate - 0.5 * volatility * volatility) * dt
    vol_sqrt_dt = volatility * math.sqrt(dt)

    st = spot
    for z in normals:
        st *= math.exp(drift + vol_sqrt_dt * z)
    return st


def simulate_terminal_price(
    spot: float,
    rate: float,
    volatility: float,
    maturity: float,
    n_steps: int = 1,
) -> float:
    """Simule S_T via GBM (solution exacte par pas)."""
    if n_steps <= 1:
        z = random.gauss(0.0, 1.0)
        drift = (rate - 0.5 * volatility * volatility) * maturity
        diffusion = volatility * math.sqrt(maturity) * z
        return spot * math.exp(drift + diffusion)

    normals = [random.gauss(0.0, 1.0) for _ in range(n_steps)]
    return _simulate_from_normals(spot, rate, volatility, maturity, normals)


def price_option_mc(
    payoff: Callable[[float], float],
    spot: float,
    rate: float,
    volatility: float,
    maturity: float,
    n_paths: int = 50_000,
    seed: int | None = 42,
    n_steps: int = 1,
    antithetic: bool = False,
) -> float:
    """Prix MC d'un payoff g(S_T) sous mesure risque-neutre."""
    if seed is not None:
        random.seed(seed)

    total = 0.0
    count = 0
    discount = math.exp(-rate * maturity)

    if antithetic:
        n_pairs = n_paths // 2
        for _ in range(n_pairs):
            if n_steps <= 1:
                z = random.gauss(0.0, 1.0)
                st1 = spot * math.exp((rate - 0.5 * volatility * volatility) * maturity + volatility * math.sqrt(maturity) * z)
                st2 = spot * math.exp((rate - 0.5 * volatility * volatility) * maturity + volatility * math.sqrt(maturity) * (-z))
            else:
                normals = [random.gauss(0.0, 1.0) for _ in range(n_steps)]
                st1 = _simulate_from_normals(spot, rate, volatility, maturity, normals)
                st2 = _simulate_from_normals(spot, rate, volatility, maturity, [-z for z in normals])
            total += payoff(st1) + payoff(st2)
            count += 2

        if n_paths % 2 == 1:
            st = simulate_terminal_price(spot, rate, volatility, maturity, n_steps=n_steps)
            total += payoff(st)
            count += 1
    else:
        for _ in range(n_paths):
            st = simulate_terminal_price(spot, rate, volatility, maturity, n_steps=n_steps)
            total += payoff(st)
        count = n_paths

    return discount * (total / count)


def price_option_mc_stats(
    payoff: Callable[[float], float],
    spot: float,
    rate: float,
    volatility: float,
    maturity: float,
    n_paths: int = 50_000,
    seed: int | None = 42,
    n_steps: int = 1,
    antithetic: bool = False,
) -> tuple[float, float, float, float]:
    """Retourne prix MC, erreur standard et IC 95%."""
    if n_paths <= 1:
        raise ValueError("n_paths doit etre > 1.")
    if seed is not None:
        random.seed(seed)

    discount = math.exp(-rate * maturity)
    values: list[float] = []

    if antithetic:
        n_pairs = n_paths // 2
        for _ in range(n_pairs):
            if n_steps <= 1:
                z = random.gauss(0.0, 1.0)
                st1 = spot * math.exp((rate - 0.5 * volatility * volatility) * maturity + volatility * math.sqrt(maturity) * z)
                st2 = spot * math.exp((rate - 0.5 * volatility * volatility) * maturity + volatility * math.sqrt(maturity) * (-z))
            else:
                normals = [random.gauss(0.0, 1.0) for _ in range(n_steps)]
                st1 = _simulate_from_normals(spot, rate, volatility, maturity, normals)
                st2 = _simulate_from_normals(spot, rate, volatility, maturity, [-z for z in normals])
            values.append(discount * payoff(st1))
            values.append(discount * payoff(st2))

        if n_paths % 2 == 1:
            st = simulate_terminal_price(spot, rate, volatility, maturity, n_steps=n_steps)
            values.append(discount * payoff(st))
    else:
        for _ in range(n_paths):
            st = simulate_terminal_price(spot, rate, volatility, maturity, n_steps=n_steps)
            values.append(discount * payoff(st))

    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    std_error = math.sqrt(variance / len(values))
    ci_low = mean - 1.96 * std_error
    ci_high = mean + 1.96 * std_error
    return mean, std_error, ci_low, ci_high
