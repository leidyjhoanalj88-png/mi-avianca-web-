import telebot
import random
import string
import time
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# ================= CONFIG =================
TOKEN = "TU_TOKEN_AQUI"
ADMIN_ID = 3754592387

bot = telebot.TeleBot(TOKEN)

# ================= BASE =================
keys_activas = {}
usuarios_vip = {}

# ================= KEYS =================
def generar_key(dias=30):
    key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    exp = datetime.now() + timedelta(days=dias)
    keys_activas[key] = exp
    return key, exp

def es_vip(user_id):
    if user_id not in usuarios_vip:
        return False
    
    if datetime.now() > usuarios_vip[user_id]:
        del usuarios_vip[user_id]
        return False
    
    return True

# ================= SISBEN =================
def consultar_sisben(tipo_doc, numero):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)

    try:
        driver.get("https://www.sisben.gov.co/Paginas/consulta-tu-grupo.html")
        time.sleep(6)

        wait = WebDriverWait(driver, 15)

        select_elem = wait.until(EC.presence_of_element_located((By.ID, "TipoID")))
        Select(select_elem).select_by_value(tipo_doc)

        input_doc = driver.find_element(By.ID, "documento")
        input_doc.send_keys(numero)

        boton = driver.find_element(By.ID, "botonenvio")
        driver.execute_script("arguments[0].click();", boton)

        time.sleep(6)

        html = driver.page_source.lower()

        if "no se encontr" in html:
            return "❌ No encontrado en SISBÉN"

        resultado = "📊 *SISBÉN RESULTADO*\n\n"

        try:
            grupo = driver.find_element(By.XPATH, "//p[contains(@class,'text-uppercase')]").text
            resultado += f"🏷 Grupo: {grupo}\n"
        except:
            pass

        campos = ["Nombres", "Apellidos", "Municipio", "Departamento"]

        for campo in campos:
            try:
                val = driver.find_element(By.XPATH, f"//p[contains(text(), '{campo}')]/following-sibling::p").text
                resultado += f"{campo}: {val}\n"
            except:
                pass

        return resultado

    except Exception as e:
        return f"⚠️ Error: {str(e)}"

    finally:
        driver.quit()

# ================= COMANDOS =================

@bot.message_handler(commands=['start'])
def start(msg):
    bot.send_message(msg.chat.id, f"""
乄 DOXEO_CONSULTAS ⚔️
══════════════════════

🤖 Bienvenido {msg.from_user.first_name}

⚔️ /activar ➛ Activar acceso
⚔️ /consultar ➛ SISBÉN IV
⚔️ /miacceso ➛ Ver acceso

👑 Owner: @Broquicalifa
""")

# ================= KEY ADMIN =================
@bot.message_handler(commands=['key'])
def crear_key_cmd(msg):
    if msg.from_user.id != ADMIN_ID:
        return bot.reply_to(msg, "❌ No autorizado")

    args = msg.text.split()
    dias = int(args[1]) if len(args) > 1 else 30

    key, exp = generar_key(dias)

    bot.reply_to(msg, f"""
🔑 NUEVA KEY

Key: `{key}`
Días: {dias}
Expira: {exp.strftime('%Y-%m-%d')}

Usar:
/activar {key}
""", parse_mode="Markdown")

# ================= ACTIVAR =================
@bot.message_handler(commands=['activar'])
def activar(msg):
    args = msg.text.split()

    if len(args) < 2:
        return bot.reply_to(msg, "Uso: /activar CLAVE")

    key = args[1]

    if key not in keys_activas:
        return bot.reply_to(msg, "❌ Key inválida")

    exp = keys_activas[key]

    if datetime.now() > exp:
        return bot.reply_to(msg, "⚠️ Key expirada")

    usuarios_vip[msg.from_user.id] = exp
    del keys_activas[key]

    bot.reply_to(msg, f"✅ Acceso activo hasta {exp.strftime('%Y-%m-%d')}")

# ================= MI ACCESO =================
@bot.message_handler(commands=['miacceso'])
def miacceso(msg):
    if msg.from_user.id not in usuarios_vip:
        return bot.reply_to(msg, "❌ No tienes acceso")

    exp = usuarios_vip[msg.from_user.id]
    bot.reply_to(msg, f"🔐 Activo hasta {exp.strftime('%Y-%m-%d')}")

# ================= CONSULTAR =================
@bot.message_handler(commands=['consultar'])
def consultar(msg):
    if not es_vip(msg.from_user.id):
        return bot.reply_to(msg, "🔒 Solo VIP")

    args = msg.text.split()

    if len(args) < 3:
        return bot.reply_to(msg, "Uso: /consultar tipo_doc numero")

    tipo = args[1]
    numero = args[2]

    bot.reply_to(msg, "🔍 Consultando...")

    resultado = consultar_sisben(tipo, numero)

    bot.send_message(msg.chat.id, resultado, parse_mode="Markdown")

# ================= RUN =================
print("🔥 BOT ACTIVO...")
bot.infinity_polling()