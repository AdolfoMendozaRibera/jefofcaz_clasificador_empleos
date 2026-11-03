"""Contratos de datos y validación en el borde para la API REST.

Define los esquemas Pydantic v2 utilizados para validar peticiones y estructurar
respuestas en los endpoints de FastAPI. Aplica la estrategia de falla rápida (Fail-Fast)
rechazando textos no analizables con errores HTTP 422 antes de invocar el modelo.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from pydantic import BaseModel, Field, field_validator, ConfigDict


# -----------------------------------------------------------------------------
# Carga de límites y configuración desde params.yaml (Fuente única de verdad)
# -----------------------------------------------------------------------------
def _cargar_limites_validacion() -> tuple[int, int, list[str]]:
    """Carga los límites de caracteres y lista de sectores desde params.yaml."""
    ruta_params = Path(__file__).resolve().parent.parent / "params.yaml"
    limite_minimo = 15
    limite_maximo = 5000
    sectores_por_defecto = [
        "transporte_logistica",
        "hosteleria_gastronomia",
        "ventas_comercial",
        "salud_servicios_sociales",
        "construccion_mantenimiento",
    ]

    if ruta_params.exists():
        try:
            with open(ruta_params, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
            datos_cfg = config.get("data", {})
            limite_minimo = int(datos_cfg.get("min_chars", limite_minimo))
            limite_maximo = int(datos_cfg.get("max_chars", limite_maximo))
            sectores_por_defecto = datos_cfg.get("sectores", sectores_por_defecto)
        except Exception:
            pass

    return limite_minimo, limite_maximo, sectores_por_defecto


MIN_CHARS, MAX_CHARS, SECTORES_VALIDOS = _cargar_limites_validacion()

# Patrón para verificar que el texto contenga al menos una letra válida en español
PATRON_LETRAS = re.compile(r"[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]")


# -----------------------------------------------------------------------------
# Funciones de validación pura
# -----------------------------------------------------------------------------
def validar_texto_oferta(texto: str) -> str:
    """Valida y limpia una cadena de oferta laboral en el borde de la API.

    Parameters
    ----------
    texto : str
        Texto ingresado por el usuario o cliente web.

    Returns
    -------
    str
        Texto limpio (sin espacios redundantes en extremos).

    Raises
    ------
    ValueError
        Si el texto está vacío, fuera de los límites de longitud o carece de letras.

    Examples
    --------
    >>> validar_texto_oferta("   ")
    Traceback (most recent call last):
    ...
    ValueError: El texto está vacío o solo contiene espacios.
    """
    if not isinstance(texto, str):
        raise ValueError("El cuerpo de la petición debe contener un texto entre comillas.")

    texto_limpio = texto.strip()

    if not texto_limpio:
        raise ValueError("El texto de la oferta está vacío o solo contiene espacios.")

    longitud = len(texto_limpio)
    if longitud < MIN_CHARS:
        raise ValueError(
            f"El texto tiene {longitud} caracteres; el mínimo requerido es de {MIN_CHARS} caracteres."
        )

    if longitud > MAX_CHARS:
        raise ValueError(
            f"El texto tiene {longitud} caracteres; el límite máximo permitido es de {MAX_CHARS} caracteres."
        )

    if not PATRON_LETRAS.search(texto_limpio):
        raise ValueError(
            "El texto no contiene letras o palabras válidas para poder clasificar el sector laboral."
        )

    return texto_limpio


# -----------------------------------------------------------------------------
# Modelos Pydantic v2: Peticiones (Requests)
# -----------------------------------------------------------------------------
class PredictRequest(BaseModel):
    """Esquema de entrada para clasificación individual de ofertas laborales."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "texto": "Se busca conductor de camión tráiler para ruta nacional con carnet C+E y CAP en vigor."
            }
        }
    )

    texto: str = Field(
        ...,
        description="Descripción textual de la oferta de trabajo a clasificar.",
    )

    @field_validator("texto")
    @classmethod
    def validar_campo_texto(cls, valor: str) -> str:
        """Aplica la validación estricta de longitud y caracteres."""
        return validar_texto_oferta(valor)


# -----------------------------------------------------------------------------
# Modelos Pydantic v2: Respuestas (Responses)
# -----------------------------------------------------------------------------
class NLPStepAudit(BaseModel):
    """Estructura de auditoría paso a paso del pipeline de NLP.

    Permite al frontend dibujar la columna de explicabilidad requerida por el proyecto.
    """

    texto_original: str = Field(..., description="Texto original tal como fue ingresado.")
    texto_normalizado: str = Field(..., description="Texto en minúsculas, sin URLs ni caracteres extraños.")
    tokens: List[str] = Field(..., description="Lista de tokens aislados.")
    sin_stopwords: List[str] = Field(..., description="Tokens tras filtrar palabras vacías manteniendo negaciones.")
    raices: List[str] = Field(..., description="Tokens reducidos mediante stemming/lematización.")
    texto_procesado: str = Field(..., description="Cadena final que recibe el vectorizador TF-IDF.")


class PredictResponse(BaseModel):
    """Respuesta estructurada para una predicción individual."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sector_predicho": "transporte_logistica",
                "probabilidad": 0.9412,
                "probabilidades": {
                    "transporte_logistica": 0.9412,
                    "hosteleria_gastronomia": 0.0211,
                    "ventas_comercial": 0.0154,
                    "salud_servicios_sociales": 0.0118,
                    "construccion_mantenimiento": 0.0105,
                },
                "preprocesamiento": {
                    "texto_original": "Se busca conductor...",
                    "texto_normalizado": "se busca conductor...",
                    "tokens": ["se", "busca", "conductor"],
                    "sin_stopwords": ["conductor"],
                    "raices": ["conductor"],
                    "texto_procesado": "conductor",
                },
                "tiempo_ms": 3.45,
            }
        }
    )

    sector_predicho: str = Field(..., description="Nombre del sector con mayor probabilidad.")
    probabilidad: float = Field(..., ge=0.0, le=1.0, description="Nivel de confianza de la predicción (0 a 1).")
    probabilidades: Dict[str, float] = Field(
        ..., description="Distribución de probabilidad de los 5 sectores laborales."
    )
    preprocesamiento: NLPStepAudit = Field(
        ..., description="Auditoría transparente de los pasos de NLP aplicados al texto."
    )
    tiempo_ms: float = Field(..., ge=0.0, description="Tiempo de inferencia del servidor en milisegundos.")


class BatchItemResult(BaseModel):
    """Resultado individual de una oferta procesada dentro de un archivo CSV."""

    id: int = Field(..., description="Índice de fila en el archivo original.")
    texto_resumen: str = Field(..., description="Primeros 120 caracteres de la oferta.")
    sector_predicho: str = Field(..., description="Sector predicho por el modelo.")
    probabilidad: float = Field(..., ge=0.0, le=1.0, description="Probabilidad de la clase predicha.")


class BatchResponse(BaseModel):
    """Resumen consolidado para la carga masiva de ofertas laborales."""

    total_procesados: int = Field(..., ge=0, description="Cantidad total de ofertas evaluadas.")
    distribucion_sectores: Dict[str, int] = Field(
        ..., description="Conteo de ofertas asignadas a cada sector."
    )
    resultados: List[BatchItemResult] = Field(
        ..., description="Listado detallado de cada fila clasificada."
    )
    tiempo_total_ms: float = Field(..., ge=0.0, description="Tiempo total invertido en procesar el lote.")


class HealthResponse(BaseModel):
    """Estado operativo del servicio y del artefacto en memoria."""

    estado: str = Field(..., description="'ok' si el modelo está listo para inferir, 'degradado' si no.")
    modelo_cargado: bool = Field(..., description="Indica si model.joblib está presente en RAM.")
    modelo_nombre: Optional[str] = Field(None, description="Nombre y configuración del modelo activo.")
    sectores_soportados: List[str] = Field(..., description="Lista de sectores que el modelo puede predecir.")
    version: str = Field(default="1.0.0", description="Versión de la API.")


class ErrorResponse(BaseModel):
    """Formato estándar para respuestas de error de la API."""

    status: str = Field(default="error", description="Identificador de estado de error.")
    mensaje: str = Field(..., description="Explicación en español amigable para el usuario.")
    detalle: Optional[Any] = Field(None, description="Detalles técnicos adicionales o lista de fallos de validación.")

