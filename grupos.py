# ==============================================
# 🛡️ SISTEMA COMPLETO - NOVA BOT
# ==============================================
import time
from config import *
from functions import *
from telebot import types
from datetime import datetime

# ⚙️ CONFIGURACIÓN
GRUPOS_AUTORIZADOS = []
inicio_bot = datetime.now()

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
# 🎛️ PANEL PRINCIPAL ADMIN
# ==============================================
def panel_admin():
    texto = """
⚙️ <b>𝐏𝐀𝐍𝐄𝐋 𝐃𝐄 𝐀𝐃𝐌𝐈𝐍</b> ⚙️

👥 <b>𝐆𝐄𝐒𝐓𝐈Ó𝐍 𝐃𝐄 𝐆𝐑𝐔𝐏𝐎𝐒</b>
👤 <b>𝐆𝐄𝐒𝐓𝐈Ó𝐍 𝐃𝐄 𝐔𝐒𝐔𝐀𝐑𝐈𝐎𝐒</b>
💳 <b>𝐌𝐎𝐍𝐈𝐓𝐎𝐑𝐄𝐎 𝐃𝐄 𝐏𝐀𝐆𝐎𝐒</b>
🧑‍💼 <b>𝐑𝐄𝐕𝐄𝐍𝐃𝐄𝐃𝐎𝐑𝐄𝐒</b>
🚀 <b>𝐇𝐄𝐑𝐑𝐀𝐌𝐈𝐄𝐍𝐓𝐀𝐒</b>
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
        types.InlineKeyboardButton("📈 Stats Pagos", callback_data="stats_pagos"),
        types.InlineKeyboardButton("📊 General", callback_data="stats_total"),
        types.InlineKeyboardButton("⏱️ Tiempo", callback_data="tiempo"),
        types.InlineKeyboardButton("🎫 Soporte", callback_data="ver_soporte"),
        types.InlineKeyboardButton("📢 Enviar", callback_data="enviar_msj"),
        types.InlineKeyboardButton("🧑‍💼 Revendedores", callback_data="list_rev"),
        types.InlineKeyboardButton("📊 Monitoreo", callback_data="monitoreo"),
        types.InlineKeyboardButton("🔄 Reiniciar", callback_data="reiniciar")
    ]
    markup.add(*btn)
    return texto, markup

# ==============================================
# 👥 GRUPOS
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
    if not GRUPOS_AUTORIZADOS: return "📝 <b>SIN GRUPOS</b>"
    return "📋 <b>GRUPOS AUTORIZADOS:</b>\n\n" + "\n".join(f"🔹 <code>{g}</code>" for g in GRUPOS_AUTORIZADOS)

def info_grupo(msg):
    return f"""
ℹ️ <b>INFORMACIÓN</b>

🏷️ <b>Nombre:</b> {msg.chat.title}
🆔 <b>ID:</b> <code>{msg.chat.id}</code>
👥 <b>Tipo:</b> {msg.chat.type}
🔐 <b>Estado:</b> {"✅ AUTORIZADO" if msg.chat.id in GRUPOS_AUTORIZADOS else "❌ NO AUTORIZADO"}
"""

# ==============================================
# 👤 USUARIOS
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
👤 <b>𝐃𝐀𝐓𝐎𝐒</b>

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
# 💳 PAGOS
# ==============================================
def historial_pagos():
    try:
        c = conectar_db().cursor()
        c.execute("SELECT id, user_id, monto, metodo, estado FROM pagos ORDER BY id DESC LIMIT 15")
        pagos = c.fetchall()
        if not pagos: return "📝 <b>SIN PAGOS</b>"
        txt = "📜 <b>HISTORIAL</b>\n\n"
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
        return "📊 <b>MÉTODOS</b>\n\n" + "\n".join(f"💳 <b>{m}</b>\n📦 {c} ops | 💰 ${t}" for m,c,t in datos)
    except: return "❌ Error"

def stats_pagos():
    try:
        c = conectar_db().cursor()
        c.execute("SELECT COUNT(*), SUM(monto) FROM pagos WHERE estado='pagado'")
        total, dinero = c.fetchone()
        c.execute("SELECT COUNT(*) FROM pagos WHERE estado='pendiente'")
        pend = c.fetchone()[0]
        return f"📈 <b>STATS PAGOS</b>\n✅ Exitosos: {total or 0}\n💵 Total: ${dinero or 0}\n⏳ Pendientes: {pend or 0}"
    except: return "❌ Error"

# ==============================================
# 🚀 HERRAMIENTAS EXTRAS
# ==============================================
def hora_actual():
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")

def tiempo_activo():
    delta = datetime.now() - inicio_bot
    return f"⏱️ <b>TIEMPO ACTIVO</b>\n{delta.days} días, {delta.seconds//3600}h {(delta.seconds%3600)//60}m"

def stats_generales():
    try:
        c = conectar_db().cursor()
        c.execute("SELECT COUNT(*) FROM usuarios")
        total_u = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM usuarios WHERE baneado=0")
        activos = c.fetchone()[0]
        c.execute("SELECT SUM(monto) FROM pagos WHERE estado='pagado'")
        total_d = c.fetchone()[0] or 0
        return f"""
📈 <b>ESTADÍSTICAS GENERALES</b>

👥 <b>Total:</b> {total_u}
🟢 <b>Activos:</b> {activos}
🔴 <b>Baneados:</b> {total_u - activos}
💵 <b>Total:</b> ${total_d}
📅 <b>{hora_actual()}</b>
"""
    except: return "❌ Error"

def enviar_masivo(texto, bot):
    try:
        c = conectar_db().cursor()
        c.execute("SELECT id FROM usuarios WHERE baneado=0")
        enviados = 0
        for uid in c.fetchall():
            try:
                bot.send_message(uid[0], texto, parse_mode="html")
                enviados += 1
            except: pass
        return f"✅ <b>ENVIADO A {enviados} USUARIOS</b>"
    except: return "❌ Error"

def registrar_soporte(uid, mensaje):
    try:
        conn = conectar_db()
        conn.cursor().execute("INSERT INTO soporte (user_id, mensaje, fecha) VALUES (?, ?, ?)", 
                            (uid, mensaje, hora_actual()))
        conn.commit()
        return "✅ <b>ENVIADO</b>\nUn admin te responderá pronto."
    except: return "❌ Error"

def ver_soporte():
    try:
        c = conectar_db().cursor()
        c.execute("SELECT * FROM soporte ORDER BY id DESC LIMIT 10")
        tickets = c.fetchall()
        if not tickets: return "📝 <b>SIN SOPORTE</b>"
        txt = "🎫 <b>SOPORTE</b>\n\n"
        for t in tickets:
            txt += f"🔸 <b>ID:</b> {t[0]}\n👤 <code>{t[1]}</code>\n💬 {t[2]}\n📅 {t[3]}\n──────────\n"
        return txt
    except: return "❌ Error"

# ==============================================
# 🧑‍💼 SISTEMA DE REVENDEDORES
# ==============================================
def panel_revendedor(uid):
    try:
        c = conectar_db().cursor()
        c.execute("SELECT comision, ganancias FROM revendedores WHERE user_id=?", (uid,))
        res = c.fetchone()
        if not res: return "❌ <b>NO ERES REVENDEDOR</b>"
        com, gan = res
        return f"""
🧑‍💼 <b>𝐏𝐀𝐍𝐄𝐋 𝐑𝐄𝐕𝐄𝐍𝐃𝐄𝐃𝐎𝐑</b>

📊 <b>TUS DATOS</b>
🔹 Comisión: {com}%
💰 Ganancias: ${gan}

📋 <b>OPCIONES</b>
🔹 /misventas - Ver ventas
🔹 /retirar - Solicitar retiro
"""
    except: return "❌ Error"

def ver_mis_ventas(uid):
    try:
        c = conectar_db().cursor()
        c.execute("SELECT * FROM ventas_rev WHERE rev_id=? ORDER BY id DESC LIMIT 15", (uid,))
        ventas = c.fetchall()
        if not ventas: return "📝 <b>SIN VENTAS</b>"
        txt = "📜 <b>MIS VENTAS</b>\n\n"
        for v in ventas:
            txt += f"🔸 <b>#{v[0]}</b>\n👤 <code>{v[2]}</code>\n💰 ${v[3]}\n💸 Ganaste: ${v[4]}\n📅 {v[5]}\n──────────\n"
        return txt
    except: return "❌ Error"

def add_revendedor(uid, porcentaje):
    try:
        conn = conectar_db()
        conn.cursor().execute("REPLACE INTO revendedores VALUES (?, ?, 0)", (uid, porcentaje))
        conn.commit()
        return f"✅ <b>REVENDEDOR AGREGADO</b>\nID: <code>{uid}</code>\nComisión: {porcentaje}%"
    except: return "❌ Error"

def del_revendedor(uid):
    try:
        conn = conectar_db()
        conn.cursor().execute("DELETE FROM revendedores WHERE user_id=?", (uid,))
        conn.commit()
        return "❌ <b>ELIMINADO</b>"
    except: return "❌ Error"

def lista_revendedores():
    try:
        c = conectar_db().cursor()
        c.execute("SELECT * FROM revendedores")
        rev = c.fetchall()
        if not rev: return "📝 <b>SIN REVENDEDORES</b>"
        txt = "📋 <b>REVENDEDORES</b>\n\n"
        for r in rev:
            txt += f"🔹 <code>{r[0]}</code>\n💼 {r[1]}% | 💰 ${r[2]}\n──────────\n"
        return txt
    except: return "❌ Error"

# ==============================================
# 📊 PANEL DE MONITOREO TOTAL
# ==============================================
def panel_monitoreo():
    try:
        c = conectar_db().cursor()
        
        # GENERAL
        c.execute("SELECT COUNT(*), SUM(saldo) FROM usuarios")
        total_u, saldo_t = c.fetchone()
        c.execute("SELECT COUNT(*), SUM(monto) FROM pagos WHERE estado='pagado'")
        total_p, dinero_t = c.fetchone()
        
        # REVENDEDORES Y COMISIONES
        c.execute("SELECT COUNT(*), SUM(ganancias) FROM revendedores")
        total_r, comisiones_t = c.fetchone()
        c.execute("SELECT SUM(ganancia) FROM ventas_rev")
        comisiones_pagadas = c.fetchone()[0] or 0

        return f"""
📊 <b>𝐏𝐀𝐍𝐄𝐋 𝐃𝐄 𝐌𝐎𝐍𝐈𝐓𝐎𝐑𝐄𝐎 𝐓𝐎𝐓𝐀𝐋</b> 📊

👥 <b>USUARIOS</b>
🔹 Total: <b>{total_u}</b>
🔹 Saldo total: <b>${saldo_t or 0}</b>

💳 <b>PAGOS</b>
🔹 Exitosos: <b>{total_p or 0}</b>
🔹 Recaudado: <b>${dinero_t or 0}</b>

🧑‍💼 <b>REVENDEDORES</b>
🔹 Total: <b>{total_r or 0}</b>
🔹 Comisiones generadas: <b>${comisiones_t or 0}</b>
🔹 Comisiones pagadas: <b>${comisiones_pagadas}</b>
🔹 Ganancia neta: <b>${(dinero_t or 0) - comisiones_pagadas}</b>

📅 <b>{hora_actual()}</b>
"""
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

    if data == "lista_grupos": bot.send_message(chat, listar_grupos(), parse_mode="html")
    elif data == "info_grupo": bot.send_message(chat, info_grupo(call.message), parse_mode="html")
    elif data == "ver_usuario": bot.send_message(chat, "⚠️ /userinfo [ID]", parse_mode="html")
    elif data == "ver_saldo": bot.send_message(chat, "⚠️ /saldo [ID]", parse_mode="html")
    elif data == "historial": bot.send_message(chat, historial_pagos(), parse_mode="html")
    elif data == "pendientes": bot.send_message(chat, pendientes_pagos(), parse_mode="html")
    elif data == "metodos": bot.send_message(chat, metodos_pago(), parse_mode="html")
    elif data == "stats_pagos": bot.send_message(chat, stats_pagos(), parse_mode="html")
    elif data == "stats_total": bot.send_message(chat, stats_generales(), parse_mode="html")
    elif data == "tiempo": bot.send_message(chat, tiempo_activo(), parse_mode="html")
    elif data == "ver_soporte": bot.send_message(chat, ver_soporte(), parse_mode="html")
    elif data == "enviar_msj": bot.send_message(chat, "⚠️ /enviar [mensaje]", parse_mode="html")
    elif data == "list_rev": bot.send_message(chat, lista_revendedores(), parse_mode="html")
    elif data == "monitoreo": bot.send_message(chat, panel_monitoreo(), parse_mode="html")
    elif data == "reiniciar":
        bot.send_message(chat, "🔄 <b>REINICIANDO...</b>", parse_mode="html")
        exit()

    bot.answer_callback_query(call.id)
