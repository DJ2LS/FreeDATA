; NSIS Script for FreeData Server

; Name of the installer
OutFile "FreeData-Server-Installer.exe"

; Default installation directory
InstallDir "$PROGRAMFILES\FreeData Server"

; Registry key to store the installation directory
InstallDirRegKey HKCU "Software\FreeDataServer" "Install_Dir"

; Show installation details
ShowInstDetails show

; Show uninstallation details
ShowUninstDetails show

; Define GITHUB location
!define GITHUB_WORKSPACE



Section "MainSection" SEC01

  ; Set the output path to the installation directory
  SetOutPath $INSTDIR

  ; Add the entire FreeData Server directory
  File /r "modem\server.dist\*.*"

  ; Write the installation path to the registry
  WriteRegStr HKCU "Software\FreeDataServer" "Install_Dir" "$INSTDIR"

  ; Create a desktop shortcut for easy access
  CreateShortCut "$DESKTOP\FreeData Server.lnk" "$INSTDIR\freedata-server.exe"

SectionEnd

Section "Uninstall"

  ; Delete the entire FreeData Server directory
  RMDir /r $INSTDIR

  ; Remove the registry entry
  DeleteRegKey HKCU "Software\FreeDataServer"

  ; Delete the desktop shortcut
  Delete "$DESKTOP\FreeData Server.lnk"

SectionEnd