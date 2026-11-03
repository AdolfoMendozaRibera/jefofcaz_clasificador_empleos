"""Modulo que implementa la clase unificada TextPreprocessor compatible con Scikit-Learn.

Orquesta secuencialmente las estaciones de preprocesamiento de NLP:
1. Limpieza base y normalizacion (src.nlp.cleaning)
2. Tokenizacion con filtrado por longitud (src.nlp.cleaning)
3. Filtrado de stop words con proteccion estricta de negaciones (src.nlp.morphology)
4. Reduccion morfologica: Stemming (Snowball) o Lematizacion (spaCy) (src.nlp.morphology)
5. Metodo .explain() para auditoria visual e inspeccion forense en FastAPI y React
"""

from typing import Any, Dict, Iterable, List, Optional
from sklearn.base import BaseEstimator, TransformerMixin

from src.nlp.cleaning import limpiar_texto_base, tokenizar_palabras
from src.nlp.morphology import (
    filtrar_stopwords,
    obtener_stopwords_personalizadas,
    reducir_morfologia,
)


class TextPreprocessor(BaseEstimator, TransformerMixin):
    """Transformador unificado de texto para Scikit-Learn y produccion.

    Cumple con el contrato estricto de Scikit-Learn (BaseEstimator, TransformerMixin)
    para integrarse directamente en un Pipeline junto con TfidfVectorizer.

    Attributes:
        metodo_morfologia: 'stem' (Snowball), 'lemma' (spaCy) o 'none' (sin reduccion).
        usar_stopwords: Si es True, filtra stop words comunes y comodines de empleo.
        proteger_negaciones: Si es True, asegura que palabras criticas ('no', 'sin') nunca se borren.
        fuente_stopwords: 'spacy' (por defecto) o 'nltk'.
        remover_tildes: Si es True, desacentua conservando intacta la 'ñ'.
        min_token_len: Longitud minima de palabra admitida (descarte de caracteres unicos).
    """

    def __init__(
        self,
        metodo_morfologia: str = "stem",
        usar_stopwords: bool = True,
        proteger_negaciones: bool = True,
        fuente_stopwords: str = "spacy",
        remover_tildes: bool = True,
        min_token_len: int = 2,
    ) -> None:
        # Se asignan directamente sin mutacion para garantizar compatibilidad con clone()
        self.metodo_morfologia = metodo_morfologia
        self.usar_stopwords = usar_stopwords
        self.proteger_negaciones = proteger_negaciones
        self.fuente_stopwords = fuente_stopwords
        self.remover_tildes = remover_tildes
        self.min_token_len = min_token_len

    def fit(self, X: Any = None, y: Any = None) -> "TextPreprocessor":
        """El preprocesador es un transformador sin estado aprendido; retorna self."""
        return self

    def _procesar_uno(self, texto: Optional[str]) -> Dict[str, Any]:
        """Ejecuta el pipeline paso a paso sobre una sola cadena de texto.

        Args:
            texto: Cadena de texto cruda o potencialmente nula.

        Returns:
            Diccionario estructurado con cada etapa intermedia y el texto final.
        """
        # Manejo de casos borde (nulos, vacios o tipos incorrectos)
        if not texto or not isinstance(texto, str) or not texto.strip():
            texto_seguro = "" if texto is None else str(texto)
            return {
                "original": texto_seguro,
                "normalizado": "",
                "tokens": [],
                "sin_stopwords": [],
                "morfologia": [],
                "final": [],
                "texto_final": "",
            }

        # 1. Normalizacion base (minusculas, regex de URLs/emails/elongaciones, tildes con respeto a ñ)
        normalizado = limpiar_texto_base(texto, remover_tildes=self.remover_tildes)

        # 2. Tokenizacion y filtrado por longitud minima
        tokens = tokenizar_palabras(normalizado, min_length=self.min_token_len)

        # 3. Filtrado de stop words con blindaje de negaciones
        if self.usar_stopwords:
            sw = obtener_stopwords_personalizadas(
                fuente=self.fuente_stopwords,
                proteger_negaciones=self.proteger_negaciones,
            )
            sin_stopwords = filtrar_stopwords(tokens, stopwords=sw)
        else:
            sin_stopwords = list(tokens)

        # 4. Reduccion morfologica
        if self.metodo_morfologia and self.metodo_morfologia.lower() != "none":
            morfologia = reducir_morfologia(sin_stopwords, metodo=self.metodo_morfologia)
        else:
            morfologia = list(sin_stopwords)

        final = morfologia
        texto_final = " ".join(final)

        return {
            "original": texto,
            "normalizado": normalizado,
            "tokens": tokens,
            "sin_stopwords": sin_stopwords,
            "morfologia": morfologia,
            "final": final,
            "texto_final": texto_final,
        }

    def transform(self, X: Iterable[Any]) -> List[str]:
        """Aplica la transformacion completa a una coleccion de textos.

        Args:
            X: Iterable con documentos de texto (listas, pandas.Series, etc.).

        Returns:
            Lista de cadenas de texto procesadas, listas para consumir por TfidfVectorizer.
        """
        if X is None:
            return []

        return [self._procesar_uno(doc)["texto_final"] for doc in X]

    def explain(self, texto: Optional[str]) -> Dict[str, Any]:
        """Inspecciona y desglosa cada estacion de NLP para una sola entrada.

        Este metodo es el contrato oficial consumido por:
        - El endpoint 'POST /api/predict' en FastAPI.
        - El panel de auditoria visual paso a paso en React.

        Args:
            texto: Cadena de texto cruda ingresada por el usuario.

        Returns:
            Diccionario con 'original', 'normalizado', 'tokens', 'sin_stopwords',
            'morfologia', 'final' y 'texto_final'.

        Example:
            >>> tp = TextPreprocessor(metodo_morfologia="stem")
            >>> salida = tp.explain("Chofer para camión sin experiencia")
            >>> salida["sin_stopwords"]
            ['chofer', 'camion', 'sin', 'experiencia']
        """
        return self._procesar_uno(texto)
