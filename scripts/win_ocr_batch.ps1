param(
    [Parameter(Mandatory=$true)][string]$ImageDir,
    [Parameter(Mandatory=$true)][string]$OutJson
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime

$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
})[0]

function Await($WinRtTask, $ResultType) {
    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRtTask))
    $netTask.Wait(-1) | Out-Null
    return $netTask.Result
}

[Windows.Graphics.Imaging.BitmapDecoder,Windows.Graphics.Imaging,ContentType=WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.SoftwareBitmap,Windows.Graphics.Imaging,ContentType=WindowsRuntime] | Out-Null
[Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime] | Out-Null

$ocrEngine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
if ($null -eq $ocrEngine) {
    throw "Failed to initialize Windows.Media.Ocr.OcrEngine"
}

$files = Get-ChildItem -Path $ImageDir -File | Sort-Object Name
$total = $files.Count
$results = [System.Collections.Generic.List[object]]::new($total)
$idx = 0

foreach ($f in $files) {
    $idx++
    $fs = $null
    $stream = $null
    $bitmap = $null
    try {
        $fs = [System.IO.File]::OpenRead($f.FullName)
        $stream = [System.IO.WindowsRuntimeStreamExtensions]::AsRandomAccessStream($fs)
        $decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
        $bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
        $ocrResult = Await ($ocrEngine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])

        $linesOut = [System.Collections.Generic.List[object]]::new()
        foreach ($line in $ocrResult.Lines) {
            $words = $line.Words
            if ($words.Count -gt 0) {
                $minX = [double]::MaxValue
                $minY = [double]::MaxValue
                $maxX = 0.0
                $maxY = 0.0
                foreach ($w in $words) {
                    $r = $w.BoundingRect
                    if ($r.X -lt $minX) { $minX = $r.X }
                    if ($r.Y -lt $minY) { $minY = $r.Y }
                    $rx = $r.X + $r.Width
                    $ry = $r.Y + $r.Height
                    if ($rx -gt $maxX) { $maxX = $rx }
                    if ($ry -gt $maxY) { $maxY = $ry }
                }
                $linesOut.Add([PSCustomObject]@{
                    text = $line.Text
                    x    = [Math]::Round($minX, 1)
                    y    = [Math]::Round($minY, 1)
                    w    = [Math]::Round($maxX - $minX, 1)
                    h    = [Math]::Round($maxY - $minY, 1)
                })
            }
        }

        $results.Add([PSCustomObject]@{
            file  = $f.Name
            img_w = [int]$bitmap.PixelWidth
            img_h = [int]$bitmap.PixelHeight
            lines = $linesOut
        })
    }
    finally {
        if ($null -ne $bitmap) { $bitmap.Dispose() }
        if ($null -ne $stream) { $stream.Dispose() }
        if ($null -ne $fs) { $fs.Dispose() }
    }

    if ($idx % 50 -eq 0 -or $idx -eq $total) {
        Write-Host "OCR progress: $idx / $total"
    }
}

$outDir = Split-Path -Parent $OutJson
if ($outDir -and -not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Force -Path $outDir | Out-Null
}

$json = $results | ConvertTo-Json -Depth 6
[System.IO.File]::WriteAllText($OutJson, $json, [System.Text.UTF8Encoding]::new($false))
Write-Host "Saved $total OCR pages to $OutJson"
