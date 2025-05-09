import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from saver import transform_coordinates, main as download_map

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Bot Handlers ---

async def start(update: Update):
    await update.message.reply_text(
        'Hi! Send me one coordinate pair and a size, like this:\n\nlat, lon, width, height\n\nExample:\n31.3257, 34.8332, 3500, 5500'
    )

from telegram import Update
from telegram.ext import ContextTypes

async def coordinates_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    try:
        # Step 1: expecting lat, lon
        if 'coords' not in context.user_data:
            parts = list(map(float, text.split(',')))
            if len(parts) != 2:
                raise ValueError("Please send two numbers: latitude, longitude (WGS84)")

            lat, lon = parts
            context.user_data['coords'] = {'lat': lat, 'lon': lon}

            await update.message.reply_text("Great! Now send me two more numbers: width, height (meters)")
            return

        # Step 2: expecting width, height
        parts = list(map(float, text.split(',')))
        if len(parts) != 2:
            raise ValueError("Now please send two numbers: width, height")

        width, height = parts
        lat = context.user_data['coords']['lat']
        lon = context.user_data['coords']['lon']

        await update.message.reply_text("Got it! Generating the map, please wait... (this might take ~10–20 seconds)")

        # Convert to tile coordinates
        x, y = transform_coordinates(longitude=lon, latitude=lat)
        output_file = "result_map.png"

        await download_map(x, y, width, height, name=output_file)

        with open(output_file, 'rb') as f:
            await update.message.reply_document(f)

        context.user_data.clear()

    except Exception as e:
        logger.exception("Error handling coordinates:")
        await update.message.reply_text(f"Error: {str(e)}\nStep 1: Send lat, lon\nStep 2: Send width, height")
        context.user_data.clear()

# --- Main Bot ---

def main():
    # Load the Telegram token from environment variable
    # Make sure to set this environment variable in your deployment environment

    logger.info("=== Starting the bot ===")    
    
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

    if not TELEGRAM_TOKEN:
        raise ValueError("No TELEGRAM_TOKEN environment variable set.")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, coordinates_handler))

    app.run_polling()

if __name__ == "__main__":
    main()
