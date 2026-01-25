$env:PYTHONPATH = "g:\RAGbot\RAG-discord-bot"
$PYTHON = "C:\Users\45082\miniconda3\python.exe"

Write-Host "Running Healthcheck..." -ForegroundColor Cyan
& $PYTHON healthcheck.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "Healthcheck Passed. Starting Bot..." -ForegroundColor Green
    & $PYTHON main_bot.py
}
else {
    Write-Host "Healthcheck Failed. Please fix errors above." -ForegroundColor Red
}
