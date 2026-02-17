import yfinance as yf
import pandas as pd
import smtplib
import os
from email.mime.text import MIMEText
from datetime import datetime

WATCHLIST = ["NVDA", "AVGO", "AMD", "ALAB", "AI", "COIN"]
MARKET = "QQQ"


# -----------------------------------
# DATA FUNCTIONS
# -----------------------------------

def get_data(ticker):
    data = yf.download(ticker, period="1y", interval="1d", progress=False)

    if data.empty:
        return None

    data["200DMA"] = data["Close"].rolling(200).mean()
    data["50DMA"] = data["Close"].rolling(50).mean()

    return data


def market_ok():
    data = get_data(MARKET)

    if data is None or len(data) < 200:
        return False

    latest = data.iloc[-1]

    if pd.isna(latest["200DMA"]):
        return False

    return latest["Close"] > latest["200DMA"]


def check_stock(ticker):
    data = get_data(ticker)

    if data is None or len(data) < 200:
        return {
            "ticker": ticker,
            "price": "N/A",
            "buy": False,
            "exit": False
        }

    latest = data.iloc[-1]

    dma_200_today = latest["200DMA"]
    dma_200_20d_ago = data["200DMA"].iloc[-20]

    if pd.isna(dma_200_today) or pd.isna(dma_200_20d_ago):
        return {
            "ticker": ticker,
            "price": round(latest["Close"], 2),
            "buy": False,
            "exit": False
        }

    buy = (
        latest["Close"] > dma_200_today and
        dma_200_today > dma_200_20d_ago and
        latest["Close"] > latest["50DMA"]
    )

    exit_risk = (
        latest["Close"] < dma_200_today or
        latest["Close"] < latest["50DMA"]
    )

    return {
        "ticker": ticker,
        "price": round(latest["Close"], 2),
        "buy": buy,
        "exit": exit_risk
    }


# -----------------------------------
# EMAIL FUNCTION
# -----------------------------------

def send_email(body):
    sender = os.getenv("EMAIL_ADDRESS")
    password = os.getenv("EMAIL_PASSWORD")

    if not sender or not password:
        raise ValueError("Email credentials missing. Check GitHub Secrets.")

    msg = MIMEText(body)
    msg["Subject"] = "Daily 200DMA Trading Report"
    msg["From"] = sender
    msg["To"] = sender

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, sender, msg.as_string())


# -----------------------------------
# MAIN RUN
# -----------------------------------

def run():
    report = f"Daily 200DMA Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"

    regime = market_ok()
    report += f"Market Regime OK (QQQ > 200DMA): {regime}\n\n"

    for ticker in WATCHLIST:
        result = check_stock(ticker)
        report += (
            f"{result['ticker']} | "
            f"Price: {result['price']} | "
            f"BUY: {result['buy']} | "
            f"EXIT: {result['exit']}\n"
        )

    send_email(report)


if __name__ == "__main__":
    run()
