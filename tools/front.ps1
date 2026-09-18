Add-Type @"
using System;
using System.Runtime.InteropServices;
public class F {
  [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr hWnd, IntPtr after, int X, int Y, int cx, int cy, uint flags);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int cmd);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
}
"@
$w = Get-Process pythonw -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -ne '' } | Select-Object -First 1
if ($w) {
  $h = $w.MainWindowHandle
  [F]::ShowWindow($h, 5) | Out-Null
  [F]::SetWindowPos($h, [IntPtr](-1), 0, 0, 0, 0, 0x0043) | Out-Null
  [F]::SetForegroundWindow($h) | Out-Null
  Write-Output "promoted pid=$($w.Id)"
} else {
  Write-Output "no window"
}
