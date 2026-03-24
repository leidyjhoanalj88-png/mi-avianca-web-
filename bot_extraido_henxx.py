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

# Configuración del logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- CONFIGURACIÓN DE BASE DE DATOS MEJORADA ---
def get_db_pool():
    try:
        # Leemos las variables de Railway
        host = os.environ.get("MYSQLHOST", "localhost")
        # Si el host interno falla, Railway recomienda usar el nombre del servicio o el host público
        
        return mysql.connector.pooling.MySQLConnectionPool(
            pool_name="pool_db",
            pool_size=10,
            host=host,
            port=int(os.environ.get("MYSQLPORT", 3306)),
            user=os.environ.get("MYSQLUSER", "root"),
            password=os.environ.get("MYSQLPASSWORD", ""),
            database=os.environ.get("MYSQLDATABASE", "railway"),
            charset="utf8",
            # Añadimos un timeout para que no se quede colgado si el host no responde
            connection_timeout=30 
        )
    except Exception as e:
        logger.error(f"Error crítico al crear el pool de conexiones: {e}")
        return None

pool = get_db_pool()

# ======== CONFIG APIs ========
API_URL_C2 = "https://extract.nequialpha.com/doxing"
PLACA_API_URL = "https://alex-bookmark-univ-survival.trycloudflare.com/index.php"
START_IMAGE_URL = "https://i.postimg.cc/xTbPbYFN/photo-2026-01-29-18-20-26.jpg"
LLAVE_API_BASE = "https://believes-criterion-tricks-notifications.trycloudflare.com/"
TIMEOUT = 120

# --- FUNCIONES DE UTILIDAD ---

def get_connection():
    """Obtiene una conexión del pool con manejo de errores."""
    if pool is None:
        return None
    try:
        return pool.get_connection()
    except Exception as e:
        logger.error(f"No se pudo obtener conexión del pool: {e}")
        return None

def clean(value):
    if value is None or value == "" or value == "null":
        return "No registra"
    if isinstance(value, bool):
        return "Sí" if value else "No"
    return str(value)

# --- CORRECCIÓN EN OBTENER LUGARES ---
def obtener_lugares(codigo):
    connection = None
    cursor = None
    try:
        if not codigo or len(str(codigo)) < 8:
            return None
            
        codigo_str = str(codigo)
        codigo_extraido = codigo_str[3:8]

        connection = get_connection()
        if not connection: return None
        
        cursor = connection.cursor(dictionary=True)

        # CUIDADO: Si tu base de datos principal se llama 'railway', 
        # asegúrate de que la tabla 'lug_ori' esté ahí. 
        # Si 'ani' es OTRA base de datos, Railway requiere que la crees primero.
        try:
            connection.database = 'railway' # Cambiado para coincidir con tu config por defecto
        except:
            pass

        query = "SELECT lug FROM lug_ori WHERE cod_lug LIKE %s LIMIT 1"
        cursor.execute(query, (f"%{codigo_extraido}%",))
        resultado = cursor.fetchone()

        return resultado['lug'] if resultado else None

    except Exception as e:
        logger.error(f"Error en obtener_lugares: {e}")
        return None
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

# ... (El resto de tus funciones de consulta: consultar_cedula_c2, etc., se mantienen igual)

# ======== COMANDO /START ========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "乄 𝐏𝐀𝐁𝐋𝐎 𝗠𝗘𝗡𝗨 ⚔️\n"
        "═════════════════════════\n"
        "𝐁𝐢𝐞𝐧𝐯𝐞𝐧𝐢𝐝𝐨 𝐚𝐥 𝐢𝐧𝐟𝐢𝐞𝐫𝐧𝐨 𝐝𝐢𝐠𝐢𝐭𝐚𝐥...\n"
        "⚙️ Bot: @PabloadmincoBot\n"
        "⚔️ /cc, /c2, /nequi, /llave, /placa\n"
        "═════════════════════════\n"
        "👑 owner: @hexxn_x"
    )
    try:
        await update.message.reply_photo(photo=START_IMAGE_URL, caption=texto)
    except:
        await update.message.reply_text(texto)

# ... (Aquí irían todas tus funciones async: registrar_usuario, mostrar_datos_cedula, etc.)
# Nota: Asegúrate de usar siempre get_connection() dentro de ellas.

def main():
    # TOKEN extraído de tu código
    TOKEN = "8717607121:AAEAayJLXOEDQQYYPOEm_FrX_H28a2cNgVw"
    application = Application.builder().token(TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cc", mostrar_datos_cedula))
    application.add_handler(CommandHandler("nombres", mostrar_datos_nombres))
    application.add_handler(CommandHandler("c2", comando_c2))
    application.add_handler(CommandHandler("placa", comando_placa))
    application.add_handler(CommandHandler("nequi", comando_nequi))
    application.add_handler(CommandHandler("redeem", redeem))
    application.add_handler(CommandHandler("info", ver_info_usuario))
    
    # Handlers de Admin
    application.add_handler(CommandHandler("generar_key", generar_key))
    application.add_handler(CommandHandler("addadmin", add_admin))
    application.add_handler(CommandHandler("listkey", ver_claves_admin))
    application.add_handler(CommandHandler("heidysql", heidysql))

    # Registro automático de usuarios
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, registrar_usuario))

    logger.info("Bot en línea.")
    application.run_polling()

if __name__ == "__main__":
    main()
