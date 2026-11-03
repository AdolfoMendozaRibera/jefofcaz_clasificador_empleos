"""Modulo para la configuracion y ensamblado del Pipeline de NLP en Scikit-Learn.

Provee funciones de construccion para:
1. TfidfVectorizer configurado segun params.yaml (n-gramas (1, 2), max_features, sublinear_tf).
2. Pipeline base de Scikit-Learn acoplando TextPreprocessor, TfidfVectorizer y modelos de clasificacion.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union
import yaml
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline

from src.nlp.preprocessing import TextPreprocessor

logger = logging.getLogger("nlp_pipeline")


def cargar_config_tfidf(ruta_yaml: Optional[Path] = None) -> Dict[str, Any]:
    """Carga los parametros de TF-IDF desde params.yaml de forma segura."""
    ruta = ruta_yaml or (Path(__file__).resolve().parent.parent.parent / "params.yaml")
    defaults: Dict[str, Any] = {
        "max_features": 4000,
        "min_df": 2,
        "max_df": 0.85,
        "sublinear_tf": True,
        "ngram_range": (1, 2),
    }

    if not ruta.exists():
        return defaults

    try:
        with open(ruta, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
            tfidf_cfg = cfg.get("tfidf", {})

            # Si ngram_range no esta en 'tfidf', buscar en 'experiments.ngram_ranges'
            ngram_raw = tfidf_cfg.get("ngram_range")
            if ngram_raw is None:
                exp_ngrams = cfg.get("experiments", {}).get("ngram_ranges", [[1, 2]])
                ngram_raw = exp_ngrams[-1] if exp_ngrams else [1, 2]

            return {
                "max_features": int(tfidf_cfg.get("max_features", defaults["max_features"])),
                "min_df": int(tfidf_cfg.get("min_df", defaults["min_df"])),
                "max_df": float(tfidf_cfg.get("max_df", defaults["max_df"])),
                "sublinear_tf": bool(tfidf_cfg.get("sublinear_tf", defaults["sublinear_tf"])),
                "ngram_range": tuple(ngram_raw),
            }
    except Exception as e:
        logger.warning(f"Error al leer configuracion TF-IDF de params.yaml: {e}. Usando valores por defecto.")
        return defaults


def crear_vectorizador_tfidf(
    max_features: Optional[int] = None,
    min_df: Optional[Union[int, float]] = None,
    max_df: Optional[float] = None,
    sublinear_tf: Optional[bool] = None,
    ngram_range: Optional[Tuple[int, int]] = None,
) -> TfidfVectorizer:
    """Instancia y configura un TfidfVectorizer alineado con el TextPreprocessor.

    Usa lowercase=False y token_pattern=r'\\S+' debido a que el texto entrante ya
    fue normalizado y segmentado en palabras atómicas separadas por espacios.

    Args:
        max_features: Límite del vocabulario. Si es None, lee de params.yaml.
        min_df: Frecuencia mínima de documento. Si es None, lee de params.yaml.
        max_df: Frecuencia máxima de documento. Si es None, lee de params.yaml.
        sublinear_tf: Escalamiento logarítmico (1 + log(TF)). Si es None, lee de params.yaml.
        ngram_range: Rango de N-gramas (ej. (1, 2)). Si es None, lee de params.yaml.

    Returns:
        Instancia de TfidfVectorizer lista para ajustar y transformar.
    """
    cfg = cargar_config_tfidf()

    return TfidfVectorizer(
        lowercase=False,
        token_pattern=r"\S+",
        max_features=max_features if max_features is not None else cfg["max_features"],
        min_df=min_df if min_df is not None else cfg["min_df"],
        max_df=max_df if max_df is not None else cfg["max_df"],
        sublinear_tf=sublinear_tf if sublinear_tf is not None else cfg["sublinear_tf"],
        ngram_range=ngram_range if ngram_range is not None else cfg["ngram_range"],
    )


def crear_pipeline_nlp(
    preprocessor: Optional[TextPreprocessor] = None,
    vectorizer: Optional[TfidfVectorizer] = None,
    modelo: Optional[Any] = None,
) -> Pipeline:
    """Construye un Pipeline oficial de Scikit-Learn unificando las etapas del sistema.

    Args:
        preprocessor: Instancia de TextPreprocessor. Si es None, se crea con defaults.
        vectorizer: Instancia de TfidfVectorizer. Si es None, se crea con defaults.
        modelo: Estimador/Clasificador final de Scikit-Learn (opcional).

    Returns:
        Objeto Pipeline acoplado, listo para fit(), transform() o predict().
    """
    pasos = [
        ("preprocessor", preprocessor or TextPreprocessor()),
        ("tfidf", vectorizer or crear_vectorizador_tfidf()),
    ]

    if modelo is not None:
        pasos.append(("model", modelo))

    return Pipeline(pasos)
