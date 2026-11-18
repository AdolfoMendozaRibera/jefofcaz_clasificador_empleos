---
title: "Paso 4.1: Contratos y Validación en el Borde (api/schemas.py)"
materia: "Tópicos y Programación Avanzada"
fase: "4"
paso: "4.1"
estado: "Completado ✅"
tags:
  - fastapi
  - pydantic
  - validation
  - schemas
  - http-422
  - fail-fast
---

# ✅ Paso 4.1: Contratos y Validación en el Borde (`api/schemas.py`)

> [!info] ¿Qué es la "validación en el borde"?
> Es la práctica de **rechazar entradas inválidas lo antes posible**, antes de pasarle nada al modelo.
> Si el texto viene vacío, es solo números o es demasiado largo → el servidor responde de inmediato con
> un error **HTTP 422 Unprocessable Entity** en español, sin desperdiciar CPU ni RAM en el pipeline.
> Esto se llama estrategia **Fail-Fast** (falla rápida).

---

## 1. ¿Por qué primero `schemas.py`?

El PDF del proyecto exige en el **punto 5.5**:

> *"Validación de entradas (texto vacío, demasiado largo, formato incorrecto) y mensajes de error claros"*

Pydantic v2 integrada con FastAPI hace esto de forma automática: si el validador lanza un `ValueError`, FastAPI lo captura y devuelve el `HTTP 422` estándar sin que el endpoint ni el modelo lleguen a ejecutarse.

La arquitectura impone separar responsabilidades:

```
schemas.py  →  ¿El dato que me pasaste tiene sentido? (BORDE)
service.py  →  Ejecuta el pipeline del modelo           (LÓGICA)
main.py     →  ¿A qué URL llamas y qué te devolveré?   (RUTAS)
```

---

## 2. Archivos creados o modificados

| Archivo | Acción | Descripción |
|---|---|---|
| [`api/schemas.py`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/api/schemas.py) | ✅ Creado | Contratos Pydantic v2 y función de guardia `validar_texto_oferta()` |
| [`tests/test_schemas.py`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/tests/test_schemas.py) | ✅ Creado | 8 pruebas unitarias de los validadores |

---

## 3. La Función de Guardia: `validar_texto_oferta()`

Esta función centraliza **toda la lógica de validación** en un lugar. Las reglas de negocio vienen de `params.yaml` (fuente única de verdad).

```python
# api/schemas.py
def validar_texto_oferta(texto: str) -> str:
    texto_limpio = texto.strip()

    if not texto_limpio:
        raise ValueError("El texto de la oferta está vacío o solo contiene espacios.")

    longitud = len(texto_limpio)
    if longitud < MIN_CHARS:  # → 15 caracteres (leído de params.yaml)
        raise ValueError(f"El texto tiene {longitud} caracteres; el mínimo requerido es de {MIN_CHARS}.")

    if longitud > MAX_CHARS:  # → 5000 caracteres (leído de params.yaml)
        raise ValueError(f"El texto tiene {longitud} caracteres; el límite máximo es de {MAX_CHARS}.")

    if not PATRON_LETRAS.search(texto_limpio):
        raise ValueError("El texto no contiene letras o palabras válidas para clasificar.")

    return texto_limpio
```

> [!tip] Cambiar los límites sin tocar código
> Edita `params.yaml` en la sección `data:` → `min_chars` y `max_chars`.
> La API los recarga cada vez que se reinicia el servidor.

---

## 4. Los Modelos Pydantic: Qué Entra y Qué Sale

### Entrada: `PredictRequest`
```python
class PredictRequest(BaseModel):
    texto: str = Field(description="Descripción textual de la oferta a clasificar.")

    @field_validator("texto")
    @classmethod
    def validar_campo_texto(cls, valor: str) -> str:
        return validar_texto_oferta(valor)  # ← Llama a la guardia
```

**Ejemplo de petición válida:**
```json
POST /api/predict
{ "texto": "Se busca conductor de camión tráiler con carnet C+E y CAP en vigor." }
→ HTTP 200 OK
```

**Ejemplos de petición inválida (HTTP 422):**
```json
{ "texto": "" }
→ HTTP 422: "El texto de la oferta está vacío o solo contiene espacios."

{ "texto": "Hola" }
→ HTTP 422: "El texto tiene 4 caracteres; el mínimo requerido es de 15 caracteres."

{ "texto": "1234567890!@#$%^" }
→ HTTP 422: "El texto no contiene letras o palabras válidas para clasificar."
```

---

### Salida: `PredictResponse`
Lo que devuelve el endpoint `POST /api/predict` cuando todo va bien:

```json
{
  "sector_predicho": "transporte_logistica",
  "probabilidad": 0.9412,
  "probabilidades": {
    "transporte_logistica": 0.9412,
    "hosteleria_gastronomia": 0.0211,
    "ventas_comercial": 0.0154,
    "salud_servicios_sociales": 0.0118,
    "construccion_mantenimiento": 0.0105
  },
  "preprocesamiento": {
    "texto_original": "Se busca conductor de camión...",
    "texto_normalizado": "busca conductor camion",
    "tokens": ["busca", "conductor", "camion"],
    "sin_stopwords": ["conductor", "camion"],
    "raices": ["conduct", "camion"],
    "texto_procesado": "conduct camion"
  },
  "tiempo_ms": 3.45
}
```

> [!note] La clave `preprocesamiento`
> Devuelve los **pasos intermedios del pipeline NLP** para que el frontend dibuje
> la "columna de auditoría" que exige el PDF. Llama directamente al método
> `TextPreprocessor.explain()` que construimos en la Fase 2.

---

### Otros contratos

| Modelo | Cuándo se usa |
|---|---|
| `BatchResponse` / `BatchItemResult` | Resultado de `POST /api/predict/batch` (CSV con muchas ofertas) |
| `HealthResponse` | Respuesta de `GET /api/health` con estado del servidor y modelo |
| `ErrorResponse` | Formato estándar para cualquier error 500 que escape al manejador |

---

## 5. Pruebas y Resultado Real

**8 pruebas en `tests/test_schemas.py`** verifican todos los casos de validación:

| Prueba | ¿Qué comprueba? | Estado |
|---|---|:---:|
| `test_texto_valido_conserva_contenido_y_remueve_espacios_extremos` | El `strip()` funciona y el texto válido pasa | ✅ PASSED |
| `test_rechazo_texto_vacio` | `""` → `ValueError` con mensaje en español | ✅ PASSED |
| `test_rechazo_texto_solo_espacios` | `"   \n\t "` → `ValueError` | ✅ PASSED |
| `test_rechazo_texto_menor_al_limite_minimo` | 14 chars → rechazado | ✅ PASSED |
| `test_rechazo_texto_mayor_al_limite_maximo` | 5001 chars → rechazado | ✅ PASSED |
| `test_rechazo_texto_sin_letras_validas` | `"1234-5678"`, `"??? !!!"` → rechazados | ✅ PASSED |
| `test_pydantic_predict_request_valida_correctamente` | Pydantic lanza `ValidationError` ante texto vacío | ✅ PASSED |
| `test_estructuras_de_respuesta_pydantic` | Los modelos de respuesta serializan los tipos correctos | ✅ PASSED |

**Suite completa del proyecto:**
```
64 passed in 47.59s
```

---

## 6. Cómo comprobarlo tú mismo

```bash
# Solo las pruebas de los contratos:
.venv\Scripts\python -m pytest tests/test_schemas.py -v

# Suite completa (64 pruebas):
.venv\Scripts\python -m pytest -q
```

