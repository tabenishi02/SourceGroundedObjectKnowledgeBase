Option Explicit

Dim fso, shell, scriptDir, repoRoot, pythonw, command
Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
repoRoot = fso.GetParentFolderName(scriptDir)
pythonw = fso.BuildPath(repoRoot, ".venv\Scripts\pythonw.exe")

If Not fso.FileExists(pythonw) Then
    MsgBox "SGOKB virtual environment was not found:" & vbCrLf & pythonw, vbCritical, "SGOKB"
    WScript.Quit 1
End If

shell.CurrentDirectory = repoRoot
command = """" & pythonw & """ -m sgokb.gui.main"
shell.Run command, 0, False
