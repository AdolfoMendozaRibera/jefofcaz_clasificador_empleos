"""Capa de servicio y orquestación del modelo de Machine Learning (Fase 4 - Paso 4.2).

Implementa la clase `ModelService` encargada de:
1. Cargar el pipeline serializado (`artifacts/model.joblib`) una sola vez en memoria (RAM).
2. Ejecutar inferencias individuales y extraer la explicabilidad de NLP paso a paso (`explain`).
3. Procesar lotes masivos de ofertas mediante archivos CSV de forma vectorizada.
4. Exponer las métricas oficiales y matriz de confusión cargadas desde `artifacts/metrics.json`.
"""

from __future__ import annotations

import io
import json
import logging
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
import yaml

from api.schemas import SECTORES_VALIDOS

logger = logging.getLogger("api_service")


class ModelService:
    """Servicio de orquestación para la inferencia del pipeline de clasificación de empleos.

    Sigue el patrón Singleton/Service Layer para desacoplar el transporte HTTP
    de la lógica del modelo de Machine Learning.
    """

    def __init__(
        self,
        ruta_modelo: Optional[Path | str] = None,
        ruta_metricas: Optional[Path | str] = None,
    ) -> None:
        """Inicializa las rutas del artefacto y el estado de la memoria.

        Parameters
        ----------
        ruta_modelo : Optional[Path | str]
            Ruta física al archivo bundle `model.joblib`.
        ruta_metricas : Optional[Path | str]
            Ruta física al archivo `metrics.json`.
        """
        raiz = Path(__file__).resolve().parent.parent
        self.ruta_modelo = Path(ruta_modelo) if ruta_modelo else (raiz / "artifacts" / "model.joblib")
        self.ruta_metricas = Path(ruta_metricas) if ruta_metricas else (raiz / "artifacts" / "metrics.json")

        self.bundle: Optional[Dict[str, Any]] = None
        self.pipeline: Optional[Pipeline] = None
        self.clases: List[str] = list(SECTORES_VALIDOS)
        self.metricas: Optional[Dict[str, Any]] = None
        self.loaded: bool = False

    def load(self) -> None:
        """Carga en memoria RAM el artefacto joblib y las métricas oficiales.

        Este método se invoca exclusivamente durante el ciclo de vida `lifespan` de FastAPI
        al arrancar el servidor web, garantizando que el modelo se cargue una sola vez.

        Raises
        ------
        FileNotFoundError
            Si `artifacts/model.joblib` no existe en disco.
        """
        if not self.ruta_modelo.exists():
            msg = (
                f"No se encontró el artefacto del modelo en: '{self.ruta_modelo}'. "
                "Ejecute 'python -m src.models.train' para generarlo."
            )
            logger.error(msg)
            raise FileNotFoundError(msg)

        logger.info(f"Cargando bundle del modelo desde '{self.ruta_modelo}'...")
        tiempo_inicio = time.perf_counter()

        bundle_cargado = joblib.load(self.ruta_modelo)
        if not isinstance(bundle_cargado, dict) or "pipeline" not in bundle_cargado:
            raise ValueError("El archivo joblib no contiene un bundle estructurado válido con clave 'pipeline'.")

        self.bundle = bundle_cargado
        self.pipeline = bundle_cargado["pipeline"]

        # Recuperar nombres de clases ordenadas
        if "clases" in bundle_cargado:
            self.clases = list(bundle_cargado["clases"])
        elif hasattr(self.pipeline, "classes_"):
            self.clases = list(self.pipeline.classes_)

        # Cargar métricas en caché si están disponibles
        if self.ruta_metricas.exists():
            try:
                with open(self.ruta_metricas, "r", encoding="utf-8") as f:
                    self.metricas = json.load(f)
                logger.info("Métricas oficiales cargadas exitosamente en memoria.")
            except Exception as e:
                logger.warning(f"No se pudieron leer las métricas desde '{self.ruta_metricas}': {e}")
        else:
            logger.warning(f"Archivo de métricas '{self.ruta_metricas}' no encontrado.")

        self.loaded = True
        ms_carga = (time.perf_counter() - tiempo_inicio) * 1000
        logger.info(f"Modelo cargado y listo en memoria RAM ({ms_carga:.2f} ms). Clases: {self.clases}")

    def _asegurar_modelo_cargado(self) -> None:
        """Verifica que el modelo esté cargado en memoria antes de inferir."""
        if not self.loaded or self.pipeline is None:
            raise RuntimeError(
                "El modelo de Machine Learning no está cargado en memoria RAM. "
                "Ejecute 'service.load()' antes de solicitar inferencias."
            )

    def explain(self, texto: str) -> Dict[str, Any]:
        """Obtiene la auditoría lingüística paso a paso mediante el TextPreprocessor.

        Parameters
        ----------
        texto : str
            Texto limpio ingresado por el usuario.

        Returns
        -------
        Dict[str, Any]
            Diccionario estructurado con las etapas de preprocesamiento de NLP.
        """
        self._asegurar_modelo_cargado()

        preprocessor = self.pipeline.named_steps.get("preprocessor")
        if preprocessor is not None and hasattr(preprocessor, "explain"):
            pasos_raw = preprocessor.explain(texto)
            return {
                "texto_original": pasos_raw.get("original", texto),
                "texto_normalizado": pasos_raw.get("normalizado", ""),
                "tokens": pasos_raw.get("tokens", []),
                "sin_stopwords": pasos_raw.get("sin_stopwords", []),
                "raices": pasos_raw.get("morfologia", []),
                "texto_procesado": pasos_raw.get("texto_final", ""),
            }

        return {
            "texto_original": texto,
            "texto_normalizado": texto.lower(),
            "tokens": texto.split(),
            "sin_stopwords": texto.split(),
            "raices": texto.split(),
            "texto_procesado": texto,
        }

    def predict_single(self, texto: str) -> Dict[str, Any]:
        """Ejecuta la predicción individual sobre una oferta laboral.

        Parameters
        ----------
        texto : str
            Descripción validada de la oferta de trabajo.

        Returns
        -------
        Dict[str, Any]
            Respuesta compatible con el esquema `PredictResponse`.
        """
        self._asegurar_modelo_cargado()

        t0 = time.perf_counter()

        # Inferencia mediante Softmax
        probas = self.pipeline.predict_proba([texto])[0]
        clase_idx = int(np.argmax(probas))
        sector_predicho = self.clases[clase_idx]
        confianza = float(probas[clase_idx])

        # Mapeo de probabilidades de los 5 sectores
        distribucion = {
            sector: round(float(prob), 4)
            for sector, prob in zip(self.clases, probas)
        }

        # Auditoría de NLP transparente
        auditoria_nlp = self.explain(texto)

        t1 = time.perf_counter()
        tiempo_ms = round((t1 - t0) * 1000, 2)

        return {
            "sector_predicho": sector_predicho,
            "probabilidad": round(confianza, 4),
            "probabilidades": distribucion,
            "preprocesamiento": auditoria_nlp,
            "tiempo_ms": tiempo_ms,
        }

    def predict_batch_csv(self, contenido_bytes: bytes) -> Dict[str, Any]:
        """Procesa un archivo CSV masivo de ofertas de forma vectorizada.

        Parameters
        ----------
        contenido_bytes : bytes
            Bytes del archivo CSV cargado mediante multipart/form-data.

        Returns
        -------
        Dict[str, Any]
            Respuesta compatible con el esquema `BatchResponse`.

        Raises
        ------
        ValueError
            Si el archivo está vacío, corrupto o carece de columna de texto.
        """
        self._asegurar_modelo_cargado()

        if not contenido_bytes or len(contenido_bytes.strip()) == 0:
            raise ValueError("El archivo CSV subido está completamente vacío.")

        try:
            df = pd.read_csv(io.BytesIO(contenido_bytes))
        except Exception as e:
            raise ValueError(f"No se pudo interpretar el archivo como CSV válido: {e}")

        if df.empty:
            raise ValueError("El archivo CSV no contiene filas de datos para clasificar.")

        # Identificar columna candidata para el texto
        columnas_candidatas = ["descripcion", "texto", "description", "oferta", "detalle", "puesto"]
        col_seleccionada = None

        columnas_lower = {str(c).lower().strip(): c for c in df.columns}
        for cand in columnas_candidatas:
            if cand in columnas_lower:
                col_seleccionada = columnas_lower[cand]
                break

        if col_seleccionada is None:
            # Buscar la primera columna de tipo texto
            cols_texto = df.select_dtypes(include=["object", "string"]).columns
            if len(cols_texto) > 0:
                col_seleccionada = cols_texto[0]
            else:
                raise ValueError(
                    f"El CSV no contiene una columna reconocible de texto (ej. 'descripcion' o 'texto'). "
                    f"Columnas encontradas: {list(df.columns)}"
                )

        # Extraer textos y sanear nulos
        textos = df[col_seleccionada].fillna("").astype(str).tolist()

        t0 = time.perf_counter()

        # Inferencia vectorizada en un solo pase matricial
        matriz_probas = self.pipeline.predict_proba(textos)
        indices_max = np.argmax(matriz_probas, axis=1)

        # Conteo inicializado en 0 para todos los sectores oficiales
        conteo_sectores: Dict[str, int] = {sector: 0 for sector in self.clases}
        resultados_items: List[Dict[str, Any]] = []

        for i, idx in enumerate(indices_max):
            sector = self.clases[idx]
            conteo_sectores[sector] = conteo_sectores.get(sector, 0) + 1

            txt_fila = textos[i].strip()
            resumen = (txt_fila[:117] + "...") if len(txt_fila) > 120 else txt_fila

            resultados_items.append(
                {
                    "id": i + 1,
                    "texto_resumen": resumen,
                    "sector_predicho": sector,
                    "probabilidad": round(float(matriz_probas[i, idx]), 4),
                }
            )

        t1 = time.perf_counter()
        tiempo_total_ms = round((t1 - t0) * 1000, 2)

        return {
            "total_procesados": len(textos),
            "distribucion_sectores": conteo_sectores,
            "resultados": resultados_items,
            "tiempo_total_ms": tiempo_total_ms,
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtiene las métricas oficiales del modelo y la matriz de confusión.

        Returns
        -------
        Dict[str, Any]
            Contenido del archivo `artifacts/metrics.json`.

        Raises
        ------
        FileNotFoundError
            Si no existe el archivo de métricas.
        """
        if self.metricas is not None:
            return self.metricas

        if not self.ruta_metricas.exists():
            raise FileNotFoundError(
                f"El archivo de métricas '{self.ruta_metricas}' no existe. "
                "Ejecute el entrenamiento para generarlo."
            )

        with open(self.ruta_metricas, "r", encoding="utf-8") as f:
            self.metricas = json.load(f)

        return self.metricas

    def health(self) -> Dict[str, Any]:
        """Informa sobre el estado operativo del servicio y del artefacto en RAM."""
        nombre_modelo = None
        if self.bundle:
            nombre_modelo = self.bundle.get("modelo", "Pipeline de Scikit-Learn")

        return {
            "estado": "ok" if self.loaded else "degradado",
            "modelo_cargado": self.loaded,
            "modelo_nombre": nombre_modelo,
            "sectores_soportados": self.clases,
            "version": "1.0.0",
        }


# Instancia única (Singleton) para ser consumida por la aplicación FastAPI
model_service = ModelService()

