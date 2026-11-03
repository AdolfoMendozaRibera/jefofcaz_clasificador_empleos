"""Modulo principal de entrenamiento, evaluacion, analisis de errores y serializacion (Fase 3 - Pasos 3.2 y 3.3).

Ejecuta el pipeline completo de entrenamiento con datos de entrenamiento (train.csv),
evalua a ciegas sobre el conjunto de prueba (test.csv) y genera los 3 artefactos oficiales:
1. artifacts/model.joblib: Pipeline de produccion empaquetado (Preprocesador + TF-IDF + LogisticRegression).
2. artifacts/metrics.json: Metricas completas (F1 Macro, reporte por clase, matriz 5x5 y terminos influyentes).
3. artifacts/errors.csv: Analisis linguistico de las ofertas falladas en test (Punto 5.3 del PDF).
"""

import json
import logging
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.pipeline import Pipeline
import yaml

from src.nlp.pipeline import crear_pipeline_nlp, crear_vectorizador_tfidf
from src.nlp.preprocessing import TextPreprocessor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("model_training")


def cargar_datasets_oficiales(
    ruta_train: Optional[Path] = None,
    ruta_test: Optional[Path] = None,
    ruta_yaml: Optional[Path] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Carga los conjuntos de datos particionados de train.csv y test.csv."""
    raiz = Path(__file__).resolve().parent.parent.parent
    yaml_path = ruta_yaml or (raiz / "params.yaml")

    train_path = ruta_train or (raiz / "data" / "processed" / "train.csv")
    test_path = ruta_test or (raiz / "data" / "processed" / "test.csv")

    if yaml_path.exists():
        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
                d_cfg = cfg.get("data", {})
                if ruta_train is None:
                    train_path = raiz / d_cfg.get("train_path", "data/processed/train.csv")
                if ruta_test is None:
                    test_path = raiz / d_cfg.get("test_path", "data/processed/test.csv")
        except Exception as e:
            logger.warning(f"No se pudo leer params.yaml: {e}. Usando rutas por defecto.")

    if not train_path.exists():
        raise FileNotFoundError(f"Archivo de entrenamiento no encontrado: {train_path}")
    if not test_path.exists():
        raise FileNotFoundError(f"Archivo de prueba no encontrado: {test_path}")

    df_train = pd.read_csv(train_path)
    df_test = pd.read_csv(test_path)

    for col in ["texto", "sector"]:
        if col not in df_train.columns:
            raise ValueError(f"Falta columna '{col}' en train dataset.")
        if col not in df_test.columns:
            raise ValueError(f"Falta columna '{col}' en test dataset.")

    return df_train, df_test


def construir_pipeline_campeon() -> Pipeline:
    """Construye la configuracion campeona identificada cientificamente en la Fase 3.1.

    Preprocesador: Stemming Snowball con conservacion estricta de negaciones.
    Vectorizador: TF-IDF con unigramas y bigramas (1, 2), max_features=4000, sublinear_tf=True.
    Modelo: Regresion Logistica Multinomial (Softmax) con C=2.0 y class_weight='balanced'.
    """
    preprocesador = TextPreprocessor(
        metodo_morfologia="stem",
        usar_stopwords=True,
        proteger_negaciones=True,
    )
    vectorizador = crear_vectorizador_tfidf(
        ngram_range=(1, 2),
        max_features=4000,
        min_df=2,
        max_df=0.85,
        sublinear_tf=True,
    )
    modelo = LogisticRegression(
        C=2.0,
        class_weight="balanced",
        max_iter=1000,
        random_state=42,
    )
    return crear_pipeline_nlp(
        preprocessor=preprocesador,
        vectorizer=vectorizador,
        modelo=modelo,
    )


def clasificar_causa_linguistica(
    texto: str,
    sector_real: str,
    sector_pred: str,
    proba_pred: float,
    proba_real: float,
) -> Tuple[str, str]:
    """Diagnostica la causa linguistica de clasificacion erronea segun el Punto 5.3 del PDF.

    Categorias linguisticas:
    1. Vocabulario cruzado intersectorial (ej. terminos de venta en farmacia, maquinaria en hosteleria).
    2. Rol hibrido o funciones multidisciplinares (ej. conductor repartidor y dependiente).
    3. Descripcion breve con baja senal tematica (< 80 caracteres).
    4. Jerga regional o catalan sin traduccion.
    5. Ambiguedad de frontera tematica.
    """
    t_lower = texto.lower()

    # 1. Jerga o variante linguistica regional (catalan)
    palabras_catalan = ["cerquem", "infermer", "feina", "tasques", "d'acord", "horari", "sou", "treball", "estem", "nostre"]
    if any(p in t_lower for p in palabras_catalan):
        return (
            "jerga_o_variante_regional",
            "Presencia de términos en catalán o variantes regionales no traducidas que dispersan el peso hacia n-gramas atípicos.",
        )

    # 2. Roles hibridos especificos
    if ("mantenimiento" in t_lower or "reparacion" in t_lower) and sector_real == "hosteleria_gastronomia":
        return (
            "rol_hibrido_multidisciplinar",
            "Mantenimiento técnico de maquinaria para hostelería; los términos mecánicos dominan sobre la cocina o servicio.",
        )

    if ("prevencion" in t_lower and "riesgos" in t_lower) and sector_real == "salud_servicios_sociales":
        return (
            "vocabulario_cruzado_intersectorial",
            "Puesto de prevención de riesgos laborales en entorno industrial; el contexto fabril arrastra la predicción hacia construcción/mantenimiento.",
        )

    if ("farmacia" in t_lower or "farmaceutic" in t_lower or "medicamentos" in t_lower) and sector_real == "salud_servicios_sociales":
        return (
            "vocabulario_cruzado_intersectorial",
            "Farmacia comunitaria con atención al público y dispensación; las palabras 'venta', 'caja' y 'atención' arrastran hacia ventas_comercial.",
        )

    if ("conductor" in t_lower or "transporte" in t_lower or "ambulancia" in t_lower) and (sector_real == "salud_servicios_sociales" or sector_pred == "transporte_logistica"):
        return (
            "rol_hibrido_multidisciplinar",
            "Transporte sanitario de pacientes; confluyen vocabulario de conducción/logística y atención sanitaria.",
        )

    # 3. Descripcion muy breve
    if len(texto.strip()) < 70:
        return (
            "descripcion_breve",
            f"La oferta tiene solo {len(texto.strip())} caracteres; la escasa señal textual impide una clara separación vectorial.",
        )

    # 4. Solapamiento general de vocabulario
    if proba_pred - proba_real < 0.25:
        return (
            "frontera_difusa_alta_incertidumbre",
            f"Frontera difusa entre '{sector_real}' y '{sector_pred}'; margen estrecho de probabilidad (pred={proba_pred:.2f} vs real={proba_real:.2f}).",
        )

    return (
        "vocabulario_cruzado_intersectorial",
        f"El léxico empleado en la oferta comparte mayor afinidad ponderada con el sector '{sector_pred}' que con '{sector_real}'.",
    )


def generar_analisis_errores(
    df_test: pd.DataFrame,
    y_pred: np.ndarray,
    y_proba: np.ndarray,
    clases: List[str],
    ruta_salida_csv: Path,
) -> pd.DataFrame:
    """Extrae, clasifica y exporta los casos erroneos en test a artifacts/errors.csv."""
    ruta_salida_csv.parent.mkdir(parents=True, exist_ok=True)
    errores: List[Dict[str, Any]] = []

    clase_a_idx = {c: i for i, c in enumerate(clases)}

    for idx, (real, pred) in enumerate(zip(df_test["sector"], y_pred)):
        if real != pred:
            fila = df_test.iloc[idx]
            p_pred = float(y_proba[idx, clase_a_idx[pred]])
            p_real = float(y_proba[idx, clase_a_idx[real]])

            texto_oferta = str(fila.get("texto", ""))
            causa, explicacion = clasificar_causa_linguistica(
                texto=texto_oferta,
                sector_real=str(real),
                sector_pred=str(pred),
                proba_pred=p_pred,
                proba_real=p_real,
            )

            errores.append({
                "id": str(fila.get("id", f"test_{idx}")),
                "sector_real": real,
                "sector_predicho": pred,
                "probabilidad_predicha": round(p_pred, 4),
                "probabilidad_real": round(p_real, 4),
                "margen_error": round(p_pred - p_real, 4),
                "causa_linguistica": causa,
                "explicacion_linguistica": explicacion,
                "titulo": str(fila.get("titulo", "")),
                "ocupacion": str(fila.get("ocupacion", "")),
                "fragmento_texto": texto_oferta[:250].replace("\n", " "),
            })

    df_errores = pd.DataFrame(errores)
    df_errores.to_csv(ruta_salida_csv, index=False, encoding="utf-8")
    logger.info(f"Análisis de errores guardado en: {ruta_salida_csv} ({len(df_errores)} errores detectados).")
    return df_errores


def extraer_terminos_influyentes(pipeline: Pipeline, top_n: int = 10) -> Dict[str, List[Dict[str, Any]]]:
    """Extrae las palabras y bigramas con mayores coeficientes positivos por clase para interpretabilidad."""
    tfidf = pipeline.named_steps["tfidf"]
    modelo = pipeline.named_steps["model"]

    nombres_features = np.array(tfidf.get_feature_names_out())
    clases = list(pipeline.classes_)

    resultado: Dict[str, List[Dict[str, Any]]] = {}

    for idx, clase in enumerate(clases):
        coeficientes = modelo.coef_[idx]
        indices_top = np.argsort(coeficientes)[::-1][:top_n]

        top_terminos = [
            {
                "termino": nombres_features[i],
                "peso": round(float(coeficientes[i]), 4),
            }
            for i in indices_top
        ]
        resultado[clase] = top_terminos

    return resultado


def entrenar_evaluar_y_serializar(
    ruta_train: Optional[Path] = None,
    ruta_test: Optional[Path] = None,
    ruta_joblib: Optional[Path] = None,
    ruta_metrics: Optional[Path] = None,
    ruta_errors: Optional[Path] = None,
) -> Dict[str, Any]:
    """Flujo completo de produccion: entrenamiento en train, evaluacion en test y exportacion de artefactos."""
    raiz = Path(__file__).resolve().parent.parent.parent
    salida_joblib = ruta_joblib or (raiz / "artifacts" / "model.joblib")
    salida_metrics = ruta_metrics or (raiz / "artifacts" / "metrics.json")
    salida_errors = ruta_errors or (raiz / "artifacts" / "errors.csv")

    salida_joblib.parent.mkdir(parents=True, exist_ok=True)

    # 1. Cargar datos
    logger.info("Cargando datasets oficiales particionados...")
    df_train, df_test = cargar_datasets_oficiales(ruta_train=ruta_train, ruta_test=ruta_test)
    logger.info(f"Train: {len(df_train)} registros | Test: {len(df_test)} registros (evaluación ciega).")

    # 2. Entrenar Pipeline campeón
    pipeline = construir_pipeline_campeon()
    logger.info("Ajustando Pipeline Campeón (TextPreprocessor + TFIDF + LogisticRegression) con train.csv...")
    t0_fit = time.time()
    pipeline.fit(df_train["texto"], df_train["sector"])
    tiempo_entrenamiento = round(time.time() - t0_fit, 2)
    logger.info(f"Entrenamiento completado exitosamente en {tiempo_entrenamiento}s.")

    # 3. Evaluar sobre el conjunto de test
    logger.info("Generando inferencia sobre el conjunto de prueba nunca antes visto (test.csv)...")
    y_test = df_test["sector"].to_numpy()
    y_pred = pipeline.predict(df_test["texto"])
    y_proba = pipeline.predict_proba(df_test["texto"])

    f1_macro_test = float(f1_score(y_test, y_pred, average="macro"))
    clases_ordenadas = list(pipeline.classes_)

    report_dict = classification_report(y_test, y_pred, output_dict=True)
    cm = confusion_matrix(y_test, y_pred, labels=clases_ordenadas)

    logger.info(f"F1-Score Macro oficial en Test: {f1_macro_test:.4f}")

    # 4. Generar analisis de errores (Punto 5.3)
    df_errores = generar_analisis_errores(
        df_test=df_test,
        y_pred=y_pred,
        y_proba=y_proba,
        clases=clases_ordenadas,
        ruta_salida_csv=salida_errors,
    )

    # 5. Extraer terminos mas influyentes
    top_features = extraer_terminos_influyentes(pipeline, top_n=10)

    # 6. Serializar model.joblib con metadatos estructurados
    bundle = {
        "pipeline": pipeline,
        "clases": clases_ordenadas,
        "sectores": clases_ordenadas,
        "modelo": "LogisticRegression",
        "hiperparametros": {"C": 2.0, "class_weight": "balanced", "max_iter": 1000},
        "ngram_range": (1, 2),
        "fecha_entrenamiento": time.strftime("%Y-%m-%d %H:%M:%S"),
        "metricas_test": {
            "f1_macro": round(f1_macro_test, 4),
            "accuracy": round(float(report_dict["accuracy"]), 4),
            "total_test": len(df_test),
            "total_errores": len(df_errores),
        },
    }
    joblib.dump(bundle, salida_joblib)
    logger.info(f"Pipeline serializado exitosamente en: {salida_joblib}")

    # 7. Serializar metrics.json para el Frontend y la API
    metricas_json = {
        "modelo": "LogisticRegression",
        "f1_macro": round(f1_macro_test, 4),
        "accuracy": round(float(report_dict["accuracy"]), 4),
        "total_test": len(df_test),
        "total_errores": len(df_errores),
        "clases": clases_ordenadas,
        "reporte_por_clase": {
            clase: {
                "precision": round(float(report_dict[clase]["precision"]), 4),
                "recall": round(float(report_dict[clase]["recall"]), 4),
                "f1_score": round(float(report_dict[clase]["f1-score"]), 4),
                "support": int(report_dict[clase]["support"]),
            }
            for clase in clases_ordenadas
            if clase in report_dict
        },
        "matriz_confusion": cm.tolist(),
        "terminos_mas_influyentes": top_features,
    }

    with open(salida_metrics, "w", encoding="utf-8") as f:
        json.dump(metricas_json, f, indent=2, ensure_ascii=False)
    logger.info(f"Métricas serializadas en JSON para la API y Frontend en: {salida_metrics}")

    return {
        "f1_macro": f1_macro_test,
        "total_test": len(df_test),
        "total_errores": len(df_errores),
        "report": report_dict,
        "matriz_confusion": cm,
    }


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    res = entrenar_evaluar_y_serializar()
    print("\n" + "=" * 80)
    print(f"REPORTE DE ENTRENAMIENTO OFICIAL (TEST F1-MACRO: {res['f1_macro']:.4f})")
    print(f"Total casos evaluados: {res['total_test']} | Errores analizados: {res['total_errores']}")
    print("=" * 80)
