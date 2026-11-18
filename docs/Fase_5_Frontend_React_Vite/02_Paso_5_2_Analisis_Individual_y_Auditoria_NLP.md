---
title: "Paso 5.2: Pestaña 1 — Análisis Individual y Auditoría NLP (Analyze.jsx)"
materia: "Tópicos y Programación Avanzada"
fase: "5"
paso: "5.2"
estado: "Completado ✅"
tags:
  - frontend
  - react
  - analyze
  - nlp-audit
  - explain
  - anti-double-submit
  - edge-states
---

# ✅ Paso 5.2: Pestaña 1 — Análisis Individual y Auditoría NLP (`Analyze.jsx`)

> [!info] Propósito de este Paso
> Implementar la vista interactiva principal donde el usuario ingresa cualquier oferta laboral libremente y el docente audita que cada estación del pipeline de NLP funciona en tiempo real.
> Cumple rigurosamente el **Punto 5.6 del PDF** y la regla de diseño [[web-fullstack.md]].

---

## 1. ¿Por Qué se Hizo Así? (Criterios de Evaluación)

1. **Explicabilidad en Vivo (Exigencia del PDF):** El docente no solo quiere ver el resultado final, sino **cómo llegó el modelo a esa conclusión**. La vista desglosa en 5 estaciones el texto recibido desde `/api/predict` consumiendo el método `.explain()` del `TextPreprocessor`.
2. **Botones de Ejemplo Rápido:** Para la defensa oral, tener 5 botones precargados (uno por cada sector arquetípico) permite demostrar el sistema en segundos sin tener que teclear párrafos enteros en vivo.
3. **Anti-Double Submit y Estados de Borde:**
   - Durante la petición a FastAPI, el botón se deshabilita (`disabled={cargando}`) y cambia a *"Analizando oferta con NLP..."*.
   - Si no hay texto, se muestra un estado `EmptyState` didáctico.
   - Mientras carga, se muestran `Skeleton` animados para evitar saltos de pantalla (cero CLS).
   - Si se ingresan menos de 15 caracteres o solo números, se captura el error **HTTP 422** en una alerta roja comprensible con botón *"Reintentar"*.

---

## 2. Mapa de Archivos Creados y Modificados

| Archivo | Acción | Descripción |
|---|---|---|
| [`frontend/src/components/Analyze.jsx`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/frontend/src/components/Analyze.jsx) | ✅ Creado | Componente de análisis en 2 columnas: formulario + auditoría NLP. |
| [`frontend/src/styles.css`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/frontend/src/styles.css) | 🔄 Actualizado | Clases CSS para grid responsivo (`.analyze-grid`), pasos de NLP (`.nlp-step`) y botones rápidos. |

---

## 3. Ejemplo Concreto: El Desglose Anatómico de NLP

Cuando el usuario hace clic en el ejemplo rápido de **Salud**:
> *"Centro sociosanitario y residencia de mayores requiere enfermero diplomado o graduado para administración de tratamientos y curas sin experiencia previa."*

La API responde y el componente `<Analyze />` dibuja la columna derecha estación por estación:

```text
1. Normalización Base
   "centro sociosanitario residencia mayores requiere enfermero diplomado graduado..."

2. Tokenización Limpia (14 tokens)
   ["centro", "sociosanitario", "residencia", "enfermero", ...]

3. Stop Words (con Negaciones Protegidas 🛡️)
   ["sociosanitario", "residencia", "enfermero", "sin 🛡️", "experiencia"]

4. Reducción Morfológica (Stemming Snowball)
   ["sociosanitari", "resident", "enferm", "sin", "experient"]

5. Entrada Vectorizada a TF-IDF
   "sociosanitari resident enferm sin experient"
```

> [!important] Valor para la Defensa Oral
> Se demuestra visualmente que la palabra clave de negación **`sin`** fue protegida con la regla de oro y no fue borrada como stop word, manteniendo el contexto semántico de *"sin experiencia"*.

---

## 4. Dónde Cambiar lo Importante

- **Para agregar o editar ofertas de ejemplo rápido:** Edita la constante `EJEMPLOS_RAPIDOS` en [`frontend/src/components/Analyze.jsx`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/frontend/src/components/Analyze.jsx).
- **Para ajustar el ancho de las columnas:** Modifica la media query `@media (min-width: 900px)` en [`frontend/src/styles.css`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/frontend/src/styles.css).

