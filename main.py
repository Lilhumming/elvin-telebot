import os
import logging
import datetime
import threading
import time
import yfinance as yf
from telegram import Bot
from telegram.ext import ApplicationBuilder, CommandHandler

# === Config ===
TOKEN = "7958535571:AAFmkGqAnL40Xg4Y67rlZqVkYyD_FI4Jle8"
CHAT_ID = 7147175084
SYMBOLS = ["BTC-USD", "AAPL", "ETH-USD", "GBPUSD=X", "EURUSD=X"]  # Add/remove pairs here
INTERVAL = 600  # 10 minutes in seconds
RSI_PERIOD = 14

# === Logging ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === RSI Calculation ===
def calculate_rsi(data, period=RSI_PERIOD):
    delta = data.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# === Signal Generator ===
def generate_signal(symbol):
    now = datetime.datetime.now()
    if now.weekday() == 5:  # Saturday = Silent Mode
        logger.info("Silent Saturday. No signal sent.")
        return None

    data = yf.download(symbol, period="2d", interval="15m", progress=False)
    if data.empty or "Close" not in data:
        logger.error(f"Failed to fetch price data for {symbol}")
        return None

    rsi = calculate_rsi(data["Close"])
    latest_rsi = rsi.dropna().iloc[-1]

    if latest_rsi < 30:
        signal = f"📊 {symbol}\n📈 RSI: {latest_rsi:.2f}\n🔵 Signal: BUY"
    elif latest_rsi > 70:
        signal = f"📊 {symbol}\n📉 RSI: {latest_rsi:.2f}\n🔴 Signal: SELL"
    else:
        signal = f"📊 {symbol}\n⚪ RSI: {latest_rsi:.2f}\n⏸️ Signal: HOLD"

    logger.info(f"Signal for {symbol}: {signal}")
    return signal

# === Send All Signals ===
def signal_loop(bot: Bot):
    while True:
        try:
            for symbol in SYMBOLS:
                signal = generate_signal(symbol)
                if signal:
                    bot.send_message(chat_id=CHAT_ID, text=signal)
        except Exception as e:
            logger.error(f"Error in signal loop: {e}")
        time.sleep(INTERVAL)

# === Bot Commands ===
async def start(update, context):
    await update.message.reply_text("🤖 I'm monitoring RSI signals for multiple assets!")

async def help_command(update, context):
    await update.message.reply_text("💡 This bot sends RSI-based signals every 10 minutes for:\n" + "\n".join(SYMBOLS) + "\n(Silent on Saturdays)")

# === Main ===
def main():
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    bot = Bot(token=TOKEN)

    # Background RSI signal thread
    thread = threading.Thread(target=signal_loop, args=(bot,))
    thread.daemon = True
    thread.start()

    application.run_polling()

if __name__ == "__main__":
    main()
