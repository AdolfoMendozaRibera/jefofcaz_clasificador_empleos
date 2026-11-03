import React, { useState, useRef } from "react";
import { clienteApi } from "../api";
import { SECTORES, formatoPorcentaje, obtenerSectorInfo } from "../labels";
import { Card, SectorBadge, AlertError, EmptyState, Skeleton } from "./ui";

/**
 * Plantilla CSV de ejemplo para facilitar la prueba inmediata durante la evaluación.
 */
const CSV_EJEMPLO = `descripcion
Conductor de tráiler frigorífico ruta internacional carnet C+E y CAP
Cocinero para restaurante de menú del día elaboración de arroces y tapas
Asesor comercial para venta telefónica de seguros y fidelización B2B
Enfermera para residencia de mayores administración de medicación y curas
Oficial albañil de primera para obra y reformas alicatado solado
Repartidor de paquetería con furgoneta propia ruta local carnet B
Camarero de barra y comedor para cafetería turno rotativo
Comercial inmobiliario captación de pisos y atención al comprador
Auxiliar de enfermería para atención a personas dependientes en domicilio
Peón de albañilería para carga de materiales y desescombro en obra`;

export function Batch() {
  const [archivo, setArchivo] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState(null);
  const [paginaActual, setPaginaActual] = useState(1);
  const [arrastrando, setArrastrando] = useState(false);

  const fileInputRef = useRef(null);
  const FILAS_POR_PAGINA = 10;

  function manejarSeleccionArchivo(file) {
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".csv")) {
      setError("El archivo seleccionado debe tener formato .csv");
      setArchivo(null);
      return;
    }

    setArchivo(file);
    setError(null);
    setResultado(null);
    setPaginaActual(1);
  }

  function handleDrop(e) {
    e.preventDefault();
    setArrastrando(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      manejarSeleccionArchivo(e.dataTransfer.files[0]);
    }
  }

  async function procesarLote() {
    if (!archivo || cargando) return;

    setCargando(true);
    setError(null);

    try {
      const data = await clienteApi.clasificarLoteCSV(archivo);
      setResultado(data);
      setPaginaActual(1);
    } catch (err) {
      setError(err.message || "Error al procesar el archivo CSV.");
      setResultado(null);
    } finally {
      setCargando(false);
    }
  }

  function descargarPlantillaEjemplo() {
    const blob = new Blob([CSV_EJEMPLO], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "plantilla_ofertas_ejemplo.csv";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  function exportarResultadosCSV() {
    if (!resultado || !resultado.resultados || resultado.resultados.length === 0) return;

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
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  // Paginación para manejar el estado de borde Overflow
  const totalFilas = resultado ? resultado.resultados.length : 0;
  const totalPaginas = Math.ceil(totalFilas / FILAS_POR_PAGINA) || 1;
  const filasPaginadas = resultado
    ? resultado.resultados.slice(
        (paginaActual - 1) * FILAS_POR_PAGINA,
        paginaActual * FILAS_POR_PAGINA
      )
    : [];

  return (
    <div className="batch-container">
      {/* Selector y zona de carga Drag & Drop */}
      <Card
        title="Procesamiento Masivo de Ofertas Laborales (CSV)"
        icon="📂"
        action={
          <button className="btn btn-outline" onClick={descargarPlantillaEjemplo} style={{ padding: "0.35rem 0.75rem", fontSize: "0.8rem" }}>
            📥 Descargar CSV de Ejemplo
          </button>
        }
      >
        <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginBottom: "1.25rem" }}>
          Sube un archivo con cientos de vacantes. El backend vectorizará las ofertas en un solo pase
          matricial con Scikit-Learn y devolverá la distribución por sector junto con la clasificación individual.
        </p>

        {/* Zona Drag & Drop */}
        <div
          className={`dropzone ${arrastrando ? "drag-over" : ""} ${archivo ? "has-file" : ""}`}
          onDragOver={(e) => {
            e.preventDefault();
            setArrastrando(true);
          }}
          onDragLeave={() => setArrastrando(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current && fileInputRef.current.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            style={{ display: "none" }}
            onChange={(e) => manejarSeleccionArchivo(e.target.files[0])}
            disabled={cargando}
          />
          <div className="dropzone-icon">📁</div>
          {archivo ? (
            <div>
              <div style={{ fontWeight: 600, color: "var(--text-primary)" }}>{archivo.name}</div>
              <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
                {(archivo.size / 1024).toFixed(1)} KB · Clic para seleccionar otro archivo
              </div>
            </div>
          ) : (
            <div>
              <div style={{ fontWeight: 600, color: "var(--text-primary)" }}>
                Arrastra tu archivo .CSV aquí o haz clic para explorar
              </div>
              <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
                Debe contener una columna llamada <code>descripcion</code>, <code>texto</code> u <code>oferta</code>.
              </div>
            </div>
          )}
        </div>

        {/* Botón de acción con Anti-Double Submit */}
        <div style={{ marginTop: "1.25rem", display: "flex", gap: "0.75rem", alignItems: "center" }}>
          <button
            className="btn btn-primary"
            onClick={procesarLote}
            disabled={!archivo || cargando}
            style={{ minWidth: "220px" }}
          >
            {cargando ? "Clasificando lote vectorizado..." : "Clasificar Archivo CSV"}
          </button>
          {archivo && (
            <button
              className="btn btn-outline"
              onClick={() => {
                setArchivo(null);
                setResultado(null);
                setError(null);
              }}
              disabled={cargando}
            >
              Quitar archivo
            </button>
          )}
        </div>

        {/* Estado de Borde: Error (HTTP 400 / 422) */}
        {error && <AlertError mensaje={error} onRetry={procesarLote} />}
      </Card>

      {/* Estado de Borde: Loading */}
      {cargando && (
        <Card title="Vectorizando y clasificando lote..." icon="⚡" className="mt-4">
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem", padding: "1.5rem 0" }}>
            <div style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
              Procesando matriz TF-IDF en Scikit-Learn y calculando probabilidades Softmax...
            </div>
            <Skeleton height="35px" width="100%" />
            <Skeleton height="80px" width="100%" />
            <Skeleton height="120px" width="100%" />
          </div>
        </Card>
      )}

      {/* Estado de Borde: Empty */}
      {!resultado && !cargando && (
        <Card className="mt-4">
          <EmptyState
            icon="📊"
            title="Esperando archivo CSV"
            description="Carga un archivo de vacantes laborales o descarga nuestra plantilla de prueba para ver el resumen estadístico de sectores y la tabla detallada de predicciones."
          />
        </Card>
      )}

      {/* Resultados de la Clasificación Masiva */}
      {resultado && !cargando && (
        <div className="batch-results-wrapper mt-4">
          {/* Tarjetas KPI de Resumen */}
          <div className="kpi-grid">
            <div className="kpi-card">
              <div className="kpi-label">Total Ofertas Evaluadas</div>
              <div className="kpi-value">{resultado.total_procesados}</div>
              <div className="kpi-sub">Procesadas en 1 pase matricial</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-label">Tiempo de Inferencia</div>
              <div className="kpi-value mono">{resultado.tiempo_total_ms} ms</div>
              <div className="kpi-sub">
                {(resultado.tiempo_total_ms / resultado.total_procesados).toFixed(2)} ms / oferta
              </div>
            </div>
            <div className="kpi-card">
              <div className="kpi-label">Sector con Mayor Demanda</div>
              <div className="kpi-value-sector">
                {(() => {
                  const dist = resultado.distribucion_sectores || {};
                  const mayor = Object.entries(dist).reduce(
                    (max, [k, v]) => (v > max.val ? { key: k, val: v } : max),
                    { key: "", val: -1 }
                  );
                  return mayor.key ? (
                    <SectorBadge sectorKey={mayor.key} />
                  ) : (
                    <span>N/A</span>
                  );
                })()}
              </div>
              <div className="kpi-sub">Mayor concentración en el lote</div>
            </div>
          </div>

          {/* Gráfico / Distribución por Sector */}
          <Card title="Distribución de Vacantes por Sector" icon="📈" className="mt-4">
            <div className="distribution-bars">
              {Object.keys(SECTORES).map((key) => {
                const info = SECTORES[key];
                const cantidad = (resultado.distribucion_sectores && resultado.distribucion_sectores[key]) || 0;
                const porcentaje = resultado.total_procesados > 0 ? (cantidad / resultado.total_procesados) : 0;

                return (
                  <div key={key} className="dist-row">
                    <div className="dist-label">
                      <span style={{ color: info.color }}>
                        {info.icono} {info.nombre}
                      </span>
                      <span className="mono" style={{ color: "var(--text-secondary)" }}>
                        {cantidad} ({formatoPorcentaje(porcentaje)})
                      </span>
                    </div>
                    <div className="prob-bar-track">
                      <div
                        className="prob-bar-fill"
                        style={{
                          width: `${Math.min(porcentaje * 100, 100)}%`,
                          backgroundColor: info.color,
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>

          {/* Tabla Detallada con Overflow y Paginación */}
          <Card
            title={`Detalle de Ofertas Clasificadas (${resultado.total_procesados})`}
            icon="📋"
            className="mt-4"
            action={
              <button className="btn btn-primary" onClick={exportarResultadosCSV} style={{ padding: "0.45rem 1rem", fontSize: "0.85rem" }}>
                📥 Descargar CSV Enriquecido (Blob)
              </button>
            }
          >
            <div className="table-overflow-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th style={{ width: "60px" }}>#</th>
                    <th>Resumen de la Oferta Laboral</th>
                    <th style={{ width: "260px" }}>Sector Asignado</th>
                    <th style={{ width: "110px", textAlign: "right" }}>Confianza</th>
                  </tr>
                </thead>
                <tbody>
                  {filasPaginadas.map((item) => (
                    <tr key={item.id}>
                      <td className="mono" style={{ color: "var(--text-muted)" }}>
                        {item.id}
                      </td>
                      <td style={{ color: "var(--text-secondary)" }}>{item.texto_resumen}</td>
                      <td>
                        <SectorBadge sectorKey={item.sector_predicho} />
                      </td>
                      <td className="mono" style={{ textAlign: "right", fontWeight: 600 }}>
                        {formatoPorcentaje(item.probabilidad)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Controles de Paginación */}
            {totalPaginas > 1 && (
              <div className="pagination-bar">
                <span style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                  Página {paginaActual} de {totalPaginas} ({totalFilas} ofertas)
                </span>
                <div style={{ display: "flex", gap: "0.5rem" }}>
                  <button
                    className="btn btn-outline"
                    disabled={paginaActual === 1}
                    onClick={() => setPaginaActual((p) => Math.max(p - 1, 1))}
                    style={{ padding: "0.35rem 0.75rem", fontSize: "0.8rem" }}
                  >
                    Anterior
                  </button>
                  <button
                    className="btn btn-outline"
                    disabled={paginaActual === totalPaginas}
                    onClick={() => setPaginaActual((p) => Math.min(p + 1, totalPaginas))}
                    style={{ padding: "0.35rem 0.75rem", fontSize: "0.8rem" }}
                  >
                    Siguiente
                  </button>
                </div>
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}

