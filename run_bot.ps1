$env:PYTHONPATH = "g:\RAGbot\RAG-discord-bot"
$PYTHON = "C:\Users\45082\miniconda3\python.exe"

Write-Host "Running Healthcheck..." -ForegroundColor Cyan
& $PYTHON healthcheck.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "Healthcheck Passed." -ForegroundColor Green
    
    # Start Monitor Server in a new window
    Write-Host "Starting Dashboard Server..." -ForegroundColor Cyan
    $monitorProcess = Start-Process -FilePath $PYTHON -ArgumentList "backend/monitor_server.py" -WindowStyle Minimized -PassThru
    
    # Give it a moment to spin up
    Start-Sleep -Seconds 3

    # Open Browser
    Write-Host "Opening Dashboard UI..." -ForegroundColor Cyan
    Start-Process "http://localhost:5000"

    Write-Host "Starting Discord Bot..." -ForegroundColor Green
    try {
        & $PYTHON main_bot.py
    }
    finally {
        # Optional: Ask user if they want to kill the monitor
        Write-Host "Bot Stopped." -ForegroundColor Yellow
        Write-Host "Monitor Server (PID: $($monitorProcess.Id)) is still running in background." -ForegroundColor Gray
        Write-Host "To stop it, close the minimized console window." -ForegroundColor Gray
        
        # Uncomment to auto-kill:
        # Stop-Process -Id $monitorProcess.Id -Force -ErrorAction SilentlyContinue
    }
}
else {
    Write-Host "Healthcheck Failed. Please fix errors above." -ForegroundColor Red
}
