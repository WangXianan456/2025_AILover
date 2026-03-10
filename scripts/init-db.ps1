Set-Location $PSScriptRoot\..
$env:DATABASE_URL = "sqlite:///./ailover.db"
Set-Location backend
python -c "from app.models.base import init_db; init_db(); print('OK')"
