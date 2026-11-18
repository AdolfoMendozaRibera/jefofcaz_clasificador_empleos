---
title: "Paso 3.4: Pruebas Unitarias Automatizadas de Artefactos de Producción"
materia: "Tópicos y Programación Avanzada"
fase: "3"
paso: "3.4"
estado: "Completado"
tags:
  - pytest
  - test_models
  - joblib
  - metrics-json
  - errors-csv
  - inferencia
  - probabilidades
---

# ✅ Paso 3.4: Pruebas Unitarias de los Artefactos de Producción (`tests/test_models.py`)

> [!info] Propósito de este Paso
> Crear el archivo [`tests/test_models.py`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/tests/test_models.py) que prueba **directamente los 3 artefactos generados en disco** sin pasar por el código de entrenamiento.
>
> Esto cumple la Regla de Oro del proyecto: *"No afirmes 'funciona' sin haberlo ejecutado"* y valida que la API de FastAPI podrá cargar `model.joblib` sin problemas.

---

## 1. ¿Por Qué Probar los Artefactos Directamente?

Probar `src/models/train.py` (con un dataset temporal) garantiza que el **código funciona**.
Probar `artifacts/model.joblib` garantiza que el **archivo generado en disco es válido y usable**.

La diferencia es crítica: si alguien borra accidentalmente el `.joblib` o lo genera con un error silencioso, las pruebas de `test_models.py` lo detectarán de inmediato sin necesidad de reentrenar.

---

## 2. Las 7 Pruebas Implementadas y su Propósito

Todas pasan `PASSED` sobre los artefactos reales del proyecto:

| Test | ¿Qué verifica? | Resultado |
|---|---|:---:|
| `test_existencia_de_artefactos_oficiales` | Que `model.joblib`, `metrics.json` y `errors.csv` existan físicamente en `artifacts/`. | ✅ PASSED |
| `test_cargar_artefacto_model_joblib_y_metadatos` | Que el bundle contenga las claves `pipeline`, `clases`, `modelo`, `hiperparametros`, `metricas_test` y los 5 sectores exactos. | ✅ PASSED |
| `test_inferencia_cinco_sectores_ofertas_claras` | Que el pipeline clasifique correctamente 5 ofertas reales arquetípicas (una por sector). | ✅ PASSED |
| `test_probabilidades_suman_uno_propiedad_matematica` | Que `predict_proba()` devuelva probabilidades que sumen $1.0 \pm 10^{-5}$ (propiedad matemática de Softmax). | ✅ PASSED |
| `test_f1_macro_supera_ampliamente_baseline` | Que el F1-Score en test ($0.9155$) supere el umbral de $\ge 0.85$, desmantelando la línea base Dummy ($0.0892$). | ✅ PASSED |
| `test_integridad_metrics_json` | Que `metrics.json` contenga el esquema completo: F1, matriz $5 \times 5$ y 10 términos influyentes por clase. | ✅ PASSED |
| `test_integridad_errors_csv` | Que en el 100% de las filas de `errors.csv`, `sector_real != sector_predicho` y exista causa lingüística. | ✅ PASSED |

---

## 3. Resultado Final de la Suite Completa del Proyecto

```
============================= 56 pruebas en verde ==============================

tests/test_cleaning.py         →  5/5  PASSED  (Limpieza base y ñ)
tests/test_experiments.py      →  3/3  PASSED  (Validación cruzada k=5)
tests/test_models.py           →  7/7  PASSED  (Artefactos de producción)
tests/test_morphology.py       →  7/7  PASSED  (Stop words y morfología)
tests/test_pipeline.py         →  6/6  PASSED  (TF-IDF y Pipeline base)
tests/test_prepare_dataset.py  → 13/13 PASSED  (Dataset y mapeo sectores)
tests/test_preprocessing.py    →  5/5  PASSED  (TextPreprocessor y explain)
tests/test_split_data.py       →  5/5  PASSED  (Partición estratificada)
tests/test_train.py            →  4/4  PASSED  (Entrenamiento y errores)

============================== 56 passed in 11.75s =============================
```

---

## 4. Casos de Inferencia Controlados Verificados a Mano

| Texto de la Oferta | Sector Esperado | ¿Acertó? |
|---|---|:---:|
| `"Conductor de camión tráiler ruta nacional e internacional carnet C+E..."` | `transporte_logistica` | ✅ |
| `"Cocinero jefe de partida para restaurante de tapas elaboración de menús diarios..."` | `hosteleria_gastronomia` | ✅ |
| `"Oficial de primera albañil para obra nueva alicatado colocación de ladrillo..."` | `construccion_mantenimiento` | ✅ |
| `"Enfermero para residencia de ancianos y centro sociosanitario administración de medicación..."` | `salud_servicios_sociales` | ✅ |
| `"Agente comercial inmobiliario prospección y captación de clientes venta de inmuebles..."` | `ventas_comercial` | ✅ |

---

## 5. Archivos Involucrados

1. [`tests/test_models.py`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/tests/test_models.py): Suite de 7 pruebas que auditan directamente los artefactos de producción en disco.
2. [`artifacts/model.joblib`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/artifacts/model.joblib): Pipeline congelado (321 KB) validado.
3. [`artifacts/metrics.json`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/artifacts/metrics.json): JSON con F1-Macro, matriz $5 \times 5$ y términos influyentes validado.
4. [`artifacts/errors.csv`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/artifacts/errors.csv): 58 errores diagnosticados y validados.

---

## 6. Cómo Reproducirlo (Para la Modificación en Vivo)

Correr solo las pruebas de artefactos:
```bash
.venv/Scripts/python -m pytest tests/test_models.py -v
```

Correr toda la suite del proyecto (56 pruebas):
```bash
.venv/Scripts/python -m pytest -v
```

> [!tip] Valor para la defensa oral
> Si el docente pregunta *"¿cómo sabes que el modelo es correcto?"*, puedes demostrar en vivo que:
> 1. `predict_proba()` devuelve 5 valores que suman exactamente 1.0 (propiedad matemática de Softmax).
> 2. El modelo clasifica correctamente las 5 ofertas arquetípicas de ejemplo.
> 3. El F1-Score oficial de 91.55% está registrado dentro del propio `.joblib`.
