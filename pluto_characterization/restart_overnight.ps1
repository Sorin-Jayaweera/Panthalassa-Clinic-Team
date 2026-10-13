# Stop the running overnight.py while it is idle between drift readings, then start it again so it picks up newly added blocks.
# It is only stopped during the 22 s pause that follows a "drift_freq" reading, when it is not talking to either instrument.
$d = Split-Path -Parent $MyInvocation.MyCommand.Path
$csv = Join-Path $d "overnight_readings.csv"
$procId = [int](Get-Content (Join-Path $d "overnight_pid.txt"))
$env:RUN_MINUTES = "55"
$deadline = (Get-Date).AddMinutes(50)
while ((Get-Date) -lt $deadline) {
    if (-not (Get-Process -Id $procId -ErrorAction SilentlyContinue)) { "process already gone"; break }
    $last = Get-Content $csv -Tail 1
    $age = ((Get-Date) - (Get-Item $csv).LastWriteTime).TotalSeconds
    if ($last -match ",drift_freq," -and $age -gt 3 -and $age -lt 14) {
        Stop-Process -Id $procId -Force
        "stopped pid $procId during the pause after: $last"
        break
    }
    Start-Sleep -Milliseconds 700
}
if (Get-Process -Id $procId -ErrorAction SilentlyContinue) { "did not find a pause; left it running"; exit 1 }
Start-Sleep 2
$stamp = Get-Date -Format "HHmmss"
$p = Start-Process -FilePath "C:\Python314\python.exe" -ArgumentList "-u","overnight.py" -WorkingDirectory $d -RedirectStandardOutput "$d\overnight_log_$stamp.txt" -RedirectStandardError "$d\overnight_err_$stamp.txt" -WindowStyle Hidden -PassThru
$p.Id | Out-File (Join-Path $d "overnight_pid.txt") -Encoding ascii
"restarted as pid $($p.Id), log overnight_log_$stamp.txt"
