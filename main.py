import telebot
import time
import sys
import os
from functions import *
from grupos import *

# ==============================================
# 🤖 INICIALIZACIÓN DEL BOT
# ==============================================
print("🚀 INICIANDO BOT...")
print("🔧 Configurando conexión segura...")

telebot.apihelper.CONNECT_TIMEOUT = 10
telebot.apihelper.READ_TIMEOUT = 15
telebot.apihelper.SSL_VERIFY = False

bot = telebot.TeleBot(TOKEN)

# ==============================================
# 🛡️ MANEJO DE ERRORES GLOBALES
# ==============================================
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    print(f"🔥 ERROR CRÍTICO: {exc_value}")
    enviar_log(bot, f"🔥 BOT SE CAYÓ\nError: {exc_value}", "ERROR")
    
    time.sleep(5)
    print("🔄 Reiniciando bot...")
    os.execv(sys.executable, ['python'] + sys.argv)

sys.excepthook = handle_exception

# ==============================================
# 🚪 VERIFICACIÓN DE GRUPOS
# ==============================================
@bot.message_handler(content_types=['new_chat_members'])
def revisar_entrada(message):
    for member in message.new_chat_members:
        if member.id == bot.get_me().id:
            if not puede_estar_en_grupo(message.chat.id):
                bot.send_message(message.chat.id, 
                    "🚫 **ACCESO DENEGADO**\n\nEste bot no tiene permiso para estar aquí.\nSeré removido automáticamente.", 
                    parse_mode="markdown")
                time.sleep(2)
                bot.leave_chat(message.chat.id)
            break

# ==============================================
# ⚙️ COMANDOS DE GRUPOS
# ==============================================
@bot.message_handler(commands=['addgrupo'])
def add_grupo_cmd(message):
    if es_admin(message.from_user.id):
        comando_agregar_grupo(bot, message, message.from_user.id)
        
@bot.message_handler(commands=['delgrupo'])
def del_grupo_cmd(message):
    if es_admin(message.from_user.id):
        comando_remover_grupo(bot, message, message.from_user.id)
        
@bot.message_handler(commands=['listargrupos'])
def listar_cmd(message):
    if es_admin(message.from_user.id):
        comando_lista_grupos(bot, message, message.from_user.id)

# ==============================================
# 👑 PANEL DE ADMINISTRACIÓN PREMIUM
# ==============================================
@bot.message_handler(commands=['admin'])
def panel_admin(message):
    uid = message.from_user.id
    if not es_admin(uid):
        bot.send_message(uid, "❌ Acceso denegado. Solo administradores.")
        return
    
    menu_admin = """
╔═══════════════════════════════╗
║ 👑 𝐏𝐀𝐍𝐄𝐋 𝐃𝐄 𝐀𝐃𝐌𝐈𝐍 👑 ║
╚═══════════════════════════════╝

🔰 Bienvenido al sistema de control.
Selecciona una opción abajo:
"""
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("💰 Añadir Saldo", callback_data="admin_addsaldo"),
        telebot.types.InlineKeyboardButton("🔑 Crear Key", callback_data="admin_createkey"),
        telebot.types.InlineKeyboardButton("🤝 Hacer Revendedor", callback_data="admin_revendedor"),
        telebot.types.InlineKeyboardButton("🎫 Crear Cupón", callback_data="admin_cupon"),
        telebot.types.InlineKeyboardButton("🎁 Iniciar Sorteo", callback_data="admin_sorteo"),
        telebot.types.InlineKeyboardButton("📊 Estadísticas", callback_data="admin_stats"),
        telebot.types.InlineKeyboardButton("🔨 Banear Usuario", callback_data="admin_ban"),
        telebot.types.InlineKeyboardButton("📢 Enviar Anuncio", callback_data="admin_anuncio")
    )
    
    bot.send_message(message.chat.id, menu_admin, reply_markup=markup, parse_mode="markdown")

# ==============================================
# 📩 COMANDO /START
# ==============================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    uid = message.from_user.id
    nombre = message.from_user.first_name
    
    if esta_baneado(uid):
        bot.send_message(uid, textos[get_lang(uid)]['banned'])
        return
    
    # Verificar si es nuevo
    conn = conectar_db()
    c = conn.cursor()
    c.execute("SELECT * FROM usuarios WHERE id=?", (uid,))
    if not c.fetchone():
        c.execute("INSERT INTO usuarios (id, nombre) VALUES (?,?)", (uid, nombre))
        conn.commit()
        add_log(bot, "JOIN", uid, f"Nuevo usuario: {nombre}")
    conn.close()
    
    lang = get_lang(uid)
    menu = f"""
🎉 <b>{textos[lang]['welcome']}</b>

👋 ¡Hola <b>{nombre}</b>!
🤖 <i>Soy tu asistente virtual personal.</i>

💡 <b>¿Qué puedo hacer por ti hoy?</b>
"""
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("💰 Saldo", callback_data="saldo"),
        telebot.types.InlineKeyboardButton("📦 Servicios", callback_data="servicios"),
        telebot.types.InlineKeyboardButton("🔑 Activar Key", callback_data="activar"),
        telebot.types.InlineKeyboardButton("🎫 Usar Cupón", callback_data="cupon"),
        telebot.types.InlineKeyboardButton("📜 Historial", callback_data="historial"),
        telebot.types.InlineKeyboardButton("🤝 Panel Revendedor", callback_data="reseller")
    )
    
    bot.send_message(uid, menu, reply_markup=markup, parse_mode="html")

# ==============================================
# 🔘 MANEJADOR DE BOTONES (CALLBACKS)
# ==============================================
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    uid = call.from_user.id
    lang = get_lang(uid)
    
    # Verificar Spam
    if verificar_spam(uid):
        bot.answer_callback_query(call.id, textos[lang]['spam_blocked'].format(seg=TIEMPO_BLOQUEO), show_alert=True)
        return

    # ===================== OPCIONES DEL MENU =====================
    if call.data == "saldo":
        saldo = get_saldo(uid)
        bot.answer_callback_query(call.id, f"Tu saldo es: ${saldo}")
        
    elif call.data == "servicios":
        mostrar_servicios(call.message)
        
    elif call.data == "activar":
        msg = bot.send_message(call.message.chat.id, textos[lang]['enter_key'])
        bot.register_next_step_handler(msg, procesar_key)
        
    elif call.data == "cupon":
        msg = bot.send_message(call.message.chat.id, "🎫 Escribe tu código de cupón:")
        bot.register_next_step_handler(msg, procesar_cupon)
        
    elif call.data == "historial":
        mostrar_historial(call.message)
        
    elif call.data == "reseller":
        if es_revendedor(uid):
            mostrar_panel_revendedor(call.message)
        else:
            bot.send_message(uid, "❌ No eres revendedor.")

# ==============================================
# 📦 MOSTRAR SERVICIOS Y PRODUCTOS
# ==============================================
def mostrar_servicios(message):
    uid = message.chat.id
    lang = get_lang(uid)
    
    texto = f"📦 <b>{textos[lang]['services']}</b>\n\n"
    
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    botones = []
    
    for id_prod, datos in productos.items():
        nombre, cant, precio, tipo, service_id = datos
        precio_final = calcular_precio_final(precio)
        texto += f"<code>{id_prod}</code> <b>{nombre}</b> | 💲 <b>{precio_final} USD</b>\n"
        botones.append(telebot.types.InlineKeyboardButton(f"{id_prod} - {nombre}", callback_data=f"comprar_{id_prod}"))
        
    markup.add(*botones)
    bot.send_message(uid, texto, reply_markup=markup, parse_mode="html")

# ==============================================
# 🛒 PROCESO DE COMPRA
# ==============================================
@bot.callback_query_handler(func=lambda call: call.data.startswith('comprar_'))
def procesar_compra(call):
    uid = call.from_user.id
    lang = get_lang(uid)
    product_id = call.data.split("_")[1]
    
    # Obtener datos del producto
    nombre_prod, cantidad, precio_costo, tipo, service_id = productos[product_id]
    precio_final = calcular_precio_final(precio_costo)
    saldo_usuario = get_saldo(uid)
    
    if saldo_usuario < precio_final:
        bot.answer_callback_query(call.id, textos[lang]['no_funds'], show_alert=True)
        return
    
    # Pedir link
    msg = bot.send_message(uid, f"""
⚡ <b>PROCESANDO ORDEN</b>

📦 <b>Producto:</b> {nombre_prod}
💲 <b>Precio:</b> ${precio_final}

🔗 <b>INGRESA EL LINK:</b>
""", parse_mode="html")
    bot.register_next_step_handler(msg, finalizar_compra, product_id, precio_final, service_id)

def finalizar_compra(message, product_id, precio, service_id):
    uid = message.from_user.id
    link = message.text
    
    descontar_saldo(uid, precio)
    
    # Enviar a la API
    exito, respuesta = enviar_orden_api(service_id, link, "1")
    
    if exito:
        order_id = str(random.randint(100000, 999999))
        factura = generar_factura(uid, product_id, "1", precio, link, order_id)
        bot.send_message(uid, factura, parse_mode="html")
        add_log(bot, "PURCHASE", uid, f"Compra exitosa: {product_id} - ${precio}")
    else:
        add_saldo(uid, precio) # Devolvemos saldo
        bot.send_message(uid, f"❌ ERROR: {respuesta}")

# ==============================================
# 🔑 PROCESAR KEY
# ==============================================
def procesar_key(message):
    uid = message.from_user.id
    key = message.text.strip()
    
    valido, saldo = activar_key(uid, key)
    
    if valido:
        bot.send_message(uid, f"✅ ✅ ACTIVADO!\n💲 +${saldo}")
    else:
        bot.send_message(uid, "❌ Clave inválida o ya usada.")

# ==============================================
# 🎫 PROCESAR CUPÓN
# ==============================================
def procesar_cupon(message):
    uid = message.from_user.id
    codigo = message.text.strip()
    
    resultado, descuento = usar_cupon(codigo)
    
    if resultado:
        bot.send_message(uid, f"✅ CUPÓN VÁLIDO!\n🎉 Tienes {descuento}% de descuento.")
    elif descuento == -1:
        bot.send_message(uid, "❌ CUPÓN AGOTADO")
    else:
        bot.send_message(uid, "❌ CUPÓN INEXISTENTE")

# ==============================================
# 📜 HISTORIAL
# ==============================================
def mostrar_historial(message):
    uid = message.chat.id
    compras = obtener_historial_compras(uid)
    
    if not compras:
        bot.send_message(uid, "📜 No tienes compras aún.")
        return
    
    texto = "📜 <b>TUS ÚLTIMAS COMPRAS</b>\n\n"
    for comp in compras:
        fecha, serv, cant, prec, oid = comp
        texto += f"🆔 <code>{oid}</code>\n📅 {fecha}\n🛒 {serv} | 💲 ${prec}\n──────────\n"
    
    bot.send_message(uid, texto, parse_mode="html")

# ==============================================
# 🤝 PANEL REVENDEDOR
# ==============================================
def mostrar_panel_revendedor(message):
    uid = message.chat.id
    saldo = get_saldo(uid)
    ganancias = 0 # Aquí iría la función de obtener ganancias
    
    texto = f"""
🤝 <b>PANEL DE REVENDEDOR</b>

💰 Tu saldo: <b>${saldo}</b>
💸 Tus ganancias: <b>${ganancias}</b>

🔹 Puedes crear Keys para vender.
🔹 Tienes comisión del {int(COMISION_REVENDEDOR*100)}%
"""
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🔑 CREAR KEY", callback_data="reseller_crearkey"))
    bot.send_message(uid, texto, reply_markup=markup, parse_mode="html")

# ==============================================
# ▶️ INICIAR EL SISTEMA
# ==============================================
if __name__ == "__main__":
    print("✅ BASE DE DATOS LISTA")
    criar_tabelas()
    print("🤖 BOT ENCENDIDO Y FUNCIONANDO!")
    print("👑 PANEL ADMIN ACTIVO")
    print("🚀 Listo para recibir comandos...")
# ==============================================
# 🛡️ SEGURIDAD
# ==============================================
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if not verificar_acceso(message.chat.id, message.from_user.id):
        bloquear_spam(message, bot)
        return
    # ... RESTO DE TU CÓDIGO ...

# ==============================================
# 🔘 MANEJAR BOTONES
# ==============================================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    manejar_callback(call, bot)

# ==============================================
# 🚀 COMANDOS DIRECTOS
# ==============================================
@bot.message_handler(commands=['paneladmin'])
def cmd_panel(message):
    if message.from_user.id in ADMINS:
        bot.send_message(message.chat.id, panel_admin_grupos(), parse_mode="html")

@bot.message_handler(commands=['addgrupo'])
def cmd_add(message):
    if message.from_user.id not in ADMINS: return
    try:
        id_grupo = int(message.text.split()[1])
        ok, txt = agregar_grupo_autorizado(id_grupo)
        bot.send_message(message.chat.id, txt, parse_mode="html")
    except:
        bot.send_message(message.chat.id, "⚠️ Uso: /addgrupo [ID]")

@bot.message_handler(commands=['delgrupo'])
def cmd_del(message):
    if message.from_user.id not in ADMINS: return
    try:
        id_grupo = int(message.text.split()[1])
        ok, txt = eliminar_grupo_autorizado(id_grupo)
        bot.send_message(message.chat.id, txt, parse_mode="html")
    except:
        bot.send_message(message.chat.id, "⚠️ Uso: /delgrupo [ID]")

@bot.message_handler(commands=['listagrupos'])
def cmd_list(message):
    if message.from_user.id not in ADMINS: return
    bot.send_message(message.chat.id, listar_grupos_autorizados(), parse_mode="html")

@bot.message_handler(commands=['infogrupo'])
def cmd_info(message):
    if message.from_user.id not in ADMINS: return
    bot.send_message(message.chat.id, info_grupo_actual(message), parse_mode="html")

@bot.message_handler(commands=['userinfo'])
def cmd_userinfo(message):
    if message.from_user.id not in ADMINS: return
    try:
        user_id = int(message.text.split()[1])
        bot.send_message(message.chat.id, info_usuario_completo(user_id, bot), parse_mode="html")
    except:
        bot.send_message(message.chat.id, "⚠️ Uso: /userinfo [ID]")

@bot.message_handler(commands=['saldo'])
def cmd_saldo(message):
    if message.from_user.id not in ADMINS: return
    try:
        user_id = int(message.text.split()[1])
        bot.send_message(message.chat.id, ver_saldo_usuario(user_id), parse_mode="html")
    except:
        bot.send_message(message.chat.id, "⚠️ Uso: /saldo [ID]")

@bot.message_handler(commands=['ban'])
def cmd_ban(message):
    if message.from_user.id not in ADMINS: return
    try:
        user_id = int(message.text.split()[1])
        ok, txt = banear_usuario_db(user_id)
        bot.send_message(message.chat.id, txt, parse_mode="html")
    except:
        bot.send_message(message.chat.id, "⚠️ Uso: /ban [ID]")

@bot.message_handler(commands=['unban'])
def cmd_unban(message):
    if message.from_user.id not in ADMINS: return
    try:
        user_id = int(message.text.split()[1])
        ok, txt = desbanear_usuario_db(user_id)
        bot.send_message(message.chat.id, txt, parse_mode="html")
    except:
        bot.send_message(message.chat.id, "⚠️ Uso: /unban [ID]")


    # ... todo tu código anterior ...

# ==============================================
# 🔄 COMANDO DE REINICIO
# ==============================================
@bot.message_handler(commands=['reiniciar', 'restart'])
def cmd_reiniciar(message):
    if message.from_user.id not in ADMINS:
        return
        
    bot.send_message(message.chat.id, "🔄 <b>REINICIANDO BOT...</b>\nEspera unos segundos...", parse_mode="html")
    
    print("🔄 Bot reiniciado por administrador")
    exit()  # Cierra el proceso y Railway lo revive solo

# ==============================================
# 🚀 INICIAR BOT
# ==============================================
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=20)
        except Exception as e:
            print(f"⚠️ Error en polling: {e}")
            time.sleep(3)
            continue
