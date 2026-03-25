import mysql.connector
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from mysql.connector import pooling
import logging
import random
import string
from datetime import datetime, timedelta
import os
import subprocess
import tempfile
import requests
import json

# ================= CONFIG =================

TOKEN = os.environ.get("BOT_TOKEN")
OWNER = "@Broquicalifoxx"

# ================= LOG =================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

# ================= DB =================

pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="pool_db",
    pool_size=10,
    host="localhost",
    user="root",
    password="nabo94nabo94",
    database="ani",
    charset="utf8"
)

# ================= APIs =================

API_URL_C2 = "https://extract.nequialpha.com/doxing"
PLACA_API_URL = "https://alex-bookmark-univ-survival.trycloudflare.com/index.php"
START_IMAGE_URL = "https://i.postimg.cc/xTbPbYFN/photo-2026-01-29-18-20-26.jpg"
LLAVE_API_BASE = "https://believes-criterion-tricks-notifications.trycloudflare.com/"
TIMEOUT = 120

# ================= NEQUI =================

def consultar_nequi(telefono):
    try:
        url = "https://extract.nequialpha.com/consultar"
        headers = {
            "X-Api-Key": "M43289032FH23B",
            "Content-Type": "application/json"
        }
        payload = {"telefono": str(telefono)}
        r = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(f"Error Nequi: {e}")
        return None

# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = f"""
乄 SISTEMA OSCURO ⚔️
═════════════════════════
Acceso a módulos de información avanzada

┏━━━━━━━━━━━━━━━━━━━━━━━⩺
┃ ⚙️ COMANDOS
┃ ⚔️ /cc
┃ ⚔️ /c2
┃ ⚔️ /nequi
┃ ⚔️ /placa
┃ ⚔️ /llave
┗━━━━━━━━━━━━━━━━━━━━━━━⩺

⚠️ Uso interno
👁 Sistema monitoreado

👑 Owner: {OWNER}
"""

    await update.message.reply_photo(photo=START_IMAGE_URL, caption=texto)

# ================= NEQUI =================

async def comando_nequi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if not context.args:
        await update.message.reply_text("Uso: /nequi 3001234567")
        return

    telefono = context.args[0]

    msg = await update.message.reply_text("🔍 Consultando...")

    res = consultar_nequi(telefono)

    if not res:
        await msg.edit_text("❌ Error de conexión API")
        return

    mensaje = (
        f"╔══════════════════════════════╗\n"
        f"        🔎 RESULTADO 🔎\n"
        f"╚══════════════════════════════╝\n\n"
        f"📡 Consulta ejecutada\n"
        f"🧠 Datos procesados\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📱 Número: {res.get('telefono','No disponible')}\n"
        f"👤 Titular: {res.get('nombre_completo','No disponible')}\n"
        f"📊 Estado: {'OK' if res.get('db') else 'Sistema protegido'}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"⚠️ Información sensible\n"
        f"👁 Uso interno\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 {OWNER}"
    )

    await msg.edit_text(mensaje)

# ================= MAIN =================

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("nequi", comando_nequi))

    print("🔥 BOT ACTIVO")
    app.run_polling()

if __name__ == "__main__":
    main()