# Structured Pricing MVP

MVP pedagogique pour pricer :
- obligation zero-coupon,
- call europeen,
- put europeen,
- autocall simplifie.

L'application permet aussi :
- la saisie manuelle des parametres de marche,
- le chargement automatique du spot/volatilite via Yahoo Finance (`yfinance`),
- l'affichage de profils de payoff,
- la comparaison Black-Scholes vs Monte Carlo (Call/Put),
- l'intervalle de confiance 95% et l'erreur standard MC,
- des reglages MC (trajectoires, seed, pas temporels),
- une option de reduction de variance (antithetic variates),
- un graphique de convergence MC (optionnel).

## Lancer le projet

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Structure

- `app.py` : interface utilisateur Streamlit.
- `structured_pricing/black_scholes.py` : briques Black-Scholes (d1, d2, call, put, digital call).
- `structured_pricing/bonds.py` : zero-coupon.
- `structured_pricing/products.py` : autocall simplifie.
- `structured_pricing/market_data.py` : recuperation de spot/volatilite depuis Yahoo Finance.
- `structured_pricing/monte_carlo.py` : moteur Monte Carlo (IC 95%, pas temporels, antithetic variates).

## Note

Ce projet est volontairement simplifie pour un usage de comprehension/theorie.
