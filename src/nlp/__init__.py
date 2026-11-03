"""Modulo de pipeline y preprocesamiento de NLP."""

from src.nlp.cleaning import desacentuar_conservando_ene, limpiar_texto_base, tokenizar_palabras
from src.nlp.morphology import (
    filtrar_stopwords,
    obtener_stopwords_personalizadas,
    reducir_morfologia,
)
from src.nlp.preprocessing import TextPreprocessor

__all__ = [
    "desacentuar_conservando_ene",
    "limpiar_texto_base",
    "tokenizar_palabras",
    "filtrar_stopwords",
    "obtener_stopwords_personalizadas",
    "reducir_morfologia",
    "TextPreprocessor",
]
