import React from "react";
import { SECTORES, formatoPorcentaje, obtenerSectorInfo } from "../labels";

/**
 * Tarjeta contenedor estándar con cabecera opcional.
 */
export function Card({ title, icon, action, children, className = "" }) {
  return (
    <div className={`card ${className}`}>
      {(title || action) && (
        <div className="card-header">
          <div className="card-title">
            {icon && <span>{icon}</span>}
            {title && <span>{title}</span>}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      {children}
    </div>
  );
}

/**
 * Badge o pastilla semántica de sector.
 */
export function SectorBadge({ sectorKey }) {
  const info = obtenerSectorInfo(sectorKey);
  return (
    <span
      className="badge"
      style={{
        backgroundColor: info.bg,
        color: info.color,
        border: `1px solid ${info.border}`,
      }}
    >
      <span>{info.icono}</span>
      <span>{info.nombre}</span>
    </span>
  );
}

/**
 * Barras horizontales de probabilidad para los 5 sectores laborales.
 */
export function ProbabilityBars({ probabilidades = {} }) {
  const sectoresKeys = Object.keys(SECTORES);

  return (
    <div className="probability-group">
      {sectoresKeys.map((key) => {
        const info = SECTORES[key];
        const prob = probabilidades[key] || 0;
        const porcentaje = formatoPorcentaje(prob);

        return (
          <div key={key} className="prob-row">
            <div className="prob-header">
              <span style={{ color: info.color }}>
                {info.icono} {info.nombre}
              </span>
              <span className="mono" style={{ color: "var(--text-secondary)" }}>
                {porcentaje}
              </span>
            </div>
            <div className="prob-bar-track">
              <div
                className="prob-bar-fill"
                style={{
                  width: `${Math.min(prob * 100, 100)}%`,
                  backgroundColor: info.color,
                }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

/**
 * Renderizador de chips lingüísticos para tokens y palabras clave.
 */
export function TokenList({ items = [], variant = "standard" }) {
  if (!items || items.length === 0) {
    return <span style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>(ninguno)</span>;
  }

  return (
    <div className="tokens-container">
      {items.map((item, idx) => (
        <span key={idx} className={`token-chip ${variant}`}>
          {item}
        </span>
      ))}
    </div>
  );
}

/**
 * Estado de borde: Error comprensible con botón de reintento.
 */
export function AlertError({ mensaje, onRetry }) {
  if (!mensaje) return null;
  return (
    <div className="state-error" role="alert">
      <div>
        <strong>Error: </strong>
        <span>{mensaje}</span>
      </div>
      {onRetry && (
        <button className="btn btn-outline" onClick={onRetry} style={{ padding: "0.4rem 0.8rem", fontSize: "0.8rem" }}>
          Reintentar
        </button>
      )}
    </div>
  );
}

/**
 * Estado de borde: Placeholder o estado vacío interactivo.
 */
export function EmptyState({ icon = "📝", title, description, children }) {
  return (
    <div className="state-empty">
      <div className="state-empty-icon">{icon}</div>
      {title && <h3 style={{ marginBottom: "0.5rem", color: "var(--text-secondary)" }}>{title}</h3>}
      {description && <p style={{ maxWidth: "420px", marginBottom: "1rem" }}>{description}</p>}
      {children}
    </div>
  );
}

/**
 * Estado de borde: Skeleton animado durante la carga.
 */
export function Skeleton({ height = "20px", width = "100%", style = {} }) {
  return <div className="skeleton-box" style={{ height, width, ...style }} />;
}

