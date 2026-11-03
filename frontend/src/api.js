/**
 * Cliente HTTP desacoplado para la API REST de FastAPI.
 * Toda llamada a la red se centraliza aquí; ningún componente hace fetch directo.
 */

const BASE_URL = "/api";

/**
 * Función base para realizar peticiones HTTP con control de errores y timeout.
 * @param {string} endpoint - Ruta relativa al BASE_URL.
 * @param {RequestInit} [options={}] - Configuración de fetch.
 * @returns {Promise<any>} Respuesta JSON decodificada.
 */
async function peticion(endpoint, options = {}) {
  const controlador = new AbortController();
  const idTimeout = setTimeout(() => controlador.abort(), 20000); // 20 segundos de timeout

  try {
    const respuesta = await fetch(`${BASE_URL}${endpoint}`, {
      ...options,
      signal: controlador.signal,
    });

    const datos = await respuesta.json().catch(() => null);

    if (!respuesta.ok) {
      let mensajeError = "Ocurrió un error inesperado al consultar el servidor.";

      if (datos) {
        if (typeof datos.mensaje === "string") {
          mensajeError = datos.mensaje;
        } else if (typeof datos.detail === "string") {
          mensajeError = datos.detail;
        } else if (Array.isArray(datos.detalle) && datos.detalle.length > 0) {
          mensajeError = datos.detalle[0].mensaje || mensajeError;
        }
      }

      const error = new Error(mensajeError);
      error.status = respuesta.status;
      error.datos = datos;
      throw error;
    }

    return datos;
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("El servidor tardó demasiado en responder (tiempo límite agotado).");
    }
    throw error;
  } finally {
    clearTimeout(idTimeout);
  }
}

export const clienteApi = {
  /**
   * Consulta el estado de salud del backend y confirmación de modelo en RAM.
   */
  obtenerSalud: () => peticion("/health"),

  /**
   * Clasifica una oferta de trabajo individual y extrae la auditoría de NLP.
   * @param {string} texto - Descripción textual de la vacante.
   */
  clasificarOferta: (texto) =>
    peticion("/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texto }),
    }),

  /**
   * Carga un archivo CSV con ofertas de empleo para procesamiento masivo vectorizado.
   * @param {File} archivo - Archivo .csv seleccionado por el usuario.
   */
  clasificarLoteCSV: (archivo) => {
    const formData = new FormData();
    formData.append("archivo", archivo);
    return peticion("/predict/batch", {
      method: "POST",
      body: formData,
    });
  },

  /**
   * Obtiene las métricas oficiales, matriz de confusión 5x5 y términos influyentes.
   */
  obtenerMetricas: () => peticion("/metrics"),
};

