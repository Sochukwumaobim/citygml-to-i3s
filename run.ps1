# CityGML to I3S Workflow Runner for Windows
Write-Host "==========================================" -ForegroundColor Green
Write-Host "CityGML to I3S Complete Workflow Runner" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

# Configuration
$POSTGRES_HOST = "host.docker.internal"
$POSTGRES_PORT = "5432"
$POSTGRES_DB = "3d-DB-tum"
$POSTGRES_USER = "postgres"
$POSTGRES_PASSWORD = "c1h1u1k1s1"
$POSTGRES_SCHEMA = "citydb"
$OUTPUT_NAME = "tum_campus"
$MAX_DEPTH = "6"
$LOD_FILTER = "2"

# Clean output directories
Write-Host "🧹 Cleaning output directories..." -ForegroundColor Yellow
Remove-Item -Recurse -Force output\*, logs\* -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path output, logs, data | Out-Null

# Build Docker image
Write-Host "🔨 Building Docker image..." -ForegroundColor Yellow
docker build -t citygml-i3s-converter .

Write-Host "🚀 Starting conversion workflow..." -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

# Run the container
docker run --rm --user root `
  --add-host=host.docker.internal:host-gateway `
  -e POSTGRES_HOST=$POSTGRES_HOST `
  -e POSTGRES_PORT=$POSTGRES_PORT `
  -e POSTGRES_DB=$POSTGRES_DB `
  -e POSTGRES_USER=$POSTGRES_USER `
  -e POSTGRES_PASSWORD=$POSTGRES_PASSWORD `
  -e POSTGRES_SCHEMA=$POSTGRES_SCHEMA `
  -e OUTPUT_NAME=$OUTPUT_NAME `
  -e MAX_DEPTH=$MAX_DEPTH `
  -e LOD_FILTER=$LOD_FILTER `
  -e WAIT_FOR_DB=true `
  -v "${PWD}\output:/app/output" `
  -v "${PWD}\logs:/app/logs" `
  citygml-i3s-converter

# Check results
Write-Host "==========================================" -ForegroundColor Green
Write-Host "📊 Checking results..." -ForegroundColor Cyan

$slpkFiles = Get-ChildItem "output\*.slpk" -ErrorAction SilentlyContinue
if ($slpkFiles) {
    Write-Host "✅ SUCCESS! SLPK files created:" -ForegroundColor Green
    foreach ($file in $slpkFiles) {
        $size = "{0:N2}" -f ($file.Length / 1KB)
        Write-Host "   - $($file.Name) ($size KB)" -ForegroundColor Green
    }
} else {
    Write-Host "❌ No SLPK files found in output directory" -ForegroundColor Red
    Write-Host "📁 Checking what was created..." -ForegroundColor Yellow
    Get-ChildItem "output\*" -Recurse -ErrorAction SilentlyContinue | Select-Object Name, Length, LastWriteTime | Format-Table
}

Write-Host "==========================================" -ForegroundColor Green
Write-Host "🎉 Workflow completed!" -ForegroundColor Green
Write-Host "📁 Output: ${PWD}\output" -ForegroundColor Cyan
Write-Host "📄 Logs: ${PWD}\logs" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Green