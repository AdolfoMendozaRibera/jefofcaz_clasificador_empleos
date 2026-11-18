---
title: "Paso 5.3: Pestaña 2 — Procesamiento Masivo CSV y Exportación (Batch.jsx)"
materia: "Tópicos y Programación Avanzada"
fase: "5"
paso: "5.3"
estado: "Completado ✅"
tags:
  - frontend
  - react
  - batch
  - csv
  - blob
  - kpi
  - pagination
  - overflow
---

# ✅ Paso 5.3: Pestaña 2 — Procesamiento Masivo CSV y Exportación (`Batch.jsx`)

> [!info] Propósito de este Paso
> Implementar la vista de procesamiento masivo orientada a negocio.
> Permite cargar archivos `.csv` con cientos de vacantes de empleo mediante Drag & Drop,
> ejecutar inferencias vectorizadas en Scikit-Learn mediante `POST /api/predict/batch`,
> visualizar KPIs inmediatos y exportar los resultados clasificados usando la API nativa de `Blob` de JavaScript.
> Cumple el **Punto 5.6 del PDF** y la sección 1 y 2 de [[web-fullstack.md]].

---

## 1. ¿Por Qué se Hizo Así? (Justificación Técnica)

1. **Inferencia Vectorizada en un Solo Pase:** A diferencia de llamar a `/api/predict` en un bucle lento en el frontend, el archivo CSV completo viaja en una sola petición `multipart/form-data`. El backend procesa toda la matriz TF-IDF de golpe, devolviendo cientos de predicciones en menos de 100 milisegundos.
2. **Descarga con API Nativa de `Blob`:** La exportación del archivo `reporte_clasificado.csv` se genera directamente en la memoria del navegador usando `new Blob()` y `URL.createObjectURL()`. **Cero carga adicional para el servidor backend**.
3. **Manejo del Estado de Borde *Overflow*:** Para evitar que una tabla con 500 filas congele el DOM o rompa el diseño visual de la pantalla, se implementó paginación (10 filas por vista) y un contenedor con scroll vertical independiente (`.table-overflow-container`).
4. **Plantilla de Prueba Integrada:** Se añadió el botón *"📥 Descargar CSV de Ejemplo"* con 10 vacantes reales para que el docente pueda probar la carga masiva en vivo sin necesidad de buscar un archivo en su computadora.

---

## 2. Mapa de Archivos Creados y Modificados

| Archivo | Acción | Descripción |
|---|---|---|
| [`frontend/src/components/Batch.jsx`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/frontend/src/components/Batch.jsx) | ✅ Creado | Vista completa: Drag & Drop, KPIs, distribución de sectores, tabla paginada y exportación con Blob. |
| [`frontend/src/styles.css`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/frontend/src/styles.css) | 🔄 Actualizado | Estilos para la zona `.dropzone`, grilla de KPIs (`.kpi-grid`), barras de distribución y `.pagination-bar`. |

---

## 3. Ejemplo Concreto: Exportación en el Cliente con `Blob`

En lugar de pedirle a FastAPI que genere y almacene un archivo temporal en disco, el frontend compila las líneas y dispara la descarga en el navegador:

```javascript
function exportarResultadosCSV() {
  const escapeCsv = (val) => `"${String(val || "").replace(/"/g, '""')}"`;
  
  const encabezados = ["id", "resumen_oferta", "sector_predicho", "probabilidad"];
  const filas = resultado.resultados.map((item) => [
    item.id,
    escapeCsv(item.texto_resumen),
    escapeCsv(item.sector_predicho),
    item.probabilidad,
  ]);

  const contenido = [encabezados.join(","), ...filas.map((f) => f.join(","))].join("\n");
  const blob = new Blob([contenido], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  
  const a = document.createElement("a");
  a.href = url;
  a.download = `reporte_clasificado_${resultado.total_procesados}_ofertas.csv`;
  a.click();
  URL.revokeObjectURL(url);
}
```

---

## 4. Los 4 Estados de Borde en `Batch.jsx`

- **Loading:** Tarjeta animada con `Skeleton` mientras se vectoriza la matriz en Scikit-Learn.
- **Empty:** Mensaje didáctico con el botón para descargar el CSV de prueba.
- **Error:** Caja roja `AlertError` si el archivo no es `.csv`, está vacío o carece de columna de texto.
- **Overflow:** Paginador interactivo con botones *"Anterior"* y *"Siguiente"* para lotes grandes.

---

## 5. Dónde Cambiar lo Importante

- **Cantidad de filas por página:** Constante `FILAS_POR_PAGINA = 10` en [`frontend/src/components/Batch.jsx`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/frontend/src/components/Batch.jsx).
- **Contenido del CSV de prueba:** Constante `CSV_EJEMPLO` en la cabecera de `Batch.jsx`.

