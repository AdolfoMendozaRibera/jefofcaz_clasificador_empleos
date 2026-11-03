"""Pruebas unitarias para la capa de servicio del modelo (api/service.py).

Verifica la carga en memoria RAM, inferencia individual con Softmax, explicabilidad
de NLP paso a paso, procesamiento vectorizado por lotes (CSV) y entrega de métricas.
"""

from __future__ import annotations

import io
import pytest
import pandas as pd
from api.service import ModelService


@pytest.fixture(scope="module")
def servicio():
    """Fixture que inicializa y carga el servicio del modelo oficial una sola vez."""
    srv = ModelService()
    srv.load()
    return srv


def test_service_load_exitoso(servicio: ModelService):
    """Verifica que el modelo y los metadatos se carguen correctamente en memoria RAM."""
    assert servicio.loaded is True
    assert servicio.pipeline is not None
    assert len(servicio.clases) == 5
    assert "transporte_logistica" in servicio.clases
    assert "hosteleria_gastronomia" in servicio.clases


def test_service_predict_single_y_propiedades_matematicas(servicio: ModelService):
    """Verifica la inferencia individual y que las probabilidades sumen 1.0."""
    texto = "Se busca cocinero jefe de partida para restaurante tradicional menús diarios y tapas."
    resultado = servicio.predict_single(texto)

    assert "sector_predicho" in resultado
    assert resultado["sector_predicho"] == "hosteleria_gastronomia"
    assert "probabilidad" in resultado
    assert resultado["probabilidad"] > 0.50

    # Las probabilidades de los 5 sectores deben sumar 1.0 (Softmax)
    probabilidades = resultado["probabilidades"]
    assert len(probabilidades) == 5
    assert sum(probabilidades.values()) == pytest.approx(1.0, abs=1e-3)

    # Explicabilidad presente
    assert "preprocesamiento" in resultado
    preproc = resultado["preprocesamiento"]
    assert "tokens" in preproc
    assert "sin_stopwords" in preproc
    assert "raices" in preproc
    assert len(preproc["tokens"]) > 0


def test_service_explain_pasos_intermedios_nlp(servicio: ModelService):
    """Verifica que el método explain desglose las 6 etapas lingüísticas."""
    texto = "Camionero chofer trailer ruta internacional"
    pasos = servicio.explain(texto)

    assert pasos["texto_original"] == texto
    assert isinstance(pasos["tokens"], list)
    assert isinstance(pasos["sin_stopwords"], list)
    assert isinstance(pasos["raices"], list)
    assert isinstance(pasos["texto_procesado"], str)


def test_service_batch_csv_procesamiento_vectorizado(servicio: ModelService):
    """Verifica el procesamiento por lotes con un CSV simulado."""
    csv_datos = (
        "descripcion\n"
        "Conductor de camión articulado con carnet C+E para transporte de mercancías\n"
        "Camarero de barra y sala con experiencia en cafetería y manejo de bandeja\n"
        "Oficial albañil de primera para obra y reformas alicatado solado\n"
    )
    bytes_csv = csv_datos.encode("utf-8")

    lote = servicio.predict_batch_csv(bytes_csv)

    assert lote["total_procesados"] == 3
    assert len(lote["resultados"]) == 3
    assert lote["resultados"][0]["sector_predicho"] == "transporte_logistica"
    assert lote["resultados"][1]["sector_predicho"] == "hosteleria_gastronomia"
    assert lote["resultados"][2]["sector_predicho"] == "construccion_mantenimiento"

    # La distribución de sectores debe sumar el total de filas
    assert sum(lote["distribucion_sectores"].values()) == 3


def test_service_batch_csv_vacio_o_invalido_falla(servicio: ModelService):
    """Verifica que un archivo vacío o sin columna de texto genere ValueError."""
    with pytest.raises(ValueError, match="vacío"):
        servicio.predict_batch_csv(b"")

    # CSV sin columnas de texto
    csv_solo_numeros = "id,edad\n1,25\n2,30\n".encode("utf-8")
    with pytest.raises(ValueError, match="no contiene una columna reconocible"):
        servicio.predict_batch_csv(csv_solo_numeros)


def test_service_get_metrics_retorna_metricas_oficiales(servicio: ModelService):
    """Verifica la exposición del archivo metrics.json."""
    metricas = servicio.get_metrics()
    assert "f1_macro" in metricas
    assert metricas["f1_macro"] >= 0.85
    assert "matriz_confusion" in metricas
    assert len(metricas["matriz_confusion"]) == 5


def test_service_health_check(servicio: ModelService):
    """Verifica el diccionario de salud de la API."""
    salud = servicio.health()
    assert salud["estado"] == "ok"
    assert salud["modelo_cargado"] is True
    assert len(salud["sectores_soportados"]) == 5

