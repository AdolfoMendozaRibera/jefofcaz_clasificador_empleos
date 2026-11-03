"""Pruebas unitarias para el modulo de entrenamiento oficial y analisis de errores (Paso 3.2)."""

import json
from pathlib import Path
import joblib
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from src.models.train import (
    cargar_datasets_oficiales,
    clasificar_causa_linguistica,
    construir_pipeline_campeon,
    entrenar_evaluar_y_serializar,
    extraer_terminos_influyentes,
)


def test_cargar_datasets_oficiales() -> None:
    """Verifica que los datasets train y test carguen con las columnas requeridas."""
    df_tr, df_ts = cargar_datasets_oficiales()

    assert len(df_tr) > 2000
    assert len(df_ts) > 500
    assert "texto" in df_tr.columns and "sector" in df_tr.columns
    assert "texto" in df_ts.columns and "sector" in df_ts.columns


def test_construir_pipeline_campeon_estructura() -> None:
    """Verifica la arquitectura del pipeline campeon."""
    pipeline = construir_pipeline_campeon()

    assert "preprocessor" in pipeline.named_steps
    assert "tfidf" in pipeline.named_steps
    assert "model" in pipeline.named_steps

    modelo = pipeline.named_steps["model"]
    assert isinstance(modelo, LogisticRegression)
    assert modelo.C == 2.0
    assert modelo.class_weight == "balanced"


def test_clasificar_causa_linguistica_casos_controlados() -> None:
    """Verifica la clasificacion automatica de causas linguisticas de error."""
    # 1. Caso descripcion corta
    causa_corta, _ = clasificar_causa_linguistica(
        texto="Oferta de empleo breve",
        sector_real="hosteleria_gastronomia",
        sector_pred="construccion_mantenimiento",
        proba_pred=0.55,
        proba_real=0.25,
    )
    assert causa_corta == "descripcion_breve"

    # 2. Caso con terminos en catalan
    causa_cat, _ = clasificar_causa_linguistica(
        texto="Cerquem infermer per a residencia assistida amb horari de matins i sou competitiu",
        sector_real="salud_servicios_sociales",
        sector_pred="transporte_logistica",
        proba_pred=0.60,
        proba_real=0.30,
    )
    assert causa_cat == "jerga_o_variante_regional"

    # 3. Caso farmacia con venta (vocabulario cruzado)
    causa_farmacia, _ = clasificar_causa_linguistica(
        texto="Farmacéutico/a para oficina de farmacia comunitaria realizando venta de medicamentos y atención al cliente",
        sector_real="salud_servicios_sociales",
        sector_pred="ventas_comercial",
        proba_pred=0.70,
        proba_real=0.20,
    )
    assert causa_farmacia == "vocabulario_cruzado_intersectorial"


def test_entrenar_y_serializar_de_punta_a_punta(tmp_path: Path) -> None:
    """Verifica que el flujo completo genere model.joblib, metrics.json y errors.csv."""
    train_csv = tmp_path / "train.csv"
    test_csv = tmp_path / "test.csv"
    salida_joblib = tmp_path / "model.joblib"
    salida_metrics = tmp_path / "metrics.json"
    salida_errors = tmp_path / "errors.csv"

    sectores = [
        "transporte_logistica",
        "hosteleria_gastronomia",
        "ventas_comercial",
        "salud_servicios_sociales",
        "construccion_mantenimiento",
    ]

    # Datos train (5 por clase)
    filas_tr = []
    for s in sectores:
        for i in range(5):
            filas_tr.append({
                "id": f"tr_{s}_{i}",
                "texto": f"Puesto de trabajo para {s} profesional calificado {i}",
                "sector": s,
            })
    pd.DataFrame(filas_tr).to_csv(train_csv, index=False)

    # Datos test (2 por clase)
    filas_ts = []
    for s in sectores:
        for i in range(2):
            filas_ts.append({
                "id": f"ts_{s}_{i}",
                "texto": f"Puesto de trabajo para {s} en la empresa {i}",
                "sector": s,
            })
    pd.DataFrame(filas_ts).to_csv(test_csv, index=False)

    resultado = entrenar_evaluar_y_serializar(
        ruta_train=train_csv,
        ruta_test=test_csv,
        ruta_joblib=salida_joblib,
        ruta_metrics=salida_metrics,
        ruta_errors=salida_errors,
    )

    # Validar que los 3 artefactos existan en disco
    assert salida_joblib.exists()
    assert salida_metrics.exists()
    assert salida_errors.exists()

    # Validar carga y predicción con model.joblib
    bundle = joblib.load(salida_joblib)
    assert "pipeline" in bundle
    assert "clases" in bundle
    pipe_cargado = bundle["pipeline"]
    pred = pipe_cargado.predict(["Puesto de trabajo para ventas_comercial"])
    assert pred[0] in sectores

    # Validar estructura de metrics.json
    with open(salida_metrics, "r", encoding="utf-8") as f:
        m = json.load(f)
        assert "f1_macro" in m
        assert "matriz_confusion" in m
        assert "reporte_por_clase" in m
        assert "terminos_mas_influyentes" in m
