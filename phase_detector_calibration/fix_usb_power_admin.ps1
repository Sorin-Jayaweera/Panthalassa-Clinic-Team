# Run in an ADMIN PowerShell (Sorin). Stops Windows from power-managing the USB path to the Pluto.
# 1. USB selective suspend off while on AC (it is currently ON: AC index 1)
powercfg /setacvalueindex SCHEME_CURRENT 2a737441-1930-4402-8d77-b2bebba308a3 48e6b7a6-50f5-4782-a5d4-53bb8f07e226 0
powercfg /setactive SCHEME_CURRENT
# 2. "Allow the computer to turn off this device to save power" off for the USB hub (WCH 1A86:8098) and the Pluto
Get-CimInstance -Namespace root\wmi -ClassName MSPower_DeviceEnable |
    Where-Object { $_.InstanceName -match 'VID_1A86&PID_8098|VID_0456&PID_B673' } |
    ForEach-Object { Set-CimInstance -InputObject $_ -Property @{Enable = $false}; $_.InstanceName }
# 3. Show the result
powercfg /q SCHEME_CURRENT 2a737441-1930-4402-8d77-b2bebba308a3 48e6b7a6-50f5-4782-a5d4-53bb8f07e226 | Select-String 'Current AC'
Get-CimInstance -Namespace root\wmi -ClassName MSPower_DeviceEnable |
    Where-Object { $_.InstanceName -match 'VID_1A86&PID_8098|VID_0456&PID_B673' } | Select-Object InstanceName, Enable

# If the Pluto drops again, this resets the hub it sits on (admin), instead of unplugging anything:
#   pnputil /restart-device "USB\VID_1A86&PID_8098\5&2D37C237&0&3"
