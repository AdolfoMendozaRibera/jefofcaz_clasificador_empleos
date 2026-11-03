"""Modulo de experimentos y validacion cruzada comparativa (Fase 3 - Paso 3.1).

Ejecuta una matriz sistematica de experimentos con StratifiedKFold (k=5)
evaluando con la metrica oficial F1-Score Macro para comparar:
1. Linea base (DummyClassifier) frente a modelos de Machine Learning.
2. Naive Bayes Multinomial vs. Regresion Logistica (Softmax).
3. Efecto de N-gramas: Unigramas (1, 1) vs. Unigramas + Bigramas (1, 2).
4. Efecto de hiperparametros: alpha en Naive Bayes, C y class_weight en Regresion Logistica.
5. Efecto de reduccion morfologica: Stemming (Snowball) vs. Lematizacion (spaCy).
6. Efecto de conservacion estricta de negaciones.

Garantiza CERO FUGA DE INFORMACION (Data Leakage):
El vocabulario TF-IDF y el modelo se ajustan unica y exclusivamente en los pliegues de entrenamiento.
"""

import logging
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedKFold
from sklearn.naive_bayes import MultinomialNB
import yaml

from src.nlp.pipeline import crear_vectorizador_tfidf
from src.nlp.preprocessing import TextPreprocessor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("experiments")


def cargar_datos_entrenamiento(ruta_train: Optional[Path] = None, ruta_yaml: Optional[Path] = None) -> Tuple[pd.Series, pd.Series]:
    """Carga los textos y etiquetas de entrenamiento desde data/processed/train.csv."""
    if ruta_train is not None and ruta_train.exists():
        ruta = ruta_train
    else:
        raiz = Path(__file__).resolve().parent.parent.parent
        yaml_path = ruta_yaml or (raiz / "params.yaml")
        if yaml_path.exists():
            with open(yaml_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
                rel_path = cfg.get("data", {}).get("train_path", "data/processed/train.csv")
                ruta = raiz / rel_path
        else:
            ruta = raiz / "data" / "processed" / "train.csv"

    if not ruta.exists():
        raise FileNotFoundError(f"No se encontro el archivo de entrenamiento en: {ruta}")

    df = pd.read_csv(ruta)
    if "texto" not in df.columns or "sector" not in df.columns:
        raise ValueError(f"El dataset en {ruta} debe contener las columnas 'texto' y 'sector'.")

    return df["texto"], df["sector"]


def evaluar_pliegues_cv(
    textos_procesados: List[str],
    etiquetas: pd.Series,
    vectorizer_config: Dict[str, Any],
    modelo: Any,
    cv: StratifiedKFold,
) -> Tuple[float, float, float, float]:
    """Evalua un modelo con validacion cruzada estratificada garantizando cero fuga.

    El vectorizador TF-IDF se ajusta (.fit_transform) UNICAMENTE en el pliegue de entrenamiento
    de cada iteracion y luego transforma (.transform) el pliegue de validacion.

    Args:
        textos_procesados: Lista de textos previamente normalizados por TextPreprocessor.
        etiquetas: Serie de pandas con las categorias de destino.
        vectorizer_config: Diccionario con parametros para crear_vectorizador_tfidf.
        modelo: Estimador de Scikit-Learn listo para fit/predict.
        cv: Objeto StratifiedKFold configurado.

    Returns:
        Tupla con (f1_macro_mean, f1_macro_std, acc_mean, acc_std).
    """
    f1_scores: List[float] = []
    acc_scores: List[float] = []

    y_arr = etiquetas.to_numpy()

    for train_idx, val_idx in cv.split(textos_procesados, y_arr):
        # 1. Separar particion del fold
        X_tr = [textos_procesados[i] for i in train_idx]
        y_tr = y_arr[train_idx]

        X_val = [textos_procesados[i] for i in val_idx]
        y_val = y_arr[val_idx]

        # 2. Vectorizar solo con entrenamiento (Cero Data Leakage)
        tfidf = crear_vectorizador_tfidf(**vectorizer_config)
        X_tr_vec = tfidf.fit_transform(X_tr)
        X_val_vec = tfidf.transform(X_val)

        # 3. Ajustar estimador
        modelo_fold = getattr(modelo, "clone", None)
        if callable(modelo_fold):
            estimador = modelo.clone()
        else:
            from sklearn.base import clone
            estimador = clone(modelo)

        estimador.fit(X_tr_vec, y_tr)

        # 4. Inferencia y evaluacion del fold
        y_pred = estimador.predict(X_val_vec)
        f1_scores.append(float(f1_score(y_val, y_pred, average="macro")))
        acc_scores.append(float(accuracy_score(y_val, y_pred)))

    s_f1 = pd.Series(f1_scores)
    s_acc = pd.Series(acc_scores)
    return float(s_f1.mean()), float(s_f1.std()), float(s_acc.mean()), float(s_acc.std())


def ejecutar_matriz_experimentos(
    ruta_train: Optional[Path] = None,
    ruta_salida_csv: Optional[Path] = None,
    ruta_yaml: Optional[Path] = None,
    incluir_lematizacion: bool = True,
    n_splits: int = 5,
) -> pd.DataFrame:
    """Ejecuta la suite cientifica de experimentos y exporta la tabla de resultados.

    Args:
        ruta_train: Ruta alternativa a train.csv.
        ruta_salida_csv: Ruta del CSV de salida (por defecto artifacts/experiments.csv).
        ruta_yaml: Ruta de params.yaml.
        incluir_lematizacion: Si es True, incluye el experimento comparativo con spaCy.
        n_splits: Numero de pliegues para StratifiedKFold (por defecto 5).

    Returns:
        DataFrame con todos los experimentos ordenados por F1-Score Macro descendente.
    """
    raiz = Path(__file__).resolve().parent.parent.parent
    salida_csv = ruta_salida_csv or (raiz / "artifacts" / "experiments.csv")
    salida_csv.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Cargando datos de entrenamiento para la validacion cruzada...")
    textos_raw, etiquetas = cargar_datos_entrenamiento(ruta_train=ruta_train, ruta_yaml=ruta_yaml)
    logger.info(f"Datos cargados: {len(textos_raw)} ofertas laborales en 5 sectores.")

    # 1. Preprocesar representaciones base (Cero redundancia en transformaciones estaticas)
    logger.info("Normalizando textos base con Stemming (Snowball)...")
    tp_stem = TextPreprocessor(metodo_morfologia="stem", usar_stopwords=True, proteger_negaciones=True)
    textos_stem = tp_stem.transform(textos_raw)

    logger.info("Normalizando textos sin proteccion de negaciones (experimento de ablacion)...")
    tp_no_neg = TextPreprocessor(metodo_morfologia="stem", usar_stopwords=True, proteger_negaciones=False)
    textos_no_neg = tp_no_neg.transform(textos_raw)

    textos_lemma = None
    if incluir_lematizacion:
        logger.info("Normalizando textos con Lematizacion (spaCy es_core_news_sm)...")
        t0_lem = time.time()
        tp_lemma = TextPreprocessor(metodo_morfologia="lemma", usar_stopwords=True, proteger_negaciones=True)
        textos_lemma = tp_lemma.transform(textos_raw)
        logger.info(f"Lematizacion completada en {time.time() - t0_lem:.2f}s.")

    # 2. Definir pliegues estratificados
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)

    # 3. Definicion de la matriz de experimentos
    definiciones_exp: List[Dict[str, Any]] = [
        # Linea Base (Baseline)
        {
            "id": 1,
            "modelo": "DummyClassifier",
            "descripcion": "Línea base (clase más frecuente)",
            "estimador": DummyClassifier(strategy="most_frequent"),
            "corpus": textos_stem,
            "morfologia": "stem",
            "stop_words": "ajustadas_con_negacion",
            "ngram_range": (1, 1),
            "hiperparametros": "strategy='most_frequent'",
        },
        # Naive Bayes con variacion de alpha y unigramas vs bigramas
        {
            "id": 2,
            "modelo": "MultinomialNB",
            "descripcion": "Naive Bayes (alpha=1.0, unigramas)",
            "estimador": MultinomialNB(alpha=1.0),
            "corpus": textos_stem,
            "morfologia": "stem",
            "stop_words": "ajustadas_con_negacion",
            "ngram_range": (1, 1),
            "hiperparametros": "alpha=1.0",
        },
        {
            "id": 3,
            "modelo": "MultinomialNB",
            "descripcion": "Naive Bayes (alpha=0.5, unigramas)",
            "estimador": MultinomialNB(alpha=0.5),
            "corpus": textos_stem,
            "morfologia": "stem",
            "stop_words": "ajustadas_con_negacion",
            "ngram_range": (1, 1),
            "hiperparametros": "alpha=0.5",
        },
        {
            "id": 4,
            "modelo": "MultinomialNB",
            "descripcion": "Naive Bayes (alpha=0.1, unigramas)",
            "estimador": MultinomialNB(alpha=0.1),
            "corpus": textos_stem,
            "morfologia": "stem",
            "stop_words": "ajustadas_con_negacion",
            "ngram_range": (1, 1),
            "hiperparametros": "alpha=0.1",
        },
        {
            "id": 5,
            "modelo": "MultinomialNB",
            "descripcion": "Naive Bayes (alpha=0.5, bigramas)",
            "estimador": MultinomialNB(alpha=0.5),
            "corpus": textos_stem,
            "morfologia": "stem",
            "stop_words": "ajustadas_con_negacion",
            "ngram_range": (1, 2),
            "hiperparametros": "alpha=0.5",
        },
        # Regresion Logistica: exploracion de C y unigramas vs bigramas
        {
            "id": 6,
            "modelo": "LogisticRegression",
            "descripcion": "Regresión Logística (C=0.5, balanced, unigramas)",
            "estimador": LogisticRegression(C=0.5, class_weight="balanced", max_iter=1000, random_state=42),
            "corpus": textos_stem,
            "morfologia": "stem",
            "stop_words": "ajustadas_con_negacion",
            "ngram_range": (1, 1),
            "hiperparametros": "C=0.5, class_weight='balanced'",
        },
        {
            "id": 7,
            "modelo": "LogisticRegression",
            "descripcion": "Regresión Logística (C=1.0, balanced, unigramas)",
            "estimador": LogisticRegression(C=1.0, class_weight="balanced", max_iter=1000, random_state=42),
            "corpus": textos_stem,
            "morfologia": "stem",
            "stop_words": "ajustadas_con_negacion",
            "ngram_range": (1, 1),
            "hiperparametros": "C=1.0, class_weight='balanced'",
        },
        {
            "id": 8,
            "modelo": "LogisticRegression",
            "descripcion": "Regresión Logística (C=2.0, balanced, unigramas)",
            "estimador": LogisticRegression(C=2.0, class_weight="balanced", max_iter=1000, random_state=42),
            "corpus": textos_stem,
            "morfologia": "stem",
            "stop_words": "ajustadas_con_negacion",
            "ngram_range": (1, 1),
            "hiperparametros": "C=2.0, class_weight='balanced'",
        },
        {
            "id": 9,
            "modelo": "LogisticRegression",
            "descripcion": "Regresión Logística (C=2.0, balanced, bigramas) [CANDIDATO CAMPEÓN]",
            "estimador": LogisticRegression(C=2.0, class_weight="balanced", max_iter=1000, random_state=42),
            "corpus": textos_stem,
            "morfologia": "stem",
            "stop_words": "ajustadas_con_negacion",
            "ngram_range": (1, 2),
            "hiperparametros": "C=2.0, class_weight='balanced'",
        },
        {
            "id": 10,
            "modelo": "LogisticRegression",
            "descripcion": "Regresión Logística (C=5.0, balanced, bigramas)",
            "estimador": LogisticRegression(C=5.0, class_weight="balanced", max_iter=1000, random_state=42),
            "corpus": textos_stem,
            "morfologia": "stem",
            "stop_words": "ajustadas_con_negacion",
            "ngram_range": (1, 2),
            "hiperparametros": "C=5.0, class_weight='balanced'",
        },
        # Ablacion 1: Impacto de class_weight='balanced' (desbalance de clases)
        {
            "id": 11,
            "modelo": "LogisticRegression",
            "descripcion": "Regresión Logística (C=2.0, SIN balanced, bigramas)",
            "estimador": LogisticRegression(C=2.0, class_weight=None, max_iter=1000, random_state=42),
            "corpus": textos_stem,
            "morfologia": "stem",
            "stop_words": "ajustadas_con_negacion",
            "ngram_range": (1, 2),
            "hiperparametros": "C=2.0, class_weight=None",
        },
        # Ablacion 2: Impacto de la conservacion estricta de negaciones
        {
            "id": 12,
            "modelo": "LogisticRegression",
            "descripcion": "Regresión Logística (C=2.0, SIN proteccion negaciones)",
            "estimador": LogisticRegression(C=2.0, class_weight="balanced", max_iter=1000, random_state=42),
            "corpus": textos_no_neg,
            "morfologia": "stem",
            "stop_words": "estandar_sin_negacion",
            "ngram_range": (1, 2),
            "hiperparametros": "C=2.0, class_weight='balanced'",
        },
    ]

    # Ablacion 3: Comparacion morfologica Stemming vs Lematizacion
    if textos_lemma is not None:
        definiciones_exp.append({
            "id": 13,
            "modelo": "LogisticRegression",
            "descripcion": "Regresión Logística (C=2.0, Lematización spaCy, bigramas)",
            "estimador": LogisticRegression(C=2.0, class_weight="balanced", max_iter=1000, random_state=42),
            "corpus": textos_lemma,
            "morfologia": "lemma",
            "stop_words": "ajustadas_con_negacion",
            "ngram_range": (1, 2),
            "hiperparametros": "C=2.0, class_weight='balanced'",
        })

    # 4. Ejecutar cada experimento
    resultados: List[Dict[str, Any]] = []

    for exp in definiciones_exp:
        logger.info(f"Ejecutando Exp #{exp['id']}: {exp['descripcion']}...")
        t_inicio = time.time()

        vec_cfg = {
            "ngram_range": exp["ngram_range"],
            "max_features": 4000,
            "min_df": 2,
            "max_df": 0.85,
            "sublinear_tf": True,
        }

        f1_m, f1_s, acc_m, acc_s = evaluar_pliegues_cv(
            textos_procesados=exp["corpus"],
            etiquetas=etiquetas,
            vectorizer_config=vec_cfg,
            modelo=exp["estimador"],
            cv=cv,
        )

        t_duracion = round(time.time() - t_inicio, 2)

        resultados.append({
            "id": exp["id"],
            "modelo": exp["modelo"],
            "descripcion": exp["descripcion"],
            "hiperparametros": exp["hiperparametros"],
            "morfologia": exp["morfologia"],
            "stop_words": exp["stop_words"],
            "ngram_range": f"{exp['ngram_range'][0]}-{exp['ngram_range'][1]}",
            "f1_macro_media": round(f1_m, 4),
            "f1_macro_std": round(f1_s, 4),
            "accuracy_media": round(acc_m, 4),
            "accuracy_std": round(acc_s, 4),
            "tiempo_segundos": t_duracion,
        })

    # 5. Generar DataFrame ordenado por F1-Score Macro descendente
    df_res = pd.DataFrame(resultados).sort_values(by="f1_macro_media", ascending=False).reset_index(drop=True)
    df_res.to_csv(salida_csv, index=False, encoding="utf-8")
    logger.info(f"Resultados guardados exitosamente en: {salida_csv}")

    return df_res


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    df_resultados = ejecutar_matriz_experimentos()
    print("\n" + "=" * 90)
    print("TABLA OFICIAL DE EXPERIMENTOS (VALIDACION CRUZADA K=5)")
    print("=" * 90)
    columnas_mostrar = ["id", "modelo", "morfologia", "ngram_range", "hiperparametros", "f1_macro_media", "f1_macro_std", "tiempo_segundos"]
    print(df_resultados[columnas_mostrar].to_markdown(index=False))
    print("=" * 90)
