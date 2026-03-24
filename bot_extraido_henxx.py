import os
import logging
import random
import string
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ================= CONFIG =================

TOKEN = os.environ.get("BOT_TOKEN")

ADMIN_ID = 8114050673  # 👑 TU ID
OWNER = "@Broquicalifa"

logging.basicConfig(level=logging.INFO)

# ================= DB =================

def get_connection():
    try:
        import mysql.connector
        return mysql.connector.connect(
            host=os.environ.get("DB_HOST"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASS"),
            database=os.environ.get("DB_NAME")
        )
    except:
        return None

# ================= FUNCIONES =================

def es_admin(user_id):
    return user_id == ADMIN_ID

def usuario_tiene_acceso(user_id):
    if es_admin(user_id):
        return True

    conn = get_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT expire_at FROM users WHERE user_id=%s", (user_id,))
        row = cursor.fetchone()

        if row and row[0]:
            return datetime.now() < row[0]
        return False
    finally:
        conn.close()

# ================= DISEÑO =================

MENU = f"""
╔══════════════════════════════╗
   🤖 DOXEO_CONSULTAS ⚔️
   👑 Owner: {OWNER}
╚══════════════════════════════╝

🔍 CONSULTAS
/consultar ➛ SISBEN
/cc <cedula> ➛ Datos
/nequi <numero> ➛ Titular Nequi

🔐 ACCESO
/redeem <KEY>
/estado

👑 ADMIN
/genkey <dias>

⚙️ SISTEMA
/start
/help
"""

# ================= COMANDOS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(MENU)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(MENU)

# ================= NEQUI =================

async def nequi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if not usuario_tiene_acceso(user_id):
        await update.message.reply_text("🔒 Sin acceso")
        return

    if not context.args:
        await update.message.reply_text("Uso: /nequi 3001234567")
        return

    numero = context.args[0]

    # ⚠️ aquí puedes conectar API real luego
    resultado = f"Consulta simulada para {numero}"

    await update.message.reply_text(
        f"┏━━━━━━━━━━━━━━━⩺\n"
        f"┃ 📱 NEQUI\n"
        f"┃\n"
        f"┃ Número: {numero}\n"
        f"┃ Resultado: {resultado}\n"
        f"┗━━━━━━━━━━━━━━━⩺"
    )

# ================= GENKEY =================

async def genkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not es_admin(update.message.from_user.id):
        await update.message.reply_text("❌ No autorizado")
        return

    dias = int(context.args[0]) if context.args else 30
    key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

    conn = get_connection()
    if not conn:
        return

    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO user_keys (key_code, duration_days, redeemed) VALUES (%s,%s,FALSE)",
        (key, dias)
    )
    conn.commit()
    conn.close()

    await update.message.reply_text(f"🔑 KEY:\n{key}")

# ================= REDEEM =================

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /redeem KEY")
        return

    key = context.args[0]
    user_id = update.message.from_user.id

    conn = get_connection()
    if not conn:
        return

    cursor = conn.cursor()
    cursor.execute("SELECT duration_days, redeemed FROM user_keys WHERE key_code=%s", (key,))
    row = cursor.fetchone()

    if not row:
        await update.message.reply_text("❌ Key inválida")
        return

    if row[1]:
        await update.message.reply_text("❌ Ya usada")
        return

    expire = datetime.now() + timedelta(days=row[0])

    cursor.execute("""
    INSERT INTO users (user_id, expire_at)
    VALUES (%s,%s)
    ON DUPLICATE KEY UPDATE expire_at=%s
    """, (user_id, expire, expire))

    cursor.execute("UPDATE user_keys SET redeemed=TRUE WHERE key_code=%s", (key,))
    conn.commit()
    conn.close()

    await update.message.reply_text("✅ Acceso activado")

# ================= ESTADO =================

async def estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if usuario_tiene_acceso(update.message.from_user.id):
        await update.message.reply_text("✅ Tienes acceso")
    else:
        await update.message.reply_text("❌ Sin acceso")

# ================= CONSULTA =================

async def consultar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not usuario_tiene_acceso(update.message.from_user.id):
        await update.message.reply_text("🔒 Sin acceso")
        return

    await update.message.reply_text("🔍 SISBEN en proceso...")

# ================= MAIN =================

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("nequi", nequi))
    app.add_handler(CommandHandler("genkey", genkey))
    app.add_handler(CommandHandler("redeem", redeem))
    app.add_handler(CommandHandler("estado", estado))
    app.add_handler(CommandHandler("consultar", consultar))

    print("🔥 BOT ACTIVO")
    app.run_polling()

if __name__ == "__main__":
    main()