import os
import logging
import random
import string
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# ================= CONFIG =================

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

# ================= LOGS =================

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
    except Exception as e:
        print("DB ERROR:", e)
        return None

# ================= ACCESO =================

def usuario_tiene_acceso(user_id):
    conn = get_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT expire_at FROM users WHERE user_id = %s
        """, (user_id,))
        row = cursor.fetchone()

        if row and row[0]:
            return datetime.now() < row[0]

        return False
    except:
        return False
    finally:
        conn.close()

# ================= COMANDOS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚔️ BOT ACTIVO ⚔️\n\n"
        "Usa /redeem KEY para activar acceso"
    )

# ================= GENKEY =================

async def genkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ No autorizado")
        return

    dias = 30
    if context.args:
        try:
            dias = int(context.args[0])
        except:
            pass

    key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

    conn = get_connection()
    if not conn:
        await update.message.reply_text("❌ Error DB")
        return

    try:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO user_keys (key_code, duration_days, redeemed)
        VALUES (%s, %s, FALSE)
        """, (key, dias))
        conn.commit()

        await update.message.reply_text(f"🔑 KEY:\n{key}\n⏳ {dias} días")
    finally:
        conn.close()

# ================= REDEEM =================

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if not context.args:
        await update.message.reply_text("Usa: /redeem TUKEY")
        return

    key = context.args[0]

    conn = get_connection()
    if not conn:
        await update.message.reply_text("❌ Error DB")
        return

    try:
        cursor = conn.cursor()

        cursor.execute("""
        SELECT duration_days, redeemed FROM user_keys WHERE key_code = %s
        """, (key,))
        row = cursor.fetchone()

        if not row:
            await update.message.reply_text("❌ Key inválida")
            return

        if row[1]:
            await update.message.reply_text("❌ Key ya usada")
            return

        dias = row[0]
        expire = datetime.now() + timedelta(days=dias)

        cursor.execute("""
        INSERT INTO users (user_id, expire_at)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE expire_at=%s
        """, (user_id, expire, expire))

        cursor.execute("""
        UPDATE user_keys SET redeemed=TRUE WHERE key_code=%s
        """, (key,))

        conn.commit()

        await update.message.reply_text(f"✅ Acceso activado por {dias} días")

    finally:
        conn.close()

# ================= CONSULTA =================

async def consultar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if not usuario_tiene_acceso(user_id):
        await update.message.reply_text("🔒 Sin acceso")
        return

    await update.message.reply_text("🔍 Consulta SISBÉN en mantenimiento")

# ================= DEBUG =================

async def debug_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("MENSAJE:", update.message.text)

# ================= MAIN =================

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("genkey", genkey))
    app.add_handler(CommandHandler("redeem", redeem))
    app.add_handler(CommandHandler("consultar", consultar))

    app.add_handler(MessageHandler(filters.ALL, debug_all))

    print("BOT CORRIENDO...")
    app.run_polling()

if __name__ == "__main__":
    main()