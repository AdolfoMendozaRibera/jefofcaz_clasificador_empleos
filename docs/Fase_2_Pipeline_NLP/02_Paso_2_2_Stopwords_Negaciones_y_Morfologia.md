---
title: "Paso 2.2: Stop Words con Negaciones Protegidas y Reducción Morfológica"
materia: "Tópicos y Programación Avanzada"
fase: "2"
paso: "2.2"
estado: "Completado"
tags:
  - fase2
  - nlp
  - stopwords
  - negaciones
  - stemming
  - lematizacion
  - snowball
  - spacy
  - pytest
---

# 🛡️ Paso 2.2: Stop Words con Negaciones Protegidas y Reducción Morfológica

> [!NOTE] ¿Qué se construyó en este paso?
> Se implementó el módulo `src/nlp/morphology.py` y su suite de pruebas `tests/test_morphology.py`.
>
> Este módulo es la **estación 2 del pipeline**: toma la lista de tokens limpios del paso anterior y aplica dos filtros en secuencia:
> 1. **Stop Words:** elimina las palabras gramaticalmente vacías (artículos, preposiciones…).
> 2. **Reducción Morfológica:** comprime variantes de una misma raíz léxica en una sola forma.

---

## 1. Stop Words: ¿Qué Son y Por Qué Filtrarlas?

Las **stop words** (*palabras vacías*) son palabras tan frecuentes en el idioma que no aportan señal discriminante para clasificar un texto. Si TF-IDF las ve, les asigna un IDF muy bajo (aparecen en casi todos los documentos), pero ocupan espacio y ralentizan el modelo.

**Ejemplos de stop words en español:**
> `el`, `la`, `los`, `de`, `en`, `para`, `con`, `un`, `que`, `se`, `es`, `su`…

**Sin filtro:**
> `["se", "busca", "conductor", "de", "camion", "con", "experiencia", "en", "logistica"]`

**Con filtro:**
> `["conductor", "camion", "experiencia", "logistica"]`
> *(El clasificador ahora trabaja solo con las palabras que realmente distinguen un empleo de otro.)*

---

## 2. El Peligro de Filtrar Sin Cuidado: Las Negaciones

> [!WARNING] El error más común en NLP de sentimiento/clasificación
> Filtrar `"no"`, `"sin"`, `"nunca"` destruye la semántica del texto:
> - `"Sin experiencia requerida"` → `["experiencia", "requerida"]` → ¡El modelo lo confunde con textos que **sí** exigen experiencia!
> - `"No es necesario título"` → `["necesario", "titulo"]` → Pierde el matiz negativo por completo.

Las librerías estándar (spaCy y NLTK) **sí incluyen** estas palabras en su lista de stop words porque en textos generales son frecuentes. Para clasificación de empleo debemos blindarlas.

---

## 3. Solución Implementada: NEGACIONES_BLINDADAS + keep_words

Se definió un conjunto doble de protección:

### 3.1 Constante hardcoded en morphology.py

```python
# src/nlp/morphology.py
NEGACIONES_BLINDADAS: Set[str] = {
    "no", "ni", "nunca", "jamas", "jamás", "nada", "tampoco",
    "sin", "nadie", "bien", "mal", "bueno", "buena",
    "muy", "poco", "mas", "más", "menos", "pero",
}
```

Estas palabras **nunca** pueden ser stop words, sin importar lo que diga cualquier librería.

### 3.2 Lista configurable en params.yaml

```yaml
# params.yaml → sección nlp
nlp:
  keep_words:
    - "no"
    - "sin"
    - "nunca"
    # refuerzo explícito configurable sin tocar el código
  extra_stopwords:
    - "busca"     # "se busca" es jerga de reclutamiento sin valor semántico
    - "requiere"
    - "necesita"
    - "empresa"
    - "puesto"
    # ...
```

`keep_words` refuerza desde configuración, `extra_stopwords` añade jerga de empleo que la lista estándar no conoce.

---

## 4. Flujo de Construcción del Conjunto de Stop Words

```
spaCy STOP_WORDS (es_core_news_sm)
         +
params.yaml → extra_stopwords
         |
         v
 desacentuar_conservando_ene(w.lower())  ← misma función usada en tokens
         |
         v
  stopwords_normalizadas (conjunto unificado)
         |
         v
  ¿Palabra en NEGACIONES_BLINDADAS o keep_words?
         |
    Sí ──┘── No
    |            |
Eliminar      Quedarse
del conjunto  en el conjunto
         |
         v
  Conjunto final seguro
```

> [!IMPORTANT] Alineación con la normalización
> Las stop words se desacentúan con **la misma función** (`desacentuar_conservando_ene`) que se usó para limpiar los tokens. Si el token dice `"camion"` (sin tilde), la stop word también dice `"camion"`. Sin este paso, la comparación falla silenciosamente y no filtra nada.

---

## 5. Reducción Morfológica: Stemming vs Lematización

Ambas técnicas buscan lo mismo: que `"conductor"`, `"conductores"` y `"conducción"` sean tratados como la misma unidad para el modelo. Difieren en cómo llegan ahí.

| Criterio        | Stemming (Snowball)                                 | Lematización (spaCy)                        |
| --------------- | --------------------------------------------------- | ------------------------------------------- |
| **Algoritmo**   | Heurístico: recorta sufijos según reglas del idioma | Morfosintáctico: usa diccionario gramatical |
| **Resultado**   | Raíz aproximada (`"cociner"`)                       | Forma canónica real (`"cocinar"`)           |
| **Velocidad**   | Muy rápido                                          | Más lento (carga modelo neuronal)           |
| **Precisión**   | Media (puede producir no-palabras)                  | Alta (siempre produce una palabra real)     |
| **Dependencia** | Solo NLTK                                           | spaCy + modelo `es_core_news_sm`            |

### Ejemplo concreto calculado a mano

| Token original | Stem (Snowball) | Lema (spaCy) |
|---|---|---|
| `cocinero` | `cociner` | `cocinero` |
| `cocinera` | `cociner` | `cocinero` |
| `cocinando` | `cocin` | `cocinar` |
| `cocina` | `cocin` | `cocinar` |
| `conductor` | `conduct` | `conductor` |
| `conductores` | `conduct` | `conductor` |

> [!TIP] Decisión del proyecto
> El parámetro `metodo` en `reducir_morfologia(tokens, metodo="stem")` permite cambiar entre `"stem"` y `"lemma"` **sin tocar el código**. El valor por defecto es `"stem"` por ser más rápido en producción; `"lemma"` es preferible si se prioriza precisión lingüística.

---

## 6. Las Funciones Creadas en src/nlp/morphology.py

| Función | Entrada | Salida | Rol |
|---|---|---|---|
| `cargar_config_nlp()` | ruta opcional | `Dict` | Lee `params.yaml` con manejo de error seguro |
| `obtener_stemmer_nltk()` | — | `SnowballStemmer` | Singleton con `@lru_cache` para no reinstanciar |
| `obtener_spacy_nlp()` | — | modelo spaCy | Singleton con `@lru_cache`; desactiva `ner` y `parser` innecesarios |
| `obtener_stopwords_personalizadas()` | fuente, flags | `Set[str]` | Construye el conjunto final con protección de negaciones |
| `filtrar_stopwords(tokens)` | `List[str]` | `List[str]` | Aplica el filtro sobre una lista de tokens |
| `aplicar_stemming(tokens)` | `List[str]` | `List[str]` | Delega en Snowball Stemmer de NLTK |
| `aplicar_lematizacion(tokens)` | `List[str]` | `List[str]` | Delega en spaCy y desacentúa el lema resultante |
| `reducir_morfologia(tokens, metodo)` | `List[str]`, `str` | `List[str]` | Selector: llama a stem o lemma según parámetro |

### ¿Por qué @lru_cache?

El `@lru_cache` es un decorador (*decorator*, función que envuelve a otra función) que **guarda el resultado de la primera llamada** en memoria. Si el stemmer o el modelo de spaCy ya se cargaron, la segunda llamada los recupera instantáneamente sin recargarlos desde disco.

```
Primera llamada:  obtener_stemmer_nltk() → carga el modelo (~100ms)
Segunda llamada:  obtener_stemmer_nltk() → retorna el objeto ya en RAM (instantáneo)
```

---

## 7. Ejemplo de Flujo Completo Paso a Paso

**Texto crudo de entrada:**
> `"Se busca conductor de camión sin experiencia previa"`

**Después de Paso 2.1** (limpiar + tokenizar):
```python
["busca", "conductor", "camion", "sin", "experiencia", "previa"]
```

**Después de filtrar_stopwords():**
```python
# "busca" estaba en extra_stopwords → se elimina
# "sin" estaba en NEGACIONES_BLINDADAS → se PROTEGE y queda
["conductor", "camion", "sin", "experiencia", "previa"]
```

**Después de aplicar_stemming():**
```python
["conduct", "camion", "sin", "experienci", "previ"]
```

**Después de aplicar_lematizacion() (alternativa):**
```python
["conductor", "camión", "sin", "experiencia", "previo"]
```

---

## 8. Correcciones Durante el Desarrollo (Lecciones Aprendidas)

### Bug 1: "busca" no era stop word

`test_filtrar_stopwords_ejemplo_a_mano` fallaba porque `"busca"` no está en las listas estándar de spaCy ni NLTK (es un verbo conjugado frecuente pero con significado concreto).

**Solución:** añadir `"busca"` a `extra_stopwords` en `params.yaml`. Eso demuestra exactamente **para qué sirve** `extra_stopwords`: complementar la lista estándar con jerga de dominio específico (en este caso, jerga de reclutamiento).

### Bug 2: Snowball no produce "cocin" para "cocinero"

El test asumía que `cocinero` → `"cocin"`. Pero el algoritmo Snowball aplica reglas de sufijo en orden: primero intenta quitar `-ero`/`-era` → deja `"cociner"`. No llega a quitar la `-er` adicional porque la raíz resultante sería demasiado corta.

**Solución:** corregir las aserciones del test para reflejar el comportamiento **real** del algoritmo, no el imaginado.

> [!TIP] Regla práctica
> Para verificar un stemmer, siempre **ejecuta primero** y luego escribe el test. Nunca asumas la salida; los algoritmos de stemming son más conservadores de lo que parecen.

---

## 9. Pruebas Unitarias Verificadas (tests/test_morphology.py)

7 pruebas, todas pasando (`PASSED`):

| Test | Verifica |
|---|---|
| `test_stopwords_proteccion_estricta_negaciones` | Ninguna negación blindada aparece en el conjunto final |
| `test_stopwords_incluye_comodines_reclutamiento` | `"busca"`, `"requiere"` están en el conjunto construido |
| `test_filtrar_stopwords_ejemplo_a_mano` | Flujo real: `"busca"` se elimina, `"sin"` se protege |
| `test_aplicar_stemming_snowball` | `"cociner"` para `cocinero/a`, `"cocin"` para `cocinando/cocina` |
| `test_aplicar_lematizacion_spacy` | `"cocinar"` para `cocinando`, `"conductor"` para `conductores` |
| `test_reducir_morfologia_selector` | `metodo="stem"` y `metodo="lemma"` delegan correctamente |
| `test_casos_borde_morfologia` | Lista vacía → lista vacía, sin excepciones |

---

## 10. Comandos de Ejecución en Git Bash

```bash
# Solo las pruebas de este paso
.venv/Scripts/python -m pytest tests/test_morphology.py -v

# Suite completa
.venv/Scripts/python -m pytest -v
```

---

## 11. Dónde Cambiar lo Importante

| ¿Qué quieres cambiar? | ¿Dónde? |
|---|---|
| Añadir o quitar palabras protegidas (negaciones) | `params.yaml` → `nlp.keep_words` |
| Añadir jerga de empleo a filtrar | `params.yaml` → `nlp.extra_stopwords` |
| Cambiar entre stemming y lematización | Parámetro `metodo` en `reducir_morfologia()` |
| Cambiar la fuente de stop words base | Parámetro `fuente` en `obtener_stopwords_personalizadas(fuente="nltk")` |
| Añadir más negaciones hardcoded permanentes | Constante `NEGACIONES_BLINDADAS` en `src/nlp/morphology.py` |
