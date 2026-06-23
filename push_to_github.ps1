# ============================================================
#  Commit + push do BI_Notify para github.com/Mastertigi/BI_Sender
#  Execute na pasta do projeto:  C:\Users\Adm\Downloads\BI_Notify
#  Pré-requisito: git instalado e autenticado (Git Credential Manager
#  ou um Personal Access Token quando o push pedir senha).
# ============================================================

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

# 1) Inicializa o repositório (idempotente)
if (-not (Test-Path ".git")) {
    git init
    git branch -M main
}

# 2) Garante identidade (ajuste se quiser)
if (-not (git config user.email)) {
    git config user.email "thiago.nascimento@pentare.com.br"
    git config user.name  "Thiago Nascimento"
}

# 3) Stage + commit
git add .
git commit -m "feat: motor de orquestracao e entrega de relatorios Power BI (FastAPI/Celery + React)"

# 4) Remote
if (-not (git remote | Select-String -Quiet "origin")) {
    git remote add origin https://github.com/Mastertigi/BI_Sender.git
} else {
    git remote set-url origin https://github.com/Mastertigi/BI_Sender.git
}

# 5) Push
#    O repo remoto tem apenas um README placeholder. O --force substitui
#    esse commit inicial pelo projeto. Se quiser PRESERVAR o histórico
#    remoto, comente a linha abaixo e use o bloco alternativo no final.
git push -u origin main --force

Write-Host "`nConcluido. Veja: https://github.com/Mastertigi/BI_Sender" -ForegroundColor Green

# ------------------------------------------------------------
# ALTERNATIVA (preservar o README remoto em vez de sobrescrever):
#   git pull origin main --allow-unrelated-histories --no-rebase
#   # resolva eventual conflito no README.md
#   git push -u origin main
# ------------------------------------------------------------
