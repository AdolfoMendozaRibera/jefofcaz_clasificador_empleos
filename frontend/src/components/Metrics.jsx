import React, { useState, useEffect } from "react";
import { clienteApi } from "../api";
import { SECTORES, formatoPorcentaje, obtenerSectorInfo } from "../labels";
import { Card, SectorBadge, AlertError, Skeleton, EmptyState } from "./ui";

/**
 * Tabla comparativa fija de los modelos evaluados experimentalmente en la Fase 3.
 * Evidencia la progresión científica desde la línea base hasta el modelo campeón.
 */
const COMPARACION_MODELOS = [
  {
    modelo: "Línea Base (DummyClassifier)",
    estrategia: "Clase mayoritaria (most_frequent)",
    cvF1: "0.0892 (8.9 %)",
    testAcc: "28.7 %",
    estado: "Superado",
    esGanador: false,
  },
  {
    modelo: "Multinomial Naive Bayes",
    estrategia: "TF-IDF (1, 2) + Stemming + alpha=0.1",
    cvF1: "0.8915 (89.2 %)",
    testAcc: "89.4 %",
    estado: "Candidato",
    esGanador: false,
  },
  {
    modelo: "Regresión Logística Multinomial",
    estrategia: "TF-IDF (1, 2) + Stemming + C=2.0 (balanced)",
    cvF1: "0.9041 (90.4 %)",
    testAcc: "91.32 %",
    estado: "🏆 En Producción",
    esGanador: true,
  },
];

export function Metrics() {
  const [metricas, setMetricas] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);
  const [sectorSeleccionado, setSectorSeleccionado] = useState("construccion_mantenimiento");

  useEffect(() => {
    cargarMetricas();
  }, []);

  async function cargarMetricas() {
    setCargando(true);
    setError(null);
    try {
      const data = await clienteApi.obtenerMetricas();
      setMetricas(data);
      if (data.clases && data.clases.length > 0) {
        setSectorSeleccionado(data.clases[0]);
      }
    } catch (err) {
      setError(err.message || "No se pudieron cargar las métricas oficiales desde el backend.");
    } finally {
      setCargando(false);
    }
  }

  return (
    <div className="metrics-container">
      {/* Estado de Borde: Error */}
      {error && <AlertError mensaje={error} onRetry={cargarMetricas} />}

      {/* Estado de Borde: Loading */}
      {cargando && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          <div className="kpi-grid">
            {[1, 2, 3, 4].map((i) => (
              <Card key={i}>
                <Skeleton height="60px" />
              </Card>
            ))}
          </div>
          <Card>
            <Skeleton height="260px" />
          </Card>
        </div>
      )}

      {/* Estado de Borde: Empty */}
      {!metricas && !cargando && !error && (
        <Card>
          <EmptyState
            icon="📊"
            title="Sin métricas registradas"
            description="Ejecuta el entrenamiento en el backend para generar 'artifacts/metrics.json'."
          />
        </Card>
      )}

      {/* Dashboard Científico Completo */}
      {metricas && !cargando && (
        <div>
          {/* Fila 1: KPIs Científicos del Test Set (668 Ofertas a Ciegas) */}
          <div className="kpi-grid">
            <div className="kpi-card">
              <div className="kpi-label">F1-Score Macro Oficial</div>
              <div className="kpi-value" style={{ color: "var(--success)" }}>
                {formatoPorcentaje(metricas.f1_macro)}
              </div>
              <div className="kpi-sub">Métrica principal multiclase (no sesgada)</div>
            </div>

            <div className="kpi-card">
              <div className="kpi-label">Exactitud Global (Accuracy)</div>
              <div className="kpi-value" style={{ color: "var(--accent-primary)" }}>
                {formatoPorcentaje(metricas.accuracy)}
              </div>
              <div className="kpi-sub">Porcentaje total de aciertos en test</div>
            </div>

            <div className="kpi-card">
              <div className="kpi-label">Conjunto de Prueba (Test Set)</div>
              <div className="kpi-value mono">{metricas.total_test}</div>
              <div className="kpi-sub">20% partición estratificada sin fuga</div>
            </div>

            <div className="kpi-card">
              <div className="kpi-label">Errores Diagnosticados</div>
              <div className="kpi-value mono" style={{ color: "var(--warning)" }}>
                {metricas.total_errores}
              </div>
              <div className="kpi-sub">
                Solo {((metricas.total_errores / metricas.total_test) * 100).toFixed(1)}% fallos lingüísticos
              </div>
            </div>
          </div>

          {/* Fila 2: Matriz de Confusión con Mapa de Calor (Heatmap) */}
          <Card
            title="Matriz de Confusión Oficial (5 × 5)"
            icon="🎯"
            className="mt-4"
            action={
              <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                Evaluada sobre {metricas.total_test} ofertas de prueba
              </span>
            }
          >
            <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: "1rem" }}>
              Las filas representan el <strong>sector real</strong> y las columnas el <strong>sector predicho</strong>.
              Las celdas verdes en la diagonal principal corresponden a aciertos; la intensidad de color representa la
              proporción de aciertos por clase.
            </p>

            <div className="table-overflow-container">
              <table className="confusion-matrix">
                <thead>
                  <tr>
                    <th className="corner-th">Real ↓ / Predicho →</th>
                    {metricas.clases.map((claseKey) => {
                      const info = obtenerSectorInfo(claseKey);
                      return (
                        <th key={claseKey} className="col-header" title={info.nombre}>
                          <span>{info.icono}</span>
                          <span className="col-header-text">{info.nombre}</span>
                        </th>
                      );
                    })}
                  </tr>
                </thead>
                <tbody>
                  {metricas.matriz_confusion.map((fila, i) => {
                    const claseFila = metricas.clases[i];
                    const infoFila = obtenerSectorInfo(claseFila);
                    const totalFila = fila.reduce((a, b) => a + b, 0) || 1;

                    return (
                      <tr key={claseFila}>
                        <th className="row-header" style={{ color: infoFila.color }}>
                          <span>{infoFila.icono}</span>
                          <span>{infoFila.nombre}</span>
                        </th>
                        {fila.map((valor, j) => {
                          const esDiagonal = i === j;
                          const ratio = valor / totalFila;
                          const claseCol = metricas.clases[j];

                          return (
                            <td
                              key={claseCol}
                              className={`matrix-cell ${esDiagonal ? "hit" : valor > 0 ? "miss" : "zero"}`}
                              style={{
                                "--intensity": esDiagonal
                                  ? Math.max(0.18, ratio).toFixed(2)
                                  : Math.min(0.7, ratio * 2.5).toFixed(2),
                              }}
                              title={`Real: ${infoFila.nombre} → Predicho: ${obtenerSectorInfo(claseCol).nombre} (${valor} ofertas)`}
                            >
                              <div className="cell-value mono">{valor}</div>
                              <div className="cell-pct mono">{((valor / totalFila) * 100).toFixed(0)}%</div>
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Fila 3: Reporte Detallado por Clase (Precision, Recall, F1) */}
          <Card title="Reporte de Rendimiento por Sector Laboral" icon="📋" className="mt-4">
            <div className="table-overflow-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Sector Laboral</th>
                    <th style={{ textAlign: "right" }}>Precisión</th>
                    <th style={{ textAlign: "right" }}>Recall (Sensibilidad)</th>
                    <th style={{ textAlign: "right" }}>F1-Score</th>
                    <th style={{ textAlign: "right" }}>Soporte (Test)</th>
                  </tr>
                </thead>
                <tbody>
                  {metricas.clases.map((claseKey) => {
                    const rep = metricas.reporte_por_clase[claseKey] || {};
                    return (
                      <tr key={claseKey}>
                        <td>
                          <SectorBadge sectorKey={claseKey} />
                        </td>
                        <td className="mono" style={{ textAlign: "right" }}>
                          {formatoPorcentaje(rep.precision)}
                        </td>
                        <td className="mono" style={{ textAlign: "right" }}>
                          {formatoPorcentaje(rep.recall)}
                        </td>
                        <td className="mono" style={{ textAlign: "right", fontWeight: 700, color: "var(--success)" }}>
                          {formatoPorcentaje(rep.f1_score)}
                        </td>
                        <td className="mono" style={{ textAlign: "right", color: "var(--text-muted)" }}>
                          {rep.support}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Fila 4: Comparación Sistemática de Modelos (Punto 5.2 del PDF) */}
          <Card title="Comparación de Modelos de Machine Learning" icon="🔬" className="mt-4">
            <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: "1rem" }}>
              Resultados de la validación cruzada estratificada ($k=5$) y evaluación ciega en el conjunto de prueba.
            </p>
            <div className="table-overflow-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Modelo Evaluado</th>
                    <th>Estrategia y Parámetros</th>
                    <th style={{ textAlign: "right" }}>F1 Macro (CV k=5)</th>
                    <th style={{ textAlign: "right" }}>Exactitud (Test)</th>
                    <th style={{ textAlign: "center" }}>Decisión</th>
                  </tr>
                </thead>
                <tbody>
                  {COMPARACION_MODELOS.map((item, idx) => (
                    <tr
                      key={idx}
                      style={{
                        backgroundColor: item.esGanador ? "rgba(16, 185, 129, 0.08)" : "transparent",
                      }}
                    >
                      <td style={{ fontWeight: item.esGanador ? 700 : 500 }}>{item.modelo}</td>
                      <td style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>{item.estrategia}</td>
                      <td className="mono" style={{ textAlign: "right" }}>
                        {item.cvF1}
                      </td>
                      <td className="mono" style={{ textAlign: "right" }}>
                        {item.testAcc}
                      </td>
                      <td style={{ textAlign: "center" }}>
                        <span
                          className="badge"
                          style={{
                            backgroundColor: item.esGanador ? "var(--success-bg)" : "var(--bg-tertiary)",
                            color: item.esGanador ? "var(--success)" : "var(--text-muted)",
                            border: `1px solid ${item.esGanador ? "var(--success)" : "var(--border-subtle)"}`,
                          }}
                        >
                          {item.estado}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Fila 5: Términos más Influyentes por Sector (Coeficientes de Regresión Logística) */}
          <Card title="Términos más Influyentes por Sector (Explicabilidad Global)" icon="💡" className="mt-4">
            <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: "1rem" }}>
              Palabras con mayores coeficientes matemáticos ($\beta$) aprendidos por la Regresión Logística.
              Estas raíces determinan la asignación de cada vacante.
            </p>

            {/* Selector de sector para explorar los términos */}
            <div className="sector-tabs">
              {metricas.clases.map((claseKey) => {
                const info = obtenerSectorInfo(claseKey);
                const activo = sectorSeleccionado === claseKey;

                return (
                  <button
                    key={claseKey}
                    className={`sector-tab-btn ${activo ? "active" : ""}`}
                    onClick={() => setSectorSeleccionado(claseKey)}
                    style={{
                      borderColor: activo ? info.color : "transparent",
                      color: activo ? info.color : "var(--text-muted)",
                      backgroundColor: activo ? info.bg : "var(--bg-tertiary)",
                    }}
                  >
                    <span>{info.icono}</span>
                    <span>{info.nombre}</span>
                  </button>
                );
              })}
            </div>

            {/* Lista de los 10 términos con barra de coeficiente */}
            <div className="terms-grid mt-4">
              {(() => {
                const listaTerminos =
                  (metricas.terminos_mas_influyentes &&
                    metricas.terminos_mas_influyentes[sectorSeleccionado]) ||
                  [];

                if (listaTerminos.length === 0) {
                  return <div style={{ color: "var(--text-muted)" }}>Sin términos registrados para este sector.</div>;
                }

                const maxPeso = Math.max(...listaTerminos.map((t) => t.peso)) || 1;
                const infoSector = obtenerSectorInfo(sectorSeleccionado);

                return listaTerminos.map((item, idx) => {
                  const ratio = (item.peso / maxPeso) * 100;

                  return (
                    <div key={idx} className="term-card">
                      <div className="term-header">
                        <span className="term-word mono">
                          #{idx + 1} {item.termino}
                        </span>
                        <span className="term-weight mono" style={{ color: infoSector.color }}>
                          +{item.peso.toFixed(2)}
                        </span>
                      </div>
                      <div className="prob-bar-track">
                        <div
                          className="prob-bar-fill"
                          style={{
                            width: `${ratio}%`,
                            backgroundColor: infoSector.color,
                          }}
                        />
                      </div>
                    </div>
                  );
                });
              })()}
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}

