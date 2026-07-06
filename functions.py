import sqlite3
import random
import string
import time
from datetime import datetime
import requests
from config import *

# ==============================================
# 📡 CONFIGURACIÓN DE LOGS AUTOMÁTICOS
# ==============================================
def enviar_log(bot, mensaje, tipo="INFO"):
    try:
        emoji = "📝"
        if tipo == "ERROR": emoji = "❌"
        elif tipo == "WARNING": emoji = "⚠️"
        elif tipo == "SUCCESS": emoji = "✅"
        elif tipo == "COMMAND": emoji = "⌨️"
        elif tipo == "BUY": emoji = "🛒"
        
        texto_log = f"""
{emoji} <b>[{tipo}]</b> <b>{datetime.now().strftime('%H:%M:%S')}</b>

{mensaje}

──────────────────
"""
        bot.send_message(CHANNEL_LOGS, texto_log, parse_mode="html")
    except:
        print(f"[LOG] {mensaje}")

# ==============================================
# 🗄️ BASE DE DATOS
# ==============================================
def conectar_db():
    return sqlite3.connect('dados_bot.db')

def criar_tabelas():
    conn = conectar_db()
    c = conn.cursor()
    
    # Tabla usuarios actualizada con más campos
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios
                 (id INTEGER PRIMARY KEY, nombre TEXT, lang TEXT DEFAULT 'es', tipo TEXT DEFAULT 'user', 
                  saldo REAL DEFAULT 0, nivel TEXT DEFAULT '1', ganancias REAL DEFAULT 0,
                  baneado INTEGER DEFAULT 0, referido_por INTEGER DEFAULT 0)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS keys
                 (key TEXT PRIMARY KEY, saldo REAL DEFAULT 0, user_id INTEGER, created_by INTEGER)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS logs_sistema
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, tipo TEXT, mensaje TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS antispam
                 (user_id INTEGER PRIMARY KEY, contador INTEGER, ultimo_mensaje REAL, bloqueado_hasta REAL)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS facturas
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  user_id INTEGER, fecha TEXT, servicio TEXT, cantidad TEXT, precio REAL, link TEXT, order_id TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS participantes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, nombre TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS configuracion
                 (nombre TEXT PRIMARY KEY, valor TEXT)''')
    
    # 🆕 TABLA NUEVA: CUPONES
    c.execute('''CREATE TABLE IF NOT EXISTS cupones
                 (codigo TEXT PRIMARY KEY, descuento INTEGER, usos INTEGER, max_usos INTEGER)''')
    
    conn.commit()
    conn.close()
    enviar_log(None, "✅ Base de datos actualizada correctamente!", "SUCCESS")

# ==============================================
# 🎫 SISTEMA DE CUPONES DE DESCUENTO
# ==============================================
def crear_cupon(codigo, porcentaje, max_usos=1):
    conn = conectar_db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO cupones (codigo, descuento, usos, max_usos) VALUES (?,?,0,?)", 
                  (codigo.upper(), porcentaje, max_usos))
        conn.commit()
        conn.close()
        return True
    except:
        conn.close()
        return False

def usar_cupon(codigo):
    conn = conectar_db()
    c = conn.cursor()
    c.execute("SELECT descuento, usos, max_usos FROM cupones WHERE codigo=?", (codigo.upper(),))
    res = c.fetchone()
    
    if not res:
        return False, 0  # No existe el cupón
    
    descuento, usos, max_usos = res
    
    if usos >= max_usos and max_usos != 0:
        conn.close()
        return False, -1  # Cupón agotado
    
    # Aumentamos contador de usos
    c.execute("UPDATE cupones SET usos = usos + 1 WHERE codigo=?", (codigo.upper(),))
    conn.commit()
    conn.close()
    return True, descuento

# ==============================================
# 🎁 SISTEMA DE SORTEOS
# ==============================================
sorteo_activo = False
premio_actual = 0
tipo_premio = "Saldo"

def iniciar_sorteo(premio, tipo="Saldo"):
    global sorteo_activo, premio_actual, tipo_premio
    sorteo_activo = True
    premio_actual = premio
    tipo_premio = tipo
    limpiar_participantes()
    enviar_log(None, f"🎁 SORTEO INICIADO | Premio: ${premio}", "SUCCESS")

def finalizar_sorteo():
    global sorteo_activo, premio_actual
    sorteo_activo = False
    return elegir_ganador()

def limpiar_participantes():
    conn = conectar_db()
    c = conn.cursor()
    c.execute("DELETE FROM participantes")
    conn.commit()
    conn.close()

def agregar_participante(uid, nombre):
    conn = conectar_db()
    c = conn.cursor()
    c.execute("SELECT * FROM participantes WHERE user_id=?", (uid,))
    if not c.fetchone():
        c.execute("INSERT INTO participantes (user_id, nombre) VALUES (?,?)", (uid, nombre))
        conn.commit()
        resultado = True
        enviar_log(None, f"👤 {nombre} (<code>{uid}</code>) se unió al sorteo!", "COMMAND")
    else:
        resultado = False
    conn.close()
    return resultado

def contar_participantes():
    conn = conectar_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM participantes")
    total = c.fetchone()[0]
    conn.close()
    return total

def elegir_ganador():
    conn = conectar_db()
    c = conn.cursor()
    c.execute("SELECT user_id, nombre FROM participantes")
    participantes = c.fetchall()
    conn.close()
    if not participantes:
        return None
    return random.choice(participantes)

# ==============================================
# 🧾 SISTEMA DE FACTURAS
# ==============================================
def generar_factura(uid, servicio, cantidad, precio, link, order_id):
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = conectar_db()
    c = conn.cursor()
    c.execute('''INSERT INTO facturas 
                 (user_id, fecha, servicio, cantidad, precio, link, order_id) 
                 VALUES (?,?,?,?,?,?,?)''', 
              (uid, fecha, servicio, cantidad, precio, link, order_id))
    conn.commit()
    conn.close()
    
    log_compra = f"""
🛒 <b>¡NUEVA COMPRA REALIZADA!</b>

👤 <b>USUARIO:</b> <code>{uid}</code>
📦 <b>PRODUCTO:</b> {servicio}
🔢 <b>CANTIDAD:</b> {cantidad}
💳 <b>PRECIO:</b> ${precio}
🔗 <b>LINK:</b> <code>{link}</code>
🆔 <b>ORDER ID:</b> <code>{order_id}</code>
📅 <b>FECHA:</b> {fecha}
"""
    enviar_log(None, log_compra, "BUY")
    
    factura_texto = f"""
╔═══════════════════════════════╗
║ 🧾 𝐅𝐀𝐂𝐓𝐔𝐑𝐀 𝐃𝐄 𝐂𝐎𝐌𝐏𝐑𝐀 🧾 ║
╚═══════════════════════════════╝

🆔 <b>𝐅𝐀𝐂𝐓𝐔𝐑𝐀 𝐍°:</b> <code>#{random.randint(10000, 99999)}</code>
📅 <b>𝐅𝐄𝐂𝐇𝐀:</b> {fecha}
👤 <b>𝐂𝐋𝐈𝐄𝐍𝐓𝐄 𝐈𝐃:</b> <code>{uid}</code>

┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈
📦 <b>𝐃𝐄𝐓𝐀𝐋𝐋𝐄 𝐃𝐄𝐋 𝐏𝐄𝐃𝐈𝐃𝐎</b>
┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈

🔹 <b>𝐏𝐑𝐎𝐃𝐔𝐂𝐓𝐎:</b> {servicio}
🔹 <b>CANTIDAD:</b> {cantidad}
🔹 <b>LINK:</b> <code>{link}</code>

💳 <b>𝐃𝐀𝐓𝐎𝐒 𝐃𝐄 𝐏𝐀𝐆𝐎</b>
🔹 <b>MONTO:</b> <b>${precio} USD</b>
🔹 <b>ESTADO:</b> ✅ 𝐏𝐀𝐆𝐀𝐃𝐎
🔹 <b>ORDEN ID:</b> <code>{order_id}</code>

╔═══════════════════════════════╗
║ ✅ 𝐏𝐄𝐃𝐈𝐃𝐎 𝐏𝐑𝐎𝐂𝐄𝐒𝐀𝐃𝐎 ║
╚═══════════════════════════════╝
"""
    return factura_texto

def obtener_historial_compras(uid):
    conn = conectar_db()
    c = conn.cursor()
    c.execute("SELECT fecha, servicio, cantidad, precio, order_id FROM facturas WHERE user_id=? ORDER BY id DESC LIMIT 10", (uid,))
    compras = c.fetchall()
    conn.close()
    return compras

# ==============================================
# 🛡️ SISTEMA ANTISPAM
# ==============================================
antispam_cache = {}

def verificar_spam(uid):
    if not ANTISPAM_ACTIVO or uid in ADMINS:
        return False
    ahora = time.time()
    if uid not in antispam_cache:
        antispam_cache[uid] = {'contador': 0, 'ultimo': ahora, 'bloqueado_hasta': 0}
    usuario = antispam_cache[uid]
    
    if usuario['bloqueado_hasta'] > ahora:
        return True
    if ahora - usuario['ultimo'] < 1:
        usuario['contador'] += 1
    else:
        usuario['contador'] = 0
        
    usuario['ultimo'] = ahora
    
    if usuario['contador'] > LIMITE_MENSAJES:
        usuario['bloqueado_hasta'] = ahora + TIEMPO_BLOQUEO
        enviar_log(None, f"🚫 Usuario <code>{uid}</code> bloqueado por spam!", "WARNING")
        return True
    return False

def obtener_tiempo_restante(uid):
    if uid in antispam_cache:
        ahora = time.time()
        if antispam_cache[uid]['bloqueado_hasta'] > ahora:
            return int(antispam_cache[uid]['bloqueado_hasta'] - ahora)
    return 0

# ==============================================
# 📝 SISTEMA DE LOGS
# ==============================================
def add_log(bot, tipo, uid, mensaje):
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = conectar_db()
    c = conn.cursor()
    c.execute("INSERT INTO logs_sistema (fecha, tipo, mensaje) VALUES (?,?,?)", (fecha, tipo, mensaje))
    conn.commit()
    conn.close()
    
    emojis = {
        "JOIN": "🆕", "PURCHASE": "🛒", "DEPOSIT": "💳",
        "CREATE_KEY": "🔑", "COMMISSION": "💸", "RESTART": "🔄",
        "SUPPORT": "💬", "ANTISPAM": "🛡️", "DOLA": "🤖",
        "INVOICE": "🧾", "GIFT": "🎁", "BAN": "🔨", "UNBAN": "✅",
        "ADMIN": "⚙️", "COMMAND": "⌨️"
    }
    emoji = emojis.get(tipo, "📝")
    
    log_texto = f"""
{emoji} <b>[{tipo}]</b> <code>{uid}</code>

{mensaje}
"""
    enviar_log(bot, log_texto, tipo)

# ==============================================
# 🛡️ FUNCIONES BÁSICAS
# ==============================================
def es_admin(uid): return uid in ADMINS

# 🆕 FUNCIÓN NUEVA: VERIFICAR SI ES REVENDEDOR
def es_revendedor(uid):
    if esta_baneado(uid): return False
    c = conectar_db().cursor()
    c.execute("SELECT tipo FROM usuarios WHERE id=?", (uid,))
    res = c.fetchone()
    return res and res[0] in ['reseller', 'reseller_vip']

def esta_baneado(uid):
    try:
        c = conectar_db().cursor()
        c.execute("SELECT baneado FROM usuarios WHERE id=?", (uid,))
        res = c.fetchone()
        return res and res[0] == 1
    except:
        return False

def get_saldo(uid):
    try:
        c = conectar_db().cursor()
        c.execute("SELECT saldo FROM usuarios WHERE id=?", (uid,))
        return float(c.fetchone()[0])
    except:
        return 0.0

def add_saldo(uid, valor):
    c = conectar_db()
    c.cursor().execute("UPDATE usuarios SET saldo = saldo + ? WHERE id=?", (float(valor), uid))
    c.commit()
    c.close()
    add_log(None, "DEPOSIT", uid, f"Saldo añadido: +${valor}")

def descontar_saldo(uid, valor):
    c = conectar_db()
    c.cursor().execute("UPDATE usuarios SET saldo = saldo - ? WHERE id=?", (float(valor), uid))
    c.commit()
    c.close()

def get_lang(uid):
    try:
        c = conectar_db().cursor()
        c.execute("SELECT lang FROM usuarios WHERE id=?", (uid,))
        res = c.fetchone()
        return res[0] if res else 'es'
    except:
        return 'es'

def cambiar_nivel(uid, nivel):
    c = conectar_db()
    c.cursor().execute("UPDATE usuarios SET nivel = ? WHERE id=?", (nivel, uid))
    c.commit()
    c.close()
    enviar_log(None, f"💎 Usuario <code>{uid}</code> ahora es nivel {nivel}", "SUCCESS")

# 🆕 FUNCIÓN NUEVA: HACER REVENDEDOR
def hacer_revendedor(uid, nombre):
    c = conectar_db()
    c.cursor().execute("UPDATE usuarios SET tipo = 'reseller' WHERE id=?", (uid,))
    c.commit()
    c.close()
    enviar_log(None, f"🤝 {nombre} (<code>{uid}</code>) ahora es REVENDEDOR!", "SUCCESS")

# ==============================================
# 💸 SISTEMA DE COMISIONES
# ==============================================
def calcular_comision(uid_creador, monto_key):
    c = conectar_db()
    cursor = c.cursor()
    cursor.execute("SELECT nivel, ganancias FROM usuarios WHERE id=?", (uid_creador,))
    res = cursor.fetchone()
    if not res:
        return 0, "📱"
        
    nivel = res[0]
    ganancias_anteriores = res[1]
    
    if nivel == '1': 
        porcentaje, emoji = 0.15, "🥉"
    elif nivel == '2': 
        porcentaje, emoji = 0.20, "🥈"
    elif nivel == '3': 
        porcentaje, emoji = 0.25, "🥇"
    elif nivel == '4': 
        porcentaje, emoji = 0.30, "💎"
    else:
        porcentaje, emoji = 0.10, "📱"
        
    comision = monto_key * porcentaje
    nuevas_ganancias = ganancias_anteriores + comision
    
    cursor.execute("UPDATE usuarios SET ganancias = ? WHERE id=?", (nuevas_ganancias, uid_creador))
    c.commit()
    c.close()
    
    enviar_log(None, f"💸 Comisión generada: ${comision} ({porcentaje*100}%)", "COMMISSION")
    return comision, emoji

# ==============================================
# 🔑 SISTEMA DE KEYS
# ==============================================
def gerar_chave(): return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(16))

def crear_key_reseller(uid_creador, saldo):
    key = gerar_chave()
    c = conectar_db()
    c.cursor().execute("INSERT INTO keys (key, saldo, user_id, created_by) VALUES (?,?,NULL,?)", (key, saldo, uid_creador))
    c.commit()
    c.close()
    
    comision, emoji = calcular_comision(uid_creador, saldo)
    add_log(None, "CREATE_KEY", uid_creador, f"Creada key: {key} | Valor: ${saldo}")
    return key, comision, emoji

def verificar_key(key):
    c = conectar_db().cursor()
    c.execute("SELECT saldo, user_id FROM keys WHERE key=?", (key,))
    res = c.fetchone()
    if not res:
        return False, 0
    if res[1] is not None:
        return False, 0
    return True, res[0]

def activar_key(uid, key):
    valido, saldo = verificar_key(key)
    if not valido:
        return False, 0
    add_saldo(uid, saldo)
    c = conectar_db()
    c.cursor().execute("UPDATE keys SET user_id = ? WHERE key = ?", (uid, key))
    c.commit()
    c.close()
    add_log(None, "DEPOSIT", uid, f"Key activada: {key} | Valor: ${saldo}")
    return True, saldo

# ==============================================
# 🔌 CONEXIÓN API (CON TIMEOUT)
# ==============================================
def enviar_orden_api(service_id, link, cantidad):
    try:
        datos = {
            'key': API_KEY,
            'action': 'add',
            'service': service_id,
            'link': link,
            'quantity': cantidad
        }
        respuesta = requests.post(API_URL, data=datos, timeout=15)
        resultado = respuesta.json()
        
        if resultado.get('error'):
            enviar_log(None, f"❌ ERROR API: {resultado.get('error')}", "ERROR")
            return False, resultado.get('error')
        else:
            enviar_log(None, f"✅ Orden enviada a API | Service: {service_id}", "SUCCESS")
            return True, resultado.get('order', 'OK')
    except requests.exceptions.Timeout:
        error_msg = "⏱️ ERROR: Tiempo de espera agotado (Timeout)"
        enviar_log(None, error_msg, "ERROR")
        return False, "Tiempo de espera agotado"
    except Exception as e:
        error_msg = f"🔥 ERROR CRÍTICO API: {str(e)}"
        enviar_log(None, error_msg, "ERROR")
        return False, str(e)

# ==============================================
# 🌍 TEXTOS
# ==============================================
textos = {
    'en': {
        'welcome': "🎉 𝐖𝐄𝐋𝐂𝐎𝐌𝐄!", 'menu': "🔻 𝐂𝐇𝐎𝐎𝐒𝐄 𝐀𝐍 𝐎𝐏𝐓𝐈𝐎𝐍 🔻", 'enter_key': "🔑 𝐄𝐍𝐓𝐄𝐑 𝐘𝐎𝐔𝐑 𝐊𝐄𝐘:",
        'activated': "✅ 𝐀𝐂𝐓𝐈𝐕𝐀𝐓𝐄𝐃!\n💲 +", 'balance': "💰 𝐁𝐀𝐋𝐀𝐍𝐂𝐄 ($): ", 'services': "📦 𝐒𝐄𝐑𝐕𝐈𝐂𝐄𝐒",
        'buy_ok': "✅ 𝐏𝐔𝐑𝐂𝐇𝐀𝐒𝐄 𝐒𝐔𝐂𝐂𝐄𝐒𝐒!", 'no_funds': "❌ 𝐈𝐍𝐒𝐔𝐅𝐅𝐈𝐂𝐈𝐄𝐍𝐓 𝐅𝐔𝐍𝐃𝐒!",
        'banned': "🚫 𝐘𝐎𝐔 𝐀𝐑𝐄 𝐁𝐀𝐍𝐍𝐄𝐃", 'enter_link': "🔗 𝐄𝐍𝐓𝐄𝐑 𝐓𝐇𝐄 𝐋𝐈𝐍𝐊:",
        'order_sent': "✅ 𝐎𝐑𝐃𝐄𝐑 𝐒𝐄𝐍𝐓! 𝐈𝐃: ", 'order_error': "❌ 𝐄𝐑𝐑𝐎𝐑: ",
        'spam_blocked': "⏳ 𝐖𝐀𝐈𝐓! 𝐘𝐎𝐔 𝐀𝐑𝐄 𝐁𝐋𝐎𝐂𝐊𝐄𝐃 𝐅𝐎𝐑 𝐒𝐏𝐀𝐌\n𝐓𝐈𝐌𝐄: {seg}s",
        'my_orders': "📜 𝐌𝐘 𝐎𝐑𝐃𝐄𝐑𝐒", 'giveaway': "🎁 𝐉𝐎𝐈𝐍 𝐆𝐈𝐕𝐄𝐀𝐖𝐀𝐘",
        'coupon': "🎫 𝐔𝐒𝐄 𝐂𝐎𝐔𝐏𝐎𝐍", 'reseller': "🤝 𝐑𝐄𝐒𝐄𝐋𝐋𝐄𝐑 𝐏𝐀𝐍𝐄𝐋"
    },
    'es': {
        'welcome': "🎉 ¡𝐁𝐈𝐄𝐍𝐕𝐄𝐍𝐈𝐃𝐎!", 'menu': "🔻 𝐒𝐄𝐋𝐄𝐂𝐂𝐈𝐎𝐍𝐀 𝐔𝐍𝐀 𝐎𝐏𝐂𝐈Ó𝐍 🔻", 'enter_key': "🔑 𝐈𝐍𝐆𝐑𝐄𝐒𝐀 𝐓𝐔 𝐊𝐄𝐘:",
        'activated': "✅ ¡𝐀𝐂𝐓𝐈𝐕𝐀𝐃𝐎!\n💲 +", 'balance': "💰 𝐒𝐀𝐋𝐃𝐎 ($): ", 'services': "📦 𝐒𝐄𝐑𝐕𝐈𝐂𝐈𝐎𝐒",
        'buy_ok': "✅ ¡𝐂𝐎𝐌𝐏𝐑𝐀 𝐑𝐄𝐀𝐋𝐈??𝐀𝐃𝐀!", 'no_funds': "❌ 𝐒𝐀𝐋𝐃𝐎 𝐈𝐍𝐒𝐔𝐅𝐈𝐂𝐈𝐄𝐍𝐓𝐄!",
        'banned': "🚫 𝐄𝐒𝐓Á𝐒 𝐁𝐀𝐍𝐄𝐀𝐃𝐎", 'enter_link': "🔗 𝐈𝐍𝐆𝐑𝐄𝐒𝐀 𝐄𝐋 𝐋𝐈𝐍𝐊:",
        'order_sent': "✅ 𝐏𝐄𝐃𝐈𝐃𝐎 𝐄𝐍𝐕𝐈𝐀𝐃𝐎! 𝐈𝐃: ", 'order_error': "❌ 𝐄𝐑𝐑𝐎𝐑: ",
        'spam_blocked': "⏳ 𝐄𝐒𝐏𝐄𝐑𝐀! 𝐄𝐒𝐓Á𝐒 𝐁𝐋𝐎𝐐𝐔𝐄𝐀𝐃𝐎 𝐏𝐎𝐑 𝐒𝐏𝐀𝐌\n𝐓𝐈𝐄𝐌𝐏𝐎: {seg}s",
        'my_orders': "📜 𝐌𝐈𝐒 𝐂𝐎𝐌𝐏𝐑𝐀𝐒", 'giveaway': "🎁 𝐏𝐀𝐑𝐓𝐈𝐂𝐈𝐏𝐀𝐑 𝐒𝐎𝐑𝐓𝐄𝐎",
        'coupon': "🎫 𝐔𝐒𝐀𝐑 𝐂𝐔𝐏𝐎𝐍", 'reseller': "🤝 𝐏𝐀𝐍𝐄𝐋 𝐑𝐄𝐕𝐄𝐍𝐃𝐄𝐃𝐎𝐑"
    },
    'pt': {
        'welcome': "🎉 𝐁𝐄𝐌-𝐕𝐈𝐍𝐃𝐎!", 'menu': "🔻 𝐄𝐒𝐂𝐎𝐋𝐇𝐀 𝐔𝐌𝐀 𝐎𝐏ÇÃ𝐎 🔻", 'enter_key': "🔑 𝐃𝐈𝐆𝐈𝐓𝐄 𝐒𝐔𝐀 𝐂𝐇𝐀𝐕𝐄:",
        'activated': "✅ 𝐀𝐓𝐈𝐕𝐀𝐃𝐎!\n💲 +", 'balance': "💰 𝐒𝐀𝐋𝐃𝐎 ($): ", 'services': "📦 𝐒𝐄𝐑𝐕𝐈Ç𝐎𝐒",
        'buy_ok': "✅ 𝐂𝐎𝐌𝐏𝐑𝐀 𝐑𝐄𝐀𝐋𝐈𝐙𝐀𝐃𝐀!", 'no_funds': "❌ 𝐒𝐀𝐋𝐃𝐎 𝐈𝐍𝐒𝐔𝐅𝐈𝐂𝐈𝐄𝐍𝐓𝐄",
        'banned': "🚫 𝐕𝐎𝐂Ê 𝐄𝐒𝐓Á 𝐁𝐀𝐍𝐈𝐃𝐎", 'enter_link': "🔗 𝐃𝐈𝐆𝐈𝐓𝐄 𝐎 𝐋𝐈𝐍𝐊:",
        'order_sent': "✅ 𝐏𝐄𝐃𝐈𝐃𝐎 𝐄𝐍𝐕𝐈𝐀𝐃𝐎! 𝐈𝐃: ", 'order_error': "❌ 𝐄𝐑𝐑𝐎: ",
        'spam_blocked': "⏳ 𝐀𝐆𝐔𝐀𝐑𝐃𝐄! 𝐕𝐎𝐂Ê 𝐄𝐒𝐓Á 𝐁𝐋𝐎𝐐𝐔𝐄𝐀𝐃𝐎 𝐏𝐎𝐑 𝐒𝐏𝐀𝐌\n𝐓𝐄𝐌𝐏𝐎: {seg}s",
        'my_orders': "📜 𝐌𝐄𝐔𝐒 𝐏𝐄𝐃𝐈𝐃𝐎𝐒", 'giveaway': "🎁 𝐏𝐀𝐑𝐓𝐈𝐂𝐈𝐏𝐀𝐑 𝐒𝐎𝐑𝐓𝐄𝐈𝐎",
        'coupon': "🎫 𝐔𝐒𝐀𝐑 𝐂𝐔𝐏𝐎𝐌", 'reseller': "🤝 𝐏𝐀𝐈𝐍𝐄𝐋 𝐑𝐄𝐕𝐄𝐍𝐃𝐄𝐃𝐎𝐑"
    }
}

# ==============================================
# 🛒 LISTA DE PRODUCTOS AMPLIADA
# ==============================================
productos = {
    # 📱 TELEGRAM
    "1": ["👥 𝐌𝐈𝐄𝐌𝐁𝐑𝐎𝐒 𝐁Á𝐒𝐈𝐂𝐎𝐒", "𝟏.𝟎𝟎𝟎", 3.99, "miembros", 10136],
    "2": ["👥 𝐌𝐈𝐄𝐌𝐁𝐑𝐎𝐒 𝐁Á𝐒𝐈𝐂𝐎𝐒", "𝟑.𝟎𝟎𝟎", 9.99, "miembros", 10137],
    "3": ["👥 𝐌𝐈𝐄𝐌𝐁𝐑𝐎𝐒 𝐁Á𝐒𝐈𝐂𝐎𝐒", "𝟓.𝟎𝟎𝟎", 14.99, "miembros", 10138],
    "4": ["👥 𝐌𝐈𝐄𝐌𝐁𝐑𝐎𝐒 𝐁Á𝐒𝐈𝐂𝐎𝐒", "𝟏𝟎.𝟎𝟎𝟎", 24.99, "miembros", 10139],
    "5": ["💎 𝐌𝐈𝐄𝐌𝐁𝐑𝐎𝐒 𝐏𝐑𝐄𝐌𝐈𝐔𝐌", "𝟏.𝟎𝟎𝟎", 8.99, "calidad", 10141],
    "6": ["💎 𝐌𝐈𝐄𝐌𝐁𝐑𝐎𝐒 𝐏𝐑𝐄𝐌𝐈𝐔𝐌", "𝟑.𝟎𝟎𝟎", 22.99, "calidad", 10142],
    "7": ["🌎 𝐌𝐈𝐄𝐌𝐁𝐑𝐎𝐒 𝐎𝐍𝐋𝐈𝐍𝐄", "𝟏.𝟎𝟎𝟎", 12.99, "online", 10145],
    "8": ["🌎 𝐌𝐈𝐄𝐌𝐁𝐑𝐎𝐒 𝐎𝐍𝐋𝐈𝐍𝐄", "𝟓.𝟎𝟎𝟎", 49.99, "online", 10146],
    "9": ["❤️ 𝐑𝐄𝐀𝐂𝐂𝐈𝐎𝐍𝐄𝐒", "𝟏𝟎𝟎", 1.99, "reacciones", 10150],
    "10": ["💬 𝐂𝐎𝐌𝐄𝐍𝐓𝐀𝐑𝐈𝐎𝐒", "𝟓𝟎", 4.99, "comentarios", 10155],
    
    # 📺 YOUTUBE
    "11": ["👁️ 𝐕𝐈𝐒𝐓𝐀𝐒 𝐘𝐓", "𝟏.𝟎𝟎𝟎", 2.99, "yt_views", 10201],
    "12": ["👍 𝐋𝐈𝐊𝐄𝐒 𝐘𝐓", "𝟓𝟎𝟎", 1.99, "yt_likes", 10202],
    "13": ["🔔 𝐒𝐔𝐁𝐒𝐂𝐑𝐈𝐁𝐓𝐎𝐑𝐄𝐒", "𝟏𝟎𝟎", 5.99, "yt_subs", 10203],
    
    # 🎵 TIKTOK
    "14": ["👁️ 𝐕𝐈𝐒𝐓𝐀𝐒 𝐓𝐓𝐊", "𝟏.𝟎𝟎𝟎", 1.99, "ttk_views", 10301],
    "15": ["❤️ 𝐋𝐈𝐊𝐄𝐒 𝐓𝐓𝐊", "𝟓𝟎𝟎", 1.49, "ttk_likes", 10302],
    "16": ["👥 𝐒𝐄𝐆𝐔𝐈𝐃𝐎𝐑𝐄𝐒 𝐓𝐓𝐊", "𝟏𝟎𝟎", 3.99, "ttk_follow", 10303],
    
    # 📸 INSTAGRAM
    "17": ["👥 𝐒𝐄𝐆𝐔𝐈𝐃𝐎𝐑𝐄𝐒 𝐈𝐆", "𝟏𝟎𝟎", 4.99, "ig_follow", 10401],
    "18": ["❤️ 𝐋𝐈𝐊𝐄𝐒 𝐈𝐆", "𝟓𝟎𝟎", 1.99, "ig_likes", 10402],
    "19": ["👁️ 𝐕𝐈𝐒𝐓𝐀𝐒 𝐇𝐈𝐒𝐓𝐎𝐑𝐈𝐀", "𝟓𝟎𝟎", 0.99, "ig_stories", 10405],
    
    # 🤖 IA
    "20": ["🤖 𝐌𝐈𝐄𝐌𝐁𝐑𝐎𝐒 𝐀𝐈", "𝟏.𝟎𝟎𝟎", 19.99, "ia", 9843],
    "21": ["🤖 𝐌𝐈𝐄𝐌𝐁𝐑𝐎𝐒 𝐀𝐈", "𝟓.𝟎𝟎𝟎", 79.99, "ia", 9842]
}
