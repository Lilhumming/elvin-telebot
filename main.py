from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import logging

# Enable logging to see bot activity
logging.basicConfig(level=logging.INFO)

# Your actual Telegram Bot Token
BOT_TOKEN = "7958535571:AAHR2XRy25ir6deEJq2tXcbCYpFLXYN97Bs"

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hello Elvin! Your trading bot is live and ready!")

# /signal command
async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📈 BUY signal triggered! Time to trade.")

# Create the bot application
app = ApplicationBuilder().token(BOT_TOKEN).build()

# Add command handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("signal", signal))

# Run the bot
print("✅ Bot is running...")
app.run_polling()
