"""
====================================================================
ASIGNATURA: Programación Orientada a Objetos Segura - INACAP
ARCHIVO: main.py (Pestaña 6 en VS Code)
====================================================================
Punto de entrada ejecutable. Ofrece un menú por consola (CLI)
y la opción de iniciar el servidor web FastAPI con Uvicorn.
"""

import uvicorn
from database import BaseDatos
from servicios import ServicioAgencia


def mostrar_menu():
    print("\n" + "="*55)
    print("   SISTEMA VIAJES AVENTURA - PROYECTO INACAP")
    print("="*55)
    print("1. Iniciar Sesión (Cliente / Admin)")
    print("2. Registrar nuevo Cliente")
    print("3. Consultar Paquetes Publicados")
    print("4. Levantar Servidor API REST (FastAPI + Swagger UI)")
    print("0. Salir")
    print("-" * 55)


def ejecutar_cli():
    db = BaseDatos()
    servicio = ServicioAgencia(db)

    while True:
        mostrar_menu()
        try:
            opc = input("Seleccione una opción: ").strip()

            if opc == "1":
                print("\n--- INICIO DE SESIÓN ---")
                correo = input("Correo: ").strip()
                clave = input("Contraseña: ").strip()
                try:
                    usuario = servicio.autenticar_usuario(correo, clave)
                    print(f"\n[+] Sesión iniciada: {usuario.nombre} ({usuario.rol})")
                except ValueError as err:
                    print(f"\n[-] Error: {err}")

            elif opc == "2":
                print("\n--- REGISTRO DE CLIENTE ---")
                rut = input("RUT: ").strip()
                correo = input("Correo: ").strip()
                nombre = input("Nombre completo: ").strip()
                telefono = input("Teléfono: ").strip()
                clave = input("Contraseña: ").strip()
                try:
                    servicio.registrar_cliente(rut, correo, clave, nombre, telefono)
                    print("\n[+] Cliente registrado exitosamente.")
                except ValueError as err:
                    print(f"\n[-] Error: {err}")

            elif opc == "3":
                paquetes = db.listar_paquetes()
                print("\n--- CATÁLOGOS DE PAQUETES ---")
                if not paquetes:
                    print("No hay paquetes publicados.")
                for p in paquetes:
                    reservadas = db.calcular_personas_reservadas(p.id_paquete)
                    disponibles = p.cupo_maximo - reservadas
                    print(
                        f"ID #{p.id_paquete} | {p.nombre} | "
                        f"Precio: ${p.precio_persona:,.0f} CLP | "
                        f"Cupo disp: {disponibles}"
                    )

            elif opc == "4":
                print("\nIniciando Servidor API REST en http://127.0.0.1:8000")
                print("Documentación Swagger UI en http://127.0.0.1:8000/docs")
                from api import app

                uvicorn.run(app, host="127.0.0.1", port=8000)

            elif opc == "0":
                print("\n¡Gracias por utilizar el sistema!")
                return

            else:
                print("\n[-] Opción no válida. Seleccione una opción entre 0 y 4.")
        except (EOFError, KeyboardInterrupt):
            print("\n\n¡Gracias por utilizar el sistema!")
            return


if __name__ == "__main__":
    ejecutar_cli()
