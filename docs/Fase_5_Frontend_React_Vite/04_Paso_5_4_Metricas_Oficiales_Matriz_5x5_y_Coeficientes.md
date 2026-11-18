---
title: "Paso 5.4: Pestaña 3 — Métricas Oficiales, Matriz 5x5 y Coeficientes (Metrics.jsx)"
materia: "Tópicos y Programación Avanzada"
fase: "5"
paso: "5.4"
estado: "Completado ✅"
tags:
  - frontend
  - react
  - metrics
  - heatmap
  - confusion-matrix
  - model-comparison
  - coefficients
---

# ✅ Paso 5.4: Pestaña 3 — Métricas Oficiales, Matriz 5x5 y Coeficientes (`Metrics.jsx`)

> [!info] Propósito de este Paso
> Implementar el panel de control científico donde se presenta la evidencia cuantitativa del proyecto.
> Consume directamente el endpoint `GET /api/metrics` (respaldado por `artifacts/metrics.json`) sin recalcular nada en caliente.
> Cumple rigurosamente los **Puntos 5.2, 5.3 y 5.6 del PDF** y la sección 5 de [[web-fullstack.md]].

---

## 1. ¿Por Qué se Hizo Así? (Criterios de Evaluación y Defensa)

1. **Cero Recálculo en Caliente:** La matriz de confusión y el reporte por clase provienen del archivo congelado generado en la Fase 3 (`artifacts/metrics.json`). El navegador no ejecuta algoritmos pesados de Scikit-Learn; solo renderiza los datos serializados en una interfaz atractiva.
2. **Matriz de Confusión con Mapa de Calor (Heatmap $5 \times 5$):** Permite al docente ver visualmente dónde acierta el modelo y dónde se confunde. La intensidad del color verde en la diagonal refleja la tasa de aciertos por clase usando la variable CSS `--intensity`.
3. **Comparación Sistemática con Línea Base (Punto 5.2):** Se demuestra empíricamente por qué la Regresión Logística con Stemming y N-gramas (1, 2) fue la configuración campeona elegida frente a la Línea Base (`DummyClassifier`) y a `Naive Bayes`.
4. **Explicabilidad Global (Coeficientes $\beta$):** Al hacer clic en cualquiera de los 5 sectores, el docente puede comprobar qué palabras tienen mayor peso matemático positivo para clasificar las vacantes.

---

## 2. Mapa de Archivos Creados y Modificados

| Archivo | Acción | Descripción |
|---|---|---|
| [`frontend/src/components/Metrics.jsx`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/frontend/src/components/Metrics.jsx) | ✅ Creado | Dashboard completo: KPIs en test, Heatmap 5x5, tabla por sector, comparativa de modelos y explorador de coeficientes. |
| [`frontend/src/styles.css`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/frontend/src/styles.css) | 🔄 Actualizado | Clases CSS `.confusion-matrix`, celdas `.matrix-cell.hit` y `.miss`, `.sector-tabs` y grilla `.terms-grid`. |

---

## 3. Ejemplo Concreto: El Heatmap de la Matriz de Confusión

La matriz relaciona las filas (Sector Real) con las columnas (Sector Predicho):

```jsx
// En frontend/src/components/Metrics.jsx:
<td
  className={`matrix-cell ${esDiagonal ? "hit" : valor > 0 ? "miss" : "zero"}`}
  style={{ "--intensity": (valor / totalFila).toFixed(2) }}
>
  <div className="cell-value">{valor}</div>
  <div className="cell-pct">{((valor / totalFila) * 100).toFixed(0)}%</div>
</td>
```

### Datos Reales del Test Set (668 Ofertas) Visualizados:
- **Construcción:** 161 aciertos de 171 (94% de acierto). 10 ofertas confundidas con transporte (por maquinaria pesada).
- **Hostelería:** 76 aciertos de 82 (93% de acierto).
- **Salud:** 178 aciertos de 192 (93% de acierto).
- **Transporte:** 157 aciertos de 183 (86% de acierto).
- **Ventas:** 38 aciertos de 40 (95% de acierto).

---

## 4. Ejemplo Concreto: Explorador de Coeficientes Lingüísticos

El modelo aprendió qué términos definen inequívocamente a cada sector:

```javascript
// Si se selecciona "Construcción y Mantenimiento":
1. instal       (+4.16) ▓▓▓▓▓▓▓▓▓▓ 100%
2. albañil      (+4.05) ▓▓▓▓▓▓▓▓▓░  97%
3. manten       (+4.00) ▓▓▓▓▓▓▓▓▓░  96%
4. construccion (+3.92) ▓▓▓▓▓▓▓▓▓░  94%
```

> [!tip] Utilidad para la Pregunta Teórica del Docente
> Si el docente pregunta: *"¿Por qué una oferta de fontanería se clasificó como construcción?"*, puedes abrir esta pestaña y demostrar que la raíz `instal` tiene el coeficiente positivo más alto del sector.

---

## 5. Dónde Cambiar lo Importante

- **Para modificar la tabla de comparación de modelos:** Edita la lista `COMPARACION_MODELOS` en [`frontend/src/components/Metrics.jsx`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/frontend/src/components/Metrics.jsx).
- **Para ajustar los colores de las celdas del Heatmap:** Edita las clases `.matrix-cell.hit` (verde) y `.matrix-cell.miss` (rojo tenue) en [`frontend/src/styles.css`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/frontend/src/styles.css).

