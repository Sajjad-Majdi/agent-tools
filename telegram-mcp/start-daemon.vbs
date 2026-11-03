' Starts the tg-mcp daemon hidden (no window). Copy a shortcut to this file into the Startup folder:
'   %APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\
' A second start is harmless: the new copy sees the port is taken and exits.
Set fso = CreateObject("Scripting.FileSystemObject")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
CreateObject("WScript.Shell").Run "node """ & dir & "\daemon.mjs""", 0, False
