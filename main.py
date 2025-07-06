from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import logging
import datetime
import random

# Enable logs
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "7958535571:AAHR2XRy25ir6deEJq2tXcbCYpFLXYN97Bs"  

# Store fake trade data
trade_log = []

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hello Elvin! Your trading bot is live and ready!")

# /signal command
async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Simulate a BUY or SELL
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

# Build the bot app
app = ApplicationBuilder().token(BOT_TOKEN).build()

# Add commands
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("signal", signal))
app.add_handler(CommandHandler("trend", trend))
app.add_handler(CommandHandler("summary", summary))

# Start the bot
print("✅ Bot is running...")
app.run_polling()
