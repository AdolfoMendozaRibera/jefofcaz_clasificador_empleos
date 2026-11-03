"""Modulo para la gestion de Stop Words con proteccion de negaciones y reduccion morfologica.

Implementa las estaciones 3 y 4 del pipeline de NLP:
1. Stop Words: Carga stop words en español (NLTK/spaCy), incorpora comodines de reclutamiento
   definidos en params.yaml (extra_stopwords) y blinda estrictamente las negaciones (keep_words).
2. Reduccion Morfologica:
   - Stemming: Algoritmo Snowball Stemmer (NLTK) rapido y heuristico.
   - Lematizacion: Modelo morfologico industrial de spaCy (es_core_news_sm).
"""

from functools import lru_cache
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from src.nlp.cleaning import desacentuar_conservando_ene

logger = logging.getLogger("morphology")

# Palabras de negacion y matiz obligatorias que NUNCA deben removerse
NEGACIONES_BLINDADAS: Set[str] = {
    "no",
    "ni",
    "nunca",
    "jamas",
    "jamás",
    "nada",
    "tampoco",
    "sin",
    "nadie",
    "bien",
    "mal",
    "bueno",
    "buena",
    "muy",
    "poco",
    "mas",
    "más",
    "menos",
    "pero",
}


def cargar_config_nlp(ruta_yaml: Optional[Path] = None) -> Dict[str, Any]:
    """Carga parametros de NLP desde params.yaml de forma segura."""
    ruta = ruta_yaml or (Path(__file__).resolve().parent.parent.parent / "params.yaml")
    if not ruta.exists():
        return {}

    try:
        import yaml

        with open(ruta, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning(f"No se pudo cargar params.yaml: {e}. Usando valores por defecto.")
        return {}


@lru_cache(maxsize=1)
def obtener_stemmer_nltk():
    """Retorna una instancia singleton de SnowballStemmer para español."""
    try:
        from nltk.stem import SnowballStemmer

        return SnowballStemmer("spanish")
    except ImportError as e:
        logger.error("NLTK no esta instalado en el entorno virtual.")
        raise RuntimeError("Se requiere nltk para ejecutar Stemming.") from e


@lru_cache(maxsize=1)
def obtener_spacy_nlp():
    """Retorna una instancia singleton del modelo en español de spaCy."""
    try:
        import spacy

        try:
            return spacy.load("es_core_news_sm", disable=["ner", "parser"])
        except OSError:
            logger.warning("es_core_news_sm no encontrado, intentando carga base de spacy 'es'.")
            return spacy.blank("es")
    except ImportError as e:
        logger.error("spaCy no esta instalado en el entorno virtual.")
        raise RuntimeError("Se requiere spacy para ejecutar Lematizacion.") from e


@lru_cache(maxsize=4)
def obtener_stopwords_personalizadas(
    fuente: str = "spacy",
    incluir_extra: bool = True,
    proteger_negaciones: bool = True,
) -> Set[str]:
    """Construye el conjunto oficial de stop words alineado con la normalizacion.

    Args:
        fuente: 'spacy' (por defecto) o 'nltk'.
        incluir_extra: Si es True, añade los comodines de empleo de params.yaml.
        proteger_negaciones: Si es True, asegura que ninguna palabra de keep_words sea eliminada.

    Returns:
        Conjunto de stop words desacentuadas listas para comparar con tokens limpios.
    """
    stopwords_base: Set[str] = set()

    if fuente == "spacy":
        try:
            from spacy.lang.es.stop_words import STOP_WORDS

            stopwords_base = set(STOP_WORDS)
        except ImportError:
            stopwords_base = set()
    elif fuente == "nltk":
        try:
            from nltk.corpus import stopwords

            stopwords_base = set(stopwords.words("spanish"))
        except (ImportError, LookupError):
            stopwords_base = set()

    # Si ambas fallan, proveer lista basica minima de contingencia
    if not stopwords_base:
        stopwords_base = {
            "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del",
            "en", "para", "por", "con", "este", "esta", "estos", "estas", "su",
            "sus", "al", "como", "que", "se", "es", "son", "fue", "ser",
        }

    # Desacentuar las stop words para que coincidan con los tokens normalizados
    stopwords_normalizadas = {desacentuar_conservando_ene(w.lower()) for w in stopwords_base}

    # Incorporar comodines de empleo de params.yaml
    cfg = cargar_config_nlp()
    nlp_cfg = cfg.get("nlp", {})

    if incluir_extra:
        extra = nlp_cfg.get("extra_stopwords", [])
        for w in extra:
            if isinstance(w, str):
                stopwords_normalizadas.add(desacentuar_conservando_ene(w.lower()))

    # Proteger estrictamente las negaciones y palabras de matiz
    if proteger_negaciones:
        palabras_protegidas = set(NEGACIONES_BLINDADAS)
        keep_yaml = nlp_cfg.get("keep_words", [])
        for k in keep_yaml:
            if isinstance(k, str):
                palabras_protegidas.add(desacentuar_conservando_ene(k.lower()))

        # Remover las palabras protegidas del conjunto de stop words
        stopwords_normalizadas = stopwords_normalizadas - palabras_protegidas

    return stopwords_normalizadas


def filtrar_stopwords(
    tokens: List[str],
    stopwords: Optional[Set[str]] = None,
) -> List[str]:
    """Filtra los tokens descartando palabras vacias pero preservando negaciones.

    Args:
        tokens: Lista de tokens limpios.
        stopwords: Conjunto de stop words. Si es None, carga las personalizadas por defecto.

    Returns:
        Lista de tokens depurados sin palabras vacias.

    Example:
        >>> filtrar_stopwords(["conductor", "de", "camion", "sin", "experiencia"])
        ['conductor', 'camion', 'sin', 'experiencia']
    """
    if not tokens:
        return []

    sw = stopwords if stopwords is not None else obtener_stopwords_personalizadas()
    return [t for t in tokens if t not in sw]


def aplicar_stemming(tokens: List[str]) -> List[str]:
    """Aplica el algoritmo morfológico Snowball Stemmer (NLTK) a una lista de tokens.

    Args:
        tokens: Lista de palabras a procesar.

    Returns:
        Lista de raíces morfológicas (stems).

    Example:
        >>> aplicar_stemming(["cocinero", "cocinando", "cocina"])
        ['cocin', 'cocin', 'cocin']
    """
    if not tokens:
        return []

    stemmer = obtener_stemmer_nltk()
    return [stemmer.stem(t) for t in tokens]


def aplicar_lematizacion(tokens: List[str]) -> List[str]:
    """Aplica lematización morfosintáctica industrial utilizando spaCy.

    Args:
        tokens: Lista de palabras a procesar.

    Returns:
        Lista de lemas canónicos de diccionario.

    Example:
        >>> aplicar_lematizacion(["cocinero", "cocinando"])
        ['cocinero', 'cocinar']
    """
    if not tokens:
        return []

    nlp = obtener_spacy_nlp()
    doc = nlp(" ".join(tokens))
    lemas: List[str] = []

    for token in doc:
        lema = token.lemma_.lower().strip()
        # Desacentuar el lema para mantener consistencia con el vectorizador
        lema_limpio = desacentuar_conservando_ene(lema) if lema else token.text.lower()
        if lema_limpio:
            lemas.append(lema_limpio)

    return lemas


def reducir_morfologia(tokens: List[str], metodo: str = "stem") -> List[str]:
    """Aplica reducción morfológica seleccionando entre 'stem' o 'lemma'.

    Args:
        tokens: Lista de tokens a transformar.
        metodo: 'stem' para Snowball Stemmer o 'lemma' para spaCy.

    Returns:
        Lista de tokens reducidos según la estrategia elegida.
    """
    if not tokens:
        return []

    metodo_normalizado = metodo.lower().strip()
    if metodo_normalizado == "lemma":
        return aplicar_lematizacion(tokens)
    return aplicar_stemming(tokens)
