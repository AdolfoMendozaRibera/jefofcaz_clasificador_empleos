"""Pruebas unitarias automatizadas para los artefactos de produccion de Fase 3 (Paso 3.4).

Verifica directamente los artefactos generados en artifacts/:
1. artifacts/model.joblib: Carga limpia, estructura del bundle, inferencia en 5 sectores y suma de probabilidades = 1.0.
2. artifacts/metrics.json: Integridad del esquema, dimensiones de matriz 5x5 y terminos influyentes por clase.
3. artifacts/errors.csv: Validez de los casos diagnosticados (sector_real != sector_predicho para todos los registros).
"""

import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.pipeline import Pipeline


RAIZ = Path(__file__).resolve().parent.parent
RUTA_JOBLIB = RAIZ / "artifacts" / "model.joblib"
RUTA_METRICS = RAIZ / "artifacts" / "metrics.json"
RUTA_ERRORS = RAIZ / "artifacts" / "errors.csv"


def test_existencia_de_artefactos_oficiales() -> None:
    """Verifica que los tres artefactos requeridos por la rúbrica existan físicamente en disk."""
    assert RUTA_JOBLIB.exists(), f"Falta el archivo: {RUTA_JOBLIB}"
    assert RUTA_METRICS.exists(), f"Falta el archivo: {RUTA_METRICS}"
    assert RUTA_ERRORS.exists(), f"Falta el archivo: {RUTA_ERRORS}"


def test_cargar_artefacto_model_joblib_y_metadatos() -> None:
    """Verifica la carga del bundle de producción y su estructura interna."""
    bundle = joblib.load(RUTA_JOBLIB)

    assert isinstance(bundle, dict), "El bundle debe ser un diccionario estructurado."
    claves_esperadas = ["pipeline", "clases", "sectores", "modelo", "hiperparametros", "metricas_test"]
    for clave in claves_esperadas:
        assert clave in bundle, f"Falta la clave '{clave}' en el bundle serializado."

    pipeline = bundle["pipeline"]
    assert isinstance(pipeline, Pipeline), "El objeto debe ser una instancia oficial de Scikit-Learn Pipeline."
    assert "preprocessor" in pipeline.named_steps
    assert "tfidf" in pipeline.named_steps
    assert "model" in pipeline.named_steps

    # Verificar que contenga los 5 sectores oficiales
    assert len(bundle["sectores"]) == 5
    sectores_esperados = {
        "transporte_logistica",
        "hosteleria_gastronomia",
        "ventas_comercial",
        "salud_servicios_sociales",
        "construccion_mantenimiento",
    }
    assert set(bundle["sectores"]) == sectores_esperados


def test_inferencia_cinco_sectores_ofertas_claras() -> None:
    """Valida que el modelo prediga con precisión ofertas arquetípicas de cada sector."""
    bundle = joblib.load(RUTA_JOBLIB)
    pipeline = bundle["pipeline"]

    casos_prueba = [
        (
            "Conductor de camión tráiler ruta nacional e internacional carnet C+E tacógrafo digital y reparto de mercancías",
            "transporte_logistica",
        ),
        (
            "Cocinero jefe de partida para restaurante de tapas elaboración de menús diarios y gestión de cocina",
            "hosteleria_gastronomia",
        ),
        (
            "Oficial de primera albañil para obra nueva alicatado colocación de ladrillo solado y reformas de construcción",
            "construccion_mantenimiento",
        ),
        (
            "Enfermero para residencia de ancianos y centro sociosanitario administración de medicación y curas a residentes",
            "salud_servicios_sociales",
        ),
        (
            "Agente comercial inmobiliario prospección y captación de clientes venta de inmuebles y cierre de contratos comerciales",
            "ventas_comercial",
        ),
    ]

    for texto, sector_esperado in casos_prueba:
        prediccion = pipeline.predict([texto])[0]
        assert prediccion == sector_esperado, f"Texto '{texto}' predijo '{prediccion}', se esperaba '{sector_esperado}'"


def test_probabilidades_suman_uno_propiedad_matematica() -> None:
    """Verifica que las probabilidades devueltas por predict_proba sumen exactamente 1.0 (Softmax)."""
    bundle = joblib.load(RUTA_JOBLIB)
    pipeline = bundle["pipeline"]

    textos = [
        "Mozo de almacén y carretillero con carnet",
        "Auxiliar de clínica dental atención a pacientes",
        "Pintor de fachadas y trabajos verticales",
    ]

    probas = pipeline.predict_proba(textos)

    assert probas.shape == (len(textos), 5)
    for fila_proba in probas:
        suma = float(np.sum(fila_proba))
        assert suma == pytest.approx(1.0, rel=1e-5), f"Las probabilidades suman {suma}, deben sumar 1.0"
        # Ninguna probabilidad puede ser negativa
        assert np.all(fila_proba >= 0.0)


def test_f1_macro_supera_ampliamente_baseline() -> None:
    """Verifica que el F1-Score en test supere el umbral de calidad exigido (mínimo 0.85)."""
    bundle = joblib.load(RUTA_JOBLIB)
    f1_test = bundle["metricas_test"]["f1_macro"]

    # F1 oficial obtenido en test es ~0.9155, muy superior al DummyClassifier (~0.0892)
    assert f1_test >= 0.85, f"F1 Macro en test ({f1_test}) no supera el umbral de 0.85."


def test_integridad_metrics_json() -> None:
    """Verifica que metrics.json cumpla con el contrato estricto requerido por FastAPI y React."""
    with open(RUTA_METRICS, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    campos_requeridos = [
        "modelo",
        "f1_macro",
        "accuracy",
        "clases",
        "reporte_por_clase",
        "matriz_confusion",
        "terminos_mas_influyentes",
    ]
    for campo in campos_requeridos:
        assert campo in metrics, f"Falta el campo '{campo}' en metrics.json"

    # Verificar matriz 5x5
    cm = metrics["matriz_confusion"]
    assert len(cm) == 5, "La matriz de confusión debe tener 5 filas."
    for fila in cm:
        assert len(fila) == 5, "Cada fila de la matriz de confusión debe tener 5 columnas."

    # Verificar términos influyentes
    top_terms = metrics["terminos_mas_influyentes"]
    assert len(top_terms) == 5, "Debe haber términos influyentes para los 5 sectores."
    for sector, terminos in top_terms.items():
        assert len(terminos) == 10, f"El sector '{sector}' debe tener 10 términos principales."
        for item in terminos:
            assert "termino" in item and "peso" in item


def test_integridad_errors_csv() -> None:
    """Verifica que errors.csv contenga exclusivamente ofertas con clasificación errónea real."""
    df_err = pd.read_csv(RUTA_ERRORS)

    columnas_requeridas = [
        "id",
        "sector_real",
        "sector_predicho",
        "probabilidad_predicha",
        "probabilidad_real",
        "causa_linguistica",
        "explicacion_linguistica",
    ]
    for col in columnas_requeridas:
        assert col in df_err.columns, f"Falta la columna '{col}' en errors.csv"

    # En el 100% de las filas, sector_real debe ser distinto a sector_predicho
    errores_reales = df_err["sector_real"] != df_err["sector_predicho"]
    assert errores_reales.all(), "Todas las filas de errors.csv deben ser clasificaciones fallidas."

    # Verificar que no haya causas lingüísticas vacías
    assert df_err["causa_linguistica"].isna().sum() == 0
