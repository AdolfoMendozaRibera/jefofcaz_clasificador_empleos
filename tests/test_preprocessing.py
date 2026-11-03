"""Pruebas unitarias para la clase unificada TextPreprocessor y su metodo .explain()."""

import pandas as pd
import pytest
from sklearn.base import clone

from src.nlp.preprocessing import TextPreprocessor


def test_scikit_learn_interface_y_clone() -> None:
    """Verifica que TextPreprocessor cumpla con el protocolo estricto de Scikit-Learn."""
    preprocesador = TextPreprocessor(
        metodo_morfologia="lemma",
        usar_stopwords=True,
        proteger_negaciones=True,
        remover_tildes=True,
        min_token_len=3,
    )

    # 1. clone() de Scikit-Learn debe funcionar sin errores y preservar hiperparametros
    clonado = clone(preprocesador)
    assert clonado.metodo_morfologia == "lemma"
    assert clonado.min_token_len == 3
    assert clonado.usar_stopwords is True

    # 2. fit() debe devolver la propia instancia (self)
    X_muestra = ["Oferta de programador junior", "Cocinero con experiencia"]
    retorno_fit = clonado.fit(X_muestra)
    assert retorno_fit is clonado

    # 3. fit_transform() debe devolver una lista de strings
    salida = clonado.fit_transform(X_muestra)
    assert isinstance(salida, list)
    assert len(salida) == 2
    assert all(isinstance(t, str) for t in salida)


def test_explain_auditoria_completa_con_negacion() -> None:
    """Verifica que el metodo .explain() entregue el desglose forense exacto para la UI."""
    tp = TextPreprocessor(metodo_morfologia="stem")
    texto = "¡URGENTE! Chofer de camión sin experiencia en España."

    resultado = tp.explain(texto)

    # Comprobar la presencia de todas las llaves del contrato
    llaves_esperadas = {
        "original",
        "normalizado",
        "tokens",
        "sin_stopwords",
        "morfologia",
        "final",
        "texto_final",
    }
    assert llaves_esperadas.issubset(set(resultado.keys()))

    # Verificaciones semanticas del pipeline
    assert resultado["original"] == texto
    assert "camion" in resultado["normalizado"]
    assert "españa" in resultado["normalizado"]  # La ñ se conserva

    # "sin" debe estar protegido frente al filtrado de stop words
    assert "sin" in resultado["sin_stopwords"]
    assert "sin" in resultado["final"]

    # "urgente" y "experiencia" deben estar presentes en tokens
    assert "urgente" in resultado["tokens"]
    assert "experiencia" in resultado["tokens"]

    # texto_final debe ser un string no vacio
    assert isinstance(resultado["texto_final"], str)
    assert len(resultado["texto_final"]) > 0


def test_transform_con_pandas_series_y_listas() -> None:
    """Verifica que transform funcione tanto con Listas de Python como con pd.Series."""
    tp = TextPreprocessor(metodo_morfologia="stem")
    datos = [
        "Enfermero para hospital en Madrid",
        "Albañil oficial de primera",
        "Vendedor de tienda comercial",
    ]

    # Entrada como lista nativa
    res_lista = tp.transform(datos)
    assert len(res_lista) == 3
    assert all(isinstance(x, str) for x in res_lista)

    # Entrada como columna de Pandas DataFrame (pd.Series)
    serie = pd.Series(datos)
    res_serie = tp.transform(serie)
    assert res_serie == res_lista


def test_selector_morfologia_stem_lemma_none() -> None:
    """Comprueba el comportamiento ante las tres variantes morfologicas: stem, lemma y none."""
    texto = "Cocinero cocinando en cocina"

    tp_stem = TextPreprocessor(metodo_morfologia="stem")
    tp_lemma = TextPreprocessor(metodo_morfologia="lemma")
    tp_none = TextPreprocessor(metodo_morfologia="none")

    exp_stem = tp_stem.explain(texto)
    exp_lemma = tp_lemma.explain(texto)
    exp_none = tp_none.explain(texto)

    # Stemming aplica recortes heuristicos (ej: 'cocin' o 'cociner')
    assert "cociner" in exp_stem["morfologia"]

    # Lematizacion busca formas canonicas de diccionario (ej: 'cocinar')
    assert "cocinar" in exp_lemma["morfologia"]

    # None no debe modificar los tokens tras el filtrado de stop words
    assert exp_none["morfologia"] == exp_none["sin_stopwords"]


def test_casos_borde_preprocesador() -> None:
    """Verifica la robustez ante entradas nulas, vacias, espacios o solo simbolos."""
    tp = TextPreprocessor()

    casos_vacios = [None, "", "    ", " \t \n ", "??? !!! ---", "12345"]

    for caso in casos_vacios:
        explicacion = tp.explain(caso)
        assert isinstance(explicacion, dict)
        assert explicacion["final"] == [] or all(isinstance(t, str) for t in explicacion["final"])
        assert isinstance(explicacion["texto_final"], str)

    # transform con lista conteniendo vacios y nulos
    salida_transform = tp.transform(["", None, "   "])
    assert salida_transform == ["", "", ""]
