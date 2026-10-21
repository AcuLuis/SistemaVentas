# CONTRASEÑAS: SOLO SE GUARDA UN HASH PBKDF2-SHA256 CON SAL ALEATORIA, NUNCA LA CONTRASEÑA
import hashlib
import hmac
import os

ITERACIONES = 200_000
LARGO_MINIMO = 6

def cifra_clave(clave, sal=None, iteraciones=ITERACIONES):
    sal = sal or os.urandom(16).hex()
    resumen = hashlib.pbkdf2_hmac("sha256", clave.encode("utf-8"), bytes.fromhex(sal), iteraciones).hex()
    return f"pbkdf2_sha256${iteraciones}${sal}${resumen}"

def verifica_clave(clave, guardado):
    try:
        algoritmo, iteraciones, sal, resumen = guardado.split("$")
    except (ValueError, AttributeError):
        return False
    if algoritmo != "pbkdf2_sha256":
        return False
    calculado = cifra_clave(clave, sal, int(iteraciones)).split("$")[3]
    return hmac.compare_digest(calculado, resumen) # COMPARACION EN TIEMPO CONSTANTE
