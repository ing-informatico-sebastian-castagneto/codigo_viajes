"""
====================================================================
ASIGNATURA: Programación Orientada a Objetos Segura - INACAP
ARCHIVO: servicios.py (Pestaña 4 en VS Code)
====================================================================
Contiene la lógica de negocio y validación de reglas R1 a R17.
"""

from datetime import datetime
from typing import List, Tuple
from seguridad import verificar_password, validar_correo, validar_rut, validar_telefono
from modelos import Usuario, Paquete


class ServicioAgencia:
    def __init__(self, db):
        self.db = db

    def autenticar_usuario(self, correo: str, password: str) -> Usuario:
        correo = correo.strip()
        if not validar_correo(correo):
            raise ValueError("El formato de correo no es válido.")
        
        usuario = self.db.obtener_usuario_por_correo(correo)
        if not usuario or not verificar_password(password, usuario.salt, usuario.clave_hash):
            raise ValueError("Credenciales incorrectas. Verifique usuario y contraseña.")
        
        return usuario

    def registrar_cliente(self, rut: str, correo: str, password: str, nombre: str, telefono: str) -> int:
        if not validar_rut(rut):
            raise ValueError("El RUT ingresado no tiene un formato válido.")
        if not validar_correo(correo):
            raise ValueError("El correo electrónico no es válido.")
        if not validar_telefono(telefono):
            raise ValueError("El número de teléfono debe contener solo dígitos.")
        if len(password) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres.")
        if not nombre.strip():
            raise ValueError("El nombre del cliente es obligatorio.")
        
        return self.db.registrar_usuario(
            rut.strip(), correo.strip(), password, nombre.strip(), telefono.strip(), rol='cliente'
        )

    def registrar_destino(self, nombre: str, zona: str, descripcion: str, duracion_dias: int, costo_base: float) -> int:
        if not nombre.strip():
            raise ValueError("El nombre del destino no puede estar vacío.")
        if duracion_dias <= 0:
            raise ValueError("La duración del viaje debe ser de al menos 1 día.")
        if costo_base <= 0:
            raise ValueError("Regla R2: El costo base debe ser un monto positivo mayor a 0.")
        
        return self.db.guardar_destino(
            nombre.strip(), zona.strip(), descripcion.strip(), duracion_dias, costo_base
        )

    def modificar_destino(self, id_destino: int, nombre: str, zona: str, descripcion: str, duracion_dias: int, costo_base: float):
        destino = self.db.obtener_destino_por_id(id_destino)
        if not destino:
            raise ValueError("El destino seleccionado no existe.")
        destino.actualizar_datos(nombre, zona, descripcion, duracion_dias, costo_base)
        self.db.actualizar_destino(
            id_destino, destino.nombre, destino.zona, destino.descripcion, destino.duracion_dias, destino.costo_base
        )

    def eliminar_destino(self, id_destino: int) -> str:
        destino = self.db.obtener_destino_por_id(id_destino)
        if not destino:
            raise ValueError("El destino a eliminar no existe.")
        
        fue_eliminado_fisicamente = self.db.eliminar_o_desactivar_destino(id_destino)
        if fue_eliminado_fisicamente:
            return f"El destino '{destino.nombre}' fue eliminado del catálogo."
        else:
            return f"El destino '{destino.nombre}' está asociado a paquetes existentes. Se ha marcado como 'No disponible' para preservar el historial (Regla R8)."

    def crear_paquete(self, nombre: str, cupo_maximo: int, fecha_salida: str, fecha_regreso: str, margen_operacion: float, id_destinos: List[int]) -> int:
        if not nombre.strip():
            raise ValueError("El nombre del paquete es obligatorio.")
        if cupo_maximo <= 0:
            raise ValueError("Regla R5: El cupo máximo debe ser mayor a 0.")
        if margen_operacion < 0:
            raise ValueError("Regla R6: El margen de operación no puede ser negativo.")
        
        try:
            f_sal = datetime.strptime(fecha_salida.strip(), "%Y-%m-%d").date()
            f_reg = datetime.strptime(fecha_regreso.strip(), "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Las fechas deben tener el formato AAAA-MM-DD (ejemplo: 2026-11-15).")
        
        if f_reg <= f_sal:
            raise ValueError("Regla R5: La fecha de regreso debe ser posterior a la fecha de salida.")
        
        if len(id_destinos) < 2 or len(id_destinos) > 5:
            raise ValueError("Regla R3: Un paquete turístico debe combinar entre 2 y 5 destinos.")
        
        if len(set(id_destinos)) != len(id_destinos):
            raise ValueError("Regla R3: No se pueden repetir destinos dentro del mismo paquete.")
        
        destinos_objetos = []
        for id_d in id_destinos:
            d = self.db.obtener_destino_por_id(id_d)
            if not d or not d.disponible:
                raise ValueError(f"El destino ID {id_d} no existe o está marcado como 'No disponible'.")
            destinos_objetos.append(d)

        precio_persona = Paquete.calcular_precio_publicacion(destinos_objetos, margen_operacion)

        return self.db.guardar_paquete(
            nombre.strip(), cupo_maximo, fecha_salida.strip(), fecha_regreso.strip(),
            margen_operacion, precio_persona, id_destinos
        )

    def realizar_reserva(self, id_usuario: int, id_paquete: int, cantidad_personas: int) -> Tuple[int, float]:
        if cantidad_personas < 1:
            raise ValueError("Regla R16: La cantidad de personas reservadas debe ser al menos 1.")
        
        usuario = self.db.obtener_usuario_por_id(id_usuario)
        if not usuario:
            raise ValueError("El usuario ingresado no existe.")

        paquete = self.db.obtener_paquete_por_id(id_paquete)
        if not paquete:
            raise ValueError("El paquete seleccionado no existe.")
        
        fecha_salida_dt = datetime.strptime(paquete.fecha_salida, "%Y-%m-%d").date()
        if fecha_salida_dt < datetime.now().date():
            raise ValueError("Regla R15: No se aceptan reservas para paquetes cuya fecha de salida ya ha transcurrido.")

        personas_reservadas = self.db.calcular_personas_reservadas(id_paquete)
        cupo_disponible = paquete.cupo_maximo - personas_reservadas

        if cantidad_personas > cupo_disponible:
            raise ValueError(f"Regla R14: Reserva rechazada. Cupo disponible excedido ({cupo_disponible} cupos restantes).")

        total_cobrado = paquete.precio_persona * cantidad_personas
        fecha_emision = datetime.now().strftime("%Y-%m-%d %H:%M")

        id_reserva = self.db.guardar_reserva(
            usuario.id_usuario, id_paquete, cantidad_personas, total_cobrado, fecha_emision
        )
        return id_reserva, total_cobrado
