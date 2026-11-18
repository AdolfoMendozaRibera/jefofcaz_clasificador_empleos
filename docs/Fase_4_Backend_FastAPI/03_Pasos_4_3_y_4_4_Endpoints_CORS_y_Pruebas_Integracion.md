---
title: "Pasos 4.3 y 4.4: Endpoints HTTP, Lifespan, CORS y Pruebas de Integración"
materia: "Tópicos y Programación Avanzada"
fase: "4"
paso: "4.3 y 4.4"
estado: "Completado ✅"
tags:
  - fastapi
  - endpoints
  - lifespan
  - cors
  - test-client
  - http-422
  - swagger
---

# ✅ Pasos 4.3 y 4.4: Endpoints HTTP, CORS y Pruebas de Integración

> [!info] El "puente" entre el modelo y el mundo exterior
> `main.py` es la capa más fina de las tres: no sabe nada de machine learning ni de validaciones complejas.
> Solo define **a qué URL responde** y **qué capa llama** en cada caso.
> Las pruebas de integración usan `TestClient` para simular peticiones HTTP reales sin levantar un servidor.

---

## 1. Archivos creados o modificados

| Archivo | Acción | Descripción |
|---|---|---|
| [`api/main.py`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/api/main.py) | ✅ Creado | Rutas HTTP, patrón `lifespan`, CORS y manejadores globales de error |
| [`tests/test_api.py`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/tests/test_api.py) | ✅ Creado | 10 pruebas de integración con `TestClient` de FastAPI |

---

## 2. El Patrón `lifespan` — La Carga Única del Modelo

> [!caution] Por qué esto importa en la defensa oral
> Si cargaras `joblib.load()` dentro del endpoint `POST /api/predict`, el servidor leería
> el archivo del disco en cada clic. Con el patrón `lifespan` la carga ocurre **una sola vez al arrancar**
> y el modelo vive en RAM para todas las peticiones subsiguientes.

```python
# api/main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ↓ Se ejecuta UNA SOLA VEZ antes de aceptar peticiones
    model_service.load()
    logger.info("✅ Pipeline de ML cargado y listo en RAM.")
    yield
    # ↓ Se ejecuta al apagar el servidor
    logger.info("🛑 Servidor apagándose.")

app = FastAPI(title="API Clasificador de Empleos", lifespan=lifespan)
```

**Salida real al arrancar con `uvicorn`:**
```
INFO: Iniciando servicio de clasificación de ofertas de empleo...
INFO: Cargando bundle del modelo desde 'artifacts/model.joblib'...
INFO: Métricas oficiales cargadas exitosamente en memoria.
INFO: ✅ Pipeline de Machine Learning cargado y listo para inferencias.
INFO: Application startup complete.
```

---

## 3. Configuración de CORS para Vite (Frontend)

CORS (*Cross-Origin Resource Sharing*) es un mecanismo de seguridad del navegador que bloquea peticiones HTTP que provienen de un dominio/puerto distinto al del servidor.

**El problema:** El frontend de Vite corre en `http://localhost:5173` y la API en `http://localhost:8000`. El navegador los ve como orígenes distintos y bloquea la petición.

**La solución:** Registrar explícitamente los orígenes permitidos:

```python
ORIGENES_PERMITIDOS = [
    "http://localhost:5173",   # Vite (React) por defecto
    "http://localhost:8080",   # Alternativa
    "http://localhost:3000",   # Alternativa adicional
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENES_PERMITIDOS,
    allow_methods=["GET", "POST", "OPTIONS"],
)
```

> [!tip] ¿Dónde cambiar esto?
> En [`api/main.py`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/api/main.py) dentro de la lista `ORIGENES_PERMITIDOS`.
> **Nunca** usar `allow_origins=["*"]` en producción (es una vulnerabilidad de seguridad).

---

## 4. Los 4 Endpoints Implementados

### `GET /api/health`
```
¿El servidor está vivo y el modelo está en RAM?

Respuesta 200 OK:
{
  "estado": "ok",
  "modelo_cargado": true,
  "modelo_nombre": "LogisticRegression",
  "sectores_soportados": ["construccion_mantenimiento", ...],
  "version": "1.0.0"
}
```

---

### `POST /api/predict`
```
Entrada:  { "texto": "Conductor camión con carnet C+E y CAP." }
                          │
                          ▼ schemas.py valida (Fail-Fast)
                          │
                          ▼ service.predict_single(texto)
                          │
Salida 200 OK:
{
  "sector_predicho": "transporte_logistica",
  "probabilidad": 0.9412,
  "probabilidades": { "transporte_logistica": 0.9412, ... },
  "preprocesamiento": { "tokens": [...], "raices": [...] ... },
  "tiempo_ms": 3.45
}

Salida 422 si texto vacío, muy corto o sin letras:
{
  "status": "error",
  "mensaje": "El texto de la oferta está vacío o solo contiene espacios.",
  "detalle": [{"campo": "texto", "mensaje": "..."}]
}
```

---

### `POST /api/predict/batch`
```
Entrada: archivo .csv (multipart/form-data) con columna "descripcion"
         ↓ leyendo 3 filas del CSV de ejemplo:

Salida 200 OK:
{
  "total_procesados": 3,
  "distribucion_sectores": {
    "transporte_logistica": 1,
    "hosteleria_gastronomia": 1,
    "ventas_comercial": 1,
    ...
  },
  "resultados": [
    { "id": 1, "sector_predicho": "transporte_logistica", "probabilidad": 0.89 },
    ...
  ],
  "tiempo_total_ms": 45.3
}

Salida 400 si el archivo no es .csv.
Salida 422 si el CSV está vacío o sin columna de texto reconocible.
```

---

### `GET /api/metrics`
```
Salida 200 OK (contenido de artifacts/metrics.json):
{
  "f1_macro": 0.9155,
  "accuracy": 0.9132,
  "clases": [ ... ],
  "matriz_confusion": [[...], ...],   ← Matriz 5x5 para el heatmap de React
  "terminos_mas_influyentes": { ... } ← Top-10 palabras por sector
}
```

---

## 5. Manejadores Globales de Errores (Sin Fugar Trazas)

```python
# Captura errores 422 de Pydantic → Respuesta limpia en español
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    # Limpia el prefijo "Value error, " que agrega Pydantic
    ...
    return JSONResponse(status_code=422, content={"status": "error", "mensaje": "..."})

# Captura cualquier error 500 → Sin stacktraces al cliente
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.error(f"Fallo no controlado: {exc}", exc_info=True)  # Se registra internamente
    return JSONResponse(status_code=500, content={"status": "error", "mensaje": "Error inesperado."})
```

---

## 6. Pruebas de Integración y Resultado Real (10/10 PASSED)

Las pruebas en [`tests/test_api.py`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/tests/test_api.py) usan `TestClient` de FastAPI, que simula peticiones HTTP reales (incluyendo el ciclo `lifespan`) sin necesidad de levantar un servidor.

| Prueba | ¿Qué verifica? | Estado |
|---|---|:---:|
| `test_health_check_endpoint` | HTTP 200, `estado: "ok"`, 5 sectores en RAM | ✅ PASSED |
| `test_predict_oferta_valida_transporte` | Clasificación correcta + Softmax suma 1.0 + auditoría NLP | ✅ PASSED |
| `test_predict_oferta_valida_salud` | Clasificación correcta sector salud | ✅ PASSED |
| `test_predict_texto_vacio_retorna_422` | `"   "` → HTTP 422, mensaje en español | ✅ PASSED |
| `test_predict_texto_muy_corto_retorna_422` | 8 chars → HTTP 422, mensaje con límite | ✅ PASSED |
| `test_predict_texto_sin_letras_retorna_422` | `"12345..."` → HTTP 422 | ✅ PASSED |
| `test_predict_batch_csv_exitoso` | CSV 3 filas → 3 sectores correctos | ✅ PASSED |
| `test_predict_batch_archivo_no_csv_retorna_400` | `.txt` → HTTP 400 | ✅ PASSED |
| `test_get_metrics_retorna_json_oficial` | F1 ≥ 0.85 y matriz 5×5 | ✅ PASSED |
| `test_root_endpoint_info` | `/` retorna enlace a `/docs` | ✅ PASSED |

```
10 passed, 4 warnings in 10.57s
```

> [!note] Sobre los warnings
> Los 4 warnings son de deprecación interna entre `httpx` y `starlette` (versiones instaladas).
> **No afectan la funcionalidad** ni los resultados de las pruebas.
> Se resuelven actualizando `httpx` a `httpx2`, pero no es necesario para el proyecto actual.

---

## 7. Cómo Probar en Vivo (Git Bash)

```bash
cd /e/desarrollador/topicos/jefofcaz_clasificador_empleos

# Arrancar el servidor en modo recarga automática
.venv/Scripts/uvicorn api.main:app --reload --port 8000

# Luego abrir en el navegador:
# http://localhost:8000/docs        ← Swagger UI interactivo
# http://localhost:8000/redoc       ← Documentación ReDoc
# http://localhost:8000/api/health  ← Verificación directa en JSON
```

```bash
# Correr solo las pruebas de la API:
.venv/Scripts/python -m pytest tests/test_api.py -v

# Suite completa del proyecto (81 pruebas):
.venv/Scripts/python -m pytest -q
```

