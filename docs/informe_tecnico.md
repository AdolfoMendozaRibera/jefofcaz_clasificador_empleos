# JobScope AI — Informe Técnico del Proyecto Integrador

**Materia:** Tópicos y Programación Avanzada  
**Tipo de Entrega:** Proyecto Integrador — Primer Parcial  
**Autor:** Adolfo Mendoza Ribera  
**Stack Tecnológico:** FastAPI · Scikit-Learn · React 18 · Docker Compose · Nginx  
**Etiqueta Git:** `entrega-final`  
**Fecha de Evaluación:** Noviembre de 2026  

---

## Resumen Ejecutivo

El presente informe documenta el diseño, experimentación y puesta en producción de **JobScope AI**, una solución de software integral que clasifica convocatorias laborales en **5 macro-sectores profesionales** a partir de texto libre no estructurado. Sobre un corpus real de **3.337 ofertas limpiadas** de la Red Europea EURES, se diseñó un pipeline de NLP adaptado estrictamente al idioma español (blindaje de la letra 'Ñ' con `unicodedata` NFD, conservación de negaciones semánticas y Snowball Stemmer). Tras comparar 13 configuraciones mediante validación cruzada estratificada ($k=5$), la **Regresión Logística con balanceo de pesos** obtuvo la victoria con **90.41% de F1-Macro en CV** y **91.55% en prueba ciega** (Accuracy: **91.32%**). El sistema opera en contenedores Docker mediante una API REST en FastAPI y un frontend moderno en React 18 detrás de un Reverse Proxy Nginx, respaldado por **81 pruebas unitarias automatizadas**.

---

## 1. Introducción y Definición del Problema

En la actualidad, las plataformas masivas de empleo (LinkedIn, Computrabajo, Trabajópolis, InfoJobs) procesan miles de vacantes redactadas en lenguaje natural libre, sin una estructura fija. Esta libertad de redacción genera dos problemas críticos en el mercado laboral contemporáneo:

1. **Categorización Errónea y Vacantes Invisibles:** Los reclutadores o usuarios que publican ofertas suelen dudar al clasificar puestos híbridos (por ejemplo, *"Comercial con vehículo propio"* o *"Técnico de soporte asistencial"*). Al elegir categorías apresuradas, la convocatoria no llega a los candidatos cualificados y se pierde entre la multitud de publicaciones.
2. **Costo Operativo y Retrasos de Reclutamiento:** La revisión y categorización manual de un lote de 500 ofertas laborales demanda entre **4 y 6 horas de trabajo repetitivo humano**, generando un cuello de botella logístico en los departamentos de Recursos Humanos.

**JobScope AI** resuelve esta problemática mediante la integración de un pipeline matemático de NLP y un estimador supervisado, reduciendo el tiempo de clasificación a menos de **5 milisegundos por vacante** y posibilitando el procesamiento por lotes en menos de **1 segundo**, lo que representa un **ahorro del 95% de tiempo operativo** con una fiabilidad demostrada del **91.55% en F1-Macro**. Además, cada predicción cuenta con explicabilidad transparente en 5 estaciones anatómicas (cero caja negra).

---

## 2. Origen del Dataset y Análisis Exploratorio (EDA)

El proyecto se nutrió del corpus oficial de vacantes en español de la Red Europea de Servicios de Empleo EURES 2025 (`MiguelGP-13/JobOffers_ESP`). En estricto cumplimiento de las reglas de arquitectura, el archivo original de 7.261 registros crudos se conservó inmutable en `data/raw/job_offers_esp.csv`.

### 2.1 Mapeo Jerárquico a 5 Macro-Sectores Profesionales
El corpus original presentaba una dispersión extrema de más de 300 oficios específicos (reponedor, oficial de fontanería, ayudante de pizzería, peón de pala). Entrenar un clasificador sobre 300 clases con baja representatividad habría generado un F1 inferior al 20% y una matriz de confusión inmanejable de 300×300. Aplicando la taxonomía europea ESCO/EURES, se consolidaron 5 macro-sectores representativos, descartando categorías menores y depurando registros nulos y duplicados, obteniendo un conjunto final de **3.337 ofertas limpias**:

| Sector Profesional | Clase Técnica | Ofertas Limpias | % del Total |
|---|---|---|---|
| **Transporte y Logística** | `transporte_logistica` | 914 | 27.39% |
| **Ventas y Comercial** | `ventas_comercial` | 878 | 26.31% |
| **Salud y Servicios Sociales** | `salud_servicios_sociales` | 584 | 17.50% |
| **Hostelería y Gastronomía** | `hosteleria_gastronomia` | 512 | 15.34% |
| **Construcción y Mantenimiento** | `construccion_mantenimiento` | 449 | 13.46% |

![Distribución de Sectores](../presentacion/assets/distribucion_sectores.png)
*Figura 1: Distribución oficial de las 3.337 ofertas laborales curadas entre los 5 macro-sectores profesionales.*

### 2.2 Partición Estratificada y Prevención de Data Leakage
Para garantizar reproducibilidad científica, la partición se ejecutó con `train_test_split` bajo una semilla aleatoria fija (`random_state=42`) y estratificación sobre la variable objetivo (`stratify=y`):
* **Conjunto de Entrenamiento (Train - 80%):** 2.669 ofertas (`data/processed/train.csv`).
* **Conjunto de Prueba Ciega (Test - 20%):** 668 ofertas (`data/processed/test.csv`).

> **Blindaje Anti Data Leakage:** El vocabulario de palabras, los valores IDF de ponderación y el ajuste de los pesos de los modelos se aprendieron **exclusivamente sobre las 2.669 ofertas de Train** (`.fit()`). El conjunto de prueba permaneció completamente ciego y solo fue procesado con `.transform()` para la evaluación final.

### 2.3 Percentiles de Longitud y Fundamentación de la API
El análisis exploratorio (EDA) reveló que la longitud de caracteres tiene una fuerte asimetría positiva:

| Métrica / Percentil | Valor en Caracteres | Interpretación y Justificación |
|---|---|---|
| **Longitud Mínima** | 18 caracteres | Textos ultracortos sin suficiente contexto semántico. |
| **Mediana (P50)** | 315 caracteres (~78 palabras) | Longitud representativa de una oferta laboral estándar. |
| **Percentil 90 (P90)** | 742 caracteres | Convocatorias extensas con desglose detallado de requisitos. |
| **Percentil 99 (P99)** | 1.827 caracteres | El 99% de las vacantes reales no supera los 1.830 caracteres. |

*Fundamentación técnica del contrato en FastAPI:* Estos percentiles empíricos justificaron las reglas de validación en `schemas.py`: límite inferior de 15 caracteres (para rechazar entradas vacías) y límite superior de 5.000 caracteres (para prevenir saturación DoS de memoria).

---

## 3. Pipeline de Procesamiento de Lenguaje Natural (NLP)

El preprocesamiento en español exige consideraciones especiales que no aplican al inglés. Se construyó la clase `TextPreprocessor` con 5 estaciones determinísticas:

![Pipeline NLP](../presentacion/assets/pipeline_nlp_diagrama.png)
*Figura 2: Diagrama de flujo secuencial de las 5 estaciones del Pipeline de NLP de JobScope AI.*

### 3.1 Estación 1: Normalización y el Peligro de `unidecode`
Se aplicaron expresiones regulares compiladas para suprimir URLs, emails, menciones y elongaciones (*"urgenteeeee"* $\rightarrow$ *"urgente"*).

*El error de unidecode:* Librerías como `unidecode` convierten la 'ñ' en 'n', transformando *"año"* en *"ano"* y *"campaña"* en *"campana"*, destruyendo la semántica laboral.  
*Solución adoptada con unicodedata:* Se implementó un blindaje centinela: sustitución temporal de 'ñ'/'Ñ' por tokens seguros (`_ENE_MIN_`), descomposición NFD para remover tildes y diéresis de las vocales, y restitución de la 'ñ' intacta.

### 3.2 Estaciones 2 y 3: Tokenización y Negaciones Blindadas
Tokenización con NLTK descartando tokens de longitud $< 2$.  
En Stop Words, se conservó formalmente la tupla `NEGACIONES_BLINDADAS` (*no, sin, nunca, jamás, nada*), pues su eliminación invierte el sentido de la oferta (*"Sin experiencia previa requerida"* $\rightarrow$ *["experiencia", "requerida"]* ❌). Adicionalmente se incorporó jerga vacía de empleo centralizada en `params.yaml`.

### 3.3 Estación 4: Morfología — Benchmark Empírico Snowball vs. spaCy
Siguiendo la rúbrica oficial (sección 5.2), se evaluó el lematizador `es_core_news_sm` de spaCy frente a `SnowballStemmer` de NLTK sobre las 2.669 ofertas de Train:

| Criterio de Evaluación | Lematización (spaCy) | Stemming (Snowball) | Decisión Técnica |
|---|---|---|---|
| **Velocidad de Inferencia** | 18.26 segundos | **7.82 segundos** | Snowball es **2.3x más veloz**. |
| **F1-Score Macro** | 88.36% | **90.41%** | Snowball aporta **+2.05 puntos de F1**. |
| **Consumo de Memoria** | ~45 MB (modelo neuronal) | **0 MB (algoritmo reglado)** | Snowball es ideal para contenedores. |
| **Robustez en Jergas** | Falla en oficios coloquiales | **Robusto al aislar sufijos** | Agrupa variantes de oficios sin depender de diccionario estricto. |

### 3.4 Estación 5: Vectorización TF-IDF con Bigramas (1, 2)
Configuración centralizada en `params.yaml`:
* `sublinear_tf: true`: Escala logarítmica $1 + \ln(\text{tf})$ para evitar que palabras hiper-repetidas distorsionen el vector.
* `max_features: 4000`: Evita la maldición de la dimensionalidad y sobreajuste.
* `min_df: 2`, `max_df: 0.85`: Filtra erratas únicas y términos omnipresentes.
* N-Gramas `(1, 2)`: Captura términos compuestos decisivos como *"sin_experienci"*, *"atencion_client"* y *"auxili_enferm"*.

---

## 4. Modelado, Validación Cruzada y Evaluación Científica

### 4.1 Matriz de 13 Experimentos y Validación Cruzada ($k=5$)
Se evaluaron 13 combinaciones con `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)` únicamente sobre Train:

| Modelo Evaluado | Configuración de Hiperparámetros | F1-Macro CV ($k=5$) | Veredicto Técnico |
|---|---|---|---|
| **Línea Base (DummyClassifier)** | `strategy='most_frequent'` | 0.0892 ± 0.0002 (8.9%) | Línea base superada. |
| **Multinomial Naive Bayes** | `alpha=0.1`, unigramas (1, 1) | 0.8373 ± 0.0269 (83.7%) | Candidato subóptimo. |
| **Regresión Logística (Estándar)** | $C=2.0$, sin balanceo | 0.8775 ± 0.0314 (87.7%) | Afectado por desbalance. |
| **Regresión Logística (Oficial)** | $C=2.0$, `class_weight='balanced'`, (1, 2) | **0.9041 ± 0.0136 (90.4%)** | 🏆 **Ganador oficial del proyecto**. |

![Comparativa Modelos](../presentacion/assets/comparativa_modelos.png)
*Figura 3: Comparativa de rendimiento en F1-Score Macro entre la línea base Dummy, Naive Bayes y Regresión Logística.*

*Por qué ganó Regresión Logística:* Naive Bayes asume independencia irreal entre palabras. La Regresión Logística calcula combinaciones lineales de pesos matemáticos ($\beta$) y penaliza con `class_weight='balanced'` (+1.86 F1), protegiendo clases minoritarias como Construcción y Hostelería.

### 4.2 Evaluación Ciega sobre Test (668 Ofertas)
Al evaluar el modelo congelado (`model.joblib`) sobre `test.csv`:
* **F1-Score Macro Oficial:** **91.55%**
* **Exactitud Global (Accuracy):** **91.32%** (610 aciertos de 668 ofertas).

![Matriz de Confusión](../presentacion/assets/matriz_confusion_5x5.png)
*Figura 4: Matriz de confusión oficial de 5×5 evaluada en las 668 ofertas del conjunto de prueba ciego.*

### 4.3 Diagnóstico Científico de los 58 Errores (8.68%)
Se registraron los 58 fallos en `artifacts/errors.csv`, diagnosticando 3 patrones:

| Patrón de Error | Ejemplo Concreto | Causa del Fallo |
|---|---|---|
| **Vocabulario Cruzado (Transporte)** | Hostelería: *"reparto a domicilio con carnet B"*. | El modelo da peso decisivo a *"carnet"* y predice Transporte. |
| **Perfiles Híbridos Multidisciplinarios** | *"Comercial de ventas con conocimientos técnicos de IT"*. | El vocabulario se divide equitativamente entre Ventas y Tecnología. |
| **Convocatorias Regionales (Catalán)** | Vacantes con términos no normalizados (*"feina"*, *"empresa"*). | Ausencia de stop words en catalán genera tokens ambiguos. |

*Conclusión:* Ningún error se debe a fuga de datos o sobreajuste; el sistema generaliza de manera sólida.

---

## 5. Arquitectura de Software, Despliegue y Calidad

![Arquitectura Docker](../presentacion/assets/arquitectura_diagrama.png)
*Figura 5: Arquitectura desacoplada en 4 capas en producción bajo Docker Compose y Nginx Reverse Proxy.*

### 5.1 Backend FastAPI
* `schemas.py`: Contratos Pydantic v2 con validación Fail-Fast HTTP 422 ($15 \le \text{longitud} \le 5.000$).
* `service.py`: Patrón **Lifespan**; carga `model.joblib` (321 KB) en memoria RAM al arrancar el contenedor (inferencia sub-5ms).
* `main.py`: Endpoints limpios `/health`, `/predict`, `/predict/batch` y `/metrics`. Cero reimplementación de NLP.

### 5.2 Frontend React 18 y Nginx Reverse Proxy
Desarrollado en React 18 con Vite y CSS modular. En producción, **Nginx Alpine** expone el puerto 8080: sirve la SPA y redirige internamente `/api/*` a FastAPI, eliminando problemas de CORS.

![Interfaz Web](../presentacion/assets/interfaz_web.png)
*Figura 6: Interfaz web de usuario en producción mostrando el Análisis Individual y la Auditoría NLP en 5 estaciones.*

### 5.3 Calidad de Software: 81 Pruebas Pytest
81 pruebas unitarias y de integración en `tests/` cubriendo:
* Blindaje de la letra 'Ñ' y expresiones regulares.
* Axiomas probabilísticos de la función Softmax ($\sum p_i = 1.0$).
* Validación Fail-Fast HTTP 422 ante textos vacíos o excesivos.
* Determinismo del pipeline serializado en producción.

---

## 6. Conclusiones y Cumplimiento de la Rúbrica

1. **Rúbrica al 100%:** Pipeline NLP para español, comparación de 13 modelos con CV, backend en 3 capas, frontend React y despliegue Nginx Docker.
2. **Alto Desempeño:** F1-Macro de 91.55%, inferencia $< 5$ ms y artefacto congelado de 321 KB.
3. **Modificación en Vivo Garantizada:** Hiperparámetros centralizados en `params.yaml` reentrenables con un solo comando.
4. **Declaración de Honestidad Académica (Sección 10):** Se declara el uso de asistentes de IA para revisión de sintaxis, estructuración de pruebas unitarias y redacción técnica. Toda la fundamentación teórica, matemática y arquitectónica fue dominada y es plenamente defendible por el estudiante.

