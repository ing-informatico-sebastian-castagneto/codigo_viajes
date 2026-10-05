# Viajes Aventura

Proyecto académico de gestión de viajes, destinos, paquetes turísticos y reservas, desarrollado para la asignatura **Programación Orientada a Objetos Segura** de INACAP.

El proyecto contiene dos partes:

- Una API REST en Python con FastAPI y base de datos SQLite.
- Una página web adaptable a móviles que presenta los viajes y se comunica con la API.

## Funcionalidades

- Registrar e iniciar sesión de clientes.
- Validar datos básicos de RUT, correo electrónico y teléfono.
- Crear, consultar, modificar y eliminar destinos.
- Crear paquetes turísticos combinando destinos.
- Calcular el precio por persona usando el costo de los destinos y el margen de operación.
- Registrar reservas, verificar los cupos y consultar las reservas de un cliente.
- Consultar indicadores de destinos, paquetes, reservas, ocupación e ingresos.
- Buscar paquetes desde la interfaz web y enviar reservas a la API.
- Explorar los endpoints de la API mediante Swagger UI.

## Tecnologías

- **Backend:** Python, FastAPI, Uvicorn y Pydantic.
- **Persistencia:** SQLite, incluido en la biblioteca estándar de Python.
- **Seguridad de contraseñas:** PBKDF2-HMAC-SHA256 con salt aleatorio y comparación segura.
- **Frontend:** HTML, CSS y JavaScript, sin un proceso de compilación.
- **Alojamiento web:** Vercel puede servir la página estática; el backend debe alojarse por separado.

## Archivos del proyecto

| Archivo | Responsabilidad |
| --- | --- |
| `index.html` | Estructura de la página web: portada, indicadores, paquetes, destinos, conexión con la API y formulario de reserva. |
| `styles.css` | Estilos, colores, tarjetas, diseño adaptable a pantallas pequeñas y componentes de la interfaz. |
| `app.js` | Carga los datos de la API, dibuja paquetes y destinos, filtra resultados, muestra indicadores y envía reservas. |
| `api.py` | Define la aplicación FastAPI, los endpoints HTTP, los esquemas de entrada y las respuestas. |
| `database.py` | Inicializa SQLite y realiza operaciones de persistencia usando consultas parametrizadas. |
| `modelos.py` | Clases del dominio —persona, usuario, destino, paquete y reserva— y esquemas Pydantic para validar peticiones. |
| `servicios.py` | Reglas de negocio para autenticación, clientes, destinos, paquetes y reservas. |
| `seguridad.py` | Hash de contraseñas, generación de salt y validaciones básicas de RUT, correo y teléfono. |
| `main.py` | Menú de consola para iniciar sesión, registrar clientes, revisar paquetes e iniciar el servidor web. |
| `requirements.txt` | Dependencias externas de Python. |
| `.gitignore` | Excluye el entorno virtual, archivos temporales de Python y la base de datos local. |

## Organización y conceptos de POO

`modelos.py` separa los objetos del dominio. `Usuario` hereda de `Persona`; los modelos convierten sus datos a diccionarios para responder a la API. `Paquete` reúne destinos y calcula el precio de publicación a partir de sus costos y del porcentaje de operación.

`servicios.py` coordina los modelos y el acceso a datos para aplicar las reglas antes de guardar cambios. `database.py` centraliza la conexión SQLite, crea las tablas y contiene las consultas. `api.py` recibe y valida peticiones, llama a los servicios o a la base de datos y devuelve respuestas HTTP.

## Requisitos

- Python instalado (se recomienda Python 3.10 o posterior).
- `pip`, incluido normalmente con Python.
- Conexión a internet para cargar las fotografías y las fuentes externas de la página.

## Instalación y ejecución en Windows

Abre PowerShell en la carpeta del proyecto y ejecuta:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Puedes iniciar la API de estas dos formas:

### Opción A: menú de consola

```powershell
python main.py
```

Selecciona la opción **4** para iniciar FastAPI.

### Opción B: iniciar Uvicorn directamente

```powershell
python -m uvicorn api:app --reload
```

La API queda disponible normalmente en `http://127.0.0.1:8000`. La documentación interactiva de Swagger UI está en `http://127.0.0.1:8000/docs`.

Al inicializar la base de datos, el programa crea las tablas que falten. Si no encuentra un administrador, el código genera una cuenta inicial de demostración: `admin@viajesaventura.cl` con contraseña `admin123`.

## Endpoints de la API

| Método | Ruta | Descripción |
| --- | --- | --- |
| `GET` | `/` | Mensaje de bienvenida y enlace a Swagger UI. |
| `POST` | `/api/auth/registro` | Registra un cliente. Recibe RUT, correo, nombre, teléfono y contraseña. |
| `POST` | `/api/auth/login` | Comprueba las credenciales de un usuario. |
| `GET` | `/api/destinos` | Lista destinos disponibles. Usa `?solo_disponibles=false` para incluir los no disponibles. |
| `POST` | `/api/destinos` | Crea un destino. |
| `PUT` | `/api/destinos/{id_destino}` | Modifica un destino existente. |
| `DELETE` | `/api/destinos/{id_destino}` | Elimina o marca como no disponible un destino. |
| `GET` | `/api/paquetes` | Lista paquetes, destinos incluidos y cupos disponibles. |
| `POST` | `/api/paquetes` | Publica un paquete turístico. |
| `POST` | `/api/reservas` | Crea una reserva si hay cupos disponibles. |
| `GET` | `/api/reservas/usuario/{id_usuario}` | Consulta las reservas de un usuario. |
| `GET` | `/api/indicadores` | Devuelve conteos de destinos, paquetes y reservas, ingresos y ocupación. |

### Ejemplos de peticiones

Crear un destino:

```json
{
  "nombre": "Torres del Paine",
  "zona": "Patagonia Chilena",
  "descripcion": "Parque Nacional",
  "duracion_dias": 5,
  "costo_base": 250000
}
```

Crear un paquete (se necesitan entre 2 y 5 destinos distintos):

```json
{
  "nombre": "Gran Tour Patagonia",
  "cupo_maximo": 10,
  "fecha_salida": "2026-11-01",
  "fecha_regreso": "2026-11-10",
  "margen_operacion": 20,
  "id_destinos": [1, 2]
}
```

Crear una reserva:

```json
{
  "id_usuario": 2,
  "id_paquete": 1,
  "cantidad_personas": 2
}
```

## Cómo se conecta la página web

Abre `index.html` en un navegador para ver la interfaz. Por defecto, JavaScript intenta conectarse a `http://127.0.0.1:8000`. Para cambiar el servidor:

1. Inicia la API y confirma que su URL sea accesible desde el navegador.
2. En la sección **Conexión de la API**, escribe la URL base, por ejemplo `https://mi-api.example.com`.
3. Selecciona **Conectar**.

La URL seleccionada se guarda en el almacenamiento local del navegador. La página consulta `/api/destinos`, `/api/paquetes` y `/api/indicadores`, y envía las reservas a `/api/reservas`.

### Publicar la página en Vercel

Importa este repositorio en Vercel y selecciona la carpeta raíz del proyecto. Como el frontend es estático, no requiere instalar paquetes de JavaScript ni ejecutar un paso de compilación. Después de desplegar:

1. Publica la API en un servidor compatible con Python y configura su base de datos persistente.
2. Abre la página desplegada en Vercel.
3. En **Conexión de la API**, guarda la URL HTTPS pública del backend.

Para que el navegador pueda comunicarse con la API desplegada, el backend debe permitir el origen de la página en su configuración CORS. La base SQLite local no se despliega con este frontend; en servicios efímeros o serverless es necesario configurar persistencia para el backend.

## Datos locales

Por defecto, SQLite crea `viajes_aventura.db` en la carpeta del proyecto al iniciar la aplicación. Se puede indicar otra ruta con la variable de entorno `VIAJES_DB_PATH`. La base de datos y sus archivos auxiliares están excluidos de Git mediante `.gitignore`; cada instalación local puede tener sus propios datos.

## Consideraciones de seguridad

Este repositorio es un proyecto académico y necesita medidas adicionales antes de usarse en producción:

- La contraseña inicial del administrador (`admin123`) está definida en el código y es pública. Cámbiala y evita usar la cuenta de demostración en un entorno real.
- La API no implementa tokens o sesiones ni autorización por rol en sus endpoints de escritura. Validar las credenciales en el endpoint de login no protege por sí solo las demás rutas.
- CORS está configurado para permitir cualquier origen. Restringe `allow_origins` al dominio de la página desplegada.
- Las validaciones de RUT y correo son básicas y no sustituyen una verificación formal.
- La base de datos SQLite local no es un servicio de persistencia compartido para producción.

## Licencia

Proyecto académico. No se define una licencia de distribución en este repositorio.
