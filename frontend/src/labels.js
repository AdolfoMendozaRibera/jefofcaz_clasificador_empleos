/**
 * Diccionario visual oficial para la categorización en 5 sectores laborales.
 * Centraliza nombres amigables, iconos y tokens de color semánticos.
 */

export const SECTORES = {
  transporte_logistica: {
    id: "transporte_logistica",
    nombre: "Transporte y Logística",
    icono: "🚛",
    color: "var(--sector-transporte)",
    bg: "var(--sector-transporte-bg)",
    border: "var(--sector-transporte-border)",
  },
  hosteleria_gastronomia: {
    id: "hosteleria_gastronomia",
    nombre: "Hostelería y Gastronomía",
    icono: "🍳",
    color: "var(--sector-hosteleria)",
    bg: "var(--sector-hosteleria-bg)",
    border: "var(--sector-hosteleria-border)",
  },
  ventas_comercial: {
    id: "ventas_comercial",
    nombre: "Ventas y Comercial",
    icono: "💼",
    color: "var(--sector-ventas)",
    bg: "var(--sector-ventas-bg)",
    border: "var(--sector-ventas-border)",
  },
  salud_servicios_sociales: {
    id: "salud_servicios_sociales",
    nombre: "Salud y Servicios Sociales",
    icono: "🩺",
    color: "var(--sector-salud)",
    bg: "var(--sector-salud-bg)",
    border: "var(--sector-salud-border)",
  },
  construccion_mantenimiento: {
    id: "construccion_mantenimiento",
    nombre: "Construcción y Mantenimiento",
    icono: "🏗️",
    color: "var(--sector-construccion)",
    bg: "var(--sector-construccion-bg)",
    border: "var(--sector-construccion-border)",
  },
};

/**
 * Formatea un valor decimal a porcentaje legible (ej: 0.9412 -> "94.1 %").
 * @param {number} valor - Proporción entre 0 y 1.
 * @returns {string} Cadena porcentual formateada.
 */
export function formatoPorcentaje(valor) {
  if (typeof valor !== "number" || isNaN(valor)) return "0.0 %";
  return `${(valor * 100).toFixed(1)} %`;
}

/**
 * Obtiene el objeto de estilo para un sector dado o un fallback seguro.
 * @param {string} sectorKey - Identificador del sector.
 * @returns {object} Metadatos del sector.
 */
export function obtenerSectorInfo(sectorKey) {
  return (
    SECTORES[sectorKey] || {
      id: sectorKey,
      nombre: sectorKey || "Desconocido",
      icono: "📋",
      color: "var(--text-muted)",
      bg: "var(--bg-tertiary)",
      border: "var(--border-subtle)",
    }
  );
}

