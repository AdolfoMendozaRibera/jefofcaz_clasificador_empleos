---
title: "Fase 0: Repositorio, Estructura Base, Librerías y Docker"
materia: "Tópicos y Programación Avanzada"
fase: "0"
estado: "Completada"
fecha: "2026-11-02"
tags:
  - fase0
  - git
  - docker
  - arquitectura
  - dependencias
  - modificacion-en-vivo
---

# 🏗️ Fase 0: Inicialización del Repositorio y Entorno

> [!tip] Resumen Ejecutivo
> En esta fase sentamos los cimientos del software: control de versiones con Git, desacoplamiento modular en carpetas estándar, aislamiento del entorno con Python 3.12 y orquestación con Docker multi-etapa. Nada de código improvisado: cada archivo responde a un criterio de la rúbrica de evaluación.

---

## 1. ¿Por qué se hizo esta fase primero?

En ingeniería de software y machine learning, el orden de construcción debe ser **reproducible y trazable**:
* Si empiezas programando modelos o interfaces sin Git ni estructura fija, los scripts se vuelven dependientes de rutas absolutas de tu máquina y no podrán ejecutarse en otra computadora ni en la del docente.
* El docente evalúa la constancia de los commits desde el día 1 (20 puntos individuales de la rúbrica).
* Las librerías de NLP (spaCy, scikit-learn) requieren versiones exactas para que el modelo serializado en un archivo `.joblib` no falle al cargarse en la API.

---

## 2. Mapa Completo de Archivos Creados y su Propósito

| Archivo / Carpeta                                                                                             | ¿Para qué sirve?                                                                                                                                                                                                        | ¿Por qué es vital para el examen?                                                                                                                                                       |
| ------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`.gitignore`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/.gitignore)                     | Lista de exclusión de Git. Evita subir archivos pesados, temporales o secretos (`.venv`, `__pycache__`, `artifacts/*.joblib`, `node_modules`, `Apunte/`).                                                               | Si subes la carpeta virtualenv o un `.joblib` de 100 MB, el repositorio se vuelve lento y viola las buenas prácticas de Git.                                                            |
| [`README.md`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/README.md)                       | Carta de presentación del proyecto. Explica el problema de negocio, los 5 sectores laborales, el diagrama de arquitectura y cómo levantarlo con Docker en 1 comando.                                                    | El punto 5.7 y 6.2 del PDF exigen un README completo con instrucciones claras de instalación.                                                                                           |
| [`CONTRIBUCIONES.md`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/CONTRIBUCIONES.md)       | Registro de la autoría de cada integrante del equipo, asociando tareas con sus commits de Git.                                                                                                                          | Requisito obligatorio del punto 6.2 (ítem 8). El docente coteja esta tabla con `git shortlog -sn`.                                                                                      |
| [`data/README.md`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/data/README.md)             | Ficha técnica formal del dataset `MiguelGP-13/JobOffers_ESP` (EURES 2025, licencia CC-BY 4.0, 7.261 filas y diccionario de columnas).                                                                                   | Exigencia directa del punto 5.1 del PDF ("documentar origen, licencia y fecha de obtención").                                                                                           |
| [`params.yaml`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/params.yaml)                   | **Fuente Única de Verdad** (Single Source of Truth). Centraliza semillas (`seed: 42`), rutas, umbrales de caracteres, palabras de negación protegidas, parámetros de TF-IDF y la grilla de búsqueda de hiperparámetros. | **Clave para la modificación en vivo (15 pts individuales):** Si el docente te pide *"cambia el parámetro C a 0.5"*, lo cambias aquí en 1 segundo y reentrenas sin tocar código Python. |
| [`requirements.txt`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/requirements.txt)         | Lista de dependencias de producción fijadas con versión exacta (`==`).                                                                                                                                                  | Evita el clásico *"en mi máquina funcionaba"*. Garantiza que Docker y tu máquina usen las mismas librerías.                                                                             |
| [`requirements-dev.txt`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/requirements-dev.txt) | Dependencias adicionales solo para desarrollo (`pytest`, `httpx`, `jupyterlab`, `matplotlib`, `seaborn`).                                                                                                               | Mantiene la imagen de producción ligera y reserva las herramientas de análisis para el entorno dev.                                                                                     |
| [`Dockerfile`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/Dockerfile)                     | Receta para compilar la imagen Docker en dos etapas: `runtime` (API y entrenador) y `dev` (tests y notebooks).                                                                                                          | Permite levantar el proyecto completo en cualquier sistema operativo sin instalar Python manualmente.                                                                                   |
| [`docker-compose.yml`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/docker-compose.yml)     | Orquestador de servicios: `trainer` (entrena primero), `api` (FastAPI), `frontend` (React + Nginx) y perfiles dev (`tests` y `notebook`).                                                                               | Ejecuta todo el sistema con un solo comando: `docker compose up --build`.                                                                                                               |
| [`.dockerignore`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/.dockerignore)               | Filtra archivos innecesarios para que no se envíen al demonio de Docker durante el build.                                                                                                                               | Acelera drásticamente la velocidad de compilación de los contenedores.                                                                                                                  |

---

## 3. Estructura de Carpetas Creada

```text
jefofcaz_clasificador_empleos/
├── data/
│   ├── raw/             # Datos originales inmutables (se descargan aqui, nunca se tocan a mano)
│   ├── processed/       # Dataset preparado (5 sectores balanceados)
│   └── README.md        # Documentacion tecnica de los datos
├── notebooks/           # Jupyter Notebooks para el EDA y experimentacion interactiva
├── src/
│   ├── data/            # Descarga, preparacion y particion estratificada
│   ├── nlp/             # Modulo de procesamiento de texto (normalizacion, lematizacion, stop words)
│   ├── models/          # Entrenamiento, validacion cruzada y analisis de errores
│   └── pipeline.py      # Script principal que orquesta todo el entrenamiento
├── api/                 # Backend REST modular (FastAPI: schemas, service, main)
├── frontend/            # Interfaz web React + Vite (auditoria paso a paso y carga masiva)
├── artifacts/           # model.joblib y metrics.json generados tras entrenar
├── tests/               # Pruebas automatizadas con pytest
├── docs/                # Informe tecnico final (docs/informe_tecnico.md)
├── Apunte/              # Apuntes locales para Obsidian (ignorado en Git)
├── params.yaml          # Configuracion centralizada
├── Dockerfile           # Imagen Docker
└── docker-compose.yml   # Orquestador de contenedores
```

---

## 4. Las Librerías Seleccionadas y ¿Para Qué Sirve Cada Una?

### 🔬 Datos y Machine Learning
* **`scikit-learn==1.9.1`:** El núcleo del modelado. Provee `TfidfVectorizer`, los clasificadores (`MultinomialNB`, `LogisticRegression`), `StratifiedKFold`, `GridSearchCV` y las métricas de evaluación (`classification_report`, `confusion_matrix`, `f1_score`).
* **`pandas==3.1.0`:** Carga y transformación de tablas de datos (`DataFrame`). Filtrado de oficios en los 5 sectores y detección de valores nulos o duplicados.
* **`numpy==2.5.4`:** Operaciones numéricas matriciales de alto rendimiento requeridas por Scikit-Learn.
* **`joblib==1.6.0`:** Serialización eficiente a disco. Empaqueta el pipeline completo (`TextPreprocessor` + `TfidfVectorizer` + `LogisticRegression`) en un único archivo binario [`artifacts/model.joblib`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/artifacts/model.joblib).

### 📝 Procesamiento de Lenguaje Natural (NLP)
* **`spacy==3.8.16` + `es_core_news_sm`:** Procesador lingüístico industrial para español. Proporciona lematización precisa basada en dependencias morfosintácticas (`es_core_news_sm`), reconociendo conjugaciones verbales complejas (`trabajando` → `trabajar`, `hicieron` → `hacer`).
* **`nltk==3.10.4`:** Provee el algoritmo morfológico **Snowball Stemmer** en español (`SnowballStemmer("spanish")`), necesario para contrastar experimentalmente *Stemming vs Lematización*.
* **`emoji==2.16.0`:** Normalización o limpieza de emoticones y símbolos visuales en el texto de las ofertas.

### ⚙️ Configuración y Backend
* **`pyyaml==6.0.3`:** Permite leer el archivo central [`params.yaml`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/params.yaml) como un diccionario de Python.
* **`fastapi==0.161.0` + `uvicorn==0.54.0`:** Framework web asíncrono y de alto rendimiento para exponer la API REST. Valida los datos de entrada con Pydantic y genera documentación Swagger automática en `/docs`.
* **`pytest==9.1.1`:** Framework de pruebas automáticas para verificar que la normalización conserve las negaciones y que la API responda HTTP 422 ante textos vacíos.

---

## 5. El "Secreto" de los Volúmenes en Docker (Vital para la Modificación en Vivo)

En [`docker-compose.yml`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/docker-compose.yml) configuramos volúmenes mapeados:

```yaml
volumes:
  - ./artifacts:/app/artifacts
```

> [!important] ¿Por qué esto es clave para la defensa oral?
> Cuando el contenedor `trainer` termina de entrenar, escribe el nuevo `model.joblib` en `/app/artifacts`. Gracias al volumen mapeado, ese archivo aparece **instantáneamente en tu máquina local y en el contenedor de FastAPI**. No tienes que recompilar la imagen Docker ni reiniciar el servidor para que la API empiece a usar el nuevo modelo.

---

## 6. Ejemplo Práctico: ¿Cómo se Defiende la "Modificación en Vivo" (15 Pts)?

Imagina que en la defensa oral el docente te dice:
> *"Quiero ver qué pasa si limitas el vocabulario de TF-IDF a 1.000 palabras en vez de 4.000, o si cambias el peso de regularización C de la Regresión Logística a 0.1"*.

**Cómo lo resuelves en 3 pasos:**
1. **Paso 1:** Abres [`params.yaml`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/params.yaml) y cambias:
   ```yaml
   tfidf:
     max_features: 1000   # Antes: 4000
   ```
2. **Paso 2:** En la terminal ejecutas el comando de entrenamiento:
   ```powershell
   .venv\Scripts\python.exe -m src.pipeline
   ```
3. **Paso 3:** Explicas el resultado al docente:
   > *"Al reducir el vocabulario a 1.000 términos, el modelo entrena más rápido pero el F1-Score disminuyó un 2.1% porque palabras técnicas especializadas quedaron fuera del vocabulario"*.
   
¡Cero cambios de código Python a mano y respuesta profesional garantizada!
