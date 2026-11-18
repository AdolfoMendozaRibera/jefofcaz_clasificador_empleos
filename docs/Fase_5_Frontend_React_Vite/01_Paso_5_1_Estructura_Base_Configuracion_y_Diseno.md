---
title: "Paso 5.1: Estructura Base, Configuración, Red y Tokens de Diseño"
materia: "Tópicos y Programación Avanzada"
fase: "5"
paso: "5.1"
estado: "Completado ✅"
tags:
  - frontend
  - react
  - vite
  - design-tokens
  - css-variables
  - api-client
  - labels
---

# ✅ Paso 5.1: Estructura Base, Configuración, Red y Tokens de Diseño

> [!info] Propósito de este Paso
> Construir los cimientos del Frontend de la aplicación.
> Siguiendo la regla de oro de arquitectura [[web-fullstack.md]], la interfaz se diseña de forma **100% desacoplada**:
> - Cero llamadas `fetch()` dispersas en componentes (todas centralizadas en `src/api.js`).
> - Cero colores o tamaños hardcodeados en línea (todos consumen **Tokens de Diseño con Variables CSS** en `src/styles.css`).
> - Diccionario visual tipado para los **5 sectores laborales oficiales** en `src/labels.js`.

---

## 1. ¿Por Qué se Hizo Así? (Justificación Técnica)

1. **Proxy en Vite (`vite.config.js`):** En desarrollo local, el frontend corre en el puerto `5173` y FastAPI en el `8000`. Al configurar el proxy para la ruta `/api`, el navegador cree que habla con el mismo servidor, eliminando de raíz cualquier error de **CORS** (*Cross-Origin Resource Sharing*).
2. **Tokens de Diseño en CSS (`:root`):** Prohíbe estilos huérfanos (`style={{ color: '#1a2b3c' }}`). Si el docente pide en la defensa cambiar el color de un sector o ajustar el modo oscuro, se cambia una sola variable CSS y se propaga a toda la web de inmediato.
3. **Manejo Amigable de Errores HTTP 422:** Cuando FastAPI rechaza una entrada inválida, el cliente `api.js` extrae el mensaje limpio en español para mostrarlo en una alerta roja comprensible para humanos, nunca un "TypeError" o código crudo.

---

## 2. Mapa de Archivos Creados y su Función

| Archivo | ¿Qué contiene? | ¿Por qué es vital? |
|---|---|---|
| [`frontend/package.json`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/frontend/package.json) | Configuración de React 18.3 y Vite 5.4. | Dependencias mínimas y ultrarrápidas sin sobrecarga de librerías globales. |
| [`frontend/vite.config.js`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/frontend/vite.config.js) | Configuración de proxy `/api` hacia `http://localhost:8000`. | Permite conectar frontend y backend sin problemas de CORS ni URLs fijas en componentes. |
| [`frontend/index.html`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/frontend/index.html) | Plantilla HTML5 con viewport accesible y meta tags. | Punto de montaje del árbol de componentes de React (`#root`). |
| [`frontend/src/labels.js`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/frontend/src/labels.js) | Diccionario de los 5 sectores (nombre, icono, colores). | Fuente única de verdad para la identidad visual de las clases laborales. |
| [`frontend/src/api.js`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/frontend/src/api.js) | Cliente HTTP con `fetch`, timeouts y control de errores. | Desacopla la lógica de red de los componentes de interfaz. |
| [`frontend/src/styles.css`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/frontend/src/styles.css) | Tokens CSS `:root`, modo oscuro, animaciones y layout. | Cumple la regla de cero estilos inline y define los 4 estados de borde. |
| [`frontend/src/components/ui.jsx`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/frontend/src/components/ui.jsx) | `Card`, `SectorBadge`, `ProbabilityBars`, `TokenList`, etc. | Componentes atómicos reutilizables para no duplicar código en las pantallas. |

---

## 3. Ejemplos Concretos de Implementación

### Ejemplo 1: El Diccionario Visual de Sectores (`src/labels.js`)
Cada sector tiene asociado su identificador oficial del dataset, nombre amigable con tildes, icono semántico y variables CSS:

```javascript
export const SECTORES = {
  transporte_logistica: {
    nombre: "Transporte y Logística",
    icono: "🚛",
    color: "var(--sector-transporte)",        // #38bdf8 (Azul celeste)
    bg: "var(--sector-transporte-bg)",
  },
  hosteleria_gastronomia: {
    nombre: "Hostelería y Gastronomía",
    icono: "🍳",
    color: "var(--sector-hosteleria)",         // #fb923c (Naranja)
    bg: "var(--sector-hosteleria-bg)",
  },
  ventas_comercial: {
    nombre: "Ventas y Comercial",
    icono: "💼",
    color: "var(--sector-ventas)",             // #34d399 (Verde)
    bg: "var(--sector-ventas-bg)",
  },
  salud_servicios_sociales: {
    nombre: "Salud y Servicios Sociales",
    icono: "🩺",
    color: "var(--sector-salud)",              // #f43f5e (Rosa médico)
    bg: "var(--sector-salud-bg)",
  },
  construccion_mantenimiento: {
    nombre: "Construcción y Mantenimiento",
    icono: "🏗️",
    color: "var(--sector-construccion)",       // #fbbf24 (Amarillo obra)
    bg: "var(--sector-construccion-bg)",
  },
};
```

### Ejemplo 2: Captura Limpia de Errores HTTP 422 en `src/api.js`
Si el usuario envía una oferta vacía o de 5 letras, la API responde con HTTP 422:
```json
{
  "status": "error",
  "mensaje": "El texto tiene 5 caracteres; el mínimo requerido es de 15 caracteres."
}
```
El cliente `api.js` extrae directamente ese mensaje para que el componente React lo pinte en la caja de alerta roja:
```javascript
// frontend/src/api.js
if (!respuesta.ok) {
  let mensajeError = datos.mensaje || datos.detail || "Error inesperado";
  const error = new Error(mensajeError);
  error.status = respuesta.status;
  throw error;
}
```

### Ejemplo 3: Componente `ProbabilityBars` (`src/components/ui.jsx`)
Dibuja las 5 barras de probabilidad porcentual con animación suave y respetando los colores del sector:
```jsx
// Uso en cualquier vista:
<ProbabilityBars probabilidades={{
  transporte_logistica: 0.9412,
  hosteleria_gastronomia: 0.0211,
  ventas_comercial: 0.0154,
  salud_servicios_sociales: 0.0118,
  construccion_mantenimiento: 0.0105
}} />
```

---

## 4. ¿Es Necesario `npm install` en tu Máquina?

> [!important] Aclaración Clave sobre Docker vs Local
> - **Con Docker Desktop:** **NO es necesario.** Al ejecutar `docker compose up --build`, Docker descarga Node dentro de su propio contenedor, ejecuta `npm install` y compila los archivos estáticos de forma transparente y aislada.
> - **El comando `source .venv/Scripts/activate`:** Es exclusivo de tu entorno de Python (para la API FastAPI y las 81 pruebas de pytest). No interfiere con el frontend.

---

## 5. Dónde Cambiar lo Importante

- **Para cambiar colores o márgenes:** Edita los tokens en [`frontend/src/styles.css`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/frontend/src/styles.css) bajo la regla `:root`.
- **Para cambiar textos o iconos de sectores:** Edita el objeto `SECTORES` en [`frontend/src/labels.js`](file:///e:/desarrollador/topicos/jefofcaz_clasificador_empleos/frontend/src/labels.js).

