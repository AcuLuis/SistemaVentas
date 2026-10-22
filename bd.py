# ACCESO A LA BASE DE DATOS: CONFIGURACION, CONEXION Y CONSULTAS PARAMETRIZADAS
import os
import sys
import configparser
from contextlib import contextmanager
import pymysql

# EN EL EJECUTABLE (PYINSTALLER) config.ini VA JUNTO AL .exe; AL EJECUTAR CON PYTHON, JUNTO A ESTE ARCHIVO
DIRECTORIO_DATOS = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
ARCHIVO_CONFIG = os.path.join(DIRECTORIO_DATOS, "config.ini")

class ErrorConfiguracion(Exception):
    pass

def lee_configuracion(ruta):
    if not os.path.exists(ruta):
        raise ErrorConfiguracion("No se encontró config.ini.\nCopia config.ejemplo.ini como config.ini y completa tus datos de MySQL.")
    lector = configparser.ConfigParser(interpolation=None) # SIN INTERPOLACION: LA CONTRASEÑA PUEDE TENER %
    lector.read(ruta, encoding="utf-8")
    if "mysql" not in lector:
        raise ErrorConfiguracion("config.ini debe tener una sección [mysql].")
    datos = lector["mysql"]
    try:
        puerto = datos.getint("port", 3306)
    except ValueError:
        raise ErrorConfiguracion("En config.ini, port debe ser un número.")
    return {
        "host": datos.get("host", "127.0.0.1"),
        "port": puerto,
        "user": datos.get("user", "root"),
        "password": datos.get("password", ""),
        "database": datos.get("database", "bd_tienda_tecnologia"),
    }

def minutos_bloqueo(ruta=ARCHIVO_CONFIG): # [sistema] bloqueo_minutos EN config.ini (OPCIONAL); 0 DESACTIVA EL BLOQUEO
    lector = configparser.ConfigParser(interpolation=None)
    lector.read(ruta, encoding="utf-8")
    try:
        return max(0, lector.getint("sistema", "bloqueo_minutos", fallback=10))
    except ValueError:
        return 10

config = None # SE LEE DE config.ini EN LA PRIMERA CONEXION

def conexion():
    global config
    if config is None:
        config = lee_configuracion(ARCHIVO_CONFIG)
    return pymysql.connect(charset="utf8mb4", **config)

@contextmanager
def cursor_bd():
    # ABRE Y CIERRA LA CONEXION; SI ALGO FALLA DESHACE TODO (ROLLBACK), SI NO CONFIRMA (COMMIT)
    con = conexion()
    try:
        with con.cursor() as cursor:
            yield cursor
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

def consulta(sql, parametros=None):
    with cursor_bd() as cursor:
        cursor.execute(sql, parametros)
        return cursor.fetchall()

def consulta_uno(sql, parametros=None):
    with cursor_bd() as cursor:
        cursor.execute(sql, parametros)
        return cursor.fetchone()

def ejecuta(sql, parametros=None): # DEVUELVE EL CODIGO GENERADO POR AUTO_INCREMENT (SI LO HAY)
    with cursor_bd() as cursor:
        cursor.execute(sql, parametros)
        return cursor.lastrowid

def identificador(nombre): # NOMBRE DE TABLA ENTRE COMILLAS INVERTIDAS (LOS NOMBRES NO PUEDEN IR COMO PARAMETRO %s)
    return "`" + nombre.replace("`", "``") + "`"

def respalda(ruta, fecha): # COPIA DE SEGURIDAD EN SQL, COMO mysqldump PERO SIN NECESITAR HERRAMIENTAS EXTERNAS
    # TODO SE LEE EN UNA SOLA TRANSACCION: LA COPIA ES COHERENTE AUNQUE ALGUIEN VENDA MIENTRAS TANTO
    temporal = ruta + ".tmp" # SI ALGO FALLA, NO QUEDA UN RESPALDO A MEDIAS CON EL NOMBRE FINAL
    con = conexion()
    filas = {}
    try:
        with con.cursor() as cursor, open(temporal, "w", encoding="utf-8", newline="\n") as archivo:
            cursor.execute("START TRANSACTION WITH CONSISTENT SNAPSHOT")
            cursor.execute(""" SELECT TABLE_NAME FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME """)
            tablas = [fila[0] for fila in cursor.fetchall()]
            archivo.write(f"-- Respaldo de la base de datos {config['database']}\n-- Generado el {fecha:%d/%m/%Y %H:%M} por el Sistema de Ventas\n"
                          f"-- Para restaurarlo: mysql -u root -p {config['database']} < este_archivo.sql\n\n"
                          "SET NAMES utf8mb4;\nSET FOREIGN_KEY_CHECKS = 0;\n\n")
            for tabla in tablas:
                cursor.execute("SHOW CREATE TABLE " + identificador(tabla))
                archivo.write(f"DROP TABLE IF EXISTS {identificador(tabla)};\n{cursor.fetchone()[1]};\n")
                cursor.execute("SELECT * FROM " + identificador(tabla))
                datos = cursor.fetchall()
                for inicio in range(0, len(datos), 200): # INSERTS DE A 200 FILAS
                    valores = ",\n".join("(" + ", ".join(con.literal(valor) for valor in fila) + ")" for fila in datos[inicio:inicio + 200])
                    archivo.write(f"INSERT INTO {identificador(tabla)} VALUES\n{valores};\n")
                archivo.write("\n")
                filas[tabla] = len(datos)
            archivo.write("SET FOREIGN_KEY_CHECKS = 1;\n")
        con.commit()
        os.replace(temporal, ruta)
    finally:
        con.close()
        if os.path.exists(temporal):
            os.remove(temporal)
    return filas

def siguiente_codigo(tabla): # VALOR QUE ASIGNARA EL AUTO_INCREMENT DE MYSQL
    with cursor_bd() as cursor:
        try:
            cursor.execute("SET SESSION information_schema_stats_expiry = 0") # SIN CACHE (MYSQL 8)
        except pymysql.err.MySQLError:
            pass
        cursor.execute(""" SELECT AUTO_INCREMENT FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s """, (tabla,))
        fila = cursor.fetchone()
    return str(fila[0] if fila and fila[0] else 1)
