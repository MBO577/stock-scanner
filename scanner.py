import yfinance as yf
import pandas as pd
import smtplib
import os
from email.mime.text import MIMEText
from datetime import datetime

WATCHLIST = ["NVDA", "AVGO", "AMD", "ALAB", "AI", "COIN"]
MARKET = "QQQ"

def get_data(ticker):
    data = yf.download(ticker, period="1y", interval="1d", progress=False)
    data["200DMA"] = data["Close"].rolling(200).mean()
    data["50DMA"] = data["Close"].rolling(50).mean()
    return data

def market_ok():
    data = get_data(MARKET)
    latest = data.iloc[-1]
    return latest["Close"] > latest["200DMA"]

def check_stock(ticker):
    data = get_data(ticker)
    latest = data.iloc[-1]
    
    dma_200_today = latest["200DMA"]
    dma_200_20d_ago = data["200DMA"].iloc[-20]
    
    buy = (
        latest["Close"] > latest["200DMA"] and
        dma_200_today > dma_200_20d_ago and
        latest["Close"] > latest["50DMA"]
    )
    
    exit_risk = (
        latest["Close"] < latest["200DMA"] or
        latest["Close"] < latest["50DMA"]
    )
    
    return {
        "ticker": ticker,
        "price": round(latest["Close"], 2),
        "buy": buy,
        "exit": exit_risk
    }

def send_email(body):
    sender = os.environ["EMAIL_ADDRESS"]
    password = os.environ["EMAIL_PASSWORD"]
    receiver = os.environ["EMAIL_ADDRESS"]
    
    msg = MIMEText(body)
    msg["Subject"] = "Daily 200DMA Trading Report"
    msg["From"] = sender
    msg["To"] = receiver
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, receiver, msg.as_string())

def run():
    report = f"Daily Report - {datetime.now()}\n\n"
    
    regime = market_ok()
    report += f"Market Regime OK: {regime}\n\n"
    
    for ticker in WATCHLIST:
        result = check_stock(ticker)
        report += (
            f"{result['ticker']} | Price: {result['price']} | "
            f"BUY: {result['buy']} | EXIT: {result['exit']}\n"
        )
    
    send_email(report)

if __name__ == "__main__":
    run()
