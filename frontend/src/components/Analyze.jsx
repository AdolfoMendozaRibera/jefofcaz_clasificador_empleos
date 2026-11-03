import React, { useState } from "react";
import { clienteApi } from "../api";
import { SECTORES, formatoPorcentaje, obtenerSectorInfo } from "../labels";
import {
  Card,
  SectorBadge,
  ProbabilityBars,
  TokenList,
  AlertError,
  EmptyState,
  Skeleton,
} from "./ui";

/**
 * Ofertas de empleo arquetípicas para demostración ágil en la defensa oral.
 * Cubren los 5 sectores e incluyen casos con palabras de negación.
 */
const EJEMPLOS_RAPIDOS = [
  {
    sectorId: "transporte_logistica",
    label: "🚛 Transporte",
    texto:
      "Se busca conductor de camión tráiler para ruta nacional e internacional con carnet C+E, CAP en vigor y tarjeta de tacógrafo digital.",
  },
  {
    sectorId: "hosteleria_gastronomia",
    label: "🍳 Hostelería",
    texto:
      "Restaurante de comida tradicional busca cocinero y jefe de partida para elaboración de menús diarios, partidas de carne y control de APPCC.",
  },
  {
    sectorId: "ventas_comercial",
    label: "💼 Ventas",
    texto:
      "Empresa líder selecciona asesor comercial para captación y prospección de clientes B2B, concertación de visitas y cierre de ventas inmobiliarias.",
  },
  {
    sectorId: "salud_servicios_sociales",
    label: "🩺 Salud",
    texto:
      "Centro sociosanitario y residencia de mayores requiere enfermero diplomado o graduado para administración de tratamientos y curas sin experiencia previa.",
  },
  {
    sectorId: "construccion_mantenimiento",
    label: "🏗️ Construcción",
    texto:
      "Empresa de reformas precisa oficiales de primera albañiles para colocación de ladrillo, alicatado, tabiquería y solados en obra nueva.",
  },
];

export function Analyze() {
  const [texto, setTexto] = useState("");
  const [cargando, setCargando] = useState(false);
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState(null);

  // Validación rápida en el cliente
  const longitud = texto.trim().length;
  const esTextoValido = longitud >= 15 && longitud <= 5000;

  async function clasificar() {
    if (!esTextoValido || cargando) return;

    setCargando(true);
    setError(null);

    try {
      const data = await clienteApi.clasificarOferta(texto.trim());
      setResultado(data);
    } catch (err) {
      setError(err.message || "Error al clasificar la oferta.");
      setResultado(null);
    } finally {
      setCargando(false);
    }
  }

  function cargarEjemplo(ejemploTexto) {
    setTexto(ejemploTexto);
    setError(null);
  }

  function limpiar() {
    setTexto("");
    setResultado(null);
    setError(null);
  }

  return (
    <div className="analyze-container">
      {/* Selector de ejemplos rápidos para la defensa oral */}
      <div className="quick-examples-bar">
        <span className="quick-examples-title">⚡ Pruebas rápidas:</span>
        <div className="quick-examples-buttons">
          {EJEMPLOS_RAPIDOS.map((ej, idx) => (
            <button
              key={idx}
              className="btn btn-outline quick-btn"
              onClick={() => cargarEjemplo(ej.texto)}
              disabled={cargando}
            >
              {ej.label}
            </button>
          ))}
        </div>
      </div>

      {/* Grid de 2 columnas: Formulario a la izquierda y Auditoría a la derecha */}
      <div className="analyze-grid">
        {/* Columna Izquierda: Formulario y Resultados */}
        <div className="analyze-column">
          <Card title="Descripción de la Oferta Laboral" icon="📝">
            <div className="textarea-wrapper">
              <label htmlFor="oferta-input" style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                Ingresa el texto de la vacante de empleo:
              </label>
              <textarea
                id="oferta-input"
                className="textarea-field"
                placeholder="Ejemplo: Se precisa conductor de camión con experiencia en reparto de mercancías..."
                value={texto}
                onChange={(e) => setTexto(e.target.value)}
                disabled={cargando}
              />
              <div className="textarea-meta">
                <span>
                  {longitud < 15 ? (
                    <span style={{ color: "var(--warning)" }}>Mínimo 15 caracteres (actual: {longitud})</span>
                  ) : longitud > 5000 ? (
                    <span style={{ color: "var(--error)" }}>Supera el límite de 5.000 caracteres</span>
                  ) : (
                    <span>{longitud} caracteres</span>
                  )}
                </span>
                {texto && (
                  <button
                    onClick={limpiar}
                    disabled={cargando}
                    style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer", fontSize: "0.8rem" }}
                  >
                    Borrar texto
                  </button>
                )}
              </div>
            </div>

            {/* Botón con Anti-Double Submit */}
            <div style={{ marginTop: "1.25rem", display: "flex", gap: "0.75rem" }}>
              <button
                className="btn btn-primary"
                onClick={clasificar}
                disabled={!esTextoValido || cargando}
                style={{ flex: 1 }}
              >
                {cargando ? "Analizando oferta con NLP..." : "Clasificar Empleo"}
              </button>
            </div>

            {/* Estado de Borde: Error (HTTP 422) */}
            {error && <AlertError mensaje={error} onRetry={clasificar} />}
          </Card>

          {/* Resultado de la Inferencia */}
          {cargando && (
            <Card title="Procesando inferencia..." icon="⏳" className="mt-4">
              <div style={{ display: "flex", flexDirection: "column", gap: "1rem", padding: "1rem 0" }}>
                <Skeleton height="35px" width="60%" />
                <Skeleton height="15px" width="100%" />
                <Skeleton height="15px" width="90%" />
                <Skeleton height="15px" width="75%" />
              </div>
            </Card>
          )}

          {resultado && !cargando && (
            <Card title="Resultado de la Clasificación" icon="🎯" className="mt-4">
              <div className="winner-card" style={{ borderColor: obtenerSectorInfo(resultado.sector_predicho).border }}>
                <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: "0.25rem" }}>
                  Sector Predicho:
                </div>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "0.5rem" }}>
                  <SectorBadge sectorKey={resultado.sector_predicho} />
                  <span className="mono" style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--text-primary)" }}>
                    {formatoPorcentaje(resultado.probabilidad)}
                  </span>
                </div>
                <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "0.5rem" }}>
                  Inferencia calculada en <span className="mono">{resultado.tiempo_ms} ms</span>
                </div>
              </div>

              {/* Distribución de Probabilidades Softmax */}
              <div style={{ marginTop: "1.5rem" }}>
                <h4 style={{ fontSize: "0.95rem", marginBottom: "0.5rem", color: "var(--text-secondary)" }}>
                  Probabilidad por Sector (Softmax):
                </h4>
                <ProbabilityBars probabilidades={resultado.probabilidades} />
              </div>
            </Card>
          )}
        </div>

        {/* Columna Derecha: Auditoría de NLP Paso a Paso (Exigencia PDF) */}
        <div className="analyze-column">
          <Card title="Auditoría NLP Paso a Paso" icon="🔬">
            {!resultado && !cargando && (
              <EmptyState
                icon="🔍"
                title="Sin análisis activo"
                description="Selecciona un ejemplo rápido de la barra superior o escribe una oferta laboral para auditar cómo se transforma el texto en cada estación del pipeline de NLP."
              />
            )}

            {cargando && (
              <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem", padding: "1rem" }}>
                <Skeleton height="40px" />
                <Skeleton height="60px" />
                <Skeleton height="60px" />
                <Skeleton height="40px" />
              </div>
            )}

            {resultado && !cargando && (
              <div className="nlp-pipeline-steps">
                {/* Estación 1: Normalización Base */}
                <div className="nlp-step">
                  <div className="nlp-step-header">
                    <span className="nlp-step-number">1</span>
                    <div>
                      <h4 className="nlp-step-title">Normalización Base</h4>
                      <p className="nlp-step-desc">
                        Conversión a minúsculas, eliminación de URLs, teléfonos y limpieza de caracteres manteniendo la letra <strong>ñ</strong>.
                      </p>
                    </div>
                  </div>
                  <div className="nlp-step-content mono">
                    {resultado.preprocesamiento.texto_normalizado || "(vacío)"}
                  </div>
                </div>

                {/* Estación 2: Tokenización */}
                <div className="nlp-step">
                  <div className="nlp-step-header">
                    <span className="nlp-step-number">2</span>
                    <div>
                      <h4 className="nlp-step-title">Tokenización Limpia</h4>
                      <p className="nlp-step-desc">
                        Segmentación léxica de palabras individuales ({resultado.preprocesamiento.tokens.length} tokens detectados).
                      </p>
                    </div>
                  </div>
                  <TokenList items={resultado.preprocesamiento.tokens} variant="standard" />
                </div>

                {/* Estación 3: Stop Words con Negaciones Protegidas */}
                <div className="nlp-step">
                  <div className="nlp-step-header">
                    <span className="nlp-step-number">3</span>
                    <div>
                      <h4 className="nlp-step-title">Filtrado de Stop Words</h4>
                      <p className="nlp-step-desc">
                        Se eliminan palabras vacías pero se <strong>blindan las negaciones</strong> (ej: <em>no</em>, <em>sin</em>, <em>nunca</em>) para no alterar el sentido de la oferta.
                      </p>
                    </div>
                  </div>
                  <TokenList
                    items={resultado.preprocesamiento.sin_stopwords.map((token) =>
                      ["no", "sin", "nunca", "jamas", "nada", "tampoco", "nadie"].includes(token.toLowerCase())
                        ? `${token} 🛡️`
                        : token
                    )}
                    variant="protected"
                  />
                </div>

                {/* Estación 4: Reducción Morfológica (Stemming Snowball) */}
                <div className="nlp-step">
                  <div className="nlp-step-header">
                    <span className="nlp-step-number">4</span>
                    <div>
                      <h4 className="nlp-step-title">Reducción Morfológica (Stemming)</h4>
                      <p className="nlp-step-desc">
                        Extracción de lexemas o raíces morfológicas de cada palabra.
                      </p>
                    </div>
                  </div>
                  <TokenList items={resultado.preprocesamiento.raices} variant="pair" />
                </div>

                {/* Estación 5: Cadena Vectorizada en TF-IDF */}
                <div className="nlp-step">
                  <div className="nlp-step-header">
                    <span className="nlp-step-number">5</span>
                    <div>
                      <h4 className="nlp-step-title">Entrada Vectorizada a TF-IDF</h4>
                      <p className="nlp-step-desc">
                        Texto final que alimenta la matriz de unigramas y bigramas (1, 2).
                      </p>
                    </div>
                  </div>
                  <div className="nlp-step-content mono">
                    {resultado.preprocesamiento.texto_procesado || "(vacío)"}
                  </div>
                </div>
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}

