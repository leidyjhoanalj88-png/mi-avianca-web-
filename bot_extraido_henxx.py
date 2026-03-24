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
        cursor.execute("SELECT expire_at FROM users WHERE user_id=%s", (user_id,))
        row = cursor.fetchone()

        if row and row[0]:
            return datetime.now() < row[0]
        return False
    except:
        return False
    finally:
        conn.close()

# ================= DISEÑO =================

MENU_TEXTO = """
╔══════════════════════════════╗
   🤖 DOXEO_CONSULTAS ⚔️
   👑 Owner: @Broquicalifa
╚══════════════════════════════╝

🔍 CONSULTAS
/consultar ➛ Consulta SISBEN
/cc <cedula> ➛ Buscar datos

🔐 ACCESO
/redeem <KEY> ➛ Activar acceso
/estado ➛ Ver estado

👑 ADMIN
/genkey <dias> ➛ Crear key
/adduser <id> ➛ Dar acceso
/deluser <id> ➛ Quitar acceso
/listusers ➛ Ver usuarios

⚙️ SISTEMA
/start ➛ Iniciar
/help ➛ Comandos

⚠️ Uso responsable
"""

# ================= COMANDOS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(MENU_TEXTO)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(MENU_TEXTO)

# ================= ESTADO =================

async def estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    conn = get_connection()
    if not conn:
        await update.message.reply_text("❌ Error DB")
        return

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT expire_at FROM users WHERE user_id=%s", (user_id,))
        row = cursor.fetchone()

        if row and row[0]:
            if datetime.now() < row[0]:
                await update.message.reply_text(f"✅ Activo hasta: {row[0]}")
            else:
                await update.message.reply_text("❌ Acceso expirado")
        else:
            await update.message.reply_text("❌ No tienes acceso")
    finally:
        conn.close()

# ================= GENKEY =================

async def genkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("❌ No autorizado")
        return

    dias = int(context.args[0]) if context.args else 30
    key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

    conn = get_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO user_keys (key_code, duration_days, redeemed) VALUES (%s,%s,FALSE)",
            (key, dias)
        )
        conn.commit()
        await update.message.reply_text(f"🔑 KEY:\n{key}\n⏳ {dias} días")
    finally:
        conn.close()

# ================= REDEEM =================

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usa: /redeem KEY")
        return

    key = context.args[0]
    user_id = update.message.from_user.id

    conn = get_connection()
    if not conn:
        return

    try:
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

        await update.message.reply_text("✅ Acceso activado")
    finally:
        conn.close()

# ================= ADMIN =================

async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    user_id = int(context.args[0])
    expire = datetime.now() + timedelta(days=30)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO users (user_id, expire_at)
    VALUES (%s,%s)
    ON DUPLICATE KEY UPDATE expire_at=%s
    """, (user_id, expire, expire))
    conn.commit()
    conn.close()

    await update.message.reply_text("✅ Usuario agregado")

async def deluser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    user_id = int(context.args[0])

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE user_id=%s", (user_id,))
    conn.commit()
    conn.close()

    await update.message.reply_text("❌ Usuario eliminado")

async def listusers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, expire_at FROM users")

    texto = "👥 Usuarios:\n\n"
    for u in cursor.fetchall():
        texto += f"{u[0]} ➛ {u[1]}\n"

    conn.close()
    await update.message.reply_text(texto)

# ================= CONSULTA =================

async def consultar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not usuario_tiene_acceso(update.message.from_user.id):
        await update.message.reply_text("🔒 Sin acceso")
        return

    await update.message.reply_text("🔍 Consulta SISBEN en mantenimiento")

# ================= MAIN =================

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("estado", estado))
    app.add_handler(CommandHandler("genkey", genkey))
    app.add_handler(CommandHandler("redeem", redeem))
    app.add_handler(CommandHandler("adduser", adduser))
    app.add_handler(CommandHandler("deluser", deluser))
    app.add_handler(CommandHandler("listusers", listusers))
    app.add_handler(CommandHandler("consultar", consultar))

    print("BOT ACTIVO 🔥")
    app.run_polling()

if __name__ == "__main__":
    main()