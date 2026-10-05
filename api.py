"""
====================================================================
ASIGNATURA: Programación Orientada a Objetos Segura - INACAP
ARCHIVO: api.py (Pestaña 5 en VS Code)
====================================================================
API REST construida con FastAPI. Permite gestionar destinos,
paquetes y reservas mediante peticiones HTTP (GET, POST, PUT, DELETE).
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from database import BaseDatos
from servicios import ServicioAgencia
from modelos import (
    RegistroClienteSchema, LoginSchema,
    DestinoSchema, PaqueteSchema, ReservaSchema
)

db = BaseDatos()
servicio = ServicioAgencia(db)

app = FastAPI(
    title="API REST - Viajes Aventura INACAP",
    description="API RESTful desarrollada para la agencia Viajes Aventura.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Inicio"])
def inicio():
    return {
        "mensaje": "Bienvenido a la API REST de Viajes Aventura - INACAP",
        "documentacion_swagger": "/docs",
        "estado": "OK"
    }


# --- AUTENTICACIÓN Y REGISTRO ---
@app.post("/api/auth/registro", status_code=status.HTTP_201_CREATED, tags=["Autenticación"])
def registrar_cliente(datos: RegistroClienteSchema):
    try:
        id_usuario = servicio.registrar_cliente(
            rut=datos.rut,
            correo=datos.correo,
            password=datos.password,
            nombre=datos.nombre,
            telefono=datos.telefono
        )
        return {"mensaje": "Cliente registrado exitosamente.", "id_usuario": id_usuario}
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))

@app.post("/api/auth/login", tags=["Autenticación"])
def iniciar_sesion(datos: LoginSchema):
    try:
        usuario = servicio.autenticar_usuario(datos.correo, datos.password)
        return {"mensaje": f"Autenticación exitosa. Bienvenido/a {usuario.nombre}.", "usuario": usuario.a_diccionario()}
    except ValueError as err:
        raise HTTPException(status_code=401, detail=str(err))


# --- ENDPOINTS DESTINOS ---
@app.get("/api/destinos", tags=["Destinos"])
def listar_destinos(solo_disponibles: bool = True):
    destinos = db.listar_destinos(solo_disponibles=solo_disponibles)
    return [d.a_diccionario() for d in destinos]


@app.post("/api/destinos", status_code=status.HTTP_201_CREATED, tags=["Destinos"])
def crear_destino(datos: DestinoSchema):
    try:
        id_destino = servicio.registrar_destino(
            nombre=datos.nombre, zona=datos.zona, descripcion=datos.descripcion,
            duracion_dias=datos.duracion_dias, costo_base=datos.costo_base
        )
        return {"mensaje": f"Destino '{datos.nombre}' registrado con éxito.", "id_destino": id_destino}
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@app.put("/api/destinos/{id_destino}", tags=["Destinos"])
def modificar_destino(id_destino: int, datos: DestinoSchema):
    try:
        servicio.modificar_destino(
            id_destino=id_destino, nombre=datos.nombre, zona=datos.zona,
            descripcion=datos.descripcion, duracion_dias=datos.duracion_dias, costo_base=datos.costo_base
        )
        return {"mensaje": f"Destino ID #{id_destino} modificado correctamente."}
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@app.delete("/api/destinos/{id_destino}", tags=["Destinos"])
def eliminar_destino(id_destino: int):
    try:
        msg = servicio.eliminar_destino(id_destino)
        return {"resultado": msg}
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


# --- ENDPOINTS PAQUETES ---
@app.get("/api/paquetes", tags=["Paquetes"])
def listar_paquetes():
    paquetes = db.listar_paquetes()
    resultado = []
    for p in paquetes:
        res_count = db.calcular_personas_reservadas(p.id_paquete)
        cupo_disp = p.cupo_maximo - res_count
        resultado.append(p.a_diccionario(cupo_disponible=cupo_disp))
    return resultado


@app.post("/api/paquetes", status_code=status.HTTP_201_CREATED, tags=["Paquetes"])
def crear_paquete(datos: PaqueteSchema):
    try:
        id_paquete = servicio.crear_paquete(
            nombre=datos.nombre, cupo_maximo=datos.cupo_maximo,
            fecha_salida=datos.fecha_salida, fecha_regreso=datos.fecha_regreso,
            margen_operacion=datos.margen_operacion, id_destinos=datos.id_destinos
        )
        paq = db.obtener_paquete_por_id(id_paquete)
        if paq is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="El paquete se creó, pero no se pudo recuperar desde la base de datos."
            )
        return {
            "mensaje": f"Paquete '{datos.nombre}' publicado con éxito.",
            "id_paquete": id_paquete,
            "precio_persona_fijado": paq.precio_persona
        }
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


# --- ENDPOINTS RESERVAS ---
@app.post("/api/reservas", status_code=status.HTTP_201_CREATED, tags=["Reservas"])
def realizar_reserva(datos: ReservaSchema):
    try:
        id_reserva, total_cobrado = servicio.realizar_reserva(
            id_usuario=datos.id_usuario, id_paquete=datos.id_paquete, cantidad_personas=datos.cantidad_personas
        )
        return {
            "mensaje": f"¡Reserva #{id_reserva} confirmada!",
            "id_reserva": id_reserva,
            "total_cobrado_clp": total_cobrado
        }
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@app.get("/api/reservas/usuario/{id_usuario}", tags=["Reservas"])
def obtener_reservas_cliente(id_usuario: int):
    reservas = db.obtener_reservas_usuario(id_usuario)
    return [r.a_diccionario() for r in reservas]


@app.get("/api/indicadores", tags=["Indicadores"])
def obtener_indicadores():
    return db.obtener_indicadores()
