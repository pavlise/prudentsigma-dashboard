# Automated Testing Script for Google Drive Setup

# This script tests your Google Drive integration after manual setup

param(
    [string]$Action = "test"
)

$PROJECT_DIR = "C:\Users\Pavlos Elpidorou\Documents\AI_Project"
$CREDENTIALS_FILE = Join-Path $PROJECT_DIR "google_drive_credentials.json"

function Test-Credentials {
    Write-Host "Testing Google Drive credentials..." -ForegroundColor Yellow

    if (!(Test-Path $CREDENTIALS_FILE)) {
        Write-Host "❌ Credentials file not found: $CREDENTIALS_FILE" -ForegroundColor Red
        Write-Host "Please complete GOOGLE_DRIVE_SETUP.md first" -ForegroundColor Red
        return $false
    }

    try {
        # Test JSON format
        $credentials = Get-Content $CREDENTIALS_FILE -Raw | ConvertFrom-Json
        Write-Host "✅ Credentials file is valid JSON" -ForegroundColor Green

        # Check required fields
        $required = @("type", "project_id", "private_key", "client_email")
        foreach ($field in $required) {
            if ($credentials.$field) {
                Write-Host "✅ $field found" -ForegroundColor Green
            } else {
                Write-Host "❌ $field missing" -ForegroundColor Red
                return $false
            }
        }

        Write-Host "✅ All required fields present" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "❌ Invalid JSON format: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Test-Upload {
    Write-Host "Testing report upload..." -ForegroundColor Yellow

    # Create a test report
    $testReport = Join-Path $PROJECT_DIR "test_report.md"
    $testContent = "# Test Report`n`nGenerated: $(Get-Date)`n`nThis is a test report for Google Drive integration."

    try {
        $testContent | Out-File -FilePath $testReport -Encoding UTF8
        Write-Host "✅ Test report created: $testReport" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Failed to create test report: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }

    # Run the upload test
    try {
        Push-Location $PROJECT_DIR
        & python automated_report.py
        Pop-Location

        # Check log for success
        $logFile = Join-Path $PROJECT_DIR "reports\generation.log"
        if (Test-Path $logFile) {
            $lastLog = Get-Content $logFile -Tail 1
            if ($lastLog -match "Uploaded to Google Drive") {
                Write-Host "✅ Upload successful! Check your Google Drive." -ForegroundColor Green
                return $true
            } else {
                Write-Host "❌ Upload may have failed. Check logs: $logFile" -ForegroundColor Red
                Write-Host "Last log: $lastLog" -ForegroundColor Yellow
                return $false
            }
        } else {
            Write-Host "❌ No generation log found" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "❌ Upload test failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
    finally {
        # Clean up test file
        if (Test-Path $testReport) {
            Remove-Item $testReport
        }
    }
}

function Show-Status {
    Write-Host "=== Google Drive Integration Status ===" -ForegroundColor Cyan

    # Check credentials
    $hasCreds = Test-Path $CREDENTIALS_FILE
    Write-Host "Credentials file: $(if ($hasCreds) { '✅ Found' } else { '❌ Missing' })" -ForegroundColor $(if ($hasCreds) { 'Green' } else { 'Red' })

    # Check scripts
    $scripts = @("automated_report.py", "dashboard.py", "drive_utils.py")
    foreach ($script in $scripts) {
        $scriptPath = Join-Path $PROJECT_DIR $script
        $exists = Test-Path $scriptPath
        Write-Host "$script updated: $(if ($exists) { '✅ Yes' } else { '❌ No' })" -ForegroundColor $(if ($exists) { 'Green' } else { 'Red' })
    }

    # Check reports directory
    $reportsDir = Join-Path $PROJECT_DIR "reports"
    $hasReports = Test-Path $reportsDir
    Write-Host "Reports directory: $(if ($hasReports) { '✅ Exists' } else { '❌ Missing' })" -ForegroundColor $(if ($hasReports) { 'Green' } else { 'Red' })

    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Yellow
    if (!$hasCreds) {
        Write-Host "1. Complete GOOGLE_DRIVE_SETUP.md to get credentials" -ForegroundColor White
    }
    Write-Host "2. Run: .\test_google_drive.ps1 -Action test" -ForegroundColor White
    Write-Host "3. Run: .\test_google_drive.ps1 -Action upload" -ForegroundColor White
    Write-Host "4. Configure Streamlit Cloud secrets" -ForegroundColor White
}

# Main execution
switch ($Action) {
    "status" {
        Show-Status
    }
    "test" {
        if (Test-Credentials) {
            Write-Host "✅ Credentials test passed!" -ForegroundColor Green
        } else {
            Write-Host "❌ Credentials test failed!" -ForegroundColor Red
        }
    }
    "upload" {
        if (Test-Credentials) {
            if (Test-Upload) {
                Write-Host "✅ Upload test passed!" -ForegroundColor Green
            } else {
                Write-Host "❌ Upload test failed!" -ForegroundColor Red
            }
        }
    }
    default {
        Write-Host "Usage: .\test_google_drive.ps1 -Action <status|test|upload>" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Actions:" -ForegroundColor Cyan
        Write-Host "  status  - Show current setup status" -ForegroundColor White
        Write-Host "  test    - Test credentials file format" -ForegroundColor White
        Write-Host "  upload  - Test actual upload to Google Drive" -ForegroundColor White
    }
}