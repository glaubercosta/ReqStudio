# Story 1.5: CI/CD Pipeline — Versionamento e Entrega Contínua

Status: in-progress

## Story

As a desenvolvedor do ReqStudio,
I want que todo Pull Request execute os testes automaticamente e que merges na main construam as imagens Docker,
So that nenhum código com falha chegue à branch principal e o processo de entrega seja automatizado.

## Acceptance Criteria

1. `ci.yml`: executa `pytest tests/ -v` no container a cada PR ou push para `main`
2. `ci.yml`: executa lint (`ruff check`) no backend
3. `ci.yml`: valida que o build do frontend (`npm run build`) não falha
4. `cd.yml`: build das imagens Docker `reqstudio-api` e `reqstudio-frontend` ao mergear em `main`
5. Branch `main` protegida: merge só permitido se CI verde (configuração manual no GitHub)
6. Falhas de CI são claramente reportadas no PR com mensagem de erro

## Tasks

- [x] Task 1: CI Pipeline (AC: #1, #2, #3)
  - [x] 1.1 `.github/workflows/ci.yml` — testes backend, lint e build frontend

- [x] Task 2: CD Pipeline (AC: #4)
  - [x] 2.1 `.github/workflows/cd.yml` — build Docker images on main

- [x] Task 3: Documentação (AC: #5)
  - [x] 3.1 README atualizado com badge de CI

## Dev Notes

- Testes rodam em container Docker para garantir paridade com produção
- CD não faz push para registry ainda (sem credenciais configuradas) — apenas valida o build
- Secrets necessários para push: `DOCKER_USERNAME`, `DOCKER_PASSWORD` (configurar no GitHub)
- Branch protection rule deve ser configurada manualmente em Settings > Branches

## Dev Agent Record

### Agent Model Used
Antigravity (Google Deepmind)

### File List
- `.github/workflows/ci.yml`
- `.github/workflows/cd.yml`
