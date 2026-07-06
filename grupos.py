# ==============================================
# 🛡️ SISTEMA DE GRUPOS Y ADMIN
# ==============================================
import sqlite3
import random
import requests
from telebot import types

# ==============================================
# 💾 CONEXIÓN
# ==============================================
def conectar_db():
    conn = sqlite3.connect('database.db')
    return conn

def hora_actual():
    from datetime import datetime
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")

# ==============================================
# 📊 PANEL DE MONITOREO TOTAL
# ==============================================
def panel_monitoreo():
    try:
        c = conectar_db().cursor()
        c.execute("SELECT COUNT(*), SUM(saldo) FROM usuarios")
        total_u, saldo_t = c.fetchone()
        c.execute("SELECT COUNT(*), SUM(monto) FROM pagos WHERE estado='pagado'")
        total_p, dinero_t = c.fetchone()
        c.execute("SELECT COUNT(*) FROM pagos WHERE estado='pendiente'")
        pendientes = c.fetchone()[0]
        c.execute("SELECT COUNT(*), SUM(ganancias) FROM revendedores")
        total_r, comisiones_t = c.fetchone()
        c.execute("SELECT SUM(ganancia) FROM ventas_rev")
        comisiones_pagadas = c.fetchone()[0] or 0

        return f"""
📊 <b>𝐏𝐀𝐍𝐄𝐋 𝐃𝐄 𝐌𝐎𝐍𝐈𝐓𝐎𝐑𝐄𝐎 𝐓𝐎𝐓𝐀𝐋</b> 📊

👥 <b>𝐔𝐒𝐔𝐀𝐑𝐈𝐎𝐒</b>
🔹 Total: <b>{total_u}</b>
🔹 Saldo total: <b>${saldo_t or 0}</b>

💳 <b>𝐏𝐀𝐆𝐎𝐒</b>
🔹 Exitosos: <b>{total_p or 0}</b>
🔹 Recaudado: <b>${dinero_t or 0}</b>
🔹 Pendientes: <b>{pendientes or 0}</b>

🧑‍💼 <b>𝐑𝐄𝐕𝐄𝐍𝐃𝐄𝐃𝐎𝐑𝐄𝐒</b>
🔹 Total: <b>{total_r or 0}</b>
🔹 Comisiones: <b>${comisiones_t or 0}</b>
🔹 Ganancia Neta: <b>${(dinero_t or 0) - comisiones_pagadas}</b>

📅 <b>{hora_actual()}</b>
"""
    except: return "❌ Error"

# ==============================================
# 🎛️ MENÚS Y BOTONES
# ==============================================

def botones_principales():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("💳 Mi Saldo", callback_data="saldo")
    btn2 = types.InlineKeyboardButton("📜 Historial", callback_data="movimientos")
    btn3 = types.InlineKeyboardButton("🏅 Mi Nivel", callback_data="nivel")
    btn4 = types.InlineKeyboardButton("👥 Referidos", callback_data="refs")
    btn5 = types.InlineKeyboardButton("💳 Recargar", callback_data="recargar")
    markup.add(btn1, btn2, btn3, btn4, btn5)
    return markup

def botones_admin():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("📊 MONITOREO", callback_data="admin_panel")
    btn2 = types.InlineKeyboardButton("📋 VER LOGS", callback_data="admin_logs")
    btn3 = types.InlineKeyboardButton("💰 VER RETIROS", callback_data="admin_retiros")
    btn4 = types.InlineKeyboardButton("🏆 TOP USUARIOS", callback_data="admin_top")
    btn5 = types.InlineKeyboardButton("👮 SUB-ADMINS", callback_data="admin_subs")
    btn6 = types.InlineKeyboardButton("📤 EXPORTAR", callback_data="admin_export")
    btn7 = types.InlineKeyboardButton("🔧 MANTENIMIENTO", callback_data="admin_mantenimiento")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7)
    return markup

# ==============================================
# 🚀 FUNCIONES DE NEGOCIO
# ==============================================

# 💸 RETIROS
def solicitar_retiro(uid, monto):
    try:
        monto = float(monto)
        conn = conectar_db()
        c = conn.cursor()
        c.execute("SELECT ganancias FROM revendedores WHERE user_id=?", (uid,))
        res = c.fetchone()
        if not res: return "❌ No eres revendedor"
        gan = res[0]
        if gan >= monto:
            c.execute("UPDATE revendedores SET ganancias = ganancias - ? WHERE user_id=?", (monto, uid))
            c.execute("INSERT INTO retiros (rev_id, monto, estado, fecha) VALUES (?, ?, 'pendiente', ?)", 
                      (uid, monto, hora_actual()))
            conn.commit()
            conn.close()
            return f"✅ Solicitud enviada\nMonto: ${monto}"
        else:
            return "❌ Saldo insuficiente"
    except: return "⚠️ /retirar [monto]"

def ver_retiros():
    try:
        c = conectar_db().cursor()
        c.execute("SELECT * FROM retiros WHERE estado='pendiente'")
        rets = c.fetchall()
        if not rets: return "✅ Sin retiros pendientes"
        txt = "📥 <b>RETIROS PENDIENTES</b>\n\n"
        for r in rets:
            txt += f"🔸 ID:<code>{r[0]}</code>\nUser:<code>{r[1]}</code>\nMonto: <b>${r[2]}</b>\n/aprobar{r[0]}\n──────────\n"
        return txt
    except: return "❌ Error"

def aprobar_retiro(id_retiro):
    try:
        conn = conectar_db()
        c = conn.cursor()
        c.execute("UPDATE retiros SET estado='aprobado' WHERE id=?", (id_retiro,))
        conn.commit()
        conn.close()
        return f"✅ Retiro #{id_retiro} Aprobado"
    except: return "❌ Error"

# 🎫 CUPONES
def crear_cupon(codigo, monto, usos=1):
    try:
        conn = conectar_db()
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO cupones VALUES (?, ?, ?)", (codigo, monto, usos))
        conn.commit()
        conn.close()
        return f"🎫 Creado: {codigo} | ${monto}"
    except: return "❌ Error"

def canjear_cupon(uid, codigo):
    try:
        conn = conectar_db()
        c = conn.cursor()
        c.execute("SELECT monto, usos FROM cupones WHERE codigo=?", (codigo,))
        res = c.fetchone()
        if not res: return "❌ Código inválido"
        monto, usos = res
        if usos <= 0: return "⏳ Ya usado"
        c.execute("UPDATE usuarios SET saldo = saldo + ? WHERE id=?", (monto, uid))
        c.execute("UPDATE cupones SET usos = usos - 1 WHERE codigo=?", (codigo,))
        conn.commit()
        conn.close()
        return f"✅ Canjeado! +${monto}"
    except: return "❌ Error"

# 📤 TRANSFERENCIAS
def transferir_saldo(uid_origen, uid_destino, monto):
    try:
        monto = float(monto)
        uid_destino = int(uid_destino)
        conn = conectar_db()
        c = conn.cursor()
        c.execute("SELECT saldo FROM usuarios WHERE id=?", (uid_origen,))
        saldo_o = c.fetchone()[0]
        if saldo_o < monto: return "❌ Saldo insuficiente"
        c.execute("SELECT id FROM usuarios WHERE id=?", (uid_destino,))
        if not c.fetchone(): return "❌ Usuario no existe"
        c.execute("UPDATE usuarios SET saldo = saldo - ? WHERE id=?", (monto, uid_origen))
        c.execute("UPDATE usuarios SET saldo = saldo + ? WHERE id=?", (monto, uid_destino))
        c.execute("INSERT INTO movimientos (user_id, tipo, monto, detalle, fecha) VALUES (?, 'ENVIADO', ?, ?, ?)",
                  (uid_origen, monto, f"A {uid_destino}", hora_actual()))
        c.execute("INSERT INTO movimientos (user_id, tipo, monto, detalle, fecha) VALUES (?, 'RECIBIDO', ?, ?, ?)",
                  (uid_destino, monto, f"De {uid_origen}", hora_actual()))
        conn.commit()
        conn.close()
        return f"✅ Enviado ${monto} a {uid_destino}"
    except: return "⚠️ /transferir [ID] [MONTO]"

# 📜 HISTORIAL
def ver_movimientos(uid):
    try:
        c = conectar_db().cursor()
        c.execute("SELECT * FROM movimientos WHERE user_id=? ORDER BY id DESC LIMIT 15", (uid,))
        movs = c.fetchall()
        if not movs: return "📝 Sin movimientos"
        txt = "📜 <b>HISTORIAL</b>\n\n"
        for m in movs:
            tipo = "📥" if m[2] == "RECIBIDO" else "📤"
            txt += f"{tipo} <b>${m[3]}</b> | {m[4]}\n{m[5]}\n──────────\n"
        return txt
    except: return "❌ Error"

# ==============================================
# ⚙️ ADMINISTRACIÓN
# ==============================================

# 📋 LOGS
def registrar_accion(admin_id, accion, objetivo=""):
    try:
        conn = conectar_db()
        c = conn.cursor()
        c.execute("INSERT INTO logs (admin_id, accion, objetivo, fecha) VALUES (?, ?, ?, ?)",
                  (admin_id, accion, objetivo, hora_actual()))
        conn.commit()
        conn.close()
    except: pass

def ver_logs():
    try:
        c = conectar_db().cursor()
        c.execute("SELECT * FROM logs ORDER BY id DESC LIMIT 20")
        logs = c.fetchall()
        if not logs: return "📝 Sin registros"
        txt = "📋 <b>HISTORIAL DE ACCIONES</b>\n\n"
        for log in logs:
            txt += f"🔹 {log[4]}\nAdmin: {log[1]} | {log[2]} {log[3]}\n──────────\n"
        return txt
    except: return "❌ Error"

# 👮 SUB-ADMINS
def add_subadmin(uid):
    try:
        conn = conectar_db()
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO subadmins VALUES (?)", (uid,))
        conn.commit()
        return f"✅ Sub-Admin {uid} agregado"
    except: return "❌ Error"

def del_subadmin(uid):
    try:
        conn = conectar_db()
        c = conn.cursor()
        c.execute("DELETE FROM subadmins WHERE user_id=?", (uid,))
        conn.commit()
        return f"❌ Sub-Admin {uid} eliminado"
    except: return "❌ Error"

def lista_subadmins():
    try:
        c = conectar_db()
        c.execute("SELECT * FROM subadmins")
        subs = c.fetchall()
        if not subs: return "📝 Sin sub-admins"
        txt = "👮 <b>LISTA DE SUB-ADMINS</b>\n\n"
        for s in subs: txt += f"🔹 <code>{s[0]}</code>\n"
        return txt
    except: return "❌ Error"

def es_subadmin(uid):
    try:
        c = conectar_db()
        c.execute("SELECT * FROM subadmins WHERE user_id=?", (uid,))
        return c.fetchone() is not None
    except: return False

# 📊 TOP
def top_usuarios():
    try:
        c = conectar_db()
        c.execute("SELECT id, nombre, saldo FROM usuarios ORDER BY saldo DESC LIMIT 10")
        top = c.fetchall()
        if not top: return "📊 Sin datos"
        txt = "🏆 <b>TOP 10 USUARIOS</b>\n\n"
        for i,u in enumerate(top,1): txt += f"{i}️⃣ <code>{u[0]}</code>\n👤 {u[1]}\n💰 ${u[2]}\n──────────\n"
        return txt
    except: return "❌ Error"

# 🔒 MANTENIMIENTO
MANTENIMIENTO = False
def activar_mantenimiento(): global MANTENIMIENTO; MANTENIMIENTO = True; return "🔧 Mantenimiento ON"
def desactivar_mantenimiento(): global MANTENIMIENTO; MANTENIMIENTO = False; return "✅ Mantenimiento OFF"

# 📤 EXPORTAR
def exportar_usuarios():
    try:
        c = conectar_db()
        c.execute("SELECT id, nombre, saldo FROM usuarios")
        users = c.fetchall()
        archivo = "usuarios.txt"
        with open(archivo,"w") as f:
            for u in users: f.write(f"ID: {u[0]} | NOM: {u[1]} | $:{u[2]}\n")
        return archivo, f"✅ Exportado! {len(users)} usuarios"
    except: return None, "❌ Error"

# ==============================================
# 🚀 FUNCIONES PREMIUM
# ==============================================

# 🏅 NIVELES
def actualizar_nivel(uid):
    try:
        c = conectar_db()
        c.execute("SELECT saldo, nivel FROM usuarios WHERE id=?", (uid,))
        saldo, nivel_actual = c.fetchone()
        if saldo >= 1000: nuevo_nivel = "💎 DIAMANTE"; desc = 15
        elif saldo >= 500: nuevo_nivel = "💛 ORO"; desc = 10
        elif saldo >= 100: nuevo_nivel = "💿 PLATA"; desc = 5
        else: nuevo_nivel = "🔰 BRONCE"; desc = 0
        if nivel_actual != nuevo_nivel:
            c.execute("UPDATE usuarios SET nivel=? WHERE id=?", (nuevo_nivel, uid))
            conectar_db().commit()
        return desc, nuevo_nivel
    except: return 0, "🔰 BRONCE"

def panel_niveles(uid):
    desc, niv = actualizar_nivel(uid)
    return f"""
🏅 <b>𝐒𝐈𝐒𝐓𝐄𝐌𝐀 𝐃𝐄 𝐍𝐈𝐕𝐄𝐋𝐄𝐒</b>

✨ Tu Nivel: <b>{niv}</b>
🎁 Descuento: <b>{desc}%</b>

📊 Requisitos:
🔰 BRONCE: $0 - $99
💿 PLATA: $100 - $499
💛 ORO: $500 - $999
💎 DIAMANTE: +$1000
"""

# 📢 CANAL OBLIGATORIO
CANAL_REQUERIDO = "@tu_canal"
def usuario_en_canal(uid, bot):
    try:
        info = bot.get_chat_member(CANAL_REQUERIDO, uid)
        return info.status not in ['left', 'kicked']
    except: return False
def mensaje_unirse():
    return f"""
📢 <b>𝐀𝐂𝐂𝐄𝐒𝐎 𝐑𝐄𝐒𝐓𝐑𝐈𝐍𝐆𝐈𝐃𝐎</b>

Únete para usar el bot:
👉 {CANAL_REQUERIDO}
"""

# 🧾 FACTURACIÓN
def generar_ticket(id_op, uid, monto, tipo):
    return f"""
🧾 <b>𝐓𝐈𝐂𝐊𝐄𝐓 𝐃𝐄 𝐎𝐏𝐄𝐑𝐀𝐂𝐈Ó𝐍</b>

🆔 ID: <code>#{id_op}</code>
👤 Usuario: <code>{uid}</code>
💰 Monto: <b>${monto}</b>
📝 Tipo: <b>{tipo}</b>
📅 Fecha: <b>{hora_actual()}</b>

✅ OPERACIÓN EXITOSA
"""

# 🔁 REFERIDOS
def registrar_referido(uid_invitor, uid_new):
    try:
        conn = conectar_db()
        c = conn.cursor()
        c.execute("SELECT * FROM referidos WHERE user_id=?", (uid_new,))
        if c.fetchone(): return
        c.execute("INSERT INTO referidos VALUES (?, ?)", (uid_new, uid_invitor))
        c.execute("UPDATE usuarios SET saldo = saldo + 5 WHERE id=?", (uid_invitor,))
        conn.commit()
        conn.close()
    except: pass

def mis_referidos(uid):
    try:
        c = conectar_db()
        c.execute("SELECT COUNT(*) FROM referidos WHERE invitador=?", (uid,))
        cant = c.fetchone()[0]
        return f"""
👥 <b>𝐌𝐈𝐒 𝐑𝐄𝐅𝐄𝐑𝐈𝐃𝐎𝐒</b>

🔢 Invitados: <b>{cant}</b>
💰 Ganaste: <b>${cant * 5}</b>

🔗 Enlace:
<code>https://t.me/tu_bot?start={uid}</code>
"""
    except: return "❌ Error"

# ==============================================
# 🛠️ HERRAMIENTAS
# ==============================================
def generar_tarjeta(bin_num):
    try:
        bin_num = str(bin_num)[:6]
        mes = random.randint(1,12); anio = random.randint(25,30); cvv = random.randint(100,999)
        numero = bin_num
        while len(numero) < 15: numero += str(random.randint(0,9))
        suma=0; pos=0; reverso = numero[::-1]
        for d in reverso:
            temp=int(d)*2 if pos%2==0 else int(d)
            suma+= temp-9 if temp>9 else temp
            pos+=1
        dv = 10-(suma%10); dv=0 if dv==10 else dv
        tarjeta = bin_num + numero[6:] + str(dv)
        return f"💳 <code>{tarjeta}|{mes:02d}|20{anio}|{cvv}</code>"
    except: return "⚠️ /gen [BIN]"

def verificar_bin(bin_num):
    try:
        r = requests.get(f"https://bins.antipublic.cc/bins/{bin_num}").json()
        return f"🏦 {r['bank']}\n🌍 {r['country_name']}\n💳 {r['brand']} {r['type']}"
    except: return "❌ Error"

def calcular_porcentaje(num, por):
    try:
        num=float(num); por=float(por); res=(num*por)/100; total=num-res
        return f"🧮 ${num} - {por}% = <b>${total:.2f}</b>\n(Ahorraste: ${res:.2f})"
    except: return "⚠️ /calcular [MONTO] [PORCENTAJE]"

def generar_contraseña(lon=12):
    car = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()"
    return "🔐 <code>" + ''.join(random.choice(car) for _ in range(int(lon))) + "</code>"

def convertir_moneda(cant):
    try:
        cant = float(cant); bs = cant * 6.96
        return f"💵 ${cant} = 🇧🇴 {bs:.2f} Bs"
    except: return "⚠️ /convertir [CANTIDAD]"

def jugar_dado(): return f"🎲 Salió el <b>{random.randint(1,6)}</b>"
def jugar_moneda(): return f"🪙 Salió: <b>{random.choice(['CARA','CRUZ'])}</b>"

def guardar_apunte(uid, txt):
    try:
        conn = conectar_db()
        c = conn.cursor()
        c.execute("INSERT INTO apuntes VALUES (null, ?, ?, ?)", (uid, txt, hora_actual()))
        conn.commit()
        return "✅ Guardado!"
    except: return "❌ Error"
def ver_apuntes(uid):
    try:
        c = conectar_db()
        c.execute("SELECT texto, fecha FROM apuntes WHERE user_id=? ORDER BY id DESC", (uid,))
        aps = c.fetchall()
        if not aps: return "📝 Sin apuntes"
        return "\n".join([f"📝 {a[1]}\n{a[0]}\n───" for a in aps])
    except: return "❌ Error"

def agregar_item(uid, it):
    try:
        conn = conectar_db()
        c = conn.cursor()
        c.execute("INSERT INTO lista_compra VALUES (null, ?, ?)", (uid, it))
        conn.commit()
        return "✅ Agregado!"
    except: return "❌ Error"
def ver_lista(uid):
    try:
        c = conectar_db()
        c.execute("SELECT item FROM lista_compra WHERE user_id=?", (uid,))
        its = c.fetchall()
        if not its: return "🛒 Lista vacía"
        return "🛒 <b>MI LISTA</b>\n\n" + "\n".join([f"🔹 {i[0]}" for i in its])
    except: return "❌ Error"
def limpiar_lista(uid):
    try:
        conn = conectar_db()
        c = conn.cursor()
        c.execute("DELETE FROM lista_compra WHERE user_id=?", (uid,))
        conn.commit()
        return "🗑️ Lista vaciada"
    except: return "❌ Error"
