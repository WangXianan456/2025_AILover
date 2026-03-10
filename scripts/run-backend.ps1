# PowerShell 启动后端（避免 && 语法错误）
# 若报错 WinError 10013，说明 8000 端口被占用，可改为 --port 8001 或先执行：Get-NetTCPConnection -LocalPort 8000 | Select OwningProcess
Set-Location $PSScriptRoot\..
Set-Location backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
# 若还没有 data/characters.jsonpip install httpx