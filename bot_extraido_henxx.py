import mysql.connector
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from mysql.connector import pooling
import logging
from datetime import datetime, timedelta
import os
import re
import requests  # 🔥 agregado

# --- LOGGING ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- TOKEN ---
TOKEN = os.environ.get("BOT_TOKEN")
ABSTRACT_API_KEY = os.environ.get("ABSTRACT_KEY")  # 🔥 agregado

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

# ================= DISEÑO ACCESO =================
async def sin_acceso(update):
    await update.message.reply_text("""
╔══════════════════════╗
        🔒 ACCESO
╚══════════════════════╝

❌ No tienes acceso activo

💎 Compra acceso:
📩 @broquicalifa
━━━━━━━━━━━━━━━━━━━━━━━
""")

# --- COMANDOS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    texto = f"""
╔══════════════════════════════╗
        ⚔️ 𝗗𝗢𝗥𝗦𝗘𝗧 𝗕𝗢𝗧 ⚔️
╚══════════════════════════════╝

👤 {user.first_name} | 🆔 {user.id}

🔍 CONSULTAS
┣ /cc 123456789
┣ /sisben 123456789
┣ /nequi 3001234567

🌐 OSINT
┣ /numero +573001234567
┣ /ip 8.8.8.8
┣ /email correo@gmail.com

🔐 ACCESO
┣ /key CLAVE
┣ /estado

━━━━━━━━━━━━━━━━━━━━━━━
🛠 @broquicalifa
"""
    await update.message.reply_text(texto)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if usuario_tiene_acceso(update.effective_user.id):
        await update.message.reply_text("✅ Acceso activo")
    else:
        await sin_acceso(update)

# --- KEY ---
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
            await update.message.reply_text("❌ Clave inválida")
            return

        key_id, dias = result
        expiration = datetime.now() + timedelta(days=dias)

        cursor.execute("""
        UPDATE user_keys 
        SET user_id=%s, redeemed=TRUE, expiration_date=%s 
        WHERE id=%s
        """, (user_id, expiration, key_id))

        conn.commit()
        await update.message.reply_text(f"✅ Activado {dias} días")

    finally:
        conn.close()

# ================= CONSULTAS =================

# CC
async def mostrar_datos_cedula(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not usuario_tiene_acceso(update.effective_user.id):
        return await sin_acceso(update)

    match = re.search(r'/cc\s*(\d+)', update.message.text)
    if not match:
        return await update.message.reply_text("Uso: /cc 123456")

    cedula = match.group(1)
    datos = buscar_cedula(cedula)

    if not datos:
        return await update.message.reply_text("❌ No encontrado")

    nombre = datos.get('ANINombre1') or "No registra"
    apellido = datos.get('ANIApellido1') or ""

    msg = f"""
╔══════════════════════╗
        🪪 CC
╚══════════════════════╝

📄 {cedula}
👤 {nombre} {apellido}

━━━━━━━━━━━━━━━━━━━━━━━
🛠 @broquicalifa
"""
    await update.message.reply_text(msg)

# SISBEN
async def sisben(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not usuario_tiene_acceso(update.effective_user.id):
        return await sin_acceso(update)

    if not context.args:
        return await update.message.reply_text("Uso: /sisben 123")

    doc = context.args[0]

    msg = f"""
╔══════════════════════╗
        📊 SISBÉN
╚══════════════════════╝

🪪 {doc}
🏷 Grupo: A2
📍 Bogotá

━━━━━━━━━━━━━━━━━━━━━━━
🛠 @broquicalifa
"""
    await update.message.reply_text(msg)

# NEQUI
async def nequi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not usuario_tiene_acceso(update.effective_user.id):
        return await sin_acceso(update)

    if not context.args:
        return await update.message.reply_text("Uso: /nequi 300...")

    num = context.args[0]

    msg = f"""
╔══════════════════════╗
        💳 NEQUI
╚══════════════════════╝

📱 {num}
👤 Titular: (pendiente API)

━━━━━━━━━━━━━━━━━━━━━━━
🛠 @broquicalifa
"""
    await update.message.reply_text(msg)

# ================= APIS =================

async def numero(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("Uso: /numero +57...")

    num = context.args[0]

    r = requests.get(f"https://phonevalidation.abstractapi.com/v1/?api_key={ABSTRACT_API_KEY}&phone={num}").json()

    msg = f"""
📞 NÚMERO
═══════════════
🌍 {r.get('country', {}).get('name')}
📡 {r.get('carrier')}
✔️ {r.get('valid')}
"""
    await update.message.reply_text(msg)

async def ip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("Uso: /ip 8.8.8.8")

    ip = context.args[0]

    r = requests.get(f"https://ipgeolocation.abstractapi.com/v1/?api_key={ABSTRACT_API_KEY}&ip_address={ip}").json()

    msg = f"""
🌐 IP
═══════════════
🌍 {r.get('country')}
🏙 {r.get('city')}
🔒 VPN: {r.get('security', {}).get('is_vpn')}
"""
    await update.message.reply_text(msg)

async def email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("Uso: /email correo")

    mail = context.args[0]

    r = requests.get(f"https://emailvalidation.abstractapi.com/v1/?api_key={ABSTRACT_API_KEY}&email={mail}").json()

    msg = f"""
📧 EMAIL
═══════════════
✔️ {r.get('deliverability')}
"""
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
    app.add_handler(CommandHandler("sisben", sisben))
    app.add_handler(CommandHandler("nequi", nequi))

    app.add_handler(CommandHandler("numero", numero))
    app.add_handler(CommandHandler("ip", ip))
    app.add_handler(CommandHandler("email", email))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, registrar_usuario))

    logger.info("🔥 BOT FULL ACTIVO 🔥")
    app.run_polling()

if __name__ == "__main__":
    main()