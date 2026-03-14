# 启动前端页面交互服务
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location "$ProjectRoot\frontend"

Write-Host "正在启动前端服务 (Vite)..." -ForegroundColor Green
npm install
npm run dev
