from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import logging
import datetime
import random
import yfinance as yf
import pandas as pd
from flask import Flask
import threading
import asyncio

# --- Keep Alive Web Server ---
web = Flask(__name__)

@web.route('/')
def home():
    return "Elvin's bot is running."

def run_web():
    web.run(host="0.0.0.0", port=10000)

threading.Thread(target=run_web).start()

# --- Logging ---
logging.basicConfig(level=logging.INFO)

# --- Bot Token ---
BOT_TOKEN = "7958535571:AAEVB49WOrlb5JNttueQeRxwDoGiCxLHZgc"
YOUR_CHAT_ID = 7147175084

# --- Trade Log ---
trade_log = []

# --- Commands ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hello Elvin! Your trading bot is live and ready!")

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    signal_type = random.choice(["BUY", "SELL"])
    result = random.choice(["Win", "Loss"])
    trade_log.append({"signal": signal_type, "result": result, "time": datetime.datetime.now()})
    await update.message.reply_text(f"📈 {signal_type} signal triggered!\nResult: {result}")

async def trend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    trend = random.choice(["📈 UPTREND", "📉 DOWNTREND", "🔁 SIDEWAYS"])
    await update.message.reply_text(f"Current Market Trend: {trend}")

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.datetime.now().date()
    today_trades = [t for t in trade_log if t["time"].date() == today]
    total = len(today_trades)
    wins = sum(1 for t in today_trades if t["result"] == "Win")
    losses = total - wins
    accuracy = (wins / total * 100) if total > 0 else 0
    await update.message.reply_text(
        f"📊 Daily Summary:\n"
        f"Total Trades: {total}\n"
        f"Wins: {wins}\n"
        f"Losses: {losses}\n"
        f"Accuracy: {accuracy:.1f}%"
    )

async def realsignal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        symbol = "EURUSD=X"
        data = yf.download(tickers=symbol, period="1d", interval="5m")

        if data.empty or len(data) < 15:
            await update.message.reply_text("⚠️ Not enough data to calculate RSI.")
            return

        delta = data["Close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        rsi = rsi.dropna()

        if rsi.empty:
            await update.message.reply_text("⚠️ RSI calculation failed.")
            return

        last_rsi = float(rsi.iloc[-1])

        if last_rsi < 30:
            signal = f"📈 BUY (RSI = {last_rsi:.2f})"
        elif last_rsi > 70:
            signal = f"📉 SELL (RSI = {last_rsi:.2f})"
        else:
            signal = f"⏸️ HOLD (RSI = {last_rsi:.2f})"

        await update.message.reply_text(f"🔍 Real Signal for {symbol}:\n{signal}")

    except Exception as e:
        print(f"[ERROR in /realsignal] {e}")
        await update.message.reply_text("❌ An error occurred while generating signal.")

# --- Run Bot ---
async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("signal", signal))
    app.add_handler(CommandHandler("trend", trend))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(CommandHandler("realsignal", realsignal))

    print("✅ Bot is running...")
    await app.run_polling()

# --- Run Everything ---
if __name__ == "__main__":
    asyncio.run(main())
