from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import logging
import datetime
import random
import yfinance as yf
import pandas as pd
from flask import Flask
import threading
import asyncio
import os
import csv
import traceback

# === Flask Web Server to Keep Render Alive ===
web = Flask(__name__)

@web.route('/')
def home():
    return "Elvin's bot is running."

def run_web():
    web.run(host="0.0.0.0", port=10000)

# === Bot Configuration ===
logging.basicConfig(level=logging.INFO)
BOT_TOKEN = "7958535571:AAEVB49WOrlb5JNttueQeRxwDoGiCxLHZgc"
CHAT_ID = 7147175084  # ← Your personal Telegram Chat ID
trade_log = []
CSV_FILE = "signals.csv"

# === Manual Bot Commands ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hello Elvin! Your trading bot is alive and running!")

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
        signal_msg = await get_rsi_signal()
        await update.message.reply_text(signal_msg)
    except Exception as e:
        traceback.print_exc()
        await update.message.reply_text("❌ An error occurred while generating signal.")

# === RSI Signal Function ===
async def get_rsi_signal():
    symbol = "EURUSD=X"
    data = yf.download(tickers=symbol, period="1d", interval="5m")

    if data.empty:
        return "⚠️ Market data load failed from yfinance."

    delta = data["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    rsi_clean = rsi.dropna()

    last_rsi = rsi_clean.iloc[-1] if not rsi_clean.empty else None
    if last_rsi is None:
        return "⚠️ Not enough data to calculate RSI."

    rsi_value = float(last_rsi)
    print(f"[AUTO] RSI for {symbol}: {rsi_value:.2f}")

    if rsi_value < 30:
        signal = f"📈 BUY (RSI = {rsi_value:.2f})"
    elif rsi_value > 70:
        signal = f"📉 SELL (RSI = {rsi_value:.2f})"
    else:
        signal = f"⏸️ HOLD (RSI = {rsi_value:.2f})"

    log_to_csv(datetime.datetime.now(), symbol, rsi_value, signal)
    return f"🔔 Auto Signal:\n{signal}"

# === CSV Logger ===
def log_to_csv(time, symbol, rsi, signal):
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, mode='a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Time", "Symbol", "RSI", "Signal"])
        writer.writerow([time, symbol, f"{rsi:.2f}", signal])

# === Background RSI Task (every 10 mins, except Saturdays) ===
async def background_rsi_task(app):
    while True:
        now = datetime.datetime.utcnow()
        if now.weekday() == 5:  # Saturday = 5
            print("⏸️ Silent mode: skipping auto alerts on Saturday.")
        else:
            try:
                message = await get_rsi_signal()
                await app.bot.send_message(chat_id=CHAT_ID, text=message)
            except Exception as e:
                print(f"[ERROR in auto signal] {e}")
        await asyncio.sleep(600)  # 10 minutes

# === Initialize Bot ===
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("signal", signal))
app.add_handler(CommandHandler("trend", trend))
app.add_handler(CommandHandler("summary", summary))
app.add_handler(CommandHandler("realsignal", realsignal))

# === Run Everything ===
threading.Thread(target=run_web).start()
print("✅ Bot is running...")

async def run_all():
    await asyncio.gather(
        app.initialize(),
        background_rsi_task(app),
        app.start(),
        app.updater.start_polling()
    )

asyncio.run(run_all())
