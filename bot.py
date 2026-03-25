import os
import logging
import asyncio
from datetime import datetime, timedelta

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ================= CONFIG =================
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8114050673

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================= DB SIMPLE =================
usuarios_vip = {}

def es_vip(user_id):
    if user_id == ADMIN_ID:
        return True
    if user_id in usuarios_vip:
        return usuarios_vip[user_id] > datetime.now()
    return False

def activar_vip(user_id, dias):
    usuarios_vip[user_id] = datetime.now() + timedelta(days=dias)

# ================= API =================
def consultar_nequi(numero):
    import requests

    try:
        r = requests.post(
            "https://extract.nequialpha.com/consultar",
            json={"telefono": numero},
            headers={"X-Api-Key": "M43289032FH23B"},
            timeout=5
        )

        if r.status_code == 200:
            data = r.json()
            return data.get("nombre", "No disponible")

    except Exception as e:
        logger.error(e)

    return "No disponible"

# ================= COMANDOS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚔️ SISTEMA ACTIVO ⚔️\n\n"
        "🔎 /nequi 300XXXXXXX\n"
        "🔑 /vip ID DIAS\n\n"
        "👑 @Broquicalifoxx"
    )

async def nequi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not es_vip(user_id):
        await update.message.reply_text("❌ Acceso denegado")
        return

    if not context.args:
        await update.message.reply_text("Uso: /nequi 3001234567")
        return

    numero = context.args[0]
    msg = await update.message.reply_text("🔍 Consultando...")

    nombre = await asyncio.to_thread(consultar_nequi, numero)

    await msg.edit_text(
        f"📱 {numero}\n👤 {nombre}\n\n👑 @Broquicalifoxx"
    )

async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        user = int(context.args[0])
        dias = int(context.args[1])
        activar_vip(user, dias)
        await update.message.reply_text("✅ VIP activado")
    except:
        await update.message.reply_text("Uso: /vip ID DIAS")

# ================= MAIN =================

if __name__ == "__main__":
    print("🔥 BOT REAL CORRIENDO")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("nequi", nequi))
    app.add_handler(CommandHandler("vip", vip))

    app.run_polling()