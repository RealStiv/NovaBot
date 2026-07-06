# ==============================================
# 🤖 NOVA BOT - VERSIÓN COMPLETA
# ==============================================
import telebot
from config import *
from functions import *
from grupos import *

# ==============================================
# ⚙️ INICIAR
# ==============================================
bot = telebot.TeleBot(TOKEN)

# ==============================================
# 🔄 REINICIO
# ==============================================
@bot.message_handler(commands=['reiniciar', 'restart'])
def cmd_reiniciar(message):
    if message.from_user.id in ADMINS:
        bot.send_message(message.chat.id, "🔄 <b>REINICIANDO...</b>", parse_mode="html")
        exit()

# ==============================================
# 🚀 PANEL ADMIN
# ==============================================
@bot.message_handler(commands=['paneladmin'])
def cmd_panel(message):
    if message.from_user.id in ADMINS:
        txt, mk = panel_admin()
        bot.send_message(message.chat.id, txt, reply_markup=mk, parse_mode="html")

# ==============================================
# 👥 GRUPOS
# ==============================================
@bot.message_handler(commands=['addgrupo'])
def cmd_add(message):
    if message.from_user.id not in ADMINS: return
    try:
        ok, txt = add_grupo(int(message.text.split()[1]))
        bot.send_message(message.chat.id, txt, parse_mode="html")
    except: bot.send_message(message.chat.id, "⚠️ /addgrupo [ID]")

@bot.message_handler(commands=['delgrupo'])
def cmd_del(message):
    if message.from_user.id not in ADMINS: return
    try:
        ok, txt = del_grupo(int(message.text.split()[1]))
        bot.send_message(message.chat.id, txt, parse_mode="html")
    except: bot.send_message(message.chat.id, "⚠️ /delgrupo [ID]")

@bot.message_handler(commands=['listagrupos'])
def cmd_list(message):
    if message.from_user.id in ADMINS:
        bot.send_message(message.chat.id, listar_grupos(), parse_mode="html")

@bot.message_handler(commands=['infogrupo'])
def cmd_info(message):
    if message.from_user.id in ADMINS:
        bot.send_message(message.chat.id, info_grupo(message), parse_mode="html")

# ==============================================
# 👤 USUARIOS
# ==============================================
@bot.message_handler(commands=['userinfo'])
def cmd_userinfo(message):
    if message.from_user.id not in ADMINS: return
    try:
        bot.send_message(message.chat.id, info_user(int(message.text.split()[1]), bot), parse_mode="html")
    except: bot.send_message(message.chat.id, "⚠️ /userinfo [ID]")

@bot.message_handler(commands=['saldo'])
def cmd_saldo(message):
    if message.from_user.id not in ADMINS: return
    try:
        bot.send_message(message.chat.id, saldo_user(int(message.text.split()[1])), parse_mode="html")
    except: bot.send_message(message.chat.id, "⚠️ /saldo [ID]")

@bot.message_handler(commands=['ban'])
def cmd_ban(message):
    if message.from_user.id not in ADMINS: return
    try:
        ok, txt = ban_user(int(message.text.split()[1]))
        bot.send_message(message.chat.id, txt, parse_mode="html")
    except: bot.send_message(message.chat.id, "⚠️ /ban [ID]")

@bot.message_handler(commands=['unban'])
def cmd_unban(message):
    if message.from_user.id not in ADMINS: return
    try:
        ok, txt = unban_user(int(message.text.split()[1]))
        bot.send_message(message.chat.id, txt, parse_mode="html")
    except: bot.send_message(message.chat.id, "⚠️ /unban [ID]")

# ==============================================
# 💳 PAGOS
# ==============================================
@bot.message_handler(commands=['historialpagos'])
def cmd_historial(message):
    if message.from_user.id in ADMINS:
        bot.send_message(message.chat.id, historial_pagos(), parse_mode="html")

@bot.message_handler(commands=['pagospendientes'])
def cmd_pendientes(message):
    if message.from_user.id in ADMINS:
        bot.send_message(message.chat.id, pendientes_pagos(), parse_mode="html")

@bot.message_handler(commands=['metodospago'])
def cmd_metodos(message):
    if message.from_user.id in ADMINS:
        bot.send_message(message.chat.id, metodos_pago(), parse_mode="html")

@bot.message_handler(commands=['estadisticaspagos'])
def cmd_stats_p(message):
    if message.from_user.id in ADMINS:
        bot.send_message(message.chat.id, stats_pagos(), parse_mode="html")

# ==============================================
# 🚀 HERRAMIENTAS
# ==============================================
@bot.message_handler(commands=['estadisticas', 'stats'])
def cmd_stats(message):
    if message.from_user.id in ADMINS:
        bot.send_message(message.chat.id, stats_generales(), parse_mode="html")

@bot.message_handler(commands=['tiempo', 'uptime'])
def cmd_tiempo(message):
    if message.from_user.id in ADMINS:
        bot.send_message(message.chat.id, tiempo_activo(), parse_mode="html")

@bot.message_handler(commands=['enviar', 'broadcast'])
def cmd_enviar(message):
    if message.from_user.id not in ADMINS: return
    try:
        texto = message.text.split(" ", 1)[1]
        bot.send_message(message.chat.id, enviar_masivo(texto, bot), parse_mode="html")
    except: bot.send_message(message.chat.id, "⚠️ /enviar [mensaje]")

@bot.message_handler(commands=['soporte', 'ayuda'])
def cmd_soporte(message):
    try:
        texto = message.text.split(" ", 1)[1]
        bot.send_message(message.chat.id, registrar_soporte(message.from_user.id, texto), parse_mode="html")
        for admin in ADMINS:
            try:
                bot.send_message(admin, f"🎫 <b>NUEVO SOPORTE</b>\n👤 <code>{message.from_user.id}</code>\n💬 {texto}", parse_mode="html")
            except: pass
    except: bot.send_message(message.chat.id, "⚠️ /soporte [mensaje]")

@bot.message_handler(commands=['versoporte', 'tickets'])
def cmd_ver_soporte(message):
    if message.from_user.id in ADMINS:
        bot.send_message(message.chat.id, ver_soporte(), parse_mode="html")

# ==============================================
# 🧑‍💼 REVENDEDORES
# ==============================================
@bot.message_handler(commands=['revendedor', 'panelrev'])
def cmd_panel_rev(message):
    bot.send_message(message.chat.id, panel_revendedor(message.from_user.id), parse_mode="html")

@bot.message_handler(commands=['misventas', 'misganancias'])
def cmd_mis_ventas(message):
    bot.send_message(message.chat.id, ver_mis_ventas(message.from_user.id), parse_mode="html")

@bot.message_handler(commands=['addrev'])
def cmd_add_rev(message):
    if message.from_user.id not in ADMINS: return
    try:
        uid = int(message.text.split()[1])
        por = int(message.text.split()[2])
        bot.send_message(message.chat.id, add_revendedor(uid, por), parse_mode="html")
    except: bot.send_message(message.chat.id, "⚠️ /addrev [ID] [PORCENTAJE]")

@bot.message_handler(commands=['delrev'])
def cmd_del_rev(message):
    if message.from_user.id not in ADMINS: return
    try:
        uid = int(message.text.split()[1])
        bot.send_message(message.chat.id, del_revendedor(uid), parse_mode="html")
    except: bot.send_message(message.chat.id, "⚠️ /delrev [ID]")

@bot.message_handler(commands=['listarev'])
def cmd_list_rev(message):
    if message.from_user.id in ADMINS:
        bot.send_message(message.chat.id, lista_revendedores(), parse_mode="html")

@bot.message_handler(commands=['monitoreo'])
def cmd_monitoreo(message):
    if message.from_user.id in ADMINS:
        bot.send_message(message.chat.id, panel_monitoreo(), parse_mode="html")

# ==============================================
# 🔘 BOTONES
# ==============================================
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    botones(call, bot)

# ==============================================
# 🛡️ SEGURIDAD
# ==============================================
@bot.message_handler(func=lambda m: True)
def seguridad(m):
    if not verificar_acceso(m.chat.id, m.from_user.id):
        bloquear_spam(m, bot)

# ==============================================
# 🚀 INICIAR
# ==============================================
print("✅ BOT COMPLETO ENCENDIDO")
bot.polling(none_stop=True)
