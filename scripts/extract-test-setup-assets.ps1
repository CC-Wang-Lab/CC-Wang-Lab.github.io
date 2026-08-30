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
        [string]$RelativePath,
        [string]$Erase = ''
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
    if ($Erase) {
        & magick $target -fill white -draw $Erase -strip $target
        if ($LASTEXITCODE -ne 0) { throw "ImageMagick cleanup failed for Slide $Slide" }
    }
}

Export-Crop -Slide 3 -Geometry '370x324+106+70' -RelativePath 'gaming-laptop-hybrid-vapor-chamber\upper-experimental-system.jpg'
Export-Crop -Slide 3 -Geometry '370x278+106+414' -RelativePath 'gaming-laptop-hybrid-vapor-chamber\lower-experimental-system.jpg'

Export-Crop -Slide 4 -Geometry '357x522+96+108' -RelativePath 'two-phase-closed-loop-thermosyphon\system-apparatus.jpg'
Export-Crop -Slide 4 -Geometry '264x266+547+448' -RelativePath 'two-phase-closed-loop-thermosyphon\glass-visualization-chamber.jpg'
Export-Crop -Slide 4 -Geometry '362x264+859+448' -RelativePath 'two-phase-closed-loop-thermosyphon\filling-ratio-levels.png'

Export-Crop -Slide 5 -Geometry '368x311+57+144' -RelativePath 'chip-package-lid-thermal-spreading\vapor-chamber-schematic.png'
Export-Crop -Slide 5 -Geometry '147x308+427+145' -RelativePath 'chip-package-lid-thermal-spreading\vapor-chamber-sample.jpg'
Export-Crop -Slide 5 -Geometry '279x195+101+460' -RelativePath 'chip-package-lid-thermal-spreading\diamond-copper-composite.jpg'
Export-Crop -Slide 5 -Geometry '194x195+379+460' -RelativePath 'chip-package-lid-thermal-spreading\pure-copper-plate.jpg'
Export-Crop -Slide 6 -Geometry '510x364+66+276' -RelativePath 'chip-package-lid-thermal-spreading\experimental-setup.jpg'
Export-Crop -Slide 6 -Geometry '293x271+618+363' -RelativePath 'chip-package-lid-thermal-spreading\thermal-map-tmax-60c.png'
Export-Crop -Slide 6 -Geometry '305x272+911+362' -RelativePath 'chip-package-lid-thermal-spreading\thermal-map-tmax-55-4c.png'

Export-Crop -Slide 7 -Geometry '419x559+89+101' -RelativePath 'thermal-fin-natural-convection-chamber\chamber.jpg'
Export-Crop -Slide 8 -Geometry '960x333+160+91' -RelativePath 'air-cooler-wind-tunnel\wind-tunnel.jpg'

Export-Crop -Slide 9 -Geometry '515x320+152+235' -RelativePath 'data-center-air-cooling-facility\facility-airflow-diagram.png'
Export-Crop -Slide 10 -Geometry '168x541+46+106' -RelativePath 'data-center-air-cooling-facility\tc-measurements-mesh.png'
Export-Crop -Slide 10 -Geometry '250x412+239+205' -RelativePath 'data-center-air-cooling-facility\tc-measurements-rack.jpg'
Export-Crop -Slide 10 -Geometry '289x258+549+67' -RelativePath 'data-center-air-cooling-facility\hot-wire-mesh-front.jpg'
Export-Crop -Slide 10 -Geometry '331x207+528+356' -RelativePath 'data-center-air-cooling-facility\hot-wire-mesh-overhead.jpg'
Export-Crop -Slide 10 -Geometry '129x437+904+139' -RelativePath 'data-center-air-cooling-facility\simulated-rack.jpg'
Export-Crop -Slide 10 -Geometry '154x405+1103+169' -RelativePath 'data-center-air-cooling-facility\simulated-rack-rendering.png'

Export-Crop -Slide 11 -Geometry '734x525+55+76' -RelativePath 'two-phase-cold-plate-test-platform\annotated-platform.jpg'

Export-Crop -Slide 12 -Geometry '402x392+382+119' -RelativePath 'flooded-evaporator-test-rig\system.jpg'
Export-Crop -Slide 12 -Geometry '348x339+18+342' -RelativePath 'flooded-evaporator-test-rig\evaporator-close-up.jpg'

Export-Crop -Slide 13 -Geometry '272x117+185+234' -RelativePath 'boiler-surface-test-rig\sintered.jpg'
Export-Crop -Slide 13 -Geometry '272x117+185+356' -RelativePath 'boiler-surface-test-rig\additively-manufactured.jpg'
Export-Crop -Slide 13 -Geometry '272x117+185+476' -RelativePath 'boiler-surface-test-rig\diamond.jpg'
Export-Crop -Slide 13 -Geometry '272x117+185+595' -RelativePath 'boiler-surface-test-rig\acid-etched.jpg'
Export-Crop -Slide 13 -Geometry '692x417+578+70' -RelativePath 'boiler-surface-test-rig\test-schematic.png'
Export-Crop -Slide 13 -Geometry '267x184+844+528' -RelativePath 'boiler-surface-test-rig\test-rig.jpg'

Export-Crop -Slide 14 -Geometry '505x378+22+260' -RelativePath 'heat-pipes-freezing-conditions\freezing-chamber.jpg'
Export-Crop -Slide 14 -Geometry '611x281+552+158' -RelativePath 'heat-pipes-freezing-conditions\heat-pipe-apparatus.jpg'

Export-Crop -Slide 15 -Geometry '604x452+8+168' -RelativePath 'three-kilowatt-cold-plate-test-facility\rig.jpg'
Export-Crop -Slide 15 -Geometry '651x368+629+204' -RelativePath 'three-kilowatt-cold-plate-test-facility\flow-diagram.png'

Export-Crop -Slide 16 -Geometry '470x352+104+148' -RelativePath 'vapor-compression-cooling-system\system-overview.jpg'
Export-Crop -Slide 16 -Geometry '515x387+650+130' -RelativePath 'vapor-compression-cooling-system\cold-plate-loop.jpg'

Export-Crop -Slide 17 -Geometry '395x343+157+79' -RelativePath 'refrigerant-lubricant-boiling-system\apparatus.jpg'
Export-Crop -Slide 17 -Geometry '478x397+721+62' -RelativePath 'refrigerant-lubricant-boiling-system\system-diagram.png'
Export-Crop -Slide 17 -Geometry '540x166+720+518' -RelativePath 'refrigerant-lubricant-boiling-system\heater-diagram.png'

Export-Crop -Slide 18 -Geometry '270x408+54+125' -RelativePath 'liquid-desiccant-air-conditioning-system\rig-front-view.jpg'
Export-Crop -Slide 18 -Geometry '811x426+469+64' -RelativePath 'liquid-desiccant-air-conditioning-system\perspective-system-diagram.png' -Erase 'rectangle 0,0 22,28'
Export-Crop -Slide 18 -Geometry '258x169+60+360' -RelativePath 'liquid-desiccant-air-conditioning-system\process-flow-diagram.png'

Export-Crop -Slide 28 -Geometry '562x398+79+167' -RelativePath 'carvera-desktop-cnc\cnc-machine.jpg'

Export-Crop -Slide 29 -Geometry '378x402+57+184' -RelativePath 'fabrication-and-microscopy-equipment\3d-printer.jpg'
Export-Crop -Slide 29 -Geometry '316x402+490+184' -RelativePath 'fabrication-and-microscopy-equipment\microscope-1.jpg'
Export-Crop -Slide 29 -Geometry '331x402+860+184' -RelativePath 'fabrication-and-microscopy-equipment\microscope-2.jpg'

Export-Crop -Slide 30 -Geometry '548x411+45+170' -RelativePath 'amca-wind-tunnel\wind-tunnel-environmental-room.jpg'
