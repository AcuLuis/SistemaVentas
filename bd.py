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
