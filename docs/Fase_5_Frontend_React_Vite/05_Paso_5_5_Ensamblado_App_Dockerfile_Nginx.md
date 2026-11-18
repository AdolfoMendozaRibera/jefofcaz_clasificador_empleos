# 🚀 Paso 5.5: Ensamblado Final de la App, Dockerfile Nginx y Reverse Proxy

Este documento registra la arquitectura de ensamblado de la aplicación web completa, la orquestación mediante Docker Compose, el contenedor de producción con Nginx como Reverse Proxy y la configuración de resiliencia en descargas.

---

## 1. Archivos Creados y Modificados

### 1. `frontend/src/App.jsx`
- **Propósito:** Contenedor raíz de la aplicación React.
- **Qué incluye:**
  - **Barra de navegación y estado de salud (`GET /api/health`):** Sondeo cada 30 segundos mediante `useEffect` para mostrar al usuario un indicador visual en tiempo real de si el modelo y el backend están operativos (`En línea (Modelo v1.0.0)`).
  - **Sistema de Pestañas (Tabs):** Navegación fluida entre las 3 vistas principales sin recarga de página:
    - 🔍 *Análisis Individual* (`Analyze.jsx`)
    - 📁 *Lote Masivo CSV* (`Batch.jsx`)
    - 📊 *Métricas del Modelo* (`Metrics.jsx`)
  - **Pie de página accesible:** Accesos rápidos a la documentación interactiva Swagger (`/docs`) y especificaciones del proyecto.

### 2. `frontend/src/main.jsx`
- **Propósito:** Punto de entrada JavaScript oficial según React 18+.
- **Qué incluye:**
  - Montaje con la API moderna `ReactDOM.createRoot()`.
  - Envoltura con `<React.StrictMode>` para auditoría de ciclos de vida.
  - Importación global de tokens CSS (`./styles.css`).

### 3. `frontend/nginx.conf`
- **Propósito:** Servidor web ultraligero de grado de producción.
- **Responsabilidades clave:**
  - **Servidor estático de la SPA:** Maneja `try_files $uri $uri/ /index.html` para soportar enrutamiento cliente sin errores 404.
  - **Reverse Proxy transparente (`/api/`):** Redirige las peticiones que comienzan con `/api/` hacia el servicio backend `http://api:8000/api/` dentro de la red interna de Docker. Esto elimina totalmente cualquier conflicto de CORS en producción y evita exponer puertos innecesarios.
  - **Compresión Gzip:** Activa compresión para archivos `.js`, `.css` y `.json`, reduciendo los tiempos de transferencia en más del 70%.

### 4. `frontend/Dockerfile`
- **Propósito:** Construcción de imagen de producción multi-etapa (*multi-stage build*).
- **Etapas:**
  1. `build-stage` (`node:20-alpine`): Ejecuta `npm ci` y `npm run build` para compilar los activos optimizados en `frontend/dist/`.
  2. `serve-stage` (`nginx:1.27-alpine`): Copia únicamente los archivos estáticos generados y el archivo `nginx.conf`. El resultado es una imagen final diminuta (< 25 MB), sin herramientas de desarrollo ni dependencias de Node en runtime.

### 5. `Dockerfile` (Backend raíz)
- **Modificación:** Se agregaron los parámetros `--default-timeout=1000 --retries 10` en la directiva `pip install` para evitar fallos de conexión (*ReadTimeoutError*) al descargar paquetes científicos pesados de PyPI.

---

## 2. Diagrama de Arquitectura de Red en Docker

```
Navegador Web (Usuario)
       │
       ▼ Puerto 8080
┌────────────────────────────────────────────────────────┐
│  Contenedor 'frontend' (Nginx 1.27 Alpine)            │
│                                                        │
│  ├── Archivos Estáticos: / (HTML, JS, CSS)            │
│  └── Reverse Proxy:      /api/*                        │
└───────────────────────────┬────────────────────────────┘
                            │ Red Interna Docker
                            ▼ (http://api:8000/api/*)
┌────────────────────────────────────────────────────────┐
│  Contenedor 'api' (FastAPI + Uvicorn)                 │
│                                                        │
│  ├── Pipeline NLP Scikit-Learn (Memoria RAM)           │
│  └── Endpoints: /health, /predict, /predict/batch      │
└────────────────────────────────────────────────────────┘
```

---

## 3. Comprobación y Verificación

### Con Docker Desktop (Método Oficial):
```bash
docker compose up --build
```
- **Frontend accesible en:** `http://localhost:8080`
- **Documentación API (Swagger):** `http://localhost:8000/docs`
- **Salud del sistema:** `http://localhost:8000/api/health`

