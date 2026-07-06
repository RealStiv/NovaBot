# ==============================================
# 🛠️ FUNCIONES - NOVA BOT
# ==============================================
import sqlite3
import time
import random

# ==============================================
# 💾 CONEXIÓN A LA BASE DE DATOS
# ==============================================
def conectar_db():
    conn = sqlite3.connect('database.db')
    return conn

# ==============================================
# 📅 CREAR TABLAS (TODAS INCLUIDAS)
# ==============================================
def crear_tablas():
    conn = conectar_db()
    c = conn.cursor()
    
    # Tabla usuarios
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios
                 (id INTEGER PRIMARY KEY, nombre TEXT, saldo REAL, nivel TEXT, baneado INTEGER)''')
    
    # Tabla pagos
    c.execute('''CREATE TABLE IF NOT EXISTS pagos
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, monto REAL, metodo TEXT, estado TEXT, fecha TEXT)''')
    
    # Tabla de Soporte
    c.execute('''CREATE TABLE IF NOT EXISTS soporte
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, mensaje TEXT, fecha TEXT)''')
    
    # Tabla de Revendedores
    c.execute('''CREATE TABLE IF NOT EXISTS revendedores
                 (user_id INTEGER PRIMARY KEY, comision INTEGER, ganancias REAL)''')
    
    # Tabla de Ventas de Revendedores
    c.execute('''CREATE TABLE IF NOT EXISTS ventas_rev
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, rev_id INTEGER, user_id INTEGER, monto REAL, ganancia REAL, fecha TEXT)''')
    
    # 🆕 Tabla de Apuntes (NUEVA)
    c.execute('''CREATE TABLE IF NOT EXISTS apuntes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, texto TEXT, fecha TEXT)''')
    
    conn.commit()
    conn.close()

# Ejecutar al iniciar
crear_tablas()

# ==============================================
# 👤 FUNCIONES DE USUARIOS
# ==============================================
def registrar_usuario(id, nombre):
    conn = conectar_db()
    c = conn.cursor()
    c.execute("SELECT * FROM usuarios WHERE id = ?", (id,))
    if not c.fetchone():
        c.execute("INSERT INTO usuarios VALUES (?, ?, ?, ?, ?)", (id, nombre, 0, "1", 0))
        conn.commit()
    conn.close()

def get_saldo(user_id):
    conn = conectar_db()
    c = conn.cursor()
    c.execute("SELECT saldo FROM usuarios WHERE id = ?", (user_id,))
    saldo = c.fetchone()
    conn.close()
    return saldo[0] if saldo else 0

def agregar_saldo(user_id, cantidad):
    conn = conectar_db()
    c = conn.cursor()
    c.execute("UPDATE usuarios SET saldo = saldo + ? WHERE id = ?", (cantidad, user_id))
    conn.commit()
    conn.close()

def restar_saldo(user_id, cantidad):
    conn = conectar_db()
    c = conn.cursor()
    c.execute("UPDATE usuarios SET saldo = saldo - ? WHERE id = ?", (cantidad, user_id))
    conn.commit()
    conn.close()

# ==============================================
# 🧩 OTRAS FUNCIONES
# ==============================================
def generar_codigo():
    return ''.join(random.SystemRandom().choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8))
