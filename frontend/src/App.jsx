import React, { useState, useEffect } from "react";
import { clienteApi } from "./api";
import { Analyze } from "./components/Analyze";
import { Batch } from "./components/Batch";
import { Metrics } from "./components/Metrics";

export function App() {
  const [pestañaActiva, setPestañaActiva] = useState("analyze");
  const [salud, setSalud] = useState({ estado: "conectando", modeloCargado: false });

  useEffect(() => {
    verificarEstadoBackend();
    // Sondeo de estado cada 30 segundos
    const intervalo = setInterval(verificarEstadoBackend, 30000);
    return () => clearInterval(intervalo);
  }, []);

  async function verificarEstadoBackend() {
    try {
      const data = await clienteApi.obtenerSalud();
      setSalud({
        estado: data.estado === "ok" ? "ok" : "degradado",
        modeloCargado: Boolean(data.modelo_cargado),
        modeloNombre: data.modelo_nombre || "Regresión Logística",
      });
    } catch {
      setSalud({ estado: "error", modeloCargado: false, modeloNombre: null });
    }
  }

  return (
    <div className="app-container">
      {/* Cabecera Principal */}
      <header className="app-header">
        <div className="brand-wrapper">
          <div className="brand-icon">💼</div>
          <div>
            <h1 className="brand-title">JobScope NLP</h1>
            <p className="brand-subtitle">
              Clasificador Inteligente de Ofertas Laborales en 5 Sectores Económicos
            </p>
          </div>
        </div>

        {/* Indicador de Salud del Backend */}
        <div className="health-badge" title="Monitoreo en vivo vía GET /api/health">
          <span
            className={`health-dot ${
              salud.estado === "ok" ? "ok" : salud.estado === "error" ? "degraded" : ""
            }`}
          />
          <span style={{ color: salud.estado === "ok" ? "var(--text-secondary)" : "var(--error)" }}>
            {salud.estado === "ok"
              ? "Backend Conectado (v1.0.0)"
              : salud.estado === "conectando"
              ? "Conectando al backend..."
              : "Backend Desconectado"}
          </span>
        </div>
      </header>

      {/* Navegación por Pestañas (Flujos clave en ≤ 2 clics) */}
      <nav className="tabs-nav" aria-label="Navegación principal">
        <button
          className={`tab-button ${pestañaActiva === "analyze" ? "active" : ""}`}
          onClick={() => setPestañaActiva("analyze")}
        >
          <span>📝</span>
          <span>Análisis Individual</span>
        </button>

        <button
          className={`tab-button ${pestañaActiva === "batch" ? "active" : ""}`}
          onClick={() => setPestañaActiva("batch")}
        >
          <span>📂</span>
          <span>Procesamiento Masivo (CSV)</span>
        </button>

        <button
          className={`tab-button ${pestañaActiva === "metrics" ? "active" : ""}`}
          onClick={() => setPestañaActiva("metrics")}
        >
          <span>📊</span>
          <span>Dashboard de Métricas</span>
        </button>
      </nav>

      {/* Vistas Dinámicas */}
      <main>
        {pestañaActiva === "analyze" && <Analyze />}
        {pestañaActiva === "batch" && <Batch />}
        {pestañaActiva === "metrics" && <Metrics />}
      </main>

      {/* Pie de Página Técnico */}
      <footer className="app-footer">
        <div>
          <strong>JobScope NLP</strong> · Proyecto Integrador de Tópicos y Programación Avanzada
        </div>
        <div style={{ color: "var(--text-muted)", fontSize: "0.8rem", marginTop: "0.25rem" }}>
          Pipeline: TF-IDF (1, 2) + Stemming Snowball + Regresión Logística Softmax (F1-Macro: 91.55%) ·{" "}
          <a
            href="/docs"
            target="_blank"
            rel="noopener noreferrer"
            style={{ color: "var(--accent-primary)", textDecoration: "none" }}
          >
            Swagger API Docs ↗
          </a>
        </div>
      </footer>
    </div>
  );
}

export default App;

