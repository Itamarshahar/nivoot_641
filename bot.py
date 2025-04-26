from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import matplotlib.pyplot as plt
import io

# Replace with your own script function
def generate_topo_map(lat: float, lon: float) -> io.BytesIO:
    fig = your_existing_map_function(lat, lon)  # Should return a matplotlib figure
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)
    return buf

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me latitude and longitude separated by a comma. For example: `32.0853, 34.7818`")

async def handle_coords(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        lat_str, lon_str = update.message.text.split(',')
        lat, lon = float(lat_str.strip()), float(lon_str.strip())
        image_buffer = generate_topo_map(lat, lon)
        await update.message.reply_photo(photo=image_buffer)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}\nPlease send coordinates like this: `latitude, longitude`")

if __name__ == '__main__':
    import os

    TOKEN = "7643327737:AAHw8a2wxyQatDC0IOmrbrBtc5vxqN5R8Eg"
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_coords))

    print("Bot is running...")
    app.run_polling()

