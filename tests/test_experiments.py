"""Pruebas unitarias para el modulo de experimentos y validacion cruzada (Paso 3.1)."""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.naive_bayes import MultinomialNB

from src.models.experiments import (
    cargar_datos_entrenamiento,
    evaluar_pliegues_cv,
    ejecutar_matriz_experimentos,
)


def test_cargar_datos_entrenamiento_estructura_y_tipos() -> None:
    """Verifica que cargar_datos_entrenamiento retorne series con los tipos y longitudes esperados."""
    X, y = cargar_datos_entrenamiento()

    assert len(X) == len(y)
    assert len(X) > 1000  # En nuestro caso 2.669 registros
    assert isinstance(X, pd.Series)
    assert isinstance(y, pd.Series)

    # Verificar que no contengan valores nulos
    assert X.isna().sum() == 0
    assert y.isna().sum() == 0

    # Verificar los 5 sectores presentes
    sectores_unicos = set(y.unique())
    sectores_esperados = {
        "transporte_logistica",
        "hosteleria_gastronomia",
        "ventas_comercial",
        "salud_servicios_sociales",
        "construccion_mantenimiento",
    }
    assert sectores_esperados.issubset(sectores_unicos)


def test_evaluar_pliegues_cv_mini_corpus_a_mano() -> None:
    """Verifica la rutina de evaluacion de pliegues con un corpus de juguete.

    Corpus sintetico de 10 muestras (2 por clase) para k=2 folds:
    - Comprueba que f1_macro y accuracy esten en el rango [0.0, 1.0].
    - Comprueba que el DummyClassifier devuelva métricas esperadas.
    """
    textos = [
        "conductor chofer transporte camion",
        "camion chofer repartidor ruta",
        "cocinero camarero restaurante chef",
        "camarero barista cocina tapas",
        "albanil oficial obra construccion",
        "encofrador ferralla pintor obra",
        "medico enfermero hospital clinica",
        "auxiliar enfermeria geriatria paciente",
        "vendedor dependiente tienda comercial",
        "comercial teleoperador ventas cliente",
    ]
    etiquetas = pd.Series([
        "transporte", "transporte",
        "hosteleria", "hosteleria",
        "construccion", "construccion",
        "salud", "salud",
        "ventas", "ventas",
    ])

    cv = StratifiedKFold(n_splits=2, shuffle=True, random_state=42)
    vec_cfg = {"ngram_range": (1, 1), "min_df": 1, "max_df": 1.0, "sublinear_tf": False}

    # 1. Probar con Modelo de ML (LogisticRegression)
    f1_m, f1_s, acc_m, acc_s = evaluar_pliegues_cv(
        textos_procesados=textos,
        etiquetas=etiquetas,
        vectorizer_config=vec_cfg,
        modelo=LogisticRegression(C=1.0, random_state=42),
        cv=cv,
    )

    assert 0.0 <= f1_m <= 1.0
    assert 0.0 <= f1_s <= 1.0
    assert 0.0 <= acc_m <= 1.0
    assert 0.0 <= acc_s <= 1.0

    # 2. Probar con DummyClassifier (estrategia most_frequent)
    dummy_f1_m, _, dummy_acc_m, _ = evaluar_pliegues_cv(
        textos_procesados=textos,
        etiquetas=etiquetas,
        vectorizer_config=vec_cfg,
        modelo=DummyClassifier(strategy="most_frequent"),
        cv=cv,
    )

    # Con 5 clases equitativas (2 cada una), predecir siempre una sola clase acierta 2/10 = 0.20
    assert dummy_acc_m == pytest.approx(0.20, abs=1e-2)
    # F1 macro con 5 clases y solo 1 clase predicha es aproximadamente (2 / (2 + 8)) / 5 = 0.04
    assert dummy_f1_m < 0.15


def test_ejecutar_matriz_experimentos_salida_csv(tmp_path: Path) -> None:
    """Verifica que ejecutar_matriz_experimentos genere correctamente el CSV en disco.

    Usa un archivo train temporal pequeño para validar el pipeline de punta a punta.
    """
    train_csv = tmp_path / "train_mini.csv"
    salida_csv = tmp_path / "experiments.csv"

    # Dataset de prueba con 30 ejemplos (6 por clase)
    sectores = [
        "transporte_logistica",
        "hosteleria_gastronomia",
        "ventas_comercial",
        "salud_servicios_sociales",
        "construccion_mantenimiento",
    ]
    filas = []
    for sector in sectores:
        for i in range(6):
            filas.append({
                "texto": f"Oferta de empleo para puesto de {sector} con experiencia requerida numero {i}",
                "sector": sector,
            })
    pd.DataFrame(filas).to_csv(train_csv, index=False)

    df_res = ejecutar_matriz_experimentos(
        ruta_train=train_csv,
        ruta_salida_csv=salida_csv,
        incluir_lematizacion=False,  # Para rapidez en el test
        n_splits=2,
    )

    assert salida_csv.exists()
    assert len(df_res) >= 10
    assert "f1_macro_media" in df_res.columns
    assert "modelo" in df_res.columns

    # El DataFrame debe estar ordenado de mayor a menor F1
    f1_valores = df_res["f1_macro_media"].tolist()
    assert f1_valores == sorted(f1_valores, reverse=True)

    # La línea base DummyClassifier no debe estar en primer lugar
    assert df_res.iloc[0]["modelo"] != "DummyClassifier"
