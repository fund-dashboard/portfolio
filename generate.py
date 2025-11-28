import yfinance as yf
import requests
from datetime import datetime
import json
import pandas as pd

TEMPLATE = "template.html"
OUTPUT = "index.html"

# 💰 ZDE DEFINUJEŠ NÁKUPY
TRADES = [
    {"date": "2025-11-14", "price": 141.90, "shares": 0.3},
    # Přidej další nákupy sem...
    # {"date": "2025-11-18", "price": 143.20, "shares": 0.7},
]

def get_vwce_price():
    t = yf.Ticker("VWCE.DE")
    data = t.history(period="1d")
    return float(data["Close"].iloc[-1])

def get_fx_rate():
    url = "https://open.er-api.com/v6/latest/EUR"
    return requests.get(url).json()["rates"]["CZK"]

def get_vwce_history(first_trade_date):
    t = yf.Ticker("VWCE.DE")
    df = t.history(period="max")

    # Odstranit časové zóny kvůli porovnání
    df.index = df.index.tz_localize(None)

    first_ts = pd.to_datetime(first_trade_date)
    df = df[df.index >= first_ts]

    return {
        "dates": df.index.strftime("%Y-%m-%d").tolist(),
        "close": df["Close"].round(2).tolist()
    }

def main():
    # ===== Výpočty =====
    total_shares = sum(t["shares"] for t in TRADES)
    total_spent  = sum(t["shares"] * t["price"] for t in TRADES)

    avg_price = total_spent / total_shares

    current_price = get_vwce_price()
    rate = get_fx_rate()

    value_eur = current_price * total_shares
    value_czk = value_eur * rate

    growth_ratio = value_eur / total_spent - 1
    growth_percent = growth_ratio * 100
    growth_eur = value_eur - total_spent

    # Historie VWCE
    first_trade = TRADES[0]["date"]
    history = get_vwce_history(first_trade)

    # ===== HTML =====
    with open(TEMPLATE, "r", encoding="utf-8") as f:
        html = f.read()

    # základní hodnoty
    html = html.replace("{{TOTAL_SHARES}}", f"{total_shares}")
    html = html.replace("{{CURRENT_PRICE}}", f"{current_price:.2f}")
    html = html.replace("{{VALUE_EUR}}", f"{value_eur:.2f}")
    html = html.replace("{{VALUE_CZK}}", f"{value_czk:.2f}")
    html = html.replace("{{RATE}}", f"{rate:.2f}")

    # růst a výkonnost
    html = html.replace("{{AVG_PRICE}}", f"{avg_price:.2f}")
    html = html.replace("{{GROWTH_PERCENT}}", f"{growth_percent:.2f}")
    html = html.replace("{{GROWTH_EUR}}", f"{growth_eur:.2f}")
    html = html.replace("{{GROWTH_COLOR}}", "#0a6" if growth_percent >= 0 else "#c00")

    html = html.replace("{{UPDATED}}", datetime.now().strftime("%Y-%m-%d %H:%M"))

    # seznam nákupů
    trade_rows = ""
    for t in TRADES:
        trade_rows += f"<tr><td>{t['date']}</td><td>{t['shares']} ks</td><td>{t['price']} EUR</td></tr>\n"

    html = html.replace("{{TRADE_ROWS}}", trade_rows)

    # graf — historie
    html = html.replace("{{HISTORY_DATES}}", json.dumps(history["dates"]))
    html = html.replace("{{HISTORY_CLOSE}}", json.dumps(history["close"]))

    # graf — tečky nákupů
    purchase_points = {}
    for t in TRADES:
        purchase_points[t["date"]] = t["price"]

    html = html.replace("{{TRADE_POINTS_DATES}}", json.dumps(list(purchase_points.keys())))
    html = html.replace("{{TRADE_POINTS_PRICES}}", json.dumps(list(purchase_points.values())))

    # průměrná cena pro graf (vodorovná čára)
    html = html.replace("{{AVG_PRICE_JS}}", f"{avg_price:.2f}")

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    main()
