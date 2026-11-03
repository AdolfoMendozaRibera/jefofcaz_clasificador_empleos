"""Pruebas unitarias para la vectorizacion TF-IDF y el Pipeline base de Scikit-Learn."""

import io
import joblib
import numpy as np
import pytest
from scipy.sparse import issparse
from sklearn.dummy import DummyClassifier
from sklearn.naive_bayes import MultinomialNB

from src.nlp.pipeline import crear_pipeline_nlp, crear_vectorizador_tfidf
from src.nlp.preprocessing import TextPreprocessor


def test_tfidf_configuracion_defaults_params_yaml() -> None:
    """Verifica que el vectorizador lea correctamente los parametros de params.yaml."""
    tfidf = crear_vectorizador_tfidf()

    assert tfidf.max_features == 4000
    assert tfidf.min_df == 2
    assert tfidf.max_df == 0.85
    assert tfidf.sublinear_tf is True
    assert tfidf.ngram_range == (1, 2)
    assert tfidf.lowercase is False
    assert tfidf.token_pattern == r"\S+"


def test_tfidf_calculo_a_mano_dos_documentos() -> None:
    """Valida la formula matematica de TF-IDF con un ejemplo minimo calculado a mano.

    Corpus de juguete (N=2 documentos):
      Doc 1: "camion camion"
      Doc 2: "camion chofer"

    Vocabulario alfabetico: ['camion', 'chofer']
    Indices: 'camion' -> 0, 'chofer' -> 1

    Calculo a mano (smooth_idf=True en scikit-learn):
      IDF(camion) = ln((1 + 2)/(1 + 2)) + 1 = ln(1) + 1 = 1.0
      IDF(chofer) = ln((1 + 2)/(1 + 1)) + 1 = ln(1.5) + 1 = 0.405465 + 1 = 1.405465

    Doc 1 (TF-sublinear: 1 + ln(2) = 1.693147):
      TF-IDF_raw(camion) = 1.693147 * 1.0 = 1.693147
      Normalizacion L2 (unico termino) -> 1.0

    Doc 2 (TF-sublinear de cada uno: 1 + ln(1) = 1.0):
      TF-IDF_raw(camion) = 1.0 * 1.0 = 1.0
      TF-IDF_raw(chofer) = 1.0 * 1.405465 = 1.405465
      Norma L2 = sqrt(1.0^2 + 1.405465^2) = sqrt(1.0 + 1.975332) = 1.724915
      TF-IDF_norm(camion) = 1.0 / 1.724915 = 0.579738
      TF-IDF_norm(chofer) = 1.405465 / 1.724915 = 0.814802
    """
    corpus = ["camion camion", "camion chofer"]
    tfidf = crear_vectorizador_tfidf(
        ngram_range=(1, 1),
        min_df=1,
        max_df=1.0,
        sublinear_tf=True,
    )
    matriz = tfidf.fit_transform(corpus).toarray()

    idx_camion = tfidf.vocabulary_["camion"]
    idx_chofer = tfidf.vocabulary_["chofer"]

    # Doc 1: solo camion -> peso 1.0
    assert matriz[0, idx_camion] == pytest.approx(1.0, rel=1e-3)
    assert matriz[0, idx_chofer] == pytest.approx(0.0)

    # Doc 2: ambos terminos, chofer tiene mayor peso discriminativo que camion
    assert matriz[1, idx_camion] == pytest.approx(0.5797, rel=1e-3)
    assert matriz[1, idx_chofer] == pytest.approx(0.8148, rel=1e-3)

    # La suma de los cuadrados en norma L2 debe ser 1.0
    norma_d2 = matriz[1, idx_camion] ** 2 + matriz[1, idx_chofer] ** 2
    assert norma_d2 == pytest.approx(1.0, rel=1e-3)


def test_tfidf_captura_bigramas_clave() -> None:
    """Verifica que el rango ngram_range=(1, 2) capture combinaciones bigrama."""
    corpus = [
        "conductor camion sin experiencia previa",
        "chofer camion con experiencia demostrable",
    ]
    # max_df=1.0 para que 'camion' (presente en 2 de 2 docs = 100%) no se pode en este mini corpus
    tfidf = crear_vectorizador_tfidf(ngram_range=(1, 2), min_df=1, max_df=1.0)
    tfidf.fit(corpus)
    vocab = tfidf.get_feature_names_out()

    # Comprueba la presencia de unigramas y bigramas
    assert "conductor" in vocab
    assert "camion" in vocab
    assert "sin experiencia" in vocab
    assert "conductor camion" in vocab


def test_pipeline_unificado_transformacion_y_sparse_matrix() -> None:
    """Verifica que el Pipeline unificado ejecute preprocesamiento y respete min_df/max_df."""
    pipeline = crear_pipeline_nlp()

    # Mini corpus con terminos repetidos entre 2 y 3 veces para satisfacer min_df=2 y max_df=0.85 (2/4 = 50%)
    ofertas = [
        "Conductor de camión con experiencia en Madrid",
        "Mozo de almacén con experiencia en Madrid",
        "Cocinero para restaurante en Barcelona",
        "Camarero para restaurante en Barcelona",
    ]

    matriz = pipeline.fit_transform(ofertas)

    # Debe ser una matriz dispersa eficiente para ahorrar memoria
    assert issparse(matriz)
    assert matriz.shape[0] == 4
    assert matriz.shape[1] > 0

    # Los componentes deben estar identificados correctamente en el Pipeline
    assert "preprocessor" in pipeline.named_steps
    assert "tfidf" in pipeline.named_steps
    assert isinstance(pipeline.named_steps["preprocessor"], TextPreprocessor)



def test_pipeline_con_clasificador_baseline() -> None:
    """Verifica el flujo completo fit-predict acoplando un clasificador al pipeline."""
    X_train = [
        "Conductor de trailer ruta internacional",
        "Mozo de almacen transporte y logistica",
        "Cocinero jefe de partida en hotel",
        "Camarero de sala y restaurante",
    ]
    y_train = [
        "transporte_logistica",
        "transporte_logistica",
        "hosteleria_gastronomia",
        "hosteleria_gastronomia",
    ]

    # Pipeline con Naive Bayes Multinomial
    pipeline = crear_pipeline_nlp(
        vectorizer=crear_vectorizador_tfidf(min_df=1),
        modelo=MultinomialNB(),
    )

    pipeline.fit(X_train, y_train)

    # Inferencia de prueba
    X_test = ["Chofer de furgoneta para reparto"]
    prediccion = pipeline.predict(X_test)
    assert prediccion[0] in ["transporte_logistica", "hosteleria_gastronomia"]

    # Validacion probabilistica: las probabilidades deben sumar 1.0
    probas = pipeline.predict_proba(X_test)[0]
    assert np.sum(probas) == pytest.approx(1.0, rel=1e-4)


def test_pipeline_serializacion_y_recuperacion_joblib() -> None:
    """Verifica que el Pipeline completo pueda serializarse a bytes y predecir sin pérdida."""
    X = ["Oferta de fontanero urgente", "Conductor de camion cisterna"]
    y = ["construccion_mantenimiento", "transporte_logistica"]

    pipeline_original = crear_pipeline_nlp(
        vectorizer=crear_vectorizador_tfidf(min_df=1),
        modelo=DummyClassifier(strategy="most_frequent"),
    )
    pipeline_original.fit(X, y)

    # Serializar en buffer de memoria con joblib
    buffer = io.BytesIO()
    joblib.dump(pipeline_original, buffer)
    buffer.seek(0)

    # Deserializar
    pipeline_cargado = joblib.load(buffer)
    pred_original = pipeline_original.predict(["Fontanero de tuberias"])
    pred_cargado = pipeline_cargado.predict(["Fontanero de tuberias"])

    assert pred_original[0] == pred_cargado[0]
