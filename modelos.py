"""
====================================================================
ASIGNATURA: Programación Orientada a Objetos Segura - INACAP
PROYECTO: Sistema de Gestión de Viajes y Reservas "Viajes Aventura"
ARCHIVO: modelos.py (Pestaña 1 en VS Code)
====================================================================
Este archivo define las clases principales del sistema aplicando POO:
- Abstracción
- Encapsulamiento
- Herencia
- Polimorfismo
"""

from pydantic import BaseModel, Field
from typing import List, Optional


# ------------------------------------------------------------------
# CLASES BASE Y DOMINIO (POO)
# ------------------------------------------------------------------

class Persona:
    """Clase base que representa a una persona genérica en el sistema."""
    def __init__(self, rut: str, nombre: str, correo: str, telefono: str):
        self._rut = rut
        self._nombre = nombre
        self._correo = correo
        self._telefono = telefono

    @property
    def rut(self):
        return self._rut

    @property
    def nombre(self):
        return self._nombre

    @property
    def correo(self):
        return self._correo

    @property
    def telefono(self):
        return self._telefono


class Usuario(Persona):
    """
    Clase Usuario que hereda de Persona.
    Maneja el rol (admin o cliente) y las credenciales de acceso.
    """
    def __init__(self, id_usuario: int, rut: str, correo: str, clave_hash: str, salt: str, nombre: str, telefono: str, rol: str = 'cliente'):
        super().__init__(rut, nombre, correo, telefono)
        self.id_usuario = id_usuario
        self.clave_hash = clave_hash
        self.salt = salt
        self.rol = rol

    def es_admin(self) -> bool:
        return self.rol == 'admin'

    def a_diccionario(self) -> dict:
        return {
            "id_usuario": self.id_usuario,
            "rut": self.rut,
            "correo": self.correo,
            "nombre": self.nombre,
            "telefono": self.telefono,
            "rol": self.rol
        }


class Destino:
    """Clase que representa un destino turístico (Reglas R1 y R2)."""
    def __init__(self, id_destino: int, nombre: str, zona: str, descripcion: str, duracion_dias: int, costo_base: float, disponible: bool = True):
        self.id_destino = id_destino
        self.nombre = nombre
        self.zona = zona
        self.descripcion = descripcion
        self.duracion_dias = int(duracion_dias)
        self.costo_base = float(costo_base)
        self.disponible = bool(disponible)

    def actualizar_datos(self, nombre: str, zona: str, descripcion: str, duracion_dias: int, costo_base: float):
        if costo_base <= 0:
            raise ValueError("Regla R2: El costo base del destino debe ser mayor a 0.")
        if duracion_dias <= 0:
            raise ValueError("La duración en días debe ser al menos 1 día.")
        self.nombre = nombre.strip()
        self.zona = zona.strip()
        self.descripcion = descripcion.strip()
        self.duracion_dias = int(duracion_dias)
        self.costo_base = float(costo_base)

    def a_diccionario(self) -> dict:
        return {
            "id_destino": self.id_destino,
            "nombre": self.nombre,
            "zona": self.zona,
            "descripcion": self.descripcion,
            "duracion_dias": self.duracion_dias,
            "costo_base": self.costo_base,
            "disponible": self.disponible
        }


class Paquete:
    """Clase que representa un paquete de viajes compuesto por varios destinos (Reglas R3 a R7)."""
    def __init__(self, id_paquete: int, nombre: str, cupo_maximo: int, fecha_salida: str, fecha_regreso: str, margen_operacion: float, precio_persona: float, destinos: Optional[List[Destino]] = None):
        self.id_paquete = id_paquete
        self.nombre = nombre
        self.cupo_maximo = int(cupo_maximo)
        self.fecha_salida = fecha_salida
        self.fecha_regreso = fecha_regreso
        self.margen_operacion = float(margen_operacion)
        self.precio_persona = float(precio_persona)
        self.destinos = destinos if destinos is not None else []

    @staticmethod
    def calcular_precio_publicacion(destinos: List[Destino], margen_porcentaje: float) -> float:
        """Regla R6: Suma de costos base de destinos + margen de ganancia."""
        costo_total = sum(d.costo_base for d in destinos)
        precio_final = costo_total * (1.0 + (margen_porcentaje / 100.0))
        return round(precio_final, 2)

    def a_diccionario(self, cupo_disponible: Optional[int] = None) -> dict:
        return {
            "id_paquete": self.id_paquete,
            "nombre": self.nombre,
            "cupo_maximo": self.cupo_maximo,
            "cupo_disponible": cupo_disponible if cupo_disponible is not None else self.cupo_maximo,
            "fecha_salida": self.fecha_salida,
            "fecha_regreso": self.fecha_regreso,
            "margen_operacion_porcentaje": self.margen_operacion,
            "precio_persona": self.precio_persona,
            "destinos": [d.a_diccionario() for d in self.destinos]
        }


class Reserva:
    """Clase que representa una reserva realizada por un cliente (Reglas R12 a R16)."""
    def __init__(self, id_reserva: int, id_usuario: int, id_paquete: int, fecha_emision: str, cantidad_personas: int, total_cobrado: float, nombre_paquete: Optional[str] = None):
        self.id_reserva = id_reserva
        self.id_usuario = id_usuario
        self.id_paquete = id_paquete
        self.fecha_emision = fecha_emision
        self.cantidad_personas = int(cantidad_personas)
        self.total_cobrado = float(total_cobrado)
        self.nombre_paquete = nombre_paquete

    def a_diccionario(self) -> dict:
        return {
            "id_reserva": self.id_reserva,
            "id_usuario": self.id_usuario,
            "id_paquete": self.id_paquete,
            "nombre_paquete": self.nombre_paquete,
            "fecha_emision": self.fecha_emision,
            "cantidad_personas": self.cantidad_personas,
            "total_cobrado": self.total_cobrado
        }


# ------------------------------------------------------------------
# ESQUEMAS PYDANTIC (Validación de la API REST)
# ------------------------------------------------------------------

class RegistroClienteSchema(BaseModel):
    rut: str = Field(..., example="12345678-9")
    correo: str = Field(..., example="estudiante@inacapmail.cl")
    nombre: str = Field(..., example="Juan Pérez")
    telefono: str = Field(..., example="987654321")
    password: str = Field(..., min_length=6, example="clave123")

class LoginSchema(BaseModel):
    correo: str = Field(..., example="estudiante@inacapmail.cl")
    password: str = Field(..., example="clave123")

class DestinoSchema(BaseModel):
    nombre: str = Field(..., example="Torres del Paine")
    zona: str = Field(..., example="Patagonia Chilena")
    descripcion: str = Field(..., example="Parque Nacional")
    duracion_dias: int = Field(..., gt=0, example=5)
    costo_base: float = Field(..., gt=0, example=250000.0)

class PaqueteSchema(BaseModel):
    nombre: str = Field(..., example="Gran Tour Patagonia")
    cupo_maximo: int = Field(..., gt=0, example=10)
    fecha_salida: str = Field(..., example="2026-11-01")
    fecha_regreso: str = Field(..., example="2026-11-10")
    margen_operacion: float = Field(..., ge=0, example=20.0)
    id_destinos: List[int] = Field(..., min_items=2, max_items=5, example=[1, 2])

class ReservaSchema(BaseModel):
    id_usuario: int = Field(..., example=2)
    id_paquete: int = Field(..., example=1)
    cantidad_personas: int = Field(..., gt=0, example=2)
