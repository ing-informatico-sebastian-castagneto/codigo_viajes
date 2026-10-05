"""
====================================================================
ASIGNATURA: Programación Orientada a Objetos Segura - INACAP
ARCHIVO: database.py (Pestaña 3 en VS Code)
====================================================================
Maneja la base de datos SQLite3 con consultas parametrizadas (?)
para prevenir ataques de Inyección SQL.
"""

import sqlite3
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, List, Optional
from modelos import Usuario, Destino, Paquete, Reserva
from seguridad import generar_salt, hashear_password


class BaseDatos:
    def __init__(self, db_name: Optional[str] = None):
        if db_name is None:
            db_name = os.environ.get(
                "VIAJES_DB_PATH",
                str(Path(__file__).resolve().with_name("viajes_aventura.db"))
            )
        self.db_name = db_name
        self.inicializar_tablas()

    @contextmanager
    def obtener_conexion(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_name, timeout=10)
        try:
            conn.execute("PRAGMA foreign_keys = ON;")
            with conn:
                yield conn
        finally:
            conn.close()

    def inicializar_tablas(self):
        with self.obtener_conexion() as conn:
            cursor = conn.cursor()
            
            # Tabla Usuarios
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
                rut TEXT UNIQUE NOT NULL,
                correo TEXT UNIQUE NOT NULL,
                clave_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                nombre TEXT NOT NULL,
                telefono TEXT NOT NULL,
                rol TEXT NOT NULL DEFAULT 'cliente'
            );
            """)

            # Tabla Destinos
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS destinos (
                id_destino INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                zona TEXT NOT NULL,
                descripcion TEXT,
                duracion_dias INTEGER NOT NULL DEFAULT 1,
                costo_base REAL NOT NULL,
                disponible INTEGER NOT NULL DEFAULT 1
            );
            """)

            # Tabla Paquetes
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS paquetes (
                id_paquete INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                cupo_maximo INTEGER NOT NULL,
                fecha_salida TEXT NOT NULL,
                fecha_regreso TEXT NOT NULL,
                margen_operacion REAL NOT NULL DEFAULT 20.0,
                precio_persona REAL NOT NULL
            );
            """)

            # Tabla Intermedia Paquete-Destino (N:M)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS paquete_destino (
                id_paquete INTEGER NOT NULL,
                id_destino INTEGER NOT NULL,
                PRIMARY KEY (id_paquete, id_destino),
                FOREIGN KEY (id_paquete) REFERENCES paquetes(id_paquete) ON DELETE CASCADE,
                FOREIGN KEY (id_destino) REFERENCES destinos(id_destino)
            );
            """)

            # Tabla Reservas
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS reservas (
                id_reserva INTEGER PRIMARY KEY AUTOINCREMENT,
                id_usuario INTEGER NOT NULL,
                id_paquete INTEGER NOT NULL,
                fecha_emision TEXT NOT NULL,
                cantidad_personas INTEGER NOT NULL,
                total_cobrado REAL NOT NULL,
                FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario),
                FOREIGN KEY (id_paquete) REFERENCES paquetes(id_paquete)
            );
            """)
            conn.commit()

        self._crear_admin_defecto()

    def _crear_admin_defecto(self):
        """Crea el usuario administrador inicial si no existe."""
        with self.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE rol = 'admin'")
            if cursor.fetchone()[0] == 0:
                salt = generar_salt()
                clave_hash = hashear_password("admin123", salt)
                cursor.execute(
                    "INSERT INTO usuarios (rut, correo, clave_hash, salt, nombre, telefono, rol) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    ("11111111-1", "admin@viajesaventura.cl", clave_hash, salt, "Paulina Ovalle (Socia Admin)", "+56912345678", "admin")
                )
                conn.commit()

    # --- USUARIOS ---
    def registrar_usuario(self, rut: str, correo: str, password: str, nombre: str, telefono: str, rol: str = 'cliente') -> int:
        salt = generar_salt()
        clave_hash = hashear_password(password, salt)
        with self.obtener_conexion() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO usuarios (rut, correo, clave_hash, salt, nombre, telefono, rol) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (rut, correo, clave_hash, salt, nombre, telefono, rol)
                )
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError as e:
                err_msg = str(e).lower()
                if "correo" in err_msg:
                    raise ValueError("El correo electrónico ya se encuentra registrado.")
                elif "rut" in err_msg:
                    raise ValueError("El RUT ya se encuentra registrado.")
                else:
                    raise ValueError("Error al registrar usuario en la base de datos.")

    def obtener_usuario_por_correo(self, correo: str) -> Optional[Usuario]:
        with self.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id_usuario, rut, correo, clave_hash, salt, nombre, telefono, rol FROM usuarios WHERE correo = ?", (correo,))
            f = cursor.fetchone()
            return Usuario(f[0], f[1], f[2], f[3], f[4], f[5], f[6], f[7]) if f else None

    def obtener_usuario_por_id(self, id_usuario: int) -> Optional[Usuario]:
        with self.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id_usuario, rut, correo, clave_hash, salt, nombre, telefono, rol FROM usuarios WHERE id_usuario = ?", (id_usuario,))
            f = cursor.fetchone()
            return Usuario(f[0], f[1], f[2], f[3], f[4], f[5], f[6], f[7]) if f else None

    # --- DESTINOS ---
    def guardar_destino(self, nombre: str, zona: str, descripcion: str, duracion_dias: int, costo_base: float) -> int:
        with self.obtener_conexion() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO destinos (nombre, zona, descripcion, duracion_dias, costo_base, disponible) VALUES (?, ?, ?, ?, ?, 1)",
                    (nombre, zona, descripcion, duracion_dias, costo_base)
                )
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                raise ValueError("Regla R1: Ya existe un destino registrado con ese nombre.")

    def listar_destinos(self, solo_disponibles: bool = True) -> List[Destino]:
        with self.obtener_conexion() as conn:
            cursor = conn.cursor()
            query = "SELECT id_destino, nombre, zona, descripcion, duracion_dias, costo_base, disponible FROM destinos WHERE disponible = 1" if solo_disponibles else "SELECT id_destino, nombre, zona, descripcion, duracion_dias, costo_base, disponible FROM destinos"
            cursor.execute(query)
            return [Destino(f[0], f[1], f[2], f[3], f[4], f[5], bool(f[6])) for f in cursor.fetchall()]

    def obtener_destino_por_id(self, id_destino: int) -> Optional[Destino]:
        with self.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id_destino, nombre, zona, descripcion, duracion_dias, costo_base, disponible FROM destinos WHERE id_destino = ?", (id_destino,))
            f = cursor.fetchone()
            return Destino(f[0], f[1], f[2], f[3], f[4], f[5], bool(f[6])) if f else None

    def actualizar_destino(self, id_destino: int, nombre: str, zona: str, descripcion: str, duracion_dias: int, costo_base: float):
        with self.obtener_conexion() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "UPDATE destinos SET nombre = ?, zona = ?, descripcion = ?, duracion_dias = ?, costo_base = ? WHERE id_destino = ?",
                    (nombre, zona, descripcion, duracion_dias, costo_base, id_destino)
                )
            except sqlite3.IntegrityError as err:
                if "nombre" in str(err).lower():
                    raise ValueError("Regla R1: Ya existe un destino registrado con ese nombre.") from err
                raise
            conn.commit()

    def eliminar_o_desactivar_destino(self, id_destino: int) -> bool:
        """Regla R8: Borrado físico si no tiene paquetes, borrado lógico si pertenece a alguno."""
        with self.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM paquete_destino WHERE id_destino = ?", (id_destino,))
            en_uso = cursor.fetchone()[0] > 0

            if en_uso:
                cursor.execute("UPDATE destinos SET disponible = 0 WHERE id_destino = ?", (id_destino,))
                conn.commit()
                return False
            else:
                cursor.execute("DELETE FROM destinos WHERE id_destino = ?", (id_destino,))
                conn.commit()
                return True

    # --- PAQUETES ---
    def guardar_paquete(self, nombre: str, cupo_maximo: int, fecha_salida: str, fecha_regreso: str, margen_operacion: float, precio_persona: float, lista_id_destinos: List[int]) -> int:
        with self.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO paquetes (nombre, cupo_maximo, fecha_salida, fecha_regreso, margen_operacion, precio_persona) VALUES (?, ?, ?, ?, ?, ?)",
                (nombre, cupo_maximo, fecha_salida, fecha_regreso, margen_operacion, precio_persona)
            )
            id_paquete = cursor.lastrowid
            for id_dest in lista_id_destinos:
                cursor.execute("INSERT INTO paquete_destino (id_paquete, id_destino) VALUES (?, ?)", (id_paquete, id_dest))
            conn.commit()
            return id_paquete

    def listar_paquetes(self) -> List[Paquete]:
        with self.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id_paquete, nombre, cupo_maximo, fecha_salida, fecha_regreso, margen_operacion, precio_persona FROM paquetes")
            filas = cursor.fetchall()
            paquetes = []
            for fp in filas:
                id_p, nombre, cupo_max, f_salida, f_regreso, margen, precio = fp
                cursor.execute("""
                    SELECT d.id_destino, d.nombre, d.zona, d.descripcion, d.duracion_dias, d.costo_base, d.disponible 
                    FROM destinos d JOIN paquete_destino pd ON d.id_destino = pd.id_destino WHERE pd.id_paquete = ?
                """, (id_p,))
                destinos = [Destino(df[0], df[1], df[2], df[3], df[4], df[5], bool(df[6])) for df in cursor.fetchall()]
                paquetes.append(Paquete(id_p, nombre, cupo_max, f_salida, f_regreso, margen, precio, destinos))
            return paquetes

    def obtener_paquete_por_id(self, id_paquete: int) -> Optional[Paquete]:
        with self.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id_paquete, nombre, cupo_maximo, fecha_salida, fecha_regreso, margen_operacion, precio_persona FROM paquetes WHERE id_paquete = ?", (id_paquete,))
            fp = cursor.fetchone()
            if not fp:
                return None
            id_p, nombre, cupo_max, f_salida, f_regreso, margen, precio = fp
            cursor.execute("""
                SELECT d.id_destino, d.nombre, d.zona, d.descripcion, d.duracion_dias, d.costo_base, d.disponible 
                FROM destinos d JOIN paquete_destino pd ON d.id_destino = pd.id_destino WHERE pd.id_paquete = ?
            """, (id_p,))
            destinos = [Destino(df[0], df[1], df[2], df[3], df[4], df[5], bool(df[6])) for df in cursor.fetchall()]
            return Paquete(id_p, nombre, cupo_max, f_salida, f_regreso, margen, precio, destinos)

    def calcular_personas_reservadas(self, id_paquete: int) -> int:
        """Regla R14: Suma las personas acumuladas en las reservas del paquete."""
        with self.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COALESCE(SUM(cantidad_personas), 0) FROM reservas WHERE id_paquete = ?", (id_paquete,))
            return cursor.fetchone()[0]

    def obtener_indicadores(self) -> dict:
        """Devuelve totales agregados para el panel de indicadores de la API."""
        with self.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*),
                       COALESCE(SUM(CASE WHEN disponible = 1 THEN 1 ELSE 0 END), 0),
                       COALESCE(SUM(CASE WHEN disponible = 0 THEN 1 ELSE 0 END), 0)
                FROM destinos
            """)
            total_destinos, destinos_disponibles, destinos_no_disponibles = cursor.fetchone()

            cursor.execute("SELECT COUNT(*), COALESCE(SUM(cupo_maximo), 0) FROM paquetes")
            total_paquetes, cupos_totales = cursor.fetchone()

            cursor.execute("""
                SELECT COUNT(*), COALESCE(SUM(cantidad_personas), 0),
                       COALESCE(SUM(total_cobrado), 0)
                FROM reservas
            """)
            total_reservas, personas_reservadas, ingresos_clp = cursor.fetchone()

            return {
                "destinos": {
                    "total": total_destinos,
                    "disponibles": destinos_disponibles,
                    "no_disponibles": destinos_no_disponibles,
                },
                "paquetes": {
                    "total": total_paquetes,
                    "cupos_totales": cupos_totales,
                },
                "reservas": {
                    "total": total_reservas,
                    "personas": personas_reservadas,
                    "ingresos_clp": ingresos_clp,
                },
                "ocupacion": {
                    "cupos_ocupados": personas_reservadas,
                    "cupos_disponibles": cupos_totales - personas_reservadas,
                    "porcentaje": round(personas_reservadas / cupos_totales * 100, 2)
                    if cupos_totales else 0,
                },
            }

    # --- RESERVAS ---
    def guardar_reserva(self, id_usuario: int, id_paquete: int, cantidad_personas: int, total_cobrado: float, fecha_emision: str) -> int:
        with self.obtener_conexion() as conn:
            if cantidad_personas < 1:
                raise ValueError("La cantidad de personas reservadas debe ser al menos 1.")

            conn.execute("BEGIN IMMEDIATE")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.cupo_maximo, COALESCE(SUM(r.cantidad_personas), 0)
                FROM paquetes p
                LEFT JOIN reservas r ON r.id_paquete = p.id_paquete
                WHERE p.id_paquete = ?
                GROUP BY p.id_paquete
            """, (id_paquete,))
            fila = cursor.fetchone()
            if not fila:
                raise ValueError("El paquete seleccionado no existe.")

            cupo_disponible = fila[0] - fila[1]
            if cantidad_personas > cupo_disponible:
                raise ValueError(
                    f"Regla R14: Reserva rechazada. Cupo disponible excedido "
                    f"({cupo_disponible} cupos restantes)."
                )

            cursor.execute(
                "INSERT INTO reservas (id_usuario, id_paquete, fecha_emision, cantidad_personas, total_cobrado) VALUES (?, ?, ?, ?, ?)",
                (id_usuario, id_paquete, fecha_emision, cantidad_personas, total_cobrado)
            )
            conn.commit()
            return cursor.lastrowid

    def obtener_reservas_usuario(self, id_usuario: int) -> List[Reserva]:
        with self.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT r.id_reserva, r.id_usuario, r.id_paquete, r.fecha_emision, r.cantidad_personas, r.total_cobrado, p.nombre
                FROM reservas r JOIN paquetes p ON r.id_paquete = p.id_paquete
                WHERE r.id_usuario = ? ORDER BY r.id_reserva DESC
            """, (id_usuario,))
            return [Reserva(f[0], f[1], f[2], f[3], f[4], f[5], f[6]) for f in cursor.fetchall()]
