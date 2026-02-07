import pandas as pd
import streamlit as st

from structured_pricing.black_scholes import price_call_bs, price_digital_call_bs, price_put_bs
from structured_pricing.bonds import zero_coupon_price
from structured_pricing.market_data import fetch_market_snapshot
from structured_pricing.products import price_autocall_simplified
from structured_pricing.monte_carlo import price_option_mc_stats


st.set_page_config(page_title="Structured Pricing MVP", page_icon="📈", layout="centered")

st.title("Moteur simplifie de pricing")
st.caption("Black-Scholes + decomposition des payoffs")

if "spot" not in st.session_state:
    st.session_state.spot = 100.0
if "rate" not in st.session_state:
    st.session_state.rate = 0.02
if "volatility" not in st.session_state:
    st.session_state.volatility = 0.20
if "maturity" not in st.session_state:
    st.session_state.maturity = 1.0
if "mc_enabled" not in st.session_state:
    st.session_state.mc_enabled = True
if "mc_paths" not in st.session_state:
    st.session_state.mc_paths = 50_000
if "mc_seed" not in st.session_state:
    st.session_state.mc_seed = 42
if "mc_steps" not in st.session_state:
    st.session_state.mc_steps = 1
if "mc_antithetic" not in st.session_state:
    st.session_state.mc_antithetic = True
if "mc_show_ci" not in st.session_state:
    st.session_state.mc_show_ci = True
if "mc_show_table" not in st.session_state:
    st.session_state.mc_show_table = True
if "mc_show_convergence" not in st.session_state:
    st.session_state.mc_show_convergence = False

st.subheader("Donnees de marche")
data_mode = st.radio(
    "Source",
    ("Saisie manuelle", "Yahoo Finance (auto)"),
    horizontal=True,
)
if data_mode == "Yahoo Finance (auto)":
    col_ticker, col_days, col_fetch = st.columns([2, 1, 1])
    with col_ticker:
        ticker = st.text_input("Ticker", value="AAPL")
    with col_days:
        lookback_days = st.number_input("Jours histo", min_value=30, value=252, step=21)
    with col_fetch:
        st.write("")
        if st.button("Charger", use_container_width=True):
            try:
                snapshot = fetch_market_snapshot(ticker=ticker, lookback_days=lookback_days)
                st.session_state.spot = snapshot.spot
                st.session_state.volatility = snapshot.annualized_volatility
                st.success(
                    f"{snapshot.ticker} charge: spot={snapshot.spot:.4f}, sigma={snapshot.annualized_volatility:.4f}"
                )
            except Exception as exc:
                st.error(f"Erreur de chargement: {exc}")

st.subheader("Parametres Monte Carlo")
with st.expander("Reglages MC", expanded=False):
    st.session_state.mc_enabled = st.checkbox("Activer Monte Carlo", value=st.session_state.mc_enabled)
    st.session_state.mc_paths = st.number_input(
        "Nombre de trajectoires",
        min_value=1_000,
        value=int(st.session_state.mc_paths),
        step=5_000,
    )
    st.session_state.mc_steps = st.number_input(
        "Nombre de pas temporels",
        min_value=1,
        value=int(st.session_state.mc_steps),
        step=1,
    )
    st.session_state.mc_seed = st.number_input(
        "Seed",
        min_value=0,
        value=int(st.session_state.mc_seed),
        step=1,
    )
    st.session_state.mc_antithetic = st.checkbox(
        "Antithetic variates (reduction variance)",
        value=st.session_state.mc_antithetic,
    )
    st.session_state.mc_show_ci = st.checkbox("Afficher IC 95%", value=st.session_state.mc_show_ci)
    st.session_state.mc_show_table = st.checkbox("Afficher tableau comparatif", value=st.session_state.mc_show_table)
    st.session_state.mc_show_convergence = st.checkbox(
        "Afficher convergence MC", value=st.session_state.mc_show_convergence
    )

product = st.selectbox(
    "Que voulez-vous pricer ?",
    (
        "Obligation zero-coupon",
        "Option Call europeenne",
        "Option Put europeenne",
        "Autocall simplifie",
    ),
)

st.subheader("Parametres de marche")
spot = st.number_input("Spot (S0)", min_value=0.0001, step=1.0, key="spot")
rate = st.number_input("Taux sans risque r (ex: 0.02)", step=0.005, format="%.4f", key="rate")
volatility = st.number_input("Volatilite sigma (ex: 0.20)", min_value=0.0001, step=0.01, format="%.4f", key="volatility")
maturity = st.number_input("Maturite T (annees)", min_value=0.0001, step=0.25, format="%.4f", key="maturity")

result = None

if product == "Obligation zero-coupon":
    if st.button("Calculer le prix"):
        result = zero_coupon_price(rate=rate, maturity=maturity)
        st.success(f"Prix theorique (par nominal 1): {result:.6f}")
        st.info("Interpretation: cout aujourd'hui d'un paiement certain de 1 a maturite.")

elif product == "Option Call europeenne":
    strike = st.number_input("Strike K", min_value=0.0001, value=100.0, step=1.0)
    if st.button("Calculer le prix"):
        result = price_call_bs(
            spot=spot,
            strike=strike,
            rate=rate,
            volatility=volatility,
            maturity=maturity,
        )
        st.success(f"Prix theorique du call: {result:.6f}")
        st.info("Decomposition payoff: max(S_T - K, 0).")

        if st.session_state.mc_enabled:
            mc_price, mc_se, mc_low, mc_high = price_option_mc_stats(
                payoff=lambda st: max(st - strike, 0.0),
                spot=spot,
                rate=rate,
                volatility=volatility,
                maturity=maturity,
                n_paths=int(st.session_state.mc_paths),
                seed=int(st.session_state.mc_seed),
                n_steps=int(st.session_state.mc_steps),
                antithetic=bool(st.session_state.mc_antithetic),
            )
            st.markdown("**Comparaison BS vs Monte Carlo**")
            col1, col2, col3 = st.columns(3)
            col1.metric("BS", f"{result:.6f}")
            col2.metric("MC", f"{mc_price:.6f}")
            col3.metric("Ecart", f"{(mc_price - result):.6f}")
            if st.session_state.mc_show_ci:
                st.caption(f"IC 95% MC: [{mc_low:.6f} ; {mc_high:.6f}] | SE={mc_se:.6f}")

            if st.session_state.mc_show_table:
                table = pd.DataFrame(
                    [
                        {"Modele": "Black-Scholes", "Prix": result, "SE": "", "IC95%": ""},
                        {
                            "Modele": "Monte Carlo",
                            "Prix": mc_price,
                            "SE": mc_se,
                            "IC95%": f"[{mc_low:.6f} ; {mc_high:.6f}]",
                        },
                        {"Modele": "Ecart MC - BS", "Prix": mc_price - result, "SE": "", "IC95%": ""},
                    ]
                )
                st.dataframe(table, use_container_width=True, hide_index=True)

            if st.session_state.mc_show_convergence:
                st.markdown("**Convergence Monte Carlo**")
                st.caption("Peut prendre du temps si le nombre de trajectoires est eleve.")
                max_paths = int(st.session_state.mc_paths)
                base = [1000, 2000, 5000, 10000, 20000, 50000]
                counts = [n for n in base if n <= max_paths]
                if max_paths not in counts:
                    counts.append(max_paths)
                counts = sorted(set(counts))
                conv_prices = []
                for n in counts:
                    price_n, _, _, _ = price_option_mc_stats(
                        payoff=lambda st: max(st - strike, 0.0),
                        spot=spot,
                        rate=rate,
                        volatility=volatility,
                        maturity=maturity,
                        n_paths=int(n),
                        seed=int(st.session_state.mc_seed),
                        n_steps=int(st.session_state.mc_steps),
                        antithetic=bool(st.session_state.mc_antithetic),
                    )
                    conv_prices.append(price_n)
                chart_df = pd.DataFrame(
                    {"Paths": counts, "MC Price": conv_prices, "BS": [result] * len(counts)}
                )
                st.line_chart(chart_df, x="Paths", y=["MC Price", "BS"], use_container_width=True)

        st.markdown("**Profil de payoff a maturite**")
        prices = [0.5 * spot + i * (spot / 15.0) for i in range(31)]
        payoffs = [max(p - strike, 0.0) for p in prices]
        chart_df = pd.DataFrame({"S_T": prices, "Payoff": payoffs})
        st.line_chart(chart_df, x="S_T", y="Payoff", use_container_width=True)

elif product == "Option Put europeenne":
    strike = st.number_input("Strike K", min_value=0.0001, value=100.0, step=1.0)
    if st.button("Calculer le prix"):
        result = price_put_bs(
            spot=spot,
            strike=strike,
            rate=rate,
            volatility=volatility,
            maturity=maturity,
        )
        st.success(f"Prix theorique du put: {result:.6f}")
        st.info("Decomposition payoff: max(K - S_T, 0).")

        if st.session_state.mc_enabled:
            mc_price, mc_se, mc_low, mc_high = price_option_mc_stats(
                payoff=lambda st: max(strike - st, 0.0),
                spot=spot,
                rate=rate,
                volatility=volatility,
                maturity=maturity,
                n_paths=int(st.session_state.mc_paths),
                seed=int(st.session_state.mc_seed),
                n_steps=int(st.session_state.mc_steps),
                antithetic=bool(st.session_state.mc_antithetic),
            )
            st.markdown("**Comparaison BS vs Monte Carlo**")
            col1, col2, col3 = st.columns(3)
            col1.metric("BS", f"{result:.6f}")
            col2.metric("MC", f"{mc_price:.6f}")
            col3.metric("Ecart", f"{(mc_price - result):.6f}")
            if st.session_state.mc_show_ci:
                st.caption(f"IC 95% MC: [{mc_low:.6f} ; {mc_high:.6f}] | SE={mc_se:.6f}")

            if st.session_state.mc_show_table:
                table = pd.DataFrame(
                    [
                        {"Modele": "Black-Scholes", "Prix": result, "SE": "", "IC95%": ""},
                        {
                            "Modele": "Monte Carlo",
                            "Prix": mc_price,
                            "SE": mc_se,
                            "IC95%": f"[{mc_low:.6f} ; {mc_high:.6f}]",
                        },
                        {"Modele": "Ecart MC - BS", "Prix": mc_price - result, "SE": "", "IC95%": ""},
                    ]
                )
                st.dataframe(table, use_container_width=True, hide_index=True)

            if st.session_state.mc_show_convergence:
                st.markdown("**Convergence Monte Carlo**")
                st.caption("Peut prendre du temps si le nombre de trajectoires est eleve.")
                max_paths = int(st.session_state.mc_paths)
                base = [1000, 2000, 5000, 10000, 20000, 50000]
                counts = [n for n in base if n <= max_paths]
                if max_paths not in counts:
                    counts.append(max_paths)
                counts = sorted(set(counts))
                conv_prices = []
                for n in counts:
                    price_n, _, _, _ = price_option_mc_stats(
                        payoff=lambda st: max(strike - st, 0.0),
                        spot=spot,
                        rate=rate,
                        volatility=volatility,
                        maturity=maturity,
                        n_paths=int(n),
                        seed=int(st.session_state.mc_seed),
                        n_steps=int(st.session_state.mc_steps),
                        antithetic=bool(st.session_state.mc_antithetic),
                    )
                    conv_prices.append(price_n)
                chart_df = pd.DataFrame(
                    {"Paths": counts, "MC Price": conv_prices, "BS": [result] * len(counts)}
                )
                st.line_chart(chart_df, x="Paths", y=["MC Price", "BS"], use_container_width=True)

        st.markdown("**Profil de payoff a maturite**")
        prices = [0.5 * spot + i * (spot / 15.0) for i in range(31)]
        payoffs = [max(strike - p, 0.0) for p in prices]
        chart_df = pd.DataFrame({"S_T": prices, "Payoff": payoffs})
        st.line_chart(chart_df, x="S_T", y="Payoff", use_container_width=True)

elif product == "Autocall simplifie":
    strike_call = st.number_input("Barriere haute / strike call", min_value=0.0001, value=105.0, step=1.0)
    strike_put = st.number_input("Barriere basse / strike put", min_value=0.0001, value=80.0, step=1.0)
    coupon_rate = st.number_input("Coupon (ex: 0.08 pour 8%)", min_value=0.0, value=0.08, step=0.01, format="%.4f")
    nominal = st.number_input("Nominal", min_value=0.01, value=100.0, step=10.0)

    if st.button("Calculer le prix"):
        result = price_autocall_simplified(
            spot=spot,
            strike_call=strike_call,
            strike_put=strike_put,
            rate=rate,
            volatility=volatility,
            maturity=maturity,
            coupon_rate=coupon_rate,
            nominal=nominal,
        )
        st.success(f"Prix theorique de l'autocall simplifie: {result:.6f}")

        zc_value = nominal * zero_coupon_price(rate=rate, maturity=maturity)
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
        st.markdown("**Decomposition du prix**")
        col1, col2, col3 = st.columns(3)
        col1.metric("Composante ZC", f"{zc_value:.4f}")
        col2.metric("Digitale call", f"{digital_call_value:.4f}")
        col3.metric("Put vendue", f"-{put_sold_cost:.4f}")

        st.markdown("**Profil de payoff simplifie a maturite**")
        prices = [0.5 * spot + i * (spot / 15.0) for i in range(31)]
        payoffs = []
        for p in prices:
            if p >= strike_call:
                payoffs.append(nominal * (1.0 + coupon_rate))
            elif p >= strike_put:
                payoffs.append(nominal)
            else:
                payoffs.append(nominal * (p / spot))
        chart_df = pd.DataFrame({"S_T": prices, "Payoff": payoffs})
        st.line_chart(chart_df, x="S_T", y="Payoff", use_container_width=True)

st.divider()
st.markdown(
    "Cette interface est un MVP pedagogique. Les resultats sont theoriques et bases sur des hypotheses simplificatrices."
)
