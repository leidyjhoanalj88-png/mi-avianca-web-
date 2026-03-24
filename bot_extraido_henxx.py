import mysql.connector
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from mysql.connector import pooling
import logging
from datetime import datetime, timedelta
import os
import re

# --- LOGGING ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- TOKEN ---
TOKEN = os.environ.get("BOT_TOKEN")

if not TOKEN:
    raise ValueError("❌ No se encontró BOT_TOKEN")

# --- ADMINS ---
ADMIN_IDS = [8114050673, 8575033873]

# --- DB ---
def get_db_pool():
    try:
        return mysql.connector.pooling.MySQLConnectionPool(
            pool_name="pool_db",
            pool_size=10,
            host=os.environ.get("MYSQLHOST", "mysql"),
            port=int(os.environ.get("MYSQLPORT", 3306)),
            user=os.environ.get("MYSQLUSER", "root"),
            password=os.environ.get("MYSQLPASSWORD", ""),
            database=os.environ.get("MYSQLDATABASE", "railway"),
            charset="utf8"
        )
    except Exception as e:
        logger.error(f"Error pool: {e}")
        return None

pool = get_db_pool()

def get_connection():
    if pool is None:
        return None
    try:
        return pool.get_connection()
    except:
        return None

# --- ACCESO ---
def tiene_key_valida(user_id):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        query = """
        SELECT 1 FROM user_keys 
        WHERE user_id = %s 
        AND redeemed = TRUE 
        AND expiration_date > NOW()
        """
        cursor.execute(query, (user_id,))
        return cursor.fetchone() is not None
    finally:
        conn.close()

def usuario_tiene_acceso(user_id):
    if user_id in ADMIN_IDS:
        return True
    return tiene_key_valida(user_id)

# --- CONSULTA CC ---
def buscar_cedula(cedula):
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM ani WHERE ANINuip = %s", (cedula,))
        return cursor.fetchone()
    finally:
        conn.close()

# --- COMANDOS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚔️ BOT ACTIVO ⚔️\nUsa /help")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = """
⚔️ COMANDOS ⚔️

🔍 CONSULTAS
/cc <cedula>

🔐 ACCESO
/key <clave>
/estado
"""
    await update.message.reply_text(texto)

async def estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if usuario_tiene_acceso(user_id):
        await update.message.reply_text("✅ Tienes acceso activo")
    else:
        await update.message.reply_text("❌ No tienes suscripción")

async def activar_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if not context.args:
        await update.message.reply_text("Uso: /key CLAVE")
        return

    key = context.args[0]

    conn = get_connection()
    if not conn:
        await update.message.reply_text("❌ Error DB")
        return

    try:
        cursor = conn.cursor()

        cursor.execute("""
        SELECT id, duration_days FROM user_keys 
        WHERE key_code = %s AND redeemed = FALSE
        """, (key,))
        result = cursor.fetchone()

        if not result:
            await update.message.reply_text("❌ Clave inválida o usada")
            return

        key_id, dias = result
        expiration = datetime.now() + timedelta(days=dias)

        cursor.execute("""
        UPDATE user_keys 
        SET user_id=%s, redeemed=TRUE, expiration_date=%s 
        WHERE id=%s
        """, (user_id, expiration, key_id))

        conn.commit()
        await update.message.reply_text(f"✅ Activado por {dias} días")

    finally:
        conn.close()

async def mostrar_datos_cedula(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if not usuario_tiene_acceso(user_id):
        await update.message.reply_text("❌ Sin acceso")
        return

    # acepta /cc123 o /cc 123
    texto = update.message.text
    match = re.search(r'/cc\s*(\d+)', texto)

    if not match:
        await update.message.reply_text("Uso: /cc 123456")
        return

    cedula = match.group(1)
    datos = buscar_cedula(cedula)

    if not datos:
        await update.message.reply_text("❌ No encontrado")
        return

    nombre = datos.get('ANINombre1') or "No registra"
    apellido = datos.get('ANIApellido1') or ""

    msg = (
        "┏━━━━━━━━━━━━━━━━━━━⩺\n"
        "┃ 🪪 CONSULTA CC\n"
        "┃\n"
        f"┃ ⚔️ CC: {cedula}\n"
        f"┃ 👤 Nombre: {nombre} {apellido}\n"
        "┗━━━━━━━━━━━━━━━━━━━⩺"
    )

    await update.message.reply_text(msg)

# --- REGISTRO ---
async def registrar_usuario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    conn = get_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT IGNORE INTO users (user_id, username)
        VALUES (%s, %s)
        """, (user.id, user.username))
        conn.commit()
    finally:
        conn.close()

# --- MAIN ---
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("estado", estado))
    app.add_handler(CommandHandler("key", activar_key))
    app.add_handler(CommandHandler("cc", mostrar_datos_cedula))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, registrar_usuario))

    logger.info("Bot corriendo...")
    app.run_polling()

if __name__ == "__main__":
    main()