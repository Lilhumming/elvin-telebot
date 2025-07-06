from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import logging
import datetime
import random
import yfinance as yf
import pandas as pd
from flask import Flask
import threading

# Dummy Flask web server to keep Render alive
web = Flask(__name__)

@web.route('/')
def home():
    return "Elvin's bot is running."

def run_web():
    web.run(host="0.0.0.0", port=10000)

# Enable logs
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "7958535571:AAFxdEWVTNUElUguXJETpOERE_Vb4eqBTk"

# Store fake trade data
trade_log = []

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hello Elvin! Your trading bot is live and ready!")

# /signal command
async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    signal_type = random.choice(["BUY", "SELL"])
    result = random.choice(["Win", "Loss"])
    trade_log.append({"signal": signal_type, "result": result, "time": datetime.datetime.now()})
    await update.message.reply_text(f"📈 {signal_type} signal triggered!\nResult: {result}")

# /trend command
async def trend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    trend = random.choice(["📈 UPTREND", "📉 DOWNTREND", "🔁 SIDEWAYS"])
    await update.message.reply_text(f"Current Market Trend: {trend}")

# /summary command
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

# /realsignal command using live RSI from yfinance
async def realsignal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = "EURUSD=X"  # Can be BTC-USD, AAPL, etc.
    data = yf.download(tickers=symbol, period="1d", interval="5m")

    if data.empty:
        await update.message.reply_text("⚠️ Failed to load market data.")
        return

    # Calculate 14-period RSI
    delta = data["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    last_rsi = rsi.iloc[-1]

    # Generate Signal
    if last_rsi < 30:
        signal = "📈 BUY (RSI = {:.2f})".format(last_rsi)
    elif last_rsi > 70:
        signal = "📉 SELL (RSI = {:.2f})".format(last_rsi)
    else:
        signal = "⏸️ HOLD (RSI = {:.2f})".format(last_rsi)

    await update.message.reply_text(f"🔍 Real Signal for {symbol}:\n{signal}")

# Build Telegram bot
app = ApplicationBuilder().token(BOT_TOKEN).build()

# Add handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("signal", signal))
app.add_handler(CommandHandler("trend", trend))
app.add_handler(CommandHandler("summary", summary))
app.add_handler(CommandHandler("realsignal", realsignal))

# Start both the web server and Telegram bot
threading.Thread(target=run_web).start()
print("✅ Bot is running...")
app.run_polling()
