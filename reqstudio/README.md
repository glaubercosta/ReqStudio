# ReqStudio

Plataforma de elicitação de requisitos assistida por IA que traduz conhecimento de domínio em artefatos estruturados.

## ⚠️ Pré-requisitos

- **Docker Desktop** rodando (verifique o ícone na bandeja do sistema)
- **Node.js 20+** instalado
- **PowerShell** (Windows) ou Bash (Linux/Mac)

---

## 🚀 Quick Start

### 1. Detectar portas disponíveis

> Execute **antes** de configurar o `.env` para evitar conflitos com outros projetos rodando na máquina.

```powershell
# Windows
.\scripts\find-ports.ps1
```

```bash
# Linux/Mac
bash ./scripts/find-ports.sh
```

O script exibe as portas livres. Use os valores sugeridos no próximo passo.

### 2. Configurar ambiente

```powershell
Copy-Item .env.example .env
```

Abra o `.env` e ajuste as portas se `find-ports` indicou conflitos:

```env
API_PORT=8000        # altere se ocupada (ex: 8001)
DB_PORT=5432         # altere se ocupada (ex: 5433)
FRONTEND_PORT=5173   # altere se ocupada (ex: 5174)
# Mantenha ALLOWED_ORIGINS alinhado com FRONTEND_PORT
ALLOWED_ORIGINS=http://localhost:5173
```

### 3. Setup do Frontend (primeira vez)

```powershell
.\scripts\setup-frontend.ps1
```

> Este script instala todas as dependências na ordem correta (Vite → deps → shadcn/ui).
> Só é necessário na primeira vez ou após limpar `node_modules`.

### 4. Subir os serviços

```powershell
docker compose up --build
```

### 5. Verificar

| Serviço | URL |
|---------|-----|
| Backend API | `http://localhost:{API_PORT}/health` |
| API Docs | `http://localhost:{API_PORT}/docs` (apenas em DEBUG=true) |
| Frontend | `http://localhost:{FRONTEND_PORT}` |

---

## 🏗 Arquitetura

- **Backend:** FastAPI + SQLAlchemy 2.0 + PostgreSQL 16
- **Frontend:** React 19 + Vite + TypeScript + shadcn/ui + Tailwind CSS v4
- **AI Engine:** LiteLLM *(Epic 5)*

## 📁 Estrutura do Projeto

```
reqstudio/
├── docker-compose.yml
├── .env.example
├── scripts/
│   ├── find-ports.ps1      # Detecta portas livres (Windows)
│   ├── find-ports.sh       # Detecta portas livres (Linux/Mac)
│   └── setup-frontend.ps1  # Setup completo do frontend (primeira vez)
├── reqstudio-api/          # Backend (Python/FastAPI)
│   ├── app/
│   │   ├── core/           # Config, security, middleware
│   │   ├── db/             # Database base, session
│   │   ├── modules/        # Domain modules (por feature)
│   │   └── integrations/   # LiteLLM e provedores externos
│   ├── alembic/            # Migrações de banco de dados
│   └── tests/
└── reqstudio-ui/           # Frontend (React/Vite)
    ├── src/
    │   ├── components/ui/  # shadcn/ui components
    │   ├── pages/          # Páginas (lazy loaded)
    │   ├── hooks/          # Custom hooks
    │   ├── services/       # Chamadas de API
    │   ├── contexts/       # React contexts
    │   ├── types/          # TypeScript types
    │   └── lib/            # Utilitários (cn, etc)
    └── src/tests/          # Testes Vitest
```

---

## 🛠 Development

```bash
# Backend: Rodar testes
docker compose exec api pytest

# Backend: Linter
docker compose exec api ruff check app/

# Backend: Migrações
docker compose exec api alembic upgrade head

# Frontend: Testes
cd reqstudio-ui && npm test

# Frontend: Dev server local (sem Docker)
cd reqstudio-ui && npm run dev
```
