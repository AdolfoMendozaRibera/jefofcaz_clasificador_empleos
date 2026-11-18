---
title: "Paso 4.2: Servicio del Modelo y Carga Única (api/service.py)"
materia: "Tópicos y Programación Avanzada"
fase: "4"
paso: "4.2"
estado: "Completado ✅"
tags:
  - fastapi
  - service-layer
  - joblib
  - lifespan
  - singleton
  - batch-csv
  - explain
---

# ✅ Paso 4.2: Servicio del Modelo y Carga Única (`api/service.py`)

> [!info] El "cerebro" de la API
> Este archivo es la capa de lógica de negocio. Su responsabilidad es única:
> **orquestar el modelo sin que `main.py` ni el frontend sepan cómo funciona internamente**.
> El pipeline de Scikit-Learn se carga en RAM una sola vez al arrancar el servidor
> y permanece ahí hasta que se apague.

---

## 1. ¿Por qué esta capa y por qué separada?

La regla de **Separación de Responsabilidades (SoC)** impone que cada módulo haga solo una cosa:

| Módulo | Responsabilidad única |
|---|---|
| `schemas.py` | ¿El dato que me pasaste tiene sentido? (Validación) |
| **`service.py`** | **Carga el modelo y ejecuta el pipeline (Lógica)** |
| `main.py` | ¿A qué URL se llama y qué se responde? (Rutas HTTP) |

Si en el futuro cambia el modelo (`.joblib` nuevo), o el formato del CSV, **solo se toca `service.py`**, no los otros dos.

---

## 2. Archivos creados o modificados

| Archivo | Acción | Descripción |
|---|---|---|
| [`api/service.py`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/api/service.py) | ✅ Creado | Clase `ModelService` con carga única, inferencia individual, lote CSV y métricas |
| [`tests/test_service.py`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/tests/test_service.py) | ✅ Creado | 7 pruebas unitarias verificadas |

---

## 3. La Clase `ModelService` y Sus Métodos

```python
class ModelService:
    def load(self) -> None              # Carga model.joblib UNA SOLA VEZ
    def predict_single(texto) -> dict  # Predicción individual con Softmax
    def explain(texto) -> dict         # Auditoría NLP paso a paso
    def predict_batch_csv(bytes) -> dict  # Procesamiento masivo de CSV
    def get_metrics() -> dict          # Expone metrics.json al frontend
    def health() -> dict               # Estado operativo del servicio
```

> [!caution] El Error Clásico que se Evita
> Si cargáramos el `.joblib` **dentro del endpoint** (`@app.post("/predict")`),
> el servidor leería el archivo del disco en cada clic del usuario, tardando cientos de milisegundos
> adicionales y saturando el servidor bajo carga. El patrón correcto es cargarlo **una sola vez al inicio**.

---

## 4. Cómo Funciona `load()` (El Patrón Lifespan)

`load()` se invoca desde el evento de inicio de FastAPI (`lifespan`) al arrancar el servidor:

```python
# api/service.py
def load(self) -> None:
    # 1. Carga el bundle del disco a la RAM
    bundle_cargado = joblib.load(self.ruta_modelo)

    # 2. Extrae el pipeline y las clases de los 5 sectores
    self.pipeline = bundle_cargado["pipeline"]
    self.clases = list(bundle_cargado["clases"])

    # 3. Carga metrics.json en caché en RAM también
    with open(self.ruta_metricas) as f:
        self.metricas = json.load(f)

    self.loaded = True
    logger.info("Modelo cargado en RAM.")
```

**Ejemplo de lo que se imprime al arrancar el servidor:**
```
INFO:api_service: Cargando bundle del modelo desde 'artifacts/model.joblib'...
INFO:api_service: Métricas oficiales cargadas exitosamente en memoria.
INFO:api_service: Modelo cargado y listo en memoria RAM (312.45 ms). Clases: ['construccion_mantenimiento', ...]
```

---

## 5. Cómo Funciona `predict_single()` — El Flujo Completo

```
texto de entrada (str)
        │
        ▼
pipeline.predict_proba([texto])          ← Scikit-Learn hace TODO: limpieza + TF-IDF + Softmax
        │
        ▼
[0.02, 0.94, 0.01, 0.01, 0.02]          ← Vector de 5 probabilidades
        │
        ▼
np.argmax(probas) = 1                    ← Índice del sector con mayor probabilidad
        │
        ▼
clases[1] = "hosteleria_gastronomia"     ← Nombre del sector predicho
        │
        ▼
explain(texto) → pasos NLP               ← TextPreprocessor.explain() para el frontend
        │
        ▼
{ sector_predicho, probabilidad, probabilidades, preprocesamiento, tiempo_ms }
```

**Ejemplo real calculable a mano:**

Entrada: `"Cocinero jefe de partida para restaurante de tapas y menú diario"`

| Sector | Probabilidad |
|---|---:|
| `hosteleria_gastronomia` | **0.9321** ← ganador |
| `ventas_comercial` | 0.0284 |
| `transporte_logistica` | 0.0201 |
| `salud_servicios_sociales` | 0.0104 |
| `construccion_mantenimiento` | 0.0090 |

Suma: $0.9321 + 0.0284 + 0.0201 + 0.0104 + 0.0090 = 1.0000$ ✅ (propiedad matemática de Softmax)

---

## 6. Cómo Funciona `explain()` — La Auditoría de NLP

El frontend necesita mostrar cada paso del pipeline aplicado al texto. En vez de reimplementar la limpieza en la API, llamamos directamente al método `.explain()` del `TextPreprocessor` que ya está **dentro del pipeline serializado**.

```python
def explain(self, texto: str) -> dict:
    # Extrae el preprocesador del pipeline
    preprocessor = self.pipeline.named_steps.get("preprocessor")
    # Llama al método explain() de la Fase 2
    pasos_raw = preprocessor.explain(texto)
    return {
        "texto_original":   pasos_raw["original"],      # "Cocinero jefe de partida..."
        "texto_normalizado": pasos_raw["normalizado"],   # "cocinero jefe de partida..."
        "tokens":           pasos_raw["tokens"],         # ["cocinero", "jefe", "partida"]
        "sin_stopwords":    pasos_raw["sin_stopwords"],  # ["cocinero", "partida"]
        "raices":           pasos_raw["morfologia"],     # ["cociner", "partid"]
        "texto_procesado":  pasos_raw["texto_final"],    # "cociner partid"
    }
```

> [!note] Ventaja Clave
> El modelo **nunca reimplementa la limpieza de texto**. El pipeline serializado
> ya contiene el preprocesador de la Fase 2 y lo aplica de forma idéntica
> tanto en entrenamiento como en producción. Esto garantiza **cero data leakage** en producción.

---

## 7. Cómo Funciona `predict_batch_csv()` — Lotes Masivos

```python
# 1. Leer el CSV subido como bytes
df = pd.read_csv(io.BytesIO(contenido_bytes))

# 2. Detectar la columna de texto automáticamente
# Candidatos: ["descripcion", "texto", "description", "oferta", "detalle", "puesto"]

# 3. Inferencia vectorizada en UN SOLO PASE (eficiente)
matriz_probas = self.pipeline.predict_proba(textos)   # Forma: (N_filas, 5_sectores)
indices_max = np.argmax(matriz_probas, axis=1)         # El sector ganador por fila
```

La eficiencia es clave: en vez de hacer N llamadas a `predict()` en un bucle,
se pasa toda la matriz de una vez a Scikit-Learn. Esto es entre **5x y 10x más rápido** para lotes grandes.

---

## 8. Pruebas y Resultado Real

**7 pruebas en `tests/test_service.py`:**

| Prueba | ¿Qué comprueba? | Estado |
|---|---|:---:|
| `test_service_load_exitoso` | 5 sectores cargados en RAM, `loaded = True` | ✅ PASSED |
| `test_service_predict_single_y_propiedades_matematicas` | Sector correcto para oferta de hostelería, Softmax suma 1.0 | ✅ PASSED |
| `test_service_explain_pasos_intermedios_nlp` | 6 claves del diccionario de auditoría presentes | ✅ PASSED |
| `test_service_batch_csv_procesamiento_vectorizado` | 3 filas de CSV → 3 sectores correctos | ✅ PASSED |
| `test_service_batch_csv_vacio_o_invalido_falla` | Archivo vacío y CSV sin columna de texto → `ValueError` | ✅ PASSED |
| `test_service_get_metrics_retorna_metricas_oficiales` | F1 ≥ 0.85 y matriz de confusión 5×5 | ✅ PASSED |
| `test_service_health_check` | Estado `"ok"`, `modelo_cargado = True`, 5 sectores | ✅ PASSED |

```
7 passed in 11.29s
```

---

## 9. Cómo comprobarlo

```bash
# Solo las pruebas del servicio:
.venv\Scripts\python -m pytest tests/test_service.py -v

# Suite completa del proyecto (71 pruebas):
.venv\Scripts\python -m pytest -q
```

