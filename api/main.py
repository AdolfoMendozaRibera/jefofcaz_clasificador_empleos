"""Punto de entrada y definición de rutas de la API REST con FastAPI (Fase 4 - Paso 4.3).

Expone los endpoints oficiales del clasificador de ofertas de empleo bajo el prefijo `/api`:
- `GET  /api/health`: Estado operativo y confirmación del modelo cargado en RAM.
- `POST /api/predict`: Inferencia individual con auditoría NLP paso a paso (HTTP 422 si es inválido).
- `POST /api/predict/batch`: Carga y clasificación masiva de archivos CSV.
- `GET  /api/metrics`: Métricas de rendimiento, matriz de confusión 5x5 y términos influyentes.

Implementa el patrón `lifespan` para carga única del modelo y CORS para Vite.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
import logging
import time
from typing import Any, Dict
from fastapi import FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.schemas import (
    BatchResponse,
    ErrorResponse,
    HealthResponse,
    PredictRequest,
    PredictResponse,
)
from api.service import model_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("api_main")


# -----------------------------------------------------------------------------
# Patrón Lifespan: Carga única del modelo en memoria RAM al iniciar el servidor
# -----------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestiona el ciclo de vida de la aplicación.
    
    Carga el artefacto serializado en memoria antes de empezar a recibir peticiones
    y libera recursos al apagarse el servidor.
    """
    logger.info("Iniciando servicio de clasificación de ofertas de empleo...")
    try:
        model_service.load()
        logger.info("✅ Pipeline de Machine Learning cargado y listo para inferencias.")
    except Exception as e:
        logger.error(f"❌ Error crítico al cargar el modelo durante el arranque: {e}")
        # Se permite que el servidor arranque en modo degradado para poder reportarlo en /health
    yield
    logger.info("🛑 Servidor apagándose. Limpieza de memoria completada.")


# -----------------------------------------------------------------------------
# Creación de la instancia FastAPI
# -----------------------------------------------------------------------------
app = FastAPI(
    title="API Clasificador de Ofertas Laborales (NLP)",
    description=(
        "Servicio REST para la clasificación automática de ofertas de empleo en 5 sectores económicos "
        "mediante NLP (TF-IDF + Regresión Logística Multinomial). Incluye explicabilidad lingüística paso a paso."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# -----------------------------------------------------------------------------
# Configuración de CORS (Cross-Origin Resource Sharing)
# -----------------------------------------------------------------------------
# Permite conexiones desde el servidor de desarrollo de Vite (puerto 5173 y 8080)
ORIGENES_PERMITIDOS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENES_PERMITIDOS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# -----------------------------------------------------------------------------
# Manejadores Globales de Excepciones
# -----------------------------------------------------------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Captura errores de validación de Pydantic v2 y responde con HTTP 422 limpio en español."""
    errores_formateados = []
    for err in exc.errors():
        ubicacion = " -> ".join(str(loc) for loc in err.get("loc", []) if loc != "body")
        mensaje = err.get("msg", "Entrada inválida.")
        # Limpiar prefijo 'Value error, ' que genera Pydantic por defecto
        if mensaje.startswith("Value error, "):
            mensaje = mensaje.replace("Value error, ", "")
        errores_formateados.append({"campo": ubicacion, "mensaje": mensaje})

    mensaje_principal = errores_formateados[0]["mensaje"] if errores_formateados else "Error de validación en la petición."

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "mensaje": mensaje_principal,
            "detalle": errores_formateados,
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Evita la fuga de trazas internas (stacktraces) ante fallos no previstos (HTTP 500)."""
    logger.error(f"Fallo no controlado en la ruta {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "mensaje": "Ocurrió un error inesperado al procesar la solicitud en el servidor.",
            "detalle": str(exc),
        },
    )


# -----------------------------------------------------------------------------
# Endpoints de la API
# -----------------------------------------------------------------------------
@app.get(
    "/api/health",
    response_model=HealthResponse,
    tags=["Monitoreo"],
    summary="Estado de salud de la API y verificación del modelo",
)
def check_health() -> Dict[str, Any]:
    """Comprueba si el servidor web está activo y si el modelo está residente en memoria RAM."""
    return model_service.health()


@app.post(
    "/api/predict",
    response_model=PredictResponse,
    responses={
        422: {"model": ErrorResponse, "description": "Texto vacío, muy corto o inválido."},
        500: {"model": ErrorResponse, "description": "Error interno del servidor."},
    },
    tags=["Inferencia"],
    summary="Clasificación individual de una oferta laboral",
)
def predict_offer(peticion: PredictRequest) -> Dict[str, Any]:
    """Recibe la descripción de un empleo y devuelve el sector clasificado con explicabilidad.

    - **Validación Fail-Fast**: Si el texto tiene menos de 15 caracteres, más de 5000 o solo signos,
      retorna **HTTP 422** de forma inmediata.
    - **Inferencia Softmax**: Entrega las probabilidades de pertenencia a los 5 sectores.
    - **Auditoría NLP**: Incluye los pasos de normalización, tokens, stop words y raíces.
    """
    try:
        return model_service.predict_single(peticion.texto)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )


@app.post(
    "/api/predict/batch",
    response_model=BatchResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Formato de archivo incorrecto o corrupto."},
        422: {"model": ErrorResponse, "description": "CSV vacío o sin columnas de texto reconocibles."},
    },
    tags=["Inferencia"],
    summary="Clasificación masiva de ofertas mediante archivo CSV",
)
async def predict_batch(
    archivo: UploadFile = File(..., description="Archivo .csv que contenga ofertas laborales.")
) -> Dict[str, Any]:
    """Recibe un archivo CSV vía `multipart/form-data` y procesa todas sus ofertas de forma vectorizada.

    Detecta automáticamente columnas como `descripcion`, `texto`, `oferta`, etc.,
    y devuelve la distribución agregada por sector junto con cada oferta clasificada.
    """
    nombre_archivo = archivo.filename or ""
    if not nombre_archivo.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo proporcionado debe tener formato .csv.",
        )

    try:
        contenido_bytes = await archivo.read()
        return model_service.predict_batch_csv(contenido_bytes)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error procesando lote CSV: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar el archivo CSV: {e}",
        )


@app.get(
    "/api/metrics",
    tags=["Monitoreo"],
    summary="Métricas oficiales del modelo entrenado y matriz de confusión",
)
def get_metrics() -> Dict[str, Any]:
    """Expone las métricas congeladas generadas durante el entrenamiento en la Fase 3.

    Permite al frontend dibujar directamente la Matriz de Confusión interactiva ($5 \times 5$),
    el F1-score macro y el ranking de términos más influyentes sin recalcular nada en caliente.
    """
    try:
        return model_service.get_metrics()
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@app.get("/", tags=["Información"], include_in_schema=False)
def root_redirect():
    """Ruta raíz que provee información de bienvenida y enlace a la documentación interactiva."""
    return {
        "nombre": "Clasificador de Ofertas de Empleo (NLP API)",
        "estado": "operativo",
        "documentacion": "/docs",
        "version": "1.0.0",
    }

