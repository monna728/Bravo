# build_lambda_zips.ps1
# Builds correctly-structured Lambda deployment zips for each service.
# Run from the repo root: .\scripts\build_lambda_zips.ps1
#
# Zip structure rule: ALL files go into the ZIP ROOT (no subdirectory wrapper).
# shared/ is copied into each zip so Lambda (/var/task/) can find it directly.
# Third-party packages (requests, etc.) are pip-installed into each zip so
# Lambda doesn't need a separate layer.

$ErrorActionPreference = "Stop"
$ROOT   = Split-Path $PSScriptRoot -Parent
$DIST   = "$ROOT\dist"
$SHARED = "$ROOT\services\shared"

if (-not (Test-Path $DIST)) { New-Item -ItemType Directory -Path $DIST | Out-Null }

function Build-Zip {
    param(
        [string]$ZipName,
        [string[]]$ServiceFiles,     # absolute paths to individual .py files
        [string[]]$PipPackages = @() # third-party packages to bundle
    )

    $tmp = "$env:TEMP\lambda_build_$ZipName"
    if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
    New-Item -ItemType Directory -Path $tmp | Out-Null

    # pip-install third-party dependencies directly into zip root
    if ($PipPackages.Count -gt 0) {
        Write-Host "    Installing: $($PipPackages -join ', ')"
        pip install --quiet --target $tmp $PipPackages 2>&1 | Out-Null
    }

    # Copy service-specific files to zip root
    foreach ($f in $ServiceFiles) {
        Copy-Item $f "$tmp" -Force
    }

    # Copy shared/ into zip root so `from shared.xxx import yyy` resolves
    Copy-Item $SHARED "$tmp\shared" -Recurse -Force

    $out = "$DIST\$ZipName.zip"
    if (Test-Path $out) { Remove-Item $out -Force }
    Compress-Archive -Path "$tmp\*" -DestinationPath $out
    Remove-Item $tmp -Recurse -Force

    $size = [math]::Round((Get-Item $out).Length / 1KB, 1)
    Write-Host "  Built $out  ($size KB)"
}

Write-Host "`n=== Building Lambda zips into $DIST ===`n"

# 1. bravo-data-collection  (handler = handler.lambda_handler)
#    Needs: requests (Open-Meteo, TLC, Ticketmaster HTTP calls)
Write-Host "[1/4] bravo-data-collection"
Build-Zip "bravo-data-collection" `
    -ServiceFiles @(
        "$ROOT\services\data-collection\handler.py",
        "$ROOT\services\data-collection\collectWeather.py",
        "$ROOT\services\data-collection\collectNYCTaxi.py",
        "$ROOT\services\data-collection\collectTicketmaster.py",
        "$ROOT\services\data-collection\taxiZone_lookup.py"
    ) `
    -PipPackages @("requests")

# 2. data-retrieval  (handler = handler.lambda_handler)
#    boto3 is pre-installed on Lambda; no extra pip packages needed
Write-Host "[2/4] data-retrieval"
Build-Zip "data-retrieval" `
    -ServiceFiles @(
        "$ROOT\services\data-retrieval\handler.py",
        "$ROOT\services\data-retrieval\s3_reader.py"
    )

# 3. data-preprocessing  (handler = handler.lambda_handler)
Write-Host "[3/4] data-preprocessing"
Build-Zip "data-preprocessing" `
    -ServiceFiles @(
        "$ROOT\services\data-preprocessing\handler.py",
        "$ROOT\services\data-preprocessing\normaliser.py",
        "$ROOT\services\data-preprocessing\merger.py"
    )

# 4. analytical-model  (handler = handler.lambda_handler)
#    prophet/numpy are too large for a zip — use a Lambda Layer for those.
#    This zip only contains the handler code; attach the layer separately.
Write-Host "[4/4] analytical-model"
Build-Zip "analytical-model" `
    -ServiceFiles @(
        "$ROOT\services\analytical-model\handler.py",
        "$ROOT\services\analytical-model\prophet_model.py"
    )

Write-Host "`n=== All zips built successfully ===`n"
Write-Host "Upload each zip to its Lambda function (Code tab -> Upload from -> .zip file)."
Write-Host "Handler for all functions: handler.lambda_handler"
Write-Host ""
Write-Host "bravo-data-collection test events:"
Write-Host '  Sydney weather: { "source": "weather", "lat": -33.8688, "lng": 151.2093, "use_forecast_only": true, "return_raw": true }'
Write-Host '  TLC:            { "source": "tlc" }'
Write-Host '  Ticketmaster:   { "source": "ticketmaster" }'
