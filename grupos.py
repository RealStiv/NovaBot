# ==============================================
# 🚀 FUNCIONES NUEVAS - NOVA BOT
# ==============================================
from datetime import datetime

# 📅 HORA ACTUAL
def hora_actual():
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")

# ⏱️ TIEMPO ACTIVO
inicio_bot = datetime.now()

def tiempo_activo():
    delta = datetime.now() - inicio_bot
    dias = delta.days
    horas, resto = divmod(delta.seconds, 3600)
    minutos, segundos = divmod(resto, 60)
    return f"⏱️ <b>TIEMPO ACTIVO</b>\n{dias} días, {horas}h {minutos}m"

# 📊 ESTADÍSTICAS GENERALES
def stats_generales():
    try:
        c = conectar_db().cursor()
        c.execute("SELECT COUNT(*) FROM usuarios")
        total_users = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM usuarios WHERE baneado=0")
        activos = c.fetchone()[0]
        c.execute("SELECT SUM(monto) FROM pagos WHERE estado='pagado'")
        total_dinero = c.fetchone()[0] or 0
        return f"""
📈 <b>ESTADÍSTICAS GENERALES</b>

👥 <b>Total Usuarios:</b> {total_users}
🟢 <b>Activos:</b> {activos}
🔴 <b>Baneados:</b> {total_users - activos}
💵 <b>Total Recaudado:</b> ${total_dinero}
📅 <b>Fecha:</b> {hora_actual()}
"""
    except: return "❌ Error al cargar"

# 📢 ENVÍO MASIVO
def enviar_masivo(texto, bot):
    try:
        c = conectar_db().cursor()
        c.execute("SELECT id FROM usuarios WHERE baneado=0")
        usuarios = c.fetchall()
        enviados = 0
        for uid in usuarios:
            try:
                bot.send_message(uid[0], texto, parse_mode="html")
                enviados += 1
            except: pass
        return f"✅ <b>ENVIADO A {enviados} USUARIOS</b>"
    except: return "❌ Error"

# 🎫 SISTEMA DE SOPORTE
def registrar_soporte(uid, mensaje):
    try:
        conn = conectar_db()
        c = conn.cursor()
        c.execute("INSERT INTO soporte (user_id, mensaje, fecha) VALUES (?, ?, ?)", 
                  (uid, mensaje, hora_actual()))
        conn.commit()
        return "✅ <b>MENSAJE ENVIADO</b>\nUn administrador te responderá pronto."
    except: return "❌ No se pudo enviar"

def ver_soporte():
    try:
        c = conectar_db().cursor()
        c.execute("SELECT * FROM soporte ORDER BY id DESC LIMIT 10")
        tickets = c.fetchall()
        if not tickets: return "📝 <b>SIN MENSAJES DE SOPORTE</b>"
        txt = "🎫 <b>MENSAJES DE SOPORTE</b>\n\n"
        for t in tickets:
            txt += f"🔸 <b>ID:</b> {t[0]}\n👤 <code>{t[1]}</code>\n💬 {t[2]}\n📅 {t[3]}\n──────────\n"
        return txt
    except: return "❌ Error"

# ==============================================
# 🔘 ACTUALIZAR PANEL CON BOTONES NUEVOS
# ==============================================
def panel_admin():
    texto = """
⚙️ <b>𝐏𝐀𝐍𝐄𝐋 𝐃𝐄 𝐀𝐃𝐌𝐈𝐍</b> ⚙️

👥 <b>𝐆𝐄𝐒𝐓𝐈Ó𝐍 𝐃𝐄 𝐆𝐑𝐔𝐏𝐎𝐒</b>
👤 <b>𝐆𝐄𝐒𝐓𝐈Ó𝐍 𝐃𝐄 𝐔𝐒𝐔𝐀𝐑𝐈𝐎𝐒</b>
💳 <b>𝐌𝐎𝐍𝐈𝐓𝐎𝐑𝐄𝐎 𝐃𝐄 𝐏𝐀𝐆𝐎𝐒</b>
🚀 <b>𝐇𝐄𝐑𝐑𝐀𝐌𝐈𝐄𝐍𝐓𝐀𝐒 𝐄𝐗𝐓𝐑𝐀𝐒</b>
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
        types.InlineKeyboardButton("📈 Stats", callback_data="stats_pagos"),
        types.InlineKeyboardButton("📊 General", callback_data="stats_total"),
        types.InlineKeyboardButton("⏱️ Tiempo", callback_data="tiempo"),
        types.InlineKeyboardButton("🎫 Soporte", callback_data="ver_soporte"),
        types.InlineKeyboardButton("📢 Enviar", callback_data="enviar_msj"),
        types.InlineKeyboardButton("🔄 Reiniciar", callback_data="reiniciar")
    ]
    markup.add(*btn)
    return texto, markup

# ==============================================
# 🔘 ACTUALIZAR MANEJADOR DE BOTONES
# ==============================================
def botones(call, bot):
    uid = call.from_user.id
    chat = call.message.chat.id
    data = call.data

    if uid not in ADMINS:
        bot.answer_callback_query(call.id, "❌ No permitido", show_alert=True)
        return

    # BOTONES VIEJOS
    if data == "lista_grupos": bot.send_message(chat, listar_grupos(), parse_mode="html")
    elif data == "info_grupo": bot.send_message(chat, info_grupo(call.message), parse_mode="html")
    elif data == "ver_usuario": bot.send_message(chat, "⚠️ Usa: /userinfo [ID]", parse_mode="html")
    elif data == "ver_saldo": bot.send_message(chat, "⚠️ Usa: /saldo [ID]", parse_mode="html")
    elif data == "historial": bot.send_message(chat, historial_pagos(), parse_mode="html")
    elif data == "pendientes": bot.send_message(chat, pendientes_pagos(), parse_mode="html")
    elif data == "metodos": bot.send_message(chat, metodos_pago(), parse_mode="html")
    elif data == "stats_pagos": bot.send_message(chat, stats_pagos(), parse_mode="html")
    
    # BOTONES NUEVOS
    elif data == "stats_total": bot.send_message(chat, stats_generales(), parse_mode="html")
    elif data == "tiempo": bot.send_message(chat, tiempo_activo(), parse_mode="html")
    elif data == "ver_soporte": bot.send_message(chat, ver_soporte(), parse_mode="html")
    elif data == "enviar_msj": bot.send_message(chat, "⚠️ Usa: /enviar [mensaje]", parse_mode="html")
    
    elif data == "reiniciar":
        bot.send_message(chat, "🔄 <b>REINICIANDO...</b>", parse_mode="html")
        exit()

    bot.answer_callback_query(call.id)
