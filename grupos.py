# ==============================================
# 🛡️ SISTEMA DE ADMINISTRACIÓN NOVA BOT
# ==============================================
import time
from config import *
from functions import *
from telebot import types

# ⚙️ CONFIGURACIÓN
GRUPOS_AUTORIZADOS = []

# ==============================================
# 🛡️ SEGURIDAD
# ==============================================
def verificar_acceso(chat_id, user_id):
    return user_id in ADMINS or chat_id > 0 or chat_id in GRUPOS_AUTORIZADOS

def bloquear_spam(message, bot):
    try:
        bot.delete_message(message.chat.id, message.message_id)
        aviso = bot.send_message(message.chat.id, "❌ <b>PROHIBIDO</b>\nSolo funciona en privado.", parse_mode="html")
        time.sleep(3)
        bot.delete_message(message.chat.id, aviso.message_id)
        return True
    except: return False

# ==============================================
# 🎛️ PANEL PRINCIPAL CON BOTONES
# ==============================================
def panel_admin():
    texto = """
⚙️ <b>𝐏𝐀𝐍𝐄𝐋 𝐃𝐄 𝐀𝐃𝐌𝐈𝐍</b> ⚙️

👥 <b>𝐆𝐄𝐒𝐓𝐈Ó𝐍 𝐃𝐄 𝐆𝐑𝐔𝐏𝐎𝐒</b>
👤 <b>𝐆𝐄𝐒𝐓𝐈Ó𝐍 𝐃𝐄 𝐔𝐒𝐔𝐀𝐑𝐈𝐎𝐒</b>
💳 <b>𝐌𝐎𝐍𝐈𝐓𝐎𝐑𝐄𝐎 𝐃𝐄 𝐏𝐀𝐆𝐎𝐒</b>
🔄 <b>𝐑𝐄𝐈𝐍𝐈𝐂𝐈𝐀𝐑 𝐁𝐎𝐓</b>
"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn = [
        types.InlineKeyboardButton("📋 Lista Grupos", callback_data="lista_grupos"),
        types.InlineKeyboardButton("ℹ️ Info Grupo", callback_data="info_grupo"),
        types.InlineKeyboardButton("👤 Ver Usuario", callback_data="ver_usuario"),
        types.InlineKeyboardButton("💰 Ver Saldo", callback_data="ver_saldo"),
        types.InlineKeyboardButton("📜 Historial", callback_data="historial"),
        types.InlineKeyboardButton("⏳ Pendientes", callback_data="pendientes"),
        types.InlineKeyboardButton("📊 Métodos", callback_data="metodos"),
        types.InlineKeyboardButton("📈 Estadísticas", callback_data="stats"),
        types.InlineKeyboardButton("🔄 Reiniciar", callback_data="reiniciar")
    ]
    markup.add(*btn)
    return texto, markup

# ==============================================
# 👥 FUNCIONES GRUPOS
# ==============================================
def add_grupo(id_grupo):
    if id_grupo not in GRUPOS_AUTORIZADOS:
        GRUPOS_AUTORIZADOS.append(id_grupo)
        return True, f"✅ <b>GRUPO AUTORIZADO</b>\nID: <code>{id_grupo}</code>"
    return False, "⚠️ Ya existe"

def del_grupo(id_grupo):
    if id_grupo in GRUPOS_AUTORIZADOS:
        GRUPOS_AUTORIZADOS.remove(id_grupo)
        return True, f"❌ <b>GRUPO ELIMINADO</b>\nID: <code>{id_grupo}</code>"
    return False, "⚠️ No existe"

def listar_grupos():
    if not GRUPOS_AUTORIZADOS: return "📝 <b>SIN GRUPOS AUTORIZADOS</b>"
    return "📋 <b>GRUPOS AUTORIZADOS:</b>\n\n" + "\n".join(f"🔹 <code>{g}</code>" for g in GRUPOS_AUTORIZADOS)

def info_grupo(msg):
    return f"""
ℹ️ <b>INFORMACIÓN DEL GRUPO</b>

🏷️ <b>Nombre:</b> {msg.chat.title}
🆔 <b>ID:</b> <code>{msg.chat.id}</code>
👥 <b>Tipo:</b> {msg.chat.type}
🔐 <b>Estado:</b> {"✅ AUTORIZADO" if msg.chat.id in GRUPOS_AUTORIZADOS else "❌ NO AUTORIZADO"}
"""

# ==============================================
# 👤 FUNCIONES USUARIOS
# ==============================================
def info_user(uid, bot):
    try:
        c = conectar_db().cursor()
        c.execute("SELECT nombre, saldo, nivel, baneado FROM usuarios WHERE id=?", (uid,))
        u = c.fetchone() or ("Desconocido", 0, "1", 0)
        nombre, saldo, nivel, baneado = u
        estado = "🔴 BANEADO" if baneado else "🟢 ACTIVO"
        try:
            user = bot.get_chat(uid)
            nombre = user.first_name
            usuario = f"@{user.username}" if user.username else "Sin usuario"
        except: usuario = "No disponible"
        return f"""
👤 <b>𝐃𝐀𝐓𝐎𝐒 𝐃𝐄𝐋 𝐔𝐒𝐔𝐀𝐑𝐈𝐎</b>

🆔 <b>ID:</b> <code>{uid}</code>
📛 <b>Nombre:</b> {nombre}
🔖 <b>Usuario:</b> {usuario}
💰 <b>Saldo:</b> <b>${saldo}</b>
💎 <b>Nivel:</b> {nivel}
🛡️ <b>Estado:</b> {estado}
"""
    except: return "❌ Error"

def saldo_user(uid):
    return f"💰 <b>SALDO:</b> <code>{uid}</code>\n💲 <b>${get_saldo(uid)}</b>"

def ban_user(uid):
    try:
        conn = conectar_db()
        conn.cursor().execute("UPDATE usuarios SET baneado=1 WHERE id=?", (uid,))
        conn.commit()
        return True, f"🔨 <b>BANEADO</b>\nID: <code>{uid}</code>"
    except: return False, "❌ Error"

def unban_user(uid):
    try:
        conn = conectar_db()
        conn.cursor().execute("UPDATE usuarios SET baneado=0 WHERE id=?", (uid,))
        conn.commit()
        return True, f"✅ <b>DESBANEADO</b>\nID: <code>{uid}</code>"
    except: return False, "❌ Error"

# ==============================================
# 💳 FUNCIONES PAGOS
# ==============================================
def historial_pagos():
    try:
        c = conectar_db().cursor()
        c.execute("SELECT id, user_id, monto, metodo, estado FROM pagos ORDER BY id DESC LIMIT 15")
        pagos = c.fetchall()
        if not pagos: return "📝 <b>SIN PAGOS</b>"
        txt = "📜 <b>HISTORIAL DE PAGOS</b>\n\n"
        for p in pagos:
            icono = "✅" if p[4]=="pagado" else "⏳" if p[4]=="pendiente" else "❌"
            txt += f"{icono} <b>#{p[0]}</b> | 👤 <code>{p[1]}</code>\n💰 ${p[2]} | 💳 {p[3]}\n──────────\n"
        return txt
    except: return "❌ Error"

def pendientes_pagos():
    try:
        c = conectar_db().cursor()
        c.execute("SELECT id, user_id, monto, metodo FROM pagos WHERE estado='pendiente'")
        pagos = c.fetchall()
        if not pagos: return "✅ <b>SIN PENDIENTES</b>"
        return "⏳ <b>PENDIENTES</b>\n\n" + "\n".join(f"🔸 <b>#{p[0]}</b> | 👤 <code>{p[1]}</code> | 💰 ${p[2]} | 💳 {p[3]}" for p in pagos)
    except: return "❌ Error"

def metodos_pago():
    try:
        c = conectar_db().cursor()
        c.execute("SELECT metodo, COUNT(*), SUM(monto) FROM pagos GROUP BY metodo")
        datos = c.fetchall()
        if not datos: return "📊 <b>SIN DATOS</b>"
        return "📊 <b>MÉTODOS MÁS USADOS</b>\n\n" + "\n".join(f"💳 <b>{m}</b>\n📦 {c} ops | 💰 ${t}" for m,c,t in datos)
    except: return "❌ Error"

def stats_pagos():
    try:
        c = conectar_db().cursor()
        c.execute("SELECT COUNT(*), SUM(monto) FROM pagos WHERE estado='pagado'")
        total, dinero = c.fetchone()
        c.execute("SELECT COUNT(*) FROM pagos WHERE estado='pendiente'")
        pend = c.fetchone()[0]
        return f"📈 <b>ESTADÍSTICAS</b>\n✅ Exitosos: {total or 0}\n💵 Total: ${dinero or 0}\n⏳ Pendientes: {pend or 0}"
    except: return "❌ Error"

# ==============================================
# 🔘 MANEJADOR DE BOTONES
# ==============================================
def botones(call, bot):
    uid = call.from_user.id
    chat = call.message.chat.id
    data = call.data

    if uid not in ADMINS:
        bot.answer_callback_query(call.id, "❌ No permitido", show_alert=True)
        return

    if data == "lista_grupos":
        bot.send_message(chat, listar_grupos(), parse_mode="html")
    elif data == "info_grupo":
        bot.send_message(chat, info_grupo(call.message), parse_mode="html")
    elif data == "ver_usuario":
        bot.send_message(chat, "⚠️ Usa: /userinfo [ID]", parse_mode="html")
    elif data == "ver_saldo":
        bot.send_message(chat, "⚠️ Usa: /saldo [ID]", parse_mode="html")
    elif data == "historial":
        bot.send_message(chat, historial_pagos(), parse_mode="html")
    elif data == "pendientes":
        bot.send_message(chat, pendientes_pagos(), parse_mode="html")
    elif data == "metodos":
        bot.send_message(chat, metodos_pago(), parse_mode="html")
    elif data == "stats":
        bot.send_message(chat, stats_pagos(), parse_mode="html")
    elif data == "reiniciar":
        bot.send_message(chat, "🔄 <b>REINICIANDO...</b>", parse_mode="html")
        exit()

    bot.answer_callback_query(call.id)
