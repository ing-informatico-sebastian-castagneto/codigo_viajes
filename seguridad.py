"""
====================================================================
ASIGNATURA: Programación Orientada a Objetos Segura - INACAP
ARCHIVO: seguridad.py (Pestaña 2 en VS Code)
====================================================================
Contiene funciones de seguridad para encriptar contraseñas mediante
PBKDF2 HMAC SHA-256 con Salt aleatorio de 16 bytes (Cumple Regla R10).
"""

import os
import hashlib
import hmac


def generar_salt() -> str:
    """Genera un salt aleatorio de 16 bytes en formato hexadecimal."""
    return os.urandom(16).hex()


def hashear_password(password: str, salt_hex: str) -> str:
    """
    Encripta la contraseña usando PBKDF2 con SHA-256 y 100,000 iteraciones.
    Nunca guarda la contraseña en texto plano.
    """
    salt = bytes.fromhex(salt_hex)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return pwd_hash.hex()


def verificar_password(password: str, salt_hex: str, hash_almacenado: str) -> bool:
    """Valida si la contraseña ingresada coincide con el hash guardado."""
    return hmac.compare_digest(hashear_password(password, salt_hex), hash_almacenado)


def validar_correo(correo: str) -> bool:
    """Valida formato básico de email."""
    correo = correo.strip()
    return "@" in correo and "." in correo and len(correo) >= 5


def validar_rut(rut: str) -> bool:
    """Valida formato chileno simplificado de RUT."""
    rut_limpio = rut.replace(".", "").replace("-", "").strip()
    return len(rut_limpio) >= 7 and rut_limpio[:-1].isdigit()


def validar_telefono(telefono: str) -> bool:
    """Valida número telefónico."""
    tel_limpio = telefono.replace("+", "").replace(" ", "").strip()
    return tel_limpio.isdigit() and len(tel_limpio) >= 8
