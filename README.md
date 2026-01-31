# Rutopia

Proyecto full-stack con Next.js 16 + React 19 (frontend) y FastAPI con WebSockets (backend).

## Prerequisitos

- Docker y Docker Compose instalados
- Archivo `.env` con las credenciales necesarias

## Inicio Rápido

```bash
# 1. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# 2. Iniciar servicios
docker-compose up

# O en background
docker-compose up -d
```

Accede a:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/docs

## Variables de Entorno Requeridas

```bash
# Backend
ANTHROPIC_API_KEY=tu_clave_anthropic
OPENAI_API_KEY=tu_clave_openai
SUPABASE_URL=tu_url_supabase
SUPABASE_KEY=tu_clave_supabase

# Frontend
NEXT_PUBLIC_MAPBOX_TOKEN=tu_token_mapbox
```

## Comandos Útiles

```bash
# Ver logs
docker-compose logs -f

# Detener servicios
docker-compose down

# Reconstruir después de cambios en dependencias
docker-compose up --build
```
