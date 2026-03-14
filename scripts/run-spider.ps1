# 启动 Genshin Spider 爬行角色数据
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location "$ProjectRoot\genshin_spider"

Write-Host "正在启动 Scrapy 爬虫抓取数据..." -ForegroundColor Green
scrapy crawl genshin
