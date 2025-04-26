import os
import io
import math
import requests
from PIL import Image
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# --- Map Download Functions ---

def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    x_tile = int((lon_deg + 180.0) / 360.0 * n)
    y_tile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return x_tile, y_tile

def num2deg(x_tile, y_tile, zoom):
    n = 2.0 ** zoom
    lon_deg = x_tile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y_tile / n)))
    lat_deg = math.degrees(lat_rad)
    return lat_deg, lon_deg

def download_tile(x_tile, y_tile, zoom):
    url = f"https://tile.opentopomap.org/{zoom}/{x_tile}/{y_tile}.png"
    response = requests.get(url)
    response.raise_for_status()
    return Image.open(io.BytesIO(response.content))

def download_map_image(lat, lon, zoom=15, tile_range=1):
    """
    Download multiple tiles and stitch them into one big map image.
    tile_range=1 means a 3x3 grid (center + 1 tile in each direction).
    """
    center_x, center_y = deg2num(lat, lon, zoom)

    tiles = []
    for y_offset in range(-tile_range, tile_range + 1):
        row = []
        for x_offset in range(-tile_range, tile_range + 1):
            try:
                tile = download_tile(center_x + x_offset, center_y + y_offset, zoom)
            except Exception:
                tile = Image.new('RGB', (256, 256), (255, 255, 255))  # Empty white tile if fail
            row.append(tile)
        tiles.append(row)

    # Stitch tiles together
    tile_size = 256
    map_width = tile_size * (2 * tile_range + 1)
    map_height = tile_size * (2 * tile_range + 1)
    map_image = Image.new('RGB', (map_width, map_height))

    for row_idx, row in enumerate(tiles):
        for col_idx, tile in enumerate(row):
            map_image.paste(tile, (col_idx * tile_size, row_idx * tile_size))

    buf = io.BytesIO()
    map_image.save(buf, format='PNG')
    buf.seek(0)
    return buf

# --- Bot Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! 👋 Send me latitude and longitude separated by a comma.\n"
        "Example: `32.0853, 34.7818`\n"
        "I'll send you a topographic map (8km x 8km) of that location!"
    )

async def handle_coords(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Parse coordinates
        lat_str, lon_str = update.message.text.split(',')
        lat = float(lat_str.strip())
        lon = float(lon_str.strip())

        # Download map (bigger area!)
        image_buffer = download_map_image(lat, lon, zoom=15, tile_range=1)

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
    TOKEN = "7643327737:AAHw8a2wxyQatDC0IOmrbrBtc5vxqN5R8Eg"

  # <- Replace here or use os.getenv("BOT_TOKEN")
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

