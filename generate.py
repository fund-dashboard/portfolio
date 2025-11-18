import yfinance as yf
import requests
from datetime import datetime
import json
import pandas as pd

SHARES = 0.3
PURCHASE_DATE = "2025-11-14"
PURCHASE_PRICE = 141.90  # EUR
TEMPLATE = "template.html"
OUTPUT = "index.html"

def get_vwce_price():
    t = yf.Ticker("VWCE.DE")
    data = t.history(period="1d")
    return float(data["Close"].iloc[-1])

def get_fx_rate():
    url = "https://open.er-api.com/v6/latest/EUR"
    return requests.get(url).json()["rates"]["CZK"]

def get_vwce_history():
    t = yf.Ticker("VWCE.DE")
    df = t.history(period="max")

    # převedeme PURCHASE_DATE na Timestamp
    purchase_ts = pd.to_datetime(PURCHASE_DATE)

    # data až od následujícího dne po nákupu
    df = df[df.index > purchase_ts]

    # zaokrouhlení
    df["Close"] = df["Close"].round(2)

    # vytvoření seznamů
    dates = df.index.strftime("%Y-%m-%d").tolist()
    close = df["Close"].tolist()

    # vložíme jako PRVNÍ bod nákupní cenu
    dates.insert(0, PURCHASE_DATE)
    close.insert(0, round(PURCHASE_PRICE, 2))

    # a pokud je historie jen 1 den (nákupní),
    # přidáme druhý bod stejné hodnoty, aby se graf vykreslil
    if len(dates) == 1:
        dates.append(PURCHASE_DATE)
        close.append(round(PURCHASE_PRICE, 2))

    return {"dates": dates, "close": close}


def main():
    price = get_vwce_price()
    rate = get_fx_rate()
    history = get_vwce_history()

    value_eur = price * SHARES
    value_czk = value_eur * rate

    initial_value = SHARES * PURCHASE_PRICE
    growth_ratio = value_eur / initial_value - 1
    growth_percent = growth_ratio * 100

    with open(TEMPLATE, "r", encoding="utf-8") as f:
        html = f.read()

    html = html.replace("{{PRICE}}", f"{price:.2f}")
    html = html.replace("{{VALUE_EUR}}", f"{value_eur:.2f}")
    html = html.replace("{{VALUE_CZK}}", f"{value_czk:.2f}")
    html = html.replace("{{RATE}}", f"{rate:.2f}")
    html = html.replace("{{SHARES}}", f"{SHARES}")
    html = html.replace("{{PURCHASE_DATE}}", PURCHASE_DATE)
    html = html.replace("{{PURCHASE_PRICE}}", f"{PURCHASE_PRICE:.2f}")
    html = html.replace("{{GROWTH_PERCENT}}", f"{growth_percent:.2f}")
    html = html.replace("{{GROWTH_COLOR}}", "#0a6" if growth_percent >= 0 else "#c00")

    html = html.replace("{{GROWTH_EUR}}", f"{value_eur - initial_value:.2f}")
    html = html.replace("{{UPDATED}}", datetime.now().strftime("%Y-%m-%d %H:%M"))

    # graph data
    html = html.replace("{{HISTORY_DATES}}", json.dumps(history["dates"]))
    html = html.replace("{{HISTORY_CLOSE}}", json.dumps(history["close"]))

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    main()
