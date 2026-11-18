---
title: "Paso 1.4: Partición Estratificada sin Fuga de Datos (Data Leakage)"
materia: "Tópicos y Programación Avanzada"
fase: "1"
paso: "1.4"
estado: "Completado"
tags:
  - fase1
  - data-leakage
  - train-test-split
  - estratificacion
  - reproduccion
  - scikit-learn
---

# 🛡️ Paso 1.4: Partición Estratificada sin Fuga de Datos (Data Leakage)

> [!info] ¿Qué se construyó en este paso?
> Se implementó el módulo de partición [`src/data/split_data.py`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/src/data/split_data.py) y su suite de pruebas unitarias en [`tests/test_split_data.py`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/tests/test_split_data.py).
> 
> Realiza la división matemática del dataset procesado en dos archivos físicos aislados:
> * **Conjunto de Entrenamiento (`data/processed/train.csv`):** 2.669 ofertas (80%).
> * **Conjunto de Evaluación (`data/processed/test.csv`):** 668 ofertas (20%).

---

## 1. El Concepto Clave: Fuga de Datos (*Data Leakage*) en NLP

### La Analogía del Examen Final
Si un estudiante tiene acceso a las preguntas y al vocabulario exacto del examen final antes de estudiar, obtendrá una calificación artificialmente perfecta (100/100). Sin embargo, cuando se enfrente al mundo real sin las respuestas filtradas, fallará rotundamente.

En NLP, **el vectorizador TF-IDF es quien "lee" el texto**:
- Si aplicamos TF-IDF a todo el dataset antes de separar `train` y `test`, el modelo aprenderá el vocabulario y las frecuencias inversas de documento (IDF) a partir de los datos de prueba.
- **Consecuencia:** Métricas de acierto (*Accuracy*, *F1-Score*) infladas y mentirosas en el reporte, pero degradación severa en producción cuando un usuario introduzca ofertas con palabras nuevas.

### La Regla de Oro en Scikit-Learn

```mermaid
flowchart TD
    D["data/processed/ofertas_5_sectores.csv<br/>(3.337 ofertas)"] -->|src/data/split_data.py| T1["Train Set (80%)<br/>2.669 ofertas"]
    D -->|src/data/split_data.py| T2["Test Set (20%)<br/>668 ofertas"]
    
    T1 -->|fit_transform| TF["Vectorizador TF-IDF<br/>(Aprende vocabulario e IDF de Train)"]
    TF -->|Entrena| M["Modelo (Naive Bayes / Logistic Regression)"]
    
    T2 -.->|SOLO transform<br/>(Evaluacion a ciegas)| M
```

* **En Train (`X_train`):** Se aplica **`fit_transform()`** (aprende vocabulario y calcula pesos numéricos).
* **En Test (`X_test`) y API FastAPI:** Se aplica **`transform()`** únicamente (utiliza solo lo aprendido; si hay palabras desconocidas, las descarta como Out-Of-Vocabulary).

---

## 2. ¿Por qué Estratificación (`stratify=y`)?

Como se identificó en el EDA, los 5 sectores presentan un **desbalance natural**:
- `salud_servicios_sociales`: 28.71%
- `transporte_logistica`: 27.39%
- `construccion_mantenimiento`: 25.65%
- `hosteleria_gastronomia`: 12.26%
- `ventas_comercial`: 5.99%

### ⚠️ El Peligro de No Estratificar (Ejemplo Intuitivo)
Imagina que tenemos una clase minoritaria con solo 10 ejemplos en un dataset de 200 filas (5%).
* Si hacemos una división puramente aleatoria (sin estratificar), la probabilidad de que por azar caigan muy pocos ejemplos (o ninguno) en el conjunto de prueba es alta.
* Si caen 0 ejemplos en `test`, ¡es matemáticamente imposible calcular el Recall o F1-Score de esa clase!
* **La Estratificación** obliga al algoritmo a calcular las proporciones exactas de cada sector y repartirlas uniformemente en ambos lados.

### Proporciones Reales Verificadas en Nuestro Proyecto:

| Sector                       | Original (3.337) | Train (2.669) | Test (668) | Diferencia |
| ---------------------------- | :--------------: | :-----------: | :--------: | :--------: |
| `salud_servicios_sociales`   |      28.71%      |    28.70%     |   28.74%   |  < 0.04%   |
| `transporte_logistica`       |      27.39%      |    27.39%     |   27.40%   |  < 0.01%   |
| `construccion_mantenimiento` |      25.65%      |    25.67%     |   25.60%   |  < 0.05%   |
| `hosteleria_gastronomia`     |      12.26%      |    12.25%     |   12.28%   |  < 0.02%   |
| `ventas_comercial`           |      5.99%       |     5.99%     |   5.99%    | **0.00%**  |

---

## 3. Ejemplo Mínimo Calculado a Mano (Verificado con Pytest)

En [`tests/test_split_data.py`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/tests/test_split_data.py) se comprueba este cálculo:

### Planteamiento a Mano:
* Dataset sintético de **10 ofertas**:
  * 6 ofertas de `ventas_comercial` (60%)
  * 4 ofertas de `hosteleria_gastronomia` (40%)
* Con `test_size=0.20`:
  * Total en `test`: $10 \times 0.20 = \mathbf{2\text{ ofertas}}$ $\rightarrow$ 1 de ventas y 1 de hostelería.
  * Total en `train`: $10 \times 0.80 = \mathbf{8\text{ ofertas}}$ $\rightarrow$ 5 de ventas y 3 de hostelería.

```python
# Verificacion unitaria exacta:
assert conteos_train["ventas_comercial"] == 5
assert conteos_train["hosteleria_gastronomia"] == 3
assert conteos_test["ventas_comercial"] == 1
assert conteos_test["hosteleria_gastronomia"] == 1
```

* **Resultado:** Pasa con aserción estricta en `pytest`.

---

## 4. Comandos de Ejecución y Validación

### Ejecutar la partición:
```powershell
.venv\Scripts\python.exe -m src.data.split_data
```

### Ejecutar las pruebas unitarias:
```powershell
.venv\Scripts\python.exe -m pytest tests/test_split_data.py -v
```

---

## 5. Dónde Cambiar lo Importante
* Proporción de división (`test_size: 0.20`): En [`params.yaml`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/params.yaml).
* Semilla reproducible (`seed: 42`): En [`params.yaml`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/params.yaml).
* Rutas de salida (`train_path`, `test_path`): En [`params.yaml`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/params.yaml).
