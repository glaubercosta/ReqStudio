# setup-frontend.ps1 — Setup completo do reqstudio-ui em uma execução
# Usage: .\scripts\setup-frontend.ps1
# Rode este script UMA VEZ antes de usar docker compose.

$ErrorActionPreference = "Stop"
$uiDir = Join-Path $PSScriptRoot "..\reqstudio-ui"

Write-Host "`n📦 ReqStudio UI — Setup Completo`n" -ForegroundColor Cyan

# 1. Verificar se o diretório já existe
if (-Not (Test-Path $uiDir)) {
    Write-Host "🚀 Criando projeto Vite (react-ts)..." -ForegroundColor Yellow
    Set-Location (Join-Path $PSScriptRoot "..")
    npm create vite@latest reqstudio-ui -- --template react-ts
} else {
    Write-Host "✅ Diretório reqstudio-ui já existe. Pulando criação do projeto." -ForegroundColor Green
}

Set-Location $uiDir

# 2. Instalar TODAS as dependências de uma vez
Write-Host "`n📥 Instalando dependências..." -ForegroundColor Yellow
npm install

Write-Host "`n📥 Instalando dependências de desenvolvimento e runtime adicionais..." -ForegroundColor Yellow
npm install `
    react-router-dom

npm install -D `
    tailwindcss `
    @tailwindcss/vite `
    @types/node `
    vitest `
    @testing-library/react `
    "@testing-library/jest-dom" `
    jsdom

Write-Host "`n✅ Dependências instaladas com sucesso!" -ForegroundColor Green

# 3. Lembrar sobre configuração Vite + tsconfig
Write-Host "`n📝 IMPORTANTE: As configurações vite.config.ts e tsconfig já foram aplicadas pela equipe." -ForegroundColor Cyan
Write-Host "   Se for uma instalação limpa, certifique-se que esses arquivos estão corretos." -ForegroundColor Gray

# 4. Inicializar shadcn/ui
Write-Host "`n🎨 Inicializando shadcn/ui..." -ForegroundColor Yellow
Write-Host "   Quando solicitado, escolha:" -ForegroundColor Gray
Write-Host "   - Component library: Radix" -ForegroundColor Gray
Write-Host "   - Preset: New York" -ForegroundColor Gray
Write-Host "   - Base color: Zinc ou Neutral" -ForegroundColor Gray
Write-Host "   - CSS variables: Yes`n" -ForegroundColor Gray
npx shadcn@latest init

Write-Host "`n✅ Setup do frontend concluído!" -ForegroundColor Green
Write-Host "`nPróximo passo: rode 'docker compose up --build' na pasta reqstudio/" -ForegroundColor Cyan
