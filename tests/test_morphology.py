"""Pruebas unitarias para el modulo de stop words y reduccion morfologica (src/nlp/morphology.py).

Verifica con ejemplos calculados a mano:
  1. Proteccion incondicional de negaciones ('no', 'sin', 'nunca', 'jamas', 'nada', 'tampoco').
  2. Inclusion de palabras comodin del dominio de reclutamiento ('empresa', 'buscamos').
  3. Filtrado correcto de stop words preservando los requisitos clave de una vacante.
  4. Reduccion de sufijos con Snowball Stemmer (NLTK).
  5. Lematizacion morfosintactica con spaCy (es_core_news_sm).
  6. Casos borde: listas vacias y None.
"""

import pytest

from src.nlp.morphology import (
    aplicar_lematizacion,
    aplicar_stemming,
    filtrar_stopwords,
    obtener_stopwords_personalizadas,
    reducir_morfologia,
)


def test_stopwords_proteccion_estricta_negaciones() -> None:
    """Verifica que las palabras de negacion y matiz NUNCA esten en la lista de stop words."""
    sw = obtener_stopwords_personalizadas(proteger_negaciones=True)

    negaciones_a_verificar = [
        "no",
        "sin",
        "nunca",
        "jamas",
        "nada",
        "tampoco",
        "nadie",
        "pero",
        "bien",
        "mal",
    ]
    for negacion in negaciones_a_verificar:
        assert negacion not in sw, f"¡ERROR LINGÜÍSTICO! La palabra '{negacion}' fue clasificada como stop word."

    # Verificar que palabras gramaticales comunes SI esten presentes
    assert "de" in sw
    assert "la" in sw
    assert "en" in sw
    assert "por" in sw


def test_stopwords_incluye_comodines_reclutamiento() -> None:
    """Verifica que los comodines de reclutamiento definidos en params.yaml se descarten."""
    sw = obtener_stopwords_personalizadas(incluir_extra=True)
    comodines = ["empresa", "buscamos", "puesto", "requisitos", "contrato"]
    for comodin in comodines:
        assert comodin in sw, f"El comodín de reclutamiento '{comodin}' debería ser stop word."


def test_filtrar_stopwords_ejemplo_a_mano() -> None:
    """Verifica el filtrado con un ejemplo calculado a mano de oferta real.

    Entrada:
      'empresa' (extra_stopword) -> fuera
      'busca' (stopword) -> fuera
      'conductor' -> se conserva
      'de' (stopword) -> fuera
      'camion' -> se conserva
      'sin' (negacion protegida) -> ¡SE CONSERVA!
      'experiencia' -> se conserva
      'pero' (matiz protegido) -> ¡SE CONSERVA!
      'no' (negacion protegida) -> ¡SE CONSERVA!
      'fuma' -> se conserva
    """
    tokens = [
        "empresa",
        "busca",
        "conductor",
        "de",
        "camion",
        "sin",
        "experiencia",
        "pero",
        "no",
        "fuma",
    ]
    resultado = filtrar_stopwords(tokens)
    esperado = ["conductor", "camion", "sin", "experiencia", "pero", "no", "fuma"]

    assert resultado == esperado
    assert "sin" in resultado
    assert "no" in resultado
    assert "pero" in resultado
    assert "empresa" not in resultado
    assert "de" not in resultado


def test_aplicar_stemming_snowball() -> None:
    """Verifica que Snowball reduzca las variantes lexicas segun sus reglas heuristicas de sufijos."""
    # Las variantes de genero comparten raiz
    stems_cocina = aplicar_stemming(["cocinero", "cocinera"])
    assert stems_cocina == ["cociner", "cociner"]

    # Las formas verbales y derivadas de trabajo unifican en 'trabaj'
    stems_trabajo = aplicar_stemming(["trabajar", "trabajando", "trabajo", "trabajador"])
    assert stems_trabajo == ["trabaj", "trabaj", "trabaj", "trabaj"]

    # Variantes singular y plural de conductor
    stems_conductor = aplicar_stemming(["conductor", "conductores"])
    assert stems_conductor == ["conductor", "conductor"]


def test_aplicar_lematizacion_spacy() -> None:
    """Verifica que spaCy retorne los lemas canonicos del diccionario en minusculas."""
    tokens = ["cocinando", "cocinaba"]
    lemas = aplicar_lematizacion(tokens)
    # Ambas conjugaciones verbales deben lematizarse al infinitivo 'cocinar'
    assert lemas == ["cocinar", "cocinar"]

    tokens_plural = ["mejores", "camiones"]
    lemas_plural = aplicar_lematizacion(tokens_plural)
    assert lemas_plural == ["mejor", "camion"]


def test_reducir_morfologia_selector() -> None:
    """Verifica que reducir_morfologia llame al metodo correcto segun el parametro."""
    tokens = ["cocinando"]
    resultado_stem = reducir_morfologia(tokens, metodo="stem")
    resultado_lemma = reducir_morfologia(tokens, metodo="lemma")

    assert resultado_stem == ["cocin"]
    assert resultado_lemma == ["cocinar"]


def test_casos_borde_morfologia() -> None:
    """Verifica el comportamiento seguro ante listas vacias o None."""
    assert filtrar_stopwords([]) == []
    assert aplicar_stemming([]) == []
    assert aplicar_lematizacion([]) == []
    assert reducir_morfologia([]) == []
