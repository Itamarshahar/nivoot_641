import os
import io
import math
import requests
from PIL import Image
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# --- Map Download Function ---

def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    x_tile = int((lon_deg + 180.0) / 360.0 * n)
    y_tile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return x_tile, y_tile

def download_map_image(lat, lon, zoom=15):
    """
    Download topographic map tile and return as BytesIO object.
    """
    x_tile, y_tile = deg2num(lat, lon, zoom)
    url = f"https://tile.opentopomap.org/{zoom}/{x_tile}/{y_tile}.png"

    response = requests.get(url)
    response.raise_for_status()

    image = Image.open(io.BytesIO(response.content))

    buf = io.BytesIO()
    image.save(buf, format='PNG')
    buf.seek(0)
    return buf

# --- Bot Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! 👋 Send me latitude and longitude separated by a comma.\n"
        "Example: `32.0853, 34.7818`\n"
        "I'll send you a topographic map of that location!"
    )

async def handle_coords(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Parse coordinates
        lat_str, lon_str = update.message.text.split(',')
        lat = float(lat_str.strip())
        lon = float(lon_str.strip())

        # Download map
        image_buffer = download_map_image(lat, lon)

        # Send map image
        await update.message.reply_photo(photo=image_buffer)

    except ValueError:
        await update.message.reply_text(
            "⚠️ Please send the coordinates in the correct format: `latitude, longitude`"
        )
    except requests.RequestException:
        await update.message.reply_text(
            "⚠️ Couldn't fetch the map. Server error. Try again later."
        )
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")

# --- Main Application ---

def main():
    TOKEN = os.getenv("7643327737:AAHw8a2wxyQatDC0IOmrbrBtc5vxqN5R8Eg")
    if not TOKEN:
        print("❌ BOT_TOKEN environment variable not set!")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_coords))

    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

