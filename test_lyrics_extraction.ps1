# Test Lyrics Extraction Service
$audioFile = "E:\Developer\lyric_cover_staging\app\static\uploads\test.mp3"

Write-Host "Testing Lyrics Extraction" -ForegroundColor Cyan
Write-Host "Audio file: $audioFile" -ForegroundColor Gray
Write-Host ""

# Create multipart form data
$fileBin = [System.IO.File]::ReadAllBytes($audioFile)
$fileName = [System.IO.Path]::GetFileName($audioFile)
$boundary = [System.Guid]::NewGuid().ToString()
$LF = "`r`n"

$bodyLines = (
    "--$boundary",
    "Content-Disposition: form-data; name=`"file`"; filename=`"$fileName`"",
    "Content-Type: audio/mpeg$LF",
    [System.Text.Encoding]::GetEncoding("iso-8859-1").GetString($fileBin),
    "--$boundary",
    "Content-Disposition: form-data; name=`"language_hint`"$LF",
    "auto",
    "--$boundary",
    "Content-Disposition: form-data; name=`"timestamps`"$LF",
    "word",
    "--$boundary--$LF"
) -join $LF

# Submit job
Write-Host "Submitting job..." -ForegroundColor Yellow

$response = Invoke-RestMethod -Uri "http://localhost:8000/v1/lyrics" `
    -Method Post `
    -ContentType "multipart/form-data; boundary=$boundary" `
    -Body $bodyLines

$jobId = $response.job_id
Write-Host "Job Created: $jobId" -ForegroundColor Green
Write-Host "Status: $($response.status)" -ForegroundColor White
Write-Host ""

# Check status
Write-Host "Checking job status..." -ForegroundColor Yellow
$maxAttempts = 30
$attempt = 0

while ($attempt -lt $maxAttempts) {
    Start-Sleep -Seconds 2
    $attempt++
    
    $status = Invoke-RestMethod -Uri "http://localhost:8000/v1/lyrics/$jobId"
    
    Write-Host "  [$attempt/$maxAttempts] Status: $($status.status)" -ForegroundColor Gray
    
    if ($status.status -eq "done") {
        Write-Host ""
        Write-Host "=== EXTRACTION COMPLETE ===" -ForegroundColor Green
        Write-Host ""
        Write-Host "LYRICS:" -ForegroundColor Cyan
        Write-Host $status.result.lyrics
        Write-Host ""
        Write-Host "METADATA:" -ForegroundColor Cyan
        Write-Host "Language: $($status.meta.language_detected)"
        Write-Host "Duration: $($status.meta.duration_sec)s"
        if ($status.result.words) {
            Write-Host "Word timestamps: $($status.result.words.Count) words"
        }
        break
    }
    
    if ($status.status -eq "error") {
        Write-Host ""
        Write-Host "ERROR:" -ForegroundColor Red
        Write-Host ($status.error | ConvertTo-Json)
        break
    }
}

if ($attempt -eq $maxAttempts) {
    Write-Host ""
    Write-Host "Timeout - Job ID: $jobId (still processing)" -ForegroundColor Yellow
}
