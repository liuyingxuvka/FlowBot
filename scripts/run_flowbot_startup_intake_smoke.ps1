$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$UiScript = Join-Path $Root "flowbot\assets\ui\startup_intake\flowbot_startup_intake.ps1"

$checks = [ordered]@{}

$smokeOutput = & powershell -NoProfile -ExecutionPolicy Bypass -File $UiScript -ProjectRoot $Root -SmokeTest
$checks.ui_loads = @{
    ok = (($smokeOutput -join "`n") -match "UI_SMOKE_OK")
}

$runsRoot = Join-Path $Root ".flowbot\runs"
$beforeCancelRunCount = 0
if (Test-Path -LiteralPath $runsRoot) {
    $beforeCancelRunCount = (Get-ChildItem -LiteralPath $runsRoot -Directory | Measure-Object).Count
}
$cancelOutput = & powershell -NoProfile -ExecutionPolicy Bypass -File $UiScript -ProjectRoot $Root -HeadlessCancel
$cancelLines = @($cancelOutput)
$afterCancelRunCount = 0
if (Test-Path -LiteralPath $runsRoot) {
    $afterCancelRunCount = (Get-ChildItem -LiteralPath $runsRoot -Directory | Measure-Object).Count
}
$checks.cancel_before_run = @{
    ok = ((Test-Path -LiteralPath ($cancelLines[-1])) -and ($beforeCancelRunCount -eq $afterCancelRunCount))
}

$beforeConfirmRuns = @()
if (Test-Path -LiteralPath $runsRoot) {
    $beforeConfirmRuns = Get-ChildItem -LiteralPath $runsRoot -Directory | Select-Object -ExpandProperty Name
}
$confirmOutput = & powershell -NoProfile -ExecutionPolicy Bypass -File $UiScript -ProjectRoot $Root -HeadlessConfirmText "用 FlowBot native startup intake smoke 跑通一次模型优先路线。"
$runDir = Get-ChildItem -LiteralPath $runsRoot -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($null -eq $runDir) {
    throw "No run directory created by confirmed startup intake."
}
$createdNewRun = -not ($beforeConfirmRuns -contains $runDir.Name)
$statePath = Join-Path $runDir.FullName "router_state.json"
$state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
$resultJsonPath = Join-Path $runDir.FullName "intake\flowbot_intake_result.json"
$resultJson = Get-Content -LiteralPath $resultJsonPath -Raw | ConvertFrom-Json

$checks.confirm_creates_run = @{
    ok = ($createdNewRun -and $state.status -eq "DONE")
    run_id = $runDir.Name
}
$checks.default_language = @{
    ok = ($resultJson.language -eq "en")
}
$checks.intake_artifacts = @{
    ok = @(
        "intake\flowbot_intake_body.md",
        "intake\flowbot_intake_result.json",
        "intake\flowbot_intake_receipt.json",
        "intake\flowbot_intake_envelope.json"
    ) | ForEach-Object { Test-Path -LiteralPath (Join-Path $runDir.FullName $_) } | Where-Object { -not $_ } | Measure-Object | ForEach-Object { $_.Count -eq 0 }
}
$checks.runtime_outputs = @{
    ok = @(
        "pm\flowguard_result.json",
        "pm\linear_route.json",
        "controller_ledger.json",
        "artifacts\final_report.md",
        "mermaid.mmd"
    ) | ForEach-Object { Test-Path -LiteralPath (Join-Path $runDir.FullName $_) } | Where-Object { -not $_ } | Measure-Object | ForEach-Object { $_.Count -eq 0 }
}

$ok = $true
foreach ($entry in $checks.Values) {
    if (-not [bool]$entry.ok) {
        $ok = $false
    }
}

$report = [ordered]@{
    ok = $ok
    checks = $checks
    confirm_output = $confirmOutput
}
$outputPath = Join-Path $Root "tmp\flowbot_startup_intake_smoke_results.json"
$report | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $outputPath -Encoding UTF8
$report | ConvertTo-Json -Depth 20

if (-not $ok) {
    exit 1
}
