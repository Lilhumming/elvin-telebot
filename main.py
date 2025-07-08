from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import logging
import datetime
import random
import yfinance as yf
import pandas as pd
from flask import Flask
import threading
import asyncio

# Flask web server to keep Render alive
web = Flask(__name__)

@web.route('/')
def home():
    return "Elvin's bot is running."

def run_web():
    web.run(host="0.0.0.0", port=10000)

# Enable logging
logging.basicConfig(level=logging.INFO)

# Your Telegram bot token and chat ID
BOT_TOKEN = "7958535571:AAEVB49WOrlb5JNttueQeRxwDoGiCxLHZgc"
ELVIN_ID = 7147175084

# Store trade results
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

# /realsignal command
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
            await update.message.reply_text("⚠️ RSI calculation failed — insufficient data.")
            return

        last_rsi = float(rsi.iloc[-1])
        print(f"[RSI] Last RSI for {symbol}: {last_rsi}")

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

# Background RSI every 10 minutes (except Saturday)
async def auto_rsi():
    await app.bot.send_chat_action(chat_id=ELVIN_ID, action=ChatAction.TYPING)
    while True:
        now = datetime.datetime.now()
        if now.weekday() != 5:  # 5 = Saturday
            try:
                symbol = "EURUSD=X"
                data = yf.download(tickers=symbol, period="1d", interval="5m")
                delta = data["Close"].diff()
                gain = delta.clip(lower=0)
                loss = -delta.clip(upper=0)

                avg_gain = gain.rolling(window=14).mean()
                avg_loss = loss.rolling(window=14).mean()

                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                rsi = rsi.dropna()

                if not rsi.empty:
                    last_rsi = float(rsi.iloc[-1])

                    if last_rsi < 30:
                        signal = f"📈 BUY (RSI = {last_rsi:.2f})"
                    elif last_rsi > 70:
                        signal = f"📉 SELL (RSI = {last_rsi:.2f})"
                    else:
                        signal = f"⏸️ HOLD (RSI = {last_rsi:.2f})"

                    await app.bot.send_message(chat_id=ELVIN_ID, text=f"🔔 Auto RSI Signal:\n{signal}")
            except Exception as e:
                print(f"[Auto RSI Error] {e}")

        await asyncio.sleep(600)  # 10 minutes

# Initialize bot
app = ApplicationBuilder().token(BOT_TOKEN).build()

# Add command handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("signal", signal))
app.add_handler(CommandHandler("trend", trend))
app.add_handler(CommandHandler("summary", summary))
app.add_handler(CommandHandler("realsignal", realsignal))

# Start Flask + Bot + Background Task
threading.Thread(target=run_web).start()

async def main():
    asyncio.create_task(auto_rsi())
    print("✅ Bot is running with auto RSI...")
    await app.run_polling()

asyncio.run(main())
