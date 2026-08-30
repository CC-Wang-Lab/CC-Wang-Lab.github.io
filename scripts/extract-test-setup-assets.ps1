param(
    [Parameter(Mandatory = $true)]
    [string]$SourceDir
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$outputRoot = Join-Path $repoRoot '_assets\img\test-setups'

function Export-Crop {
    param(
        [int]$Slide,
        [string]$Geometry,
        [string]$RelativePath
    )

    $source = Join-Path $SourceDir ("Slide{0}.jpg" -f $Slide)
    $target = Join-Path $outputRoot $RelativePath
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
        throw "Missing source slide: $source"
    }
    New-Item -ItemType Directory -Force (Split-Path -Parent $target) | Out-Null

    if ([IO.Path]::GetExtension($target).Equals('.jpg', [StringComparison]::OrdinalIgnoreCase)) {
        & magick $source -crop $Geometry +repage -strip -quality 95 $target
    }
    else {
        & magick $source -crop $Geometry +repage -strip $target
    }
    if ($LASTEXITCODE -ne 0) { throw "ImageMagick failed for Slide $Slide" }
}

Export-Crop -Slide 7 -Geometry '419x559+89+101' -RelativePath 'thermal-fin-natural-convection-chamber\chamber.jpg'
Export-Crop -Slide 8 -Geometry '960x333+160+91' -RelativePath 'air-cooler-wind-tunnel\wind-tunnel.jpg'

Export-Crop -Slide 9 -Geometry '515x320+152+235' -RelativePath 'data-center-air-cooling-facility\facility-airflow-diagram.png'
Export-Crop -Slide 10 -Geometry '168x541+46+106' -RelativePath 'data-center-air-cooling-facility\tc-measurements-mesh.png'
Export-Crop -Slide 10 -Geometry '250x412+239+205' -RelativePath 'data-center-air-cooling-facility\tc-measurements-rack.jpg'
Export-Crop -Slide 10 -Geometry '289x258+549+67' -RelativePath 'data-center-air-cooling-facility\hot-wire-mesh-front.jpg'
Export-Crop -Slide 10 -Geometry '331x207+528+356' -RelativePath 'data-center-air-cooling-facility\hot-wire-mesh-overhead.jpg'
Export-Crop -Slide 10 -Geometry '129x437+904+139' -RelativePath 'data-center-air-cooling-facility\simulated-rack.jpg'
Export-Crop -Slide 10 -Geometry '154x405+1103+169' -RelativePath 'data-center-air-cooling-facility\simulated-rack-rendering.png'
