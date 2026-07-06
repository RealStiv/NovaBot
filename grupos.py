# ==============================================
# 🛡️ SISTEMA DE SEGURIDAD Y PANEL DE ADMIN
# ==============================================
import time
from config import *
from functions import *

# ==============================================
# ⚙️ CONFIGURACIÓN
# ==============================================

GRUPOS_AUTORIZADOS = []

# ==============================================
# 🛡️ FUNCIONES DE SEGURIDAD
# ==============================================

def verificar_acceso(chat_id, user_id):
    if user_id in ADMINS:
        return True
    if chat_id > 0:
        return True
    if chat_id in GRUPOS_AUTORIZADOS:
        return True
    return False

def bloquear_spam(message, bot):
    try:
        bot.delete_message(message.chat.id, message.message_id)
        aviso = bot.send_message(
            message.chat.id, 
            "❌ <b>PROHIBIDO</b>\nEste bot solo funciona en privado.\nUso en grupos no autorizado.",
            parse_mode="html"
        )
        time.sleep(3)
        bot.delete_message(message.chat.id, aviso.message_id)
        print(f"🚫 Bloqueado en grupo: {message.chat.title}")
        return True
    except:
        return False

# ==============================================
# 🎛️ PANEL PRINCIPAL
# ==============================================

def panel_admin_grupos():
    return """
⚙️ <b>𝐏𝐀𝐍𝐄𝐋 𝐃𝐄 𝐀𝐃𝐌𝐈𝐍𝐈𝐒𝐓𝐑𝐀𝐂𝐈Ó𝐍</b> ⚙️

👥 <b>𝐆𝐄𝐒𝐓𝐈Ó𝐍 𝐃𝐄 𝐆𝐑𝐔𝐏𝐎𝐒</b>
🔹 /addgrupo [ID] - Autorizar grupo
🔹 /delgrupo [ID] - Quitar autorización
🔹 /listagrupos - Ver grupos autorizados
🔹 /infogrupo - Info del grupo actual

👤 <b>𝐆𝐄𝐒𝐓𝐈Ó𝐍 𝐃𝐄 𝐔𝐒𝐔𝐀𝐑𝐈𝐎𝐒</b>
🔹 /userinfo [ID] - Ver datos del usuario
🔹 /saldo [ID] - Ver saldo del usuario
🔹 /ban [ID] - Banear usuario
🔹 /unban [ID] - Desbanear usuario

🛡️ <b>𝐒𝐄𝐆𝐔𝐑𝐈𝐃𝐀𝐃</b>
✅ Anti-spam activado
✅ Bloqueo automático en grupos no autorizado
"""

# ==============================================
# 👥 FUNCIONES DE GRUPOS
# ==============================================

def agregar_grupo_autorizado(chat_id):
    if chat_id not in GRUPOS_AUTORIZADOS:
        GRUPOS_AUTORIZADOS.append(chat_id)
        return True, f"✅ <b>GRUPO AUTORIZADO</b>\nID: <code>{chat_id}</code>"
    return False, "⚠️ Este grupo ya está autorizado."

def eliminar_grupo_autorizado(chat_id):
    if chat_id in GRUPOS_AUTORIZADOS:
        GRUPOS_AUTORIZADOS.remove(chat_id)
        return True, f"❌ <b>GRUPO RETIRADO</b>\nID: <code>{chat_id}</code>"
    return False, "⚠️ Este grupo no está en la lista."

def listar_grupos_autorizados():
    if not GRUPOS_AUTORIZADOS:
        return "📝 <b>LISTA VACÍA</b>\nNo tienes grupos autorizados."
    texto = "📋 <b>GRUPOS AUTORIZADOS:</b>\n\n"
    for id_grupo in GRUPOS_AUTORIZADOS:
        texto += f"🔹 <code>{id_grupo}</code>\n"
    return texto

def info_grupo_actual(message):
    chat = message.chat
    return f"""
ℹ️ <b>INFORMACIÓN DEL GRUPO</b>

🏷️ <b>Nombre:</b> {chat.title}
🆔 <b>ID:</b> <code>{chat.id}</code>
👥 <b>Tipo:</b> {chat.type}
🔐 <b>Estado:</b> {"✅ AUTORIZADO" if chat.id in GRUPOS_AUTORIZADOS else "❌ NO AUTORIZADO"}
"""

# ==============================================
# 👤 FUNCIONES DE USUARIOS
# ==============================================

def info_usuario_completo(user_id, bot):
    try:
        conn = conectar_db()
        c = conn.cursor()
        c.execute("SELECT nombre, saldo, nivel, baneado FROM usuarios WHERE id=?", (user_id,))
        usuario = c.fetchone()
        conn.close()

        if usuario:
            nombre, saldo, nivel, baneado = usuario
            estado = "🔴 BANEADO" if baneado == 1 else "🟢 ACTIVO"
        else:
            nombre = "Desconocido"
            saldo = 0
            nivel = "1"
            estado = "⚫ SIN REGISTRO"

        try:
            user_chat = bot.get_chat(user_id)
            nombre_real = user_chat.first_name
            username = f"@{user_chat.username}" if user_chat.username else "Sin usuario"
        except:
            nombre_real = nombre
            username = "No disponible"

        return f"""
👤 <b>𝐃𝐀𝐓𝐎𝐒 𝐃𝐄𝐋 𝐔𝐒𝐔𝐀𝐑𝐈𝐎</b>

🆔 <b>ID:</b> <code>{user_id}</code>
📛 <b>Nombre:</b> {nombre_real}
🔖 <b>Usuario:</b> {username}
💰 <b>Saldo:</b> <b>${saldo}</b>
💎 <b>Nivel:</b> {nivel}
🛡️ <b>Estado:</b> {estado}
"""
    except Exception as e:
        return f"❌ Error al obtener datos: {e}"

def ver_saldo_usuario(user_id):
    saldo = get_saldo(user_id)
    return f"💰 <b>𝐒𝐀𝐋𝐃𝐎 𝐃𝐄𝐋 𝐔𝐒𝐔𝐀𝐑𝐈𝐎</b>\n\n🆔 ID: <code>{user_id}</code>\n💲 Saldo: <b>${saldo}</b>"

def banear_usuario_db(user_id):
    try:
        conn = conectar_db()
        c = conn.cursor()
        c.execute("UPDATE usuarios SET baneado = 1 WHERE id=?", (user_id,))
        conn.commit()
        conn.close()
        return True, f"🔨 <b>USUARIO BANEADO</b>\nID: <code>{user_id}</code>"
    except:
        return False, "❌ Error al banear"

def desbanear_usuario_db(user_id):
    try:
        conn = conectar_db()
        c = conn.cursor()
        c.execute("UPDATE usuarios SET baneado = 0 WHERE id=?", (user_id,))
        conn.commit()
        conn.close()
        return True, f"✅ <b>USUARIO DESBANEADO</b>\nID: <code>{user_id}</code>"
    except:
        return False, "❌ Error al desbanear"

# ==============================================
# 🔘 MANEJADOR DE BOTONES INLINE
# ==============================================

def manejar_callback(call, bot):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    data = call.data

    if user_id not in ADMINS:
        bot.answer_callback_query(call.id, text="❌ No permitido", show_alert=True)
        return

    if data == "panel_grupos":
        bot.send_message(chat_id, panel_admin_grupos(), parse_mode="html")
        
    elif data == "lista_grupos":
        bot.send_message(chat_id, listar_grupos_autorizados(), parse_mode="html")
        
    elif data == "info_grupo":
        bot.send_message(chat_id, info_grupo_actual(call.message), parse_mode="html")
        
    elif data == "ver_usuario":
        bot.send_message(chat_id, "⚠️ <b>Uso:</b>\nEscribe: /userinfo [ID]", parse_mode="html")
        
    elif data == "ver_saldo":
        bot.send_message(chat_id, "⚠️ <b>Uso:</b>\nEscribe: /saldo [ID]", parse_mode="html")
        
    elif data == "banear_usuario":
        bot.send_message(chat_id, "⚠️ <b>Uso:</b>\nEscribe: /ban [ID]", parse_mode="html")
        
    elif data == "desbanear_usuario":
        bot.send_message(chat_id, "⚠️ <b>Uso:</b>\nEscribe: /unban [ID]", parse_mode="html")

    bot.answer_callback_query(call.id)
