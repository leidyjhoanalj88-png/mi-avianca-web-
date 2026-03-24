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

# --- CONFIGURACIÓN DE LOGGING ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- CONFIGURACIÓN DE BASE DE DATOS ---
def get_db_pool():
    try:
        return mysql.connector.pooling.MySQLConnectionPool(
            pool_name="pool_db",
            pool_size=10,
            host=os.environ.get("MYSQLHOST", "mysql"), # Intenta 'mysql' a secas
            port=int(os.environ.get("MYSQLPORT", 3306)),
            user=os.environ.get("MYSQLUSER", "root"),
            password=os.environ.get("MYSQLPASSWORD", ""),
            database=os.environ.get("MYSQLDATABASE", "railway"),
            charset="utf8",
            connection_timeout=30
        )
    except Exception as e:
        logger.error(f"Error al crear el pool: {e}")
        return None

pool = get_db_pool()

def get_connection():
    if pool is None: return None
    try:
        return pool.get_connection()
    except:
        return None

# --- FUNCIONES DE APOYO ---
def clean(value):
    if value is None or value == "" or value == "null": return "No registra"
    return "Sí" if isinstance(value, bool) and value else ("No" if isinstance(value, bool) else str(value))

def tiene_key_valida(user_id):
    conn = get_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        query = "SELECT 1 FROM user_keys WHERE user_id = %s AND redeemed = TRUE AND expiration_date > NOW()"
        cursor.execute(query, (user_id,))
        return cursor.fetchone() is not None
    finally:
        conn.close()

# --- LÓGICA DE BÚSQUEDA ---
def buscar_cedula(cedula):
    conn = get_connection()
    if not conn: return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM ani WHERE ANINuip = %s", (cedula,))
        return cursor.fetchone()
    finally:
        conn.close()

# --- COMANDOS DEL BOT ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚔️ PABLO MENU ACTIVO ⚔️\nUsa /help para ver comandos.")

async def mostrar_datos_cedula(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not tiene_key_valida(user_id):
        await update.message.reply_text("❌ No tienes suscripción activa.")
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ Uso: /cc 123456")
        return

    cedula = context.args[0]
    datos = buscar_cedula(cedula)
    
    if datos:
        msg = f"🪪 **CC:** `{cedula}`\n👤 **Nombre:** {datos['ANINombre1']} {datos['ANIApellido1']}"
        await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ No encontrado.")

# --- AGREGAR EL RESTO DE TUS FUNCIONES (nequi, placa, etc.) AQUÍ ---
# Asegúrate de que todas las funciones mencionadas en main() estén escritas arriba.

async def registrar_usuario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Lógica para guardar usuario en la DB
    pass

# --- FUNCIÓN PRINCIPAL ---
def main():
    TOKEN = "8717607121:AAEAayJLXOEDQQYYPOEm_FrX_H28a2cNgVw"
    application = Application.builder().token(TOKEN).build()

    # Handlers (Ahora sí encontrarán las funciones definidas arriba)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cc", mostrar_datos_cedula))
    # application.add_handler(CommandHandler("nequi", comando_nequi)) # Descomenta cuando pegues la función

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, registrar_usuario))

    logger.info("Bot iniciado con éxito.")
    application.run_polling()

if __name__ == "__main__":
    main()
