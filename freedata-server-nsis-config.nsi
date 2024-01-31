!include "MUI2.nsh"

; The name and file name of the installer
Name "FreeData Server"
OutFile "FreeData-Server-Installer.exe"

; Default installation directory
InstallDir "$PROGRAMFILES\FreeData\freedata-server"

; Registry key to store the installation directory
InstallDirRegKey HKCU "Software\FreeData\freedata-server" "Install_Dir"

; Modern UI settings
!define MUI_ABORTWARNING

; Define the welcome page text
!define MUI_WELCOMEPAGE_TEXT "Welcome to the FreeData Server Setup Wizard. This wizard will guide you through the installation process."

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; Uninstaller
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Language (you can choose and configure the language(s) you want)
!insertmacro MUI_LANGUAGE "English"

; Installer Sections
Section "Install FreeData Server" SEC01

  ; Set output path to the installation directory
  SetOutPath $INSTDIR

  ; Add your application files here
  File /r "modem\server.dist\*.*"

  ; Additional installation commands here

  ; Create a shortcut in the user's desktop
  CreateShortCut "$DESKTOP\FreeData Server.lnk" "$INSTDIR\freedata-server.exe"

  ; Create Uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

; Uninstaller Section
Section "Uninstall"

  ; Delete files and directories
  Delete $INSTDIR\freedata-server.exe
  RMDir /r $INSTDIR

  ; Remove the shortcut
  Delete "$DESKTOP\FreeData Server.lnk"

  ; Additional uninstallation commands here

SectionEnd


