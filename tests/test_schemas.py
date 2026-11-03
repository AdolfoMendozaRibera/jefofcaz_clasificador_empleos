"""Pruebas unitarias para los esquemas y validadores de la API (Pydantic v2).

Verifica la estrategia Fail-Fast: rechazo inmediato de texto vacío, muy corto,
excesivamente largo o sin caracteres lingüísticos válidos con mensajes en español.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from api.schemas import (
    MIN_CHARS,
    MAX_CHARS,
    PredictRequest,
    PredictResponse,
    NLPStepAudit,
    BatchResponse,
    BatchItemResult,
    HealthResponse,
    validar_texto_oferta,
)


def test_texto_valido_conserva_contenido_y_remueve_espacios_extremos():
    """Verifica que un texto válido pasa la validación y se limpia."""
    entrada = "   Se busca cocinero profesional para restaurante de menú diario.   "
    salida = validar_texto_oferta(entrada)
    assert salida == "Se busca cocinero profesional para restaurante de menú diario."


def test_rechazo_texto_vacio():
    """Verifica que cadenas vacías lanzan ValueError en español."""
    with pytest.raises(ValueError, match="está vacío o solo contiene espacios"):
        validar_texto_oferta("")


def test_rechazo_texto_solo_espacios():
    """Verifica que cadenas con solo espacios o tabulaciones sean rechazadas."""
    with pytest.raises(ValueError, match="está vacío o solo contiene espacios"):
        validar_texto_oferta("      \n\t  ")


def test_rechazo_texto_menor_al_limite_minimo():
    """Verifica que textos con menos caracteres que MIN_CHARS sean rechazados."""
    texto_corto = "Hola camarero"
    assert len(texto_corto) < MIN_CHARS
    with pytest.raises(ValueError, match=f"el mínimo requerido es de {MIN_CHARS}"):
        validar_texto_oferta(texto_corto)


def test_rechazo_texto_mayor_al_limite_maximo():
    """Verifica que textos que exceden MAX_CHARS sean rechazados."""
    texto_largo = "a" * (MAX_CHARS + 1)
    with pytest.raises(ValueError, match=f"el límite máximo permitido es de {MAX_CHARS}"):
        validar_texto_oferta(texto_largo)


def test_rechazo_texto_sin_letras_validas():
    """Verifica que cadenas compuestas únicamente por números, signos o emojis fallen."""
    casos_sin_letras = [
        "1234567890123456",
        "??? !!! *** --- ___ +++",
        "1234-5678-9012-3456",
    ]
    for caso in casos_sin_letras:
        with pytest.raises(ValueError, match="no contiene letras o palabras válidas"):
            validar_texto_oferta(caso)


def test_pydantic_predict_request_valida_correctamente():
    """Verifica que el modelo PredictRequest de Pydantic capture errores con ValidationError."""
    # Caso válido
    req = PredictRequest(texto="Se busca oficial albañil para obra en Valencia.")
    assert "albañil" in req.texto

    # Caso inválido: dispara ValidationError de Pydantic
    with pytest.raises(ValidationError) as exc_info:
        PredictRequest(texto="   ")
    errores = exc_info.value.errors()
    assert len(errores) > 0
    assert "está vacío" in errores[0]["msg"]


def test_estructuras_de_respuesta_pydantic():
    """Verifica que los modelos de respuesta serialicen los tipos esperados."""
    audit = NLPStepAudit(
        texto_original="Oferta de empleo",
        texto_normalizado="oferta de empleo",
        tokens=["oferta", "empleo"],
        sin_stopwords=["empleo"],
        raices=["emple"],
        texto_procesado="emple",
    )
    assert audit.tokens == ["oferta", "empleo"]

    resp = PredictResponse(
        sector_predicho="ventas_comercial",
        probabilidad=0.9123,
        probabilidades={
            "transporte_logistica": 0.02,
            "hosteleria_gastronomia": 0.03,
            "ventas_comercial": 0.9123,
            "salud_servicios_sociales": 0.0177,
            "construccion_mantenimiento": 0.02,
        },
        preprocesamiento=audit,
        tiempo_ms=2.15,
    )
    assert resp.sector_predicho == "ventas_comercial"
    assert resp.probabilidad == 0.9123

    salud = HealthResponse(
        estado="ok",
        modelo_cargado=True,
        modelo_nombre="Regresión Logística",
        sectores_soportados=["ventas_comercial"],
    )
    assert salud.modelo_cargado is True

