# ==============================================================================
# Etapa 1: Compilación de la aplicación React con Vite
# ==============================================================================
FROM node:20-alpine AS builder

WORKDIR /app

# Copiar archivos de dependencias
COPY package*.json ./
RUN npm install

# Copiar código fuente y compilar estáticos
COPY . .
RUN npm run build

# ==============================================================================
# Etapa 2: Servidor web de producción Nginx (ultraligero ~25 MB)
# ==============================================================================
FROM nginx:1.27-alpine AS runtime

# Configuración personalizada con Reverse Proxy hacia la API
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar artefactos compilados desde la etapa builder
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

