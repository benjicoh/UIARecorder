param(
    [Parameter(Position=0, Mandatory=$false)]
    [ValidateScript({Test-Path $_ -PathType 'Container'})]
    [string]$Folder = "generated_scripts\user_recording",

    [Parameter(Position=1, Mandatory=$false)]
    [ArgumentCompleter({ param($commandName, $parameterName, $wordToComplete, $commandAst, $fakeBoundParameters)
        Get-Process | Where-Object { $_.MainWindowTitle -ne "" } | ForEach-Object { $_.ProcessName + ".exe" }
    })]
    [string]$ProcessName = "notepad.exe"
)

# Try to use venv if available, else fallback to system python
$python = "python"
if (Test-Path ".\.venv\Scripts\python.exe") {
    $python = ".\.venv\Scripts\python.exe"
}

& $python -m python.recorder_tool -wh $ProcessName
