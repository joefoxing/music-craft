#!/usr/bin/env pwsh
# Test if backend returns newlines in lyrics

$audioFile = "E:\Developer\lyric_cover_staging\app\static\uploads\00daf4d19d2c4eb790e2244e67d1c954.mp3"

Write-Host "`n=== Testing Lyrics Extraction Backend ===" -ForegroundColor Cyan
Write-Host "Audio file: $audioFile" -ForegroundColor Yellow

# Submit extraction job
Write-Host "`n1. Submitting extraction job..." -ForegroundColor Green
$response = Invoke-RestMethod -Uri "http://localhost:8000/v1/lyrics" -Method Post -Form @{
    file = Get-Item $audioFile
    language_hint = "auto"
    timestamps = "word"
}

$jobId = $response.job_id
Write-Host "   Job ID: $jobId" -ForegroundColor Yellow

# Wait and check status
Write-Host "`n2. Checking job status..." -ForegroundColor Green
$maxAttempts = 30
$attempt = 0

while ($attempt -lt $maxAttempts) {
    Start-Sleep -Seconds 2
    $attempt++
    
    $statusResponse = Invoke-RestMethod -Uri "http://localhost:8000/v1/lyrics/$jobId"
    $status = $statusResponse.status
    
    Write-Host "   Attempt $attempt : Status = $status" -ForegroundColor Yellow
    
    if ($status -eq "completed" -or $status -eq "failed") {
        break
    }
}

# Get final result
Write-Host "`n3. Final Result:" -ForegroundColor Green
$finalResponse = Invoke-RestMethod -Uri "http://localhost:8000/v1/lyrics/$jobId"

$lyrics = $finalResponse.lyrics
$language = $finalResponse.language

Write-Host "   Status: $($finalResponse.status)" -ForegroundColor Yellow
Write-Host "   Language: $language" -ForegroundColor Yellow
Write-Host "   Lyrics length: $($lyrics.Length) characters" -ForegroundColor Yellow

# Count newlines
$newlineCount = ($lyrics -split "`n").Count - 1
Write-Host "   Newline count: $newlineCount" -ForegroundColor $(if ($newlineCount -gt 0) { "Green" } else { "Red" })

# Show lyrics with line numbers
Write-Host "`n4. Lyrics with line breaks:" -ForegroundColor Green
$lines = $lyrics -split "`n"
for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i].Trim() -eq "") {
        Write-Host "   Line $($i+1): [BLANK LINE]" -ForegroundColor DarkGray
    } else {
        Write-Host "   Line $($i+1): $($lines[$i])" -ForegroundColor White
    }
}

Write-Host "`n=== Test Complete ===" -ForegroundColor Cyan
if ($newlineCount -gt 0) {
    Write-Host "[OK] Backend is returning newlines correctly!" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Backend is NOT returning newlines - lyrics are a single block!" -ForegroundColor Red
}
